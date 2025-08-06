#!/bin/bash

# Tool Installation Script
# This script is called by MACHETE when installing the tool

set -e

echo "Installing Example Tool..."

# Check dependencies
if ! command -v node &> /dev/null; then
    echo "Node.js is required but not installed."
    exit 1
fi

# Install npm dependencies
if [ -f "package.json" ]; then
    echo "Installing npm dependencies..."
    npm install --production
fi

# Create required directories
mkdir -p ./data
mkdir -p ./logs

# Set permissions
chmod -R 755 ./data
chmod -R 755 ./logs

# Run any setup commands
echo "Running setup commands..."
# Add your setup commands here

echo "Installation complete!"
