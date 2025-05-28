"""Python compiler module."""
import os
from typing import List

from team_query.builders.compilers.python.compiler import PythonCompiler
from team_query.models import QueriesFile, SQLConfig


def compile(
    queries_files: List[QueriesFile], config: SQLConfig, output_dir: str
) -> None:
    """Compile SQL queries to Python code."""
    compiler = PythonCompiler()
    compiler.compile(queries_files, config, output_dir)
