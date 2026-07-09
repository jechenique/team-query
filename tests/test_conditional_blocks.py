"""Regression tests for /* IF param */ conditional SQL blocks.

These cover three historical bugs:
1. The Python builder emitted `sql = process_conditional_blocks(sql, ...)`
   without ever embedding the raw SQL (NameError at runtime).
2. The conditional-processing template was indented 4 spaces inside an
   8-space `try:` body (SyntaxError at import).
3. Parameters that appear only inside an /* IF param */ condition were not
   registered by the parser, so the generated function had no way to
   receive the flag.
"""

import asyncio
import importlib
import os
import sys
import tempfile
import types
import unittest
from unittest.mock import MagicMock

# Add the src directory to the path so we can import the modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from team_query.builders.compilers.js.compiler import JavaScriptCompiler
from team_query.builders.compilers.python.compiler import PythonCompiler
from team_query.models import Parameter, QueriesFile, Query
from team_query.sql_parser import SQLCStyleParser

PROBE_SQL = """-- name: ProbeConditional :many
-- param: sort_created_desc bool Include created_at DESC ordering
SELECT id, external_id, created_at
FROM player
WHERE external_id IS NOT NULL
ORDER BY
/* IF sort_created_desc */ created_at DESC, /* END IF */
external_id ASC
LIMIT 5;
"""

MULTI_BLOCK_SQL = """-- name: SearchPlayers :many
-- param: name string Optional name filter
-- param: email string Optional email filter
-- param: sort_by_name bool Sort results by name
SELECT id, name, email FROM player
WHERE TRUE
/* IF name */ AND name ILIKE '%' || :name || '%' /* END IF */
/* IF email */ AND email = :email /* END IF */
ORDER BY
/* IF sort_by_name */ name, /* END IF */
id;
"""


def _install_psycopg_stubs():
    """Install minimal psycopg/psycopg_pool stand-ins so generated code imports.

    The generator itself does not depend on psycopg; only the generated code
    does. Stubs are only installed when the real packages are absent.
    """
    if "psycopg" in sys.modules:
        return
    try:
        importlib.import_module("psycopg")
        return
    except ImportError:
        pass
    psycopg = types.ModuleType("psycopg")
    psycopg.OperationalError = type("OperationalError", (Exception,), {})
    psycopg.AsyncConnection = type("AsyncConnection", (), {})
    rows = types.ModuleType("psycopg.rows")
    rows.dict_row = object()
    psycopg.rows = rows
    psycopg_pool = types.ModuleType("psycopg_pool")
    psycopg_pool.AsyncConnectionPool = type(
        "AsyncConnectionPool",
        (),
        {"check_connection": staticmethod(lambda conn: None)},
    )
    sys.modules["psycopg"] = psycopg
    sys.modules["psycopg.rows"] = rows
    sys.modules["psycopg_pool"] = psycopg_pool


class _RecordingCursor:
    """Async cursor stub that records executed SQL instead of hitting a DB."""

    def __init__(self, executed):
        self._executed = executed

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def execute(self, sql, params=None):
        self._executed.append((sql, params))

    async def fetchall(self):
        return []

    async def fetchone(self):
        return None


class _RecordingConnection:
    """Async connection stub accepted as-is by ensure_connection."""

    def __init__(self):
        self.executed = []

    async def set_autocommit(self, value):
        pass

    def cursor(self, row_factory=None):
        return _RecordingCursor(self.executed)


class TestConditionalBlocks(unittest.TestCase):
    """Test cases for conditional SQL block code generation."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

    def _parse_probe(self):
        queries = SQLCStyleParser.parse_sql_file(PROBE_SQL)
        return QueriesFile(path="probe.sql", queries=queries)

    def _generate_and_import(self, pkg_name, sql, module, options=None):
        """Generate a Python package from SQL and import one of its modules."""
        out_dir = os.path.join(self.temp_dir.name, pkg_name)
        queries_file = QueriesFile(
            path=f"{module}.sql", queries=SQLCStyleParser.parse_sql_file(sql)
        )
        PythonCompiler().compile([queries_file], MagicMock(), out_dir, options)
        _install_psycopg_stubs()
        sys.path.insert(0, self.temp_dir.name)
        try:
            return importlib.import_module(f"{pkg_name}.{module}")
        finally:
            sys.path.remove(self.temp_dir.name)

    def test_parser_registers_if_only_params(self):
        """Params referenced only in /* IF param */ conditions are parsed."""
        queries = SQLCStyleParser.parse_sql_file(PROBE_SQL)
        self.assertEqual(len(queries), 1)
        params = {p.name: p for p in queries[0].params}
        self.assertIn("sort_created_desc", params)
        self.assertEqual(params["sort_created_desc"].type, "bool")
        self.assertEqual(
            params["sort_created_desc"].description,
            "Include created_at DESC ordering",
        )

    def test_python_generated_module_compiles_and_runs(self):
        """Generated Python imports cleanly and includes/removes the block."""
        out_dir = os.path.join(self.temp_dir.name, "genpy")
        PythonCompiler().compile([self._parse_probe()], MagicMock(), out_dir)

        # The module must at least be valid Python (bug 2 was a SyntaxError)
        for fname in ("utils.py", "probe.py", "__init__.py"):
            with open(os.path.join(out_dir, fname), encoding="utf-8") as f:
                compile(f.read(), fname, "exec")

        _install_psycopg_stubs()
        sys.path.insert(0, self.temp_dir.name)
        try:
            probe = importlib.import_module("genpy.probe")
        finally:
            sys.path.remove(self.temp_dir.name)

        # Truthy flag: block content is included
        conn = _RecordingConnection()
        result, _ = asyncio.run(probe.ProbeConditional(conn, sort_created_desc=True))
        self.assertEqual(result, [])
        executed_sql, executed_params = conn.executed[-1]
        self.assertIn("created_at DESC,", executed_sql)
        self.assertNotIn("/* IF", executed_sql)
        self.assertIn("external_id ASC", executed_sql)
        self.assertEqual(executed_params, {"sort_created_desc": True})

        # Falsy/absent flag: block is removed entirely
        for flag in (False, None):
            conn = _RecordingConnection()
            asyncio.run(probe.ProbeConditional(conn, sort_created_desc=flag))
            executed_sql, _ = conn.executed[-1]
            self.assertNotIn("created_at DESC", executed_sql)
            self.assertNotIn("/* IF", executed_sql)
            self.assertIn("external_id ASC", executed_sql)

    def test_static_query_body_unchanged(self):
        """Queries without conditional blocks keep the static SQL path."""
        query = Query(
            name="GetPlayer",
            sql="SELECT id FROM player WHERE id = :id",
            params=[Parameter(name="id", type="int")],
        )
        body = PythonCompiler()._generate_function_body(query)
        self.assertIn('sql = """SELECT id FROM player WHERE id = :id"""', body)
        self.assertNotIn("process_conditional_blocks", body)

    def test_python_static_mode_compiles_and_runs(self):
        """conditional_mode: static expands blocks at generation time."""
        probe = self._generate_and_import(
            "genpy_static", PROBE_SQL, "probe", {"conditional_mode": "static"}
        )
        source = os.path.join(self.temp_dir.name, "genpy_static", "probe.py")
        with open(source, encoding="utf-8") as f:
            content = f.read()
        self.assertNotIn("process_conditional_blocks(", content.split("import")[-1])
        self.assertIn("if sort_created_desc:", content)

        conn = _RecordingConnection()
        asyncio.run(probe.ProbeConditional(conn, sort_created_desc=True))
        executed_sql, _ = conn.executed[-1]
        self.assertIn("created_at DESC,", executed_sql)
        conn = _RecordingConnection()
        asyncio.run(probe.ProbeConditional(conn, sort_created_desc=False))
        executed_sql, _ = conn.executed[-1]
        self.assertNotIn("created_at DESC", executed_sql)

    def test_python_static_mode_equivalent_to_runtime(self):
        """Static and runtime modes execute identical SQL for every combo."""
        runtime_mod = self._generate_and_import(
            "genpy_eq_rt", MULTI_BLOCK_SQL, "search"
        )
        static_mod = self._generate_and_import(
            "genpy_eq_st", MULTI_BLOCK_SQL, "search", {"conditional_mode": "static"}
        )
        for name in (None, "Jo"):
            for email in (None, "jo@example.com"):
                for sort_by_name in (True, False, None):
                    kwargs = {
                        "name": name,
                        "email": email,
                        "sort_by_name": sort_by_name,
                    }
                    conn_rt, conn_st = _RecordingConnection(), _RecordingConnection()
                    asyncio.run(runtime_mod.SearchPlayers(conn_rt, **kwargs))
                    asyncio.run(static_mod.SearchPlayers(conn_st, **kwargs))
                    self.assertEqual(conn_rt.executed[-1], conn_st.executed[-1], kwargs)

    def test_static_mode_rejects_malformed_blocks(self):
        """Nested/unbalanced markers and undeclared IF params fail at codegen."""
        compiler = PythonCompiler()
        compiler.options = {"conditional_mode": "static"}
        nested = Query(
            name="Nested",
            sql="SELECT 1 /* IF a */ x /* IF b */ y /* END IF */ /* END IF */",
            params=[Parameter(name="a", type="bool"), Parameter(name="b", type="bool")],
        )
        with self.assertRaises(ValueError):
            compiler._generate_function_body(nested)
        undeclared = Query(
            name="Undeclared",
            sql="SELECT 1 /* IF missing */ x /* END IF */",
            params=[],
        )
        with self.assertRaises(ValueError):
            compiler._generate_function_body(undeclared)

    def test_javascript_static_mode(self):
        """JS static mode emits if-appends instead of runtime processing."""
        out_dir = os.path.join(self.temp_dir.name, "genjs_static")
        JavaScriptCompiler().compile(
            [self._parse_probe()], MagicMock(), out_dir, {"conditional_mode": "static"}
        )
        with open(os.path.join(out_dir, "probe.js"), encoding="utf-8") as f:
            content = f.read()
        self.assertIn("if (sort_created_desc) {", content)
        self.assertIn("rawSql += ` created_at DESC, `;", content)
        self.assertNotIn("processConditionalBlocks(rawSql", content)
        self.assertIn("const cleanSql = cleanupSql(rawSql);", content)

    def test_javascript_generated_module(self):
        """Generated JS embeds the SQL, processes blocks, and takes the param."""
        out_dir = os.path.join(self.temp_dir.name, "genjs")
        compiler = JavaScriptCompiler()
        compiler.compile([self._parse_probe()], MagicMock(), out_dir)
        with open(os.path.join(out_dir, "probe.js"), encoding="utf-8") as f:
            content = f.read()
        # IF-only param is accepted and destructured (bug 3 left it out,
        # hardcoding `const params = {}` so the block was always removed)
        self.assertIn("async function ProbeConditional(connection, params)", content)
        self.assertIn("sort_created_desc,", content)
        # Raw SQL is embedded and processed at runtime
        self.assertIn("/* IF sort_created_desc */", content)
        self.assertIn("processConditionalBlocks(rawSql, params)", content)


if __name__ == "__main__":
    unittest.main()
