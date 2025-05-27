"""JavaScript code templates for the JavaScript compiler."""

# Template for the logger
LOGGER = """
/**
 * Logger utility for database queries
 */
class Logger {
  constructor() {
    this._logger = null;
    this._defaultLogger = console; // Default to console
    this._level = 'info';
    this.levels = {
      error: 0,
      warn: 1,
      info: 2,
      debug: 3
    };
  }

  /**
   * Set a custom logger
   * @param {object} logger - The logger object to use (must have log, error, warn, debug methods)
   */
  setLogger(logger) {
    this._logger = logger;
  }

  /**
   * Set the log level
   * @param {string} level - The log level ('error', 'warn', 'info', 'debug')
   */
  setLevel(level) {
    if (this.levels.hasOwnProperty(level)) {
      this._level = level;
    } else {
      this._warn(`Invalid log level: ${level}. Using 'info' as default.`);
    }
  }

  _shouldLog(level) {
    return this.levels[level] <= this.levels[this._level];
  }

  _log(level, ...args) {
    const logger = this._logger || this._defaultLogger;
    const method = logger[level] || logger.log || (() => {});
    
    if (this._shouldLog(level)) {
      method.call(logger, `[${level.toUpperCase()}]`, ...args);
    }
  }

  error(...args) {
    this._log('error', ...args);
  }

  warn(...args) {
    this._log('warn', ...args);
  }

  info(...args) {
    this._log('info', ...args);
  }

  debug(...args) {
    this._log('debug', ...args);
  }
}

// Create a singleton instance
const logger = new Logger();

// Monitoring configuration
let _monitoringMode = 'none';
"""

# Template for the monitoring function
MONITOR_QUERY_PERFORMANCE = """/**
 * Wrap a query function with performance monitoring
 * @param {Function} queryFn - The query function to wrap
 * @param {string} queryName - The name of the query
 * @returns {Function} - The wrapped function
 */
function monitorQueryPerformance(queryFn, queryName) {
  return async function(...args) {
    // Skip monitoring if mode is none
    if (_monitoringMode === "none") {
      return queryFn.apply(this, args);
    }
    
    // For basic monitoring
    if (_monitoringMode === "basic") {
      const startTime = performance.now();
      try {
        const result = await queryFn.apply(this, args);
        const endTime = performance.now();
        const executionTime = (endTime - startTime) / 1000; // Convert to seconds
        if (typeof logger.debug === 'function') {
          logger.debug(`Query ${queryName} executed in ${executionTime.toFixed(6)} seconds`);
        }
        return [result, executionTime];
      } catch (error) {
        const endTime = performance.now();
        const executionTime = (endTime - startTime) / 1000; // Convert to seconds
        if (typeof logger.error === 'function') {
          logger.error(`Query ${queryName} failed after ${executionTime.toFixed(6)} seconds: ${error.message}`);
        }
        throw error;
      }
    }
    
    // If we get here, monitoring is disabled
    return queryFn.apply(this, args);
  };
}
"""

# Template for the monitoring configuration
MONITORING_CONFIG = """/**
 * Configure performance monitoring for database queries
 * @param {string} mode - Monitoring mode: "none" or "basic"
 */
function configureMonitoring(mode = "none") {
  // Validate mode
  if (!["none", "basic"].includes(mode)) {
    throw new Error("Monitoring mode must be either 'none' or 'basic'");
  }
  
  _monitoringMode = mode;
  logger.info(`Monitoring configured: ${mode}`);
}
"""

# Template for conditional blocks processing
CONDITIONAL_BLOCKS = """/**
 * Process conditional blocks in SQL
 * @param {string} sql - SQL with conditional blocks
 * @param {object} params - Parameters for the query
 * @returns {string} - Processed SQL
 */
function processConditionalBlocks(sql, params) {
  // Regular expression to match conditional blocks
  // Format: /* IF param */.../* END IF */
  const ifRegex = /\\/\\* IF ([a-zA-Z0-9_]+) \\*\\/([\\s\\S]*?)\\/\\* END IF \\*\\//g;
  
  // Process each conditional block
  let processedSql = sql;
  let match;
  
  // Reset lastIndex to ensure we start from the beginning
  ifRegex.lastIndex = 0;
  
  while ((match = ifRegex.exec(sql)) !== null) {
    const paramName = match[1];
    const conditionalContent = match[2];
    
    // Check if the parameter exists and is truthy
    if (params[paramName]) {
      // Replace the conditional block with its content
      processedSql = processedSql.replace(match[0], conditionalContent);
    } else {
      // Remove the conditional block
      processedSql = processedSql.replace(match[0], '');
    }
  }
  
  return processedSql;
}
"""

# Template for SQL cleanup
SQL_CLEANUP = """/**
 * Clean up SQL by removing extra whitespace and comments
 * @param {string} sql - SQL to clean up
 * @returns {string} - Cleaned SQL
 */
function cleanupSql(sql) {
  // Remove single-line comments
  let cleanSql = sql.replace(/--.*$/gm, '');
  
  // Remove multi-line comments (except conditional blocks)
  cleanSql = cleanSql.replace(/\\/\\*(?!\\s*IF)[\\s\\S]*?\\*\\//g, '');
  
  // Replace multiple whitespace with a single space
  cleanSql = cleanSql.replace(/\\s+/g, ' ');
  
  // Trim leading and trailing whitespace
  cleanSql = cleanSql.trim();
  
  return cleanSql;
}
"""

# Template for named parameters conversion
NAMED_PARAMS = """/**
 * Convert named parameters to positional parameters for PostgreSQL
 * @param {string} sql - SQL with named parameters
 * @param {object} params - Named parameters
 * @returns {object} - Object with converted SQL and values array
 */
function convertNamedParams(sql, params) {
  const values = [];
  const paramRegex = /:([a-zA-Z0-9_]+)/g;
  
  // Reset lastIndex to ensure we start from the beginning
  paramRegex.lastIndex = 0;
  
  // Replace named parameters with positional parameters
  const convertedSql = sql.replace(paramRegex, (match, paramName) => {
    if (params[paramName] !== undefined) {
      values.push(params[paramName]);
      return `$${values.length}`;
    }
    return match;
  });
  
  return { sql: convertedSql, values };
}
"""

# Template for ensuring connection
ENSURE_CONNECTION = """/**
 * Ensure a database connection is available
 * @param {object|string} connection - Database connection, pool, or connection string
 * @returns {object} - Database connection
 */
async function ensureConnection(connection) {
  // If connection is already a client or pool, return it
  if (connection && typeof connection !== 'string') {
    // TODO: Add checks to ensure it's a valid pg Client or Pool
    return connection;
  }
  
  // If connection is a string, create a new client
  if (typeof connection === 'string') {
    const { Client } = require('pg');
    const client = new Client(connection);
    await client.connect(); // Wait for connection to establish
    return client;
  }
  
  // If no connection provided, throw error
  throw new Error('No database connection provided');
}
"""

# Template for transaction creation
CREATE_TRANSACTION = """/**
 * Create a transaction object
 * @param {object|string} connection - Database connection, pool, or connection string
 * @returns {object} - Transaction object
 */
async function createTransaction(connection) {
  const db = await ensureConnection(connection);
  const isNewConnection = typeof connection === 'string';
  let client = null;
  
  return {
    /**
     * Begin a transaction
     * @returns {Promise<void>}
     */
    async begin() {
      if (!client) {
        if (db.query) {
          // If db is already a client, use it directly
          client = db;
          client._transactionClient = true;
        } else {
          // If db is a pool, get a client from the pool
          client = await db.connect();
          client._transactionClient = true;
        }
      }
      await client.query('BEGIN');
      logger.debug('Transaction started');
      return client;
    },
    
    /**
     * Commit a transaction
     * @returns {Promise<void>}
     */
    async commit() {
      if (!client) {
        throw new Error('No active transaction to commit');
      }
      await client.query('COMMIT');
      logger.debug('Transaction committed');
      if (client !== db) {
        client.release();
      }
      if (isNewConnection) {
        await db.end();
      }
      client = null;
    },
    
    /**
     * Rollback a transaction
     * @returns {Promise<void>}
     */
    async rollback() {
      if (!client) {
        throw new Error('No active transaction to rollback');
      }
      await client.query('ROLLBACK');
      logger.debug('Transaction rolled back');
      if (client !== db) {
        client.release();
      }
      if (isNewConnection) {
        await db.end();
      }
      client = null;
    },
    
    /**
     * Get the transaction client
     * @returns {object} - Transaction client
     */
    getClient() {
      if (!client) {
        throw new Error('No active transaction client');
      }
      return client;
    },
    
    /**
     * Execute a function within the transaction
     * @param {Function} fn - Function to execute
     * @returns {Promise<any>} - Result of the function
     */
    async execute(fn) {
      if (!client) {
        throw new Error('No active transaction client');
      }
      return await fn(client);
    }
  };
}
"""

# Template for module exports
MODULE_EXPORTS = """// Export utility functions
module.exports = {
  logger,
  configureMonitoring,
  monitorQueryPerformance,
  processConditionalBlocks,
  cleanupSql,
  convertNamedParams,
  ensureConnection,
  createTransaction
};
"""
