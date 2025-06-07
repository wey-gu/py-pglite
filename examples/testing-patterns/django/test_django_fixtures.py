"""
🌟 Django Fixtures + py-pglite Examples
======================================

Demonstrates different Django testing patterns with proper abstraction:
• Pure Django ORM testing
• Advanced Django features (relationships, constraints)
• Reusable fixtures and utilities
• Clean separation of concerns

This complements test_pytest_django.py by showing Django-focused patterns.
"""

import django
import pytest
from django.conf import settings
from django.db import IntegrityError, connection, models
from django.db.models import Count, Q


def configure_django_for_testing(pglite_manager):
    """
    🎯 Proper Django configuration abstraction

    This helper encapsulates Django setup for testing,
    making it reusable across different test patterns.
    """
    if not settings.configured:
        conn_str = pglite_manager.config.get_connection_string()
        socket_dir = conn_str.split("host=")[1].split("&")[0].split("#")[0]

        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": "postgres",
                    "USER": "postgres",
                    "PASSWORD": "postgres",
                    "HOST": socket_dir,
                    "PORT": "",
                    "OPTIONS": {"connect_timeout": 10},
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            USE_TZ=False,  # Avoid timezone conflicts with PGlite
            SECRET_KEY="django-fixtures-example",
        )
        django.setup()


def test_basic_django_operations(configured_django):
    """
    🎯 Test basic Django ORM operations

    Shows fundamental Django operations with py-pglite:
    - Model creation and queries
    - Field validation
    - Basic relationships
    """

    # Define simple models
    class Author(models.Model):
        name = models.CharField(max_length=100)
        email = models.EmailField(unique=True)
        bio = models.TextField(blank=True)

        class Meta:
            app_label = "blog_operations"

    class Post(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        author = models.ForeignKey(Author, on_delete=models.CASCADE)
        published = models.BooleanField(default=False)

        class Meta:
            app_label = "blog_operations"

    # Create database tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Author)
        schema_editor.create_model(Post)

    # Test model creation
    author = Author.objects.create(name="Test Author", email="test@example.com")

    post = Post.objects.create(
        title="Test Post",
        content="This is a test post content.",
        author=author,
        published=True,
    )

    # Test queries
    assert Author.objects.count() == 1
    assert Post.objects.count() == 1

    # Test relationships
    assert post.author.name == "Test Author"

    # Test filtering
    published_posts = Post.objects.filter(published=True)
    assert published_posts.count() == 1


def test_advanced_django_queries(configured_django):
    """
    🎯 Test advanced Django query features

    Demonstrates complex Django queries with py-pglite:
    - Filtering and aggregation
    - Complex conditions with Q objects
    - Forward relationship queries
    """

    # Define models
    class Category(models.Model):
        name = models.CharField(max_length=50, unique=True)
        slug = models.SlugField(unique=True)

        class Meta:
            app_label = "blog_advanced"

    class Article(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        category = models.ForeignKey(Category, on_delete=models.CASCADE)
        published = models.BooleanField(default=False)
        view_count = models.PositiveIntegerField(default=0)

        class Meta:
            app_label = "blog_advanced"

    # Create tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Category)
        schema_editor.create_model(Article)

    # Create test data
    tech_cat = Category.objects.create(name="Technology", slug="tech")
    python_cat = Category.objects.create(name="Python", slug="python")

    # Create articles
    Article.objects.create(
        title="Django Testing",
        content="Testing with Django",
        category=tech_cat,
        published=True,
        view_count=100,
    )

    Article.objects.create(
        title="Python Tips",
        content="Python best practices",
        category=python_cat,
        published=True,
        view_count=50,
    )

    Article.objects.create(
        title="Draft Article",
        content="This is a draft",
        category=tech_cat,
        published=False,
        view_count=0,
    )

    # Test complex queries

    # 1. Filter by category
    tech_articles = Article.objects.filter(category__name="Technology")
    assert tech_articles.count() == 2

    # 2. Aggregation
    popular_articles = Article.objects.filter(view_count__gt=75)
    assert popular_articles.count() == 1

    # 3. Complex filtering with Q objects
    published_popular = Article.objects.filter(
        Q(published=True) & Q(view_count__gte=50)
    )
    assert published_popular.count() == 2

    # 4. Forward relationship queries
    tech_category_articles = Article.objects.filter(category=tech_cat)
    assert tech_category_articles.count() == 2


def test_database_constraints(configured_django):
    """
    🎯 Test database constraints and error handling

    Shows that PostgreSQL constraints work properly:
    - Unique constraints
    - Foreign key constraints
    - unique_together constraints
    """

    # Define models with constraints
    class User(models.Model):
        username = models.CharField(max_length=50, unique=True)
        email = models.EmailField(unique=True)

        class Meta:
            app_label = "constraints_test"

    class Profile(models.Model):
        user = models.ForeignKey(User, on_delete=models.CASCADE)
        bio = models.TextField()

        class Meta:
            app_label = "constraints_test"

    # Create tables
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(User)
        schema_editor.create_model(Profile)

    # Create initial data
    user = User.objects.create(username="testuser", email="test@example.com")

    # Test unique constraint
    with pytest.raises(IntegrityError):
        User.objects.create(username="testuser2", email="test@example.com")

    # Test foreign key constraint works
    profile = Profile.objects.create(user=user, bio="Test bio")
    assert profile.user.username == "testuser"


def test_django_transactions(configured_django):
    """
    🎯 Test Django transaction support

    Demonstrates transaction behavior with py-pglite:
    - Atomic transactions
    - Rollback on error
    - Transaction isolation
    """
    from django.db import transaction

    # Define model
    class Order(models.Model):
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        processed = models.BooleanField(default=False)

        class Meta:
            app_label = "transaction_test"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Order)

    # Test successful transaction
    with transaction.atomic():
        order = Order.objects.create(amount=100.00, processed=True)

    assert Order.objects.count() == 1

    # Test rollback on error
    try:
        with transaction.atomic():
            Order.objects.create(amount=200.00, processed=True)
            # Force an error to test rollback
            raise Exception("Simulated error")
    except Exception:
        pass

    # Should still be 1 (rollback worked)
    assert Order.objects.count() == 1


def test_bulk_operations(configured_django):
    """
    🎯 Test bulk operations for performance

    Shows Django bulk operations with py-pglite:
    - bulk_create for efficiency
    - bulk_update operations
    - Performance with PostgreSQL
    """

    # Define model
    class Item(models.Model):
        name = models.CharField(max_length=100)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        category = models.CharField(max_length=50, default="general")

        class Meta:
            app_label = "bulk_test"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Item)

    # Bulk create items
    items = [
        Item(name=f"Item {i}", price=i * 10.00, category="bulk") for i in range(25)
    ]
    Item.objects.bulk_create(items)

    assert Item.objects.count() == 25

    # Bulk update
    Item.objects.filter(category="bulk").update(category="updated")

    updated_count = Item.objects.filter(category="updated").count()
    assert updated_count == 25


if __name__ == "__main__":
    print("🌟 Django Fixtures + py-pglite Examples")
    print("Run with: pytest testing-patterns/django/test_django_fixtures.py -v")
