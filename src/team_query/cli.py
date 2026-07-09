"""
Command-line interface for team-query.
"""

import inspect
import os
import pathlib
import sys
from typing import List, Optional

import click

from team_query.config import load_config, load_queries, load_schema
from team_query.log import set_verbose, vprint
from team_query.models import Config, SQLConfig
from team_query.sync import sync_directory


def get_compiler_plugins():
    """Get available compiler plugins.

    Built-in compilers are always available; third-party plugins registered
    under the "team_query.compilers" entry-point group are added on top.
    """
    from team_query.builders.compilers.js import compile as javascript_compile
    from team_query.builders.compilers.python import compile as python_compile

    plugins = {
        "python": python_compile,
        "javascript": javascript_compile,
    }
    try:
        from importlib import metadata

        entry_points = metadata.entry_points()
        if hasattr(entry_points, "select"):  # Python 3.10+
            group = entry_points.select(group="team_query.compilers")
        else:  # Python 3.9
            group = entry_points.get("team_query.compilers", [])
        for entry_point in group:
            if entry_point.name not in plugins:
                plugins[entry_point.name] = entry_point.load()
    except Exception as e:
        click.echo(f"Warning: could not load compiler entry points: {e}", err=True)
    return plugins


@click.group()
@click.version_option()
def cli():
    """team-query: A Python clone of sqlc with YAML-based SQL queries."""
    pass


@cli.command()
@click.option("--config", "-c", required=True, help="Path to config file")
@click.option("--output", "-o", help="Output directory (overrides config)")
@click.option("--cwd", help="Working directory for the command")
@click.option(
    "--sync",
    "-s",
    multiple=True,
    help="Sync generated output to a target directory. Format: plugin:path (e.g. python:/path/to/target)",
)
@click.option(
    "--formatter",
    "-f",
    multiple=True,
    help="Run a formatter on generated files before syncing. Can be specified multiple times (e.g. -f 'ruff check --fix' -f 'ruff format').",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="Show detailed diagnostic output while generating.",
)
def generate(
    config: str,
    output: Optional[str] = None,
    cwd: Optional[str] = None,
    sync: tuple = (),
    formatter: tuple = (),
    verbose: bool = False,
):
    """Generate code from SQL queries."""
    set_verbose(verbose)
    # Change working directory if specified
    original_cwd = None
    if cwd:
        original_cwd = os.getcwd()
        os.chdir(cwd)
        vprint(f"Changed working directory to: {os.getcwd()}")

    try:
        # Parse --sync arguments into a plugin -> path mapping
        sync_targets = {}
        for sync_arg in sync:
            if ":" not in sync_arg:
                click.echo(
                    f"Error: --sync must be in format plugin:path (got '{sync_arg}')",
                    err=True,
                )
                sys.exit(1)
            plugin, path = sync_arg.split(":", 1)
            sync_targets[plugin] = os.path.expanduser(path)

        if not os.path.exists(config):
            click.echo(f"Error: Config file not found: {config}", err=True)
            sys.exit(1)

        # Load configuration
        vprint(f"Loading configuration from {config}")
        cfg = load_config(config)
        vprint(f"Configuration loaded successfully")

        # Get compiler plugins
        vprint(f"Loading compiler plugins")
        plugins = get_compiler_plugins()
        vprint(f"Available plugins: {', '.join(plugins.keys())}")

        # Process each SQL config
        for i, sql_config in enumerate(cfg.sql):
            vprint(f"Processing SQL config #{i + 1}")

            # Load queries
            vprint(f"Loading queries from patterns: {sql_config.queries}")
            queries_files = load_queries(sql_config.queries)
            if not queries_files:
                click.echo(
                    f"Warning: No query files found matching patterns: {sql_config.queries}"
                )
                continue
            vprint(f"Found {len(queries_files)} query files")

            # Load schema
            vprint(f"Loading schema from patterns: {sql_config.schema}")
            schema = load_schema(sql_config.schema)
            vprint(f"Schema loaded: {len(schema)} characters")

            # Generate code for each plugin
            for gen_config in sql_config.gen:
                plugin_name = gen_config.plugin
                vprint(f"Processing plugin: {plugin_name}")

                if plugin_name not in plugins:
                    click.echo(f"Error: Plugin not found: {plugin_name}", err=True)
                    continue

                # Determine output directory
                out_dir = gen_config.out
                if output:
                    # Override with command-line output if provided
                    out_dir = os.path.join(output, plugin_name)
                vprint(f"Output directory for {plugin_name}: {out_dir}")

                # Create output directory if it doesn't exist
                pathlib.Path(out_dir).mkdir(parents=True, exist_ok=True)
                vprint(f"Ensuring output directory exists: {out_dir}")

                # Get compiler function
                compiler_func = plugins[plugin_name]

                click.echo(f"Generating {plugin_name} code in {out_dir}...")
                # Pass per-plugin options when the plugin accepts them, so
                # third-party plugins with the old 3-arg signature keep working
                if len(inspect.signature(compiler_func).parameters) >= 4:
                    compiler_func(
                        queries_files, sql_config, out_dir, gen_config.options
                    )
                else:
                    compiler_func(queries_files, sql_config, out_dir)

                # Sync to target directory if requested via CLI
                if plugin_name in sync_targets:
                    sync_target = sync_targets[plugin_name]
                    click.echo(f"Syncing {plugin_name} to {sync_target}...")
                    result = sync_directory(out_dir, sync_target, formatters=formatter)
                    click.echo(f"  Sync: {result.summary}")
                    for f in result.copied:
                        click.echo(f"    copied: {f}")
                    for f in result.removed:
                        click.echo(f"    removed: {f}")

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
