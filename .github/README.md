# GitHub Actions Workflows

This directory contains the CI/CD workflows for py-pglite.

## 🔄 CI Workflow (`.github/workflows/ci.yml`)

**Triggers**: Push to `main`/`develop` branches and all pull requests

**Jobs**:

### 1. **Test Matrix**

- **Python versions**: 3.10, 3.11, 3.12, 3.13
- **Node.js versions**: 22
- **OS**: Ubuntu Latest

**Steps**:

- ✅ Code quality checks (Ruff linting & formatting)
- ✅ Type checking (MyPy)
- ✅ Test suite with coverage reporting
- ✅ Package build verification
- ✅ Coverage upload to Codecov

### 2. **Package Installation Test**

- Tests actual package installation from built wheel
- Verifies imports work correctly after installation

### 3. **Security Scanning**

- **Safety**: Scans dependencies for known vulnerabilities
- **Bandit**: Static security analysis of Python code

## 🚀 Release Workflow (`.github/workflows/release.yml`)

**Triggers**:

- Version tags (`v*`, e.g., `v0.2.0`)
- GitHub releases

**Jobs**:

### 1. **Pre-release Testing**

- Complete test suite
- Code quality verification
- Package build and installation test

### 2. **PyPI Release**

- **Trusted Publishing**: Secure, automated PyPI publishing
- **Environment**: Protected `pypi` environment
- **Permissions**: `id-token: write` for OIDC authentication

### 3. **GitHub Release Creation**

- Automatic GitHub release with built packages
- Release notes generation
- Pre-release detection (alpha/beta/rc versions)

## 🔧 Setup Requirements

### For Repository Maintainers

1. **PyPI Trusted Publishing Setup**:
   - Go to [PyPI project settings](https://pypi.org/manage/project/py-pglite/settings/)
   - Add GitHub as trusted publisher:
     - Owner: `wey-gu`
     - Repository: `py-pglite`
     - Workflow: `release.yml`

2. **GitHub Environment Configuration**:
   - Create `pypi` environment in repository settings
   - Configure protection rules (optional)

3. **Codecov Integration**:
   - Repository automatically uploads coverage
   - No additional setup required for public repos

## 📋 Coverage Configuration

Coverage settings are in `pyproject.toml`:

```toml
[tool.coverage.run]
source = ["py_pglite"]
omit = ["*/tests/*", "*/test_*", "examples/*"]

[tool.coverage.report]
show_missing = true
precision = 2
```

## 🏃‍♂️ Local Development

Run the same checks locally:

```bash
# Full CI pipeline
ruff check py_pglite/
ruff format --check py_pglite/
mypy py_pglite/
pytest examples/ --cov=py_pglite --cov-report=term-missing -v

# Package build test
python -m build
twine check dist/*
```

## 🔖 Making a Release

1. Update version in `py_pglite/__init__.py`
2. Commit and push to main
3. Create and push version tag:

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. GitHub Actions automatically handles the rest!

## 📊 Workflow Status

- [![CI](https://github.com/wey-gu/py-pglite/actions/workflows/ci.yml/badge.svg)](https://github.com/wey-gu/py-pglite/actions/workflows/ci.yml)
- [![Release](https://github.com/wey-gu/py-pglite/actions/workflows/release.yml/badge.svg)](https://github.com/wey-gu/py-pglite/actions/workflows/release.yml)
