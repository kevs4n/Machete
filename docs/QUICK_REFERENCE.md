# MACHETE Tool Quick Reference

## Repository Requirements ✅

Your Git repository **MUST** contain:

### 📄 `machete.yml` - Tool Configuration
```yaml
name: "my-tool"
version: "1.0.0"
description: "What your tool does"
machete:
  category: "automation"  # automation, devops, testing, etc.
  port: 8080
  health_check: "/health"
ui:
  icon: "🔧"
  color: "#ff6b35"
```

### 🐳 `Dockerfile` - Container Definition
```dockerfile
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 8080
HEALTHCHECK CMD curl -f http://localhost:8080/health || exit 1
CMD ["npm", "start"]
```

### 📖 `README.md` - Documentation
- Clear description
- Installation instructions
- Usage examples
- API documentation

## Required API Endpoints 🔗

Your tool **MUST** implement:

```javascript
// Health check - returns 200 when healthy
GET /health
Response: { "status": "healthy" }

// Optional but recommended
GET /info
Response: { "name": "My Tool", "version": "1.0.0" }
```

## Installation Process 🚀

1. **Open MACHETE** → http://localhost:8080
2. **Click "Install New Tool"**
3. **Enter Git URL** → `https://github.com/your-org/your-tool`
4. **Click Install**

MACHETE will automatically:
- ✅ Clone repository
- ✅ Validate structure
- ✅ Build Docker image
- ✅ Start container
- ✅ Add to dashboard

## Tool Categories 📂

| Category | Description | Examples |
|----------|-------------|----------|
| `automation` | Workflow automation | CI/CD, schedulers |
| `devops` | Infrastructure tools | Deployment, monitoring |
| `testing` | QA and testing tools | Test runners, validators |
| `analysis` | Data analysis | Reports, metrics |
| `monitoring` | System monitoring | Alerts, dashboards |
| `security` | Security tools | Scanners, compliance |
| `collaboration` | Team tools | Chat, wikis |
| `other` | Everything else | Utilities, demos |

## Common Patterns 🔄

### Simple Web App
```yaml
name: "my-web-app"
machete:
  category: "automation"
  port: 3000
  health_check: "/health"
```

### API Service
```yaml
name: "my-api"
machete:
  category: "devops"
  port: 8080
  health_check: "/api/health"
  environment:
    - API_KEY=your-key
```

### Multi-Container Tool
```yaml
name: "my-complex-tool"
machete:
  category: "monitoring"
  port: 9090
  dependencies:
    - postgresql
    - redis
```

## Troubleshooting 🛠️

| Issue | Solution |
|-------|----------|
| Build fails | Check Dockerfile syntax |
| Health check fails | Ensure `/health` returns 200 |
| Port conflicts | Change port in `machete.yml` |
| Tool not in dashboard | Check MACHETE logs |

## Quick Commands 💻

```bash
# Test locally
docker build -t my-tool .
docker run -p 8080:8080 my-tool
curl http://localhost:8080/health

# Check MACHETE logs
docker-compose logs api
docker-compose logs frontend

# View installed tools
curl http://localhost:8080/api/tools
```

## Examples 📚

- **URL Shortener**: Simple web service
- **Log Analyzer**: File processing tool
- **API Gateway**: Multi-service tool
- **Dashboard**: Monitoring interface

## Support 💡

- 📖 [Full Documentation](./TOOL_DEVELOPMENT.md)
- 🔗 [Tool Template](../tools/_template/)
- 🏠 [MACHETE Platform](http://localhost:8080)

---
**Ready to build? Use the template in `tools/_template/`** 🚀
