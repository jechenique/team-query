"""Python code templates for the Python compiler."""

# Template for the __init__.py file
INIT_FILE = '''"""Generated database access code."""
'''

# Template for the utils.py file
UTILS_FILE = '''"""Utility functions for database access."""
import logging
import time
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple, Union, Callable
import re
import psycopg
from psycopg.rows import dict_row

# Configure logging
logger = logging.getLogger("team_query")

def set_log_level(level: str) -> None:
    """Set the log level for the team_query logger."""
    numeric_level = getattr(logging, level.upper(), None)
    if not isinstance(numeric_level, int):
        raise ValueError(f"Invalid log level: {level}")
    logger.setLevel(numeric_level)
    # Add a handler if none exists
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

# Default to INFO level
set_log_level("INFO")

# Monitoring configuration
_monitoring_mode = None

def configure_monitoring(mode: str) -> None:
    """Configure monitoring mode.
    
    Args:
        mode: Monitoring mode ('none', 'basic', or 'detailed')
    """
    global _monitoring_mode
    _monitoring_mode = mode.lower()
    logger.info(f"Monitoring configured: {mode}")

def monitor_query_performance(func: Callable) -> Callable:
    """Decorator to monitor query performance.
    
    Args:
        func: Function to decorate
        
    Returns:
        Decorated function
    """
    def wrapper(*args, **kwargs):
        """Wrapper function."""
        if not _monitoring_mode or _monitoring_mode == "none":
            return func(*args, **kwargs)
            
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            end_time = time.time()
            execution_time = end_time - start_time
            
            # Get function name for logging
            func_name = func.__name__
            
            if _monitoring_mode == "basic":
                logger.debug(f"Query {func_name} executed in {execution_time:.6f} seconds")
            elif _monitoring_mode == "detailed":
                # More detailed logging
                logger.debug(f"Query {func_name} executed in {execution_time:.6f} seconds with args: {args}, kwargs: {kwargs}")
            
            return result
        except Exception as e:
            end_time = time.time()
            execution_time = end_time - start_time
            logger.error(f"Query {func.__name__} failed after {execution_time:.6f} seconds: {str(e)}")
            raise
    
    return wrapper

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
    for line in sql.split("\n"):
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
    # Replace :name with %(name)s
    pattern = r":(\w+)"
    return re.sub(pattern, r"%(\1)s", sql)

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
