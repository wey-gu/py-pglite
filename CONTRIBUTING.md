# 🛠️ Hacking

## Local Development

```bash
git clone https://github.com/wey-gu/py-pglite
cd py-pglite
pip install -e ".[dev]"

# Run development workflow
python hacking.py
```

## Running Tests

```bash
# Run all tests
pytest

# Run specific test categories
pytest examples/test_basic.py      # Basic functionality
pytest examples/test_advanced.py   # Advanced features
pytest examples/test_utils.py      # Utility functions
pytest examples/test_fastapi_integration.py  # FastAPI integration

# Run with coverage
pytest --cov=py_pglite
```

## Code Quality

```bash
# Lint and format
ruff check py_pglite/
ruff format py_pglite/

# Type checking
mypy py_pglite/

# Run full development workflow
python hacking.py
```
