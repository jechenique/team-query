"""Python compiler implementation module."""
import os
import re
from typing import Dict, List, Optional, Set, Tuple, Any

from team_query.builders.compilers.base import BaseCompiler
from team_query.builders.compilers.python.templates import (
    INIT_FILE,
    UTILS_FILE,
    FUNCTION_WITH_PARAMS,
    FUNCTION_WITHOUT_PARAMS,
    SELECT_QUERY_BODY,
    MODIFY_QUERY_BODY,
    SINGLE_ROW_FETCH,
    MULTIPLE_ROWS_FETCH,
    EXEC_RESULT_FETCH,
    EXEC_ROWS_FETCH,
    EXEC_NO_RESULT,
    CONDITIONAL_BLOCKS_PROCESSING,
    STATIC_SQL,
)
from team_query.models import Parameter, QueriesFile, Query, QueryType, SQLConfig


class PythonCompiler(BaseCompiler):
    """Compiler for Python code."""

    def __init__(self):
        """Initialize the Python compiler."""
        super().__init__()
        self.query_files = []
        self.config = None
        self.output_dir = ""

    def compile(self, queries_files: List[QueriesFile], config: SQLConfig, output_dir: str) -> None:
        """Compile SQL queries to Python code."""
        print(f"Python compiler: Starting compilation to {output_dir}")
        self.query_files = queries_files
        self.config = config
        
        # Clean output directory and ensure it exists
        self.clean_output_directory(output_dir)
        self.create_output_dir(output_dir)
        
        # Create __init__.py
        self._create_init_file(os.path.join(output_dir, "__init__.py"))
        
        # Create utils.py
        self._create_utils_file(os.path.join(output_dir, "utils.py"))
        
        # Process each query file
        print(f"Processing {len(queries_files)} query files")
        for query_file in queries_files:
            module_name = self._get_module_name(query_file.path)
            output_file = os.path.join(output_dir, f"{module_name}.py")
            self._create_query_file(query_file, output_file)

    def _create_init_file(self, file_path: str) -> None:
        """Create an __init__.py file."""
        try:
            print(f"Creating file: {file_path}")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Create a clean copy of the template with proper newlines
            template = INIT_FILE.replace('\r\n', '\n').replace('\r', '\n')
            
            # Write the template to the file with proper encoding
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(template)
                
            print("Created __init__.py successfully")
        except Exception as e:
            print(f"Error creating __init__.py: {e}")
            raise

    def _create_utils_file(self, file_path: str) -> None:
        """Create a utils.py file with utility functions using the template."""
        try:
            print(f"Creating file: {file_path}")
            # Ensure the directory exists
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            
            # Instead of using regex replacements which can cause escape sequence issues,
            # we'll create a completely new utils.py file with our corrected functions
            
            # Start with the imports and header
            utils_content = '''"""Utility functions for database access."""
'''
            # Add imports
            utils_content += '''import inspect
import logging
import re
import sys
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, TypeVar, Generic, Type

import psycopg
from psycopg.rows import dict_row

'''
            
            # Add Logger class and logging setup
            utils_content += '''# Logging setup
class Logger:
    """Logger wrapper that supports both built-in logging and custom loggers.
    
    This class provides a unified interface for logging that can work with:
    - Python's built-in logging
    - Custom loggers (like loguru)
    - Any object that implements standard logging methods (debug, info, warning, error, etc.)
    """
    _instance = None
    _logger = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Logger, cls).__new__(cls)
            # Initialize with default Python logging
            cls._init_default_logger()
        return cls._instance
    
    @classmethod
    def _init_default_logger(cls):
        """Initialize the default Python logger."""
        logger = logging.getLogger('team_query')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        cls._logger = logger
    
    @classmethod
    def set_custom_logger(cls, custom_logger):
        """Set a custom logger to be used instead of the default one.
        
        Args:
            custom_logger: A logger instance that implements standard logging methods
                          (debug, info, warning, error, etc.)
        """
        if custom_logger is not None:
            cls._logger = custom_logger
    
    @classmethod
    def get_logger(cls):
        """Get the current logger instance.
        
        Returns:
            The current logger instance being used
        """
        if cls._logger is None:
            cls._init_default_logger()
        return cls._logger
    
    @classmethod
    def set_level(cls, level):
        """Set the logging level.
        
        Args:
            level: Log level as a string (e.g., 'DEBUG', 'INFO', 'WARNING', 'ERROR')
        """
        log = cls.get_logger()
        if hasattr(log, 'setLevel'):
            numeric_level = getattr(logging, level.upper(), None)
            if isinstance(numeric_level, int):
                log.setLevel(numeric_level)
        # For loguru and other loggers that don't use setLevel
        elif hasattr(log, 'remove') and hasattr(log, 'add'):
            log.remove()
            log.add(lambda msg: print(msg), level=level.upper())
        elif hasattr(log, 'warning'):
            log.warning(f"Cannot set log level on logger of type {type(log).__name__}")
    
    @classmethod
    def debug(cls, msg, *args, **kwargs):
        """Log a debug message."""
        log = cls.get_logger()
        if hasattr(log, 'debug'):
            log.debug(msg, *args, **kwargs)
    
    @classmethod
    def info(cls, msg, *args, **kwargs):
        """Log an info message."""
        log = cls.get_logger()
        if hasattr(log, 'info'):
            log.info(msg, *args, **kwargs)
    
    @classmethod
    def warning(cls, msg, *args, **kwargs):
        """Log a warning message."""
        log = cls.get_logger()
        if hasattr(log, 'warning'):
            log.warning(msg, *args, **kwargs)
    
    @classmethod
    def error(cls, msg, *args, **kwargs):
        """Log an error message."""
        log = cls.get_logger()
        if hasattr(log, 'error'):
            log.error(msg, *args, **kwargs)
    
    @classmethod
    def exception(cls, msg, *args, **kwargs):
        """Log an exception with stack trace."""
        log = cls.get_logger()
        if hasattr(log, 'exception'):
            log.exception(msg, *args, **kwargs)
        elif hasattr(log, 'error'):
            log.error(f"{msg}: {str(kwargs.get('exc_info', ''))}", *args)
    
    @classmethod
    def critical(cls, msg, *args, **kwargs):
        """Log a critical error message."""
        log = cls.get_logger()
        if hasattr(log, 'critical'):
            log.critical(msg, *args, **kwargs)
        elif hasattr(log, 'error'):
            log.error(f"CRITICAL: {msg}", *args)

# Global logger instance
logger = Logger.get_logger()

def set_logger(custom_logger=None):
    """Set a custom logger to be used by the module.
    
    Args:
        custom_logger: A logger instance that implements standard logging methods.
                      If None, resets to the default logger.
    """
    if custom_logger is None:
        Logger._init_default_logger()
    else:
        Logger.set_custom_logger(custom_logger)

def set_log_level(level: str) -> None:
    """Set the log level for the current logger.
    
    Args:
        level: Log level as a string (e.g., 'INFO', 'DEBUG')
    """
    Logger.set_level(level)

def get_logger():
    """Get the current logger instance.
    
    Returns:
        The current logger instance being used
    """
    return Logger.get_logger()
'''
            
            # Add monitoring configuration
            utils_content += '''
# Monitoring configuration
_monitoring_mode = None

def configure_monitoring(mode: str) -> None:
    """Configure monitoring mode.
    
    Args:
        mode: Monitoring mode ('none' or 'basic')
        
    Raises:
        ValueError: If mode is not 'none' or 'basic'
    """
    global _monitoring_mode
    if mode.lower() not in ["none", "basic"]:
        raise ValueError('Monitoring mode must be either "none" or "basic"')
    _monitoring_mode = mode.lower()
    Logger.info(f"Monitoring configured: {mode}")

def monitor_query_performance(func: Callable = None) -> Callable:
    """Decorator to monitor query performance.
    
    Args:
        func: Function to decorate (for direct usage as @monitor_query_performance)
        
    Returns:
        Decorated function that returns (result, execution_time) when monitoring is enabled
    """
    def decorator(f):
        def wrapper(*args, **kwargs):
            if not _monitoring_mode or _monitoring_mode == "none":
                return f(*args, **kwargs)
                
            start_time = time.time()
            try:
                result = f(*args, **kwargs)
                end_time = time.time()
                execution_time = end_time - start_time
                
                # Log the execution time
                Logger.debug(f"Query {f.__name__} executed in {execution_time:.6f} seconds")
                
                # Return both result and execution time as a tuple
                return result, execution_time
                
            except Exception as e:
                end_time = time.time()
                execution_time = end_time - start_time
                Logger.error(
                    f"Query {f.__name__} failed after {execution_time:.6f} seconds: {str(e)}",
                    exc_info=True
                )
                raise
        
        # Copy the original function's name and docstring
        wrapper.__name__ = f.__name__
        wrapper.__doc__ = f.__doc__
        wrapper.__module__ = f.__module__
        wrapper.__annotations__ = f.__annotations__
        
        # Copy the original function's signature
        wrapper.__signature__ = inspect.signature(f)
        
        return wrapper
    
    # Handle both @monitor_query_performance and @monitor_query_performance() syntax
    if func is None:
        return decorator
    return decorator(func)
'''
            
            # Add the fixed SQL utility functions
            utils_content += '''
def process_conditional_blocks(sql: str, params: Dict[str, Any]) -> str:
    """Process conditional blocks in SQL based on parameters.
    
    Args:
        sql: SQL query with conditional blocks
        params: Query parameters
        
    Returns:
        Processed SQL query
    """
    # Simple implementation that handles basic conditional blocks
    
    # Find all conditional blocks
    pattern = r"/\* IF (\w+) \*/(.*?)/\* END IF \*/"
    
    def replace_block(match):
        param_name = match.group(1)
        content = match.group(2)
        
        # If parameter exists and is not None/empty, keep the content
        if param_name in params and params[param_name]:
            return content
        # Otherwise, remove the block
        return ""
    
    # Process all conditional blocks
    processed_sql = re.sub(pattern, replace_block, sql, flags=re.DOTALL)
    return processed_sql

def cleanup_sql(sql: str) -> str:
    """Clean up SQL query by removing extra whitespace and comments.
    
    Args:
        sql: SQL query to clean up
        
    Returns:
        Cleaned SQL query
    """
    # Remove comments
    lines = []
    # Split by newline, handling different line endings
    for line in re.split('\\r\\n|\\r|\\n', sql):
        # Remove line comments
        if "--" in line:
            line = line[:line.index("--")]
        # Keep non-empty lines
        if line.strip():
            lines.append(line)
    
    # Join lines and clean up whitespace
    cleaned_sql = " ".join(lines)
    # Replace multiple spaces with a single space
    cleaned_sql = re.sub(r"[ \t]+", " ", cleaned_sql)
    return cleaned_sql.strip()

def convert_named_params(sql: str) -> str:
    """Convert named parameters from :name to %(name)s format.
    
    Args:
        sql: SQL query with :name parameters
        
    Returns:
        SQL query with %(name)s parameters
    """
    # Find all named parameters in the SQL query
    pattern = r":([a-zA-Z0-9_]+)"
    
    result = []
    last_end = 0
    
    for match in re.finditer(pattern, sql):
        # Add text before the match
        result.append(sql[last_end:match.start()])
        # Add the parameter with %(name)s format
        param_name = match.group(1)
        result.append(f"%({param_name})s")
        last_end = match.end()
    
    # Add remaining text
    result.append(sql[last_end:])
    
    return "".join(result)

def ensure_connection(conn_or_string: Union[psycopg.Connection, str]) -> Tuple[psycopg.Connection, bool]:
    """Ensure we have a database connection.
    
    Args:
        conn_or_string: Connection object or connection string
        
    Returns:
        Tuple of (connection, should_close)
    """
    should_close = False
    
    if isinstance(conn_or_string, str):
        # It's a connection string, create a new connection
        conn = psycopg.connect(conn_or_string)
        should_close = True
    else:
        # It's already a connection object
        conn = conn_or_string
        
    return conn, should_close

class SQLParser:
    """SQL Parser for handling conditional blocks and parameter substitution."""
    
    @staticmethod
    def process_conditional_blocks(sql: str, params: Dict[str, Any]) -> str:
        """Process conditional blocks in SQL based on parameters."""
        return process_conditional_blocks(sql, params)
    
    @staticmethod
    def cleanup_sql(sql: str) -> str:
        """Clean up SQL query by removing extra whitespace and comments."""
        return cleanup_sql(sql)
    
    @staticmethod
    def convert_named_params(sql: str) -> str:
        """Convert named parameters from :name to %(name)s format."""
        return convert_named_params(sql)
'''
            
            # Write the complete utils.py file
            with open(file_path, 'w', encoding='utf-8', newline='\n') as f:
                f.write(utils_content)
                
            print("Created utils.py successfully")
        except Exception as e:
            print(f"Error creating utils file: {e}")
            raise

    def _get_module_name(self, file_name: str) -> str:
        """Get the module name from a file name."""
        # Remove path and extension
        base_name = os.path.basename(file_name)
        module_name = os.path.splitext(base_name)[0]
        return module_name

    def _create_query_file(self, query_file: QueriesFile, output_file: str) -> None:
        """Create a Python file for a query file."""
        try:
            print(f"Creating file: {output_file}")
            module_name = self._get_module_name(query_file.path)
            
            # Get all queries from the file
            queries = query_file.queries
            print(f"Found {len(queries)} queries in {module_name}")
            
            with open(output_file, "w", encoding="utf-8") as f:
                # Write imports
                f.write('"""Generated database access functions for {module_name}."""\n'.format(module_name=module_name))
                f.write("from typing import Any, Dict, List, Optional, Union\n")
                f.write("import psycopg\n")
                f.write("from psycopg.rows import dict_row\n\n")
                f.write("from .utils import monitor_query_performance, ensure_connection, process_conditional_blocks, cleanup_sql, convert_named_params\n\n\n")
                
                # Write each query function
                for query in queries:
                    print(f"Generating function for query: {query.name}")
                    function_code = self._generate_query_function(query)
                    f.write(function_code)
                    f.write("\n\n")
            
            print(f"Created {module_name}.py successfully")
        except Exception as e:
            print(f"Error creating {output_file}: {str(e)}")
            raise

    def _parse_params(self, query: Query) -> List[Tuple[str, str, str]]:
        """
        Extract parameters from a query.
        
        Returns:
            List of tuples with (param_name, param_type, param_description)
        """
        result = []
        for param in query.params:
            result.append((param.name, param.type, param.description or param.name))
        return result

    @classmethod
    def sanitize_name(cls, name: str) -> str:
        """
        Sanitize a name to be used as a Python identifier.
        Ensures valid Python naming by adding underscore prefix to names starting with numbers.
        """
        # Replace non-alphanumeric characters with underscores
        sanitized = ''.join(c if c.isalnum() else '_' for c in name)
        
        # Ensure the name starts with a letter or underscore
        if sanitized and not sanitized[0].isalpha():
            sanitized = '_' + sanitized
        
        return sanitized

    def _generate_query_function(self, query: Query) -> str:
        """Generate a Python function for a query."""
        # Use the original query name (PascalCase)
        function_name = query.name
        
        # Determine return type
        return_type = self._get_return_type(query)
        
        # Generate function documentation
        function_doc = query.description or f"Execute the {query.name} query."
        
        # Generate parameter documentation
        param_docs = ""
        for param in query.params:
            param_docs += f"        {param.name}: {param.description or 'Parameter'}\n"
        
        # Generate return documentation
        return_doc = self._get_return_doc(query)
        
        # Generate function body
        function_body = self._generate_function_body(query)
        
        # Generate parameter list
        param_list = ""
        if query.params:
            typed_params = []
            for param in query.params:
                python_type = self._get_python_type(param.type)
                typed_params.append(f"{param.name}: {python_type} = None")
            param_list = ", ".join(typed_params)
        
        # Use the appropriate template
        if query.params:
            return FUNCTION_WITH_PARAMS.format(
                function_name=function_name,
                param_list=param_list,
                return_type=return_type,
                function_doc=function_doc,
                param_docs=param_docs,
                return_doc=return_doc,
                function_body=function_body
            )
        else:
            # Add a trailing comma to match test expectations
            return FUNCTION_WITHOUT_PARAMS.format(
                function_name=function_name,
                return_type=return_type,
                function_doc=function_doc,
                return_doc=return_doc,
                function_body=function_body
            ).replace("def " + function_name + "(conn)", "def " + function_name + "(conn, )")

    def _get_return_type(self, query: Query) -> str:
        """Get the return type for a query."""
        if not query.query_type:
            return "List[Dict]"
            
        if query.query_type == QueryType.SELECT:
            if query.returns and query.returns.lower() == "one":
                return "Optional[Dict]"
            return "List[Dict]"
        elif query.query_type == QueryType.INSERT:
            if query.returns and query.returns.lower() == "execresult":
                return "Dict"
            return "int"
        elif query.query_type == QueryType.UPDATE or query.query_type == QueryType.DELETE:
            if query.returns and query.returns.lower() == "execresult":
                return "Dict"
            return "int"
        
        return "List[Dict]"

    def _get_return_doc(self, query: Query) -> str:
        """Get the return documentation for a query."""
        if not query.query_type:
            return "        List[Dict]: Query result"
            
        if query.query_type == QueryType.SELECT:
            if query.returns and query.returns.lower() == "one":
                return "        Optional[Dict]: Single row result or None if no rows found"
            return "        List[Dict]: List of rows"
        elif query.query_type == QueryType.INSERT:
            if query.returns and query.returns.lower() == "execresult":
                return "        Dict: Returned data from the INSERT"
            return "        int: Number of rows affected"
        elif query.query_type == QueryType.UPDATE or query.query_type == QueryType.DELETE:
            if query.returns and query.returns.lower() == "execresult":
                return "        Dict: Returned data from the UPDATE/DELETE"
            return "        int: Number of rows affected"
        
        return "        List[Dict]: Query result"

    def _generate_function_body(self, query: Query) -> str:
        """Generate the function body for a query."""
        # Check if there are conditional blocks in the SQL
        has_conditional_blocks = self._has_conditional_blocks(query.sql)
        
        # Generate SQL processing code
        if has_conditional_blocks:
            params_dict = "{" + ", ".join([f"'{param.name}': {param.name}" for param in query.params]) + "}"
            process_conditional_blocks = CONDITIONAL_BLOCKS_PROCESSING.format(params_dict=params_dict)
        else:
            process_conditional_blocks = STATIC_SQL.format(sql=query.sql)
        
        # Generate parameters argument for execute
        if query.params:
            params_arg = ", {"
            for param in query.params:
                params_arg += f"'{param.name}': {param.name}, "
            params_arg = params_arg.rstrip(", ") + "}"
        else:
            params_arg = ""
        
        # Generate result fetch code based on query type
        if not query.query_type:
            result_fetch = MULTIPLE_ROWS_FETCH
        elif query.query_type == QueryType.SELECT:
            if query.returns and query.returns.lower() == "one":
                result_fetch = SINGLE_ROW_FETCH
            else:
                result_fetch = MULTIPLE_ROWS_FETCH
        elif query.query_type == QueryType.INSERT or query.query_type == QueryType.UPDATE or query.query_type == QueryType.DELETE:
            if query.returns and query.returns.lower() == "execresult":
                result_fetch = EXEC_RESULT_FETCH
            elif query.returns and query.returns.lower() == "execrows":
                result_fetch = EXEC_ROWS_FETCH
            else:
                result_fetch = EXEC_NO_RESULT
        else:
            result_fetch = MULTIPLE_ROWS_FETCH
        
        # Use the appropriate template based on query type
        if not query.query_type or query.query_type == QueryType.SELECT:
            return SELECT_QUERY_BODY.format(
                process_conditional_blocks=process_conditional_blocks,
                params_arg=params_arg,
                result_fetch=result_fetch
            )
        else:
            return MODIFY_QUERY_BODY.format(
                process_conditional_blocks=process_conditional_blocks,
                params_arg=params_arg,
                result_fetch=result_fetch
            )

    def _has_conditional_blocks(self, sql: str) -> bool:
        """Check if SQL has conditional blocks."""
        return "/* IF " in sql and "/* END IF */" in sql

    def _get_python_type(self, param_type: str) -> str:
        """Get the Python type for a parameter."""
        # Map SQL types to Python types
        type_map = {
            "int": "int",
            "integer": "int",
            "boolean": "bool",
            "bool": "bool",
            "text": "str",
            "string": "str",
            "varchar": "str",
            "date": "str",
            "time": "str",
            "timestamp": "str",
            "interval": "str",
            "numeric": "float",
            "float": "float",
            "money": "float",
            "bytea": "bytes",
            "json": "Dict[str, Any]",
            "jsonb": "Dict[str, Any]",
        }
        
        # Default to Any if type is not recognized
        return type_map.get(param_type.lower(), "Any")
