const Docker = require('dockerode');
const simpleGit = require('simple-git');
const fs = require('fs-extra');
const path = require('path');
const yaml = require('yaml');

class ToolManager {
  constructor() {
    this.docker = new Docker({ socketPath: process.env.DOCKER_SOCKET || '/var/run/docker.sock' });
    this.toolsDir = process.env.TOOLS_DIR || '/app/tools';
    this.dataDir = process.env.DATA_DIR || '/app/data';
    
    // Ensure directories exist
    fs.ensureDirSync(this.toolsDir);
    fs.ensureDirSync(this.dataDir);
  }

  async getAllTools() {
    try {
      const toolsConfigPath = path.join(this.dataDir, 'tools.json');
      
      if (!await fs.pathExists(toolsConfigPath)) {
        return [];
      }
      
      const toolsConfig = await fs.readJson(toolsConfigPath);
      
      // Get current status for each tool
      const toolsWithStatus = await Promise.all(
        toolsConfig.map(async (tool) => {
          const status = await this.getToolStatus(tool.id);
          return { ...tool, status: status.status };
        })
      );
      
      return toolsWithStatus;
    } catch (error) {
      console.error('Error getting tools:', error);
      return [];
    }
  }

  async installTool(toolConfig) {
    const { name, gitUrl, description, credentials } = toolConfig;
    const toolId = name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');
    
    try {
      // Clone the repository
      const toolPath = path.join(this.toolsDir, toolId);
      
      if (await fs.pathExists(toolPath)) {
        throw new Error(`Tool ${toolId} already exists`);
      }
      
      console.log(`Cloning tool from ${gitUrl}...`);
      const git = simpleGit();
      
      // Configure git credentials if provided
      if (credentials && credentials.username && credentials.token) {
        const authUrl = gitUrl.replace('https://', `https://${credentials.username}:${credentials.token}@`);
        await git.clone(authUrl, toolPath);
      } else {
        await git.clone(gitUrl, toolPath);
      }
      
      // Read tool configuration - prioritize machete.yml, fallback to tool.json
      let toolMetadata = {
        id: toolId,
        name,
        description,
        gitUrl,
        version: '1.0.0',
        category: 'other',
        port: 8080,
        health_check: '/health',
        icon: '🔧',
        color: '#ff6b35',
        docker: {
          build: '.',
          ports: ['8080:8080'],
          environment: {}
        }
      };
      
      // Try to read machete.yml first (new format)
      const macheteConfigPath = path.join(toolPath, 'machete.yml');
      if (await fs.pathExists(macheteConfigPath)) {
        console.log(`Reading machete.yml configuration...`);
        const macheteConfig = yaml.parse(await fs.readFile(macheteConfigPath, 'utf8'));
        
        // Map machete.yml format to internal format
        toolMetadata = {
          ...toolMetadata,
          name: macheteConfig.name || name,
          description: macheteConfig.description || description,
          version: macheteConfig.version || '1.0.0',
          author: macheteConfig.author,
          license: macheteConfig.license,
          category: macheteConfig.machete?.category || 'other',
          port: macheteConfig.machete?.port || 8080,
          health_check: macheteConfig.machete?.health_check || '/health',
          icon: macheteConfig.ui?.icon || '🔧',
          color: macheteConfig.ui?.color || '#ff6b35',
          routes: macheteConfig.ui?.routes || [{ path: '/', title: 'Dashboard' }],
          environment: macheteConfig.machete?.environment || [],
          volumes: macheteConfig.machete?.volumes || [],
          dependencies: macheteConfig.machete?.dependencies || [],
          config: macheteConfig.config || {},
          docker: {
            build: '.',
            ports: [`${macheteConfig.machete?.port || 8080}:${macheteConfig.machete?.port || 8080}`],
            environment: this.arrayToObject(macheteConfig.machete?.environment || []),
            volumes: macheteConfig.machete?.volumes || []
          }
        };
      } else {
        // Fallback to tool.json (legacy format)
        const toolConfigPath = path.join(toolPath, 'tool.json');
        if (await fs.pathExists(toolConfigPath)) {
          console.log(`Reading tool.json configuration...`);
          const customConfig = await fs.readJson(toolConfigPath);
          toolMetadata = { ...toolMetadata, ...customConfig };
        }
      }
      
      // Validate required files
      const requiredFiles = ['Dockerfile', 'README.md'];
      for (const file of requiredFiles) {
        if (!await fs.pathExists(path.join(toolPath, file))) {
          throw new Error(`Required file ${file} not found in repository`);
        }
      }
      
      // Build Docker image
      console.log(`Building Docker image for ${toolId}...`);
      await this.buildToolImage(toolId, toolPath, toolMetadata.docker);
      
      // Save tool to registry
      await this.saveToolToRegistry(toolMetadata);
      
      // Start the tool automatically
      console.log(`Starting tool ${toolId}...`);
      await this.startTool(toolId);
      
      console.log(`Tool ${toolId} installed and started successfully`);
      return { 
        success: true, 
        toolId, 
        message: 'Tool installed and started successfully',
        tool: toolMetadata
      };
      
    } catch (error) {
      console.error(`Error installing tool ${toolId}:`, error);
      
      // Cleanup on failure
      const toolPath = path.join(this.toolsDir, toolId);
      if (await fs.pathExists(toolPath)) {
        await fs.remove(toolPath);
      }
      
      throw error;
    }
  }

  async buildToolImage(toolId, toolPath, dockerConfig) {
    const dockerfilePath = path.join(toolPath, 'Dockerfile');
    
    if (!await fs.pathExists(dockerfilePath)) {
      // Create a basic Dockerfile if none exists
      const basicDockerfile = `
FROM node:18-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install --production
COPY . .
EXPOSE 8080
CMD ["npm", "start"]
      `.trim();
      
      await fs.writeFile(dockerfilePath, basicDockerfile);
    }
    
    // Build the image
    const stream = await this.docker.buildImage(
      {
        context: toolPath,
        src: ['.']
      },
      {
        t: `machete-tool-${toolId}:latest`
      }
    );
    
    return new Promise((resolve, reject) => {
      this.docker.modem.followProgress(stream, (err, res) => {
        if (err) reject(err);
        else resolve(res);
      });
    });
  }

  async saveToolToRegistry(toolMetadata) {
    const toolsConfigPath = path.join(this.dataDir, 'tools.json');
    let tools = [];
    
    if (await fs.pathExists(toolsConfigPath)) {
      tools = await fs.readJson(toolsConfigPath);
    }
    
    // Remove existing tool with same ID
    tools = tools.filter(tool => tool.id !== toolMetadata.id);
    
    // Add new tool
    tools.push(toolMetadata);
    
    await fs.writeJson(toolsConfigPath, tools, { spaces: 2 });
  }

  async startTool(toolId) {
    try {
      const tool = await this.getToolConfig(toolId);
      if (!tool) {
        throw new Error(`Tool ${toolId} not found`);
      }
      
      // Check if container is already running
      const status = await this.getToolStatus(toolId);
      if (status.status === 'running') {
        return { success: true, message: 'Tool is already running' };
      }
      
      // Start the container
      const containerName = `machete-tool-${toolId}`;
      const imageTag = `machete-tool-${toolId}:latest`;
      
      const container = await this.docker.createContainer({
        Image: imageTag,
        name: containerName,
        ExposedPorts: { '8080/tcp': {} },
        HostConfig: {
          PortBindings: { '8080/tcp': [{ HostPort: '0' }] }, // Let Docker assign a port
          NetworkMode: 'machete_machete-network'
        },
        Env: Object.entries(tool.docker.environment || {}).map(([key, value]) => `${key}=${value}`)
      });
      
      await container.start();
      
      console.log(`Tool ${toolId} started successfully`);
      return { success: true, message: 'Tool started successfully' };
      
    } catch (error) {
      console.error(`Error starting tool ${toolId}:`, error);
      throw error;
    }
  }

  async stopTool(toolId) {
    try {
      const containerName = `machete-tool-${toolId}`;
      const container = this.docker.getContainer(containerName);
      
      try {
        await container.stop();
        await container.remove();
        console.log(`Tool ${toolId} stopped successfully`);
        return { success: true, message: 'Tool stopped successfully' };
      } catch (error) {
        if (error.statusCode === 404) {
          return { success: true, message: 'Tool was not running' };
        }
        throw error;
      }
      
    } catch (error) {
      console.error(`Error stopping tool ${toolId}:`, error);
      throw error;
    }
  }

  async uninstallTool(toolId) {
    try {
      // Stop the tool first
      await this.stopTool(toolId);
      
      // Remove from registry
      const toolsConfigPath = path.join(this.dataDir, 'tools.json');
      if (await fs.pathExists(toolsConfigPath)) {
        let tools = await fs.readJson(toolsConfigPath);
        tools = tools.filter(tool => tool.id !== toolId);
        await fs.writeJson(toolsConfigPath, tools, { spaces: 2 });
      }
      
      // Remove tool directory
      const toolPath = path.join(this.toolsDir, toolId);
      if (await fs.pathExists(toolPath)) {
        await fs.remove(toolPath);
      }
      
      // Remove Docker image
      try {
        const image = this.docker.getImage(`machete-tool-${toolId}:latest`);
        await image.remove();
      } catch (error) {
        console.warn(`Could not remove image for ${toolId}:`, error.message);
      }
      
      console.log(`Tool ${toolId} uninstalled successfully`);
      return { success: true, message: 'Tool uninstalled successfully' };
      
    } catch (error) {
      console.error(`Error uninstalling tool ${toolId}:`, error);
      throw error;
    }
  }

  async getToolStatus(toolId) {
    try {
      const containerName = `machete-tool-${toolId}`;
      const container = this.docker.getContainer(containerName);
      
      try {
        const info = await container.inspect();
        return {
          status: info.State.Running ? 'running' : 'stopped',
          containerId: info.Id,
          created: info.Created,
          ports: info.NetworkSettings.Ports
        };
      } catch (error) {
        if (error.statusCode === 404) {
          return { status: 'stopped' };
        }
        throw error;
      }
      
    } catch (error) {
      console.error(`Error getting tool status for ${toolId}:`, error);
      return { status: 'error', error: error.message };
    }
  }

  async getToolConfig(toolId) {
    const toolsConfigPath = path.join(this.dataDir, 'tools.json');
    
    if (!await fs.pathExists(toolsConfigPath)) {
      return null;
    }
    
    const tools = await fs.readJson(toolsConfigPath);
    return tools.find(tool => tool.id === toolId);
  }

  // Helper method to convert environment array to object
  arrayToObject(envArray) {
    const envObj = {};
    if (Array.isArray(envArray)) {
      envArray.forEach(env => {
        if (typeof env === 'string' && env.includes('=')) {
          const [key, ...valueParts] = env.split('=');
          envObj[key] = valueParts.join('=');
        }
      });
    }
    return envObj;
  }
}

module.exports = ToolManager;
