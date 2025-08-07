import React, { useState, useEffect } from 'react';
import { systemAPI, toolsAPI, apiUtils } from './services/api';

function SimpleApp() {
  const [systemHealth, setSystemHealth] = useState(null);
  const [tools, setTools] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadSystemData();
  }, []);

  const loadSystemData = async () => {
    try {
      setLoading(true);
      setError(null);

      // Load system health and tools in parallel
      const [healthResponse, toolsResponse] = await Promise.all([
        systemAPI.getHealth().catch(() => null),
        toolsAPI.getAll().catch(() => ({ data: [] }))
      ]);

      setSystemHealth(healthResponse?.data || null);
      setTools(toolsResponse.data || []);
    } catch (err) {
      console.error('Error loading system data:', err);
      setError(apiUtils.handleError(err, 'Failed to load system data'));
    } finally {
      setLoading(false);
    }
  };

  const testApiConnection = async () => {
    try {
      const response = await toolsAPI.test();
      alert(`API Test Successful: ${response.data.message}`);
    } catch (error) {
      alert(`API Test Failed: ${apiUtils.handleError(error)}`);
    }
  };

  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🔪 MACHETE Platform</h1>
      <p>Welcome to the MACHETE Platform - Your hub for engineering tools and automation!</p>
      
      {loading && (
        <div style={{ 
          border: '1px solid #ccc', 
          padding: '20px', 
          margin: '20px 0',
          backgroundColor: '#f0f0f0'
        }}>
          <h2>⏳ Loading...</h2>
          <p>Connecting to MACHETE API...</p>
        </div>
      )}

      {error && (
        <div style={{ 
          border: '1px solid #ff6b6b', 
          padding: '20px', 
          margin: '20px 0',
          backgroundColor: '#ffe0e0'
        }}>
          <h2>⚠️ Error</h2>
          <p>{error}</p>
          <button onClick={loadSystemData}>Retry</button>
        </div>
      )}

      {!loading && !error && (
        <>
          {/* System Health Status */}
          <div style={{ 
            border: '1px solid #4caf50', 
            padding: '20px', 
            margin: '20px 0',
            backgroundColor: '#e8f5e8'
          }}>
            <h2>✅ System Status</h2>
            {systemHealth ? (
              <>
                <p><strong>Status:</strong> {systemHealth.status}</p>
                <p><strong>Version:</strong> {systemHealth.version}</p>
                <p><strong>Timestamp:</strong> {new Date(systemHealth.timestamp).toLocaleString()}</p>
              </>
            ) : (
              <p>System health data unavailable</p>
            )}
          </div>

          {/* Tools Overview */}
          <div style={{ 
            border: '1px solid #2196f3', 
            padding: '20px', 
            margin: '20px 0',
            backgroundColor: '#e3f2fd'
          }}>
            <h2>🔧 Tools Overview</h2>
            {tools.length > 0 ? (
              <>
                <p><strong>Total Tools:</strong> {tools.length}</p>
                <p><strong>Running:</strong> {tools.filter(t => t.status === 'running').length}</p>
                <p><strong>Stopped:</strong> {tools.filter(t => t.status === 'stopped').length}</p>
                <div style={{ marginTop: '15px' }}>
                  <h3>Installed Tools:</h3>
                  <ul>
                    {tools.map(tool => (
                      <li key={tool.id}>
                        <strong>{tool.display_name || tool.name}</strong> 
                        <span style={{ 
                          marginLeft: '10px',
                          padding: '2px 8px',
                          borderRadius: '12px',
                          fontSize: '12px',
                          backgroundColor: tool.status === 'running' ? '#4caf50' : '#ff9800',
                          color: 'white'
                        }}>
                          {tool.status}
                        </span>
                        {tool.port && (
                          <span style={{ marginLeft: '10px', fontSize: '12px', color: '#666' }}>
                            :{tool.port}
                          </span>
                        )}
                      </li>
                    ))}
                  </ul>
                </div>
              </>
            ) : (
              <p>No tools installed yet. <a href="/tools">Install your first tool</a></p>
            )}
          </div>

          {/* API Test */}
          <div style={{ 
            border: '1px solid #ff9800', 
            padding: '20px', 
            margin: '20px 0',
            backgroundColor: '#fff3e0'
          }}>
            <h2>🧪 API Testing</h2>
            <p>Test the connection to the MACHETE API backend:</p>
            <button 
              onClick={testApiConnection}
              style={{
                padding: '10px 20px',
                backgroundColor: '#ff9800',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer'
              }}
            >
              Test API Connection
            </button>
          </div>

          {/* Navigation */}
          <div style={{ 
            border: '1px solid #9c27b0', 
            padding: '20px', 
            margin: '20px 0',
            backgroundColor: '#f3e5f5'
          }}>
            <h2>🚀 Quick Navigation</h2>
            <div style={{ display: 'flex', gap: '10px', flexWrap: 'wrap' }}>
              <a 
                href="/" 
                style={{
                  padding: '10px 15px',
                  backgroundColor: '#9c27b0',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '4px'
                }}
              >
                Dashboard
              </a>
              <a 
                href="/tools" 
                style={{
                  padding: '10px 15px',
                  backgroundColor: '#9c27b0',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '4px'
                }}
              >
                Tool Registry
              </a>
              <a 
                href="http://localhost:8080/api/docs" 
                target="_blank" 
                rel="noopener noreferrer"
                style={{
                  padding: '10px 15px',
                  backgroundColor: '#9c27b0',
                  color: 'white',
                  textDecoration: 'none',
                  borderRadius: '4px'
                }}
              >
                API Documentation
              </a>
            </div>
          </div>
        </>
      )}

      {/* Debug Information */}
      <div style={{ 
        border: '1px solid #ccc', 
        padding: '20px', 
        margin: '20px 0',
        backgroundColor: '#f0f0f0'
      }}>
        <h2>🔍 Debug Information</h2>
        <p>React is rendering successfully</p>
        <p>Date: {new Date().toISOString()}</p>
        <p>Frontend: <strong>Connected</strong></p>
        <p>Backend API: <strong>{systemHealth ? 'Connected' : 'Disconnected'}</strong></p>
        <button 
          onClick={loadSystemData}
          style={{
            padding: '5px 10px',
            backgroundColor: '#007bff',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            marginTop: '10px'
          }}
        >
          Refresh Data
        </button>
      </div>
    </div>
  );
}

export default SimpleApp;
