"""
Python query builder for team-query.
"""
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from team_query.models import Query, QueryType


class PythonQueryBuilder:
    """Base class for Python query builders."""

    def __init__(self, conn, query: Query, params: Dict[str, Any] = None):
        """
        Initialize a query builder.

        Args:
            conn: Database connection
            query: Query object
            params: Initial parameters
        """
        self.conn = conn
        self.query = query
        self.params = params or {}
        self.where_conditions = {}
        self.order_by_clause = None
        self.limit_value = None
        self.offset_value = None
        self._executed = False

    def where(self, **kwargs) -> "PythonQueryBuilder":
        """
        Add WHERE conditions to the query.

        Args:
            **kwargs: Field-value pairs for WHERE conditions

        Returns:
            Self for method chaining
        """
        self.where_conditions.update(kwargs)
        return self

    def orderBy(self, column: str, direction: str = "asc") -> "PythonQueryBuilder":
        """
        Add ORDER BY clause to the query.

        Args:
            column: Column to order by
            direction: Sort direction (asc or desc)

        Returns:
            Self for method chaining
        """
        if direction.lower() not in ["asc", "desc"]:
            raise ValueError("Direction must be 'asc' or 'desc'")

        self.order_by_clause = f"{column} {direction.upper()}"
        return self

    def limit(self, limit: int) -> "PythonQueryBuilder":
        """
        Add LIMIT clause to the query.

        Args:
            limit: Maximum number of rows to return

        Returns:
            Self for method chaining
        """
        if not isinstance(limit, int) or limit < 0:
            raise ValueError("Limit must be a non-negative integer")

        self.limit_value = limit
        return self

    def offset(self, offset: int) -> "PythonQueryBuilder":
        """
        Add OFFSET clause to the query.

        Args:
            offset: Number of rows to skip

        Returns:
            Self for method chaining
        """
        if not isinstance(offset, int) or offset < 0:
            raise ValueError("Offset must be a non-negative integer")

        self.offset_value = offset
        return self

    def _build_dynamic_sql(self) -> Tuple[str, List[Any]]:
        """
        Build dynamic SQL based on the builder state.

        Returns:
            Tuple of (sql, params)
        """
        # Start with the base SQL
        sql = self.query.sql

        # Determine which parameters are provided
        provided_params = set()
        for param in self.query.params:
            if param.name in self.params and self.params[param.name] is not None:
                provided_params.add(param.name)

        # Add WHERE conditions
        if self.where_conditions:
            # Check if there's already a WHERE clause
            if "WHERE" not in sql.upper():
                sql += " WHERE "
            else:
                sql += " AND "

            conditions = []
            for field, value in self.where_conditions.items():
                conditions.append(f"{field} = :{field}")
                self.params[field] = value
                provided_params.add(field)

            sql += " AND ".join(conditions)

        # Add ORDER BY clause
        if self.order_by_clause:
            if "ORDER BY" not in sql.upper():
                sql += f" ORDER BY {self.order_by_clause}"
            else:
                # Replace existing ORDER BY
                import re

                sql = re.sub(
                    r"ORDER BY.*?(?=(LIMIT|OFFSET|$))",
                    f"ORDER BY {self.order_by_clause} ",
                    sql,
                    flags=re.IGNORECASE | re.DOTALL,
                )

        # Add LIMIT clause
        if self.limit_value is not None:
            if "LIMIT" not in sql.upper():
                sql += f" LIMIT :{self._get_unique_param_name('limit')}"
                self.params[self._get_unique_param_name("limit")] = self.limit_value
                provided_params.add(self._get_unique_param_name("limit"))
            else:
                # Replace existing LIMIT
                import re

                sql = re.sub(
                    r"LIMIT\s+:?\w+",
                    f"LIMIT :{self._get_unique_param_name('limit')}",
                    sql,
                    flags=re.IGNORECASE,
                )
                self.params[self._get_unique_param_name("limit")] = self.limit_value
                provided_params.add(self._get_unique_param_name("limit"))

        # Add OFFSET clause
        if self.offset_value is not None:
            if "OFFSET" not in sql.upper():
                sql += f" OFFSET :{self._get_unique_param_name('offset')}"
                self.params[self._get_unique_param_name("offset")] = self.offset_value
                provided_params.add(self._get_unique_param_name("offset"))
            else:
                # Replace existing OFFSET
                import re

                sql = re.sub(
                    r"OFFSET\s+:?\w+",
                    f"OFFSET :{self._get_unique_param_name('offset')}",
                    sql,
                    flags=re.IGNORECASE,
                )
                self.params[self._get_unique_param_name("offset")] = self.offset_value
                provided_params.add(self._get_unique_param_name("offset"))

        # Process conditional blocks
        from team_query.parser import SQLParser

        sql = SQLParser.build_dynamic_sql(sql, provided_params)

        # Extract parameters from the processed SQL
        import re

        param_names = []
        param_values = []

        for match in re.finditer(r":([a-zA-Z_][a-zA-Z0-9_]*)", sql):
            param_name = match.group(1)
            if param_name in self.params:
                param_names.append(param_name)
                param_values.append(self.params[param_name])
                # Replace named parameter with positional
                sql = sql.replace(f":{param_name}", f"${len(param_names)}", 1)

        return sql, param_values

    def _get_unique_param_name(self, base_name: str) -> str:
        """
        Generate a unique parameter name to avoid conflicts.

        Args:
            base_name: Base parameter name

        Returns:
            Unique parameter name
        """
        if base_name not in self.params:
            return base_name

        i = 1
        while f"{base_name}_{i}" in self.params:
            i += 1

        return f"{base_name}_{i}"

    def execute(self) -> Any:
        """
        Execute the query and return results.

        Returns:
            Query results based on query type
        """
        if self._executed:
            raise RuntimeError("Query already executed")

        self._executed = True
        sql, params = self._build_dynamic_sql()

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

            # Handle different query types
            if self.query.query_type and self.query.query_type.value == "select":
                result = cur.fetchall()
                return result
            elif self.query.query_type and self.query.query_type.value in [
                "insert",
                "update",
                "delete",
            ]:
                self.conn.commit()
                if "RETURNING" in sql.upper():
                    result = cur.fetchall()
                    return result
                return cur.rowcount
            else:
                result = cur.fetchall()
                return result


class SelectQueryBuilder(PythonQueryBuilder):
    """Builder for SELECT queries."""

    def __init__(self, conn, query: Query, params: Dict[str, Any] = None):
        super().__init__(conn, query, params)
        if not query.query_type or query.query_type.value != "select":
            raise ValueError("Query must be a SELECT query")


class InsertQueryBuilder(PythonQueryBuilder):
    """Builder for INSERT queries."""

    def __init__(self, conn, query: Query, params: Dict[str, Any] = None):
        super().__init__(conn, query, params)
        if not query.query_type or query.query_type.value != "insert":
            raise ValueError("Query must be an INSERT query")


class UpdateQueryBuilder(PythonQueryBuilder):
    """Builder for UPDATE queries."""

    def __init__(self, conn, query: Query, params: Dict[str, Any] = None):
        super().__init__(conn, query, params)
        if not query.query_type or query.query_type.value != "update":
            raise ValueError("Query must be an UPDATE query")


class DeleteQueryBuilder(PythonQueryBuilder):
    """Builder for DELETE queries."""

    def __init__(self, conn, query: Query, params: Dict[str, Any] = None):
        super().__init__(conn, query, params)
        if not query.query_type or query.query_type.value != "delete":
            raise ValueError("Query must be a DELETE query")
