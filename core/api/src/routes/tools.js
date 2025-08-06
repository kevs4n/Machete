const express = require('express');
const router = express.Router();
const ToolManager = require('../services/ToolManager');

const toolManager = new ToolManager();

// Get all installed tools
router.get('/', async (req, res) => {
  try {
    const tools = await toolManager.getAllTools();
    res.json(tools);
  } catch (error) {
    console.error('Error getting tools:', error);
    res.status(500).json({ error: 'Failed to get tools' });
  }
});

// Get tools formatted for dashboard cards
router.get('/dashboard', async (req, res) => {
  try {
    const tools = await toolManager.getAllTools();
    
    // Format tools for dashboard display
    const dashboardTools = tools.map(tool => ({
      id: tool.id,
      name: tool.name,
      description: tool.description,
      icon: tool.icon || '🔧',
      color: tool.color || '#ff6b35',
      category: tool.category || 'other',
      status: tool.status,
      port: tool.port,
      url: `http://localhost:8080/tools/${tool.id}`,
      routes: tool.routes || [{ path: '/', title: 'Dashboard' }],
      health_check: tool.health_check || '/health',
      version: tool.version || '1.0.0',
      author: tool.author
    }));
    
    res.json(dashboardTools);
  } catch (error) {
    console.error('Error getting dashboard tools:', error);
    res.status(500).json({ error: 'Failed to get dashboard tools' });
  }
});

// Install a new tool
router.post('/install', async (req, res) => {
  try {
    const { name, gitUrl, description, credentials } = req.body;
    
    if (!name || !gitUrl) {
      return res.status(400).json({ error: 'Name and gitUrl are required' });
    }

    const result = await toolManager.installTool({
      name,
      gitUrl,
      description,
      credentials
    });

    res.json(result);
  } catch (error) {
    console.error('Error installing tool:', error);
    res.status(500).json({ error: 'Failed to install tool' });
  }
});

// Start a tool
router.post('/:toolId/start', async (req, res) => {
  try {
    const { toolId } = req.params;
    const result = await toolManager.startTool(toolId);
    res.json(result);
  } catch (error) {
    console.error('Error starting tool:', error);
    res.status(500).json({ error: 'Failed to start tool' });
  }
});

// Stop a tool
router.post('/:toolId/stop', async (req, res) => {
  try {
    const { toolId } = req.params;
    const result = await toolManager.stopTool(toolId);
    res.json(result);
  } catch (error) {
    console.error('Error stopping tool:', error);
    res.status(500).json({ error: 'Failed to stop tool' });
  }
});

// Uninstall a tool
router.delete('/:toolId', async (req, res) => {
  try {
    const { toolId } = req.params;
    const result = await toolManager.uninstallTool(toolId);
    res.json(result);
  } catch (error) {
    console.error('Error uninstalling tool:', error);
    res.status(500).json({ error: 'Failed to uninstall tool' });
  }
});

// Get tool status
router.get('/:toolId/status', async (req, res) => {
  try {
    const { toolId } = req.params;
    const status = await toolManager.getToolStatus(toolId);
    res.json(status);
  } catch (error) {
    console.error('Error getting tool status:', error);
    res.status(500).json({ error: 'Failed to get tool status' });
  }
});

module.exports = router;
