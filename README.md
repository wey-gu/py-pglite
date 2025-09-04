# py-pglite

<img src="https://github.com/user-attachments/assets/3c6ef886-5075-4d82-a180-a6b1dafe792b" alt="py-pglite Logo" width="60" align="left" style="margin-right: 16px;"/>

**A Pythonic interface for PGlite - the instant, zero-config PostgreSQL.** ⚡️

`py-pglite` brings the magic of [PGlite](https://github.com/electric-sql/pglite) to Python with a high-level, developer-friendly API. Real PostgreSQL, instant testing.

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

[![License](https://img.shields.io/pypi/l/py-pglite.svg)](https://github.com/wey-gu/py-pglite/blob/main/LICENSE) [![MyPy](https://img.shields.io/badge/type_checked-mypy-informational.svg)](https://mypy.readthedocs.io/en/stable/introduction.html) [![Ruff](https://img.shields.io/badge/style-ruff-blue?logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff) [![codecov](https://codecov.io/github/wey-gu/py-pglite/graph/badge.svg?token=VQHDHT5LIM)](https://codecov.io/github/wey-gu/py-pglite)

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

# Extra Features
pip install py-pglite[extensions]  # pglite extensions, like pgvector, fuzzystrmatch etc.
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

### **Django**

**🔹 Lightweight/Socket** (Minimal setup)

```python
def test_django_socket_pattern(configured_django):
    Post.objects.create(title="Hello", content="World")
    assert Post.objects.count() == 1  # Real PostgreSQL via socket!
```

**🔸 Full Integration/Backend** (Enhanced features)

```python
def test_django_backend_pattern(django_pglite_db):
    Post.objects.create(title="Hello", content="World", metadata={"tags": ["test"]})
    assert Post.objects.count() == 1  # Custom backend with JSON support!
```

**Choose your pattern:**

- **Lightweight**: Fast, minimal dependencies, standard PostgreSQL backend
- **Full Integration**: Advanced features, custom backend, enhanced JSON support

👉 [**See Django patterns guide**](examples/testing-patterns/django/) for detailed examples and migration guide.

### **Any PostgreSQL client**

```python
def test_any_client_works(pglite_manager):
    # Extract connection details
    engine = pglite_manager.get_engine()
    host, port, database = str(engine.url.host), engine.url.port, engine.url.database

    # Use with any PostgreSQL client
    # conn = psycopg.connect(host=host, port=port, dbname=database)
    # engine = create_async_engine(f"postgresql+asyncpg://{host}:{port}/{database}")

# For asyncpg specifically, use TCP mode with proper configuration:
async def test_asyncpg_works(pglite_tcp_manager):
    config = pglite_tcp_manager.config
    conn = await asyncpg.connect(
        host=config.tcp_host,
        port=config.tcp_port,
        user="postgres", 
        password="postgres",
        database="postgres",
        ssl=False,
        server_settings={}  # CRITICAL: Required for PGlite compatibility
    )
    result = await conn.fetchval("SELECT 1")
    await conn.close()
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

### **PostgreSQL Extensions**

`py-pglite` supports PostgreSQL extensions, allowing you to test advanced features like vector similarity search for AI/RAG applications.

### **🚀 `pgvector` for RAG Applications**

Enable `pgvector` to test vector embeddings and similarity search directly in your test suite.

**1. Install with the `[extensions]` extra:**

```bash
pip install 'py-pglite[extensions]'
```

**2. Enable `pgvector` in the configuration:**

```python
from py_pglite import PGliteConfig, PGliteManager
from pgvector.psycopg import register_vector
import psycopg
import numpy as np

# Enable the extension
config = PGliteConfig(extensions=["pgvector"])

with PGliteManager(config=config) as db:
    with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
        # Create the extension and register the type
        conn.execute("CREATE EXTENSION IF NOT EXISTS vector")
        register_vector(conn)

        # Create a table and insert a vector
        conn.execute("CREATE TABLE items (embedding vector(3))")
        conn.execute("INSERT INTO items (embedding) VALUES (%s)", (np.array([1, 2, 3]),))

        # Perform a similarity search
        result = conn.execute("SELECT * FROM items ORDER BY embedding <-> %s LIMIT 1", (np.array([1, 1, 1]),)).fetchone()
        assert np.array_equal(result[0], np.array([1, 2, 3]))
```

`py-pglite` can support many other extensions available in the underlying [PGlite extensions](https://pglite.dev/extensions/) ♥️.

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
<summary><strong>🌐 Socket Modes (Unix vs TCP)</strong></summary>

py-pglite supports both Unix domain sockets (default) and TCP sockets for different use cases:

### Unix Socket Mode (Default)
```python
# Default configuration - uses Unix domain socket for best performance
from py_pglite import PGliteManager

with PGliteManager() as db:
    # Connection via Unix socket - fastest for local testing
    dsn = db.get_dsn()  # host=/tmp/... dbname=postgres
```

### TCP Socket Mode
```python
from py_pglite import PGliteConfig, PGliteManager

# Enable TCP mode for any TCP-only clients
config = PGliteConfig(
    use_tcp=True,
    tcp_host="127.0.0.1",  # Default: localhost only
    tcp_port=5432,         # Default: PostgreSQL standard port
    extensions=["pgvector"]
)

with PGliteManager(config) as db:
    # Now compatible with any TCP-only clients
    uri = db.get_psycopg_uri()
    # postgresql://postgres:postgres@127.0.0.1:5432/postgres?sslmode=disable
```

**When to use TCP mode:**
- Any TCP-only clients (doesn't support Unix sockets)
- Cloud-native testing environments
- Docker containers with network isolation
- Testing network-based database tools
- **Required for asyncpg**: asyncpg only works in TCP mode

**Important notes:**
- PGlite Socket supports only **one active connection** at a time
- SSL is not supported - always use `sslmode=disable`
- Unix sockets are faster for local testing (default)
- TCP mode binds to localhost by default for security
- **asyncpg requires `server_settings={}` to prevent hanging**

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
    # Django:   Uses custom py-pglite backend automatically

# asyncpg requires TCP mode and specific configuration:
config = PGliteConfig(use_tcp=True)
with PGliteManager(config) as manager:
    conn = await asyncpg.connect(
        host=config.tcp_host,
        port=config.tcp_port,
        user="postgres",
        password="postgres", 
        database="postgres",
        ssl=False,
        server_settings={}  # Required for PGlite compatibility
    )
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

Powered by the 🚀 amazing and ♥️ beloved [PGlite](https://github.com/electric-sql/pglite).
