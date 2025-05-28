"""JavaScript compiler module."""
import os
from typing import List

from team_query.builders.compilers.js.compiler import JavaScriptCompiler
from team_query.models import QueriesFile, SQLConfig


def compile(
    queries_files: List[QueriesFile], config: SQLConfig, output_dir: str
) -> None:
    """Compile SQL queries to JavaScript code."""
    compiler = JavaScriptCompiler()
    compiler.compile(queries_files, config, output_dir)
