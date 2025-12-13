"""Test runner script for ToneGrab."""

import subprocess
import sys
from pathlib import Path


def run_tests(args=None):
    """Run pytest with given arguments."""
    cmd = [sys.executable, "-m", "pytest"]
    
    if args:
        cmd.extend(args)
    else:
        # Default: run all tests with coverage
        cmd.extend([
            "tests/",
            "-v",
            "--tb=short",
        ])
    
    result = subprocess.run(cmd, cwd=Path(__file__).parent)
    return result.returncode


def run_unit_tests():
    """Run only unit tests."""
    return run_tests(["tests/unit/", "-v"])


def run_integration_tests():
    """Run only integration tests."""
    return run_tests(["tests/integration/", "-v"])


def run_with_coverage():
    """Run tests with coverage report."""
    return run_tests([
        "tests/",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html",
    ])


if __name__ == "__main__":
    if len(sys.argv) > 1:
        command = sys.argv[1]
        if command == "unit":
            sys.exit(run_unit_tests())
        elif command == "integration":
            sys.exit(run_integration_tests())
        elif command == "coverage":
            sys.exit(run_with_coverage())
        else:
            print(f"Unknown command: {command}")
            print("Usage: python run_tests.py [unit|integration|coverage]")
            sys.exit(1)
    else:
        sys.exit(run_tests())
