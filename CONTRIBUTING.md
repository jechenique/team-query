# Contributing to Team Query

Thank you for your interest in contributing to Team Query! This guide will help you understand how to contribute to the project, particularly how to implement new language plugins.

## Project Structure

The project is organized as follows:

```
team-query/
├── examples/           # Example projects
├── src/                # Source code
│   └── team_query/     # Main package
│       ├── builders/   # Query builders
│       ├── compilers/  # Language compilers
│       │   ├── base.py # Base compiler class
│       │   ├── python/ # Python compiler plugin
│       │   ├── js/     # JavaScript compiler plugin
│       │   └── ...     # Other language plugins
│       ├── models.py   # Data models
│       ├── parser.py   # SQL parser
│       └── ...
└── ...
```

## Implementing a New Language Plugin

To implement a new language plugin, you need to create a new folder in the `src/team_query/compilers/` directory with the following files:

1. `__init__.py` - Entry point for the plugin
2. `compiler.py` - Compiler implementation
3. `templates.py` - Code templates

### 1. Create the Plugin Directory

First, create a directory for your language plugin:

```
src/team_query/compilers/rust/
```

### 2. Create the Templates File

Next, create a `templates.py` file in your plugin directory with all the code templates for your language. This should include templates for:

- Utility functions
- Query function templates
- SQL processing templates
- Any other language-specific templates

Example (`rust/templates.py`):

```python
"""Rust code templates for the Rust compiler."""

# Template for the lib.rs file
LIB_FILE = '''//! Generated database access code.
use tokio_postgres::{Client, Row};
use std::error::Error;
use std::time::Instant;

pub mod utils;
'''

# Template for the utils.rs file
UTILS_FILE = '''//! Utility functions for database access.
use tokio_postgres::{Client, Row};
use std::error::Error;
use std::time::Instant;

// Logger implementation
pub struct Logger {
    level: LogLevel,
}

pub enum LogLevel {
    Debug,
    Info,
    Warning,
    Error,
}

impl Logger {
    pub fn new(level: LogLevel) -> Self {
        Logger { level }
    }
    
    pub fn debug(&self, message: &str) {
        if matches!(self.level, LogLevel::Debug) {
            println!("[DEBUG] {}", message);
        }
    }
    
    // Other logging methods...
}

// More utility functions...
'''

# Other templates...
```

### 3. Create the Compiler Implementation

Next, create a `compiler.py` file in your plugin directory that implements the compiler logic. This should inherit from the `BaseCompiler` class and implement the required methods.

Example (`rust/compiler.py`):

```python
"""Rust compiler implementation module."""
import os
from typing import List, Dict, Any, Optional

from team_query.compilers.base import BaseCompiler
from team_query.compilers.rust.templates import (
    LIB_FILE,
    UTILS_FILE,
    # Import other templates...
)
from team_query.models import QueriesFile, SQLConfig, Query


class RustCompiler(BaseCompiler):
    """Compiler for Rust code."""

    def __init__(self):
        """Initialize the Rust compiler."""
        super().__init__()
        self.query_files = []
        self.config = None
        self.output_dir = ""

    def compile(self, queries_files: List[QueriesFile], config: SQLConfig, output_dir: str) -> None:
        """Compile SQL queries to Rust code."""
        print(f"Rust compiler: Starting compilation to {output_dir}")
        self.query_files = queries_files
        self.config = config
        
        # Clean output directory and ensure it exists
        self.clean_output_directory(output_dir)
        self.create_output_dir(output_dir)
        
        # Create lib.rs
        self._create_lib_file(os.path.join(output_dir, "lib.rs"))
        
        # Create utils.rs
        self._create_utils_file(os.path.join(output_dir, "utils.rs"))
        
        # Process each query file
        print(f"Processing {len(queries_files)} query files")
        for query_file in queries_files:
            module_name = self._get_module_name(query_file.name)
            output_file = os.path.join(output_dir, f"{module_name}.rs")
            self._create_query_file(query_file, output_file)
    
    def _create_lib_file(self, file_path: str) -> None:
        """Create a lib.rs file."""
        print(f"Creating file: {file_path}")
        with open(file_path, "w") as f:
            f.write(LIB_FILE)
    
    def _create_utils_file(self, file_path: str) -> None:
        """Create a utils.rs file with utility functions."""
        print(f"Creating file: {file_path}")
        with open(file_path, "w") as f:
            f.write(UTILS_FILE)
    
    def _get_module_name(self, file_name: str) -> str:
        """Get the module name from a file name."""
        # Remove path and extension
        base_name = os.path.basename(file_name)
        module_name = os.path.splitext(base_name)[0]
        return module_name
    
    def _create_query_file(self, query_file: QueriesFile, output_file: str) -> None:
        """Create a Rust file for a query file."""
        # Implementation...
    
    def _generate_query_function(self, query: Query) -> str:
        """Generate a Rust function for a query."""
        # Implementation...
    
    # Other methods...
```

### 4. Create the Entry Point

Finally, create an `__init__.py` file in your plugin directory that serves as the entry point for your plugin. This should be a simple wrapper that imports and uses your compiler class.

Example (`rust/__init__.py`):

```python
"""Rust compiler module."""
import os
from typing import List

from team_query.compilers.rust.compiler import RustCompiler
from team_query.models import QueriesFile, SQLConfig


def compile(queries_files: List[QueriesFile], config: SQLConfig, output_dir: str) -> None:
    """Compile SQL queries to Rust code."""
    compiler = RustCompiler()
    compiler.compile(queries_files, config, output_dir)
```

### 4. Register Your Plugin

To make your plugin available to the team-query tool, you need to register it in the `src/team_query/plugins.py` file:

```python
def get_available_plugins():
    """Get a list of available plugins."""
    return {
        "python": "team_query.compilers.python",
        "javascript": "team_query.compilers.javascript",
        "rust": "team_query.compilers.rust",  # Add your plugin here
    }
```

## Best Practices

When implementing a new language plugin, follow these best practices:

1. **Separation of Concerns**: Keep templates separate from logic
2. **Consistent Structure**: Follow the same structure as existing plugins
3. **Error Handling**: Provide clear error messages for compilation issues
4. **Documentation**: Document your code and provide examples
5. **Testing**: Add tests for your plugin

## Testing Your Plugin

To test your plugin, you can use the example projects in the `examples/` directory. Add your plugin to the configuration file and run the code generation:

```yaml
sql:
  - queries: ["./queries/*.sql"]
    schema: ["public"]
    engine: postgresql
    gen:
      - plugin: rust  # Your plugin
        out: "./generated/rust"
```

Then run:

```bash
team-query generate --config team-query.yaml
```

## Submitting Your Contribution

Once you've implemented and tested your plugin, you can submit a pull request:

1. Fork the repository
2. Create a branch for your feature
3. Commit your changes
4. Push to your branch
5. Submit a pull request

Thank you for contributing to Team Query!
