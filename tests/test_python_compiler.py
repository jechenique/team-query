"""Unit tests for the Python compiler."""
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from team_query.builders.compilers.python.compiler import PythonCompiler
from team_query.models import Parameter, Query


class TestPythonCompiler(unittest.TestCase):
    """Test cases for the Python compiler."""

    def setUp(self):
        """Set up test fixtures."""
        self.compiler = PythonCompiler()

        # Create a temporary directory for output
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)

        # Sample query for testing
        self.sample_query = Query(
            name="GetAuthorById",
            description="Get author by ID",
            sql="SELECT * FROM authors WHERE id = %s",
            params=[Parameter(name="id", type="int", description="Author ID")],
        )
        # Set the file path as an attribute (not part of the constructor)
        self.sample_query.file_path = "authors.sql"

        # Sample query with conditional blocks
        self.conditional_query = Query(
            name="ListPosts",
            description="List posts with optional filtering",
            sql="""
            SELECT * FROM posts 
            WHERE 1=1
            -- {author_id} AND author_id = %s -- }
            -- {published_only} AND published = TRUE -- }
            """,
            params=[
                Parameter(
                    name="author_id", type="int", description="Filter by author ID"
                ),
                Parameter(
                    name="published_only",
                    type="bool",
                    description="Show only published posts",
                ),
            ],
        )
        # Set the file path as an attribute
        self.conditional_query.file_path = "posts.sql"

    def tearDown(self):
        """Clean up after tests."""
        self.temp_dir.cleanup()

    def test_parse_params(self):
        """Test parameter parsing from a query."""
        params = self.compiler._parse_params(self.sample_query)

        # Check that we have the correct number of parameters
        self.assertEqual(len(params), 1)

        # Check that the parameter has the correct name, type, and description
        param_name, param_type, param_desc = params[0]
        self.assertEqual(param_name, "id")
        self.assertEqual(param_type, "int")
        self.assertEqual(param_desc, "Author ID")

    def test_parse_conditional_params(self):
        """Test parsing parameters from a query with conditional blocks."""
        params = self.compiler._parse_params(self.conditional_query)

        # Check that we have the correct number of parameters
        self.assertEqual(len(params), 2)

        # Check that the parameters have the correct names
        param_names = [p[0] for p in params]
        self.assertIn("author_id", param_names)
        self.assertIn("published_only", param_names)

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_utils_file(self, mock_file):
        """Test generation of the utils.py file."""
        # Create a mock QueriesFile
        queries_file = MagicMock()
        queries_file.path = "authors.sql"
        queries_file.queries = [self.sample_query]

        # Create a mock SQLConfig
        config = MagicMock()

        self.compiler.compile([queries_file], config, str(self.output_dir))

        # Check that the utils.py file was created
        utils_path = os.path.join(self.output_dir, "utils.py")
        mock_file.assert_any_call(utils_path, "w", encoding="utf-8", newline="\n")

        # Check that the file contains the SQLParser class
        handle = mock_file()
        written_content = "".join(
            [call.args[0] for call in handle.write.call_args_list]
        )
        self.assertIn("class SQLParser:", written_content)
        self.assertIn("def process_conditional_blocks", written_content)
        self.assertIn("def cleanup_sql", written_content)

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_query_file(self, mock_file):
        """Test generation of a query file."""
        # Create a mock QueriesFile
        queries_file = MagicMock()
        queries_file.path = "authors.sql"
        queries_file.queries = [self.sample_query]

        # Create a mock SQLConfig
        config = MagicMock()

        self.compiler.compile([queries_file], config, str(self.output_dir))

        # Check that the authors.py file was created
        authors_path = os.path.join(self.output_dir, "authors.py")
        mock_file.assert_any_call(authors_path, "w", encoding="utf-8")

        # Check that the file contains the GetAuthorById function
        handle = mock_file()
        written_content = "".join(
            [call.args[0] for call in handle.write.call_args_list]
        )
        self.assertIn("def GetAuthorById(conn, id: int = None)", written_content)
        self.assertIn("List[Dict]", written_content)  # Check return type
        self.assertIn("SELECT * FROM authors WHERE id = %s", written_content)

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_conditional_query(self, mock_file):
        """Test generation of a query with conditional blocks."""
        # Create a test query with conditional blocks
        query = Query(
            name="ListPosts",
            sql="""
            SELECT * FROM posts 
            WHERE 1=1
            -- {author_id} AND author_id = %s -- }
            -- {published_only} AND published = TRUE -- }
            """,
            params=[
                Parameter(name="author_id", type="int"),
                Parameter(name="published_only", type="bool"),
            ],
        )
        query.file_path = "posts.sql"

        # Create a mock QueriesFile
        queries_file = MagicMock()
        queries_file.module_name = "posts"
        queries_file.queries = [query]

        # Create a mock SQLConfig
        config = MagicMock()
        config.db_type = "postgres"

        # Create a compiler instance
        compiler = PythonCompiler()

        # Mock the file operations
        with patch("builtins.open", mock_open()) as mock_file, patch(
            "os.path.exists", return_value=True
        ), patch("os.makedirs"):
            # Call the compile method
            compiler.compile([queries_file], config, "/tmp/output")

            # Get the content that would have been written to the file
            calls = mock_file.return_value.__enter__.return_value.write.call_args_list
            written_content = "".join(call[0][0] for call in calls)

            # Check if the function signature is in the content (with type annotations)
            self.assertIn(
                "def ListPosts(conn, author_id: int = None, published_only: bool = None)",
                written_content,
            )
            self.assertIn("List[Dict]", written_content)  # Check return type

    @patch("builtins.open", new_callable=mock_open)
    def test_generate_init_file(self, mock_file):
        """Test generation of the __init__.py file."""
        # Create mock QueriesFiles
        queries_file1 = MagicMock()
        queries_file1.path = "authors.sql"
        queries_file1.queries = [self.sample_query]

        queries_file2 = MagicMock()
        queries_file2.path = "posts.sql"
        queries_file2.queries = [self.conditional_query]

        # Create a mock SQLConfig
        config = MagicMock()
        config.db_type = "postgres"

        # Create a compiler instance
        compiler = PythonCompiler()

        # Mock the file operations
        with patch("builtins.open", mock_open()) as mock_file, patch(
            "os.path.exists", return_value=True
        ), patch("os.makedirs"):
            # Call the compile method
            compiler.compile([queries_file1, queries_file2], config, "/tmp/output")

            # Get the content that would have been written to the file
            calls = mock_file.return_value.__enter__.return_value.write.call_args_list
            written_content = "".join(call[0][0] for call in calls)

            # Check if the function signature is in the content (with type annotations)
            self.assertIn("def GetAuthorById(conn, id: int = None)", written_content)
            self.assertIn(
                "def ListPosts(conn, author_id: int = None, published_only: bool = None)",
                written_content,
            )
            self.assertIn("List[Dict]", written_content)  # Check return type

    @patch("builtins.open", new_callable=mock_open)
    def test_multiple_queries_same_file(self, mock_file):
        """Test generation of multiple queries from the same SQL file."""
        # Create test queries
        query1 = Query(
            name="GetAuthorById",
            sql="SELECT * FROM authors WHERE id = %s",
            params=[Parameter(name="id", type="int")],
        )
        query1.file_path = "authors.sql"

        query2 = Query(
            name="ListAuthors",
            sql="SELECT * FROM authors",
            params=[],
        )
        query2.file_path = "authors.sql"

        # Create a mock QueriesFile
        queries_file = MagicMock()
        queries_file.module_name = "authors"
        queries_file.queries = [query1, query2]

        # Create a mock SQLConfig
        config = MagicMock()
        config.db_type = "postgres"

        # Create a compiler instance
        compiler = PythonCompiler()

        # Mock the file operations
        with patch("builtins.open", mock_open()) as mock_file, patch(
            "os.path.exists", return_value=True
        ), patch("os.makedirs"):
            # Call the compile method
            compiler.compile([queries_file], config, "/tmp/output")

            # Get the content that would have been written to the file
            calls = mock_file.return_value.__enter__.return_value.write.call_args_list
            written_content = "".join(call[0][0] for call in calls)

            # Check if both function signatures are in the content (with type annotations)
            self.assertIn("def GetAuthorById(conn, id: int = None)", written_content)
            self.assertIn("def ListAuthors(conn, )", written_content)
            self.assertIn("List[Dict]", written_content)  # Check return type

    def test_sanitize_name(self):
        """Test sanitizing a name for use in Python."""
        # Test with a normal name
        name = "authors"
        sanitized = self.compiler.sanitize_name(name)
        self.assertEqual(sanitized, "authors")

        # Test with a name starting with a number
        name = "123authors"
        sanitized = self.compiler.sanitize_name(name)
        self.assertEqual(sanitized, "_123authors")

        # Test with invalid characters
        name = "authors-table"
        sanitized = self.compiler.sanitize_name(name)
        self.assertEqual(sanitized, "authors_table")


if __name__ == "__main__":
    unittest.main()
