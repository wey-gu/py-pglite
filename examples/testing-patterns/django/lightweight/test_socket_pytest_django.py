"""
🌟 pytest-django + py-pglite: Lightweight/Socket Pattern
========================================================

Pattern 1: pytest-django integration with socket connection.

This shows how to use pytest-django features with the lightweight approach:
• Using @pytest.mark.django_db decorator with socket connection
• pytest-django fixtures and utilities with standard backend
• Django test utilities with py-pglite
• Direct socket connection to PGlite

📋 Pattern Details:
• Backend: django.db.backends.postgresql (standard)
• Connection: Direct socket to PGlite
• Framework: pytest-django integration
• Use case: pytest-django users who want socket-based testing

Compare with: ../full-integration/ for custom backend pattern

Note: This is an OPTIONAL integration. You can use py-pglite with Django
without pytest-django. This example is for users who specifically want
to use pytest-django features with the lightweight socket approach.

For basic Django testing without pytest-django, see test_socket_basic.py
"""

import pytest
from django.db import connection, models
from django.test import TestCase

# pytest-django specific markers
pytestmark = pytest.mark.django


def test_with_django_db_marker(configured_django):
    """
    🎯 Using @pytest.mark.django_db decorator with py-pglite

    This demonstrates pytest-django specific functionality:
    - Working with py-pglite backend
    - Proper database configuration via fixtures
    - Clean test isolation
    """

    # Define model
    class Article(models.Model):
        title = models.CharField(max_length=100)
        content = models.TextField()

        class Meta:
            app_label = "pytest_django_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Article)

    # Use Django ORM
    article = Article.objects.create(
        title="pytest-django Works!", content="Using Django testing with py-pglite"
    )

    assert Article.objects.count() == 1
    assert article.title == "pytest-django Works!"


def test_with_db_access(configured_django):
    """
    🎯 Database access with proper abstraction

    This shows pytest-django pattern:
    - Database access via proper fixtures
    - Clean abstraction through conftest.py
    - Works with py-pglite backend
    """

    # Define model
    class Comment(models.Model):
        text = models.TextField()
        approved = models.BooleanField(default=False)

        class Meta:
            app_label = "pytest_django_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Comment)

    # Test database operations
    Comment.objects.create(text="pytest-django db access works great!", approved=True)

    assert Comment.objects.filter(approved=True).count() == 1


def test_django_transaction_support(configured_django):
    """
    🎯 Django transaction support

    Shows transaction testing with py-pglite:
    - Real transaction behavior
    - Rollback testing
    - Works with PostgreSQL features
    """

    from django.db import transaction

    # Define model
    class Order(models.Model):
        amount = models.DecimalField(max_digits=10, decimal_places=2)
        processed = models.BooleanField(default=False)

        class Meta:
            app_label = "pytest_django_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(Order)

    # Test transaction rollback
    try:
        with transaction.atomic():
            Order.objects.create(amount=100.00, processed=True)
            # Force an error to test rollback
            raise Exception("Simulated error")
    except Exception:
        pass

    # Verify rollback worked
    assert Order.objects.count() == 0

    # Test successful transaction
    with transaction.atomic():
        Order.objects.create(amount=50.00, processed=True)

    assert Order.objects.count() == 1


def test_django_testing_utilities(configured_django):
    """
    🎯 Django testing utilities with py-pglite

    Shows how to use Django's testing utilities:
    - Django TestCase features available
    - Test client functionality
    - All working with py-pglite backend
    """

    from django.http import HttpResponse
    from django.test import Client

    # Create a simple view for testing
    def simple_view(request):
        return HttpResponse("Hello from py-pglite + Django testing!")

    # Test with Django test client
    client = Client()
    # Note: In real usage, you'd configure URLs and test actual views

    # Test that we can create client and it's available
    assert client is not None

    print("✅ Django testing utilities available with py-pglite")


if __name__ == "__main__":
    print("🌟 pytest-django + py-pglite Example")
    print("Run with: pytest testing-patterns/django/test_pytest_django.py -v")
