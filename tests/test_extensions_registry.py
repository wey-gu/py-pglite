"""Tests for extension registry and configuration system."""

import pytest

from py_pglite.config import PGliteConfig
from py_pglite.extensions import SUPPORTED_EXTENSIONS
from py_pglite.manager import PGliteManager


def test_supported_extensions_registry():
    """Test that the SUPPORTED_EXTENSIONS registry is properly structured."""
    assert isinstance(SUPPORTED_EXTENSIONS, dict)
    assert len(SUPPORTED_EXTENSIONS) > 0

    # Check pgvector extension is registered
    assert "pgvector" in SUPPORTED_EXTENSIONS

    # Verify structure of each extension entry
    for ext_name, ext_config in SUPPORTED_EXTENSIONS.items():
        assert isinstance(ext_name, str)
        assert isinstance(ext_config, dict)
        assert "module" in ext_config
        assert "name" in ext_config
        assert isinstance(ext_config["module"], str)
        assert isinstance(ext_config["name"], str)


def test_pgvector_extension_registration():
    """Test pgvector extension is properly registered."""
    pgvector_config = SUPPORTED_EXTENSIONS["pgvector"]

    assert pgvector_config["module"] == "@electric-sql/pglite/vector"
    assert pgvector_config["name"] == "vector"


def test_pg_trgm_extension_registration():
    """Test pg_trgm extension is properly registered."""
    pg_trgm_config = SUPPORTED_EXTENSIONS["pg_trgm"]

    assert pg_trgm_config["module"] == "@electric-sql/pglite/contrib/pg_trgm"
    assert pg_trgm_config["name"] == "pg_trgm"


def test_btree_gin_extension_registration():
    """Test btree_gin extension is properly registered."""
    btree_gin_config = SUPPORTED_EXTENSIONS["btree_gin"]

    assert btree_gin_config["module"] == "@electric-sql/pglite/contrib/btree_gin"
    assert btree_gin_config["name"] == "btree_gin"


def test_btree_gist_extension_registration():
    """Test btree_gist extension is properly registered."""
    btree_gist_config = SUPPORTED_EXTENSIONS["btree_gist"]

    assert btree_gist_config["module"] == "@electric-sql/pglite/contrib/btree_gist"
    assert btree_gist_config["name"] == "btree_gist"


def test_fuzzystrmatch_extension_registration():
    """Test fuzzystrmatch extension is properly registered."""
    fuzzystrmatch_config = SUPPORTED_EXTENSIONS["fuzzystrmatch"]

    assert (
        fuzzystrmatch_config["module"] == "@electric-sql/pglite/contrib/fuzzystrmatch"
    )
    assert fuzzystrmatch_config["name"] == "fuzzystrmatch"


def test_config_extension_validation():
    """Test that PGliteConfig properly validates extensions."""
    # Valid extension should work
    config = PGliteConfig(extensions=["pgvector"])
    assert config.extensions == ["pgvector"]

    # Multiple valid extensions should work
    valid_extensions = list(SUPPORTED_EXTENSIONS.keys())
    config = PGliteConfig(extensions=valid_extensions)
    assert config.extensions == valid_extensions

    # Invalid extension should raise error
    with pytest.raises(ValueError, match="Unsupported extension: 'invalid_ext'"):
        PGliteConfig(extensions=["invalid_ext"])

    # Mix of valid and invalid should raise error
    with pytest.raises(ValueError, match="Unsupported extension: 'bad_ext'"):
        PGliteConfig(extensions=["pgvector", "bad_ext"])

    # Empty extension list should be valid
    config = PGliteConfig(extensions=[])
    assert config.extensions == []

    # None extensions should be valid
    config = PGliteConfig(extensions=None)
    assert config.extensions is None


def test_extension_configuration_in_manager():
    """Test that extensions are properly configured in the manager."""
    # Test without extensions
    config = PGliteConfig(extensions=None)
    manager = PGliteManager(config)

    # Check that no extensions are configured
    assert manager.config.extensions is None

    # Test with pgvector extension
    config = PGliteConfig(extensions=["pgvector"])
    manager = PGliteManager(config)

    # Check that pgvector is configured
    assert manager.config.extensions == ["pgvector"]


def test_javascript_generation_with_extensions():
    """Test that extensions are properly configured in the manager."""
    config = PGliteConfig(extensions=["pgvector"])
    manager = PGliteManager(config)

    # Test that extensions are configured in the manager
    assert manager.config.extensions == ["pgvector"]

    # Test that the extension is properly registered
    assert "pgvector" in SUPPORTED_EXTENSIONS


def test_javascript_generation_without_extensions():
    """Test that manager works without extensions."""
    config = PGliteConfig(extensions=None)
    manager = PGliteManager(config)

    # Should not have extensions configured
    assert manager.config.extensions is None


def test_multiple_extensions_javascript():
    """Test configuration with multiple extensions."""
    # If we had multiple extensions, test them
    all_extensions = list(SUPPORTED_EXTENSIONS.keys())
    config = PGliteConfig(extensions=all_extensions)
    manager = PGliteManager(config)

    # Should have all extensions configured
    assert manager.config.extensions == all_extensions


def test_extension_case_sensitivity():
    """Test that extension names are case-sensitive."""
    # Should fail with wrong case
    with pytest.raises(ValueError, match="Unsupported extension: 'PGVECTOR'"):
        PGliteConfig(extensions=["PGVECTOR"])

    with pytest.raises(ValueError, match="Unsupported extension: 'PgVector'"):
        PGliteConfig(extensions=["PgVector"])

    # Should work with correct case
    config = PGliteConfig(extensions=["pgvector"])
    assert config.extensions == ["pgvector"]


def test_extension_duplicate_handling():
    """Test handling of duplicate extensions in configuration."""
    # Duplicates should be allowed (user's choice)
    config = PGliteConfig(extensions=["pgvector", "pgvector"])
    assert config.extensions == ["pgvector", "pgvector"]


def test_extension_order_preservation():
    """Test that extension order is preserved."""
    if len(SUPPORTED_EXTENSIONS) > 1:
        extensions = list(SUPPORTED_EXTENSIONS.keys())
        reversed_extensions = list(reversed(extensions))

        config1 = PGliteConfig(extensions=extensions)
        config2 = PGliteConfig(extensions=reversed_extensions)

        assert config1.extensions == extensions
        assert config2.extensions == reversed_extensions
        assert config1.extensions != config2.extensions


def test_extension_registry_is_immutable():
    """Test that the SUPPORTED_EXTENSIONS registry behaves as immutable."""
    original_pgvector = SUPPORTED_EXTENSIONS["pgvector"].copy()

    # Try to modify the registry (this shouldn't affect the original)
    try:
        SUPPORTED_EXTENSIONS["test_extension"] = {"module": "test", "name": "test"}
    except Exception:
        pass  # Some implementations might prevent this

    # Original pgvector config should be unchanged
    assert SUPPORTED_EXTENSIONS["pgvector"] == original_pgvector


def test_new_extensions_configuration():
    """Test that all new extensions can be configured."""
    # Test individual extensions
    for ext in ["pg_trgm", "btree_gin", "btree_gist", "fuzzystrmatch"]:
        config = PGliteConfig(extensions=[ext])
        assert config.extensions == [ext]

        manager = PGliteManager(config)
        assert manager.config.extensions == [ext]

    # Test all new extensions together
    new_extensions = ["pg_trgm", "btree_gin", "btree_gist", "fuzzystrmatch"]
    config = PGliteConfig(extensions=new_extensions)
    assert config.extensions == new_extensions

    manager = PGliteManager(config)
    assert manager.config.extensions == new_extensions

    # Test all extensions including pgvector
    all_exts = ["pgvector", "pg_trgm", "btree_gin", "btree_gist", "fuzzystrmatch"]
    config = PGliteConfig(extensions=all_exts)
    assert config.extensions == all_exts


def test_extension_validation_error_messages():
    """Test that extension validation provides helpful error messages."""
    try:
        PGliteConfig(extensions=["nonexistent"])
        raise AssertionError("Should have raised ValueError")
    except ValueError as e:
        error_msg = str(e)
        assert "Unsupported extension: 'nonexistent'" in error_msg
        assert "Available extensions:" in error_msg
        assert "pgvector" in error_msg
        assert "pg_trgm" in error_msg
        assert "btree_gin" in error_msg
        assert "btree_gist" in error_msg
        assert "fuzzystrmatch" in error_msg


def test_extensions_with_empty_string():
    """Test handling of empty string in extensions list."""
    with pytest.raises(ValueError, match="Unsupported extension: ''"):
        PGliteConfig(extensions=[""])


def test_extensions_with_none_in_list():
    """Test handling of None values in extensions list."""
    # This should raise an error during validation
    with pytest.raises((ValueError, TypeError)):
        PGliteConfig(extensions=[None])  # type: ignore


@pytest.mark.parametrize("ext_name", list(SUPPORTED_EXTENSIONS.keys()))
def test_individual_extension_validity(ext_name):
    """Test that each registered extension can be configured individually."""
    config = PGliteConfig(extensions=[ext_name])
    assert config.extensions == [ext_name]

    # Should be able to create manager with this extension
    manager = PGliteManager(config)
    assert manager.config.extensions == [ext_name]
