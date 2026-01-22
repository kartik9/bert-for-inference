# Quick start script for the AI Agent Risk Assessment Framework (Windows)

Write-Host "🚀 Starting AI Agent Risk Assessment Framework API..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
& .\venv\Scripts\Activate.ps1

# Run the server
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
