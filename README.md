# Py-PGlite

<div style="display: flex; align-items: flex-start;">
  <div style="flex: 0 0 auto; margin-right: 18px;">
    <img src="https://github.com/user-attachments/assets/3c6ef886-5075-4d82-a180-a6b1dafe792b" alt="py-pglite Logo" width="160" style="border-radius: 8px;"/>
  </div>
  <div style="flex: 1;">
    <p><strong>Instant PostgreSQL for Python testing</strong> ⚡</p>
    <p><code>pip install py-pglite</code></p>
    <pre><code class="language-python">def test_users(pglite_session):
    user = User(name="Alice")
    pglite_session.add(user)
    pglite_session.commit()
    assert user.id == 1  # It's real PostgreSQL!</code></pre>
    <p><strong>That's it.</strong> No Docker, no setup, no config files. Real PostgreSQL, instant testing.</p>
  </div>
</div>

<br clear="all"/>

[![CI](https://github.com/wey-gu/py-pglite/actions/workflows/ci.yml/badge.svg)](https://github.com/wey-gu/py-pglite/actions/workflows/ci.yml) [![PyPI](https://badge.fury.io/py/py-pglite.svg)](https://badge.fury.io/py/py-pglite) [![Python](https://img.shields.io/pypi/pyversions/py-pglite.svg)](https://pypi.org/project/py-pglite/)

[![License](https://img.shields.io/pypi/l/py-pglite.svg)](https://github.com/wey-gu/py-pglite/blob/main/LICENSE) [![MyPy](https://img.shields.io/badge/type_checked-mypy-informational.svg)](https://mypy.readthedocs.io/en/stable/introduction.html) [![Ruff](https://img.shields.io/badge/style-ruff-blue?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff) [![codecov](https://codecov.io/gh/wey-gu/py-pglite/branch/main/graph/badge.svg?token=YOUR_CODECOV_TOKEN)](https://codecov.io/gh/wey-gu/py-pglite)

---

## ⚡ **Zero-Config Quick Start**

### **SQLAlchemy** (Zero imports needed)

```python
def test_sqlalchemy_just_works(pglite_session):
    # Tables created automatically
    user = User(name="Alice", email="alice@test.com")  
    pglite_session.add(user)
    pglite_session.commit()
    
    assert user.id is not None
    assert User.query.count() == 1  # Real PostgreSQL!
```

### **Django** (Auto-configured)

```python  
def test_django_just_works(db):
    # Models ready automatically
    Post.objects.create(title="Hello", content="World")
    assert Post.objects.count() == 1  # Real PostgreSQL!
```

### **Raw SQL** (Pure speed)

```python
def test_raw_sql_power(pglite_engine):
    with pglite_engine.connect() as conn:
        # Full PostgreSQL features
        result = conn.execute(text("""
            SELECT '{"users": [{"name": "Alice"}]}'::json ->> 'users'
        """)).scalar()
        assert '"name": "Alice"' in result  # JSON queries work!
```

---

## 🚀 **Why py-pglite?**

```python
# ❌ Traditional testing
def test_old_way():
    # 1. Install PostgreSQL
    # 2. Configure connection  
    # 3. Manage test databases
    # 4. Handle cleanup
    # 5. Docker containers...
    pass

# ✅ py-pglite way  
def test_new_way(pglite_session):
    User.objects.create(name="Alice")  # Just works!
```

**The magic:**

- **🎯 Zero config** - No setup, no Docker, no servers
- **⚡ Sweet spot** - PostgreSQL power + near-SQLite convenience  
- **🔄 Isolated** - Fresh database per test
- **🎪 Full featured** - JSON, arrays, window functions, etc.
- **🧪 Framework ready** - SQLAlchemy, Django, FastAPI
- **🚀 Fast setup** - 2-3s vs 30-60s Docker PostgreSQL startup

---

## 📦 **Installation**

```bash
# Core (framework-agnostic)
pip install py-pglite

# With your favorite framework
pip install py-pglite[sqlalchemy]  # SQLAlchemy + SQLModel
pip install py-pglite[django]      # Django + pytest-django  
pip install py-pglite[all]         # Everything
```

---

## 🎯 **Real Examples**

### **SQLAlchemy + FastAPI** (Production ready)

```python
from fastapi.testclient import TestClient

def test_api_endpoint(client: TestClient):
    # Auto-configured FastAPI + SQLAlchemy + PostgreSQL
    response = client.post("/users/", json={"name": "Alice"})
    assert response.status_code == 201
    
    response = client.get("/users/")
    assert len(response.json()) == 1
```

### **Django Models** (Zero setup)

```python
def test_django_models(db):
    # Django auto-configured with real PostgreSQL
    user = User.objects.create_user("alice", "alice@test.com") 
    blog = Blog.objects.create(title="Hello", author=user)
    
    assert Blog.objects.filter(author__username="alice").count() == 1
```

### **PostgreSQL Features** (Full power)

```python
def test_postgresql_features(pglite_session):
    pglite_session.execute(text("""
        CREATE TABLE analytics (
            id SERIAL PRIMARY KEY,
            data JSONB,
            tags TEXT[],
            created TIMESTAMP DEFAULT NOW()
        )
    """))
    
    # JSON operations
    pglite_session.execute(text("""
        INSERT INTO analytics (data, tags) VALUES 
        ('{"clicks": 100, "views": 1000}', ARRAY['web', 'mobile'])
    """))
    
    # Complex PostgreSQL query
    result = pglite_session.execute(text("""
        SELECT data->>'clicks' as clicks,
               array_length(tags, 1) as tag_count,
               extract(hour from created) as hour
        FROM analytics 
        WHERE data->>'clicks' > '50'
    """)).fetchone()
    
    assert result.clicks == '100'
    assert result.tag_count == 2
```

---

## 🏗️ **Architecture**

```
py_pglite/
├── 📦 Core (no dependencies)
├── 🔧 SQLAlchemy integration  
├── 🌟 Django integration
└── ⚡ Auto-discovery pytest plugin
```

**Design principles:**

- **Framework agnostic core** - Use with anything
- **Optional integrations** - Only load what you need
- **Zero configuration** - Intelligent defaults
- **Perfect isolation** - No framework interference

---

## 🎪 **Advanced Features**

<details>
<summary><strong>🔧 Custom Configuration</strong></summary>

```python
@pytest.fixture(scope="session")
def custom_pglite():
    config = PGliteConfig(
        port_range=(5500, 5600),
        timeout=30,
        cleanup_on_exit=True
    )
    with PGliteManager(config) as manager:
        yield manager
```

</details>

<details>
<summary><strong>🚀 Performance Testing</strong></summary>

```python
def test_bulk_insert_performance(pglite_session):
    users = [User(name=f"user_{i}") for i in range(1000)]
    pglite_session.add_all(users)
    pglite_session.commit()
    
    assert pglite_session.query(User).count() == 1000
    # Blazing fast with real PostgreSQL!
```

</details>

<details>
<summary><strong>🎯 Framework Isolation</strong></summary>

```bash
# Pure SQLAlchemy tests
pytest -m sqlalchemy -p no:django

# Pure Django tests  
pytest -m django

# Directory isolation
pytest tests/sqlalchemy/  # Auto-isolated
pytest tests/django/       # Auto-isolated
```

</details>

---

## 💝 **Community**

> **"Finally, PostgreSQL testing that just works!"** - *Happy Developer*

> **"From 30 minutes of setup to 30 seconds. Game changer."** - *Django User*

> **"Vite for databases. This is the future."** - *FastAPI Enthusiast*

---

**Built for developers who want PostgreSQL testing without the complexity.**

🎯 [View Examples](examples/) • 📚 [Contributing](CONTRIBUTING.md) • 🐛 [Issues](https://github.com/wey-gu/py-pglite/issues)

---

<<<<<<< HEAD

# Custom configuration

config = PGliteConfig(
    timeout=30,
    cleanup_on_exit=True,
    log_level="DEBUG"
)

# Manual management

with PGliteManager(config) as manager:
    engine = manager.get_engine()
    SQLModel.metadata.create_all(engine)

    with Session(engine) as session:
        # Your database operations here
        pass

```

## 🔧 Features

### Pytest Fixtures

- **`pglite_engine`**: SQLAlchemy engine connected to PGlite
- **`pglite_session`**: Database session with automatic cleanup
- **`pglite_manager`**: Direct access to PGlite process management

### Automatic Management

- ✅ Process lifecycle management
- ✅ Socket cleanup and health checks
- ✅ Graceful shutdown and error handling
- ✅ Per-test isolation with automatic cleanup
- ✅ Node.js dependency management

### Configuration

```python
from py_pglite import PGliteConfig

config = PGliteConfig(
    timeout=30,               # Startup timeout in seconds
    cleanup_on_exit=True,     # Auto cleanup on exit
    log_level="INFO",         # Logging level (DEBUG/INFO/WARNING/ERROR)
    socket_path="/tmp/.s.PGSQL.5432",  # Custom socket path
    work_dir=None,            # Working directory (None = temp dir)
    node_modules_check=True,  # Verify node_modules exists
    auto_install_deps=True,   # Auto-install npm dependencies
)
```

### Utility Functions

```python
from py_pglite import utils

# Database cleanup utilities
utils.clean_database_data(engine)                    # Clean all data
utils.clean_database_data(engine, exclude_tables=["users"])  # Exclude tables
utils.reset_sequences(engine)                        # Reset auto-increment sequences
utils.verify_database_empty(engine)                  # Check if database is empty

# Schema operations
utils.create_test_schema(engine, "test_schema")      # Create test schema
utils.drop_test_schema(engine, "test_schema")        # Drop test schema

# Get table statistics
row_counts = utils.get_table_row_counts(engine)      # Dict of table row counts
```

## 📚 Examples

### FastAPI Integration

```python
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlmodel import Session
from py_pglite import pglite_engine

app = FastAPI()

def get_db():
    # Production database dependency
    pass

@app.post("/users/")
def create_user(user_data: dict, db: Session = Depends(get_db)):
    # Your endpoint logic
    pass

# Test with PGlite
def test_create_user_endpoint(pglite_engine):
    # Override database dependency
    def override_get_db():
        with Session(pglite_engine) as session:
            yield session
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as client:
        response = client.post("/users/", json={"name": "Bob"})
        assert response.status_code == 200
```

See also [examples/test_fastapi_auth_example.py](examples/test_fastapi_auth_example.py) for an example of how to use py-pglite with FastAPI e2e test that includes authentication.

### Complex Testing Scenario

```python
def test_complex_operations(pglite_session: Session):
    # Create related data
    user = User(name="Alice", email="alice@example.com")
    pglite_session.add(user)
    pglite_session.commit()
    pglite_session.refresh(user)
    
    # Create dependent records
    orders = [
        Order(user_id=user.id, amount=100.0),
        Order(user_id=user.id, amount=250.0),
    ]
    pglite_session.add_all(orders)
    pglite_session.commit()
    
    # Complex query with joins
    result = pglite_session.exec(
        select(User.name, func.sum(Order.amount))
        .join(Order)
        .group_by(User.name)
    ).first()
    
    assert result[0] == "Alice"
    assert result[1] == 350.0
```

## 🤝 Contributing

Contributions welcome! Please read our [Contributing Guide](CONTRIBUTING.md).

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the development workflow: `python hacking.py` | `uv run hacking.py` | `pdm run hacking.py`
6. Submit a pull request

## 📄 License

Apache 2.0 License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [PGlite](https://github.com/electric-sql/pglite) - The amazing in-memory PostgreSQL
- [SQLAlchemy](https://www.sqlalchemy.org/) - Python SQL toolkit
- [SQLModel](https://sqlmodel.tiangolo.com/) - Modern Python SQL toolkit
- [Pytest](https://pytest.org/) - Testing framework

## Best Practices

### Multiple Database Sessions

For multiple database connections, use **multiple sessions with the same engine** rather than multiple engines:

```python
# ✅ Recommended: Multiple sessions with same engine
with PGliteManager() as manager:
    engine = manager.get_engine()
    
    # Multiple sessions work perfectly
    session1 = Session(engine)
    session2 = Session(engine)
    session3 = Session(engine)

# ❌ Not recommended: Multiple engines from same manager
with PGliteManager() as manager:
    engine1 = manager.get_engine()  # Can cause connection conflicts
    engine2 = manager.get_engine()  # when used simultaneously
```

**Why?** Creating multiple SQLAlchemy engines from the same PGlite manager can cause connection pool conflicts since they all connect to the same Unix socket.

### Performance Tips

- Use `pglite_session` fixture for automatic cleanup between tests
- Use `pglite_engine` fixture when you need direct engine access
- Use utility functions for efficient database operations
- Consider custom configurations for specific test requirements

### Testing Patterns

```python
# Pattern 1: Simple CRUD testing
def test_user_crud(pglite_session):
    # Create
    user = User(name="Test", email="test@example.com")
    pglite_session.add(user)
    pglite_session.commit()
    
    # Read
    found_user = pglite_session.get(User, user.id)
    assert found_user.name == "Test"
    
    # Update
    found_user.name = "Updated"
    pglite_session.commit()
    
    # Delete
    pglite_session.delete(found_user)
    pglite_session.commit()

# Pattern 2: Custom cleanup
def test_with_custom_cleanup(pglite_engine):
    SQLModel.metadata.create_all(pglite_engine)
    
    with Session(pglite_engine) as session:
        # Your test logic
        pass
    
    # Custom cleanup if needed
    utils.clean_database_data(pglite_engine)
```

=======
*py-pglite: Because testing should be simple.* ⚡
>>>>>>> 7555fb5 (feat & refactor: decouple sqlalchemy, introduce django & pytest-django)
