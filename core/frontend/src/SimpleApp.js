import React from 'react';

function SimpleApp() {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>🔪 MACHETE Platform</h1>
      <p>Simple version is working!</p>
      <div style={{ 
        border: '1px solid #ccc', 
        padding: '20px', 
        margin: '20px 0',
        backgroundColor: '#f0f0f0'
      }}>
        <h2>Debug Information</h2>
        <p>React is rendering successfully</p>
        <p>Date: {new Date().toISOString()}</p>
      </div>
    </div>
  );
}

export default SimpleApp;
