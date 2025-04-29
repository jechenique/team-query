"""JavaScript code templates for the JavaScript compiler."""

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
    
    // For OpenTelemetry monitoring
    if (_monitoringMode === "opentelemetry" && _openTelemetryConfigured) {
      try {
        const opentelemetry = require("@opentelemetry/api");
        
        return await opentelemetry.context.with(
          opentelemetry.trace.setSpan(
            opentelemetry.context.active(),
            _tracer.startSpan(`db_query_${queryName}`)
          ),
          async () => {
            const span = opentelemetry.trace.getSpan(opentelemetry.context.active());
            span.setAttribute("db.system", "postgresql");
            span.setAttribute("db.operation", queryName);
            
            const startTime = performance.now();
            try {
              const result = await queryFn.apply(this, args);
              const endTime = performance.now();
              const executionTime = (endTime - startTime) / 1000; // Convert to seconds
              
              // Record metrics
              _queryDurationHistogram.record(executionTime, { query: queryName });
              
              // Set span attributes
              span.setAttribute("db.execution_time_seconds", executionTime);
              span.setStatus({ code: opentelemetry.SpanStatusCode.OK });
              
              return result;
            } catch (error) {
              span.setStatus({
                code: opentelemetry.SpanStatusCode.ERROR,
                message: error.message
              });
              span.recordException(error);
              throw error;
            } finally {
              span.end();
            }
          }
        );
      } catch (error) {
        // If OpenTelemetry fails, fall back to basic monitoring
        logger.warn(`OpenTelemetry monitoring failed: ${error.message}. Falling back to basic monitoring.`);
        const startTime = performance.now();
        try {
          const result = await queryFn.apply(this, args);
          const endTime = performance.now();
          const executionTime = (endTime - startTime) / 1000; // Convert to seconds
          logger.debug(`Query ${queryName} executed in ${executionTime.toFixed(6)} seconds`);
          return result;
        } catch (error) {
          const endTime = performance.now();
          const executionTime = (endTime - startTime) / 1000; // Convert to seconds
          logger.error(`Query ${queryName} failed after ${executionTime.toFixed(6)} seconds: ${error.message}`);
          throw error;
        }
      }
    }
    
    // For basic monitoring
    const startTime = performance.now();
    try {
      const result = await queryFn.apply(this, args);
      const endTime = performance.now();
      const executionTime = (endTime - startTime) / 1000; // Convert to seconds
      logger.debug(`Query ${queryName} executed in ${executionTime.toFixed(6)} seconds`);
      return result;
    } catch (error) {
      const endTime = performance.now();
      const executionTime = (endTime - startTime) / 1000; // Convert to seconds
      logger.error(`Query ${queryName} failed after ${executionTime.toFixed(6)} seconds: ${error.message}`);
      throw error;
    }
  };
}
"""

# Template for the logger configuration
LOGGER_CONFIG = """/**
 * Logger utility for database queries
 */
const logger = {
  level: 'info', // Default log level
  levels: {
    error: 0,
    warn: 1,
    info: 2,
    debug: 3
  },
  
  error: function(message) {
    if (this.levels[this.level] >= this.levels.error) {
      console.error(`[ERROR] ${message}`);
    }
  },
  
  warn: function(message) {
    if (this.levels[this.level] >= this.levels.warn) {
      console.warn(`[WARN] ${message}`);
    }
  },
  
  info: function(message) {
    if (this.levels[this.level] >= this.levels.info) {
      console.info(`[INFO] ${message}`);
    }
  },
  
  debug: function(message) {
    if (this.levels[this.level] >= this.levels.debug) {
      console.debug(`[DEBUG] ${message}`);
    }
  }
};

/**
 * Set the log level
 * @param {string} level - Log level (error, warn, info, debug)
 */
function setLogLevel(level) {
  if (logger.levels[level] !== undefined) {
    logger.level = level;
    logger.info(`Log level set to: ${level}`);
  } else {
    logger.warn(`Invalid log level: ${level}. Using default: info`);
  }
}
"""

# Template for the monitoring configuration
MONITORING_CONFIG = """// Monitoring configuration
let _monitoringMode = "none"; // none, basic, opentelemetry
let _openTelemetryConfigured = false;
let _tracer = null;
let _meter = null;
let _queryDurationHistogram = null;

/**
 * Configure performance monitoring for database queries
 * @param {string} mode - Monitoring mode: "none", "basic", or "opentelemetry"
 * @param {object} [opentelemetryConfig] - OpenTelemetry configuration
 */
function configureMonitoring(mode = "none", opentelemetryConfig = null) {
  // Validate mode
  if (!["none", "basic", "opentelemetry"].includes(mode)) {
    logger.warn(`Invalid monitoring mode: ${mode}. Using default: none`);
    mode = "none";
  }
  
  // Configure OpenTelemetry if requested
  if (mode === "opentelemetry" && opentelemetryConfig) {
    try {
      const opentelemetry = require("@opentelemetry/api");
      
      // Get tracer and meter from provided configuration
      _tracer = opentelemetryConfig.tracer || opentelemetry.trace.getTracer("db-queries");
      _meter = opentelemetryConfig.meter || opentelemetry.metrics.getMeter("db-queries");
      
      // Create metrics
      _queryDurationHistogram = _meter.createHistogram("db_query_duration", {
        description: "Duration of database queries in seconds",
        unit: "s",
      });
      
      _openTelemetryConfigured = true;
      logger.info("OpenTelemetry monitoring configured successfully");
    } catch (error) {
      logger.error(`Failed to configure OpenTelemetry: ${error.message}`);
      logger.info("Falling back to basic monitoring");
      mode = "basic";
    }
  }
  
  _monitoringMode = mode;
  
  logger.info(`Query performance monitoring mode set to: ${_monitoringMode}`);
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
  setLogLevel,
  processConditionalBlocks,
  cleanupSql,
  convertNamedParams,
  ensureConnection,
  configureMonitoring,
  monitorQueryPerformance,
  createTransaction
};
"""
