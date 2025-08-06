#!/bin/bash

# MACHETE Platform Setup Script
# This script sets up the MACHETE platform on a host system

set -e

echo "🔪 Setting up MACHETE Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "   Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "   Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

# Create required directories
echo "📁 Creating required directories..."
mkdir -p ./data
mkdir -p ./tools
mkdir -p ./core/caddy/data
mkdir -p ./core/caddy/config

# Set permissions
echo "🔧 Setting permissions..."
chmod -R 755 ./data
chmod -R 755 ./tools

# Build and start the platform
echo "🏗️ Building and starting MACHETE platform..."
docker-compose build
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check if services are running
echo "🔍 Checking service health..."
if docker-compose ps | grep -q "Up"; then
    echo "✅ MACHETE platform is running successfully!"
    echo ""
    echo "🌐 Access the platform at: http://localhost:8080"
    echo "📚 API documentation at: http://localhost:8080/api/health"
    echo ""
    echo "📊 View running containers:"
    docker-compose ps
else
    echo "❌ Some services failed to start. Check the logs:"
    docker-compose logs
    exit 1
fi

echo ""
echo "🎉 MACHETE platform setup complete!"
echo ""
echo "Next steps:"
echo "1. Open http://localhost:8080 in your browser"
echo "2. Use the Tool Registry to install new tools"
echo "3. Check the documentation in the docs/ folder"
