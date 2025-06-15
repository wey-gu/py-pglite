"""
🌟 Django + py-pglite: Full Integration Pattern
==============================================

Pattern 2: Custom py-pglite Django backend integration.

This example demonstrates:
• Django ORM with custom py_pglite.django.backend
• Full py-pglite integration features
• Advanced backend capabilities
• Perfect for comprehensive Django testing

📋 Pattern Details:
• Backend: py_pglite.django.backend (custom)
• Connection: Managed by py-pglite backend
• Setup: Full integration features
• Use case: Comprehensive Django testing, production-like setup

Compare with: ../lightweight/ for socket-based pattern

Addresses community request: https://github.com/wey-gu/py-pglite/issues/5
"""

import pytest
from django.db import connection, models

# Mark as Django test
pytestmark = pytest.mark.django


def test_django_blog_with_backend_pattern(django_pglite_db):
    """
    🎯 Test Django ORM with Full Integration Pattern!

    This shows the custom backend approach:
    - Custom py_pglite.django.backend
    - Full py-pglite integration features
    - Advanced backend capabilities
    - Production-ready testing setup
    """

    # Define Django model
    class BlogPost(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        published = models.BooleanField(default=False)
        created_at = models.DateTimeField(auto_now_add=True)

        class Meta:
            app_label = "backend_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(BlogPost)

    # Test Django ORM operations
    post = BlogPost.objects.create(
        title="Full Integration Pattern + py-pglite = 🚀",
        content="Custom backend PostgreSQL testing is powerful!",
        published=True,
    )

    # Verify it works
    assert post.id is not None  # type: ignore
    assert post.created_at is not None  # type: ignore
    assert BlogPost.objects.count() == 1
    assert BlogPost.objects.filter(published=True).count() == 1

    # Test Django query features
    found_post = BlogPost.objects.get(title__icontains="Integration")
    assert found_post.content == "Custom backend PostgreSQL testing is powerful!"

    # Test advanced features available with custom backend
    assert BlogPost.objects.filter(created_at__isnull=False).count() == 1

    print("✅ Django Full Integration pattern example passed!")


def test_backend_specific_features(django_pglite_db):
    """
    🎯 Test features specific to the custom backend pattern.

    This demonstrates capabilities that are enhanced by the custom backend.
    """

    # Define model with PostgreSQL-specific features
    class AdvancedModel(models.Model):
        name = models.CharField(max_length=100)
        data = models.JSONField(default=dict)  # PostgreSQL JSON support
        tags = models.TextField(blank=True)  # Will use as array simulation

        class Meta:
            app_label = "backend_features"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(AdvancedModel)

    # Test JSON field support
    advanced = AdvancedModel.objects.create(
        name="Test Record",
        data={"features": ["json", "arrays", "custom_backend"]},
        tags="tag1,tag2,tag3",
    )

    # Verify JSON operations work
    assert advanced.data["features"] == ["json", "arrays", "custom_backend"]

    # Test querying JSON fields
    json_results = AdvancedModel.objects.filter(data__features__contains=["json"])
    assert json_results.count() == 1

    print("✅ Custom backend specific features working!")


if __name__ == "__main__":
    print("🌟 Django + py-pglite: Full Integration Pattern")
    print(
        "Run with: pytest testing-patterns/django/"
        "full-integration/test_backend_basic.py -v"
    )
