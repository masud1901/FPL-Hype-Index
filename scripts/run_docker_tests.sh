#!/bin/bash

# Phase 4 Docker Test Runner
# This script runs the Phase 4 tests inside Docker containers

set -e

echo "🚀 Starting Phase 4 Docker Tests"
echo "=================================="

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker and try again."
    exit 1
fi

# Check if docker-compose is available
if ! command -v docker compose > /dev/null 2>&1; then
    echo "❌ Docker Compose is not available. Please install Docker Compose and try again."
    exit 1
fi

echo "📋 Checking Docker Compose configuration..."

# Build the Docker image
echo "🔨 Building Docker image..."
docker compose build

# Start the database
echo "🗄️  Starting database..."
docker compose up -d database

# Wait for database to be ready
echo "⏳ Waiting for database to be ready..."
sleep 10

# Run the tests
echo "🧪 Running Phase 4 tests..."
docker compose --profile test run --rm test

# Get the exit code
EXIT_CODE=$?

echo ""
echo "=================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ All Phase 4 Docker tests passed!"
else
    echo "❌ Some Phase 4 Docker tests failed."
fi
echo "=================================="

# Clean up
echo "🧹 Cleaning up..."
docker compose down

exit $EXIT_CODE 