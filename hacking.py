#!/usr/bin/env python3
"""Development script for py-pglite package."""

import subprocess
import sys
from pathlib import Path


def run_command(description: str, command: list[str], cwd: Path | None = None) -> bool:
    """Run a command and return True if successful."""
    print(f"\n{'=' * 50}")
    print(f"🔄 {description}")
    print(f"{'=' * 50}")
    
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=True
        )
        print(f"✅ {description} completed successfully")
        if result.stdout.strip():
            print("Output:")
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed")
        if e.stdout:
            print("STDOUT:")
            print(e.stdout)
        if e.stderr:
            print("STDERR:")
            print(e.stderr)
        return False


def main():
    """Run the complete development workflow."""
    print("🚀 py-pglite Development Workflow")
    
    # Get current directory
    current_dir = Path.cwd()
    print(f"📁 Working in: {current_dir}")
    
    # Commands to run
    commands = [
        ("Installing package in development mode", ["pip", "install", "-e", "."]),
        ("Running ruff check (linting)", ["ruff", "check", "py_pglite/"]),
        ("Running ruff format check", ["ruff", "format", "--check", "py_pglite/"]),
        ("Running type checker (mypy)", ["mypy", "py_pglite/"]),
        ("Running basic tests", ["python", "-m", "pytest", "examples/test_basic.py", "-v"]),
        ("Running advanced tests", ["python", "-m", "pytest", "examples/test_advanced.py", "-v"]),
        ("Running utils tests", ["python", "-m", "pytest", "examples/test_utils.py", "-v"]),
        ("Running FastAPI integration tests", ["python", "-m", "pytest", "examples/test_fastapi_integration.py", "-v"]),
    ]
    
    # Track success/failure
    results = []
    
    for description, command in commands:
        success = run_command(description, command, current_dir)
        results.append((description, success))
        
        # Continue even if some steps fail, but warn
        if not success:
            print(f"⚠️  {description.split('(')[0].strip()} failed, but continuing...")
    
    # Print summary
    print(f"\n{'=' * 50}")
    print("📊 SUMMARY")
    print(f"{'=' * 50}")
    
    for description, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {description}")
    
    # Exit with error code if any command failed
    if not all(success for _, success in results):
        print("\n⚠️  Some commands failed. Check the output above.")
        sys.exit(1)
    else:
        print("\n🎉 All commands completed successfully!")


if __name__ == "__main__":
    main() 