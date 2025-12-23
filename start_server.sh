#!/bin/bash
# Simple startup script for Togetherly Flask app

echo "Starting Togetherly Flask server..."
echo "Make sure you're in the project root directory"
echo ""

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Virtual environment not found. Run setup first:"
    echo "python3 -m venv .venv"
    echo "source .venv/bin/activate"
    echo "pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Set development environment
export FLASK_ENV=development
export PORT=5001

# Start the server
echo "🚀 Starting Flask server on port 5001..."
echo "Visit: http://localhost:5001"
echo "Press Ctrl+C to stop"
echo ""

nohup python3 app.py > server.log 2>&1 &