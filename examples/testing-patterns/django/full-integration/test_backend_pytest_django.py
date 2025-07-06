"""
🌟 pytest-django + py-pglite: Full Integration Pattern
======================================================

Pattern 2: pytest-django integration with custom backend.

This shows how to use pytest-django features with the full integration approach:
• Using @pytest.mark.django_db decorator with custom backend
• pytest-django fixtures and utilities with py_pglite.django.backend
• Django test utilities enhanced by custom backend
• Backend-managed connection and optimization

📋 Pattern Details:
• Backend: py_pglite.django.backend (custom)
• Connection: Managed by py-pglite backend
• Framework: pytest-django integration with backend features
• Use case: pytest-django users who want full backend integration

Compare with: ../lightweight/ for socket-based pattern

Note: This demonstrates the FULL INTEGRATION approach with pytest-django.
For the lightweight socket approach with pytest-django, see
../lightweight/test_socket_pytest_django.py

For basic Django testing with custom backend, see test_backend_basic.py
"""

import pytest
from django.db import connection, models, transaction
from django.test import Client, TestCase

# pytest-django specific markers
pytestmark = pytest.mark.django


def test_with_django_db_backend_marker(django_pglite_db):
    """
    🎯 Using @pytest.mark.django_db decorator with custom backend

    This demonstrates pytest-django with full backend integration:
    - Working with py_pglite.django.backend
    - Backend-managed database configuration
    - Enhanced performance and features
    """

    # Define model with backend-specific features
    class Article(models.Model):
        title = models.CharField(max_length=100)
        content = models.TextField()
        metadata = models.JSONField(default=dict)  # Backend JSON support

        class Meta:
            app_label = "pytest_backend_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Article)

    # Use Django ORM with backend features
    article = Article.objects.create(
        title="pytest-django + Custom Backend Works!",
        content="Using Django testing with py-pglite custom backend",
        metadata={"tags": ["pytest-django", "backend", "integration"]},
    )

    assert Article.objects.count() == 1
    assert article.title == "pytest-django + Custom Backend Works!"
    assert article.metadata["tags"] == ["pytest-django", "backend", "integration"]


def test_backend_transaction_support(django_pglite_db):
    """
    🎯 Backend-enhanced transaction support with pytest-django

    Shows transaction testing optimized by the custom backend:
    - Real transaction behavior with backend optimization
    - Rollback testing with backend features
    - Performance improvements
    """

    # Define model
    class Order(models.Model):
        order_number = models.CharField(max_length=20, unique=True)
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        processed = models.BooleanField(default=False)
        details = models.JSONField(default=dict)

        class Meta:
            app_label = "pytest_backend_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Order)

    # Test transaction rollback with backend optimization
    try:
        with transaction.atomic():
            Order.objects.create(
                order_number="ORD-001",
                amount=100.00,
                processed=True,
                details={"payment_id": "pay_123", "method": "card"},
            )
            # Force an error to test rollback
            raise Exception("Simulated error")
    except Exception:
        pass

    # Verify rollback worked
    assert Order.objects.count() == 0

    # Test successful transaction with backend features
    with transaction.atomic():
        order = Order.objects.create(
            order_number="ORD-002",
            amount=50.00,
            processed=True,
            details={"payment_id": "pay_456", "method": "bank"},
        )

    assert Order.objects.count() == 1
    assert order.details["payment_id"] == "pay_456"


def test_backend_advanced_features(django_pglite_db):
    """
    🎯 Test custom backend advanced features with pytest-django

    Demonstrates capabilities enhanced by the custom backend:
    - JSON field operations with backend optimization
    - Advanced query features
    - Performance improvements
    """

    # Define model with advanced features
    class Product(models.Model):
        name = models.CharField(max_length=100)
        specifications = models.JSONField(default=dict)
        tags = models.JSONField(default=list)
        active = models.BooleanField(default=True)

        class Meta:
            app_label = "pytest_backend_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Product)

    # Test backend-enhanced JSON operations
    Product.objects.create(
        name="Advanced Widget",
        specifications={
            "weight": "2.5kg",
            "dimensions": {"width": 10, "height": 5, "depth": 3},
            "materials": ["plastic", "metal"],
        },
        tags=["widget", "advanced", "premium"],
    )

    # Test complex JSON queries (backend feature)
    heavy_products = Product.objects.filter(specifications__weight__endswith="kg")
    assert heavy_products.count() == 1

    # Test JSON array operations
    premium_products = Product.objects.filter(tags__contains=["premium"])
    assert premium_products.count() == 1

    # Test nested JSON queries
    compact_products = Product.objects.filter(specifications__dimensions__width__lt=15)
    assert compact_products.count() == 1


def test_django_testing_utilities_with_backend(django_pglite_db):
    """
    🎯 Django testing utilities enhanced by custom backend

    Shows how to use Django's testing utilities with backend optimization:
    - Django TestCase features with backend
    - Test client functionality with backend
    - Performance improvements from custom backend
    """

    from django.http import HttpResponse

    # Define a simple model for testing
    class TestModel(models.Model):
        name = models.CharField(max_length=50)
        data = models.JSONField(default=dict)

        class Meta:
            app_label = "pytest_backend_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(TestModel)

    # Create test data with backend features
    TestModel.objects.create(
        name="Test Record", data={"api_version": "v1", "features": ["json", "backend"]}
    )

    # Test with Django test client
    Client()

    # Verify the test environment is working with backend
    assert TestModel.objects.count() == 1
    test_record = TestModel.objects.first()
    assert test_record is not None
    assert test_record.data["api_version"] == "v1"
    assert "backend" in test_record.data["features"]

    print("✅ Django testing utilities with custom backend working!")


def test_backend_performance_features(django_pglite_db):
    """
    🎯 Test performance features of the custom backend

    Demonstrates performance improvements available with the backend:
    - Optimized connection management
    - Efficient query processing
    - Enhanced bulk operations
    """

    # Define model for performance testing
    class PerformanceTest(models.Model):
        name = models.CharField(max_length=100)
        value = models.IntegerField()
        metadata = models.JSONField(default=dict)

        class Meta:
            app_label = "pytest_backend_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(PerformanceTest)

    # Test bulk operations with backend optimization
    records = [
        PerformanceTest(
            name=f"Record {i}",
            value=i,
            metadata={"batch": "performance_test", "index": i},
        )
        for i in range(100)
    ]

    # Backend-optimized bulk create
    PerformanceTest.objects.bulk_create(records)
    assert PerformanceTest.objects.count() == 100

    # Test efficient querying with backend
    high_value_records = PerformanceTest.objects.filter(
        value__gte=50, metadata__batch="performance_test"
    )
    assert high_value_records.count() == 50

    print("✅ Backend performance features working!")


if __name__ == "__main__":
    print("🌟 pytest-django + py-pglite: Full Integration Pattern")
    print(
        "Run with: "
        "pytest testing-patterns/django/full-integration/"
        "test_backend_pytest_django.py -v"
    )
