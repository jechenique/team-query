"""
Data models for team-query.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Union


class QueryType(Enum):
    """Type of SQL query."""

    SELECT = "select"
    INSERT = "insert"
    UPDATE = "update"
    DELETE = "delete"


@dataclass
class Parameter:
    """SQL query parameter."""

    name: str
    type: str
    description: Optional[str] = None


@dataclass
class Query:
    """SQL query definition."""

    name: str
    sql: str
    params: List[Parameter] = field(default_factory=list)
    returns: Optional[str] = None
    description: Optional[str] = None
    query_type: Optional[QueryType] = None

    def __post_init__(self):
        """Infer query type if not provided."""
        if not self.query_type:
            sql_upper = self.sql.strip().upper()
            if sql_upper.startswith("SELECT"):
                self.query_type = QueryType.SELECT
            elif sql_upper.startswith("INSERT"):
                self.query_type = QueryType.INSERT
            elif sql_upper.startswith("UPDATE"):
                self.query_type = QueryType.UPDATE
            elif sql_upper.startswith("DELETE"):
                self.query_type = QueryType.DELETE


@dataclass
class QueriesFile:
    """Container for a set of queries from a single YAML file."""

    path: str
    queries: List[Query] = field(default_factory=list)


@dataclass
class PluginConfig:
    """Configuration for a code generation plugin."""

    plugin: str
    out: str
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SQLConfig:
    """SQL configuration."""

    queries: List[str]
    schema: List[str]
    engine: str
    gen: List[PluginConfig] = field(default_factory=list)


@dataclass
class ProjectConfig:
    """Project configuration."""

    name: str
    version: Optional[str] = None


@dataclass
class Config:
    """Main configuration."""

    version: str
    project: ProjectConfig
    sql: List[SQLConfig] = field(default_factory=list)
