"""
SQL parser for team-query.
"""
import re
from typing import Dict, List, Set, Tuple

from team_query.models import Query


class SQLParser:
    """Parser for SQL queries with wildcard support."""

    # Regex patterns for parameter placeholders
    NAMED_PARAM_PATTERN = r":([a-zA-Z_][a-zA-Z0-9_]*)"
    POSITIONAL_PARAM_PATTERN = r"\$([0-9]+)"

    # Regex pattern for conditional blocks
    CONDITIONAL_BLOCK_PATTERN = r"--\s*{\s*(\w+)(.*?)--\s*}"

    @classmethod
    def extract_wildcards(cls, query: Query) -> Set[str]:
        """Extract wildcard parameters from a SQL query."""
        wildcards = set()

        # Find all named parameters (:param)
        for match in re.finditer(cls.NAMED_PARAM_PATTERN, query.sql):
            wildcards.add(match.group(1))

        # Find all positional parameters ($1, $2, etc.)
        for match in re.finditer(cls.POSITIONAL_PARAM_PATTERN, query.sql):
            # We don't add positional parameters to wildcards
            pass

        return wildcards

    @classmethod
    def validate_params(cls, query: Query) -> List[str]:
        """Validate that all parameters in SQL are defined in the query."""
        wildcards = cls.extract_wildcards(query)
        defined_params = {param.name for param in query.params}

        missing_params = wildcards - defined_params
        extra_params = defined_params - wildcards

        errors = []
        if missing_params:
            errors.append(f"Missing parameter definitions: {', '.join(missing_params)}")

        # We don't consider extra parameters as errors, as they might be used
        # in prepared statements or dynamic queries

        return errors

    @classmethod
    def replace_wildcards(cls, sql: str, params: Dict[str, str]) -> str:
        """Replace wildcards in SQL with actual values."""
        result = sql

        # Replace named parameters
        for name, value in params.items():
            result = re.sub(f":{name}\\b", value, result)

        return result

    @classmethod
    def extract_conditional_blocks(cls, sql: str) -> Dict[str, List[Tuple[str, str]]]:
        """
        Extract conditional blocks from SQL based on comment markers.
        Returns a mapping of parameter names to their SQL blocks.
        """
        # Find all conditional blocks
        param_to_blocks = {}
        for match in re.finditer(cls.CONDITIONAL_BLOCK_PATTERN, sql, re.DOTALL):
            param_name = match.group(1)
            block_content = match.group(2)

            if param_name not in param_to_blocks:
                param_to_blocks[param_name] = []

            param_to_blocks[param_name].append((match.group(0), block_content))

        return param_to_blocks

    @classmethod
    def build_dynamic_sql(cls, sql: str, provided_params: Set[str]) -> str:
        """
        Build a dynamic SQL query based on provided parameters.
        """
        # Extract conditional blocks
        param_to_blocks = cls.extract_conditional_blocks(sql)

        # Process the SQL
        result_sql = sql

        # For each parameter, decide whether to include or exclude its blocks
        for param, blocks in param_to_blocks.items():
            for block_marker, block_content in blocks:
                if param in provided_params:
                    # Parameter is provided, keep the content but remove the markers
                    result_sql = result_sql.replace(block_marker, block_content)
                else:
                    # Parameter is not provided, remove the entire block
                    result_sql = result_sql.replace(block_marker, "")

        # Handle WHERE clauses more intelligently
        # First, normalize whitespace to make regex simpler
        result_sql = re.sub(r"\s+", " ", result_sql)

        # Find the WHERE clause if it exists
        where_match = re.search(
            r"(WHERE\s+)(.*?)(\s+(?:ORDER|GROUP|LIMIT|HAVING|UNION|INTERSECT|EXCEPT|$))",
            result_sql,
            re.IGNORECASE,
        )
        if where_match:
            where_keyword = where_match.group(1)
            where_conditions = where_match.group(2)
            where_end = where_match.group(3)

            # Remove any "1=1" or "TRUE" placeholder
            where_conditions = re.sub(
                r"^1=1\s+AND\s+", "", where_conditions, flags=re.IGNORECASE
            )
            where_conditions = re.sub(
                r"^TRUE\s+AND\s+", "", where_conditions, flags=re.IGNORECASE
            )
            where_conditions = re.sub(
                r"^1=1$", "TRUE", where_conditions, flags=re.IGNORECASE
            )

            # Check if there are any real conditions left
            if where_conditions.strip() and where_conditions.upper() != "TRUE":
                # Replace the WHERE clause with the cleaned up version
                result_sql = result_sql.replace(
                    where_match.group(0),
                    f"{where_keyword}{where_conditions}{where_end}",
                )
            else:
                # No conditions left, remove the WHERE clause entirely or replace with WHERE TRUE
                if re.search(r"(JOIN|FROM)\s+.*?\s+WHERE", result_sql, re.IGNORECASE):
                    # There's a FROM or JOIN, so we need a WHERE clause
                    result_sql = result_sql.replace(
                        where_match.group(0), f"{where_keyword}TRUE{where_end}"
                    )
                else:
                    # No FROM or JOIN, so we can remove the WHERE clause
                    result_sql = result_sql.replace(
                        where_match.group(0), where_end.lstrip()
                    )

        # Handle AND/OR at the beginning of conditions
        result_sql = re.sub(
            r"WHERE\s+AND\s+", "WHERE ", result_sql, flags=re.IGNORECASE
        )
        result_sql = re.sub(r"WHERE\s+OR\s+", "WHERE ", result_sql, flags=re.IGNORECASE)

        # Handle JOIN conditions
        result_sql = re.sub(
            r"(JOIN\s+\w+(?:\s+\w+)?\s+ON\s+.*?)\s+AND\s+$",
            r"\1",
            result_sql,
            flags=re.IGNORECASE,
        )

        return result_sql.strip()

    @classmethod
    def prepare_query(
        cls, query: Query, provided_params: Set[str] = None
    ) -> Tuple[str, List[str]]:
        """
        Prepare a query for execution, converting named parameters to positional.
        Returns the modified SQL and a list of parameter names in order.
        """
        sql = query.sql

        # Apply dynamic SQL generation if provided_params is given
        if provided_params is not None:
            sql = cls.build_dynamic_sql(sql, provided_params)

        param_names = []

        # Find all named parameters and replace them with positional
        for i, match in enumerate(re.finditer(cls.NAMED_PARAM_PATTERN, sql)):
            param_name = match.group(1)
            # Only include parameters that are provided
            if provided_params is None or param_name in provided_params:
                param_names.append(param_name)
                sql = sql.replace(f":{param_name}", f"${i+1}", 1)

        return sql, param_names
