/**
 * @fileoverview Centralized error handling middleware
 * @author MACHETE Team
 * @version 1.0.0
 */

const { ERROR_MESSAGES, LOG_LEVELS } = require('../config/constants');

/**
 * Custom error class for application-specific errors
 */
class AppError extends Error {
  constructor(message, statusCode = 500, code = null) {
    super(message);
    this.statusCode = statusCode;
    this.code = code;
    this.isOperational = true;
    
    Error.captureStackTrace(this, this.constructor);
  }
}

/**
 * Development error response with stack trace
 * @param {Error} err - Error object
 * @param {Object} res - Express response object
 */
const sendErrorDev = (err, res) => {
  res.status(err.statusCode).json({
    status: 'error',
    error: err,
    message: err.message,
    stack: err.stack
  });
};

/**
 * Production error response without sensitive information
 * @param {Error} err - Error object
 * @param {Object} res - Express response object
 */
const sendErrorProd = (err, res) => {
  // Operational, trusted error: send message to client
  if (err.isOperational) {
    res.status(err.statusCode).json({
      status: 'error',
      message: err.message,
      code: err.code
    });
  } else {
    // Programming or other unknown error: don't leak error details
    console.error('ERROR 💥', err);
    
    res.status(500).json({
      status: 'error',
      message: ERROR_MESSAGES.INTERNAL_ERROR
    });
  }
};

/**
 * Handle Docker-related errors
 * @param {Error} err - Docker error
 * @returns {AppError} Formatted application error
 */
const handleDockerError = (err) => {
  let message = ERROR_MESSAGES.INTERNAL_ERROR;
  let statusCode = 500;

  if (err.statusCode === 404) {
    message = 'Docker container not found';
    statusCode = 404;
  } else if (err.statusCode === 409) {
    message = 'Docker container already exists or is in use';
    statusCode = 409;
  } else if (err.message.includes('Cannot connect to the Docker daemon')) {
    message = 'Docker service is not available';
    statusCode = 503;
  }

  return new AppError(message, statusCode, 'DOCKER_ERROR');
};

/**
 * Handle Git-related errors
 * @param {Error} err - Git error
 * @returns {AppError} Formatted application error
 */
const handleGitError = (err) => {
  let message = ERROR_MESSAGES.GIT_CLONE_FAILED;
  let statusCode = 400;

  if (err.message.includes('not found') || err.message.includes('404')) {
    message = 'Git repository not found or access denied';
    statusCode = 404;
  } else if (err.message.includes('authentication') || err.message.includes('401')) {
    message = 'Git authentication failed';
    statusCode = 401;
  } else if (err.message.includes('timeout')) {
    message = 'Git operation timed out';
    statusCode = 408;
  }

  return new AppError(message, statusCode, 'GIT_ERROR');
};

/**
 * Handle file system errors
 * @param {Error} err - File system error
 * @returns {AppError} Formatted application error
 */
const handleFSError = (err) => {
  let message = ERROR_MESSAGES.INTERNAL_ERROR;
  let statusCode = 500;

  if (err.code === 'ENOENT') {
    message = 'Required file or directory not found';
    statusCode = 404;
  } else if (err.code === 'EACCES') {
    message = 'Permission denied';
    statusCode = 403;
  } else if (err.code === 'ENOSPC') {
    message = 'Insufficient disk space';
    statusCode = 507;
  }

  return new AppError(message, statusCode, 'FS_ERROR');
};

/**
 * Handle validation errors
 * @param {Error} err - Validation error
 * @returns {AppError} Formatted application error
 */
const handleValidationError = (err) => {
  const message = err.details 
    ? err.details.map(detail => detail.message).join('. ')
    : ERROR_MESSAGES.INVALID_REQUEST;
  
  return new AppError(message, 400, 'VALIDATION_ERROR');
};

/**
 * Global error handling middleware
 * @param {Error} err - Error object
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
const globalErrorHandler = (err, req, res, next) => {
  err.statusCode = err.statusCode || 500;
  err.status = err.status || 'error';

  if (process.env.NODE_ENV === 'development') {
    sendErrorDev(err, res);
  } else {
    let error = { ...err };
    error.message = err.message;

    // Handle different types of errors
    if (err.name === 'ValidationError') error = handleValidationError(error);
    if (err.name === 'DockerodeError' || err.message.includes('docker')) error = handleDockerError(error);
    if (err.message.includes('git') || err.name === 'GitError') error = handleGitError(error);
    if (err.code && err.code.startsWith('E')) error = handleFSError(error);

    sendErrorProd(error, res);
  }
};

/**
 * Middleware to catch async errors
 * @param {Function} fn - Async function to wrap
 * @returns {Function} Express middleware function
 */
const catchAsync = (fn) => {
  return (req, res, next) => {
    fn(req, res, next).catch(next);
  };
};

/**
 * Middleware to handle 404 errors
 * @param {Object} req - Express request object
 * @param {Object} res - Express response object
 * @param {Function} next - Express next function
 */
const notFoundHandler = (req, res, next) => {
  const err = new AppError(`Route ${req.originalUrl} not found`, 404, 'ROUTE_NOT_FOUND');
  next(err);
};

module.exports = {
  AppError,
  globalErrorHandler,
  catchAsync,
  notFoundHandler
};
