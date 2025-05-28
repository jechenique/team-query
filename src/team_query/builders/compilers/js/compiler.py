"""JavaScript compiler module."""
import os
from typing import Any, Dict, List, Optional

from team_query.builders.compilers.base import BaseCompiler
from team_query.builders.compilers.js.templates import (
    CONDITIONAL_BLOCKS, CREATE_TRANSACTION, ENSURE_CONNECTION, LOGGER,
    MODULE_EXPORTS, MONITOR_QUERY_PERFORMANCE, MONITORING_CONFIG, NAMED_PARAMS,
    SQL_CLEANUP)
from team_query.models import QueriesFile, Query, SQLConfig


class JavaScriptCompiler(BaseCompiler):
    """JavaScript compiler class."""

    def __init__(self):
        """Initialize the JavaScript compiler."""
        super().__init__()

    def _has_conditional_blocks(self, sql: str) -> bool:
        """Check if SQL has conditional blocks."""
        # Look for conditional blocks in the format /* IF param */.../* END IF */
        return "/* IF " in sql and "/* END IF */" in sql

    def _get_js_type(self, sql_type: str) -> str:
        """Convert SQL type to JavaScript type."""
        sql_type = sql_type.lower()

        # Number types
        if sql_type in [
            "int",
            "integer",
            "bigint",
            "smallint",
            "decimal",
            "numeric",
            "float",
            "real",
            "double",
        ]:
            return "number"

        # String types
        if sql_type in ["string", "text", "varchar", "char"]:
            return "string"

        # Boolean type
        if sql_type in ["bool", "boolean"]:
            return "boolean"

        # Date/time types
        if sql_type in ["date", "time", "timestamp", "timestamptz"]:
            return "Date"

        # JSON types
        if sql_type in ["json", "jsonb"]:
            return "object"

        # UUID type
        if sql_type == "uuid":
            return "string"

        # Binary data
        if sql_type == "bytea":
            return "Buffer"

        # Default to any
        return "any"

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """
        Sanitize a name to be used as a JavaScript identifier.
        Converts snake_case to camelCase and ensures valid identifier.
        """
        # Replace non-alphanumeric characters with underscores
        sanitized = "".join(c if c.isalnum() else "_" for c in name)

        # Ensure the name starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha():
            sanitized = "_" + sanitized

        # Convert snake_case to camelCase
        parts = sanitized.split("_")
        sanitized = parts[0] + "".join(part.capitalize() for part in parts[1:] if part)

        return sanitized

    def _create_utils_file(self, file_path: str) -> None:
        """Create a utils.js file with utility functions."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                # Add logger utility
                print("Writing logger utility...")
                f.write(LOGGER)
                f.write("\n\n")

                # Add monitoring configuration and wrapper function
                try:
                    print("Writing monitoring configuration...")
                    f.write(MONITORING_CONFIG)
                    f.write("\n\n")
                    print("Writing monitoring wrapper function...")
                    f.write(MONITOR_QUERY_PERFORMANCE)
                    f.write("\n\n")
                    print(
                        "Finished writing monitoring configuration and wrapper function"
                    )
                except Exception as e:
                    print(
                        f"Error writing monitoring configuration and wrapper function: {str(e)}"
                    )
                    import traceback

                    traceback.print_exc()

                # Add utility functions for conditional blocks and SQL cleanup
                try:
                    print(
                        "Writing utility functions for conditional blocks and SQL cleanup..."
                    )
                    f.write(CONDITIONAL_BLOCKS)
                    f.write("\n\n")
                    print(
                        "Finished writing utility functions for conditional blocks and SQL cleanup"
                    )
                except Exception as e:
                    print(f"Error writing utility functions: {str(e)}")

                # Add SQL cleanup function
                try:
                    print("Writing SQL cleanup function...")
                    f.write(SQL_CLEANUP)
                    f.write("\n\n")
                    print("Finished writing SQL cleanup function")
                except Exception as e:
                    print(f"Error writing SQL cleanup function: {str(e)}")

                # Add utility function to convert named parameters to positional parameters
                try:
                    print(
                        "Writing utility function to convert named parameters to positional parameters..."
                    )
                    f.write(NAMED_PARAMS)
                    f.write("\n\n")
                    print(
                        "Finished writing utility function to convert named parameters to positional parameters"
                    )
                except Exception as e:
                    print(f"Error writing utility function: {str(e)}")

                # Add ensureConnection utility function
                try:
                    print("Writing ensureConnection utility function...")
                    f.write(ENSURE_CONNECTION)
                    f.write("\n\n")
                    print("Finished writing ensureConnection utility function")
                except Exception as e:
                    print(f"Error writing ensureConnection utility function: {str(e)}")

                # Add createTransaction utility function
                try:
                    print("Writing createTransaction utility function...")
                    f.write(CREATE_TRANSACTION)
                    f.write("\n\n")
                    print("Finished writing createTransaction utility function")
                except Exception as e:
                    print(f"Error writing createTransaction utility function: {str(e)}")

                # Export utility functions
                try:
                    print("Exporting utility functions...")
                    f.write(MODULE_EXPORTS)
                    print("Finished exporting utility functions")
                except Exception as e:
                    print(f"Error exporting utility functions: {str(e)}")

                print("Created utils.js successfully")
        except Exception as e:
            print(f"Error creating utils.js: {str(e)}")

    def _create_index_file(self, file_path: str) -> None:
        """Create an index.js file with utility functions and module exports."""
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write("/**\n")
                f.write(f" * Generated JavaScript client for database queries.\n")
                f.write(" */\n\n")

                # Import utility functions
                f.write(
                    'const { logger, setLogLevel, processConditionalBlocks, cleanupSql, convertNamedParams, ensureConnection, configureMonitoring, monitorQueryPerformance, createTransaction } = require("./utils");\n\n'
                )

                # Create transaction function
                f.write("/**\n")
                f.write(" * Create a database client\n")
                f.write(
                    " * @param {string} connectionString - Database connection string\n"
                )
                f.write(" * @returns {object} - Database client\n")
                f.write(" */\n")
                f.write("async function createClient(connectionString) {\n")
                f.write("  return await ensureConnection(connectionString);\n")
                f.write("}\n\n")

                # Import query modules
                for query_file in self.query_files:
                    # Extract module name from file path
                    file_name = os.path.basename(query_file.path)
                    module_name = self.sanitize_name(os.path.splitext(file_name)[0])
                    f.write(f'const {module_name} = require("./{module_name}");\n')
                f.write("\n")

                # Export everything
                f.write("module.exports = {\n")
                f.write("  // Utility functions\n")
                f.write("  logger,\n")
                f.write("  setLogLevel,\n")
                f.write("  configureMonitoring,\n")
                f.write("  createClient,\n")
                f.write("  createTransaction,\n")

                # Export query modules directly
                print(f"Processing {len(self.query_files)} query files for JavaScript")
                for query_file in self.query_files:
                    # Extract module name from file path
                    file_name = os.path.basename(query_file.path)
                    module_name = self.sanitize_name(os.path.splitext(file_name)[0])
                    print(f"  Module name for {file_name}: {module_name}")
                    f.write(f"  {module_name}: {module_name},\n")

                f.write("};\n")
                print(f"Created index.js successfully")
        except Exception as e:
            print(f"Error creating index.js: {str(e)}")

    def _create_query_file(self, module_name: str, queries: List[Query]) -> None:
        """Create a JavaScript file for a query module."""
        file_path = os.path.join(self.output_dir, f"{module_name}.js")
        try:
            with open(file_path, "w") as f:
                # Add imports
                f.write("/**\n")
                f.write(f" * Generated JavaScript queries for {module_name}\n")
                f.write(" */\n\n")
                f.write(
                    "const { logger, monitorQueryPerformance, processConditionalBlocks, cleanupSql, convertNamedParams, ensureConnection } = require('./utils');\n\n"
                )

                # Add each query function
                for query in queries:
                    print(f"Generating JavaScript function for query: {query.name}")

                    # Generate the function
                    function_name = self.sanitize_name(query.name)

                    # Add function documentation
                    f.write("/**\n")
                    if query.description:
                        f.write(f" * {query.description}\n")

                    # Add parameter documentation
                    for param in query.params:
                        js_type = self._get_js_type(param.type)
                        f.write(
                            f" * @param {{{js_type}}} {param.name} - {param.description or param.name}\n"
                        )

                    # Add return type documentation
                    if query.returns and query.returns.lower() == "one":
                        f.write(" * @returns {Promise<Object>} - Single row result\n")
                    else:
                        f.write(
                            " * @returns {Promise<Array<Object>>} - Array of rows\n"
                        )

                    f.write(" */\n")

                    # Generate function parameters
                    param_list = []
                    if query.params:
                        for param in query.params:
                            param_list.append(param.name)

                    # Add function declaration
                    if param_list:
                        f.write(
                            f"async function {function_name}(connection, params) {{\n"
                        )
                    else:
                        f.write(f"async function {function_name}(connection) {{\n")

                    # Initialize params object
                    if param_list:
                        f.write("  // Extract parameters from params object\n")
                        f.write("  const {\n")
                        for param in query.params:
                            f.write(f"    {param.name},\n")
                        f.write("  } = params || {};\n")
                    else:
                        f.write("  // No parameters for this query\n")
                        f.write("  const params = {};\n")

                    # Add logging for function entry
                    f.write("  // Log function entry\n")
                    f.write(
                        f"  logger.debug(`Executing {function_name} with parameters: ${{JSON.stringify(params)}}`);\n"
                    )

                    # Process SQL with conditional blocks if present
                    if self._has_conditional_blocks(query.sql):
                        f.write("  // Process conditional blocks in SQL\n")
                        f.write(f"  const rawSql = `{query.sql}`;\n")
                        f.write(
                            "  const processedSql = processConditionalBlocks(rawSql, params);\n"
                        )
                        f.write("  const cleanSql = cleanupSql(processedSql);\n")
                    else:
                        f.write("  // Use static SQL (no conditional blocks)\n")
                        f.write(f"  const cleanSql = `{query.sql}`;\n")

                    # Convert named parameters to positional
                    f.write(
                        "  // Convert named parameters to positional parameters for PostgreSQL\n"
                    )
                    f.write(
                        "  const { sql: convertedSql, values } = convertNamedParams(cleanSql, params);\n"
                    )
                    f.write("  logger.debug(`Executing SQL: ${convertedSql}`);\n")
                    f.write(
                        "  logger.debug(`With values: ${JSON.stringify(values)}`);\n"
                    )

                    # Execute the query based on its type
                    if query.query_type and query.query_type.value == "select":
                        f.write("  try {\n")
                        f.write("    // Execute SELECT query\n")
                        f.write(
                            "    const client = await ensureConnection(connection);\n"
                        )
                        f.write(
                            "    const result = await client.query(convertedSql, values);\n"
                        )
                        f.write(
                            "    logger.debug(`Query returned ${result.rows.length} rows`);\n"
                        )

                        # For single row result
                        if query.returns and query.returns.lower() == "one":
                            f.write("    // Return single row result\n")
                            f.write(
                                "    return result.rows.length > 0 ? result.rows[0] : null;\n"
                            )
                        else:
                            f.write("    // Return all rows\n")
                            f.write("    return result.rows;\n")

                        f.write("  } catch (error) {\n")
                        f.write(
                            "    logger.error(`Error executing query: ${error.message}`);\n"
                        )
                        f.write("    throw error;\n")
                        f.write("  }\n")
                    elif query.query_type and query.query_type.value == "insert":
                        f.write("  try {\n")
                        f.write("    // Execute INSERT query\n")
                        f.write(
                            "    const client = await ensureConnection(connection);\n"
                        )
                        f.write(
                            "    const result = await client.query(convertedSql, values);\n"
                        )
                        f.write("    let rowCount = result.rowCount || 0;\n")
                        f.write(
                            "    const returnedData = result.rows && result.rows.length > 0 ? result.rows[0] : null;\n"
                        )
                        f.write(
                            "    logger.debug(`INSERT query completed with result: ${JSON.stringify(returnedData)}`);\n"
                        )
                        f.write("    return returnedData;\n")
                        f.write("  } catch (error) {\n")
                        f.write(
                            "    logger.error(`Error executing query: ${error.message}`);\n"
                        )
                        f.write("    throw error;\n")
                        f.write("  }\n")
                    elif query.query_type and query.query_type.value == "update":
                        f.write("  try {\n")
                        f.write("    // Execute UPDATE query\n")
                        f.write(
                            "    const client = await ensureConnection(connection);\n"
                        )
                        f.write(
                            "    const result = await client.query(convertedSql, values);\n"
                        )
                        f.write("    let rowCount = result.rowCount || 0;\n")
                        f.write(
                            "    const returnedData = result.rows && result.rows.length > 0 ? result.rows[0] : null;\n"
                        )
                        f.write("    logger.debug(`Updated ${rowCount} rows`);\n")
                        f.write("    return returnedData;\n")
                        f.write("  } catch (error) {\n")
                        f.write(
                            "    logger.error(`Error executing query: ${error.message}`);\n"
                        )
                        f.write("    throw error;\n")
                        f.write("  }\n")
                    elif query.query_type and query.query_type.value == "delete":
                        f.write("  try {\n")
                        f.write("    // Execute DELETE query\n")
                        f.write(
                            "    const client = await ensureConnection(connection);\n"
                        )
                        f.write(
                            "    const result = await client.query(convertedSql, values);\n"
                        )
                        f.write("    let rowCount = result.rowCount || 0;\n")
                        f.write("    logger.debug(`Deleted ${rowCount} rows`);\n")
                        f.write("    return rowCount;\n")
                        f.write("  } catch (error) {\n")
                        f.write(
                            "    logger.error(`Error executing query: ${error.message}`);\n"
                        )
                        f.write("    throw error;\n")
                        f.write("  }\n")
                    else:
                        # Default to generic query execution
                        f.write("  try {\n")
                        f.write("    // Execute generic query\n")
                        f.write(
                            "    const client = await ensureConnection(connection);\n"
                        )
                        f.write(
                            "    const result = await client.query(convertedSql, values);\n"
                        )
                        f.write("    let rowCount = result.rowCount || 0;\n")
                        f.write(
                            "    logger.debug(`Query affected ${rowCount} rows`);\n"
                        )
                        f.write("    return result.rows;\n")
                        f.write("  } catch (error) {\n")
                        f.write(
                            "    logger.error(`Error executing query: ${error.message}`);\n"
                        )
                        f.write("    throw error;\n")
                        f.write("  }\n")

                    f.write("}\n\n")

                    # Export the function
                    f.write(f"// Export the function\n")
                    f.write(
                        f"module.exports.{function_name} = monitorQueryPerformance({function_name}, '{function_name}');\n\n"
                    )

                print(f"Created {module_name}.js successfully")
        except Exception as e:
            print(f"Error creating {module_name}.js: {str(e)}")
            import traceback

            traceback.print_exc()

    def compile(
        self, queries_files: List[QueriesFile], config: SQLConfig, output_dir: str
    ) -> None:
        """Compile queries to JavaScript code."""
        print(f"JavaScript compiler: Starting compilation to {output_dir}")

        # Initialize compiler state
        self.query_files = queries_files
        self.config = config
        self.output_dir = output_dir

        # Ensure output directory exists
        print(f"Output directory exists: {os.path.exists(output_dir)}")
        try:
            self.clean_output_directory(output_dir)
            self.create_output_dir(output_dir)
            print(f"Output directory created/verified: {os.path.exists(output_dir)}")
        except Exception as e:
            print(f"Error creating output directory: {str(e)}")

        # Create a utils.js file with utility functions
        utils_path = os.path.join(output_dir, "utils.js")
        print(f"Creating file: {utils_path}")
        self._create_utils_file(utils_path)

        # Create an index.js file with utility functions and module exports
        index_path = os.path.join(output_dir, "index.js")
        print(f"Creating file: {index_path}")
        self._create_index_file(index_path)

        # Create a file for each queries file
        for queries_file in queries_files:
            # Extract module name from file path
            file_name = os.path.basename(queries_file.path)
            module_name = self.sanitize_name(os.path.splitext(file_name)[0])
            file_path = os.path.join(output_dir, f"{module_name}.js")
            print(f"Creating file: {file_path}")
            print(f"Found {len(queries_file.queries)} queries in {module_name}")

            # Create the query file
            self._create_query_file(module_name, queries_file.queries)
