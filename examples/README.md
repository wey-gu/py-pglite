# 🚀 py-pglite Examples

**Real PostgreSQL testing made instant** ⚡

## ⚡ **Quick Start** (0 to PostgreSQL in 30 seconds)

### **🎯 Instant Demo** - See the magic

```bash
python quickstart/demo_instant.py
```

**Output:**

```bash
⚡ py-pglite: Instant PostgreSQL Magic
✅ PostgreSQL started (zero config!)
🔥 Running: PostgreSQL 17.4
🚀 JSON test: py-pglite
🎯 Array test: 3 features
📊 Inserted 3 users instantly
🏆 First user: Alice (rank #1)
🎉 DONE! Real PostgreSQL in seconds!
```

### **🌐 FastAPI Integration** - Production ready

```bash
python quickstart/simple_fastapi.py
# Open http://localhost:8000/docs
```

Full REST API with PostgreSQL in 30 lines. Interactive Swagger docs included!

### **🏃 The Sweet Spot** - Honest performance comparison

```bash
python quickstart/simple_performance.py
```

**Honest results:** SQLite wins raw speed, py-pglite wins features + convenience vs Docker PostgreSQL.

---

## **✨ Feature Examples**

### **🤖 `pgvector` for AI/RAG**

Test vector similarity search for Retrieval-Augmented Generation (RAG) applications.

```bash
# Requires 'py-pglite[extensions]' to be installed
pytest examples/features/test_pgvector_rag.py -v
```

---

## 🧪 **Testing Patterns** (Production examples)

### **📊 SQLAlchemy** - Zero config testing

```bash
pytest testing-patterns/sqlalchemy/ -v
```

Perfect SQLAlchemy integration with automatic cleanup.

### **🌟 Django** - Two integration patterns  

**🔹 Lightweight/Socket Pattern** (Minimal setup)

```bash
# Standard PostgreSQL backend with socket connection
pytest testing-patterns/django/lightweight/ -v
```

**🔸 Full Integration/Backend Pattern** (Enhanced features)

```bash  
# Custom py-pglite backend with advanced capabilities
pytest testing-patterns/django/full-integration/ -v
```

**🔄 Pattern Comparison & Migration Guide**

```bash
# Side-by-side comparison and migration guidance
pytest testing-patterns/django/comparison/ -v -s
```

**📚 Complete Django Guide**

```bash
# All Django patterns (26 comprehensive tests)
pytest testing-patterns/django/ -v
```

**Choose your pattern:**

- **Lightweight**: Fast startup, minimal dependencies, standard Django patterns
- **Full Integration**: Advanced JSON features, backend optimization, production-like setup

👉 **See [Django patterns guide](testing-patterns/django/README.md)** for detailed documentation!

### **🎪 Comprehensive** - All fixtures

```bash
pytest testing-patterns/test_fixtures_showcase.py -v
```

Advanced PostgreSQL features, performance patterns, edge cases.

---

## 📁 **Directory Structure**

```bash
examples/
├── quickstart/                 # 🚀 Instant demos (3 files)
│   ├── demo_instant.py        #    ⚡ See the magic (30 seconds)
│   ├── simple_fastapi.py      #    🌐 FastAPI + PostgreSQL API
│   └── simple_performance.py  #    🏃 The honest performance sweet spot
│
├── features/                   # ✨ Feature examples
│   └── test_pgvector_rag.py   #    🤖 pgvector for AI/RAG
│
├── testing-patterns/          # 🧪 Production examples
│   ├── sqlalchemy/            #    📊 SQLAlchemy patterns
│   │   ├── test_sqlalchemy_quickstart.py
│   │   └── conftest.py
│   ├── django/                #    🌟 Two Django integration patterns
│   │   ├── conftest.py        #        Dual-pattern fixtures
│   │   ├── README.md          #        📚 Comprehensive Django guide
│   │   ├── lightweight/       #        🔹 Socket pattern (minimal setup)
│   │   │   ├── test_socket_basic.py
│   │   │   ├── test_socket_advanced.py
│   │   │   └── test_socket_pytest_django.py
│   │   ├── full-integration/  #        🔸 Backend pattern (enhanced features)
│   │   │   ├── test_backend_basic.py
│   │   │   ├── test_backend_advanced.py
│   │   │   └── test_backend_pytest_django.py
│   │   └── comparison/        #        🔄 Pattern comparison
│   │       └── test_both_patterns.py
│   └── test_fixtures_showcase.py #  Advanced patterns
│
└── README.md                  # 📚 This guide
```

---

## 🎯 **Usage Patterns**

### **⚡ Instant Results** (Like Vite)

```python
# ONE LINE setup - real PostgreSQL ready!
with PGliteManager() as db:
    engine = db.get_engine()
    # Full PostgreSQL power available immediately
```

### **🧪 Testing Patterns**

```python
# SQLAlchemy tests
def test_users(pglite_session):
    user = User(name="Alice")
    pglite_session.add(user)
    pglite_session.commit()
    assert user.id == 1  # Real PostgreSQL!

# Django tests - Lightweight/Socket pattern
def test_django_socket(configured_django):
    Post.objects.create(title="Hello World")
    assert Post.objects.count() == 1  # Standard backend + socket!

# Django tests - Full Integration/Backend pattern  
def test_django_backend(django_pglite_db):
    Post.objects.create(title="Hello", metadata={"tags": ["test"]})
    assert Post.objects.count() == 1  # Custom backend + JSON support!

# Django with pytest-django (both patterns supported)
@pytest.mark.django_db
def test_with_pytest_django(django_pglite_db):
    Post.objects.create(title="pytest-django works!")
    assert Post.objects.count() == 1
```

### **🚀 Production Examples**

```python
# FastAPI integration
@app.post("/users/")
def create_user(user: UserCreate, session: Session = Depends(get_db)):
    db_user = User(**user.dict())
    session.add(db_user)
    session.commit()
    return db_user  # Real PostgreSQL backend!
```

---

## 🎪 **Advanced Features**

### **🔧 Custom Configuration**

```python
config = PGliteConfig(
    port_range=(5500, 5600),
    timeout=30,
    cleanup_on_exit=True
)
```

### **🏃 Performance Testing**

```python
def test_bulk_operations(pglite_session):
    users = [User(name=f"user_{i}") for i in range(1000)]
    pglite_session.add_all(users)
    pglite_session.commit()
    # Blazing fast with real PostgreSQL!
```

### **🎯 Framework Isolation**

```bash
pytest testing-patterns/sqlalchemy/ -p no:django  # Pure SQLAlchemy
pytest testing-patterns/django/                   # Pure Django patterns
```

---

## 🎊 **Why py-pglite?**

### **❌ Traditional Way**

```python
# 1. Install PostgreSQL server
# 2. Configure connection strings  
# 3. Manage test databases
# 4. Handle cleanup manually
# 5. Docker containers...
# 6. Still not portable
```

### **✅ py-pglite Way**

```python  
def test_my_feature(pglite_session):
    User.objects.create(name="Alice")  # Just works!
```

**That's it.** No Docker, no setup, no configuration files.

---

## 🚀 **Getting Started**

1. **⚡ See the magic** - `python quickstart/demo_instant.py`
2. **🌐 Try FastAPI** - `python quickstart/simple_fastapi.py`
3. **🏃 See the value** - `python quickstart/simple_performance.py`
4. **🤖 Try pgvector** - `pytest examples/features/test_pgvector_rag.py -v`
5. **🎪 Explore Django patterns** - `pytest testing-patterns/django/ -v`
6. **📚 Read the Django guide** - [Django patterns documentation](testing-patterns/django/README.md)
