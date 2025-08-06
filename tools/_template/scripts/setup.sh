#!/bin/bash

# MACHETE Tool Setup Script
# This script runs during tool installation in MACHETE

echo "🔧 Setting up My Awesome Tool..."

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p /app/data/uploads
mkdir -p /app/data/cache
mkdir -p /app/logs
mkdir -p /app/config

# Set proper permissions
echo "🔒 Setting permissions..."
chmod 755 /app/data
chmod 755 /app/logs
chmod 755 /app/config

# Initialize configuration if it doesn't exist
if [ ! -f /app/config/tool.json ]; then
    echo "⚙️ Creating default configuration..."
    cat > /app/config/tool.json << EOF
{
  "name": "My Awesome Tool",
  "version": "1.0.0",
  "settings": {
    "maxCacheSize": "100MB",
    "logLevel": "info",
    "enableMetrics": true
  },
  "features": {
    "autoBackup": false,
    "notifications": true
  }
}
EOF
fi

# Initialize database or data files if needed
if [ ! -f /app/data/initialized ]; then
    echo "🗄️ Initializing data storage..."
    
    # Example: Create initial data structure
    echo "[]" > /app/data/items.json
    echo "{}" > /app/data/metadata.json
    
    # Mark as initialized
    touch /app/data/initialized
    echo "Initialized at $(date)" > /app/data/initialized
fi

# Set up logging
echo "📝 Configuring logging..."
if [ ! -f /app/logs/app.log ]; then
    touch /app/logs/app.log
    chmod 644 /app/logs/app.log
fi

# Install any additional tools or dependencies
echo "📦 Checking additional dependencies..."

# Example: Install system packages if needed
# apk add --no-cache curl jq

# Run any initialization commands
echo "🚀 Running initialization..."

# Example: Database setup, cache warming, etc.
# npm run init-db
# npm run warm-cache

echo "✅ Setup complete!"
echo "🎉 My Awesome Tool is ready to use!"

# Output setup summary
echo ""
echo "📋 Setup Summary:"
echo "   - Data directory: /app/data"
echo "   - Config directory: /app/config"
echo "   - Logs directory: /app/logs"
echo "   - Initialized: $(cat /app/data/initialized)"
echo ""
echo "🔗 Access your tool at: http://localhost:8080"
echo "🏥 Health check: http://localhost:8080/health"
