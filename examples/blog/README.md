# Blog Example

This example demonstrates how to use team-query with a fictional blog database containing authors, posts, and comments.

## Database Schema

The database consists of three main tables:
- `authors`: Information about blog authors
- `posts`: Blog posts written by authors
- `comments`: Comments on blog posts by readers

## Files in this Example

- `schema.sql`: Database schema definition
- `seed_data.sql`: Sample data for testing
- `team-query.yaml`: Configuration file for team-query
- `authors.sql`: Queries related to authors
- `posts.sql`: Queries related to posts
- `comments.sql`: Queries related to comments
- `python_example.py`: Example usage with Python
- `javascript_example.js`: Example usage with JavaScript

## Getting Started

1. Create and seed the database:
   ```bash
   createdb blog_example
   psql -d blog_example -f schema.sql
   psql -d blog_example -f seed_data.sql
   ```

2. Generate the code:
   ```bash
   # Using the CLI directly
   team-query generate --config team-query.yaml
   
   # Or using Poetry (if you are developing team-query)
   poetry run blog-example
   ```

3. Set up Python environment:
   ```bash
   # Create a virtual environment (optional but recommended)
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   
   # Install required dependencies
   # For bash:
   pip install "psycopg[binary]" loguru
   # For zsh:
   pip install "psycopg[binary]" loguru
   ```

4. Set up JavaScript environment:
   ```bash
   # Make sure you have Node.js version 14 or higher installed
   # You can check your version with: node --version
   
   # Install required dependencies
   npm install pg
   ```

   > **Note:** These examples require Node.js version 14 or higher. You can check your Node.js version with `node --version`.

5. Run the examples:
   ```bash
   # Python example
   python python_example.py
   
   # JavaScript example
   node javascript_example.js
   ```

## Configuration

The `team-query.yaml` file configures how the code is generated. You can modify this file to change:
- Output directories
- Target languages
- SQL query files to process
- Code generation options

## Database Connection

Both examples assume a PostgreSQL database running on localhost with default settings. If your database has different connection parameters, you'll need to modify the connection settings in the example files.
