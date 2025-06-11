# py-pglite

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

## **Why py-pglite?**

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

- 🎯 **Zero config** - No setup, no Docker, no servers
- ⚡ **Instant** - 2-3s startup vs 30-60s Docker
- 🔄 **Isolated** - Fresh database per test
- 🐘 **Real PostgreSQL** - JSON, arrays, window functions
- 🚀 **Any client** - SQLAlchemy, Django, psycopg, asyncpg

---

## **Install**

```bash
# Core (framework-agnostic)
pip install py-pglite

# With your stack
pip install py-pglite[sqlalchemy]  # SQLAlchemy + SQLModel
pip install py-pglite[django]      # Django + pytest-django  
pip install py-pglite[asyncpg]     # Pure async client
pip install py-pglite[all]         # Everything
```

---

## **Quick Start**

### **SQLAlchemy** (Zero imports needed)

```python
def test_sqlalchemy_just_works(pglite_session):
    user = User(name="Alice", email="alice@test.com")  
    pglite_session.add(user)
    pglite_session.commit()
    
    assert user.id is not None
    assert User.query.count() == 1  # Real PostgreSQL!
```

### **Django** (Auto-configured)

```python  
def test_django_just_works(db):
    Post.objects.create(title="Hello", content="World")
    assert Post.objects.count() == 1  # Real PostgreSQL!
```

### **Any PostgreSQL client**

```python
def test_any_client_works(pglite_manager):
    # Extract connection details
    engine = pglite_manager.get_engine()
    host, port, database = str(engine.url.host), engine.url.port, engine.url.database
    
    # Use with any PostgreSQL client
    # conn = psycopg.connect(host=host, port=port, dbname=database)
    # conn = await asyncpg.connect(host=host, port=port, database=database)
    # engine = create_async_engine(f"postgresql+asyncpg://{host}:{port}/{database}")
```

---

## **Examples**

### **FastAPI + SQLModel**

```python
from fastapi.testclient import TestClient

def test_api_endpoint(client: TestClient):
    response = client.post("/users/", json={"name": "Alice"})
    assert response.status_code == 201
    
    response = client.get("/users/")
    assert len(response.json()) == 1
```

### **PostgreSQL Features**

```python
def test_postgresql_power(pglite_session):
    pglite_session.execute(text("""
        CREATE TABLE analytics (
            data JSONB,
            tags TEXT[],
            created TIMESTAMP DEFAULT NOW()
        )
    """))
    
    pglite_session.execute(text("""
        INSERT INTO analytics (data, tags) VALUES 
        ('{"clicks": 100}', ARRAY['web', 'mobile'])
    """))
    
    result = pglite_session.execute(text("""
        SELECT data->>'clicks' as clicks,
               array_length(tags, 1) as tag_count
        FROM analytics 
        WHERE data->>'clicks' > '50'
    """)).fetchone()
    
    assert result.clicks == '100'
```

---

## **Advanced**

<details>
<summary><strong>🔧 Production Configuration</strong></summary>

```python
from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

config = PGliteConfig(
    timeout=60,                    # Extended timeout for CI/CD
    log_level="INFO",              # Balanced logging
    cleanup_on_exit=True,          # Automatic cleanup
    work_dir=Path("./test-data")   # Custom directory
)

with SQLAlchemyPGliteManager(config) as manager:
    engine = manager.get_engine(
        pool_recycle=3600,         # Connection recycling
        echo=False                 # SQL logging
    )
```

</details>

<details>
<summary><strong>🔄 Client Compatibility</strong></summary>

```python
# py-pglite provides a REAL PostgreSQL server - any client works!

with SQLAlchemyPGliteManager() as manager:
    engine = manager.get_engine()
    url = engine.url
    
    # Extract connection details for any PostgreSQL client
    host, port, database = str(url.host), url.port, url.database
    
    # Examples for different clients:
    # psycopg:  psycopg.connect(host=host, port=port, dbname=database)
    # asyncpg:  await asyncpg.connect(host=host, port=port, database=database)
    # Django:   Uses custom py-pglite backend automatically
```

**Installation Matrix:**

| Client | Install | Use Case |
|--------|---------|----------|
| `[sqlalchemy]` | SQLAlchemy + SQLModel | ORM, modern Python |
| `[django]` | Django + pytest-django | Django projects |
| `[psycopg]` | psycopg (sync/async) | Raw SQL, custom |
| `[asyncpg]` | Pure async client | High-performance async |
| `[all]` | Everything | Full compatibility |

</details>

<details>
<summary><strong>🎯 Framework Isolation</strong></summary>

```bash
# Perfect isolation - no framework bleeding
pytest -m sqlalchemy -p no:django     # Pure SQLAlchemy
pytest -m django -p no:sqlalchemy     # Pure Django  
pytest tests/sqlalchemy/              # Directory isolation
```

</details>

---

**Built for developers who want PostgreSQL testing without the complexity.**

🎯 [Examples](examples/) • 📚 [Contributing](CONTRIBUTING.md) • 🐛 [Issues](https://github.com/wey-gu/py-pglite/issues)

---

*py-pglite: Because testing should be simple.* ⚡
