"""
🌟 Django + py-pglite Example
============================

Zero-configuration Django testing with real PostgreSQL!

This example demonstrates:
• Django ORM with py-pglite (no setup required)
• Real PostgreSQL features in tests
• Perfect for testing Django models

Addresses community request: https://github.com/wey-gu/py-pglite/issues/5
"""

import pytest
from django.db import connection, models

# Mark as Django test
pytestmark = pytest.mark.django


def test_django_blog_with_pglite(configured_django):
    """
    🎯 Test Django ORM with zero configuration!

    This shows how easy it is to test Django models with py-pglite:
    - No database setup needed (handled by conftest.py)
    - Real PostgreSQL features
    - Lightning fast test execution
    - Clean abstraction via fixtures
    """

    # Define Django model (using proper abstraction)
    class BlogPost(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        published = models.BooleanField(default=False)

        class Meta:
            app_label = "example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(BlogPost)

    # Test Django ORM operations
    post = BlogPost.objects.create(
        title="Django + py-pglite = ❤️",
        content="Zero-config PostgreSQL testing is amazing!",
        published=True,
    )

    # Verify it works
    assert post.id is not None  # type: ignore
    assert BlogPost.objects.count() == 1
    assert BlogPost.objects.filter(published=True).count() == 1

    # Test Django query features
    found_post = BlogPost.objects.get(title__icontains="Django")
    assert found_post.content == "Zero-config PostgreSQL testing is amazing!"

    print("✅ Django + py-pglite example passed!")


if __name__ == "__main__":
    print("🌟 Django + py-pglite Example")
    print("Run with: pytest testing-patterns/django/test_django_quickstart.py -v")
