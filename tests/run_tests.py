#!/usr/bin/env python3
"""
Test runner for all unit tests.
"""
import os
import sys
import unittest

# Add the parent directory to the path so we can import the tests
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from test_javascript_compiler import TestJavaScriptCompiler

# Import all test modules
from test_python_compiler import TestPythonCompiler
from test_sql_parser import TestSQLParser


def create_test_suite():
    """Create a test suite containing all tests."""
    test_suite = unittest.TestSuite()

    # Add tests from each test module
    loader = unittest.TestLoader()
    test_suite.addTest(loader.loadTestsFromTestCase(TestPythonCompiler))
    test_suite.addTest(loader.loadTestsFromTestCase(TestJavaScriptCompiler))
    test_suite.addTest(loader.loadTestsFromTestCase(TestSQLParser))

    return test_suite


def main():
    """Run the test suite."""
    # Create the test suite
    suite = create_test_suite()

    # Run the tests with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Return non-zero exit code if tests failed
    sys.exit(not result.wasSuccessful())


if __name__ == "__main__":
    main()
