@echo off
REM Quick start script for the AI Agent Risk Assessment Framework (Windows)

echo 🚀 Starting AI Agent Risk Assessment Framework API...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Run the server (exclude venv and __pycache__ from watching)
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --reload-exclude "venv/*" --reload-exclude "**/__pycache__/*"
