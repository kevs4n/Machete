# MACHETE
**Multi-purpose Automation & Configuration Hub for Engineering Tools and Execution**

## Overview
MACHETE is a containerized platform that serves as a Swiss Army knife for engineering tools. It provides a unified interface to manage and access various automation tools through a web-based frontend.

## Features
- **Tool Registry**: Easily install new tools by pointing to Git repositories
- **Unified Frontend**: Simple web interface to access all tools
- **Docker-based**: All tools run in isolated containers
- **Caddy Proxy**: Automatic HTTPS and reverse proxy
- **Extensible**: Plugin system for adding new capabilities

## Architecture
```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Web Browser   │────│   Caddy Proxy    │────│   Tool Registry │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                    ┌───────────┼───────────┐
                    │           │           │
            ┌───────▼────┐ ┌────▼────┐ ┌────▼────┐
            │   Tool A   │ │ Tool B  │ │ Tool C  │
            │(Container) │ │(Container)│ │(Container)│
            └────────────┘ └─────────┘ └─────────┘
```

## Initial Tools
1. **Azure DevOps Process Creation**: Tool for creating and managing Azure DevOps processes
2. **Fasttrack Process Model Import**: Tool for importing and managing Fasttrack process models

## Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd machete

# Start the platform
docker-compose up -d

# Access the platform
# Open http://localhost:8080 (will redirect to HTTPS)
```

### Windows Setup Options

**Option 1: Using Batch File (Recommended)**
```cmd
scripts\setup.bat
```

**Option 2: Using PowerShell**
```powershell
# First, allow script execution (one-time setup)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Then run the setup
.\scripts\setup.ps1
```

## Tool Development

MACHETE automatically discovers and displays any tool you install from a Git repository. Each tool should include:

### Required Files
- **`machete.yml`** - Tool configuration (recommended) or `tool.json` (legacy)
- **`Dockerfile`** - Container definition
- **`README.md`** - Tool documentation

### Tool Configuration (`machete.yml`)
```yaml
name: "my-awesome-tool"
version: "1.0.0"
description: "What your tool does"
machete:
  category: "automation"     # Affects UI grouping
  port: 8080                # Port your tool runs on
  health_check: "/health"   # Health check endpoint
ui:
  icon: "🔧"               # Tool icon (emoji or URL)
  color: "#ff6b35"         # Primary color
```

### Installation Process
1. **Install Tool**: Click "Install New Tool" in MACHETE dashboard
2. **Enter Git URL**: Provide your tool's repository URL
3. **Automatic Setup**: MACHETE will:
   - Clone your repository
   - Build Docker container
   - Start the tool
   - Add new card to dashboard

### Tool Access
Once installed, tools appear as new cards on the MACHETE dashboard with:
- ✅ **Real-time status** (running/stopped/error)
- 🎨 **Custom styling** (icon, color from `machete.yml`)
- 🔗 **Direct access** via "Open Tool" button
- 📊 **Health monitoring** via configured health check

For detailed development instructions, see [`docs/TOOL_DEVELOPMENT.md`](docs/TOOL_DEVELOPMENT.md)

## Directory Structure
```
machete/
├── core/                 # Core platform components
│   ├── frontend/        # Management UI
│   ├── api/            # Core API
│   └── caddy/          # Proxy configuration
├── tools/              # Individual tools
├── scripts/            # Setup scripts
├── docker-compose.yml  # Main orchestration
└── docs/              # Documentation
```
