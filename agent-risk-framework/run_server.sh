#!/bin/bash
# Quick start script for the AI Agent Risk Assessment Framework

echo "🚀 Starting AI Agent Risk Assessment Framework API..."
echo ""

# Activate virtual environment
source venv/bin/activate

# Run the server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
