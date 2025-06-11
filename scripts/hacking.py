#!/usr/bin/env python3
"""
🚨 DEPRECATED: Use scripts/dev.py instead
==========================================

This script is deprecated. Use the new unified development script:

    python scripts/dev.py              # Full workflow (like CI)
    python scripts/dev.py --quick      # Quick checks only
    python scripts/dev.py --test       # Tests only
    python scripts/dev.py --examples   # Examples only
    python scripts/dev.py --lint       # Linting only

Or use the convenient Makefile:

    make dev                           # Full workflow
    make quick                         # Quick checks
    make test                          # Tests only
    make examples                      # Examples only
    make lint                          # Linting only
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Show deprecation notice and redirect to new script."""
    print("🚨 DEPRECATED SCRIPT")
    print("=" * 50)
    print("This script is deprecated. Please use:")
    print("")
    print("🚀 Full development workflow:")
    print("   python scripts/dev.py")
    print("   make dev")
    print("")
    print("⚡ Quick checks:")
    print("   python scripts/dev.py --quick")
    print("   make quick")
    print("")
    print("🧪 Tests only:")
    print("   python scripts/dev.py --test")
    print("   make test")
    print("")
    print("📚 Examples only:")
    print("   python scripts/dev.py --examples")
    print("   make examples")
    print("")
    print("🎨 Linting only:")
    print("   python scripts/dev.py --lint")
    print("   make lint")
    print("")
    print("❓ Help:")
    print("   python scripts/dev.py --help")
    print("   make help")

    print("\n🔄 Auto-redirecting to full workflow...")

    # Auto-redirect to new script
    root_dir = Path(__file__).parent.parent
    result = subprocess.run([sys.executable, "scripts/dev.py"], cwd=root_dir)

    return result.returncode


if __name__ == "__main__":
    sys.exit(main())
