"""
SQL parser for team-query that supports sqlc-style query definitions.
"""
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from team_query.models import Parameter, Query, QueryType


class SQLCStyleParser:
    """Parser for SQL queries in sqlc-style format."""

    # Regex patterns for sqlc-style queries
    QUERY_PATTERN = r"--\s*name:\s*(\w+)\s*:(\w+)\s*\n((?:(?:--(?!\s*name:).*\n)|(?:\s*\n))*)(([\s\S]+?)(?=(?:--\s*name:)|\Z))"
    PARAM_PATTERN = r"(?<!:):(\w+)"
    PARAM_TYPE_PATTERN = r"--\s*param:\s*(\w+)\s+(\w+)(?:\s+(.+))?"

    # Query type mapping
    QUERY_TYPE_MAP = {
        "one": QueryType.SELECT,
        "many": QueryType.SELECT,
        "exec": QueryType.UPDATE,  # For INSERT, UPDATE, DELETE without returning
        "execrows": QueryType.UPDATE,  # For INSERT, UPDATE, DELETE returning row count
        "execresult": QueryType.UPDATE,  # For INSERT, UPDATE, DELETE returning result
    }

    # Default type mapping for parameters
    DEFAULT_TYPE_MAP = {
        "int": "int",
        "integer": "int",
        "bigint": "int",
        "smallint": "int",
        "text": "string",
        "varchar": "string",
        "char": "string",
        "string": "string",
        "bool": "bool",
        "boolean": "bool",
        "float": "float",
        "real": "float",
        "double": "float",
        "numeric": "decimal",
        "decimal": "decimal",
        "date": "date",
        "time": "time",
        "timestamp": "datetime",
        "timestamptz": "datetime",
        "json": "json",
        "jsonb": "json",
        "uuid": "string",
        "bytea": "bytes",
    }

    @classmethod
    def parse_sql_file(cls, sql_content: str) -> List[Query]:
        """Parse a SQL file containing sqlc-style query definitions."""
        # Normalize line endings to Unix style
        sql_content = sql_content.replace("\r\n", "\n").replace("\r", "\n")
        lines = sql_content.split("\n")
        queries: List[Query] = []
        current_name = None
        current_type = None
        comment_lines: List[str] = []
        sql_lines: List[str] = []
        for line in lines:
            header_match = re.match(r"--\s*name:\s*(\w+)\s*:\s*(\w+)", line)
            if header_match:
                # Flush previous query
                if current_name:
                    sql_text = "\n".join(sql_lines).strip()
                    # Parse parameter types from comment lines
                    param_types: Dict[str, str] = {}
                    param_descriptions: Dict[str, str] = {}
                    for cl in comment_lines:
                        pm = re.match(cls.PARAM_TYPE_PATTERN, cl)
                        if pm:
                            pname, ptype, pdesc = pm.group(1), pm.group(2), pm.group(3)
                            param_types[pname] = cls.DEFAULT_TYPE_MAP.get(
                                ptype.lower(), ptype
                            )
                            if pdesc:
                                param_descriptions[pname] = pdesc
                    # Extract parameters from SQL
                    params = []
                    seen = set()
                    for pm in re.finditer(cls.PARAM_PATTERN, sql_text):
                        pname = pm.group(1)
                        if pname not in seen:
                            seen.add(pname)
                            params.append(
                                Parameter(
                                    name=pname,
                                    type=param_types.get(pname, "string"),
                                    description=param_descriptions.get(pname),
                                )
                            )
                    qtype = cls.QUERY_TYPE_MAP.get(current_type.lower())
                    queries.append(
                        Query(
                            name=current_name,
                            sql=sql_text,
                            params=params,
                            query_type=qtype,
                            # Store the original directive in returns
                            returns=current_type.lower(),
                        )
                    )
                # Start a new query
                current_name = header_match.group(1)
                current_type = header_match.group(2)
                comment_lines = []
                sql_lines = []
                continue
            if current_name:
                if line.strip().startswith("--"):
                    comment_lines.append(line)
                else:
                    sql_lines.append(line)
        # Flush last query
        if current_name:
            sql_text = "\n".join(sql_lines).strip()
            param_types: Dict[str, str] = {}
            param_descriptions: Dict[str, str] = {}
            for cl in comment_lines:
                pm = re.match(cls.PARAM_TYPE_PATTERN, cl)
                if pm:
                    pname, ptype, pdesc = pm.group(1), pm.group(2), pm.group(3)
                    param_types[pname] = cls.DEFAULT_TYPE_MAP.get(ptype.lower(), ptype)
                    if pdesc:
                        param_descriptions[pname] = pdesc
            params = []
            seen = set()
            for pm in re.finditer(cls.PARAM_PATTERN, sql_text):
                pname = pm.group(1)
                if pname not in seen:
                    seen.add(pname)
                    params.append(
                        Parameter(
                            name=pname,
                            type=param_types.get(pname, "string"),
                            description=param_descriptions.get(pname),
                        )
                    )
            qtype = cls.QUERY_TYPE_MAP.get(current_type.lower())
            queries.append(
                Query(
                    name=current_name,
                    sql=sql_text,
                    params=params,
                    query_type=qtype,
                    # Store the original directive in returns
                    returns=current_type.lower(),
                )
            )
        return queries

    @classmethod
    def _infer_return_type(cls, query_type_str: str, sql: str) -> Optional[str]:
        """Infer the return type based on the query type and SQL."""
        query_type_str = query_type_str.lower()

        if query_type_str == "one":
            # Try to infer from the table name
            table_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1)
                # Convert to singular and capitalize for a type name
                return cls._table_to_type(table_name)
            return "Record"

        elif query_type_str == "many":
            # Try to infer from the table name
            table_match = re.search(r"FROM\s+(\w+)", sql, re.IGNORECASE)
            if table_match:
                table_name = table_match.group(1)
                # Convert to singular and capitalize for a type name
                return f"{cls._table_to_type(table_name)}[]"
            return "Record[]"

        elif query_type_str == "exec":
            return None

        elif query_type_str == "execrows":
            return "int"

        elif query_type_str == "execresult":
            if "RETURNING" in sql.upper():
                table_match = re.search(
                    r"(INSERT|UPDATE|DELETE)\s+.*?(?:INTO|FROM)\s+(\w+)",
                    sql,
                    re.IGNORECASE,
                )
                if table_match:
                    table_name = table_match.group(2)
                    return cls._table_to_type(table_name)
            return "Record"

        return None

    @staticmethod
    def _table_to_type(table_name: str) -> str:
        """Convert a table name to a type name."""
        # Remove trailing 's' if present (simple pluralization)
        if table_name.endswith("s"):
            table_name = table_name[:-1]

        # Capitalize first letter
        return table_name[0].upper() + table_name[1:]
