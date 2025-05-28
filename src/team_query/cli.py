"""
Command-line interface for team-query.
"""
import os
import pathlib
import sys
from typing import List, Optional

import click

from team_query.config import load_config, load_queries, load_schema
from team_query.models import Config, SQLConfig


def get_compiler_plugins():
    """Get available compiler plugins."""
    # Temporarily force fallback to diagnose potential importlib.metadata issues
    # try:
    #     return {
    #         entry_point.name: entry_point.load()
    #         for entry_point in metadata.entry_points(group="team_query.compilers")
    #     }
    # except Exception as e:
    # Fallback to direct imports if entry points are not working
    from team_query.builders.compilers.js import compile as javascript_compile
    from team_query.builders.compilers.python import compile as python_compile

    return {
        "python": python_compile,
        "javascript": javascript_compile,
    }


@click.group()
@click.version_option()
def cli():
    """team-query: A Python clone of sqlc with YAML-based SQL queries."""
    pass


@cli.command()
@click.option("--config", "-c", required=True, help="Path to config file")
@click.option("--output", "-o", help="Output directory (overrides config)")
@click.option("--cwd", help="Working directory for the command")
def generate(config: str, output: Optional[str] = None, cwd: Optional[str] = None):
    """Generate code from SQL queries."""
    # Change working directory if specified
    original_cwd = None
    if cwd:
        original_cwd = os.getcwd()
        os.chdir(cwd)
        print(f"Changed working directory to: {os.getcwd()}")

    try:
        if not os.path.exists(config):
            click.echo(f"Error: Config file not found: {config}", err=True)
            sys.exit(1)

        # Load configuration
        print(f"Loading configuration from {config}")
        cfg = load_config(config)
        print(f"Configuration loaded successfully")

        # Get compiler plugins
        print(f"Loading compiler plugins")
        plugins = get_compiler_plugins()
        print(f"Available plugins: {', '.join(plugins.keys())}")

        # Process each SQL config
        for i, sql_config in enumerate(cfg.sql):
            print(f"Processing SQL config #{i+1}")

            # Load queries
            print(f"Loading queries from patterns: {sql_config.queries}")
            queries_files = load_queries(sql_config.queries)
            if not queries_files:
                click.echo(
                    f"Warning: No query files found matching patterns: {sql_config.queries}"
                )
                continue
            print(f"Found {len(queries_files)} query files")

            # Load schema
            print(f"Loading schema from patterns: {sql_config.schema}")
            schema = load_schema(sql_config.schema)
            print(f"Schema loaded: {len(schema)} characters")

            # Generate code for each plugin
            for gen_config in sql_config.gen:
                plugin_name = gen_config.plugin
                print(f"Processing plugin: {plugin_name}")

                if plugin_name not in plugins:
                    click.echo(f"Error: Plugin not found: {plugin_name}", err=True)
                    continue

                # Determine output directory
                out_dir = gen_config.out
                if output:
                    # Override with command-line output if provided
                    out_dir = os.path.join(output, plugin_name)
                print(f"Output directory for {plugin_name}: {out_dir}")

                # Create output directory if it doesn't exist
                pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
                print(f"Ensuring output directory exists: {out_dir}")

                # Get compiler function
                compiler_func = plugins[plugin_name]

                click.echo(f"Generating {plugin_name} code in {out_dir}...")
                compiler_func(queries_files, sql_config, out_dir)

        click.echo("Code generation completed successfully.")

    except Exception as e:
        click.echo(f"Error: {str(e)}", err=True)
        import traceback

        traceback.print_exc()
        sys.exit(1)
    finally:
        # Restore original working directory if changed
        if original_cwd:
            os.chdir(original_cwd)


@cli.command()
def plugins():
    """List available compiler plugins."""
    plugins = get_compiler_plugins()

    click.echo("Available compiler plugins:")
    for name in sorted(plugins.keys()):
        click.echo(f"  - {name}")


def main():
    """Entry point for the CLI."""
    cli()


def main_with_args(args=None):
    """Entry point for the CLI with predefined arguments."""
    return cli.main(args=args)


def blog_example():
    """Entry point for the blog example."""
    args = ["generate", "--config", "./team-query.yaml", "--cwd", "./examples/blog"]
    return cli.main(args=args)
