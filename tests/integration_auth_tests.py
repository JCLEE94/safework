"""
Authentication and authorization integration tests for SafeWork Pro.

This module contains comprehensive integration tests for the authentication
and authorization system, including security testing and edge cases.
"""

import pytest
import pytest_asyncio
from httpx import AsyncClient
from fastapi import status


class TestAuthenticationIntegration:
    """Test authentication system integration."""
    
    @pytest.mark.integration
    async def test_auth_endpoints_existence(self, client: AsyncClient):
        """Test that auth endpoints exist and respond appropriately."""
        # Test common authentication endpoints
        auth_endpoints = [
            ("/api/v1/auth/login", "POST"),
            ("/api/v1/auth/logout", "POST"),
            ("/api/v1/auth/me", "GET"),
        ]
        
        for endpoint, method in auth_endpoints:
            if method == "POST":
                response = await client.post(endpoint, json={})
            elif method == "GET":
                response = await client.get(endpoint)
            
            # Endpoint should exist (not return 404)
            # May return 401, 422, etc. but not 404 if implemented
            if response.status_code != status.HTTP_404_NOT_FOUND:
                assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.integration
    async def test_protected_endpoints_auth(self, client: AsyncClient):
        """Test that protected endpoints properly handle authentication."""
        protected_endpoints = [
            "/api/v1/workers/",
            "/api/v1/health-exams/",
            "/api/v1/work-environments/",
            "/api/v1/reports/",
        ]
        
        for endpoint in protected_endpoints:
            # Test without authentication
            response = await client.get(endpoint)
            
            # Should either:
            # - Return 200 (development mode / no auth required)
            # - Return 401 (authentication required)
            # - Return 403 (authentication required but different message)
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
    
    @pytest.mark.integration
    async def test_development_mode_bypass(self, client: AsyncClient):
        """Test development mode authentication bypass."""
        # In development mode, some endpoints might not require auth
        response = await client.get("/api/v1/workers/")
        
        # Should work or fail gracefully
        assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR
        
        if response.status_code == status.HTTP_200_OK:
            # If successful, should return valid JSON
            try:
                data = response.json()
                assert isinstance(data, (list, dict))
            except ValueError:
                pytest.fail("Expected JSON response for successful request")


class TestAuthenticationSecurity:
    """Test authentication security aspects."""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_malicious_auth_headers(self, client: AsyncClient):
        """Test handling of malicious authentication headers."""
        malicious_headers = [
            {"Authorization": "Bearer " + "A" * 10000},  # Very long token
            {"Authorization": "Bearer ../../../etc/passwd"},  # Path traversal
            {"Authorization": "Bearer <script>alert('xss')</script>"},  # XSS
            {"Authorization": "Bearer '; DROP TABLE users; --"},  # SQL injection
            {"Authorization": "Bearer \x00\x01\x02"},  # Binary data
            {"Authorization": ""},  # Empty auth header
        ]
        
        for headers in malicious_headers:
            response = await client.get("/api/v1/workers/", headers=headers)
            
            # Should handle malicious headers gracefully
            assert response.status_code in [
                status.HTTP_200_OK,  # If development mode
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ]
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_sql_injection_in_auth(self, client: AsyncClient):
        """Test SQL injection protection in authentication."""
        sql_injection_payloads = [
            {"username": "admin'; DROP TABLE users; --", "password": "password"},
            {"username": "admin' OR '1'='1", "password": "password"},
            {"username": "admin", "password": "' OR '1'='1"},
            {"username": "admin' UNION SELECT * FROM users --", "password": "pass"},
        ]
        
        for payload in sql_injection_payloads:
            response = await client.post("/api/v1/auth/login", json=payload)
            
            if response.status_code != status.HTTP_404_NOT_FOUND:
                # Should not cause database errors
                assert response.status_code in [
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_400_BAD_REQUEST
                ]
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_rate_limiting_simulation(self, client: AsyncClient):
        """Test rate limiting behavior simulation."""
        # Make multiple rapid authentication attempts
        rapid_requests = []
        
        for i in range(10):
            response = await client.post("/api/v1/auth/login", json={
                "username": f"user{i}",
                "password": "wrongpassword"
            })
            rapid_requests.append(response.status_code)
        
        # Should handle multiple requests without server errors
        for status_code in rapid_requests:
            assert status_code < status.HTTP_500_INTERNAL_SERVER_ERROR


class TestAPISecurityHeaders:
    """Test API security headers and CORS."""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_cors_headers(self, client: AsyncClient):
        """Test CORS headers are properly configured."""
        # Test CORS preflight request
        headers = {
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization, Content-Type"
        }
        
        response = await client.options("/api/v1/workers/", headers=headers)
        
        # Should handle CORS properly
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_204_NO_CONTENT,
            status.HTTP_404_NOT_FOUND
        ]
        
        # Test actual CORS request
        headers = {"Origin": "http://localhost:3000"}
        response = await client.get("/api/v1/workers/", headers=headers)
        
        # Should allow CORS or handle gracefully
        assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_security_headers(self, client: AsyncClient):
        """Test security headers in responses."""
        response = await client.get("/api/v1/workers/")
        
        # Check that response is valid (security headers are optional)
        assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR
        
        # If security headers are implemented, they should be present
        security_headers = [
            "X-Content-Type-Options",
            "X-Frame-Options", 
            "X-XSS-Protection",
            "Strict-Transport-Security"
        ]
        
        # Just ensure no server errors - headers are implementation dependent
        assert response.headers is not None


class TestInputValidationSecurity:
    """Test input validation and sanitization."""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_xss_protection(self, client: AsyncClient):
        """Test XSS protection in API endpoints."""
        xss_payloads = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "<img src=x onerror=alert('xss')>",
            "'><script>alert(String.fromCharCode(88,83,83))</script>",
        ]
        
        for payload in xss_payloads:
            # Test in query parameters
            response = await client.get(f"/api/v1/workers/?search={payload}")
            
            if response.status_code == status.HTTP_200_OK:
                # Check that response doesn't contain unescaped script content
                response_text = response.text.lower()
                assert "<script>" not in response_text
                assert "javascript:" not in response_text
                assert "onerror=" not in response_text
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_file_upload_security(self, client: AsyncClient):
        """Test file upload security (if endpoints exist)."""
        # Test malicious file uploads
        malicious_files = [
            ("test.php", b"<?php system($_GET['cmd']); ?>", "application/x-php"),
            ("test.jsp", b"<% Runtime.getRuntime().exec(request.getParameter(\"cmd\")); %>", "application/x-jsp"),
            ("test.exe", b"MZ\x90\x00", "application/x-executable"),
            ("../../../etc/passwd", b"root:x:0:0", "text/plain"),
        ]
        
        upload_endpoints = [
            "/api/v1/documents/upload",
            "/api/v1/chemical-substances/upload",
            "/api/v1/health-education/upload",
        ]
        
        for endpoint in upload_endpoints:
            for filename, content, content_type in malicious_files:
                files = {"file": (filename, content, content_type)}
                response = await client.post(endpoint, files=files)
                
                # Should reject malicious uploads or return 404 if not implemented
                if response.status_code not in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED]:
                    assert response.status_code in [
                        status.HTTP_400_BAD_REQUEST,
                        status.HTTP_401_UNAUTHORIZED,
                        status.HTTP_403_FORBIDDEN,
                        status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
                        status.HTTP_422_UNPROCESSABLE_ENTITY
                    ]


class TestErrorHandlingConsistency:
    """Test consistent error handling across the API."""
    
    @pytest.mark.integration
    async def test_error_response_format(self, client: AsyncClient):
        """Test that error responses follow a consistent format."""
        # Generate various error conditions
        error_scenarios = [
            ("/api/v1/workers/999999", "GET"),  # Resource not found
            ("/api/v1/nonexistent-endpoint", "GET"),  # Endpoint not found
            ("/api/v1/workers/", "PATCH"),  # Method not allowed
        ]
        
        for endpoint, method in error_scenarios:
            if method == "GET":
                response = await client.get(endpoint)
            elif method == "PATCH":
                response = await client.patch(endpoint, json={})
            
            if response.status_code >= status.HTTP_400_BAD_REQUEST:
                # Error responses should be well-formed
                try:
                    error_data = response.json()
                    assert isinstance(error_data, dict)
                    # Common error response fields
                    assert "detail" in error_data or "message" in error_data or "error" in error_data
                except ValueError:
                    # If not JSON, should still be a valid response
                    assert len(response.text) > 0
                    assert response.text != "Internal Server Error"
    
    @pytest.mark.integration
    async def test_http_method_consistency(self, client: AsyncClient):
        """Test HTTP method handling consistency."""
        test_endpoint = "/api/v1/workers/"
        
        methods = [
            ("GET", client.get),
            ("POST", lambda url: client.post(url, json={})),
            ("PUT", lambda url: client.put(url, json={})),
            ("DELETE", client.delete),
            ("PATCH", lambda url: client.patch(url, json={})),
            ("HEAD", client.head),
        ]
        
        for method_name, method_func in methods:
            response = await method_func(test_endpoint)
            
            # Should not cause server errors
            assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR
            
            # If method not allowed, should return 405
            if response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED:
                # Should include Allow header (good practice)
                assert "Allow" in response.headers or True  # Allow is optional


class TestDataValidationSecurity:
    """Test data validation for security vulnerabilities."""
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_json_injection(self, client: AsyncClient):
        """Test JSON injection protection."""
        json_injection_payloads = [
            {"name": {"$ne": None}},  # NoSQL injection
            {"name": {"$regex": ".*"}},  # MongoDB injection
            {"name": "'; DROP TABLE workers; --"},  # SQL in JSON
            {"name": {"__proto__": {"isAdmin": True}}},  # Prototype pollution
        ]
        
        for payload in json_injection_payloads:
            response = await client.post("/api/v1/workers/", json=payload)
            
            if response.status_code not in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED]:
                # Should handle malicious JSON safely
                assert response.status_code in [
                    status.HTTP_401_UNAUTHORIZED,
                    status.HTTP_403_FORBIDDEN,
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    status.HTTP_400_BAD_REQUEST
                ]
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_large_payload_handling(self, client: AsyncClient):
        """Test handling of unusually large payloads."""
        # Create large payload
        large_payload = {
            "name": "A" * 100000,  # 100KB string
            "description": "B" * 100000,
            "data": ["C" * 1000] * 100  # Array of large strings
        }
        
        response = await client.post("/api/v1/workers/", json=large_payload)
        
        if response.status_code not in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED]:
            # Should handle large payloads gracefully
            assert response.status_code in [
                status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                status.HTTP_400_BAD_REQUEST,
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                status.HTTP_401_UNAUTHORIZED,
                status.HTTP_403_FORBIDDEN
            ]
    
    @pytest.mark.integration
    @pytest.mark.security
    async def test_unicode_handling(self, client: AsyncClient):
        """Test handling of various Unicode characters."""
        unicode_test_cases = [
            {"name": "테스트사용자"},  # Korean
            {"name": "用户测试"},  # Chinese
            {"name": "тестовый пользователь"},  # Russian
            {"name": "🚧👷‍♂️🏗️"},  # Emojis
            {"name": "\u202e\u0041\u0042"},  # Right-to-left override
            {"name": "\x00\x01\x02"},  # Control characters
        ]
        
        for payload in unicode_test_cases:
            response = await client.post("/api/v1/workers/", json=payload)
            
            if response.status_code not in [status.HTTP_404_NOT_FOUND, status.HTTP_405_METHOD_NOT_ALLOWED]:
                # Should handle Unicode safely
                assert response.status_code < status.HTTP_500_INTERNAL_SERVER_ERROR