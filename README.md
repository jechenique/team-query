# Team Query

> The ORM you get when you love SQL but hate typing it twice.

A SQL-first code generator inspired by [sqlc](https://github.com/sqlc-dev/sqlc) that creates type-safe database clients for multiple languages from SQL query files.

[![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)](https://github.com/jechenique/team-query)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

## **Why *Not* Using Team Query?**  
*A bold tale of chaos, creativity, and the art of duplicating SQL in every language imaginable.*

Ah, Team Query—so preachy, so organized, so… *collaborative*. But let’s be honest: where’s the fun in shared logic, code reusability, and consistent data access when you could just wing it?

---

### **1. Embrace Creative SQL Expression**  
Why settle for one boring, correct version of a SQL query when each engineer can write their *own* slightly different, definitely-not-bug-free version?

**Analytics Team:**
``` sql
SELECT u.id AS user_id, AVG(o.total_amount) AS avg_order_value
FROM users u
JOIN orders o ON u.id = o.user_id
WHERE o.created_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY u.id
```

**Backend Team:**
``` sql
SELECT o.user_id, SUM(o.total_amount) / COUNT(DISTINCT o.id) AS avg_order_value
FROM orders o
WHERE o.created_at >= NOW() - INTERVAL '1 month'
GROUP BY o.user_id
```

**Data Engineering:**
``` sql
SELECT user_id, ROUND(AVG(order_value)::numeric, 2) AS avg_order_value
FROM (
  SELECT user_id, SUM(amount) AS order_value
  FROM order_items
  WHERE created_at >= DATE_TRUNC('day', NOW() - INTERVAL '30 days')
  GROUP BY order_id, user_id
) sub
GROUP BY user_id
```

Who needs consistency when you’ve got *character*?

---

### **2. Promote Job Security Through Mystery**  
When no one knows which version of the query is “the real one,” debugging becomes an exciting, career-building treasure hunt.  
**SQL spelunking**: a new sport for engineers.

---

### **3. Strengthen Team Bonding Over Cross-Team Blame**  
- Frontend team broke the app? Backend says “works on my query.”  
- Backend returns bad data? Frontend says “not my logic.”  

Thanks to the *absence* of a shared source of truth, everyone gets to participate in a lively blame game—perfect for team morale!

---

### **4. Enable Infinite Customization**  
Why let one boring Team Query dictate your style when each team can implement their own caching, parameterization, pagination, and bug?  
Think of all the slightly-off implementations you can proudly call your own.

---

### **5. Make Onboarding Unforgettable**  
New engineer asks:
>“Where’s the query for revenue?”

You say:
> “Depends. Which version do you want? The Python one, the JavaScript one, or the undocumented legacy one from 2017?”

They’ll never forget their first week. Neither will HR.

---

So next time someone preaches Team Query, just smile and say,  
> “No thanks. I prefer a *little* chaos in my SQL.”

## Table of Contents
1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Connection Flexibility](#connection-flexibility)
5. [Writing SQL Queries](#writing-sql-queries)
   - [Query Annotations](#query-annotations)
   - [Parameter Types](#parameter-types)
   - [Dynamic Queries](#dynamic-queries)
   - [Conditional SQL Blocks](#conditional-sql-blocks)
   - [Result Types](#result-types)
6. [Using Generated Code](#using-generated-code)
   - [Python Usage](#python-usage)
   - [JavaScript Usage](#javascript-usage)
   - [Logging](#logging)
   - [Performance Monitoring](#performance-monitoring)
   - [Transaction Support](#transaction-support)
7. [Recommended Team Workflow](#recommended-team-workflow)
8. [Configuration](#configuration)
9. [Advanced Features](#advanced-features)
10. [Building and Publishing](#building-and-publishing)
11. [Contributing](#contributing)
12. [License](#license)
## Overview

Team Query lets you write SQL queries once and generate type-safe database clients for multiple programming languages. It's designed for developers who:

- Prefer writing SQL directly rather than using an ORM
- Want type safety and IDE autocompletion
- Need to support multiple programming languages
- Want to avoid duplicating database logic across languages

**Key Features:**
- Write SQL queries in `.sql` files with type annotations
- Generate type-safe clients for Python and JavaScript 
- Support for dynamic queries with conditional blocks
- Built-in logging and performance monitoring
- Transaction support
- Parameter validation to prevent SQL injection

## Installation

```bash
# Quick installation using the provided shell script (recommended)
curl -sSL https://raw.githubusercontent.com/jechenique/team-query/master/install.sh | bash

# Install as a library
pip install team-query

# Install as a CLI tool
pipx install team-query
```

## Quick Start

1. **Create SQL query files**

```sql
-- name: GetUserById :one
-- param: id int User ID
SELECT * FROM users WHERE id = :id;

-- name: CreateUser :execresult
-- param: name string User's name
-- param: email string User's email
INSERT INTO users (name, email) 
VALUES (:name, :email)
RETURNING id, name, email;
```

2. **Create a configuration file** (`team-query.yaml`)

```yaml
version: 1
project:
  name: myproject
  version: "1.0.0"
sql:
  - queries: ["./queries/*.sql"]
    schema: ["public"]
    engine: postgresql
    gen:
      - plugin: python
        out: "./generated/python"
      - plugin: javascript
        out: "./generated/javascript"
```

3. **Generate code**

```bash
team-query generate --config team-query.yaml
```

4. **Use the generated code**

Python:
```python
from generated.python import GetUserById, ListActiveUsers, SearchUsers

# Connect to database
import psycopg
conn = psycopg.connect("postgresql://user:password@localhost/dbname")

# Simple query with required parameters
user = GetUserById(conn, id=1)
print(f"Found user: {user['name']}")

# Query with limit
users = ListActiveUsers(conn, limit=10)
for user in users:
    print(f"Active user: {user['name']}")

# Dynamic query with optional parameters
search_results = SearchUsers(
    conn,
    name="John",     # Optional - will be included in WHERE clause
    email=None,      # Optional - will be excluded from WHERE clause
    limit=10,
    offset=0
)
```

JavaScript:
```javascript
// Import generated functions
const { GetUserById, ListActiveUsers, SearchUsers } = require('./generated/javascript');

// Connect to database
const { Pool } = require('pg');
const pool = new Pool({
  connectionString: 'postgresql://user:password@localhost/dbname'
});

async function main() {
  // Simple query with required parameters
  const user = await GetUserById(pool, { id: 1 });
  console.log(`Found user: ${user.name}`);
  
  // Query with limit
  const users = await ListActiveUsers(pool, { limit: 10 });
  users.forEach(user => {
    console.log(`Active user: ${user.name}`);
  });
  
  // Dynamic query with optional parameters
  const searchResults = await SearchUsers(pool, {
    name: "John",    // Optional - will be included in WHERE clause
    limit: 10,
    offset: 0
  });
}

main().catch(console.error);
```

## Connection Flexibility

The generated query functions are designed to be flexible with database connections:

- **Python**: Functions can accept either:
  - An existing connection object (`psycopg.Connection`)
  - A connection string (e.g., `"postgresql://user:password@localhost/dbname"`)

- **JavaScript**: Functions can accept either:
  - A Pool object from the `pg` package
  - A Client object from the `pg` package
  - A connection string (e.g., `"postgresql://user:password@localhost/dbname"`)

This flexibility allows you to manage connections however best suits your application's needs - either by passing connection strings directly to query functions or by managing connection pools externally.

## Writing SQL Queries

### Query Annotations

Each SQL query needs annotations to define its name and return type:

```sql
-- name: QueryName :returnType
-- param: paramName paramType Description
SQL_QUERY_HERE;
```

Return types:
- `:one` - Returns a single record
- `:many` - Returns multiple records
- `:exec` - Executes without returning data
- `:execrows` - Returns affected row count
- `:execresult` - Returns result data (for INSERT/UPDATE with RETURNING)

Example:
```sql
-- name: ListActiveUsers :many
-- param: limit int Maximum number of users to return
SELECT id, name, email FROM users 
WHERE active = true 
ORDER BY created_at DESC
LIMIT :limit;
```

### Parameter Types

Define parameters with type annotations:

```sql
-- param: paramName paramType [optional description]
```

Supported types:
- `int`, `integer`, `bigint`, `smallint`
- `string`, `text`, `varchar`, `char`
- `bool`, `boolean`
- `float`, `real`, `double`
- `decimal`, `numeric`
- `date`, `time`, `timestamp`, `timestamptz`
- `json`, `jsonb`
- `uuid`
- `bytea`

### Dynamic Queries

Create dynamic queries with optional parameters:

```sql
-- name: SearchUsers :many
-- param: name string Optional name filter
-- param: email string Optional email filter
-- param: limit int Maximum results to return
-- param: offset int Pagination offset
SELECT * FROM users
WHERE 
  (:name IS NULL OR name ILIKE '%' || :name || '%') AND
  (:email IS NULL OR email ILIKE '%' || :email || '%')
ORDER BY name
LIMIT :limit OFFSET :offset;
```

### Conditional SQL Blocks

For better performance with dynamic queries, use conditional blocks:

```sql
-- name: SearchUsers :many
-- param: name string Optional name filter
-- param: email string Optional email filter
-- param: limit int Maximum results to return
-- param: offset int Pagination offset
SELECT * FROM users
WHERE 
  -- {name
  AND name ILIKE '%' || :name || '%'
  -- }
  -- {email
  AND email ILIKE '%' || :email || '%'
  -- }
ORDER BY name
LIMIT :limit OFFSET :offset;
```

When a parameter is null/undefined, its entire block is removed from the query. This creates more efficient SQL that can better utilize indexes.

### Result Types

Query results are returned as:

- **Python**: Dictionary objects with column names as keys
- **JavaScript**: Plain JavaScript objects with column names as properties

This makes the results easy to work with and compatible with most frameworks and libraries.

## Using Generated Code

### Python Usage

The generated Python code provides a clean, type-safe API for database operations:

```python
# Import generated functions
from generated.python import GetUserById, ListActiveUsers, SearchUsers

# Connect to database
import psycopg
conn = psycopg.connect("postgresql://user:password@localhost/dbname")

# Simple query with required parameters
user = GetUserById(conn, id=1)
print(f"Found user: {user['name']}")

# Query with limit
users = ListActiveUsers(conn, limit=10)
for user in users:
    print(f"Active user: {user['name']}")

# Dynamic query with optional parameters
search_results = SearchUsers(
    conn,
    name="John",     # Optional - will be included in WHERE clause
    email=None,      # Optional - will be excluded from WHERE clause
    limit=10,
    offset=0
)
```

### JavaScript Usage

The generated JavaScript code provides an async/await API for database operations:

```javascript
// Import generated functions
const { GetUserById, ListActiveUsers, SearchUsers } = require('./generated/javascript');

// Connect to database
const { Pool } = require('pg');
const pool = new Pool({
  connectionString: 'postgresql://user:password@localhost/dbname'
});

async function main() {
  // Simple query with required parameters
  const user = await GetUserById(pool, { id: 1 });
  console.log(`Found user: ${user.name}`);
  
  // Query with limit
  const users = await ListActiveUsers(pool, { limit: 10 });
  users.forEach(user => {
    console.log(`Active user: ${user.name}`);
  });
  
  // Dynamic query with optional parameters
  const searchResults = await SearchUsers(pool, {
    name: "John",    // Optional - will be included in WHERE clause
    // email is undefined - will be excluded from WHERE clause
    limit: 10,
    offset: 0
  });
}

main().catch(console.error);
```

### Logging

Both Python and JavaScript clients include built-in logging and performance monitoring:

#### Python Logging

```python
from generated.python import set_log_level, set_logger

# Set log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
set_log_level("DEBUG")

# Use a custom logger if desired
from logging import getLogger
custom_logger = getLogger("my_app")
set_logger(custom_logger)

# Now all database operations will log at the specified level
user = GetUserById(conn, id=1)  # Will log query details at DEBUG level
```

#### JavaScript Logging

```javascript
const { setLogLevel, setLogger } = require('./generated/javascript');

// Set log level (debug, info, warn, error)
setLogLevel('debug');

// Use a custom logger if desired
const customLogger = {
  debug: (msg) => console.debug(`[DB] ${msg}`),
  info: (msg) => console.info(`[DB] ${msg}`),
  warn: (msg) => console.warn(`[DB] ${msg}`),
  error: (msg) => console.error(`[DB] ${msg}`)
};
setLogger(customLogger);

// Now all database operations will log at the specified level
const user = await GetUserById(pool, { id: 1 });  // Will log query details at debug level
```

### Performance Monitoring

Team Query includes basic performance monitoring to help track query execution times:

#### Python Monitoring

```python
from generated.python import configure_monitoring

# Option 1: No monitoring (default)
configure_monitoring(mode="none")

# Option 2: Basic monitoring (logs execution time)
configure_monitoring(mode="basic")

# Use queries normally - they'll be monitored according to configuration
user = GetUserById(conn, id=1)  # Will log execution time at DEBUG level
```

#### JavaScript Monitoring

```javascript
const { configureMonitoring } = require('./generated/javascript');

// Option 1: No monitoring (default)
configureMonitoring("none");

// Option 2: Basic monitoring (logs execution time)
configureMonitoring("basic");

// Use queries normally - they'll be monitored according to configuration
const user = await GetUserById(pool, { id: 1 });  // Will log execution time at debug level
});

// Use queries normally - they will be monitored according to configuration
const user = await GetUserById(pool, { id: 1 });
```

### Transaction Support

#### Python Transactions

```python
// Using psycopg transaction support
with conn.cursor() as cur:
    conn.autocommit = False
    try:
        author = CreateAuthor(conn, name="John", bio="A writer")
        book = CreateBook(conn, title="My Book", author_id=author["id"])
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
```

#### JavaScript Transactions

```javascript
// Using the built-in transaction manager
const { createTransaction } = require('./generated/javascript');

async function createAuthorWithBooks() {
  const tx = createTransaction(pool);
  try {
    await tx.begin();
    const author = await CreateAuthor(tx.client, { name: "John", bio: "A writer" });
    const book = await CreateBook(tx.client, { 
      title: "My Book", 
      author_id: author.id
    });
    await tx.commit();
    return { author, book };
  } catch (error) {
    await tx.rollback();
    throw error;
  }
}
```

#### Getting a Client Directly

For more flexibility, you can get a client directly and manage transactions manually:

##### Python

```python
// Using psycopg directly
import psycopg

// Get a connection
conn = psycopg.connect("postgresql://user:password@localhost/dbname")

// Start a transaction
conn.autocommit = False
try:
    // Execute multiple queries in the same transaction
    user = CreateUser(conn, name="Alice", email="alice@example.com")
    profile = CreateUserProfile(conn, user_id=user["id"], bio="Software Engineer")
    
    // Custom SQL if needed
    with conn.cursor() as cur:
        cur.execute("UPDATE user_stats SET last_login = NOW() WHERE user_id = %s", (user["id"],))
    
    // Commit when done
    conn.commit()
except Exception as e:
    conn.rollback()
    raise e
finally:
    conn.close()
```

##### JavaScript

```javascript
// Using pg directly
const { Pool } = require('pg');
const pool = new Pool({
  connectionString: 'postgresql://user:password@localhost/dbname'
});

async function complexTransaction() {
  // Get a client from the pool
  const client = await pool.connect();
  
  try {
    // Start transaction
    await client.query('BEGIN');
    
    // Execute generated queries with the client
    const user = await CreateUser(client, { name: "Alice", email: "alice@example.com" });
    const profile = await CreateUserProfile(client, { userId: user.id, bio: "Software Engineer" });
    
    // Mix with custom queries if needed
    await client.query(
      'UPDATE user_stats SET last_login = NOW() WHERE user_id = $1',
      [user.id]
    );
    
    // Commit transaction
    await client.query('COMMIT');
    return { user, profile };
  } catch (error) {
    // Rollback on error
    await client.query('ROLLBACK');
    throw error;
  } finally {
    // Release client back to pool
    client.release();
  }
}
```

## Recommended Team Workflow

For teams working on multiple projects that share database access, we recommend the following approach:

#### 1. Centralized SQL Repository

Create a dedicated repository for your SQL queries, organized by domain or responsibility:

```
sql-repository/
├── team-query.yaml        # Configuration file
├── schema/
│   └── schema.sql         # Database schema
└── queries/
    ├── users/             # User-related queries
    │   ├── auth.sql       # Authentication queries
    │   └── profiles.sql   # User profile queries
    ├── content/           # Content-related queries
    │   ├── posts.sql      # Blog post queries
    │   └── comments.sql   # Comment queries
    └── analytics/         # Analytics queries
        └── metrics.sql    # Usage metrics queries
```

This structure:
- Keeps all SQL in one place (single source of truth)
- Makes it easy to review SQL changes
- Allows for domain-specific organization
- Facilitates code reviews by domain experts

#### 2. Individual Code Generation

Team members clone the SQL repository and generate code for their specific projects:

```bash
// Clone the SQL repository
git clone https://github.com/your-org/sql-repository.git

// Generate code for your specific project
cd sql-repository
team-query generate --config team-query.yaml --output ../my-project/src/generated
```

#### 3. Continuous Integration

For larger teams, set up CI/CD to automatically generate and publish client packages:

1. Set up a GitHub Action or other CI pipeline that:
   - Triggers on changes to the SQL repository
   - Generates code for each supported language
   - Publishes packages to your package registry (npm, PyPI, etc.)

2. Projects then depend on these published packages:

```bash
// Python project
pip install your-org-db-client

// JavaScript project
npm install @your-org/db-client
```

This workflow ensures:
- Consistent database access across all projects
- Type safety and validation in all languages
- Easy updates when SQL changes
- Minimal duplication of database logic

## Configuration

Create a `team-query.yaml` configuration file:

```yaml
version: 1
project:
  name: myproject
  version: "1.0.0"
sql:
  - queries: ["./queries/*.sql"]  # Path to SQL files (glob pattern)
    schema: ["public"]            # Database schema
    engine: postgresql            # Database engine
    gen:
      - plugin: python            # Generate Python client
        out: "./generated/python" # Output directory
      - plugin: javascript        # Generate JavaScript client
        out: "./generated/javascript"
```

## Advanced Features

### Type Safety and SQL Injection Prevention

Team Query provides built-in type safety and SQL injection prevention:

- Generated code includes type validation for all parameters
- Parameters are passed separately from SQL (never string concatenation)
- Leverages database driver's built-in protection (psycopg for Python, pg for Node.js)

```python
// This will raise a TypeError because id should be an integer
user = GetUserById(conn, id="not_an_integer")
```

## Building and Publishing

If you've made changes to Team Query and want to build and publish your own version, follow these steps:

### Prerequisites

- Python 3.8 or higher
- Poetry (dependency management)
- A PyPI account (for publishing)

### Development Workflow

1. Clone the repository:
   ```bash
   git clone https://github.com/jechenique/team-query.git
   cd team-query
   ```

2. Install development dependencies:
   ```bash
   poetry install
   ```

3. Run code formatters:
   ```bash
   // Format code with Black
   poetry run black src tests

   // Sort imports with isort
   poetry run isort src tests
   ```

4. Run linters and type checking:
   ```bash
   // Run pylint
   poetry run pylint src

   // Run mypy for type checking
   poetry run mypy src
   ```

   > **Note:** If you're using Python 3.13, you may encounter issues with pylint due to compatibility problems with new language features like `typealias`. In this case, you can skip the pylint check or use an earlier Python version for development.
   >
   > **Note on type checking:** The codebase has some mypy errors related to Optional types and missing type annotations. These don't affect functionality but should be addressed over time. To fix missing stubs, run `python -m pip install types-PyYAML`.

5. Run tests to ensure everything works:
   ```bash
   poetry run pytest
   ```

### Building the Package

1. Build the package:
   ```bash
   poetry build
   ```
   
   This will create distribution files in the `dist/` directory.

### Publishing to PyPI

1. Configure Poetry with your PyPI credentials:
   ```bash
   poetry config pypi-token.pypi your-pypi-token
   ```

2. Publish the package:
   ```bash
   poetry publish
   ```

   Or build and publish in one step:
   ```bash
   poetry publish --build
   ```

### Publishing to a Private Repository

For organizations using a private package repository:

1. Configure Poetry with your private repository:
   ```bash
   poetry config repositories.my-repo https://your-repo-url.com/simple/
   poetry config http-basic.my-repo username password
   ```

2. Publish to your private repository:
   ```bash
   poetry publish -r my-repo
   ```

### Automated Publishing with GitHub Actions

You can also set up GitHub Actions to automatically build and publish the package when you create a new release:

1. Create a `.github/workflows/publish.yml` file:
   ```yaml
   name: Publish to PyPI

   on:
     release:
       types: [created]

   jobs:
     deploy:
       runs-on: ubuntu-latest
       steps:
       - uses: actions/checkout@v3
       - name: Set up Python
         uses: actions/setup-python@v4
         with:
           python-version: '3.10'
       - name: Install dependencies
         run: |
           python -m pip install --upgrade pip
           pip install poetry
       - name: Build and publish
         env:
           PYPI_TOKEN: ${{ secrets.PYPI_TOKEN }}
         run: |
           poetry config pypi-token.pypi $PYPI_TOKEN
           poetry build
           poetry publish
   ```

2. Add your PyPI token as a secret in your GitHub repository settings.

3. Create a new release on GitHub to trigger the workflow.

This automated approach ensures consistent builds and simplifies the release process.

## Contributing

Contributions to Team Query are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines on how to contribute to this project, including code style requirements, testing procedures, and the process for submitting pull requests.

## License

MIT License
