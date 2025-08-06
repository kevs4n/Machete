import React, { useState, useEffect } from 'react';
import {
  Container,
  Typography,
  Card,
  CardContent,
  Button,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Chip,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  AppBar,
  Toolbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Home as HomeIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

const ToolRegistry = () => {
  const [tools, setTools] = useState([]);
  const [open, setOpen] = useState(false);
  const [newTool, setNewTool] = useState({
    name: '',
    gitUrl: '',
    description: '',
    credentials: { username: '', token: '' }
  });
  const navigate = useNavigate();

  // Mock installed tools
  const mockInstalledTools = [
    {
      id: 'azure-devops',
      name: 'Azure DevOps Process Creation',
      gitUrl: 'https://github.com/example/azure-devops-tool',
      status: 'running',
      description: 'Create and manage Azure DevOps process templates'
    },
    {
      id: 'fasttrack',
      name: 'Fasttrack Process Model Import',
      gitUrl: 'https://github.com/example/fasttrack-tool',
      status: 'stopped',
      description: 'Import and manage Fasttrack process models'
    }
  ];

  useEffect(() => {
    setTools(mockInstalledTools);
  }, []);

  const handleInstallTool = async () => {
    try {
      // TODO: Implement actual API call
      const toolId = newTool.name.toLowerCase().replace(/\s+/g, '-');
      const newInstalledTool = {
        id: toolId,
        name: newTool.name,
        gitUrl: newTool.gitUrl,
        description: newTool.description,
        status: 'installing'
      };
      
      setTools([...tools, newInstalledTool]);
      setOpen(false);
      setNewTool({ name: '', gitUrl: '', description: '', credentials: { username: '', token: '' } });
      
      // Simulate installation process
      setTimeout(() => {
        setTools(prev => prev.map(tool => 
          tool.id === toolId ? { ...tool, status: 'stopped' } : tool
        ));
      }, 3000);
    } catch (error) {
      console.error('Error installing tool:', error);
    }
  };

  const handleStartStop = async (toolId, currentStatus) => {
    const newStatus = currentStatus === 'running' ? 'stopped' : 'running';
    setTools(prev => prev.map(tool => 
      tool.id === toolId ? { ...tool, status: newStatus } : tool
    ));
  };

  const handleUninstall = async (toolId) => {
    setTools(prev => prev.filter(tool => tool.id !== toolId));
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'default';
      case 'installing': return 'warning';
      case 'error': return 'error';
      default: return 'default';
    }
  };

  return (
    <>
      <AppBar position="static">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => navigate('/')}
          >
            <HomeIcon />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            Tool Registry
          </Typography>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
          <Typography variant="h4">
            Installed Tools
          </Typography>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setOpen(true)}
          >
            Install New Tool
          </Button>
        </Box>

        <Grid container spacing={3}>
          {tools.map((tool) => (
            <Grid item xs={12} md={6} key={tool.id}>
              <Card>
                <CardContent>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                    <Typography variant="h6">
                      {tool.name}
                    </Typography>
                    <Chip 
                      label={tool.status} 
                      color={getStatusColor(tool.status)}
                      size="small"
                    />
                  </Box>
                  <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                    {tool.description}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    {tool.gitUrl}
                  </Typography>
                  <Box sx={{ display: 'flex', gap: 1 }}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={tool.status === 'running' ? <StopIcon /> : <PlayIcon />}
                      onClick={() => handleStartStop(tool.id, tool.status)}
                      disabled={tool.status === 'installing'}
                    >
                      {tool.status === 'running' ? 'Stop' : 'Start'}
                    </Button>
                    <Button
                      size="small"
                      variant="outlined"
                      color="error"
                      startIcon={<DeleteIcon />}
                      onClick={() => handleUninstall(tool.id)}
                    >
                      Uninstall
                    </Button>
                  </Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>

        {/* Install Tool Dialog */}
        <Dialog open={open} onClose={() => setOpen(false)} maxWidth="sm" fullWidth>
          <DialogTitle>Install New Tool</DialogTitle>
          <DialogContent>
            <TextField
              autoFocus
              margin="dense"
              label="Tool Name"
              fullWidth
              variant="outlined"
              value={newTool.name}
              onChange={(e) => setNewTool({ ...newTool, name: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Git Repository URL"
              fullWidth
              variant="outlined"
              value={newTool.gitUrl}
              onChange={(e) => setNewTool({ ...newTool, gitUrl: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Description"
              fullWidth
              multiline
              rows={3}
              variant="outlined"
              value={newTool.description}
              onChange={(e) => setNewTool({ ...newTool, description: e.target.value })}
              sx={{ mb: 2 }}
            />
            <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>
              Git Credentials (Optional)
            </Typography>
            <TextField
              margin="dense"
              label="Username"
              fullWidth
              variant="outlined"
              value={newTool.credentials.username}
              onChange={(e) => setNewTool({ 
                ...newTool, 
                credentials: { ...newTool.credentials, username: e.target.value }
              })}
              sx={{ mb: 1 }}
            />
            <TextField
              margin="dense"
              label="Personal Access Token"
              type="password"
              fullWidth
              variant="outlined"
              value={newTool.credentials.token}
              onChange={(e) => setNewTool({ 
                ...newTool, 
                credentials: { ...newTool.credentials, token: e.target.value }
              })}
            />
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)}>Cancel</Button>
            <Button 
              onClick={handleInstallTool} 
              variant="contained"
              disabled={!newTool.name || !newTool.gitUrl}
            >
              Install
            </Button>
          </DialogActions>
        </Dialog>
      </Container>
    </>
  );
};

export default ToolRegistry;
