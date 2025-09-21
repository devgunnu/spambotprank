#!/bin/bash

# Spam Detection Functions Server Setup Script

echo "Setting up Spam Detection Functions Server..."

# Create necessary directories
mkdir -p data/uploads
mkdir -p models

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your configuration"
fi

# Install Python dependencies
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Start Qdrant using Docker (optional)
echo ""
echo "To start Qdrant database, run:"
echo "docker run -p 6333:6333 -v \$(pwd)/qdrant_storage:/qdrant/storage qdrant/qdrant"
echo ""

# Instructions
echo "Setup complete!"
echo ""
echo "To start the servers:"
echo "1. Start Qdrant RAG server: cd rag && python qdrant_rag_server.py"
echo "2. Start main server: python app.py"
echo ""
echo "Health checks:"
echo "- Main server: http://localhost:5000/health"
echo "- RAG server: http://localhost:6334/health"