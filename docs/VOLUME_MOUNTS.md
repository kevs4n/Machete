# MACHETE Volume Mounts - Complete Guide

## Overview

MACHETE handles volume mounts for tools through a multi-step process that ensures data persistence and proper file access for containerized tools.

## Architecture

### 1. **Volume Configuration Storage**
- Volumes are stored in the `Tool.volumes` database field as JSON
- Format: `{"host_path": "container_path", ...}`
- Example: `{"./data": "/app/data", "./config": "/app/config"}`

### 2. **Volume Processing Pipeline**

```
Tool Installation
    ↓
machete.yml parsing (volumes section)
    ↓
JSON storage in database (Tool.volumes field)
    ↓
Container startup (volume preparation)
    ↓
Docker volume mounting
```

## Volume Configuration

### Method 1: machete.yml (Recommended)
```yaml
# machete.yml
machete:
  volumes:
    - "./data:/app/data"
    - "./config:/app/config" 
    - "./logs:/app/logs"
```

### Method 2: Direct API (Advanced)
```json
{
  "volumes": {
    "./data": "/app/data",
    "./config": "/app/config",
    "./logs": "/app/logs"
  }
}
```

## Volume Types & Patterns

### 1. **Tool Data Directory (Recommended)**
```yaml
volumes:
  - "./data:/app/data"           # Tool-specific data
  - "./config:/app/config"       # Tool configuration
  - "./logs:/app/logs"           # Tool logs
```

**Host Location:** `/app/data/tools/{tool-name}/data`
**Benefits:** 
- ✅ Isolated per tool
- ✅ Easy backup/restore
- ✅ No conflicts between tools

### 2. **Shared Volumes (Advanced)**
```yaml
volumes:
  - "/shared/data:/app/shared"    # Shared across tools
  - "/host/config:/app/config"    # Host system integration
```

**Use Cases:**
- Shared databases
- Common configuration
- Integration with host services

### 3. **Named Volumes (Future)**
```yaml
volumes:
  - "tool-database:/var/lib/mysql"
  - "tool-cache:/app/cache"
```

## Implementation Details

### Current Docker Service Logic

```python
# 1. Volume parsing during container start
if tool.volumes:
    import json
    volume_config = json.loads(tool.volumes)
    volumes = prepare_volumes(tool.name, volume_config)

# 2. Volume preparation (with directory creation)
def prepare_volumes(tool_name, config):
    prepared = {}
    base_dir = f"/app/data/tools/{tool_name}"
    
    for host_path, container_path in config.items():
        if host_path.startswith('./'):
            # Relative path - under tool directory
            full_path = f"{base_dir}/{host_path[2:]}"
        else:
            # Absolute path - use as-is
            full_path = host_path
            
        # Ensure directory exists
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        # Docker volume format
        prepared[full_path] = {
            'bind': container_path, 
            'mode': 'rw'
        }
    
    return prepared

# 3. Container startup with volumes
container = docker_client.containers.run(
    image=f"machete-{tool.name}",
    volumes=volumes,
    # ... other config
)
```

## Directory Structure

```
/app/data/tools/
├── my-tool/
│   ├── data/           # ./data mount
│   ├── config/         # ./config mount
│   ├── logs/           # ./logs mount
│   └── uploads/        # Custom mounts
├── another-tool/
│   ├── data/
│   └── config/
└── shared/             # Shared volumes
    ├── databases/
    └── common-config/
```

## Volume Mount Examples

### Example 1: Simple Web Tool
```yaml
# Tool: dashboard-app
machete:
  port: 3000
  volumes:
    - "./data:/app/data"
    - "./uploads:/app/public/uploads"
```

**Result:**
- Host: `/app/data/tools/dashboard-app/data` ↔ Container: `/app/data`
- Host: `/app/data/tools/dashboard-app/uploads` ↔ Container: `/app/public/uploads`

### Example 2: Database Tool
```yaml
# Tool: postgres-admin
machete:
  port: 5050
  volumes:
    - "./db-data:/var/lib/postgresql/data"
    - "./backups:/app/backups"
    - "/shared/database-configs:/app/configs"
```

### Example 3: Development Tool
```yaml
# Tool: code-server
machete:
  port: 8080
  volumes:
    - "./workspace:/home/coder/workspace"
    - "./settings:/home/coder/.local/share/code-server"
    - "/host/projects:/home/coder/projects"  # Host integration
```

## Security Considerations

### 1. **Path Validation**
- ✅ Relative paths are contained within tool directory
- ⚠️ Absolute paths require validation
- ❌ Parent directory traversal blocked (`../` paths)

### 2. **Permission Management**
```yaml
# Tool configuration
machete:
  volumes:
    - "./data:/app/data:rw"      # Read-write (default)
    - "./config:/app/config:ro"  # Read-only
```

### 3. **Resource Limits**
```yaml
resources:
  disk_quota: "5GB"             # Per-tool limit
  volumes:
    max_mounts: 10              # Maximum volume mounts
```

## Troubleshooting

### Common Issues

1. **Permission Denied**
   ```bash
   # Check host directory permissions
   ls -la /app/data/tools/my-tool/
   
   # Fix permissions
   chown -R 1000:1000 /app/data/tools/my-tool/
   ```

2. **Volume Not Created**
   ```bash
   # Check if MACHETE created the directory
   docker exec machete-api ls -la /app/data/tools/
   
   # Manually create if needed
   docker exec machete-api mkdir -p /app/data/tools/my-tool/data
   ```

3. **Data Not Persisting**
   ```bash
   # Verify volume mount in container
   docker exec machete-tool-my-tool mount | grep /app/data
   
   # Check Docker volume configuration
   docker inspect machete-tool-my-tool | jq '.Mounts'
   ```

## Best Practices

### 1. **Tool Design**
- Use relative paths in machete.yml
- Keep data in predictable locations (`/app/data`, `/app/config`)
- Document required volumes in README

### 2. **Volume Organization**
```
./data/          # Application data
./config/        # Configuration files  
./logs/          # Log files
./cache/         # Temporary/cache data
./uploads/       # User uploads
```

### 3. **Backup Strategy**
```bash
# Backup tool data
tar -czf my-tool-backup.tar.gz /app/data/tools/my-tool/

# Restore tool data
tar -xzf my-tool-backup.tar.gz -C /
```

## Future Enhancements

### Planned Features
- 🔄 Named volume support
- 🔄 Volume templates
- 🔄 Automatic backup/restore
- 🔄 Volume quota management
- 🔄 Shared volume orchestration

### API Enhancements
```python
# Future API endpoints
POST /api/tools/{id}/volumes          # Add volume mount
DELETE /api/tools/{id}/volumes/{name} # Remove volume mount
GET /api/tools/{id}/volumes/usage     # Volume usage stats
```

---

## Quick Reference

### Check Tool Volumes
```bash
# Via API
curl http://localhost:8090/api/tools/{tool_id}

# Via Database
docker exec -it machete-db psql -U machete -c "SELECT name, volumes FROM tools;"

# Via Container
docker inspect machete-tool-{name} | jq '.Mounts'
```

### Add Volume to Existing Tool
```bash
# Update tool volumes via API (future)
curl -X PATCH http://localhost:8090/api/tools/{id} \
  -H "Content-Type: application/json" \
  -d '{"volumes": {"./new-data": "/app/new-data"}}'
```
