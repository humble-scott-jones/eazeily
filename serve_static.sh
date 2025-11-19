#!/bin/bash
# Simple script to serve the static HTML launch page

echo "Serving Togetherly static launch page..."
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Please install Python 3."
    exit 1
fi

# Set port (default 8000 for static serving)
PORT=${PORT:-8000}

echo "🌐 Serving static files on port $PORT"
echo "Visit: http://localhost:$PORT/swelly-launch-static.html"
echo "Press Ctrl+C to stop"
echo ""

# Use Python's built-in HTTP server
cd /Users/daniellejones/Documents/togetherly_v2
python3 -m http.server $PORT