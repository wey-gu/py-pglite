# 🧪 py-pglite Test Suite

Comprehensive test coverage for py-pglite ensuring reliability, performance, and framework isolation.

## 📊 Test Organization

Our test suite is organized by functionality and scope to ensure comprehensive coverage:

```
tests/
├── test_core_manager.py         # Core PGliteManager functionality
├── test_framework_isolation.py  # Framework independence & isolation
├── test_advanced.py            # Advanced usage patterns & edge cases
├── test_fastapi_integration.py # FastAPI integration testing
└── README.md                   # This documentation
```

## 🎯 Test Categories

### 🔧 **Core Manager Tests** (`test_core_manager.py`)

Tests fundamental PGliteManager functionality:

- **Configuration Testing**
  - Default and custom configurations
  - Connection string generation
  - Working directory management
  - Timeout and cleanup settings

- **Lifecycle Management**
  - Start/stop/restart functionality
  - Context manager behavior
  - Double operation safety
  - Process management

- **Engine Creation**
  - SQLAlchemy engine generation
  - Custom engine parameters
  - Multiple engine handling
  - Error conditions

- **Error Handling**
  - Missing dependencies
  - Invalid configurations
  - Process failures
  - Resource cleanup

**Run:** `pytest tests/test_core_manager.py -v`

### 🔀 **Framework Isolation Tests** (`test_framework_isolation.py`)

Ensures true framework independence:

- **Core Independence**
  - Works without any frameworks
  - Framework-agnostic utilities
  - Clean imports

- **SQLAlchemy Isolation**
  - No Django contamination
  - Independent operation
  - Legacy utils isolation

- **Django Isolation**
  - No SQLAlchemy contamination
  - Backend independence
  - Framework-agnostic backend

- **Framework Coexistence**
  - Sequential usage
  - Import order independence
  - Optional dependencies

**Run:** `pytest tests/test_framework_isolation.py -v`

### 🚀 **Advanced Tests** (`test_advanced.py`)

Complex usage patterns and edge cases:

- **Custom Configuration**
- **Manual Lifecycle Management**
- **Multiple Sessions**
- **Concurrent Operations**
- **Error Scenarios**

**Run:** `pytest tests/test_advanced.py -v`

### 🌐 **FastAPI Integration** (`test_fastapi_integration.py`)

Real-world FastAPI integration:

- **API Endpoint Testing**
- **Database Dependencies**
- **CRUD Operations**
- **Error Handling**
- **Manual Setup Patterns**

**Run:** `pytest tests/test_fastapi_integration.py -v`

## 📈 Coverage Goals

Our test suite aims for comprehensive coverage across these dimensions:

### ✅ **Functional Coverage**

- ✅ All public APIs tested
- ✅ All configuration options covered
- ✅ Error conditions handled
- ✅ Edge cases identified

### ✅ **Framework Coverage**

- ✅ Core functionality (framework-agnostic)
- ✅ SQLAlchemy integration
- ✅ Django integration
- ✅ Framework isolation verified

### ✅ **Integration Coverage**

- ✅ FastAPI integration
- ✅ Real-world usage patterns
- ✅ Production scenarios
- ✅ Performance characteristics

### ✅ **Error Coverage**

- ✅ Missing dependencies
- ✅ Invalid configurations
- ✅ Network failures
- ✅ Resource exhaustion
- ✅ Process management issues

## 🎮 Running Tests

### **Run All Tests**

```bash
# Complete test suite
pytest tests/ -v

# With coverage report
pytest tests/ --cov=py_pglite --cov-report=html
```

### **Run by Category**

```bash
# Core functionality
pytest tests/test_core_manager.py -v

# Framework isolation
pytest tests/test_framework_isolation.py -v

# Advanced patterns
pytest tests/test_advanced.py -v

# FastAPI integration
pytest tests/test_fastapi_integration.py -v
```

### **Run by Test Type**

```bash
# Quick smoke tests
pytest tests/ -m "not slow" -v

# Performance tests
pytest tests/ -k "performance" -v

# Error handling tests
pytest tests/ -k "error" -v

# Integration tests
pytest tests/ -k "integration" -v
```

### **Run with Different Configurations**

```bash
# Verbose output
pytest tests/ -v -s

# Stop on first failure
pytest tests/ -x

# Run specific test
pytest tests/test_core_manager.py::TestPGliteConfig::test_default_config -v

# Parallel execution (if pytest-xdist installed)
pytest tests/ -n auto
```

## 🎯 Test Quality Metrics

### **Performance Benchmarks**

- ✅ **Startup Time**: < 3 seconds (typical: ~1.5s)
- ✅ **Test Suite Time**: < 60 seconds for full suite
- ✅ **Memory Usage**: < 100MB during test execution
- ✅ **Resource Cleanup**: Zero leaked processes/files

### **Reliability Metrics**

- ✅ **Flake Rate**: < 1% (tests should be deterministic)
- ✅ **Framework Isolation**: 100% (no cross-contamination)
- ✅ **Error Recovery**: 100% (graceful failure handling)
- ✅ **Resource Management**: 100% cleanup rate

### **Coverage Targets**

- ✅ **Line Coverage**: > 90%
- ✅ **Branch Coverage**: > 85%
- ✅ **Function Coverage**: 100%
- ✅ **Integration Coverage**: All framework combinations

## 🔧 Test Configuration

### **Pytest Configuration** (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "core: marks tests as core functionality tests",
    "utils: marks tests as utility function tests",
]
addopts = [
    "--strict-markers",
    "--tb=short",
    "-ra",
]
```

### **Test Fixtures** (Provided by pytest plugin)

- `pglite_manager`: Session-scoped PGlite manager
- `pglite_engine`: SQLAlchemy engine connected to PGlite
- `pglite_session`: SQLAlchemy session for testing

## 🧪 Testing Best Practices

### **Test Structure**

1. **Arrange**: Set up test data and conditions
2. **Act**: Execute the operation being tested
3. **Assert**: Verify expected outcomes
4. **Cleanup**: Ensure resources are properly cleaned up

### **Test Naming**

```python
def test_[component]_[scenario]_[expected_outcome]():
    """Clear description of what is being tested."""
```

### **Test Organization**

- Group related tests in classes
- Use descriptive test class names
- Keep tests focused and independent
- Use fixtures for common setup

### **Error Testing**

- Test both success and failure paths
- Use `pytest.raises()` for expected exceptions
- Verify error messages are helpful
- Test edge cases and boundary conditions

## 🔍 Debugging Tests

### **Common Issues**

1. **Port Conflicts**: Use different ports or cleanup properly
2. **Resource Leaks**: Check process/file cleanup
3. **Framework Contamination**: Verify import isolation
4. **Timing Issues**: Add appropriate waits for async operations

### **Debug Commands**

```bash
# Run with debugging
pytest tests/ -v -s --pdb

# Show test output
pytest tests/ -v -s --capture=no

# Run single test with full output
pytest tests/test_core_manager.py::TestPGliteConfig::test_default_config -v -s
```

## 🎉 Contributing Tests

### **Adding New Tests**

1. Choose appropriate test file based on functionality
2. Follow existing naming conventions
3. Ensure tests are independent and reproducible
4. Add appropriate markers for categorization
5. Update this documentation if adding new categories

### **Test Review Checklist**

- [ ] Tests are deterministic (no random failures)
- [ ] Resources are properly cleaned up
- [ ] Error cases are covered
- [ ] Integration with existing fixtures
- [ ] Performance impact is minimal
- [ ] Documentation is updated

**Our comprehensive test suite ensures py-pglite is reliable, performant, and truly framework-agnostic! 🚀**
