/**
 * API service for MACHETE Platform
 * Handles all communication with the backend API
 */

import axios from 'axios';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: 'http://localhost:3001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
api.interceptors.request.use(
  (config) => {
    console.log(`🌐 API Request: ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('❌ API Request Error:', error);
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => {
    console.log(`✅ API Response: ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    console.error('❌ API Response Error:', {
      status: error.response?.status,
      url: error.config?.url,
      message: error.message,
      data: error.response?.data
    });
    return Promise.reject(error);
  }
);

// API endpoints
export const toolsAPI = {
  // Get all tools
  getAll: () => api.get('/tools/'),
  
  // Get tool by ID
  getById: (id) => api.get(`/tools/${id}`),
  
  // Install new tool
  install: (toolData) => api.post('/tools/install', toolData),
  
  // Update tool
  update: (id, toolData) => api.patch(`/tools/${id}`, toolData),
  
  // Delete tool
  delete: (id) => api.delete(`/tools/${id}`),
  
  // Start tool
  start: (id) => api.post(`/tools/${id}/start`),
  
  // Stop tool
  stop: (id) => api.post(`/tools/${id}/stop`),
  
  // Get tool status
  getStatus: (id) => api.get(`/tools/${id}/status`),
  
  // Get tool health
  getHealth: (id) => api.get(`/tools/${id}/health`),
  
  // Get tool logs
  getLogs: (id) => api.get(`/tools/${id}/logs`),
  
  // Test endpoint
  test: () => api.get('/tools/test'),
};

export const systemAPI = {
  // Get system health
  getHealth: () => api.get('/health'),
  
  // Get system diagnostics
  getDiagnostics: () => api.get('/system/diagnostics'),
};

// Utility functions
export const apiUtils = {
  // Handle API errors with user-friendly messages
  handleError: (error, defaultMessage = 'An error occurred') => {
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }
    if (error.response?.data?.message) {
      return error.response.data.message;
    }
    if (error.message) {
      return error.message;
    }
    return defaultMessage;
  },
  
  // Check if API is available
  isApiAvailable: async () => {
    try {
      await systemAPI.getHealth();
      return true;
    } catch (error) {
      return false;
    }
  },
};

export default api;
