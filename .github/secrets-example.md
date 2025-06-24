# GitHub Secrets Configuration Example

## Required Secrets

### Docker Hub (for base images)
- **DOCKERHUB_USERNAME**: `your-dockerhub-username`
- **DOCKERHUB_TOKEN**: `dckr_pat_xxxxxxxxxxxxxxxxxxxxx` (NOT your password!)
  - Create at: https://hub.docker.com/settings/security
  - Select "New Access Token"
  - Give it a descriptive name like "github-actions"

### Private Registry
- **REGISTRY_USERNAME**: `your-registry-username`
- **REGISTRY_PASSWORD**: `your-registry-password`

### Deployment Server
- **DEPLOY_HOST**: `192.168.50.215`
- **DEPLOY_USER**: `docker`
- **DEPLOY_PASSWORD**: `your-ssh-password`
- **DEPLOY_PORT**: `1111`

## How to Set via GitHub CLI

```bash
# Example with actual values (replace with your own)
echo "myusername" | gh secret set DOCKERHUB_USERNAME --repo=qws941/health-management-system
echo "dckr_pat_xxxxx" | gh secret set DOCKERHUB_TOKEN --repo=qws941/health-management-system
echo "reguser" | gh secret set REGISTRY_USERNAME --repo=qws941/health-management-system
echo "regpass123" | gh secret set REGISTRY_PASSWORD --repo=qws941/health-management-system
echo "192.168.50.215" | gh secret set DEPLOY_HOST --repo=qws941/health-management-system
echo "docker" | gh secret set DEPLOY_USER --repo=qws941/health-management-system
echo "sshpass123" | gh secret set DEPLOY_PASSWORD --repo=qws941/health-management-system
echo "1111" | gh secret set DEPLOY_PORT --repo=qws941/health-management-system
```

## How to Set via GitHub Web UI

1. Navigate to: https://github.com/qws941/health-management-system/settings/secrets/actions
2. Click "New repository secret"
3. Add each secret with the name and value
4. Click "Add secret"

## Verify Secrets

```bash
gh secret list --repo=qws941/health-management-system
```

Expected output:
```
DEPLOY_HOST        Updated 2025-01-19
DEPLOY_PASSWORD    Updated 2025-01-19
DEPLOY_PORT        Updated 2025-01-19
DEPLOY_USER        Updated 2025-01-19
DOCKERHUB_TOKEN    Updated 2025-01-19
DOCKERHUB_USERNAME Updated 2025-01-19
REGISTRY_PASSWORD  Updated 2025-01-19
REGISTRY_USERNAME  Updated 2025-01-19
```