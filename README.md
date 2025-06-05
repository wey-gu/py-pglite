# py-pglite

A Python testing library that provides seamless integration between [PGlite](https://github.com/electric-sql/pglite) and Python test suites. Get the full power of PostgreSQL in your tests without the overhead of a full PostgreSQL installation.

## 🎯 Why py-pglite?

- **⚡ Blazing Fast**: In-memory PostgreSQL for ultra-quick test runs
- **🛠️ Effortless Setup**: No PostgreSQL install needed—just Node.js(I know)!
- **🐍 Pythonic**: Native support for SQLAlchemy & SQLModel in your tests
- **🧊 Fully Isolated**: Every test module gets its own fresh database
- **🦾 100% Compatible**: True PostgreSQL features via [PGlite](https://pglite.dev/)
- **🧩 Pytest Plug-and-Play**: Ready-to-use fixtures for instant productivity

## 📦 Installation

### Basic Installation

```bash
pip install py-pglite
```

### With Optional Dependencies

```bash
# For SQLModel support
pip install "py-pglite[sqlmodel]"

# For FastAPI integration
pip install "py-pglite[fastapi]"

# For development
pip install "py-pglite[dev]"
```

### Requirements

- **Python**: 3.10+
- **Node.js**: 18+ (for PGlite)
- **SQLAlchemy**: 2.0+

The library automatically manages PGlite npm dependencies.

## 🚀 Quick Start

### Basic Usage with Pytest

```python
import pytest
from sqlmodel import Session, SQLModel, Field, select
from py_pglite import pglite_session

# Your models
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str

# Test with automatic PGlite management
def test_user_creation(pglite_session: Session):
    user = User(name="Alice", email="alice@example.com")
    pglite_session.add(user)
    pglite_session.commit()
    
    # Query back
    users = pglite_session.exec(select(User)).all()
    assert len(users) == 1
    assert users[0].name == "Alice"
```

### Manual Management

```python
from py_pglite import PGliteManager, PGliteConfig

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
5. Run the development workflow: `python hacking.py`
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
