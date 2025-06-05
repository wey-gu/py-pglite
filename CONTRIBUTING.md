# 🛠️ Hacking py-pglite

Thank you for your interest in contributing to py-pglite! This guide will help you get started.

## Development Setup

1. **Clone the repository:**

   ```bash
   git clone https://github.com/wey-gu/py-pglite.git
   cd py-pglite
   ```

2. **Install in development mode:**

   ```bash
   pip install -e ".[dev]"
   pip install types-psutil  # for mypy type checking
   ```

3. **Install Node.js:** PGlite requires Node.js (version 18 or later)

## Code Quality

We use several tools to maintain code quality:

- **Ruff**: For linting and formatting
- **MyPy**: For static type checking
- **Pytest**: For testing

Run all checks:

```bash
# Linting and formatting
ruff check py_pglite/
ruff format py_pglite/

# Type checking
mypy py_pglite/

# Tests with coverage
pytest examples/ --cov=py_pglite --cov-report=term-missing -v
```

## Testing

- Tests are located in the `examples/` directory as they serve as both tests and usage examples
- All tests should pass before submitting a PR
- New features should include tests
- Aim for high test coverage

## Pull Request Process

1. **Fork the repository** and create a feature branch
2. **Make your changes** following the code style guidelines
3. **Add or update tests** for any new functionality
4. **Ensure all tests pass** and code quality checks pass
5. **Update documentation** if needed
6. **Submit a pull request** with a clear description of your changes

## GitHub Actions Workflows

### CI Pipeline (`.github/workflows/ci.yml`)

Runs on every push and pull request:

- **Matrix testing**: Python 3.10-3.12 × Node.js 18-20
- **Code quality**: Ruff linting/formatting, MyPy type checking
- **Testing**: Full test suite with coverage reporting
- **Security**: Safety and Bandit security scans
- **Package testing**: Build and installation verification

### Release Pipeline (`.github/workflows/release.yml`)

Triggered by version tags (e.g., `v0.2.0`):

- **Pre-release testing**: Full CI pipeline
- **PyPI publication**: Automated release to PyPI using trusted publishing
- **GitHub release**: Creates GitHub release with built packages

## Making a Release

Releases are automated through GitHub Actions. To make a release:

1. **Update the version** in `py_pglite/__init__.py`:

   ```python
   __version__ = "0.2.0"  # Update version number
   ```

2. **Commit the version change:**

   ```bash
   git add py_pglite/__init__.py
   git commit -m "Bump version to 0.2.0"
   git push origin main
   ```

3. **Create and push a version tag:**

   ```bash
   git tag v0.2.0
   git push origin v0.2.0
   ```

4. **GitHub Actions will automatically:**
   - Run the full test suite
   - Build the package
   - Publish to PyPI
   - Create a GitHub release

### Version Synchronization

The package maintains version synchronization between Python and npm packages:

- Python version is defined in `py_pglite/__init__.py`
- npm package.json version is automatically updated from Python version
- Both packages are always released with the same version number

## PyPI Trusted Publishing Setup

The release workflow uses PyPI's trusted publishing feature for secure, automated releases. Repository maintainers need to:

1. **Set up PyPI trusted publishing:**
   - Go to PyPI project settings
   - Add GitHub as a trusted publisher
   - Configure: `wey-gu/py-pglite` repository, `release.yml` workflow

2. **Configure GitHub environment:**
   - Create a `pypi` environment in repository settings
   - Set environment protection rules if desired

## Code Style Guidelines

- **Follow PEP 8** (enforced by Ruff)
- **Use type hints** everywhere (enforced by MyPy strict mode)
- **Write descriptive docstrings** for public APIs
- **Use modern Python features** (Union → |, etc.)
- **Keep lines under 88 characters**

## Documentation

- **README.md**: Main documentation with examples
- **Docstrings**: All public functions and classes
- **Examples**: Comprehensive examples that also serve as tests
- **Type hints**: Complete type coverage for better developer experience

## Questions?

- **Open an issue** for bugs or feature requests
- **Start a discussion** for questions or ideas
- **Check existing issues** before creating new ones

Thank you for contributing! 🎉
