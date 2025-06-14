# 🚀 Contributing to py-pglite

**Welcome!** We built py-pglite with a **Vite-style development experience** - instant setup, fast feedback, and easy maintenance.

## ⚡ **Quick Start** (30 seconds)

```bash
# Clone and setup
git clone https://github.com/wey-gu/py-pglite.git
cd py-pglite

# Install dependencies (choose your package manager)
make install          # Standard pip
# OR
PDM_RUN_CWD=. make install    # PDM
# OR  
UV=1 make install            # UV

# Run full development workflow (like CI)
make dev
```

**That's it!** You're ready to contribute.

---

## 🎯 **Development Commands**

We use **one unified script** that mirrors CI exactly:

### **Core Commands**

```bash
make dev         # Full workflow (linting + tests + examples)
make test        # Run tests only  
make examples    # Run examples only
make lint        # Run linting only
make quick       # Quick checks during development
```

### **Utility Commands**

```bash
make install     # Install in development mode
make clean       # Clean build artifacts  
make fmt         # Auto-fix formatting
make status      # Show project status
```

### **Direct Script Usage**

```bash
# Use the script directly for more control
python scripts/dev.py              # Full workflow
python scripts/dev.py --quick      # Quick checks  
python scripts/dev.py --test       # Tests only
python scripts/dev.py --examples   # Examples only
python scripts/dev.py --lint       # Linting only
```

### **📦 Package Manager Support**

py-pglite supports modern Python package managers:

```bash
# Standard pip (default)
make dev

# PDM (Project Dependency Manager)
PDM_RUN_CWD=. make dev

# UV (Ultra-fast Python package installer)
UV=1 make dev
```

**Auto-detection:** The development script automatically detects your package manager based on environment variables and uses the appropriate commands.

---

## 🔥 **Development Workflow**

### **1. Quick Development Loop**

```bash
# Make your changes
vim py_pglite/manager.py

# Quick validation
make quick              # ~10s: linting + imports

# Full validation  
make dev                # ~30s: everything (like CI)
```

### **2. Testing Specific Components**

```bash
make test               # All tests
make examples           # All examples  
pytest tests/test_core_manager.py -v    # Specific test
```

### **3. Before Committing**

```bash
make dev                # Full workflow
make fmt                # Auto-fix formatting
```

**Local `make dev` === CI pipeline** - if it passes locally, it passes in CI!

---

## 📁 **Project Structure**

```bash
py-pglite/
├── py_pglite/                    # 📦 Core package
│   ├── __init__.py              #    Public API
│   ├── manager.py               #    Framework-agnostic PGlite management
│   ├── config.py                #    Robust configuration system
│   ├── utils.py                 #    Framework-agnostic utilities
│   ├── sqlalchemy/              #    SQLAlchemy integration
│   │   ├── manager.py           #    Enhanced SQLAlchemy manager
│   │   ├── fixtures.py          #    Pytest fixtures
│   │   └── utils.py             #    SQLAlchemy utilities
│   ├── django/                  #    Django integration  
│   │   ├── backend.py           #    Custom database backend
│   │   ├── fixtures.py          #    Django fixtures
│   │   └── utils.py             #    Django utilities
│   ├── pytest_plugin.py         #    Auto-discovery pytest plugin
│   └── extensions.py            #    🆕 Extension registry (e.g., pgvector)
│
├── tests/                       # 🧪 Core tests (88 tests)
│   ├── test_core_manager.py     #    Manager lifecycle & process management
│   ├── test_advanced.py         #    Advanced usage patterns
│   ├── test_configuration.py    #    🆕 Configuration validation & edge cases
│   ├── test_connection_management.py # 🆕 Connection pooling & lifecycle
│   ├── test_reliability.py      #    🆕 Error recovery & resilience
│   ├── test_django_backend.py   #    🆕 Django backend & decoupling
│   ├── test_fastapi_integration.py #  FastAPI patterns
│   ├── test_framework_isolation.py # Framework isolation validation
│   └── test_extensions.py       #    🆕 Extension tests (e.g., pgvector)
│
├── examples/                    # 📚 Examples & demos (51 tests)
│   ├── quickstart/              #    ⚡ Instant demos
│   │   ├── demo_instant.py      #    5-line PostgreSQL demo
│   │   ├── simple_fastapi.py    #    FastAPI integration
│   │   └── simple_performance.py #   Performance comparison
│   ├── features/                #    🆕 Advanced feature examples
│   │   └── test_pgvector_rag.py #    pgvector RAG example
│   └── testing-patterns/        #    🧪 Production examples
│       ├── sqlalchemy/          #    SQLAlchemy patterns (2 tests)
│       ├── django/              #    Django patterns (10 tests)
│       └── test_fixtures_showcase.py # Advanced patterns (8 tests)
│
├── scripts/                     # 🔧 Development tools
│   └── dev.py                   #    Unified development script
│
└── Makefile                     # 🎯 Convenience commands
```

---

## 🧪 **Testing Strategy**

### **Comprehensive Test Coverage (139 Total Tests)**

**Core Tests** (`tests/` - 88 tests)

- **🏗️ Manager lifecycle** (`test_core_manager.py`) - Process management, configuration
- **⚙️ Configuration validation** (`test_configuration.py`) - Edge cases, validation, performance
- **🔗 Connection management** (`test_connection_management.py`) - Pooling, lifecycle, concurrency
- **🛡️ Reliability & recovery** (`test_reliability.py`) - Error handling, process recovery, edge cases
- **🌟 Django backend** (`test_django_backend.py`) - Django integration, decoupling validation
- **🚀 FastAPI integration** (`test_fastapi_integration.py`) - REST API patterns
- **🔀 Framework isolation** (`test_framework_isolation.py`) - SQLAlchemy/Django separation
- **💎 Advanced features** (`test_advanced.py`) - Complex scenarios, manual management

**Example Tests** (`examples/` - 51 tests)

- **🎯 SQLAlchemy patterns** (2 tests) - Real ORM usage, modern SQLAlchemy 2.0
- **⭐ Django patterns** (10 tests) - Django ORM, pytest-django, advanced features
- **🎪 Advanced patterns** (8 tests) - Performance, PostgreSQL features, transactions
- **⚡ Quickstart validation** (31 tests) - User experience, FastAPI, utilities

### **Quality Assurance Features**

```bash
# Framework isolation validation
pytest -m sqlalchemy -p no:django     # Pure SQLAlchemy (no Django bleeding)
pytest -m django -p no:sqlalchemy     # Pure Django (no SQLAlchemy bleeding)

# Comprehensive coverage areas
pytest tests/test_configuration.py    # Config validation & edge cases
pytest tests/test_reliability.py      # Error recovery & resilience
pytest tests/test_connection_management.py # Connection pooling & cleanup

# Real-world scenario validation
pytest examples/testing-patterns/     # Production usage patterns
```

### **Battle-Tested Scenarios**

Our test suite validates these critical scenarios:

- ✅ **Process recovery** - Manager restart, cleanup, resource management
- ✅ **Connection storms** - Concurrent access, pool exhaustion, timeout handling
- ✅ **Memory stability** - Long-running suites, large datasets, cleanup validation
- ✅ **Unicode data** - International character sets, special characters
- ✅ **Framework decoupling** - Zero bleeding between SQLAlchemy/Django components
- ✅ **Configuration robustness** - Edge cases, validation, invalid inputs
- ✅ **Production patterns** - FastAPI + SQLAlchemy, Django models, complex queries

### **Framework Isolation Testing**

```bash
# Test SQLAlchemy isolation
pytest examples/testing-patterns/sqlalchemy/ -p no:django

# Test Django isolation  
pytest examples/testing-patterns/django/ -p no:sqlalchemy

# Test framework coexistence
pytest tests/test_framework_isolation.py

# Test decoupling fix
pytest tests/test_django_backend.py::TestDjangoBackendDecoupling
```

---

## 🎨 **Code Style**

We use **Ruff** for linting and formatting:

```bash
make lint               # Check style
make fmt                # Auto-fix formatting
ruff check py_pglite/   # Manual check
ruff format py_pglite/  # Manual format
```

**Style Guide:**

- **PEP 8** compliant
- **Type hints** for public APIs
- **Docstrings** for public functions
- **f-strings** for formatting
- **pathlib** over os.path

---

## 🚀 **Adding Features**

### **1. Core Features** (manager, config)

```bash
# Edit core
vim py_pglite/manager.py

# Test core  
pytest tests/test_core_manager.py -v

# Full validation
make dev
```

### **2. Framework Integration** (SQLAlchemy, Django)

```bash
# Edit integration
vim py_pglite/sqlalchemy/fixtures.py

# Test integration
pytest examples/testing-patterns/sqlalchemy/ -v

# Test isolation
pytest tests/test_framework_isolation.py -v
```

### **3. Examples/Demos**

```bash
# Add example
vim examples/testing-patterns/new_example.py

# Test example
pytest examples/testing-patterns/new_example.py -v

# Test quickstart
python examples/quickstart/demo_instant.py
```

### 4. PostgreSQL Extensions

`py-pglite` supports a growing number of PostgreSQL extensions.

**1. Register the Extension:**
Add the extension's details to `py_pglite/extensions.py`.

```python
# py_pglite/extensions.py
SUPPORTED_EXTENSIONS = {
    "pgvector": {"module": "@electric-sql/pglite/vector", "name": "vector"},
    "new_extension": {"module": "npm-package-name", "name": "js_export_name"},
}
```

**2. Add Optional Dependencies:**
Add any necessary Python client libraries to `pyproject.toml` under the `[project.optional-dependencies]` section.

```toml
# pyproject.toml
[project.optional-dependencies]
extensions = [
    "pgvector>=0.4.1",
    "numpy>=1.0.0",
    "new-python-dependency>=1.0.0",
]
```

**3. Add a Test:**
Create a new test file in `tests/` to validate the extension's functionality. Use the `@pytest.mark.extensions` marker.

```python
# tests/test_new_extension.py
import pytest

@pytest.mark.extensions
def test_new_extension_feature():
    # ...
```

---

## 📝 **Documentation**

### **README Updates**

- Keep examples **simple and compelling**
- Show **zero-config experience**
- Maintain **Vite-style messaging**

### **Code Documentation**

```python
def new_feature(param: str) -> bool:
    """Short description.
    
    Args:
        param: Parameter description
        
    Returns:
        Description of return value
        
    Example:
        >>> new_feature("test")
        True
    """
```

---

## 🐛 **Issue Workflow**

### **Bug Reports**

1. **Reproduce** with minimal example
2. **Check** which component (core, SQLAlchemy, Django)
3. **Write test** that fails
4. **Fix** the issue  
5. **Validate** with `make dev`

### **Feature Requests**

1. **Discuss** in GitHub issue first
2. **Design** for framework isolation
3. **Implement** with tests
4. **Document** with examples
5. **Validate** full workflow

---

## 🎯 **Design Principles**

### **1. Framework Agnostic Core**

```python
# ✅ Good - no framework dependencies
from py_pglite import PGliteManager

# ❌ Bad - framework-specific in core
from py_pglite.sqlalchemy import SomeHelper
```

### **2. Optional Dependencies**

```python
# ✅ Good - graceful degradation
try:
    from sqlalchemy import Engine
except ImportError:
    Engine = None  # type: ignore
```

### **3. Zero Configuration**

```python
# ✅ Good - works immediately
def test_users(pglite_session):
    user = User(name="Alice")
    pglite_session.add(user)
    # Tables created automatically!

# ❌ Bad - requires manual setup
def test_users(pglite_session):
    Base.metadata.create_all(pglite_session.bind)  # Manual step
```

---

## 🔧 **Known Issues & Solutions**

### **Django Backend Decoupling (Fixed in v0.3.0+)**

**Issue:** Django backend was calling `manager.wait_for_ready()` but the base `PGliteManager` only had `wait_for_ready_basic()`, causing framework coupling.

**Cause:** Django integration was inadvertently depending on SQLAlchemy-specific methods, breaking the framework-agnostic design.

**Solution:** Added `wait_for_ready()` method to base `PGliteManager` that delegates to `wait_for_ready_basic()` for API consistency.

```python
# Now works perfectly across all frameworks
def test_django_backend_ready(db):
    # Django backend uses base manager with consistent API
    manager = get_pglite_manager()
    manager.wait_for_ready()  # ✅ Works in both SQLAlchemy and Django
```

**Validation:** Comprehensive Django backend tests added (`test_django_backend.py`) with 9 tests covering decoupling, imports, and error handling.

### **Connection Timeouts (Fixed in v0.2.0+)**

**Issue:** `psycopg.errors.ConnectionTimeout` when creating tables or running DDL operations.

**Cause:** PGlite's socket server handles one connection at a time. Multiple SQLAlchemy engines caused connection conflicts.

**Solution:** py-pglite now uses a shared engine architecture automatically. All `get_engine()` calls return the same instance, preventing timeouts.

```python
# This now works perfectly - no timeouts!
engine = manager.get_engine()
SQLModel.metadata.create_all(engine)  # ✅ Works
```

**Additional Improvements:**

- **Connection pooling** - StaticPool and NullPool support with proper configuration
- **Timeout handling** - Configurable timeouts with robust retry logic
- **Process recovery** - Automatic cleanup and restart on failures
- **Resource management** - Comprehensive socket and memory cleanup

### **Framework Isolation (Enhanced in v0.3.0+)**

**Validation:** py-pglite now has comprehensive framework isolation testing:

```bash
# These work perfectly without interference
pytest -m sqlalchemy -p no:django     # Pure SQLAlchemy
pytest -m django -p no:sqlalchemy     # Pure Django  
pytest tests/test_framework_isolation.py # Validation suite
```

**Coverage:** 139 total tests including edge cases, error recovery, and production scenarios.

---

## 🎉 **Release Process**

### **Local Validation**

```bash
make dev                # Full workflow passes
make clean              # Clean build
python scripts/dev.py   # Final check
```

### **CI Validation**

- **All Python versions** (3.10, 3.11, 3.12, 3.13)
- **All frameworks** (SQLAlchemy, Django, FastAPI)
- **All examples** pass
- **Package builds** correctly

### **Release**

```bash
git tag v0.3.0          # Create tag
git push origin v0.3.0  # Trigger release workflow
```

CI automatically:

- ✅ Runs full test suite
- ✅ Builds package
- ✅ Publishes to PyPI
- ✅ Creates GitHub release

---

## 💝 **Community**

### **Getting Help**

- 🐛 **GitHub Issues** - Bug reports, feature requests
- 💬 **Discussions** - Questions, ideas, feedback
- 📧 **Direct contact** - <maintainer@py-pglite.com>

### **Contributing**

- 🔀 **Pull requests** welcome!
- 📝 **Documentation** improvements
- 🧪 **Test coverage** enhancements  
- 🎨 **Example** additions

---

**Thank you for contributing to py-pglite!**

Together we're building the **Vite of database testing** - instant, powerful, and delightful to use. 🚀
