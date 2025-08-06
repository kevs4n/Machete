import React from 'react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('React Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div style={{ padding: '20px', textAlign: 'center' }}>
          <h1>🔧 MACHETE Platform</h1>
          <h2>Something went wrong loading the dashboard.</h2>
          <details style={{ whiteSpace: 'pre-wrap', textAlign: 'left', marginTop: '20px' }}>
            <summary>Error Details</summary>
            {this.state.error && this.state.error.toString()}
          </details>
          <button 
            onClick={() => window.location.reload()} 
            style={{ marginTop: '20px', padding: '10px 20px' }}
          >
            Reload Page
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
