const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const compression = require('compression');
const rateLimit = require('express-rate-limit');
require('dotenv').config();

const { API_CONFIG, SECURITY_CONFIG } = require('./config/constants');
const { globalErrorHandler, notFoundHandler } = require('./middleware/errorHandler');
const { logger } = require('./utils/logger');

const toolRoutes = require('./routes/tools');
const healthRoutes = require('./routes/health');

const app = express();
const PORT = process.env.PORT || API_CONFIG.DEFAULT_PORT;

// Trust proxy for rate limiting
app.set('trust proxy', 1);

// Security middleware
app.use(helmet(SECURITY_CONFIG.HELMET_OPTIONS));

// Compression middleware
app.use(compression());

// Rate limiting
const limiter = rateLimit({
  windowMs: API_CONFIG.RATE_LIMIT_WINDOW,
  max: API_CONFIG.RATE_LIMIT_MAX,
  message: {
    error: 'Too many requests from this IP, please try again later',
    retryAfter: Math.ceil(API_CONFIG.RATE_LIMIT_WINDOW / 1000)
  },
  standardHeaders: true,
  legacyHeaders: false
});

app.use('/api/', limiter);

// CORS configuration
app.use(cors({
  origin: API_CONFIG.CORS_ORIGIN,
  credentials: true,
  optionsSuccessStatus: 200
}));

// Body parsing middleware
app.use(express.json({ limit: API_CONFIG.MAX_REQUEST_SIZE }));
app.use(express.urlencoded({ extended: true, limit: API_CONFIG.MAX_REQUEST_SIZE }));

// Request logging middleware
app.use((req, res, next) => {
  const start = Date.now();
  
  res.on('finish', () => {
    const duration = Date.now() - start;
    logger.info('HTTP Request', {
      method: req.method,
      url: req.url,
      statusCode: res.statusCode,
      duration,
      ip: req.ip,
      userAgent: req.get('User-Agent')
    });
  });
  
  next();
});

// API Routes
app.use('/api/health', healthRoutes);
app.use('/api/tools', toolRoutes);

// Tool proxy route - handles /tools/toolname/* requests
app.use('/tools/:toolId/*', async (req, res) => {
  const { toolId } = req.params;
  const toolPath = req.params[0] || '';
  
  try {
    const ToolManager = require('./services/ToolManager');
    const toolManager = new ToolManager();
    
    // Get tool configuration
    const tool = await toolManager.getToolConfig(toolId);
    if (!tool) {
      return res.status(404).json({ 
        error: 'Tool not found',
        code: 'TOOL_NOT_FOUND'
      });
    }
    
    // Check if tool is running
    const status = await toolManager.getToolStatus(toolId);
    if (status.status !== 'running') {
      return res.status(503).json({ 
        error: 'Tool not running', 
        status: status.status,
        code: 'TOOL_NOT_RUNNING'
      });
    }
    
    // Proxy request to tool container
    const toolUrl = `http://machete-tool-${toolId}:${tool.port}/${toolPath}`;
    const { createProxyMiddleware } = require('http-proxy-middleware');
    
    const proxy = createProxyMiddleware({
      target: `http://machete-tool-${toolId}:${tool.port}`,
      changeOrigin: true,
      pathRewrite: {
        [`^/tools/${toolId}`]: ''
      },
      onError: (err, req, res) => {
        logger.error(`Proxy error for tool ${toolId}`, { error: err.message });
        if (!res.headersSent) {
          res.status(503).json({ 
            error: 'Tool service unavailable',
            code: 'PROXY_ERROR'
          });
        }
      },
      timeout: API_CONFIG.REQUEST_TIMEOUT
    });
    
    proxy(req, res);
    
  } catch (error) {
    logger.error(`Error proxying to tool ${toolId}`, { error: error.message });
    res.status(500).json({ 
      error: 'Internal server error',
      code: 'PROXY_INTERNAL_ERROR'
    });
  }
});

// 404 handler - must be before error handler
app.use('*', notFoundHandler);

// Global error handling middleware - must be last
app.use(globalErrorHandler);

// Start server
app.listen(PORT, () => {
  logger.info(`MACHETE API server started`, {
    port: PORT,
    environment: process.env.NODE_ENV || 'development',
    timestamp: new Date().toISOString()
  });
});

// Graceful shutdown
const shutdown = (signal) => {
  logger.info(`Received ${signal}, shutting down gracefully`);
  process.exit(0);
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
