#!/usr/bin/env python3
"""
Cloudflare Service Token Rotation Script
Automatically rotates service tokens and updates Kubernetes secrets
"""

import asyncio
import httpx
import json
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import subprocess
import base64
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ServiceTokenRotator:
    def __init__(self, cloudflare_api_token: str, account_id: str, team_domain: str):
        self.api_token = cloudflare_api_token
        self.account_id = account_id
        self.team_domain = team_domain
        self.base_url = "https://api.cloudflare.com/client/v4"
        
        # Service token configurations
        self.service_tokens = {
            'safework-api': {
                'description': 'API access authentication',
                'duration': '8760h',  # 1 year
                'env_vars': {
                    'client_id': 'CF_SERVICE_TOKEN_API_CLIENT_ID',
                    'client_secret': 'CF_SERVICE_TOKEN_API_CLIENT_SECRET'
                }
            },
            'safework-registry': {
                'description': 'Docker registry access',
                'duration': '8760h',
                'env_vars': {
                    'client_id': 'CF_SERVICE_TOKEN_REGISTRY_CLIENT_ID',
                    'client_secret': 'CF_SERVICE_TOKEN_REGISTRY_CLIENT_SECRET'
                }
            },
            'safework-cicd': {
                'description': 'CI/CD pipeline authentication',
                'duration': '4380h',  # 6 months
                'env_vars': {
                    'client_id': 'CF_SERVICE_TOKEN_CICD_CLIENT_ID',
                    'client_secret': 'CF_SERVICE_TOKEN_CICD_CLIENT_SECRET'
                }
            },
            'safework-monitoring': {
                'description': 'Monitoring and health checks',
                'duration': '8760h',
                'env_vars': {
                    'client_id': 'CF_SERVICE_TOKEN_MONITORING_CLIENT_ID',
                    'client_secret': 'CF_SERVICE_TOKEN_MONITORING_CLIENT_SECRET'
                }
            }
        }
        
        self.headers = {
            'Authorization': f'Bearer {self.api_token}',
            'Content-Type': 'application/json'
        }
    
    async def rotate_all_tokens(self) -> Dict[str, Dict[str, str]]:
        """Rotate all service tokens"""
        results = {}
        
        for token_name in self.service_tokens.keys():
            try:
                logger.info(f"Rotating service token: {token_name}")
                result = await self.rotate_token(token_name)
                results[token_name] = result
                logger.info(f"Successfully rotated token: {token_name}")
            except Exception as e:
                logger.error(f"Failed to rotate token {token_name}: {e}")
                results[token_name] = {"error": str(e)}
        
        return results
    
    async def rotate_token(self, token_name: str) -> Dict[str, str]:
        """Rotate a specific service token"""
        
        if token_name not in self.service_tokens:
            raise ValueError(f"Unknown service token: {token_name}")
        
        token_config = self.service_tokens[token_name]
        
        # Get current token
        current_token = await self._get_service_token(token_name)
        
        # Create new token
        new_token = await self._create_service_token(token_name, token_config)
        
        # Update Kubernetes secret
        await self._update_kubernetes_secret(token_name, new_token)
        
        # Update GitHub secrets
        await self._update_github_secrets(token_name, new_token)
        
        # Wait for propagation
        logger.info(f"Waiting for token propagation ({token_name})...")
        await asyncio.sleep(60)  # Wait 1 minute for propagation
        
        # Test new token
        is_valid = await self._test_service_token(new_token)
        
        if is_valid:
            # Delete old token if it exists
            if current_token:
                await self._delete_service_token(current_token['id'])
                logger.info(f"Deleted old token: {token_name}")
            
            return {
                'client_id': new_token['client_id'],
                'client_secret': new_token['client_secret'],
                'created_at': new_token['created_at'],
                'expires_at': new_token['expires_at']
            }
        else:
            # Rollback - delete new token and keep old one
            await self._delete_service_token(new_token['id'])
            raise Exception(f"New token validation failed for {token_name}")
    
    async def _get_service_token(self, token_name: str) -> Optional[Dict[str, Any]]:
        """Get service token by name"""
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/accounts/{self.account_id}/access/service_tokens",
                    headers=self.headers,
                    timeout=30
                )
                response.raise_for_status()
                
                tokens = response.json()['result']
                return next((token for token in tokens if token['name'] == token_name), None)
            except Exception as e:
                logger.warning(f"Failed to get service token {token_name}: {e}")
                return None
    
    async def _create_service_token(self, token_name: str, token_config: Dict[str, Any]) -> Dict[str, str]:
        """Create new service token"""
        
        data = {
            'name': token_name,
            'duration': token_config['duration']
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/accounts/{self.account_id}/access/service_tokens",
                headers=self.headers,
                json=data,
                timeout=30
            )
            response.raise_for_status()
            
            return response.json()['result']
    
    async def _delete_service_token(self, token_id: str):
        """Delete service token"""
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/accounts/{self.account_id}/access/service_tokens/{token_id}",
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
    
    async def _update_kubernetes_secret(self, token_name: str, token_data: Dict[str, str]):
        """Update Kubernetes secret with new token"""
        
        token_config = self.service_tokens[token_name]
        
        # Get current secret
        try:
            result = subprocess.run([
                'kubectl', 'get', 'secret', 'cloudflare-service-tokens', 
                '-n', 'safework', '-o', 'json'
            ], capture_output=True, text=True, check=True)
            
            secret_data = json.loads(result.stdout)
            
            # Decode existing data
            existing_data = {}
            for key, value in secret_data['data'].items():
                existing_data[key] = base64.b64decode(value).decode('utf-8')
            
            # Update with new token data
            existing_data[token_config['env_vars']['client_id']] = token_data['client_id']
            existing_data[token_config['env_vars']['client_secret']] = token_data['client_secret']
            
            # Delete existing secret
            subprocess.run([
                'kubectl', 'delete', 'secret', 'cloudflare-service-tokens', 
                '-n', 'safework'
            ], check=True)
            
            # Create new secret with updated data
            cmd = ['kubectl', 'create', 'secret', 'generic', 'cloudflare-service-tokens', '-n', 'safework']
            
            for key, value in existing_data.items():
                cmd.extend(['--from-literal', f'{key}={value}'])
            
            subprocess.run(cmd, check=True)
            
            # Add labels
            subprocess.run([
                'kubectl', 'label', 'secret', 'cloudflare-service-tokens', '-n', 'safework',
                'app=safework', 'component=authentication', 'security=service-tokens'
            ], check=True)
            
            logger.info(f"Updated Kubernetes secret for {token_name}")
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to update Kubernetes secret: {e}")
            raise
    
    async def _update_github_secrets(self, token_name: str, token_data: Dict[str, str]):
        """Update GitHub secrets with new token"""
        
        token_config = self.service_tokens[token_name]
        
        try:
            # Update client ID
            subprocess.run([
                'gh', 'secret', 'set', token_config['env_vars']['client_id'],
                '--body', token_data['client_id']
            ], check=True)
            
            # Update client secret
            subprocess.run([
                'gh', 'secret', 'set', token_config['env_vars']['client_secret'],
                '--body', token_data['client_secret']
            ], check=True)
            
            logger.info(f"Updated GitHub secrets for {token_name}")
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to update GitHub secrets for {token_name}: {e}")
            # Don't raise error - GitHub secrets are optional
    
    async def _test_service_token(self, token_data: Dict[str, str]) -> bool:
        """Test service token validity"""
        
        try:
            url = f"https://{self.team_domain}.cloudflareaccess.com/cdn-cgi/access/login"
            
            headers = {
                'CF-Access-Client-Id': token_data['client_id'],
                'CF-Access-Client-Secret': token_data['client_secret'],
                'Content-Type': 'application/json'
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, timeout=10)
                return response.status_code == 200
                
        except Exception as e:
            logger.error(f"Token test failed: {e}")
            return False
    
    async def get_token_expiry_info(self) -> Dict[str, Dict[str, Any]]:
        """Get expiry information for all tokens"""
        
        expiry_info = {}
        
        for token_name in self.service_tokens.keys():
            token = await self._get_service_token(token_name)
            
            if token:
                expires_at = datetime.fromisoformat(token['expires_at'].replace('Z', '+00:00'))
                days_until_expiry = (expires_at - datetime.now()).days
                
                expiry_info[token_name] = {
                    'expires_at': token['expires_at'],
                    'days_until_expiry': days_until_expiry,
                    'needs_rotation': days_until_expiry < 30,
                    'client_id': token['client_id']
                }
            else:
                expiry_info[token_name] = {
                    'error': 'Token not found',
                    'needs_rotation': True
                }
        
        return expiry_info


async def main():
    """Main function"""
    
    # Get environment variables
    cloudflare_api_token = os.getenv('CLOUDFLARE_API_TOKEN')
    account_id = os.getenv('CLOUDFLARE_ACCOUNT_ID')
    team_domain = os.getenv('CLOUDFLARE_TEAM_DOMAIN')
    
    if not all([cloudflare_api_token, account_id, team_domain]):
        logger.error("Missing required environment variables:")
        logger.error("- CLOUDFLARE_API_TOKEN")
        logger.error("- CLOUDFLARE_ACCOUNT_ID")
        logger.error("- CLOUDFLARE_TEAM_DOMAIN")
        sys.exit(1)
    
    rotator = ServiceTokenRotator(cloudflare_api_token, account_id, team_domain)
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        logger.error("Usage: python rotate-service-tokens.py <command> [token_name]")
        logger.error("Commands:")
        logger.error("  rotate-all    - Rotate all service tokens")
        logger.error("  rotate <name> - Rotate specific token")
        logger.error("  check-expiry  - Check token expiry status")
        sys.exit(1)
    
    command = sys.argv[1]
    
    try:
        if command == 'rotate-all':
            logger.info("Starting rotation of all service tokens...")
            results = await rotator.rotate_all_tokens()
            
            print("\n🔄 Service Token Rotation Results:")
            print("=" * 40)
            
            for token_name, result in results.items():
                if 'error' in result:
                    print(f"❌ {token_name}: {result['error']}")
                else:
                    print(f"✅ {token_name}: Rotated successfully")
                    print(f"   Client ID: {result['client_id']}")
                    print(f"   Expires: {result['expires_at']}")
            
        elif command == 'rotate':
            if len(sys.argv) < 3:
                logger.error("Token name required for rotate command")
                sys.exit(1)
                
            token_name = sys.argv[2]
            logger.info(f"Rotating service token: {token_name}")
            
            result = await rotator.rotate_token(token_name)
            
            print(f"\n✅ Service Token '{token_name}' rotated successfully:")
            print(f"   Client ID: {result['client_id']}")
            print(f"   Expires: {result['expires_at']}")
            
        elif command == 'check-expiry':
            logger.info("Checking token expiry status...")
            expiry_info = await rotator.get_token_expiry_info()
            
            print("\n📅 Service Token Expiry Status:")
            print("=" * 40)
            
            for token_name, info in expiry_info.items():
                if 'error' in info:
                    print(f"❌ {token_name}: {info['error']}")
                else:
                    status = "⚠️ NEEDS ROTATION" if info['needs_rotation'] else "✅ OK"
                    print(f"{status} {token_name}:")
                    print(f"   Expires: {info['expires_at']}")
                    print(f"   Days until expiry: {info['days_until_expiry']}")
                    print(f"   Client ID: {info['client_id']}")
                    print()
            
        else:
            logger.error(f"Unknown command: {command}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Operation failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())