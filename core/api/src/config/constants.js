/**
 * @fileoverview Constants and configuration values for MACHETE platform
 * @author MACHETE Team
 * @version 1.0.0
 */

// Tool Configuration
const TOOL_CONFIG = {
  DEFAULT_PORT: 8080,
  DEFAULT_HEALTH_CHECK: '/health',
  DEFAULT_CATEGORY: 'other',
  DEFAULT_ICON: '🔧',
  DEFAULT_COLOR: '#ff6b35',
  DEFAULT_VERSION: '1.0.0',
  MAX_TOOL_NAME_LENGTH: 50,
  MAX_DESCRIPTION_LENGTH: 500,
  ALLOWED_CATEGORIES: ['automation', 'devops', 'monitoring', 'testing', 'deployment', 'other']
};

// Docker Configuration
const DOCKER_CONFIG = {
  DEFAULT_BUILD_CONTEXT: '.',
  DEFAULT_DOCKERFILE: 'Dockerfile',
  NETWORK_NAME: 'machete_machete-network',
  CONTAINER_PREFIX: 'machete-tool-',
  IMAGE_PREFIX: 'machete-tool-',
  DEFAULT_RESTART_POLICY: 'unless-stopped',
  HEALTH_CHECK_INTERVAL: '30s',
  HEALTH_CHECK_TIMEOUT: '10s',
  HEALTH_CHECK_RETRIES: 3
};

// API Configuration
const API_CONFIG = {
  DEFAULT_PORT: 3001,
  RATE_LIMIT_WINDOW: 15 * 60 * 1000, // 15 minutes
  RATE_LIMIT_MAX: 100, // requests per window
  REQUEST_TIMEOUT: 30000, // 30 seconds
  MAX_REQUEST_SIZE: '10mb',
  CORS_ORIGIN: process.env.CORS_ORIGIN || '*'
};

// File System Configuration
const FS_CONFIG = {
  TOOLS_DIR: process.env.TOOLS_DIR || '/app/tools',
  DATA_DIR: process.env.DATA_DIR || '/app/data',
  LOGS_DIR: process.env.LOGS_DIR || '/app/logs',
  TOOLS_CONFIG_FILE: 'tools.json',
  MACHETE_CONFIG_FILE: 'machete.yml',
  LEGACY_CONFIG_FILE: 'tool.json',
  REQUIRED_FILES: ['Dockerfile', 'README.md']
};

// Git Configuration
const GIT_CONFIG = {
  CLONE_TIMEOUT: 300000, // 5 minutes
  CLONE_DEPTH: 1, // shallow clone
  DEFAULT_BRANCH: 'main'
};

// Security Configuration
const SECURITY_CONFIG = {
  HELMET_OPTIONS: {
    contentSecurityPolicy: {
      directives: {
        defaultSrc: ["'self'"],
        styleSrc: ["'self'", "'unsafe-inline'"],
        scriptSrc: ["'self'"],
        imgSrc: ["'self'", "data:", "https:"],
        connectSrc: ["'self'"],
        fontSrc: ["'self'"],
        objectSrc: ["'none'"],
        mediaSrc: ["'self'"],
        frameSrc: ["'none'"]
      }
    },
    crossOriginEmbedderPolicy: false
  },
  JWT_EXPIRY: '24h',
  BCRYPT_ROUNDS: 12
};

// Error Messages
const ERROR_MESSAGES = {
  TOOL_NOT_FOUND: 'Tool not found',
  TOOL_ALREADY_EXISTS: 'Tool already exists',
  TOOL_NOT_RUNNING: 'Tool is not running',
  TOOL_INSTALLATION_FAILED: 'Tool installation failed',
  INVALID_TOOL_CONFIG: 'Invalid tool configuration',
  GIT_CLONE_FAILED: 'Failed to clone repository',
  DOCKER_BUILD_FAILED: 'Docker build failed',
  CONTAINER_START_FAILED: 'Failed to start container',
  CONTAINER_STOP_FAILED: 'Failed to stop container',
  INVALID_REQUEST: 'Invalid request data',
  UNAUTHORIZED: 'Unauthorized access',
  FORBIDDEN: 'Access forbidden',
  RATE_LIMITED: 'Too many requests',
  INTERNAL_ERROR: 'Internal server error'
};

// Success Messages
const SUCCESS_MESSAGES = {
  TOOL_INSTALLED: 'Tool installed successfully',
  TOOL_STARTED: 'Tool started successfully',
  TOOL_STOPPED: 'Tool stopped successfully',
  TOOL_UNINSTALLED: 'Tool uninstalled successfully',
  HEALTH_CHECK_PASSED: 'Health check passed'
};

// Validation Schemas (Joi patterns)
const VALIDATION_PATTERNS = {
  TOOL_ID: /^[a-z0-9-]+$/,
  GIT_URL: /^https:\/\/github\.com\/[\w\-\.]+\/[\w\-\.]+(?:\.git)?$/,
  TOOL_NAME: /^[a-zA-Z0-9\s\-_\.]+$/,
  PORT: /^[1-9]\d{3,4}$/,
  VERSION: /^\d+\.\d+\.\d+$/
};

// Status Constants
const STATUS = {
  RUNNING: 'running',
  STOPPED: 'stopped',
  INSTALLING: 'installing',
  ERROR: 'error',
  BUILDING: 'building',
  STARTING: 'starting',
  STOPPING: 'stopping'
};

// Log Levels
const LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug'
};

module.exports = {
  TOOL_CONFIG,
  DOCKER_CONFIG,
  API_CONFIG,
  FS_CONFIG,
  GIT_CONFIG,
  SECURITY_CONFIG,
  ERROR_MESSAGES,
  SUCCESS_MESSAGES,
  VALIDATION_PATTERNS,
  STATUS,
  LOG_LEVELS
};
