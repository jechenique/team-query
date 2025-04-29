"""
Compiler plugins for team-query.
"""
import abc
import os
from typing import Any, Dict, List

from team_query.models import QueriesFile, Query, SQLConfig


class BaseCompiler(abc.ABC):
    """Base class for query compilers."""

    @abc.abstractmethod
    def compile(
        self, queries_files: List[QueriesFile], config: SQLConfig, output_dir: str
    ) -> None:
        """Compile queries to target language."""
        pass

    def create_output_dir(self, output_dir: str) -> None:
        """Create output directory if it doesn't exist."""
        os.makedirs(output_dir, exist_ok=True)

    @staticmethod
    def get_type_mapping() -> Dict[str, str]:
        """Get mapping from SQL types to target language types."""
        return {}

    @staticmethod
    def sanitize_name(name: str) -> str:
        """Sanitize a name for use in target language."""
        return name
