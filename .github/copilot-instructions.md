# py-pglite Development Instructions

**Always follow these instructions first and only fall back to additional search and context gathering if the information here is incomplete or found to be in error.**

## Project Overview
py-pglite is a Python testing library providing a Pythonic interface for PGlite - instant, zero-config PostgreSQL for testing. It supports SQLAlchemy, Django, FastAPI, asyncpg, and other PostgreSQL clients with real PostgreSQL features including JSON, arrays, and extensions like pgvector.

## Essential Setup - Bootstrap Everything First

**CRITICAL**: Always run these commands in exact order before any development work:

```bash
# Install uv package manager (if not available)
pip install uv

# Install all dependencies 
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Verify installation
make status
```

**Installation takes 2-3 minutes. Dependencies include Node.js integration for PGlite.**

## Core Development Commands - VALIDATED TO WORK

### Quick Development Loop (~10 seconds)
```bash
# Basic validation - imports and linting
uv run python -c "import py_pglite; from py_pglite import PGliteManager, PGliteConfig; print('✅ All imports working')"
uv run ruff check src/ tests/ examples/ --no-fix
uv run ruff format --check src/ tests/ examples/
```

### Full Test Suite - NEVER CANCEL
```bash
make test          # 5m 34s - 634 tests - NEVER CANCEL, set timeout 10+ minutes
make examples      # 1m 57s - 67 examples - NEVER CANCEL, set timeout 5+ minutes
```

**CRITICAL TIMING**: Tests take 5+ minutes, examples take 2+ minutes. These are NOT hanging - wait for completion.

### Full Development Workflow
```bash
make dev           # Full workflow: install + lint + examples + test
```

**NOTE**: `make dev` may fail due to pre-commit network timeouts. Use individual commands instead:
```bash
uv sync
uv run ruff check src/ tests/ examples/ --no-fix
make examples
make test
```

### Individual Commands
```bash
make install       # uv sync - dependency installation
make fmt           # Auto-fix formatting (<1 second)
make clean         # Clean build artifacts
make lint          # Pre-commit hooks (may fail due to network)
```

## Validation Scenarios - ALWAYS TEST THESE

After making any changes, always run these validation scenarios:

### 1. Basic Functionality Test
```bash
# Must work - validates core functionality
uv run python examples/quickstart/demo_instant.py
```
This tests real PostgreSQL features: JSON, arrays, window functions, table operations.

### 2. Framework-Specific Testing
```bash
# SQLAlchemy patterns
uv run pytest -m sqlalchemy examples/testing-patterns/sqlalchemy/ -v

# Django patterns  
uv run pytest -m django examples/testing-patterns/django/lightweight/ -v

# Core manager functionality
uv run pytest tests/test_core_manager.py -v
```

### 3. Before Committing - MANDATORY
```bash
make fmt                # Auto-fix formatting
uv run ruff check src/ tests/ examples/ --no-fix  # Linting
make test               # Full test suite - NEVER CANCEL 5+ minutes
```

## Project Structure and Navigation

### Key Directories
```
src/py_pglite/           # Main package code
├── manager.py           # Core PGlite manager
├── config.py           # Configuration classes
├── sqlalchemy/         # SQLAlchemy integration
├── django/             # Django integration and custom backend
├── fixtures.py         # pytest fixtures
└── pytest_plugin.py   # pytest plugin registration

tests/                  # 634 comprehensive tests
├── test_core_manager.py        # Core functionality
├── test_reliability.py        # Error recovery, timeouts
├── test_configuration.py      # Config validation
├── test_framework_isolation.py # Framework separation

examples/               # 67 working examples
├── quickstart/         # Simple demos
├── testing-patterns/   # Production patterns
│   ├── sqlalchemy/     # SQLAlchemy examples
│   └── django/         # Django examples (lightweight vs full-integration)
```

### Essential Files to Know
- `Makefile` - All development commands
- `CONTRIBUTING.md` - Comprehensive development guide
- `pyproject.toml` - Project configuration, dependencies, tool settings
- `.github/workflows/ci.yml` - CI pipeline (mirrors local `make dev`)

## Build and Package

```bash
# Build package
uv build                # Creates dist/ with wheel and source dist

# Test package installation
python -m pip install dist/*.whl
python -c "import py_pglite; print(f'py-pglite {py_pglite.__version__} ready!')"
```

## Framework Isolation Testing

py-pglite supports multiple frameworks without bleeding:

```bash
# Pure SQLAlchemy (no Django dependencies)
uv run pytest -m sqlalchemy -p no:django

# Pure Django (no SQLAlchemy dependencies)  
uv run pytest -m django -p no:sqlalchemy

# Directory-based isolation
uv run pytest tests/sqlalchemy/
uv run pytest examples/testing-patterns/django/
```

## Known Issues and Workarounds

### Pre-commit Hook Installation Failures
**Issue**: `make quick` and `make dev` may fail with network timeouts during pre-commit installation.

**Workaround**: Use direct ruff commands:
```bash
# Instead of make lint
uv run ruff check src/ tests/ examples/ --no-fix
uv run ruff format src/ tests/ examples/

# Instead of make quick  
uv run python -c "import py_pglite; from py_pglite import PGliteManager, PGliteConfig; print('✅ All imports working')"
uv run ruff check src/ tests/ examples/ --no-fix
```

### MyPy Type Checking
```bash
uv run mypy src/py_pglite
```
**Note**: Some type errors expected due to async/sync interface compatibility. Project uses relaxed mypy settings for mixed framework support.

## Development Workflow Patterns

### Quick Change Validation
```bash
# Make changes to core code
vim src/py_pglite/manager.py

# Quick validation (~30s)
uv run python -c "import py_pglite; print('✅ Import working')"
uv run ruff check src/ --no-fix
uv run pytest tests/test_core_manager.py -v

# Full validation if quick validation passes
make test examples
```

### Adding New Features

#### Core Features (manager, config)
```bash
# Edit and test
vim src/py_pglite/manager.py
uv run pytest tests/test_core_manager.py -v
make test
```

#### Framework Integration (SQLAlchemy, Django)
```bash
# Edit integration
vim src/py_pglite/sqlalchemy/fixtures.py
uv run pytest examples/testing-patterns/sqlalchemy/ -v
uv run pytest tests/test_framework_isolation.py -v
```

#### Examples/Demos
```bash
# Add example
vim examples/testing-patterns/new_example.py
uv run pytest examples/testing-patterns/new_example.py -v
uv run python examples/quickstart/demo_instant.py
```

## Testing Strategy Summary

- **639 Total Tests** (634 in tests/, 67 in examples/)
- **Framework-agnostic core** + **framework-specific integrations**
- **Real PostgreSQL validation** with features like JSON, arrays, extensions
- **Comprehensive error recovery** and timeout handling
- **Production patterns** including FastAPI, Django ORM, SQLAlchemy 2.0

## CI Pipeline Equivalence

**Local `make dev` === CI pipeline**

The CI runs across Python 3.10-3.13 with the same commands. If it passes locally, it passes in CI.

## Package Manager: uv

All commands use uv by default:
- `make install` → `uv sync`  
- `make test` → `uv run pytest tests/`
- `make lint` → `uv run pre-commit run --all-files`

## Required Dependencies

- **Python 3.10+**
- **Node.js** (for PGlite backend)
- **uv package manager** 
- Network access for npm package installation (PGlite dependencies)

## Performance Expectations

- **Quick checks**: <30 seconds
- **Examples**: ~2 minutes
- **Full test suite**: ~5.5 minutes  
- **Dependency installation**: ~2-3 minutes
- **Package build**: <30 seconds

**NEVER CANCEL operations that appear to hang - these are normal durations for a comprehensive PostgreSQL testing library.**