"""
Configuration loader for team-query.
"""
import glob
import os
from typing import Any, Dict, List, Optional, Union

from team_query.models import (Config, Parameter, PluginConfig, ProjectConfig,
                               QueriesFile, Query, SQLConfig)
from team_query.sql_parser import SQLCStyleParser


def load_config(config_path: str) -> Config:
    """Load configuration from a YAML file."""
    import yaml

    print(f"Opening config file: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        config_data = yaml.safe_load(f)

    print(f"Config data loaded: {config_data}")

    project_data = config_data.get("project", {})
    project = ProjectConfig(
        name=project_data.get("name", ""), version=project_data.get("version")
    )
    print(f"Project config: {project}")

    sql_configs = []
    for i, sql_config_data in enumerate(config_data.get("sql", [])):
        print(f"Processing SQL config #{i+1}: {sql_config_data}")
        gen_configs = []
        for j, gen_config_data in enumerate(sql_config_data.get("gen", [])):
            print(f"  Processing gen config #{j+1}: {gen_config_data}")
            gen_configs.append(
                PluginConfig(
                    plugin=gen_config_data.get("plugin", ""),
                    out=gen_config_data.get("out", ""),
                    options=gen_config_data.get("options", {}),
                )
            )

        sql_configs.append(
            SQLConfig(
                queries=sql_config_data.get("queries", []),
                schema=sql_config_data.get("schema", []),
                engine=sql_config_data.get("engine", ""),
                gen=gen_configs,
            )
        )

    config = Config(
        version=config_data.get("version", "1"), project=project, sql=sql_configs
    )
    print(f"Final config: {config}")
    return config


def load_queries(query_patterns: List[str]) -> List[QueriesFile]:
    """Load queries from SQL files matching the given patterns."""
    query_files = []

    print(f"Loading queries from patterns: {query_patterns}")
    for pattern in query_patterns:
        print(f"Processing pattern: {pattern}")
        matching_files = glob.glob(pattern, recursive=True)
        print(f"  Found {len(matching_files)} files matching pattern: {matching_files}")

        for file_path in matching_files:
            if not os.path.isfile(file_path):
                print(f"  Skipping non-file: {file_path}")
                continue

            # Only process SQL files
            file_ext = os.path.splitext(file_path)[1].lower()
            if file_ext != ".sql":
                print(f"  Warning: Skipping non-SQL file: {file_path}")
                continue

            print(f"  Processing SQL file: {file_path}")
            # Process SQL file with sqlc-style comments
            query_file = load_sql_queries(file_path)
            print(f"  Loaded {len(query_file.queries)} queries from {file_path}")
            query_files.append(query_file)

    print(f"Total query files loaded: {len(query_files)}")
    return query_files


def load_sql_queries(file_path: str) -> QueriesFile:
    """Load queries from a SQL file with sqlc-style comments."""
    with open(file_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Parse SQL content using SQLCStyleParser
    queries = SQLCStyleParser.parse_sql_file(sql_content)

    return QueriesFile(path=file_path, queries=queries)


def load_schema(schema_patterns: List[str]) -> str:
    """Load schema from SQL files matching the given patterns."""
    schema = []

    for pattern in schema_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            if not os.path.isfile(file_path):
                continue

            with open(file_path, "r", encoding="utf-8") as f:
                schema.append(f.read())

    return "\n\n".join(schema)
