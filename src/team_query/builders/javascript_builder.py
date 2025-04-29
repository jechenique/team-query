"""
JavaScript query builder generator for team-query.
"""
from typing import List

from team_query.models import Query


class JavaScriptQueryBuilder:
    """Generator for JavaScript query builder classes."""

    @classmethod
    def generate_builder_class(cls, query: Query) -> List[str]:
        """
        Generate JavaScript code for a query builder class.

        Args:
            query: Query object

        Returns:
            List of JavaScript code lines
        """
        function_name = query.name

        lines = []

        # Add class definition
        lines.append(f"class {function_name}Builder {{")

        # Add constructor
        lines.append("  constructor(db, params = {}) {")
        lines.append("    this.db = db;")
        lines.append("    this.params = { ...params };")
        lines.append("    this.whereConditions = {};")
        lines.append("    this.orderByClause = null;")
        lines.append("    this.limitValue = null;")
        lines.append("    this.offsetValue = null;")
        lines.append("    this.executed = false;")
        lines.append("    this.sqlTemplate = `" + query.sql + "`;")
        lines.append("  }")

        # Add where method
        lines.append("  where(conditions) {")
        lines.append(
            "    this.whereConditions = { ...this.whereConditions, ...conditions };"
        )
        lines.append("    return this;")
        lines.append("  }")

        # Add orderBy method
        lines.append("  orderBy(column, direction = 'asc') {")
        lines.append("    if (!['asc', 'desc', 'ASC', 'DESC'].includes(direction)) {")
        lines.append("      throw new Error(\"Direction must be 'asc' or 'desc'\");")
        lines.append("    }")
        lines.append("    this.orderByClause = `${column} ${direction.toUpperCase()}`;")
        lines.append("    return this;")
        lines.append("  }")

        # Add limit method
        lines.append("  limit(limit) {")
        lines.append("    if (!Number.isInteger(limit) || limit < 0) {")
        lines.append("      throw new Error('Limit must be a non-negative integer');")
        lines.append("    }")
        lines.append("    this.limitValue = limit;")
        lines.append("    return this;")
        lines.append("  }")

        # Add offset method
        lines.append("  offset(offset) {")
        lines.append("    if (!Number.isInteger(offset) || offset < 0) {")
        lines.append("      throw new Error('Offset must be a non-negative integer');")
        lines.append("    }")
        lines.append("    this.offsetValue = offset;")
        lines.append("    return this;")
        lines.append("  }")

        # Add _buildDynamicSql method
        lines.append("  _buildDynamicSql() {")
        lines.append("    // Start with the base SQL")
        lines.append("    let sql = this.sqlTemplate;")

        # Determine which parameters are provided
        lines.append("    // Determine which parameters are provided")
        lines.append("    const providedParams = new Set();")
        lines.append("    for (const [key, value] of Object.entries(this.params)) {")
        lines.append("      if (value !== undefined && value !== null) {")
        lines.append("        providedParams.add(key);")
        lines.append("      }")
        lines.append("    }")

        # Add WHERE conditions
        lines.append("    // Add WHERE conditions")
        lines.append("    if (Object.keys(this.whereConditions).length > 0) {")
        lines.append("      if (!sql.toUpperCase().includes('WHERE')) {")
        lines.append("        sql += ' WHERE ';")
        lines.append("      } else {")
        lines.append("        sql += ' AND ';")
        lines.append("      }")
        lines.append("      const conditions = [];")
        lines.append(
            "      for (const [field, value] of Object.entries(this.whereConditions)) {"
        )
        lines.append("        conditions.push(`${field} = :${field}`);")
        lines.append("        this.params[field] = value;")
        lines.append("        providedParams.add(field);")
        lines.append("      }")
        lines.append("      sql += conditions.join(' AND ');")
        lines.append("    }")

        # Add ORDER BY clause
        lines.append("    // Add ORDER BY clause")
        lines.append("    if (this.orderByClause) {")
        lines.append("      if (!sql.toUpperCase().includes('ORDER BY')) {")
        lines.append("        sql += ` ORDER BY ${this.orderByClause}`;")
        lines.append("      } else {")
        lines.append("        // Replace existing ORDER BY")
        lines.append(
            "        sql = sql.replace(/ORDER BY.*?(?=(LIMIT|OFFSET|$))/i, `ORDER BY ${this.orderByClause} `);"
        )
        lines.append("      }")
        lines.append("    }")

        # Add LIMIT clause
        lines.append("    // Add LIMIT clause")
        lines.append("    if (this.limitValue !== null) {")
        lines.append("      const limitParam = this._getUniqueParamName('limit');")
        lines.append("      if (!sql.toUpperCase().includes('LIMIT')) {")
        lines.append("        sql += ` LIMIT :${limitParam}`;")
        lines.append("      } else {")
        lines.append("        // Replace existing LIMIT")
        lines.append(
            "        sql = sql.replace(/LIMIT\\s+:?\\w+/i, `LIMIT :${limitParam}`);"
        )
        lines.append("      }")
        lines.append("      this.params[limitParam] = this.limitValue;")
        lines.append("      providedParams.add(limitParam);")
        lines.append("    }")

        # Add OFFSET clause
        lines.append("    // Add OFFSET clause")
        lines.append("    if (this.offsetValue !== null) {")
        lines.append("      const offsetParam = this._getUniqueParamName('offset');")
        lines.append("      if (!sql.toUpperCase().includes('OFFSET')) {")
        lines.append("        sql += ` OFFSET :${offsetParam}`;")
        lines.append("      } else {")
        lines.append("        // Replace existing OFFSET")
        lines.append(
            "        sql = sql.replace(/OFFSET\\s+:?\\w+/i, `OFFSET :${offsetParam}`);"
        )
        lines.append("      }")
        lines.append("      this.params[offsetParam] = this.offsetValue;")
        lines.append("      providedParams.add(offsetParam);")
        lines.append("    }")

        # Process conditional blocks
        lines.append("    // Process conditional blocks")
        lines.append("    const blockPattern = /--\\s*{\\s*(\\w+)(.*?)--\\s*}/gs;")
        lines.append("    let match;")
        lines.append("    while ((match = blockPattern.exec(sql)) !== null) {")
        lines.append("      const [fullBlock, paramName, blockContent] = match;")
        lines.append("      if (providedParams.has(paramName)) {")
        lines.append(
            "        // Parameter is provided, keep the content but remove the markers"
        )
        lines.append("        sql = sql.replace(fullBlock, blockContent);")
        lines.append("      } else {")
        lines.append("        // Parameter is not provided, remove the entire block")
        lines.append("        sql = sql.replace(fullBlock, '');")
        lines.append("      }")
        lines.append("    }")

        # Clean up SQL
        lines.append("    // Clean up the SQL")
        lines.append("    // Handle WHERE clauses intelligently")
        lines.append("    sql = sql.replace(/\\s+/g, ' ');")
        lines.append(
            "    const wherePattern = /(WHERE\\s+)(.*?)(\\s+(?:ORDER|GROUP|LIMIT|HAVING|UNION|INTERSECT|EXCEPT|$))/i;"
        )
        lines.append("    const whereMatch = sql.match(wherePattern);")
        lines.append("    if (whereMatch) {")
        lines.append("      const whereKeyword = whereMatch[1];")
        lines.append("      let whereConditions = whereMatch[2];")
        lines.append("      const whereEnd = whereMatch[3];")
        lines.append("      // Remove any '1=1' or 'TRUE' placeholder")
        lines.append(
            "      whereConditions = whereConditions.replace(/^1=1\\s+AND\\s+/i, '');"
        )
        lines.append(
            "      whereConditions = whereConditions.replace(/^TRUE\\s+AND\\s+/i, '');"
        )
        lines.append(
            "      whereConditions = whereConditions.replace(/^1=1$/i, 'TRUE');"
        )
        lines.append("      // Check if there are any real conditions left")
        lines.append(
            "      if (whereConditions.trim() && whereConditions.toUpperCase() !== 'TRUE') {"
        )
        lines.append("        // Replace the WHERE clause with the cleaned up version")
        lines.append(
            "        sql = sql.replace(whereMatch[0], `${whereKeyword}${whereConditions}${whereEnd}`);"
        )
        lines.append("      } else {")
        lines.append(
            "        // No conditions left, remove the WHERE clause entirely or replace with WHERE TRUE"
        )
        lines.append("        if (/(JOIN|FROM)\\s+.*?\\s+WHERE/i.test(sql)) {")
        lines.append("          // There's a FROM or JOIN, so we need a WHERE clause")
        lines.append(
            "          sql = sql.replace(whereMatch[0], `${whereKeyword}TRUE${whereEnd}`);"
        )
        lines.append("        } else {")
        lines.append("          // No FROM or JOIN, so we can remove the WHERE clause")
        lines.append(
            "          sql = sql.replace(whereMatch[0], whereEnd.trimStart());"
        )
        lines.append("        }")
        lines.append("      }")
        lines.append("    }")
        lines.append("    // Handle AND/OR at the beginning of conditions")
        lines.append("    sql = sql.replace(/WHERE\\s+AND\\s+/i, 'WHERE ');")
        lines.append("    sql = sql.replace(/WHERE\\s+OR\\s+/i, 'WHERE ');")
        lines.append("    // Handle JOIN conditions")
        lines.append(
            "    sql = sql.replace(/(JOIN\\s+\\w+(?:\\s+\\w+)?\\s+ON\\s+.*?)\\s+AND\\s+$/i, '$1');"
        )

        # Extract parameters
        lines.append("    // Extract parameters from the processed SQL")
        lines.append("    const paramPattern = /:([a-zA-Z_][a-zA-Z0-9_]*)/g;")
        lines.append("    const usedParams = [];")
        lines.append("    while ((match = paramPattern.exec(sql)) !== null) {")
        lines.append("      usedParams.push(match[1]);")
        lines.append("    }")
        lines.append("    // Build values array with only the used parameters")
        lines.append("    const values = [];")
        lines.append("    let paramIndex = 1;")
        lines.append("    for (const paramName of usedParams) {")
        lines.append("      values.push(this.params[paramName]);")
        lines.append("      sql = sql.replace(`:${paramName}`, `$${paramIndex++}`);")
        lines.append("    }")
        lines.append("    return { sql, values };")
        lines.append("  }")

        # Add _getUniqueParamName method
        lines.append("  _getUniqueParamName(baseName) {")
        lines.append("    if (this.params[baseName] === undefined) {")
        lines.append("      return baseName;")
        lines.append("    }")
        lines.append("    let i = 1;")
        lines.append("    while (this.params[`${baseName}_${i}`] !== undefined) {")
        lines.append("      i++;")
        lines.append("    }")
        lines.append("    return `${baseName}_${i}`;")
        lines.append("  }")

        # Add execute method
        lines.append("  async execute() {")
        lines.append("    if (this.executed) {")
        lines.append("      throw new Error('Query already executed');")
        lines.append("    }")
        lines.append("    this.executed = true;")
        lines.append("    const { sql, values } = this._buildDynamicSql();")
        lines.append("    try {")
        lines.append("      const result = await this.db.query(sql, values);")

        # Handle different query types
        if query.query_type and query.query_type.value == "select":
            lines.append("      return result.rows;")
        elif query.query_type and query.query_type.value in [
            "insert",
            "update",
            "delete",
        ]:
            lines.append("      if (sql.toUpperCase().includes('RETURNING')) {")
            lines.append("        return result.rows;")
            lines.append("      }")
            lines.append("      return result.rowCount;")
        else:
            lines.append("      return result.rows;")

        lines.append("    } catch (error) {")
        lines.append("      console.error(`Error executing query ${sql}:`, error);")
        lines.append("      throw error;")
        lines.append("    }")
        lines.append("  }")

        # Close class definition
        lines.append("}")

        return lines
