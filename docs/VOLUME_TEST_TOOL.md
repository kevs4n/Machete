# Simple Volume Test Tool

This tool demonstrates MACHETE's volume mount capabilities.

## What it does

- Creates files in mounted volumes
- Shows directory listings
- Tests read/write permissions
- Displays volume mount information

## Volume Configuration

```yaml
# machete.yml
machete:
  port: 8080
  volumes:
    - "./data:/app/data"
    - "./config:/app/config"
    - "./logs:/app/logs"
```

## Expected Behavior

1. **Data Directory**: `/app/data` mapped to host `./data`
   - Tool creates `data.txt` with timestamp
   - Persistent across container restarts

2. **Config Directory**: `/app/config` mapped to host `./config`
   - Tool reads `config.json` if present
   - Creates default config if missing

3. **Logs Directory**: `/app/logs` mapped to host `./logs`
   - Tool writes access logs
   - Rotated log files

## Testing

```bash
# Install the tool
curl -X POST http://localhost:8090/api/tools/install \
  -H "Content-Type: application/json" \
  -d '{"git_url": "https://github.com/example/volume-test-tool", "name": "volume-test"}'

# Start the tool
curl -X POST http://localhost:8090/api/tools/{tool_id}/start

# Check volumes
docker inspect machete-tool-volume-test | jq '.Mounts'

# Verify file creation
ls -la /app/data/tools/volume-test/
```

## File Structure

```
volume-test-tool/
├── machete.yml          # MACHETE configuration
├── Dockerfile           # Container definition  
├── package.json         # Node.js dependencies
├── server.js           # Main application
└── public/
    ├── index.html      # Volume status page
    └── style.css       # Basic styling
```
