/**
 * @fileoverview Structured logging configuration using Winston
 * @author MACHETE Team
 * @version 1.0.0
 */

const winston = require('winston');
const path = require('path');
const { FS_CONFIG, LOG_LEVELS } = require('../config/constants');

// Ensure logs directory exists
const fs = require('fs-extra');
fs.ensureDirSync(FS_CONFIG.LOGS_DIR);

/**
 * Custom log format for production
 */
const productionFormat = winston.format.combine(
  winston.format.timestamp(),
  winston.format.errors({ stack: true }),
  winston.format.json()
);

/**
 * Custom log format for development
 */
const developmentFormat = winston.format.combine(
  winston.format.timestamp({ format: 'YYYY-MM-DD HH:mm:ss' }),
  winston.format.errors({ stack: true }),
  winston.format.colorize(),
  winston.format.printf(({ level, message, timestamp, stack, ...meta }) => {
    let log = `${timestamp} [${level}]: ${message}`;
    if (stack) log += `\n${stack}`;
    if (Object.keys(meta).length > 0) log += `\n${JSON.stringify(meta, null, 2)}`;
    return log;
  })
);

/**
 * Create Winston logger instance
 */
const logger = winston.createLogger({
  level: process.env.LOG_LEVEL || LOG_LEVELS.INFO,
  format: process.env.NODE_ENV === 'production' ? productionFormat : developmentFormat,
  defaultMeta: { service: 'machete-api' },
  transports: [
    // Write all logs to combined.log
    new winston.transports.File({
      filename: path.join(FS_CONFIG.LOGS_DIR, 'combined.log'),
      maxsize: 10485760, // 10MB
      maxFiles: 5
    }),
    
    // Write error logs to error.log
    new winston.transports.File({
      filename: path.join(FS_CONFIG.LOGS_DIR, 'error.log'),
      level: LOG_LEVELS.ERROR,
      maxsize: 10485760, // 10MB
      maxFiles: 5
    })
  ]
});

// Add console transport for development
if (process.env.NODE_ENV !== 'production') {
  logger.add(new winston.transports.Console({
    format: developmentFormat
  }));
}

/**
 * Create HTTP request logger middleware
 */
const createHttpLogger = () => {
  return winston.format.combine(
    winston.format.timestamp(),
    winston.format.printf(({ timestamp, message }) => {
      return `${timestamp} [HTTP]: ${message}`;
    })
  );
};

/**
 * Log tool operations
 * @param {string} operation - Operation type
 * @param {string} toolId - Tool identifier
 * @param {Object} metadata - Additional metadata
 */
const logToolOperation = (operation, toolId, metadata = {}) => {
  logger.info(`Tool ${operation}`, {
    operation,
    toolId,
    ...metadata,
    category: 'tool-operation'
  });
};

/**
 * Log Docker operations
 * @param {string} operation - Docker operation
 * @param {string} containerName - Container name
 * @param {Object} metadata - Additional metadata
 */
const logDockerOperation = (operation, containerName, metadata = {}) => {
  logger.info(`Docker ${operation}`, {
    operation,
    containerName,
    ...metadata,
    category: 'docker-operation'
  });
};

/**
 * Log Git operations
 * @param {string} operation - Git operation
 * @param {string} repository - Repository URL
 * @param {Object} metadata - Additional metadata
 */
const logGitOperation = (operation, repository, metadata = {}) => {
  logger.info(`Git ${operation}`, {
    operation,
    repository: repository.replace(/\/\/.*@/, '//***@'), // Hide credentials
    ...metadata,
    category: 'git-operation'
  });
};

/**
 * Log API requests
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {number} responseTime - Response time in milliseconds
 */
const logApiRequest = (req, res, responseTime) => {
  const { method, url, ip } = req;
  const { statusCode } = res;
  
  logger.info('API Request', {
    method,
    url,
    statusCode,
    responseTime,
    ip,
    userAgent: req.get('User-Agent'),
    category: 'api-request'
  });
};

/**
 * Log security events
 * @param {string} event - Security event type
 * @param {Object} details - Event details
 */
const logSecurityEvent = (event, details = {}) => {
  logger.warn(`Security Event: ${event}`, {
    event,
    ...details,
    category: 'security'
  });
};

module.exports = {
  logger,
  createHttpLogger,
  logToolOperation,
  logDockerOperation,
  logGitOperation,
  logApiRequest,
  logSecurityEvent
};
