"""Unit tests for the SQL parser module."""
import os
import re
import sys
import unittest

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from team_query.models import Parameter, Query
from team_query.parser import SQLParser


class TestSQLParser(unittest.TestCase):
    """Test cases for the SQL parser."""

    def test_extract_wildcards(self):
        """Test extracting wildcard parameters from a SQL query."""
        # Test with named parameters
        query = Query(
            name="GetUser", sql="SELECT * FROM users WHERE name = :name AND age = :age"
        )
        wildcards = SQLParser.extract_wildcards(query)
        self.assertEqual(wildcards, {"name", "age"})

        # Test with positional parameters (should not be included in wildcards)
        query = Query(
            name="GetUser", sql="SELECT * FROM users WHERE name = $1 AND age = $2"
        )
        wildcards = SQLParser.extract_wildcards(query)
        self.assertEqual(wildcards, set())

        # Test with mixed parameters
        query = Query(
            name="GetUser", sql="SELECT * FROM users WHERE name = :name AND age = $1"
        )
        wildcards = SQLParser.extract_wildcards(query)
        self.assertEqual(wildcards, {"name"})

    def test_validate_params(self):
        """Test validating parameters in a SQL query."""
        # Test with all parameters defined
        query = Query(
            name="GetUser",
            sql="SELECT * FROM users WHERE name = :name AND age = :age",
            params=[
                Parameter(name="name", type="string"),
                Parameter(name="age", type="int"),
            ],
        )
        errors = SQLParser.validate_params(query)
        self.assertEqual(errors, [])

        # Test with missing parameters
        query = Query(
            name="GetUser",
            sql="SELECT * FROM users WHERE name = :name AND age = :age",
            params=[Parameter(name="name", type="string")],
        )
        errors = SQLParser.validate_params(query)
        self.assertEqual(len(errors), 1)
        self.assertIn("Missing parameter definitions: age", errors[0])

    def test_replace_wildcards(self):
        """Test replacing wildcards in SQL with actual values."""
        sql = "SELECT * FROM users WHERE name = :name AND age = :age"
        params = {"name": "'John'", "age": "30"}
        result = SQLParser.replace_wildcards(sql, params)
        expected = "SELECT * FROM users WHERE name = 'John' AND age = 30"
        self.assertEqual(result, expected)

    def test_extract_conditional_blocks(self):
        """Test extracting conditional blocks from SQL."""
        sql = """
        SELECT * FROM users 
        WHERE 1=1
        -- {name} AND name = 'John' -- }
        -- {age} AND age > 18 -- }
        """
        blocks = SQLParser.extract_conditional_blocks(sql)
        self.assertEqual(len(blocks), 2)
        self.assertIn("name", blocks)
        self.assertIn("age", blocks)
        self.assertEqual(len(blocks["name"]), 1)
        self.assertEqual(len(blocks["age"]), 1)
        self.assertIn("AND name = 'John'", blocks["name"][0][1])
        self.assertIn("AND age > 18", blocks["age"][0][1])

    def test_build_dynamic_sql(self):
        """Test building dynamic SQL based on provided parameters."""
        # Test including conditional blocks
        sql = """
        SELECT * FROM users 
        WHERE 1=1
        -- {name} AND name = 'John' -- }
        -- {age} AND age > 18 -- }
        """
        provided_params = {"name", "age"}
        result = SQLParser.build_dynamic_sql(sql, provided_params)
        self.assertIn("AND name = 'John'", result)
        self.assertIn("AND age > 18", result)

        # Test excluding conditional blocks
        sql = """
        SELECT * FROM users 
        WHERE 1=1
        -- {name} AND name = 'John' -- }
        -- {age} AND age > 18 -- }
        """
        provided_params = {"name"}
        result = SQLParser.build_dynamic_sql(sql, provided_params)
        self.assertIn("AND name = 'John'", result)
        self.assertNotIn("AND age > 18", result)

        # Test cleaning up WHERE clause
        sql = """
        SELECT * FROM users 
        WHERE 1=1
        -- {name} AND name = 'John' -- }
        """
        provided_params = set()
        result = SQLParser.build_dynamic_sql(sql, provided_params)
        self.assertNotIn("AND name = 'John'", result)
        self.assertIn("WHERE TRUE", result)

    def test_prepare_query(self):
        """Test preparing a query for execution."""
        # Test with named parameters
        query = Query(
            name="GetUser", sql="SELECT * FROM users WHERE name = :name AND age = :age"
        )
        sql, param_names = SQLParser.prepare_query(query)
        self.assertEqual(param_names, ["name", "age"])
        self.assertIn("$1", sql)
        self.assertIn("$2", sql)

        # Test with provided parameters
        query = Query(
            name="GetUser",
            sql="""
            SELECT * FROM users 
            WHERE 1=1
            -- {name} AND name = :name -- }
            -- {age} AND age = :age -- }
            """,
        )
        provided_params = {"name"}
        sql, param_names = SQLParser.prepare_query(query, provided_params)
        self.assertEqual(param_names, ["name"])
        self.assertIn("name = $1", sql)
        self.assertNotIn("age = ", sql)


if __name__ == "__main__":
    unittest.main()
