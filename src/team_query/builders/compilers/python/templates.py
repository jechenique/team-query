"""Python code templates for the Python compiler."""

# No templates needed for __init__.py as it's generated dynamically

# Template for the utils.py file
UTILS_FILE = '''"""Utility functions for database access."""
import inspect
import logging
import re
import sys
import time
from enum import Enum
from functools import wraps
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

# Import additional modules needed for thread-safe singleton pattern
import os
import weakref
import threading
import importlib.util

# Initialize thread-safe storage with weak references if it doesn't exist yet
if not hasattr(sys, '_monitoring_config_instances'):
    sys._monitoring_config_instances = weakref.WeakValueDictionary()
    
# Initialize the lock at module level
_monitoring_config_lock = threading.Lock()

# Get the canonical module path
_spec = importlib.util.find_spec(__name__)
_module_path = os.path.abspath(_spec.origin) if _spec and _spec.origin else __file__
_module_key = f"monitoring_config_{hash(_module_path)}"

class _MonitoringState:
    """Thread-safe singleton state container for monitoring configuration."""
    def __init__(self):
        self.monitoring_mode = None
        self._lock = threading.Lock()

    def set_mode(self, mode):
        """Thread-safe mode setter."""
        with self._lock:
            self.monitoring_mode = mode

    def get_mode(self):
        """Thread-safe mode getter."""
        with self._lock:
            return self.monitoring_mode
            
    def __str__(self):
        return f"Monitoring mode: {self.monitoring_mode}"

def _get_monitoring_state() -> _MonitoringState:
    """Get or create the singleton monitoring state instance.
    
    This function is thread-safe and ensures only one _MonitoringState instance exists
    per module path, even when imported multiple times or from different paths.
    """
    with _monitoring_config_lock:
        if _module_key not in sys._monitoring_config_instances:
            state = _MonitoringState()
            sys._monitoring_config_instances[_module_key] = state
            # Keep a strong reference in the module's global namespace
            sys.modules[__name__]._monitoring_state_ref = state
        return sys._monitoring_config_instances[_module_key]

# Initialize the singleton state
_monitoring_state = _get_monitoring_state()

class MonitoringConfig:
    """Class for monitoring configuration.

    This class provides methods for configuring monitoring settings.
    Uses a thread-safe singleton pattern to ensure consistent state across imports.
    """

    @classmethod
    def get_mode(cls):
        """Get the current monitoring mode.

        Returns:
            str: The current monitoring mode.
        """
        # Always get the latest instance from the global registry
        state = _get_monitoring_state()
        return state.get_mode()

    @classmethod
    def set_mode(cls, mode: str):
        """Set the monitoring mode.

        Args:
            mode: The monitoring mode to set.
        """
        # Always get the latest instance from the global registry
        state = _get_monitoring_state()
        state.set_mode(mode)

def configure_monitoring(mode: str) -> None:
    """Configure monitoring mode.
    
    Args:
        mode: Monitoring mode ('none' or 'basic')
        
    Raises:
        ValueError: If mode is not 'none' or 'basic'
    """
    if mode.lower() not in ["none", "basic"]:
        raise ValueError('Monitoring mode must be either "none" or "basic"')
    
    # Use the MonitoringConfig class to set the mode
    MonitoringConfig.set_mode(mode.lower())
    Logger.info(f"Monitoring configured: {mode}")

def monitor_query_performance(func_or_mode=None) -> Callable:
    """Decorator to monitor query performance.
    
    This can be used in two ways:
    1. As a decorator directly: @monitor_query_performance
    2. As a function to configure monitoring: monitor_query_performance("basic")
    
    Args:
        func_or_mode: Either a function to decorate or a string specifying the monitoring mode
        
    Returns:
        Decorated function or None if used to configure monitoring
    """
    # If called with a string argument, it's being used to configure monitoring
    if isinstance(func_or_mode, str):
        configure_monitoring(func_or_mode)
        return
        
    def decorator(f):
        # Check if the function is async
        is_async = inspect.iscoroutinefunction(f)
        
        if is_async:
            @wraps(f)
            async def wrapper(*args, **kwargs):
                # Always get the latest state from the global registry
                monitoring_mode = MonitoringConfig.get_mode()
                
                if not monitoring_mode or monitoring_mode == "none":
                    # Even when monitoring is disabled, return a tuple for consistent interface
                    result = await f(*args, **kwargs)
                    return result, 0
                    
                start_time = time.time()
                try:
                    result = await f(*args, **kwargs)
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
            return wrapper
        else:
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Always get the latest state from the global registry
                monitoring_mode = MonitoringConfig.get_mode()
                
                if not monitoring_mode or monitoring_mode == "none":
                    # Even when monitoring is disabled, return a tuple for consistent interface
                    result = f(*args, **kwargs)
                    return result, 0
                    
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
            return wrapper
    
    # Handle both @monitor_query_performance and @monitor_query_performance() syntax
    if func_or_mode is None:
        return decorator
    return decorator(func_or_mode)

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
    for line in re.split(r'\\r\\n|\\r|\\n', sql):
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
    pattern = r"(?<!:):(\w+)"
    
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

async def ensure_connection(conn_or_string: Union[psycopg.AsyncConnection, str]) -> Tuple[psycopg.AsyncConnection, bool]:
    """Ensure we have a database connection.
    
    Args:
        conn_or_string: Connection object or connection string
        
    Returns:
        Tuple of (connection, should_close)
    """
    should_close = False
    
    if isinstance(conn_or_string, str):
        # It's a connection string, create a new connection
        conn = await psycopg.AsyncConnection.connect(conn_or_string, autocommit=True)
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
async def {function_name}(conn, {param_list}) -> {return_type}:
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
async def {function_name}(conn) -> {return_type}:
    """{function_doc}
    
    Args:
        conn: Database connection or connection string
        
    Returns:
{return_doc}
    """
{function_body}
'''

# Template for SELECT query function body
SELECT_QUERY_BODY = """    # Get connection
    conn, should_close = await ensure_connection(conn)
    
    try:
{process_conditional_blocks}
        # Convert named parameters
        sql = convert_named_params(sql)
        sql = cleanup_sql(sql)
        # Execute query
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql{params_arg})
{result_fetch}
    finally:
        if should_close:
            await conn.close()
"""

# Template for INSERT/UPDATE/DELETE query function body
MODIFY_QUERY_BODY = """    # Get connection
    conn, should_close = await ensure_connection(conn)
    
    try:
{process_conditional_blocks}
        # Convert named parameters
        sql = convert_named_params(sql)
        sql = cleanup_sql(sql)
        # Execute query
        async with conn.cursor(row_factory=dict_row) as cur:
            await cur.execute(sql{params_arg})
            # Commit changes before returning
            await conn.commit()
{result_fetch}
    finally:
        if should_close:
            await conn.close()
"""

# Template for single row result fetch
SINGLE_ROW_FETCH = """            result = await cur.fetchone()
            return result"""

# Template for multiple rows result fetch
MULTIPLE_ROWS_FETCH = """            result = await cur.fetchall()
            return result"""

# Template for exec result fetch
EXEC_RESULT_FETCH = """            # For INSERT/UPDATE with RETURNING
            result = await cur.fetchone()
            return result"""

# Template for exec rows fetch
EXEC_ROWS_FETCH = """            # Return affected row count
            return cur.rowcount"""

# Template for exec (no result)
EXEC_NO_RESULT = """            # No result to return
            return None"""

# Template for conditional blocks processing
CONDITIONAL_BLOCKS_PROCESSING = """    # Process conditional blocks in SQL
    sql = process_conditional_blocks(sql, {params_dict})
"""

# Template for static SQL
STATIC_SQL = '''        # Static SQL (no conditional blocks)
        sql = """{sql}"""
'''
