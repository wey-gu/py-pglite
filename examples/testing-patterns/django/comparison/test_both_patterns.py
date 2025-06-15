"""
🔄 Django + py-pglite: Pattern Comparison
=========================================

Side-by-side comparison of both Django integration patterns.

This example demonstrates:
• Pattern 1: Lightweight/Socket approach
• Pattern 2: Full Integration/Custom backend approach
• When to use each pattern
• Performance and feature differences

📋 Pattern Comparison:

┌─────────────────┬─────────────────────────┬────────────────────────────┐
│ Aspect          │ Lightweight/Socket      │ Full Integration/Backend   │
├─────────────────┼─────────────────────────┼────────────────────────────┤
│ Backend         │ django.db.backends.     │ py_pglite.django.backend   │
│                 │ postgresql (standard)   │ (custom)                   │
├─────────────────┼─────────────────────────┼────────────────────────────┤
│ Setup           │ Minimal, socket-based   │ Full integration features  │
├─────────────────┼─────────────────────────┼────────────────────────────┤
│ Performance     │ Fast, lightweight       │ Optimized, feature-rich   │
├─────────────────┼─────────────────────────┼────────────────────────────┤
│ Features        │ Standard PostgreSQL     │ Enhanced + py-pglite       │
├─────────────────┼─────────────────────────┼────────────────────────────┤
│ Use Case        │ Simple testing,         │ Comprehensive testing,     │
│                 │ quick prototypes        │ production-like setup      │
└─────────────────┴─────────────────────────┴────────────────────────────┘

🎯 Choose based on your needs:
• Lightweight: Quick tests, minimal dependencies
• Full Integration: Advanced features, comprehensive testing
"""

import pytest
from django.db import connection, models

# Mark as Django test
pytestmark = pytest.mark.django


def test_pattern_1_lightweight_socket(configured_django):
    """
    🔹 Pattern 1: Lightweight/Socket Approach

    Features:
    • Standard PostgreSQL backend (django.db.backends.postgresql)
    • Direct socket connection to PGlite
    • Minimal setup and dependencies
    • Fast and simple
    """
    print("\n🔹 Testing Pattern 1: Lightweight/Socket")

    # Define model
    class SocketProduct(models.Model):
        name = models.CharField(max_length=100)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        active = models.BooleanField(default=True)

        class Meta:
            app_label = "pattern_comparison_socket"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(SocketProduct)

    # Basic operations work perfectly
    product = SocketProduct.objects.create(
        name="Socket Widget", price=29.99, active=True
    )

    assert SocketProduct.objects.count() == 1
    assert product.name == "Socket Widget"
    assert product.price == 29.99

    # Standard PostgreSQL features available
    active_products = SocketProduct.objects.filter(active=True)
    assert active_products.count() == 1

    print("✅ Pattern 1: Basic operations work great!")


def test_pattern_2_full_integration_backend(django_pglite_db):
    """
    🔸 Pattern 2: Full Integration/Custom Backend Approach

    Features:
    • Custom py_pglite.django.backend
    • Full py-pglite integration
    • Advanced backend capabilities
    • Enhanced features and optimization
    """
    print("\n🔸 Testing Pattern 2: Full Integration/Backend")

    # Define model with advanced features
    class BackendProduct(models.Model):
        name = models.CharField(max_length=100)
        price = models.DecimalField(max_digits=10, decimal_places=2)
        active = models.BooleanField(default=True)
        metadata = models.JSONField(default=dict)  # JSON support
        tags = models.JSONField(default=list)  # JSON arrays

        class Meta:
            app_label = "pattern_comparison_backend"

    # Create table
    with connection.schema_editor() as schema_editor:
        schema_editor.create_model(BackendProduct)

    # Advanced operations with backend features
    product = BackendProduct.objects.create(
        name="Backend Widget",
        price=39.99,
        active=True,
        metadata={
            "category": "premium",
            "features": ["json_support", "backend_optimization"],
            "rating": 4.8,
        },
        tags=["premium", "widget", "advanced"],
    )

    assert BackendProduct.objects.count() == 1
    assert product.name == "Backend Widget"
    assert product.metadata["category"] == "premium"

    # Advanced JSON queries (backend feature)
    premium_products = BackendProduct.objects.filter(metadata__category="premium")
    assert premium_products.count() == 1

    # JSON array operations
    widget_products = BackendProduct.objects.filter(tags__contains=["widget"])
    assert widget_products.count() == 1

    print("✅ Pattern 2: Advanced features work great!")


def test_pattern_comparison_side_by_side():
    """
    🔄 Direct comparison of both patterns

    This test runs independently to show the differences clearly.
    """
    print("\n🔄 Pattern Comparison Summary")

    # Create summary comparison
    patterns = {
        "Pattern 1 (Lightweight/Socket)": {
            "backend": "django.db.backends.postgresql",
            "setup": "Minimal - direct socket connection",
            "features": "Standard PostgreSQL features",
            "performance": "Fast startup, lightweight",
            "use_case": "Simple testing, quick prototypes",
            "dependencies": "Minimal - standard Django + socket",
            "json_support": "Basic PostgreSQL JSON",
            "optimization": "Standard PostgreSQL optimization",
        },
        "Pattern 2 (Full Integration/Backend)": {
            "backend": "py_pglite.django.backend",
            "setup": "Full integration with custom backend",
            "features": "Enhanced PostgreSQL + py-pglite features",
            "performance": "Optimized for comprehensive testing",
            "use_case": "Comprehensive testing, production-like",
            "dependencies": "Full py-pglite Django integration",
            "json_support": "Enhanced JSON with backend optimization",
            "optimization": "Custom backend optimization",
        },
    }

    # Print comparison
    print("\n📊 Feature Comparison:")
    for pattern_name, details in patterns.items():
        print(f"\n{pattern_name}:")
        for feature, description in details.items():
            print(f"  • {feature}: {description}")

    # Decision guide
    print("\n🎯 When to use each pattern:")
    print("\n🔹 Use Lightweight/Socket when:")
    print("  • You want minimal setup and dependencies")
    print("  • You're doing basic Django model testing")
    print("  • You need fast startup times")
    print("  • You're prototyping or doing simple tests")

    print("\n🔸 Use Full Integration/Backend when:")
    print("  • You want comprehensive Django testing")
    print("  • You need advanced PostgreSQL features")
    print("  • You're building production-like test suites")
    print("  • You want backend optimization features")


def test_pattern_performance_characteristics():
    """
    🏃 Performance characteristics comparison

    Shows the performance trade-offs between patterns.
    """
    print("\n🏃 Performance Characteristics:")

    characteristics = {
        "Startup Time": {
            "Lightweight/Socket": "⚡ Very Fast - Direct socket connection",
            "Full Integration/Backend": "🚀 Fast - Backend initialization included",
        },
        "Memory Usage": {
            "Lightweight/Socket": "💾 Lower - Minimal overhead",
            "Full Integration/Backend": "💾 Moderate - Full backend features",
        },
        "Query Performance": {
            "Lightweight/Socket": "🔄 Standard PostgreSQL performance",
            "Full Integration/Backend": "🔄 Enhanced with backend optimization",
        },
        "Feature Availability": {
            "Lightweight/Socket": "📦 Standard Django + PostgreSQL",
            "Full Integration/Backend": "📦 Enhanced Django + py-pglite features",
        },
    }

    for metric, values in characteristics.items():
        print(f"\n{metric}:")
        for pattern, description in values.items():
            print(f"  {pattern}: {description}")


def test_migration_between_patterns():
    """
    🔄 Migration guidance between patterns

    Shows how to migrate from one pattern to another.
    """
    print("\n🔄 Migration Between Patterns:")

    migration_guide = {
        "From Lightweight to Full Integration": [
            (
                "1. Change ENGINE from 'django.db.backends.postgresql' to "
                "'py_pglite.django.backend'"
            ),
            "2. Update fixture usage from 'configured_django' to 'django_pglite_db'",
            "3. Remove manual socket configuration (handled by backend)",
            "4. Add JSON field usage for enhanced features",
            "5. Update test assertions for backend-specific optimizations",
        ],
        "From Full Integration to Lightweight": [
            (
                "1. Change ENGINE from 'py_pglite.django.backend' to "
                "'django.db.backends.postgresql'"
            ),
            "2. Update fixture usage from 'django_pglite_db' to 'configured_django'",
            "3. Add manual socket configuration in conftest.py",
            "4. Remove backend-specific JSON optimizations",
            "5. Simplify test setup for minimal dependencies",
        ],
    }

    for direction, steps in migration_guide.items():
        print(f"\n{direction}:")
        for step in steps:
            print(f"  {step}")

    print("\n💡 Migration Tips:")
    print("  • Both patterns work with the same Django models")
    print("  • You can run both patterns in the same project")
    print("  • Choose based on your specific testing needs")
    print("  • Start with Lightweight, upgrade to Full Integration as needed")


if __name__ == "__main__":
    print("🔄 Django + py-pglite: Pattern Comparison")
    print(
        "Run with: "
        "pytest testing-patterns/django/comparison/test_both_patterns.py -v -s"
    )
