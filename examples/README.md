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

## 🧪 **Testing Patterns** (Production examples)

### **📊 SQLAlchemy** - Zero config testing

```bash
pytest testing-patterns/sqlalchemy/ -v
```

Perfect SQLAlchemy integration with automatic cleanup.

### **🌟 Django** - Auto-configured testing  

```bash
# Basic Django test, without pytest-django
pytest testing-patterns/django/ -v

# Django test with pytest-django (requires pytest-django)
pip install pytest-django
pytest testing-patterns/django/test_pytest_django.py -v
```

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
├── testing-patterns/          # 🧪 Production examples
│   ├── sqlalchemy/            #    📊 SQLAlchemy patterns
│   │   ├── test_sqlalchemy_quickstart.py
│   │   └── conftest.py
│   ├── django/                #    🌟 Django patterns
│   │   ├── test_django_quickstart.py
│   │   ├── test_django_fixtures.py
│   │   ├── test_pytest_django.py
│   │   └── conftest.py
│   └── test_fixtures_showcase.py # 🎪 Advanced patterns
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

# Django tests (基础用法)
def test_models(pglite_django_db):
    Post.objects.create(title="Hello World")
    assert Post.objects.count() == 1  # Zero config!

# Django tests (使用 pytest-django)
@pytest.mark.django_db
def test_with_pytest_django(pglite_django_db):
    Post.objects.create(title="Hello World")
    assert Post.objects.count() == 1  # 更多测试功能！
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
pytest testing-patterns/django/                   # Pure Django
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
4. **🧪 Run tests** - `pytest testing-patterns/ -v`
5. **🎪 Explore advanced** - `pytest testing-patterns/test_fixtures_showcase.py -v`

---

**py-pglite: Because PostgreSQL testing should be instant.** ⚡
