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
  Alert,
  CircularProgress,
  Snackbar,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete as DeleteIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
  Home as HomeIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { toolsAPI, apiUtils } from '../services/api';

const ToolRegistry = () => {
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [open, setOpen] = useState(false);
  const [installing, setInstalling] = useState(false);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'info' });
  const [newTool, setNewTool] = useState({
    name: '',
    git_url: '',
    description: '',
    git_branch: 'main',
    tool_type: 'web',
    port: 3000
  });
  const navigate = useNavigate();

  useEffect(() => {
    loadTools();
  }, []);

  const loadTools = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await toolsAPI.getAll();
      setTools(response.data);
    } catch (err) {
      console.error('Error loading tools:', err);
      setError(apiUtils.handleError(err, 'Failed to load tools'));
    } finally {
      setLoading(false);
    }
  };

  const showSnackbar = (message, severity = 'info') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleInstallTool = async () => {
    try {
      setInstalling(true);
      
      // Prepare tool data for API (matching backend ToolCreate model)
      const toolData = {
        git_url: newTool.git_url,
        name: newTool.name.toLowerCase().replace(/\s+/g, '-'),
        branch: newTool.git_branch
      };
      
      const response = await toolsAPI.install(toolData);
      
      // Check if installation was successful
      if (response.data.success) {
        showSnackbar('Tool installation started successfully!', 'success');
        setOpen(false);
        setNewTool({
          name: '',
          git_url: '',
          description: '',
          git_branch: 'main',
          tool_type: 'web',
          port: 3000
        });
        
        // Reload tools after installation
        await loadTools();
      } else {
        showSnackbar(`Installation failed: ${response.data.error}`, 'error');
      }
    } catch (error) {
      console.error('Error installing tool:', error);
      showSnackbar(apiUtils.handleError(error, 'Failed to install tool'), 'error');
    } finally {
      setInstalling(false);
    }
  };

  const handleStartStop = async (toolId, currentStatus) => {
    try {
      if (currentStatus === 'running') {
        await toolsAPI.stop(toolId);
        showSnackbar('Tool stopped successfully', 'success');
      } else {
        await toolsAPI.start(toolId);
        showSnackbar('Tool started successfully', 'success');
      }
      
      // Reload tools to get updated status
      await loadTools();
    } catch (error) {
      console.error('Error changing tool status:', error);
      showSnackbar(apiUtils.handleError(error, 'Failed to change tool status'), 'error');
    }
  };

  const handleUninstall = async (toolId) => {
    if (!window.confirm('Are you sure you want to uninstall this tool?')) {
      return;
    }
    
    try {
      await toolsAPI.delete(toolId);
      showSnackbar('Tool uninstalled successfully', 'success');
      
      // Reload tools after uninstall
      await loadTools();
    } catch (error) {
      console.error('Error uninstalling tool:', error);
      showSnackbar(apiUtils.handleError(error, 'Failed to uninstall tool'), 'error');
    }
  };
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'running': return 'success';
      case 'stopped': return 'default';
      case 'installing': return 'warning';
      case 'failed': return 'error';
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
          <IconButton color="inherit" onClick={loadTools} disabled={loading}>
            <RefreshIcon />
          </IconButton>
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

        {/* Error Alert */}
        {error && (
          <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {/* Loading State */}
        {loading && (
          <Box sx={{ display: 'flex', justifyContent: 'center', mt: 4 }}>
            <CircularProgress />
          </Box>
        )}

        {/* Tools Grid */}
        {!loading && (
          <Grid container spacing={3}>
            {tools.map((tool) => (
              <Grid item xs={12} md={6} key={tool.id}>
                <Card>
                  <CardContent>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                      <Typography variant="h6">
                        {tool.display_name || tool.name}
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
                      {tool.git_url}
                    </Typography>
                    {tool.port && (
                      <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                        Port: {tool.port} | Type: {tool.tool_type} | Version: {tool.version || 'N/A'}
                      </Typography>
                    )}
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
        )}

        {/* Empty State */}
        {!loading && tools.length === 0 && (
          <Box sx={{ textAlign: 'center', mt: 4 }}>
            <Typography variant="h6" color="text.secondary" gutterBottom>
              No Tools Installed
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
              Get started by installing your first tool from a Git repository
            </Typography>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => setOpen(true)}
            >
              Install New Tool
            </Button>
          </Box>
        )}

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
              value={newTool.git_url}
              onChange={(e) => setNewTool({ ...newTool, git_url: e.target.value })}
              sx={{ mb: 2 }}
            />
            <TextField
              margin="dense"
              label="Git Branch"
              fullWidth
              variant="outlined"
              value={newTool.git_branch}
              onChange={(e) => setNewTool({ ...newTool, git_branch: e.target.value })}
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
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  margin="dense"
                  label="Tool Type"
                  select
                  fullWidth
                  variant="outlined"
                  value={newTool.tool_type}
                  onChange={(e) => setNewTool({ ...newTool, tool_type: e.target.value })}
                  SelectProps={{ native: true }}
                >
                  <option value="web">Web Application</option>
                  <option value="api">API Service</option>
                  <option value="service">Background Service</option>
                </TextField>
              </Grid>
              <Grid item xs={6}>
                <TextField
                  margin="dense"
                  label="Port"
                  type="number"
                  fullWidth
                  variant="outlined"
                  value={newTool.port}
                  onChange={(e) => setNewTool({ ...newTool, port: e.target.value })}
                />
              </Grid>
            </Grid>
          </DialogContent>
          <DialogActions>
            <Button onClick={() => setOpen(false)} disabled={installing}>
              Cancel
            </Button>
            <Button 
              onClick={handleInstallTool} 
              variant="contained"
              disabled={!newTool.name || !newTool.git_url || installing}
            >
              {installing ? <CircularProgress size={20} /> : 'Install'}
            </Button>
          </DialogActions>
        </Dialog>

        {/* Snackbar for notifications */}
        <Snackbar
          open={snackbar.open}
          autoHideDuration={6000}
          onClose={() => setSnackbar({ ...snackbar, open: false })}
        >
          <Alert 
            onClose={() => setSnackbar({ ...snackbar, open: false })} 
            severity={snackbar.severity}
            sx={{ width: '100%' }}
          >
            {snackbar.message}
          </Alert>
        </Snackbar>
      </Container>
    </>
  );
};

export default ToolRegistry;
