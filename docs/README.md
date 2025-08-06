# MACHETE Platform Documentation

## Table of Contents

1. [Getting Started](#getting-started)
2. [Architecture](#architecture)
3. [Tool Development](#tool-development)
4. [API Reference](#api-reference)
5. [Deployment](#deployment)
6. [Troubleshooting](#troubleshooting)

## Getting Started

### Prerequisites

- Docker 20.10 or later
- Docker Compose 2.0 or later
- Git
- At least 4GB RAM
- 10GB free disk space

### Quick Setup

#### Linux/macOS
```bash
# Clone the repository
git clone <repository-url>
cd machete

# Make setup script executable
chmod +x scripts/setup.sh

# Run setup
./scripts/setup.sh
```

#### Windows
```powershell
# Clone the repository
git clone <repository-url>
cd machete

# Run setup
.\scripts\setup.ps1
```

### First Steps

1. Open your browser and go to `http://localhost:8080`
2. You'll see the MACHETE dashboard with available tools
3. Use the Tool Registry to install new tools
4. Access installed tools through the dashboard

## Architecture

MACHETE uses a microservices architecture with the following components:

### Core Components

- **Caddy Proxy**: Reverse proxy and load balancer
- **Frontend**: React-based web interface
- **API**: Node.js backend for tool management
- **Database**: PostgreSQL for storing tool configurations

### Tool Architecture

Each tool runs in its own Docker container and communicates with the core platform through:

- HTTP APIs
- Shared volumes
- Network isolation

```
┌─────────────────┐
│   Web Browser   │
└─────────┬───────┘
          │
┌─────────▼───────┐    ┌──────────────────┐
│   Caddy Proxy   │────│   Tool Registry  │
└─────────┬───────┘    └──────────────────┘
          │
    ┌─────┼─────┐
    │     │     │
┌───▼──┐ ┌▼───┐ ┌▼────┐
│Tool A│ │Tool│ │Tool │
│      │ │ B  │ │ C   │
└──────┘ └────┘ └─────┘
```

## Tool Development

### Tool Structure

Each tool should follow this structure:

```
tool-name/
├── tool.json          # Tool metadata and configuration
├── Dockerfile         # Container definition
├── package.json       # Dependencies (for Node.js tools)
├── install.sh         # Installation script
├── README.md          # Documentation
└── src/              # Source code
    ├── server.js     # Main application
    └── ...
```

### Tool Configuration (tool.json)

```json
{
  "id": "my-tool",
  "name": "My Tool",
  "description": "Description of what the tool does",
  "version": "1.0.0",
  "docker": {
    "build": ".",
    "ports": ["8080:8080"],
    "environment": {
      "NODE_ENV": "production"
    }
  },
  "routes": {
    "base": "/tools/my-tool"
  }
}
```

### Creating a New Tool

1. Use the template in `tools/_template/`
2. Modify `tool.json` with your tool's configuration
3. Implement your tool's functionality
4. Test locally with Docker
5. Push to a Git repository
6. Install through MACHETE Tool Registry

### Tool Requirements

- Must run on port 8080 inside the container
- Must include a `/health` endpoint
- Must handle graceful shutdown
- Should follow REST API conventions
- Must include proper error handling

## API Reference

### Core API Endpoints

#### Health Check
```
GET /api/health
```

#### Tool Management
```
GET /api/tools                    # List all tools
POST /api/tools/install           # Install a new tool
POST /api/tools/:id/start         # Start a tool
POST /api/tools/:id/stop          # Stop a tool
DELETE /api/tools/:id             # Uninstall a tool
GET /api/tools/:id/status         # Get tool status
```

### Tool Installation

```bash
curl -X POST http://localhost:8080/api/tools/install \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Tool",
    "gitUrl": "https://github.com/user/my-tool",
    "description": "Tool description",
    "credentials": {
      "username": "optional-username",
      "token": "optional-token"
    }
  }'
```

## Deployment

### Production Deployment

1. Clone the repository on your server
2. Configure environment variables
3. Run the setup script
4. Configure reverse proxy (if needed)
5. Set up SSL certificates
6. Configure monitoring

### Environment Variables

```bash
# Core API
NODE_ENV=production
PORT=3001
DATABASE_URL=postgresql://user:pass@localhost:5432/machete

# Docker
DOCKER_SOCKET=/var/run/docker.sock
TOOLS_DIR=/app/tools
DATA_DIR=/app/data
```

### SSL Configuration

Update `core/caddy/Caddyfile` for your domain:

```
yourdomain.com {
    reverse_proxy frontend:3000
    
    handle /api/* {
        reverse_proxy api:3001
    }
}
```

## Troubleshooting

### Common Issues

#### Tools not starting
1. Check Docker logs: `docker-compose logs`
2. Verify tool configuration in `tool.json`
3. Check port conflicts
4. Ensure sufficient system resources

#### Connection issues
1. Verify Caddy configuration
2. Check network connectivity
3. Review firewall settings
4. Check Docker network status

#### Performance issues
1. Monitor system resources
2. Check Docker container limits
3. Review tool resource usage
4. Consider scaling options

### Debug Mode

Enable debug logging:

```bash
# Set environment variables
export DEBUG=machete:*
export LOG_LEVEL=debug

# Restart services
docker-compose restart
```

### Logs

View logs for specific services:

```bash
# All services
docker-compose logs

# Specific service
docker-compose logs api
docker-compose logs frontend
docker-compose logs caddy

# Follow logs
docker-compose logs -f api
```

## Support

- Create issues on GitHub
- Check the troubleshooting guide
- Review the API documentation
- Join the community discussions
