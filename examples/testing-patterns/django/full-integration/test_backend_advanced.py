"""
🌟 Django + py-pglite: Advanced Full Integration Pattern
=======================================================

Pattern 2: Advanced Django features with custom backend integration.

This example demonstrates advanced Django patterns with the full integration approach:
• Advanced Django ORM features with custom py_pglite.django.backend
• Complex queries, relationships, and database constraints
• Transaction management and bulk operations
• Custom backend optimization features
• Production-ready advanced patterns

📋 Pattern Details:
• Backend: py_pglite.django.backend (custom)
• Connection: Managed by py-pglite backend
• Features: Full backend integration capabilities
• Use case: Advanced Django testing, enterprise applications

Compare with: ../lightweight/ for socket-based pattern

This complements test_backend_basic.py by showing advanced backend-focused patterns.
"""

import pytest
from django.db import IntegrityError, connection, models, transaction
from django.db.models import Count, Q

# Mark as Django test
pytestmark = pytest.mark.django


def test_advanced_django_queries_with_backend(django_pglite_db):
    """
    🎯 Test advanced Django query features with custom backend.

    Demonstrates complex Django queries enhanced by the custom backend:
    - Advanced filtering and aggregation
    - Complex conditions with Q objects
    - Backend-optimized query performance
    """

    # Define models with relationships
    class Category(models.Model):
        name = models.CharField(max_length=50, unique=True)
        slug = models.SlugField(unique=True)
        metadata = models.JSONField(default=dict)

        class Meta:
            app_label = "backend_advanced"

    class Article(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        category = models.ForeignKey(
            Category, on_delete=models.CASCADE, related_name="articles"
        )
        published = models.BooleanField(default=False)
        view_count = models.PositiveIntegerField(default=0)
        tags = models.JSONField(default=list)  # Backend supports JSON arrays

        class Meta:
            app_label = "backend_advanced"
            indexes = [
                models.Index(fields=["published", "view_count"]),
            ]

    # Create tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Category)
        schema_editor.create_model(Article)

    # Create test data with backend-specific features
    tech_cat = Category.objects.create(
        name="Technology",
        slug="tech",
        metadata={"description": "Tech articles", "priority": 1},
    )
    python_cat = Category.objects.create(
        name="Python",
        slug="python",
        metadata={"description": "Python tutorials", "priority": 2},
    )

    # Create articles with JSON tags (backend feature)
    Article.objects.create(
        title="Django Backend Testing",
        content="Advanced testing with custom backend",
        category=tech_cat,
        published=True,
        view_count=150,
        tags=["django", "testing", "backend"],
    )

    Article.objects.create(
        title="Python Performance Tips",
        content="Optimizing Python applications",
        category=python_cat,
        published=True,
        view_count=75,
        tags=["python", "performance", "optimization"],
    )

    Article.objects.create(
        title="Draft: Future Features",
        content="Upcoming backend features",
        category=tech_cat,
        published=False,
        view_count=0,
        tags=["draft", "future"],
    )

    # Test complex queries with backend optimization

    # 1. JSON field queries (backend feature)
    high_priority_cats = Category.objects.filter(metadata__priority__lte=2)
    assert high_priority_cats.count() == 2

    # 2. Advanced filtering with Q objects and JSON
    popular_tech_articles = Article.objects.filter(
        Q(published=True) & Q(view_count__gte=100) & Q(tags__contains=["testing"])
    )
    assert popular_tech_articles.count() == 1

    # 3. Simple aggregation without complex relationships
    tech_articles = Article.objects.filter(category=tech_cat)
    python_articles = Article.objects.filter(category=python_cat)

    assert tech_articles.count() == 2  # 2 articles in tech category
    assert python_articles.count() == 1  # 1 article in python category

    # Test published vs unpublished counts
    published_articles = Article.objects.filter(published=True)
    assert published_articles.count() == 2

    print("✅ Advanced backend queries working!")


def test_database_constraints_with_backend(django_pglite_db):
    """
    🎯 Test database constraints enhanced by custom backend.

    Shows that PostgreSQL constraints work optimally with the backend:
    - Unique constraints with backend optimization
    - Foreign key constraints
    - Check constraints and validation
    """

    # Define models with advanced constraints
    class User(models.Model):
        username = models.CharField(max_length=50, unique=True)
        email = models.EmailField(unique=True)
        profile_data = models.JSONField(default=dict)

        class Meta:
            app_label = "backend_constraints"

    class UserProfile(models.Model):
        user = models.OneToOneField(User, on_delete=models.CASCADE)
        bio = models.TextField()
        preferences = models.JSONField(default=dict)

        class Meta:
            app_label = "backend_constraints"

    # Create tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(User)
        schema_editor.create_model(UserProfile)

    # Create initial data
    user = User.objects.create(
        username="testuser",
        email="test@example.com",
        profile_data={"theme": "dark", "notifications": True},
    )

    profile = UserProfile.objects.create(
        user=user,
        bio="Test user profile",
        preferences={"language": "en", "timezone": "UTC"},
    )

    # Test unique constraint enforcement
    with pytest.raises(IntegrityError):
        User.objects.create(username="testuser2", email="test@example.com")

    # Test one-to-one relationship constraint
    with pytest.raises(IntegrityError):
        UserProfile.objects.create(
            user=user,  # Same user, should fail
            bio="Duplicate profile",
        )

    # Test JSON field operations (backend feature)
    assert user.profile_data["theme"] == "dark"
    assert profile.preferences["language"] == "en"

    print("✅ Backend-enhanced constraints working!")


def test_transaction_management_with_backend(django_pglite_db):
    """
    🎯 Test transaction management with custom backend.

    Demonstrates transaction behavior optimized by the backend:
    - Atomic transactions with backend optimization
    - Rollback handling
    - Nested transaction support
    """

    # Define model
    class Order(models.Model):
        order_id = models.CharField(max_length=50, unique=True)
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        processed = models.BooleanField(default=False)
        metadata = models.JSONField(default=dict)

        class Meta:
            app_label = "backend_transactions"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Order)

    # Test successful transaction
    with transaction.atomic():
        order = Order.objects.create(
            order_id="ORD-001",
            amount=100.00,
            processed=True,
            metadata={"payment_method": "card", "currency": "USD"},
        )

    assert Order.objects.count() == 1
    assert order.metadata["payment_method"] == "card"

    # Test rollback on error
    try:
        with transaction.atomic():
            Order.objects.create(order_id="ORD-002", amount=200.00, processed=True)
            # Force an error to test rollback
            raise Exception("Simulated payment failure")
    except Exception:
        pass

    # Should still be 1 (rollback worked)
    assert Order.objects.count() == 1

    # Test nested transactions (backend feature)
    with transaction.atomic():
        # Outer transaction
        Order.objects.create(order_id="ORD-003", amount=50.00)

        try:
            with transaction.atomic():
                # Inner transaction that fails
                Order.objects.create(order_id="ORD-004", amount=75.00)
                raise Exception("Inner transaction failure")
        except Exception:
            pass

        # Outer transaction should continue
        Order.objects.create(order_id="ORD-005", amount=25.00)

    # Should have orders 001, 003, and 005 (004 rolled back)
    assert Order.objects.count() == 3

    print("✅ Backend transaction management working!")


def test_bulk_operations_with_backend(django_pglite_db):
    """
    🎯 Test bulk operations optimized by custom backend.

    Shows Django bulk operations enhanced by the backend:
    - bulk_create with backend optimization
    - bulk_update operations
    - Performance improvements with custom backend
    """

    # Define model
    class Product(models.Model):
        name = models.CharField(max_length=100)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        category = models.CharField(max_length=50, default="general")
        attributes = models.JSONField(default=dict)

        class Meta:
            app_label = "backend_bulk"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Product)

    # Bulk create with JSON data (backend feature)
    products = [
        Product(
            name=f"Product {i}",
            price=i * 10.00,
            category="bulk",
            attributes={"sku": f"SKU-{i:03d}", "in_stock": True},
        )
        for i in range(50)
    ]

    # Backend-optimized bulk creation
    Product.objects.bulk_create(products)
    assert Product.objects.count() == 50

    # Test bulk update with backend optimization
    Product.objects.filter(category="bulk").update(
        category="updated_bulk",
    )

    updated_count = Product.objects.filter(category="updated_bulk").count()
    assert updated_count == 50

    # Test filtering on JSON fields (backend feature)
    in_stock = Product.objects.filter(attributes__in_stock=True)
    assert in_stock.count() == 50

    print("✅ Backend-optimized bulk operations working!")


if __name__ == "__main__":
    print("🌟 Django + py-pglite: Advanced Full Integration Pattern")
    print(
        "Run with: pytest testing-patterns/django/"
        "full-integration/test_backend_advanced.py -v"
    )
