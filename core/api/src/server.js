const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');
require('dotenv').config();

const toolRoutes = require('./routes/tools');
const healthRoutes = require('./routes/health');

const app = express();
const PORT = process.env.PORT || 3001;

// Middleware
app.use(helmet());
app.use(cors());
app.use(morgan('combined'));
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
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
      return res.status(404).json({ error: 'Tool not found' });
    }
    
    // Check if tool is running
    const status = await toolManager.getToolStatus(toolId);
    if (status.status !== 'running') {
      return res.status(503).json({ error: 'Tool not running', status: status.status });
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
        console.error(`Proxy error for tool ${toolId}:`, err.message);
        res.status(503).json({ error: 'Tool service unavailable' });
      }
    });
    
    proxy(req, res);
    
  } catch (error) {
    console.error(`Error proxying to tool ${toolId}:`, error);
    res.status(500).json({ error: 'Internal server error' });
  }
});

// Error handling middleware
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ error: 'Something went wrong!' });
});

// 404 handler
app.use('*', (req, res) => {
  res.status(404).json({ error: 'Route not found' });
});

app.listen(PORT, () => {
  console.log(`MACHETE API server running on port ${PORT}`);
});
