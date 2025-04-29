#!/usr/bin/env python3
"""
Script to build and publish the team-query package to PyPI.
"""
import os
import subprocess
import sys
from pathlib import Path


def run_command(command, description=None):
    """Run a shell command and print its output."""
    if description:
        print(f"\n{description}...")
    
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    
    if result.stdout:
        print(result.stdout)
    
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    
    if result.returncode != 0:
        print(f"Command failed with exit code {result.returncode}")
        sys.exit(result.returncode)
    
    return result


def clean_build_dirs():
    """Clean up build directories."""
    dirs_to_clean = ["dist", "build", "*.egg-info"]
    for dir_pattern in dirs_to_clean:
        run_command(f"rm -rf {dir_pattern}", f"Cleaning {dir_pattern}")


def build_package():
    """Build the package."""
    run_command("python -m build", "Building package")


def check_package():
    """Check the package with twine."""
    run_command("twine check dist/*", "Checking package")


def publish_to_pypi(test=False):
    """Publish the package to PyPI or TestPyPI."""
    if test:
        run_command(
            "twine upload --repository-url https://test.pypi.org/legacy/ dist/*",
            "Uploading to TestPyPI"
        )
    else:
        run_command("twine upload dist/*", "Uploading to PyPI")


def main():
    """Main function."""
    # Parse arguments
    test = "--test" in sys.argv
    
    # Clean up
    clean_build_dirs()
    
    # Build
    build_package()
    
    # Check
    check_package()
    
    # Confirm before publishing
    if test:
        repo = "TestPyPI"
    else:
        repo = "PyPI"
    
    confirm = input(f"\nReady to publish to {repo}. Continue? (y/n): ")
    if confirm.lower() != "y":
        print("Aborted.")
        return
    
    # Publish
    publish_to_pypi(test)
    
    print("\nPublishing completed successfully!")
    if test:
        print("\nTo install from TestPyPI:")
        print("pip install --index-url https://test.pypi.org/simple/ team-query")
    else:
        print("\nTo install from PyPI:")
        print("pip install team-query")
        print("\nTo install globally:")
        print("pip install -g team-query")


if __name__ == "__main__":
    main()
