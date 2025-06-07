#!/usr/bin/env python3
"""
🚀 py-pglite Development Script
==============================

Usage:
    python scripts/dev.py              # Full workflow (like CI)
    python scripts/dev.py --quick      # Quick checks only
    python scripts/dev.py --test       # Tests only
    python scripts/dev.py --examples   # Examples only
    python scripts/dev.py --lint       # Linting only
"""

import argparse
import os
import subprocess
import sys
import time
from pathlib import Path


class DevWorkflow:
    def __init__(self):
        self.root_dir = Path(__file__).parent.parent
        self.start_time = time.time()
        self.failed_steps = []
        
        # Detect package manager based on environment variables
        self._setup_package_manager()
        
    def _setup_package_manager(self):
        """Detect and configure package manager commands."""
        use_uv = os.environ.get("UV") is not None
        use_pdm = os.environ.get("PDM_RUN_CWD") is not None

        if use_pdm:
            print("🔧 PDM_RUN_CWD environment variable detected - using pdm commands")
            self.install_cmd = ["pdm", "install"]
            self.python_cmd = ["pdm", "run", "python"]
            self.mypy_cmd = ["pdm", "run", "mypy"]
            self.ruff_cmd = ["pdm", "run", "ruff"]
        elif use_uv:
            print("🔧 UV environment variable detected - using uv commands")
            self.install_cmd = ["uv", "pip", "install", "-e"]
            self.python_cmd = ["uv", "run", "python"]
            self.mypy_cmd = ["uv", "run", "mypy"]
            self.ruff_cmd = ["uv", "run", "ruff"]
        else:
            print("🔧 Using standard pip and python commands")
            self.install_cmd = ["pip", "install", "-e"]
            self.python_cmd = ["python"]
            self.mypy_cmd = ["mypy"]
            self.ruff_cmd = ["ruff"]
        
    def run_command(self, description: str, command: list[str], cwd: Path | None = None) -> bool:
        """Run a command with Vite-style output."""
        print(f"\n⚡ {description}")
        print("─" * 50)
        
        start = time.time()
        try:
            result = subprocess.run(
                command, 
                cwd=cwd or self.root_dir, 
                capture_output=True, 
                text=True, 
                check=True
            )
            duration = time.time() - start
            print(f"✅ {description} ({duration:.2f}s)")
            if result.stdout.strip():
                print(result.stdout)
            return True
        except subprocess.CalledProcessError as e:
            duration = time.time() - start
            print(f"❌ {description} FAILED ({duration:.2f}s)")
            if e.stdout:
                print("STDOUT:", e.stdout)
            if e.stderr:
                print("STDERR:", e.stderr)
            self.failed_steps.append(description)
            return False

    def lint_check(self) -> bool:
        """Run linting checks."""
        print("\n🎨 LINTING")
        print("=" * 50)
        
        success = True
        if not self.run_command("Ruff linting", self.ruff_cmd + ["check", "py_pglite/"]):
            success = False
        if not self.run_command("Ruff formatting", self.ruff_cmd + ["format", "--check", "py_pglite/"]):
            success = False
        if not self.run_command("MyPy type checking", self.mypy_cmd + ["py_pglite/"]):
            success = False
            
        return success

    def test_core(self) -> bool:
        """Run core tests."""
        print("\n🧪 CORE TESTS")
        print("=" * 50)
        
        return self.run_command(
            "Core test suite", 
            self.python_cmd + ["-m", "pytest", "tests/", "-v", "--tb=short"]
        )

    def test_examples(self) -> bool:
        """Run example tests."""
        print("\n📚 EXAMPLE TESTS")
        print("=" * 50)
        
        success = True
        
        # SQLAlchemy examples
        if not self.run_command(
            "SQLAlchemy examples",
            self.python_cmd + ["-m", "pytest", "examples/testing-patterns/sqlalchemy/", "-v"]
        ):
            success = False
            
        # Django examples  
        if not self.run_command(
            "Django examples",
            self.python_cmd + ["-m", "pytest", "examples/testing-patterns/django/", "-v"]
        ):
            success = False
            
        # Fixtures showcase
        if not self.run_command(
            "Fixtures showcase",
            self.python_cmd + ["-m", "pytest", "examples/testing-patterns/test_fixtures_showcase.py", "-v"]
        ):
            success = False
            
        return success

    def test_quickstart(self) -> bool:
        """Test quickstart demos."""
        print("\n⚡ QUICKSTART DEMOS")
        print("=" * 50)
        
        success = True
        
        # Test instant demo
        if not self.run_command(
            "Instant demo",
            self.python_cmd + ["examples/quickstart/demo_instant.py"],
            cwd=self.root_dir
        ):
            success = False
            
        # Test performance demo
        if not self.run_command(
            "Performance demo", 
            self.python_cmd + ["examples/quickstart/simple_performance.py"],
            cwd=self.root_dir
        ):
            success = False
            
        return success

    def package_check(self) -> bool:
        """Check package building."""
        print("\n📦 PACKAGE CHECK")
        print("=" * 50)
        
        # Install in dev mode
        if self.install_cmd[0] == "pdm":
            # PDM installs dependencies from pyproject.toml automatically
            install_command = self.install_cmd
        else:
            # UV and pip need the "." to install current directory
            install_command = self.install_cmd + ["."]
        if not self.run_command("Install in dev mode", install_command):
            return False
            
        # Test import
        if not self.run_command(
            "Test imports",
            self.python_cmd + ["-c", "import py_pglite; from py_pglite import PGliteManager, PGliteConfig; print('✅ All imports working')"]
        ):
            return False
            
        return True

    def print_summary(self):
        """Print final summary."""
        duration = time.time() - self.start_time
        
        print("\n" + "=" * 60)
        print("📊 DEVELOPMENT SUMMARY")
        print("=" * 60)
        
        if self.failed_steps:
            print("❌ FAILED STEPS:")
            for step in self.failed_steps:
                print(f"   • {step}")
            print(f"\n⏱️  Total time: {duration:.2f}s")
            print("💡 Fix the issues above and try again")
            return False
        else:
            print("✅ ALL CHECKS PASSED!")
            print(f"⏱️  Total time: {duration:.2f}s")
            print("🚀 Ready for production!")
            return True

    def run_quick(self):
        """Quick checks for development."""
        print("🚀 py-pglite Quick Development Checks")
        
        success = True
        if not self.package_check():
            success = False
        if not self.lint_check():
            success = False
            
        return self.print_summary()

    def run_tests_only(self):
        """Run tests only."""
        print("🚀 py-pglite Test Suite")
        
        success = True
        if not self.test_core():
            success = False
        if not self.test_examples():
            success = False
            
        return self.print_summary()

    def run_examples_only(self):
        """Run examples only."""
        print("🚀 py-pglite Examples")
        
        success = True
        if not self.test_examples():
            success = False
        if not self.test_quickstart():
            success = False
            
        return self.print_summary()

    def run_full(self):
        """Full development workflow (like CI)."""
        print("🚀 py-pglite Full Development Workflow")
        print("🎯 This mirrors our CI pipeline exactly")
        
        success = True
        if not self.package_check():
            success = False
        if not self.lint_check():
            success = False
        if not self.test_core():
            success = False
        if not self.test_examples():
            success = False
        if not self.test_quickstart():
            success = False
            
        return self.print_summary()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="py-pglite development workflow")
    parser.add_argument("--quick", action="store_true", help="Quick checks only")
    parser.add_argument("--test", action="store_true", help="Tests only") 
    parser.add_argument("--examples", action="store_true", help="Examples only")
    parser.add_argument("--lint", action="store_true", help="Linting only")
    
    args = parser.parse_args()
    
    workflow = DevWorkflow()
    
    if args.quick:
        success = workflow.run_quick()
    elif args.test:
        success = workflow.run_tests_only()
    elif args.examples:
        success = workflow.run_examples_only()
    elif args.lint:
        success = workflow.lint_check() and workflow.print_summary()
    else:
        success = workflow.run_full()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main() 