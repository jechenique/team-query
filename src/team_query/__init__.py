"""
team-query: A Python clone of sqlc with YAML-based SQL queries and multi-language compilation.
"""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("team-query")
except PackageNotFoundError:  # running from a source tree without install
    __version__ = "0.0.0"
