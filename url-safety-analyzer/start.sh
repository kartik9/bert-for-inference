#!/bin/bash

# URL Safety Analyzer Startup Script

echo "🛡️  URL Trust & Safety Analysis Platform"
echo "========================================"
echo ""

# Check if backend .env exists
if [ ! -f "backend/.env" ]; then
    echo "⚠️  Warning: backend/.env not found!"
    echo "Creating from template..."
    cp backend/.env.example backend/.env
    echo ""
    echo "📝 Please edit backend/.env and add your API key:"
    echo "   - OPENAI_API_KEY for GPT-4, or"
    echo "   - ANTHROPIC_API_KEY for Claude"
    echo ""
    read -p "Press Enter after configuring .env to continue..."
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python found"

# Install backend dependencies
echo ""
echo "📦 Installing backend dependencies..."
cd backend
pip install -q -r requirements.txt
if [ $? -ne 0 ]; then
    echo "❌ Failed to install backend dependencies"
    exit 1
fi
echo "✓ Backend dependencies installed"

cd ..

# Start backend in background
echo ""
echo "🚀 Starting backend server..."
cd backend
python main.py &
BACKEND_PID=$!
echo "✓ Backend running (PID: $BACKEND_PID) on http://localhost:8000"

cd ..

# Wait for backend to start
echo ""
echo "⏳ Waiting for backend to initialize..."
sleep 3

# Start frontend
echo ""
echo "🚀 Starting frontend server..."
cd frontend
python server.py &
FRONTEND_PID=$!
echo "✓ Frontend running (PID: $FRONTEND_PID) on http://localhost:3000"

cd ..

echo ""
echo "=========================================="
echo "✅ Application is running!"
echo ""
echo "🌐 Open your browser and navigate to:"
echo "   http://localhost:3000"
echo ""
echo "📚 API Documentation:"
echo "   http://localhost:8000/docs"
echo ""
echo "To stop the application:"
echo "   kill $BACKEND_PID $FRONTEND_PID"
echo "   or press Ctrl+C (may need to run twice)"
echo "=========================================="

# Wait for user interrupt
trap "echo ''; echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit 0" INT

# Keep script running
wait
