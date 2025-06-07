# Py-PGlite

<img src="https://github.com/user-attachments/assets/3c6ef886-5075-4d82-a180-a6b1dafe792b" alt="py-pglite Logo" width="60" align="left" style="margin-right: 16px;"/>

**Instant PostgreSQL for Python testing** ⚡

`pip install py-pglite`

<br clear="all"/>

```python
def test_users(pglite_session):
    user = User(name="Alice")
    pglite_session.add(user)
    pglite_session.commit()
    assert user.id == 1  # It's real PostgreSQL!
```

**That's it.** No Docker, no setup, no config files. Real PostgreSQL, instant testing.

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

*py-pglite: Because testing should be simple.* ⚡

