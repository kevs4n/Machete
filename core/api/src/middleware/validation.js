/**
 * @fileoverview Input validation middleware using Joi
 * @author MACHETE Team
 * @version 1.0.0
 */

const Joi = require('joi');
const { ERROR_MESSAGES, VALIDATION_PATTERNS } = require('../config/constants');

/**
 * Joi schema for tool installation
 */
const toolInstallationSchema = Joi.object({
  name: Joi.string()
    .pattern(VALIDATION_PATTERNS.TOOL_NAME)
    .min(1)
    .max(50)
    .required()
    .messages({
      'string.pattern.base': 'Tool name can only contain letters, numbers, spaces, hyphens, underscores, and dots',
      'string.min': 'Tool name must be at least 1 character long',
      'string.max': 'Tool name cannot exceed 50 characters',
      'any.required': 'Tool name is required'
    }),
  
  gitUrl: Joi.string()
    .pattern(VALIDATION_PATTERNS.GIT_URL)
    .required()
    .messages({
      'string.pattern.base': 'Git URL must be a valid GitHub HTTPS URL',
      'any.required': 'Git URL is required'
    }),
  
  description: Joi.string()
    .max(500)
    .optional()
    .messages({
      'string.max': 'Description cannot exceed 500 characters'
    }),
  
  credentials: Joi.object({
    username: Joi.string().optional(),
    token: Joi.string().optional()
  }).optional()
});

/**
 * Joi schema for tool operations (start/stop/uninstall)
 */
const toolOperationSchema = Joi.object({
  toolId: Joi.string()
    .pattern(VALIDATION_PATTERNS.TOOL_ID)
    .required()
    .messages({
      'string.pattern.base': 'Tool ID can only contain lowercase letters, numbers, and hyphens',
      'any.required': 'Tool ID is required'
    })
});

/**
 * Middleware to validate request body against a Joi schema
 * @param {Joi.Schema} schema - Joi validation schema
 * @returns {Function} Express middleware function
 */
const validateBody = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.body, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));

      return res.status(400).json({
        error: ERROR_MESSAGES.INVALID_REQUEST,
        details: errors
      });
    }

    // Replace req.body with validated and sanitized data
    req.body = value;
    next();
  };
};

/**
 * Middleware to validate request parameters against a Joi schema
 * @param {Joi.Schema} schema - Joi validation schema
 * @returns {Function} Express middleware function
 */
const validateParams = (schema) => {
  return (req, res, next) => {
    const { error, value } = schema.validate(req.params, {
      abortEarly: false,
      stripUnknown: true
    });

    if (error) {
      const errors = error.details.map(detail => ({
        field: detail.path.join('.'),
        message: detail.message
      }));

      return res.status(400).json({
        error: ERROR_MESSAGES.INVALID_REQUEST,
        details: errors
      });
    }

    // Replace req.params with validated data
    req.params = value;
    next();
  };
};

/**
 * Sanitize tool name to create a valid tool ID
 * @param {string} name - Tool name
 * @returns {string} Sanitized tool ID
 */
const sanitizeToolId = (name) => {
  return name
    .toLowerCase()
    .replace(/\s+/g, '-')
    .replace(/[^a-z0-9-]/g, '')
    .replace(/-+/g, '-')
    .replace(/^-+|-+$/g, '');
};

/**
 * Validate and sanitize git URL
 * @param {string} gitUrl - Git repository URL
 * @returns {string} Sanitized git URL
 */
const sanitizeGitUrl = (gitUrl) => {
  // Remove .git suffix if present
  return gitUrl.replace(/\.git$/, '');
};

module.exports = {
  toolInstallationSchema,
  toolOperationSchema,
  validateBody,
  validateParams,
  sanitizeToolId,
  sanitizeGitUrl
};
