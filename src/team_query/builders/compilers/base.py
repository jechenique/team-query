"""Base compiler module with common functionality."""
import os
import shutil
from typing import Any, Dict, List, Optional

from team_query.models import QueriesFile, Query, SQLConfig


class BaseCompiler:
    """Base compiler class with common functionality."""

    def __init__(self):
        """Initialize the base compiler."""
        self.query_files = []
        self.output_dir = ""
        self.config = None

    def create_output_dir(self, output_dir: str) -> None:
        """Create the output directory if it doesn't exist."""
        os.makedirs(output_dir, exist_ok=True)
        self.output_dir = output_dir

    def clean_output_directory(self, output_dir: str) -> None:
        """Clean the output directory by removing all files and subdirectories."""
        if os.path.exists(output_dir):
            print(f"Cleaning output directory: {output_dir}")
            try:
                # Remove all files and subdirectories
                for item in os.listdir(output_dir):
                    item_path = os.path.join(output_dir, item)
                    if os.path.isfile(item_path):
                        os.unlink(item_path)
                    elif os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                print(f"Output directory cleaned: {output_dir}")
            except (FileNotFoundError, PermissionError) as e:
                # Handle the case where the directory exists but can't be accessed
                print(f"Warning: Could not clean directory {output_dir}: {str(e)}")
                # Create it anyway
                os.makedirs(output_dir, exist_ok=True)
        else:
            print(f"Output directory does not exist, will be created: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)

    def sanitize_name(self, name: str) -> str:
        """Sanitize a name to be used as a function or variable name."""
        # Replace non-alphanumeric characters with underscores
        sanitized = "".join(c if c.isalnum() else "_" for c in name)
        # Ensure the name starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "f_" + sanitized
        return sanitized

    def compile(
        self, queries_files: List[QueriesFile], config: SQLConfig, output_dir: str
    ) -> None:
        """Compile queries to code."""
        self.query_files = queries_files
        self.config = config
        self.clean_output_directory(output_dir)
        self.create_output_dir(output_dir)
        # This method should be implemented by subclasses
        raise NotImplementedError("Subclasses must implement compile method")
