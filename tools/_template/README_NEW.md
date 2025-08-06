# MACHETE Tool Template

This template provides the basic structure for creating tools that can be installed and managed by the MACHETE platform.

## Quick Start

1. **Clone this template**:
   ```bash
   git clone <this-repo> my-awesome-tool
   cd my-awesome-tool
   ```

2. **Customize the configuration**:
   - Edit `machete.yml` with your tool details
   - Update `package.json` with your dependencies
   - Modify `Dockerfile` for your runtime needs

3. **Develop your tool**:
   - Add your source code to `src/`
   - Implement the required health check endpoint
   - Test locally with Docker

4. **Install in MACHETE**:
   - Push to Git repository
   - Use MACHETE's "Install Tool" feature
   - Enter your repository URL

## Required Files

### `machete.yml` - Tool Configuration
The main configuration file that tells MACHETE how to install and run your tool.

### `Dockerfile` - Container Definition
Defines how to build your tool's container image.

### `package.json` - Dependencies (Node.js tools)
Standard Node.js package configuration.

### `README.md` - Documentation
This file - provide clear documentation for your tool.

## Tool Structure

```
your-tool/
├── machete.yml          # MACHETE configuration
├── Dockerfile           # Container definition
├── package.json         # Node.js dependencies
├── README.md           # Documentation
├── src/                # Source code
│   ├── index.js        # Main application
│   ├── routes/         # API routes
│   └── public/         # Static files
├── config/             # Configuration files
├── scripts/            # Setup scripts
└── data/               # Persistent data (mounted)
```

## API Requirements

Your tool must implement:

- **Health Check**: `GET /health` - Returns 200 when healthy
- **Basic Info**: `GET /info` - Returns tool information

Example health check:
```javascript
app.get('/health', (req, res) => {
  res.status(200).json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString() 
  });
});
```

## Environment Variables

Common environment variables:
- `NODE_ENV` - Runtime environment (production/development)
- `PORT` - Port to run on (from machete.yml)
- `LOG_LEVEL` - Logging level
- `DATA_DIR` - Data directory path

## Development Tips

1. **Test Locally**:
   ```bash
   docker build -t my-tool .
   docker run -p 8080:8080 my-tool
   ```

2. **Check Health**:
   ```bash
   curl http://localhost:8080/health
   ```

3. **View Logs**:
   ```bash
   docker logs <container-id>
   ```

## Installation in MACHETE

1. Push your tool to a Git repository
2. Open MACHETE platform
3. Click "Install New Tool"
4. Enter your repository URL
5. MACHETE will automatically:
   - Clone your repository
   - Validate configuration
   - Build Docker image
   - Start your tool
   - Add to dashboard

## Example Tools

See the MACHETE documentation for examples of:
- Simple web applications
- API services
- Multi-container tools
- Tools with databases

## Support

- 📖 [Tool Development Guide](../docs/TOOL_DEVELOPMENT.md)
- 🛠️ [MACHETE Platform](http://localhost:8080)
- 💡 [Best Practices](../docs/TOOL_DEVELOPMENT.md#best-practices)
