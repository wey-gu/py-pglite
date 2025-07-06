"""
�� Django + py-pglite: Lightweight/Socket Pattern
================================================

Pattern 1: Direct socket connection with standard PostgreSQL backend.

This example demonstrates:
• Django ORM with standard django.db.backends.postgresql
• Direct socket connection to PGlite
• Minimal setup, maximum simplicity
• Perfect for basic Django testing

📋 Pattern Details:
• Backend: django.db.backends.postgresql (standard)
• Connection: Direct socket to PGlite
• Setup: Minimal configuration
• Use case: Simple Django testing, quick prototypes

Compare with: ../full-integration/ for custom backend pattern

Addresses community request: https://github.com/wey-gu/py-pglite/issues/5
"""

import pytest

from django.db import connection
from django.db import models


# Mark as Django test
pytestmark = pytest.mark.django


def test_django_blog_with_socket_pattern(configured_django):
    """
    🎯 Test Django ORM with Lightweight/Socket Pattern!

    This shows the socket-based approach:
    - Standard PostgreSQL backend (django.db.backends.postgresql)
    - Direct socket connection to PGlite
    - Zero custom backend dependencies
    - Lightning fast and simple
    """

    # Define Django model (using proper abstraction)
    class BlogPost(models.Model):
        title = models.CharField(max_length=200)
        content = models.TextField()
        published = models.BooleanField(default=False)

        class Meta:
            app_label = "lightweight_example"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(BlogPost)

    # Test Django ORM operations
    post = BlogPost.objects.create(
        title="Lightweight Pattern + py-pglite = ❤️",
        content="Socket-based PostgreSQL testing is amazing!",
        published=True,
    )

    # Verify it works
    assert post.id is not None  # type: ignore
    assert BlogPost.objects.count() == 1
    assert BlogPost.objects.filter(published=True).count() == 1

    # Test Django query features
    found_post = BlogPost.objects.get(title__icontains="Lightweight")
    assert found_post.content == "Socket-based PostgreSQL testing is amazing!"

    print("✅ Django Lightweight/Socket pattern example passed!")


if __name__ == "__main__":
    print("🌟 Django + py-pglite: Lightweight/Socket Pattern")
    print(
        "Run with: pytest testing-patterns/django/lightweight/test_socket_basic.py -v"
    )
