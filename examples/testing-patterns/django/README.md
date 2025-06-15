# 🌟 Django + py-pglite Integration Patterns

This directory showcases **two distinct patterns** for integrating Django with py-pglite, each with different strengths and use cases.

## 📋 Pattern Overview

| Pattern | Backend | Connection | Setup | Use Case |
|---------|---------|------------|-------|----------|
| **Lightweight/Socket** | `django.db.backends.postgresql` | Direct socket | Minimal | Quick tests, prototypes |
| **Full Integration/Backend** | `py_pglite.django.backend` | Managed by backend | Full features | Comprehensive testing |

## 🔹 Pattern 1: Lightweight/Socket

**Directory**: `lightweight/`

Uses the standard PostgreSQL backend with direct socket connections to PGlite.

### Pattern 1 ✅ Advantages

- **Minimal setup**: Standard Django + socket connection
- **Fast startup**: Direct connection, no overhead
- **Simple dependencies**: Uses standard Django backend
- **Quick prototyping**: Perfect for rapid development

### 📁 Pattern 1 Files

- `test_socket_basic.py` - Basic Django ORM usage
- `test_socket_advanced.py` - Advanced Django features  
- `test_socket_pytest_django.py` - pytest-django integration

### 🚀 Pattern 1 Quick Start

```python
def test_django_with_socket(configured_django):
    """Uses standard PostgreSQL backend via socket"""
    
    class Product(models.Model):
        name = models.CharField(max_length=100)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        
        class Meta:
            app_label = "example"
    
    # Standard Django operations work perfectly
    product = Product.objects.create(name="Widget", price=29.99)
    assert product.id is not None
```

### ⚙️ Configuration

```python
# In conftest.py - uses configured_django fixture
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",  # Standard backend
        "HOST": socket_directory,  # PGlite socket
        # ... other settings
    }
}
```

## 🔸 Pattern 2: Full Integration/Backend

**Directory**: `full-integration/`

Uses the custom py-pglite Django backend for enhanced features and optimization.

### Pattern 2 ✅ Advantages

- **Enhanced features**: Full py-pglite integration capabilities
- **Backend optimization**: Custom optimizations for testing
- **Advanced JSON support**: Enhanced PostgreSQL JSON features
- **Production-like**: Comprehensive testing environment

### 📁 Pattern 2 Files

- `test_backend_basic.py` - Basic custom backend usage
- `test_backend_advanced.py` - Advanced backend features
- `test_backend_pytest_django.py` - pytest-django with backend

### 🚀 Pattern 2 Quick Start

```python
def test_django_with_backend(django_pglite_db):
    """Uses custom py-pglite backend"""
    
    class Product(models.Model):
        name = models.CharField(max_length=100)
        metadata = models.JSONField(default=dict)  # Enhanced JSON
        tags = models.JSONField(default=list)     # JSON arrays
        
        class Meta:
            app_label = "example"
    
    # Advanced features with backend optimization
    product = Product.objects.create(
        name="Advanced Widget",
        metadata={"features": ["json", "backend"]},
        tags=["premium", "advanced"]
    )
    
    # Enhanced JSON queries
    results = Product.objects.filter(tags__contains=["premium"])
    assert results.count() == 1
```

### ⚙️ Pattern 2 Configuration

```python
# In conftest.py - uses django_pglite_db fixture
DATABASES = {
    "default": {
        "ENGINE": "py_pglite.django.backend",  # Custom backend
        # Backend manages connection automatically
    }
}
```

## 🔄 Pattern Comparison

**Directory**: `comparison/`

Side-by-side comparison showing both patterns in action.

### 📁 Pattern 1 Files

- `test_both_patterns.py` - Direct comparison and migration guide

## 🎯 When to Use Each Pattern

### Choose **Lightweight/Socket** when

- ✅ You want minimal setup and dependencies
- ✅ You're doing basic Django model testing
- ✅ You need fast startup times
- ✅ You're prototyping or doing simple tests
- ✅ You prefer standard Django patterns

### Choose **Full Integration/Backend** when

- ✅ You want comprehensive Django testing
- ✅ You need advanced PostgreSQL features
- ✅ You're building production-like test suites
- ✅ You want backend optimization features
- ✅ You need enhanced JSON support

## 🚀 Running Examples

### Run all lightweight examples

```bash
pytest examples/testing-patterns/django/lightweight/ -v
```

### Run all full integration examples

```bash
pytest examples/testing-patterns/django/full-integration/ -v
```

### Run pattern comparison

```bash
pytest examples/testing-patterns/django/comparison/ -v -s
```

### Run everything

```bash
pytest examples/testing-patterns/django/ -v
```

## 🔧 Configuration Files

### `conftest.py`

Provides fixtures for both patterns:

- `configured_django` - Lightweight/Socket pattern
- `django_pglite_db` - Full Integration pattern
- Shared utilities and setup

### Migration Between Patterns

Both patterns work with the same Django models! You can easily switch:

**From Lightweight to Full Integration:**

1. Change fixture: `configured_django` → `django_pglite_db`
2. Update ENGINE: `django.db.backends.postgresql` → `py_pglite.django.backend`
3. Add enhanced JSON features if desired

**From Full Integration to Lightweight:**

1. Change fixture: `django_pglite_db` → `configured_django`
2. Update ENGINE: `py_pglite.django.backend` → `django.db.backends.postgresql`
3. Simplify JSON usage if needed

## 💡 Best Practices

1. **Start Simple**: Begin with Lightweight/Socket for basic needs
2. **Upgrade When Needed**: Move to Full Integration for advanced features
3. **Test Both**: Use comparison examples to understand differences
4. **Choose by Use Case**: Match pattern to your specific requirements
5. **Document Choice**: Be clear about which pattern you're using

## 🐛 Troubleshooting

### Common Issues

**Pattern 1 (Lightweight/Socket)**:

- Ensure PGlite manager is running
- Check socket directory permissions
- Verify PostgreSQL client compatibility

**Pattern 2 (Full Integration/Backend)**:

- Ensure py-pglite Django backend is installed
- Check backend configuration
- Verify fixture usage is correct

### Getting Help

1. Check the examples in each pattern directory
2. Run the comparison tests to understand differences
3. Review the conftest.py configuration
4. Look at the specific pattern that matches your use case

## 🌟 Contributing

When adding new examples:

1. Choose the appropriate pattern directory
2. Follow the naming convention (`test_[pattern]_[feature].py`)
3. Include comprehensive docstrings
4. Update this README if adding new concepts

---

**Happy testing with Django + py-pglite!** 🚀

Choose the pattern that fits your needs and start building amazing tests!
