import React, { useState, useEffect } from 'react';
import {
  Container,
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  AppBar,
  Toolbar,
  IconButton,
  Menu,
  MenuItem,
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Build as BuildIcon,
  CloudDownload as CloudDownloadIcon,
  AccountTree as AccountTreeIcon,
  Speed as SpeedIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';

const Dashboard = () => {
  const [tools, setTools] = useState([]);
  const [anchorEl, setAnchorEl] = useState(null);
  const navigate = useNavigate();

  // Mock tools for now - will be replaced with API call
  const mockTools = [
    {
      id: 'azure-devops',
      name: 'Azure DevOps Process Creation',
      description: 'Create and manage Azure DevOps process templates',
      icon: <AccountTreeIcon fontSize="large" />,
      status: 'available',
      url: '/tools/azure-devops'
    },
    {
      id: 'fasttrack',
      name: 'Fasttrack Process Model Import',
      description: 'Import and manage Fasttrack process models',
      icon: <SpeedIcon fontSize="large" />,
      status: 'available',
      url: '/tools/fasttrack'
    }
  ];

  useEffect(() => {
    // TODO: Replace with actual API call
    setTools(mockTools);
  }, []);

  const handleMenuOpen = (event) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
  };

  const handleToolClick = (tool) => {
    if (tool.status === 'available') {
      window.open(tool.url, '_blank');
    }
  };

  return (
    <>
      <AppBar position="static" className="header">
        <Toolbar>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            <Box className="machete-logo">
              🔪 MACHETE
            </Box>
            <Typography variant="subtitle1" sx={{ opacity: 0.8 }}>
              Multi-purpose Automation & Configuration Hub for Engineering Tools and Execution
            </Typography>
          </Typography>
          <IconButton
            color="inherit"
            onClick={handleMenuOpen}
          >
            <SettingsIcon />
          </IconButton>
          <Menu
            anchorEl={anchorEl}
            open={Boolean(anchorEl)}
            onClose={handleMenuClose}
          >
            <MenuItem onClick={() => { handleMenuClose(); navigate('/tools'); }}>
              Tool Registry
            </MenuItem>
            <MenuItem onClick={handleMenuClose}>
              Settings
            </MenuItem>
          </Menu>
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography variant="h4" gutterBottom align="center">
          Available Tools
        </Typography>
        
        <Grid container spacing={3} sx={{ mt: 2 }}>
          {tools.map((tool) => (
            <Grid item xs={12} sm={6} md={4} key={tool.id}>
              <Card 
                className="tool-card"
                onClick={() => handleToolClick(tool)}
                sx={{ 
                  height: '100%',
                  opacity: tool.status === 'available' ? 1 : 0.5,
                  cursor: tool.status === 'available' ? 'pointer' : 'not-allowed'
                }}
              >
                <CardContent sx={{ textAlign: 'center', p: 3 }}>
                  <Box sx={{ color: 'primary.main', mb: 2 }}>
                    {tool.icon}
                  </Box>
                  <Typography variant="h6" gutterBottom>
                    {tool.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {tool.description}
                  </Typography>
                  <Typography 
                    variant="caption" 
                    sx={{ 
                      mt: 2, 
                      display: 'block',
                      color: tool.status === 'available' ? 'success.main' : 'warning.main'
                    }}
                  >
                    {tool.status.toUpperCase()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
          
          {/* Add New Tool Card */}
          <Grid item xs={12} sm={6} md={4}>
            <Card 
              className="tool-card"
              onClick={() => navigate('/tools')}
              sx={{ 
                height: '100%',
                border: '2px dashed',
                borderColor: 'primary.main',
                backgroundColor: 'transparent'
              }}
            >
              <CardContent sx={{ textAlign: 'center', p: 3 }}>
                <Box sx={{ color: 'primary.main', mb: 2 }}>
                  <CloudDownloadIcon fontSize="large" />
                </Box>
                <Typography variant="h6" gutterBottom>
                  Install New Tool
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  Add new tools from Git repositories
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Container>
    </>
  );
};

export default Dashboard;
