#!/bin/bash
echo "🚀 Deploying Swelly Landing Page to Railway..."

# Check if railway CLI is installed
if ! command -v railway &> /dev/null; then
    echo "Installing Railway CLI..."
    npm install -g @railway/cli
fi

# Login to Railway (if not already logged in)
railway login

# Create new project (just run railway init without project name)
echo "Creating new Railway project..."
railway init

# Deploy
echo "Deploying to Railway..."
railway up

echo "✅ Deployment complete!"
echo "Get your URL with: railway domain"
