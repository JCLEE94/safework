# CI/CD Pipeline Documentation

## Overview

This document describes the CI/CD pipeline setup for the SafeWork Pro Health Management System. The pipeline is implemented using GitHub Actions and provides automated testing, building, security scanning, and deployment.

## Pipeline Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │     Staging     │    │   Production    │
│                 │    │                 │    │                 │
│ Feature Branch  │───▶│ Develop Branch  │───▶│  Main Branch    │
│ Pull Request    │    │ Auto Deploy     │    │ Manual Deploy   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  PR Validation  │    │ Staging Tests   │    │ Release Build   │
│  - Unit Tests   │    │ - Integration   │    │ - Full Tests    │
│  - Lint/Format  │    │ - E2E Tests     │    │ - Security Scan │
│  - Security     │    │ - Performance   │    │ - Docker Build  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## Workflows

### 1. CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch

**Jobs:**
- **Backend Tests**: Python unit tests, security tests, API tests, performance tests
- **Frontend Tests**: JavaScript/TypeScript tests, linting, type checking, build
- **Security Scan**: Bandit security analysis, dependency vulnerability scanning
- **Docker Build**: Multi-platform container builds with caching
- **Deploy Staging**: Automatic deployment to staging environment (develop branch)
- **Deploy Production**: Automatic deployment to production (main branch)

### 2. Release Workflow (`.github/workflows/release.yml`)

**Triggers:**
- Git tags matching `v*` pattern

**Jobs:**
- **Create Release**: Generate changelog, create GitHub release
- **Build Release Image**: Build and push production Docker images
- **Create Package**: Generate distribution packages (tar.gz, zip)
- **Auto Deploy Production**: Deploy stable releases to production
- **Notify**: Send notifications about release status

### 3. Code Quality (`.github/workflows/code-quality.yml`)

**Triggers:**
- Push to `main` or `develop` branches
- Pull requests to `main` branch
- Weekly scheduled runs (Monday 6 AM UTC)

**Jobs:**
- **Python Quality**: Black formatting, isort imports, Flake8 linting, MyPy type checking
- **JavaScript Quality**: ESLint, Prettier, TypeScript checking
- **Docker Security**: Trivy vulnerability scanning
- **Security Testing**: SQL injection and XSS testing
- **Complexity Analysis**: Cyclomatic complexity and maintainability index
- **Performance Analysis**: Benchmark testing
- **Documentation Check**: Verify documentation completeness

## Environment Setup

### Required Secrets

Add these secrets in your GitHub repository settings:

```bash
# Docker Registry
DOCKER_USERNAME=your-docker-hub-username
DOCKER_PASSWORD=your-docker-hub-token

# Production Deployment (if using automated deployment)
PRODUCTION_SSH_KEY=your-ssh-private-key
PRODUCTION_HOST=192.168.50.215
PRODUCTION_USER=docker

# Notification Services (optional)
SLACK_WEBHOOK_URL=your-slack-webhook-url
DISCORD_WEBHOOK_URL=your-discord-webhook-url
```

### Environment Variables

Configure these in your repository environment settings:

```bash
# Application Settings
DATABASE_URL=postgresql://admin:password@postgres:5432/health_management
REDIS_URL=redis://redis:6379/0
JWT_SECRET=your-production-jwt-secret

# Monitoring
SENTRY_DSN=your-sentry-dsn
LOG_LEVEL=INFO

# External APIs
KOSHA_API_URL=https://www.kosha.or.kr/api
MOEL_API_URL=https://www.moel.go.kr/api
```

## Local Development Workflow

### 1. Setup Development Environment

```bash
# Clone repository
git clone <repository-url>
cd health-management-system

# Copy environment template
cp .env.example .env

# Edit .env with your local settings
vim .env

# Start development environment
docker-compose -f docker-compose.dev.yml up
```

### 2. Development Workflow

```bash
# Create feature branch
git checkout -b feature/new-feature

# Make changes
# ... develop your feature ...

# Run tests locally
./scripts/deploy.sh test

# Commit changes
git add .
git commit -m "feat: add new feature"

# Push and create PR
git push origin feature/new-feature
# Create pull request on GitHub
```

### 3. Pre-commit Hooks (Recommended)

```bash
# Install pre-commit
pip install pre-commit

# Setup hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

## Deployment Strategies

### 1. Automated Deployment

**Staging (Develop Branch):**
- Automatically deployed on every push to `develop`
- Runs integration and E2E tests
- Accessible at staging URL

**Production (Main Branch):**
- Automatically deployed on push to `main`
- Requires all tests to pass
- Creates deployment artifacts

### 2. Manual Deployment

Using the deployment script:

```bash
# Deploy locally
./scripts/deploy.sh local

# Deploy to production (with confirmation)
./scripts/deploy.sh production

# Force deployment (skip confirmation)
./scripts/deploy.sh production --force

# Deploy with cleanup
./scripts/deploy.sh production --cleanup

# Rollback deployment
./scripts/deploy.sh rollback
```

### 3. Release Deployment

```bash
# Create and push a tag
git tag -a v1.2.3 -m "Release version 1.2.3"
git push origin v1.2.3

# This triggers:
# 1. Release workflow
# 2. Docker image build and push
# 3. GitHub release creation
# 4. Automatic production deployment
```

## Monitoring and Alerting

### 1. Health Monitoring

The monitoring script provides comprehensive health checks:

```bash
# Run full health monitoring
./scripts/monitor.sh

# Check specific components
./scripts/monitor.sh status    # Service status only
./scripts/monitor.sh health    # Health endpoint only
./scripts/monitor.sh metrics   # System metrics only
./scripts/monitor.sh database  # Database connectivity
./scripts/monitor.sh redis     # Redis connectivity
```

### 2. Automated Monitoring

Set up cron jobs for continuous monitoring:

```bash
# Add to crontab
crontab -e

# Run health check every 5 minutes
*/5 * * * * /path/to/project/scripts/monitor.sh --quiet

# Generate daily health report
0 8 * * * /path/to/project/scripts/monitor.sh report
```

### 3. Log Analysis

Monitor application logs for issues:

```bash
# View recent logs
docker-compose logs --tail=100 --follow

# Check for errors
./scripts/monitor.sh logs

# View specific service logs
docker-compose logs health-app
docker-compose logs postgres
docker-compose logs redis
```

## Security Considerations

### 1. Secret Management

- Store sensitive data in GitHub Secrets
- Use environment variables for configuration
- Never commit secrets to repository
- Rotate secrets regularly

### 2. Container Security

- Use official base images
- Scan images for vulnerabilities (Trivy)
- Keep dependencies updated
- Run containers as non-root user

### 3. Network Security

- Use HTTPS in production
- Implement proper CORS policies
- Secure database connections
- Use firewall rules

## Performance Optimization

### 1. Build Optimization

- Multi-stage Docker builds
- Build caching with GitHub Actions
- Optimized image layers
- Minimal production images

### 2. Testing Optimization

- Parallel test execution
- Test result caching
- Selective test running
- Performance benchmarking

### 3. Deployment Optimization

- Blue-green deployments
- Rolling updates
- Health checks during deployment
- Automatic rollback on failure

## Troubleshooting

### Common Issues

1. **Build Failures**
   ```bash
   # Check build logs
   docker-compose logs --tail=50
   
   # Rebuild without cache
   docker-compose build --no-cache
   ```

2. **Test Failures**
   ```bash
   # Run tests locally
   ./scripts/deploy.sh test
   
   # Run specific test file
   pytest tests/test_specific.py -v
   ```

3. **Deployment Issues**
   ```bash
   # Check deployment status
   ./scripts/monitor.sh status
   
   # View recent logs
   ./scripts/monitor.sh logs
   
   # Rollback if needed
   ./scripts/deploy.sh rollback
   ```

4. **Performance Issues**
   ```bash
   # Check system metrics
   ./scripts/monitor.sh metrics
   
   # Run performance tests
   pytest tests/test_performance.py -v
   ```

### Getting Help

1. Check GitHub Actions logs for detailed error messages
2. Review application logs using monitoring script
3. Verify environment configuration
4. Check resource usage and limits
5. Review security scan results

## Best Practices

### 1. Code Quality

- Write comprehensive tests (aim for >80% coverage)
- Use type hints in Python code
- Follow consistent code formatting (Black, Prettier)
- Write meaningful commit messages
- Keep functions and classes small and focused

### 2. Testing

- Write unit tests for all business logic
- Include integration tests for API endpoints
- Add performance tests for critical paths
- Test security features thoroughly
- Mock external dependencies

### 3. Deployment

- Always test changes locally first
- Use staging environment for integration testing
- Deploy during low-traffic periods
- Monitor system health after deployment
- Have rollback plan ready

### 4. Security

- Keep dependencies updated
- Regular security scans
- Follow principle of least privilege
- Validate all inputs
- Encrypt sensitive data

## Metrics and KPIs

### 1. Pipeline Metrics

- Build success rate
- Test coverage percentage
- Security scan results
- Deployment frequency
- Time to deployment

### 2. Application Metrics

- Response times
- Error rates
- System resource usage
- Database performance
- Cache hit rates

### 3. Business Metrics

- User satisfaction
- Feature adoption
- System availability
- Bug resolution time
- Security incident count

## Future Enhancements

### 1. Pipeline Improvements

- [ ] Add automated performance regression testing
- [ ] Implement canary deployments
- [ ] Add automated dependency updates
- [ ] Enhance security scanning with SAST/DAST
- [ ] Add infrastructure as code (Terraform)

### 2. Monitoring Enhancements

- [ ] Integrate with external monitoring (Prometheus/Grafana)
- [ ] Add real-time alerting (PagerDuty, Slack)
- [ ] Implement distributed tracing
- [ ] Add business metrics dashboards
- [ ] Enhance log aggregation and analysis

### 3. Security Improvements

- [ ] Implement certificate management
- [ ] Add vulnerability scanning in dependencies
- [ ] Enhance secrets management
- [ ] Add compliance checking
- [ ] Implement security testing automation