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

```
py-pglite/
├── py_pglite/                 # 📦 Core package
│   ├── __init__.py           #    Public API
│   ├── manager.py            #    PGlite management
│   ├── config.py             #    Configuration
│   ├── sqlalchemy/           #    SQLAlchemy integration
│   ├── django/               #    Django integration  
│   └── pytest_plugin.py     #    Pytest plugin
│
├── tests/                    # 🧪 Core tests
│   ├── test_core_manager.py  #    Manager tests
│   ├── test_advanced.py      #    Advanced features
│   └── test_framework_isolation.py # Framework isolation
│
├── examples/                 # 📚 Examples & demos
│   ├── quickstart/           #    ⚡ Instant demos
│   └── testing-patterns/     #    🧪 Production examples
│
├── scripts/                  # 🔧 Development tools
│   └── dev.py               #    Unified development script
│
└── Makefile                  # 🎯 Convenience commands
```

---

## 🧪 **Testing Strategy**

### **Core Tests** (`tests/`)

- **Manager lifecycle** - Start/stop, configuration
- **Framework isolation** - SQLAlchemy/Django separation  
- **Advanced features** - Complex scenarios
- **FastAPI integration** - REST API patterns

### **Example Tests** (`examples/`)

- **SQLAlchemy patterns** - Real ORM usage
- **Django patterns** - Real Django models
- **Quickstart demos** - User experience validation

### **Framework Isolation**

```bash
# Test SQLAlchemy alone
pytest examples/testing-patterns/sqlalchemy/ -p no:django

# Test Django alone  
pytest examples/testing-patterns/django/

# Test framework coexistence
pytest tests/test_framework_isolation.py
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
