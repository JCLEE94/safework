# CI/CD Pipeline Integration Testing

This directory contains integration tests for the SafeWork Pro CI/CD pipeline, implementing inline testing similar to Rust's approach.

## 🏗️ Structure

```
.github/
├── scripts/                    # Testable shell scripts
│   ├── install-claude.sh      # Claude Code installation with tests
│   ├── check-oauth.sh         # OAuth verification with tests
│   └── verify-deployment.sh   # Deployment health checks
├── workflows/
│   ├── main-integrated.yml    # Main CI/CD pipeline
│   └── test-pipeline.yml      # Pipeline testing workflow
└── README-TESTING.md          # This file

tests/cicd/
└── test_pipeline_integration.py  # Python integration tests

Makefile.cicd                    # Testing commands
```

## 🧪 Testing Philosophy

Following Rust's inline testing approach, our CI/CD tests are:

1. **Co-located**: Tests live alongside the code they test
2. **Self-documenting**: Each script contains its own tests
3. **Executable**: Tests can run independently or as part of a suite
4. **Integrated**: Tests validate real integration points

## 🚀 Quick Start

### Run All Tests
```bash
make -f Makefile.cicd test-local
```

### Test Specific Components
```bash
# Test workflow syntax
make -f Makefile.cicd test-workflows

# Test shell scripts
make -f Makefile.cicd test-scripts

# Test service containers
make -f Makefile.cicd test-containers

# Test deployment verification
make -f Makefile.cicd test-deployment
```

### Run in GitHub Actions
```bash
# Trigger pipeline tests
make -f Makefile.cicd test-pipeline
```

## 📋 Test Categories

### 1. Script Tests (Inline)
Each shell script contains self-tests:

```bash
# Example from install-claude.sh
test_claude_exists() {
    if command -v claude &> /dev/null; then
        echo "✅ Claude Code CLI found"
        return 0
    else
        echo "❌ Claude Code CLI not found"
        return 1
    fi
}
```

### 2. Integration Tests (Python)
Comprehensive tests for pipeline components:

```python
def test_service_container_startup(self, service: ServiceContainer) -> bool:
    """Test service container startup and health check"""
    # Start container, check health, cleanup
```

### 3. Workflow Tests (YAML)
Automated validation of GitHub Actions workflows:

```yaml
validate-workflows:
  name: Validate Workflow Syntax
  steps:
    - name: Run workflow validation tests
      run: python tests/cicd/test_pipeline_integration.py
```

## 🔧 Writing New Tests

### Adding Script Tests
1. Add test functions to your script:
```bash
test_my_feature() {
    # Test implementation
    [ condition ] && echo "✅ Pass" || echo "❌ Fail"
}
```

2. Add to the test runner:
```bash
run_tests() {
    test_my_feature
    # Report results
}
```

### Adding Integration Tests
1. Add test method to `PipelineIntegrationTest`:
```python
def test_new_feature(self) -> bool:
    """Test description with doctest example"""
    # Implementation
```

2. Include in `run_all_tests()` method

### Adding Workflow Tests
1. Add job to `test-pipeline.yml`:
```yaml
test-new-feature:
  name: Test New Feature
  steps:
    - name: Run feature test
      run: |
        # Test commands
```

## 🏃 Continuous Testing

### Automated Triggers
- **PR Changes**: Tests run on workflow/script changes
- **Nightly**: Full integration tests at 2 AM UTC
- **Manual**: Use workflow_dispatch for on-demand testing

### Local Development
```bash
# Watch mode for continuous testing
make -f Makefile.cicd watch

# Generate coverage report
make -f Makefile.cicd coverage
```

## 🔍 Debugging Failed Tests

### Check Logs
```bash
# View specific job logs
gh run view <run-id> --job <job-id> --log

# View failed logs only
gh run view <run-id> --log-failed
```

### Run Tests Locally
```bash
# Run specific test
python -c "from tests.cicd.test_pipeline_integration import PipelineIntegrationTest; \
          test = PipelineIntegrationTest(); \
          test.test_docker_build_process()"
```

### Enable Debug Mode
```bash
# Set debug environment variable
export ACTIONS_STEP_DEBUG=true
export ACTIONS_RUNNER_DEBUG=true
```

## 📊 Test Coverage

Current test coverage includes:

- ✅ Workflow syntax validation
- ✅ Service container startup (PostgreSQL, Redis)
- ✅ Docker build process
- ✅ Registry connectivity
- ✅ Claude Code installation
- ✅ OAuth verification
- ✅ Deployment health checks
- ✅ Security scanning
- ✅ Concurrent workflow handling

## 🚨 Common Issues

### Service Container Failures
- Check port conflicts (25432 for PostgreSQL, 26379 for Redis)
- Verify Docker daemon is running
- Ensure sufficient resources

### Claude OAuth Issues
- Manual authentication required on self-hosted runners
- Run `claude auth login` on the runner machine

### Registry Access
- Verify registry credentials in GitHub Secrets
- Check network connectivity to registry.jclee.me

## 🔐 Security Considerations

- Scripts validate inputs to prevent injection
- Sensitive data masked in logs
- OAuth tokens never exposed
- Registry credentials stored as secrets

## 📈 Future Improvements

- [ ] Add performance benchmarks
- [ ] Implement mutation testing
- [ ] Add visual regression tests
- [ ] Create test result dashboard
- [ ] Add load testing for deployments

## 🤝 Contributing

When adding new CI/CD features:

1. Write inline tests in scripts
2. Add integration tests in Python
3. Create workflow tests
4. Update this documentation
5. Run full test suite before PR

---

**Remember**: A well-tested pipeline is a reliable pipeline! 🚀