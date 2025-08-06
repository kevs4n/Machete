const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

const app = express();
const PORT = process.env.PORT || 8080;

// Security and CORS
app.use(helmet());
app.use(cors());
app.use(express.json());

// Health check endpoint (required for MACHETE)
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy',
    timestamp: new Date().toISOString(),
    uptime: process.uptime(),
    version: process.env.npm_package_version || '1.0.0'
  });
});

// Tool info endpoint (recommended)
app.get('/info', (req, res) => {
  res.json({
    name: 'My Awesome Tool',
    version: '1.0.0',
    description: 'A template tool for MACHETE',
    endpoints: [
      { path: '/health', method: 'GET', description: 'Health check' },
      { path: '/info', method: 'GET', description: 'Tool information' },
      { path: '/api/status', method: 'GET', description: 'Tool status' }
    ]
  });
});

// Example API endpoint
app.get('/api/status', (req, res) => {
  res.json({
    status: 'running',
    environment: process.env.NODE_ENV || 'development',
    memory: process.memoryUsage(),
    pid: process.pid
  });
});

// Serve static files (if any)
app.use(express.static('public'));

// Main dashboard route
app.get('/', (req, res) => {
  res.send(`
    <!DOCTYPE html>
    <html>
    <head>
        <title>My Awesome Tool</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #333; border-bottom: 2px solid #ff6b35; padding-bottom: 10px; }
            .status { background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0; }
            .endpoint { background: #f8f9fa; padding: 10px; margin: 10px 0; border-left: 4px solid #ff6b35; }
            code { background: #f1f1f1; padding: 2px 6px; border-radius: 3px; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔧 My Awesome Tool</h1>
            <div class="status">
                <strong>Status:</strong> Running successfully in MACHETE!
            </div>
            
            <h2>Available Endpoints</h2>
            <div class="endpoint">
                <strong>GET</strong> <code>/health</code> - Health check
            </div>
            <div class="endpoint">
                <strong>GET</strong> <code>/info</code> - Tool information
            </div>
            <div class="endpoint">
                <strong>GET</strong> <code>/api/status</code> - Detailed status
            </div>
            
            <h2>Getting Started</h2>
            <p>This is a template tool. Replace this content with your tool's interface!</p>
            
            <h2>Development</h2>
            <ul>
                <li>Edit <code>src/server.js</code> to add your functionality</li>
                <li>Update <code>machete.yml</code> with your tool configuration</li>
                <li>Add your UI to <code>public/</code> directory</li>
                <li>Test with <code>docker build -t my-tool . && docker run -p 8080:8080 my-tool</code></li>
            </ul>
        </div>
    </body>
    </html>
  `);
});

// Error handling
app.use((err, req, res, next) => {
  console.error(err.stack);
  res.status(500).json({ 
    error: 'Something went wrong!',
    message: process.env.NODE_ENV === 'development' ? err.message : 'Internal server error'
  });
});

// Start server
app.listen(PORT, '0.0.0.0', () => {
  console.log(`🔧 Tool server running on port ${PORT}`);
  console.log(`📊 Health check: http://localhost:${PORT}/health`);
  console.log(`ℹ️  Tool info: http://localhost:${PORT}/info`);
});

// Graceful shutdown
process.on('SIGTERM', () => {
  console.log('📴 Shutting down gracefully...');
  process.exit(0);
});

process.on('SIGINT', () => {
  console.log('📴 Shutting down gracefully...');
  process.exit(0);
});
