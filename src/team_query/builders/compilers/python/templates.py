"""Python code templates for the Python compiler."""

# Template for the __init__.py file
INIT_FILE = '''"""Generated database access code."""
'''

# Template for the utils.py file
UTILS_FILE = '''"""Utility functions for database access."""
import inspect
import logging
import re
import sys
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable, TypeVar, Generic, Type

import psycopg
from psycopg.rows import dict_row

# Logging setup
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
    for line in re.split(r'\r\n|\r|\n', sql):
        # Remove line comments
        if "--" in line:
            line = line[:line.index("--")]
        # Keep non-empty lines
        if line.strip():
            lines.append(line)
    
    # Join lines and clean up whitespace
    cleaned_sql = " ".join(lines)
    # Replace multiple spaces with a single space
    cleaned_sql = re.sub(r"\s+", " ", cleaned_sql)
    return cleaned_sql.strip()

def convert_named_params(sql: str) -> str:
    """Convert named parameters from :name to %(name)s format.
    
    Args:
        sql: SQL query with :name parameters
        
    Returns:
        SQL query with %(name)s parameters
    """
    # Find all named parameters in the SQL query
    pattern = r":(\w+)"
    
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

# Template for function with parameters
FUNCTION_WITH_PARAMS = '''@monitor_query_performance
def {function_name}(conn, {param_list}) -> {return_type}:
    """{function_doc}
    
    Args:
        conn: Database connection or connection string
{param_docs}
        
    Returns:
{return_doc}
    """
{function_body}
'''

# Template for function without parameters
FUNCTION_WITHOUT_PARAMS = '''@monitor_query_performance
def {function_name}(conn) -> {return_type}:
    """{function_doc}
    
    Args:
        conn: Database connection or connection string
        
    Returns:
{return_doc}
    """
{function_body}
'''

# Template for SELECT query function body
SELECT_QUERY_BODY = '''    # Get connection
    conn, should_close = ensure_connection(conn)
    
    try:
{process_conditional_blocks}
        # Convert named parameters
        sql = convert_named_params(sql)
        sql = cleanup_sql(sql)
        # Execute query
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql{params_arg})
{result_fetch}
    finally:
        if should_close:
            conn.close()
'''

# Template for INSERT/UPDATE/DELETE query function body
MODIFY_QUERY_BODY = '''    # Get connection
    conn, should_close = ensure_connection(conn)
    
    try:
{process_conditional_blocks}
        # Convert named parameters
        sql = convert_named_params(sql)
        sql = cleanup_sql(sql)
        # Execute query
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute(sql{params_arg})
{result_fetch}
            conn.commit()
    finally:
        if should_close:
            conn.close()
'''

# Template for single row result fetch
SINGLE_ROW_FETCH = '''            result = cur.fetchone()
            return result'''

# Template for multiple rows result fetch
MULTIPLE_ROWS_FETCH = '''            result = cur.fetchall()
            return result'''

# Template for exec result fetch
EXEC_RESULT_FETCH = '''            # For INSERT/UPDATE with RETURNING
            result = cur.fetchone()
            return result'''

# Template for exec rows fetch
EXEC_ROWS_FETCH = '''            # Return affected row count
            return cur.rowcount'''

# Template for exec (no result)
EXEC_NO_RESULT = '''            # No result to return
            return None'''

# Template for conditional blocks processing
CONDITIONAL_BLOCKS_PROCESSING = '''    # Process conditional blocks in SQL
    sql = process_conditional_blocks(sql, {params_dict})
'''

# Template for static SQL
STATIC_SQL = '''        # Static SQL (no conditional blocks)
        sql = """{sql}"""
'''
