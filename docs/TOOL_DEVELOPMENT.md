# MACHETE Tool Development Guide

## Overview

MACHETE (Multi-purpose Automation & Configuration Hub for Engineering Tools and Execution) allows you to install and manage engineering tools as containerized applications. This guide explains how to structure your Git repository so MACHETE can automatically install and deploy your tool.

## Quick Start

1. **Use the Template**: Start with the MACHETE tool template:
   ```bash
   git clone https://github.com/your-org/machete-tool-template
   cd machete-tool-template
   # Customize for your tool
   ```

2. **Required Files**: Your repository must contain:
   - `machete.yml` - Tool configuration
   - `Dockerfile` - Container definition
   - `README.md` - Tool documentation

## Repository Structure

```
your-tool-repo/
├── machete.yml          # Required: Tool configuration
├── Dockerfile           # Required: Container definition
├── docker-compose.yml   # Optional: Multi-service tools
├── README.md           # Required: Tool documentation
├── src/                # Your tool source code
├── config/             # Configuration files
├── scripts/            # Setup/utility scripts
└── docs/               # Additional documentation
```

## Required Files

### 1. `machete.yml` - Tool Configuration

This file tells MACHETE how to install and configure your tool:

```yaml
# Tool metadata
name: "my-awesome-tool"
version: "1.0.0"
description: "A powerful automation tool for engineering workflows"
author: "Your Name <your.email@company.com>"
license: "MIT"

# MACHETE configuration
machete:
  # Minimum MACHETE version required
  version: ">=1.0.0"
  
  # Tool category (affects UI grouping)
  category: "automation" # automation, devops, testing, analysis, etc.
  
  # Port configuration
  port: 8080
  
  # Health check endpoint
  health_check: "/health"
  
  # Environment variables
  environment:
    - NODE_ENV=production
    - LOG_LEVEL=info
    
  # Volume mounts (optional)
  volumes:
    - "./data:/app/data"
    - "./config:/app/config"
    
  # Dependencies (optional)
  dependencies:
    - postgresql
    - redis

# Tool-specific configuration
config:
  # Default configuration values
  default_timeout: 30
  max_concurrent_jobs: 5
  
# UI configuration
ui:
  # Icon (emoji or URL to icon file)
  icon: "🔧"
  
  # Primary color (hex)
  color: "#ff6b35"
  
  # Tool URL patterns
  routes:
    - path: "/"
      title: "Dashboard"
    - path: "/jobs"
      title: "Job Management"
    - path: "/settings"
      title: "Settings"
```

### 2. `Dockerfile` - Container Definition

Your tool must be containerized:

```dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci --only=production

# Copy source code
COPY . .

# Create required directories
RUN mkdir -p /app/data /app/logs

# Expose the port specified in machete.yml
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Start the application
CMD ["npm", "start"]
```

### 3. `README.md` - Tool Documentation

Provide clear documentation for your tool:

```markdown
# My Awesome Tool

Brief description of what your tool does.

## Features

- Feature 1
- Feature 2
- Feature 3

## Installation via MACHETE

1. Open MACHETE platform
2. Click "Install New Tool"
3. Enter repository URL: `https://github.com/your-org/your-tool`
4. Click Install

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| LOG_LEVEL | Logging level | info |
| API_KEY | External API key | none |

### Volume Mounts

- `/app/data` - Persistent data storage
- `/app/config` - Configuration files

## API Endpoints

- `GET /health` - Health check
- `GET /api/status` - Tool status
- `POST /api/jobs` - Create new job

## Usage

Detailed usage instructions...
```

## Optional Files

### `docker-compose.yml` - Multi-Service Tools

For tools requiring multiple containers:

```yaml
version: '3.8'
services:
  app:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DATABASE_URL=postgresql://user:pass@db:5432/mydb
    depends_on:
      - db
      
  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=mydb
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
    volumes:
      - db_data:/var/lib/postgresql/data

volumes:
  db_data:
```

### `scripts/setup.sh` - Setup Script

Optional setup script for complex installations:

```bash
#!/bin/bash
# This script runs during tool installation

echo "Setting up My Awesome Tool..."

# Create necessary directories
mkdir -p /app/data/uploads
mkdir -p /app/logs

# Set permissions
chmod 755 /app/data
chmod 755 /app/logs

# Initialize database (if needed)
if [ ! -f /app/data/database.db ]; then
    echo "Initializing database..."
    npm run init-db
fi

echo "Setup complete!"
```

## Installation Process

When you install a tool via MACHETE, the following happens:

1. **Repository Clone**: MACHETE clones your Git repository
2. **Validation**: Checks for required files (`machete.yml`, `Dockerfile`, `README.md`)
3. **Configuration Parse**: Reads `machete.yml` configuration
4. **Docker Build**: Builds the container using your `Dockerfile`
5. **Network Setup**: Creates isolated Docker network for the tool
6. **Service Start**: Starts the container with specified configuration
7. **Health Check**: Verifies the tool is running correctly
8. **Route Registration**: Adds tool routes to MACHETE's reverse proxy
9. **UI Integration**: Adds tool to MACHETE dashboard

## Best Practices

### Security
- ✅ Use non-root user in container
- ✅ Scan for vulnerabilities
- ✅ Use official base images
- ✅ Don't hardcode secrets

### Performance
- ✅ Use multi-stage builds
- ✅ Minimize image size
- ✅ Implement proper health checks
- ✅ Use appropriate resource limits

### Reliability
- ✅ Handle graceful shutdown
- ✅ Implement proper logging
- ✅ Use persistent volumes for data
- ✅ Provide configuration validation

### User Experience
- ✅ Clear documentation
- ✅ Intuitive UI
- ✅ Helpful error messages
- ✅ Consistent API design

## Tool Categories

Choose the appropriate category for your tool:

- **automation** - Workflow automation, CI/CD tools
- **devops** - Infrastructure, deployment tools
- **testing** - Testing frameworks, quality assurance
- **analysis** - Data analysis, reporting tools
- **monitoring** - System monitoring, alerting
- **security** - Security scanning, compliance tools
- **collaboration** - Team tools, communication
- **other** - Tools that don't fit other categories

## Example Tools

### Simple Web Tool
```yaml
name: "url-shortener"
version: "1.0.0"
description: "URL shortening service"
machete:
  category: "automation"
  port: 3000
  health_check: "/health"
```

### Complex Multi-Service Tool
```yaml
name: "monitoring-stack"
version: "2.1.0"
description: "Complete monitoring solution"
machete:
  category: "monitoring"
  port: 9090
  health_check: "/api/health"
  dependencies:
    - prometheus
    - grafana
    - alertmanager
```

## Troubleshooting

### Common Issues

1. **Build Failures**
   - Check Dockerfile syntax
   - Verify base image availability
   - Review build logs in MACHETE

2. **Health Check Failures**
   - Ensure health endpoint returns 200
   - Check port configuration
   - Verify container is actually running

3. **Routing Issues**
   - Confirm port matches `machete.yml`
   - Check for port conflicts
   - Review MACHETE logs

### Getting Help

- Check MACHETE platform logs
- Review tool container logs
- Consult MACHETE documentation
- Open issues on tool repository

## Contributing

To contribute to MACHETE tool development:

1. Fork the tool template repository
2. Create your tool following this guide
3. Test thoroughly with MACHETE
4. Submit for community review
5. Share with the MACHETE community

---

**Happy Tool Building! 🔧**
