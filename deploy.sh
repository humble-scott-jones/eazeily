#!/bin/bash

# Swelly Deployment Script
# Run this to deploy to Heroku

echo "🚀 Swelly Deployment Script"
echo "=========================="

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo "❌ Heroku CLI not found. Install with: brew install heroku/brew/heroku"
    exit 1
fi

# Check if logged in to Heroku
if ! heroku whoami &> /dev/null; then
    echo "❌ Not logged in to Heroku. Run: heroku login"
    exit 1
fi

# Create Heroku app
echo "📦 Creating Heroku app..."
heroku create swelly-app --region us

# Set environment variables
echo "🔧 Setting environment variables..."
heroku config:set SECRET_KEY=$(openssl rand -hex 32)
heroku config:set PORT=5000
heroku config:set FLASK_ENV=production

# Ask for optional configurations
read -p "Do you have Stripe keys? (y/n): " has_stripe
if [ "$has_stripe" = "y" ]; then
    read -p "Enter STRIPE_SECRET_KEY: " stripe_secret
    read -p "Enter STRIPE_PUBLISHABLE_KEY: " stripe_public
    read -p "Enter STRIPE_PRICE_ID: " stripe_price

    heroku config:set STRIPE_SECRET_KEY=$stripe_secret
    heroku config:set STRIPE_PUBLISHABLE_KEY=$stripe_public
    heroku config:set STRIPE_PRICE_ID=$stripe_price
fi

read -p "Do you have OpenAI API key? (y/n): " has_openai
if [ "$has_openai" = "y" ]; then
    read -p "Enter OPENAI_API_KEY: " openai_key
    heroku config:set OPENAI_API_KEY=$openai_key
fi

# Deploy
echo "🚀 Deploying to Heroku..."
git push heroku main

# Check if deployment succeeded
if [ $? -eq 0 ]; then
    echo "✅ Deployment successful!"
    echo ""
    echo "🌐 Your app is live at: https://swelly-app.herokuapp.com"
    echo ""
    echo "📋 Next steps:"
    echo "1. Visit your app and test it"
    echo "2. Set up your custom domain (swellyapp.com)"
    echo "3. Run: heroku domains:add swellyapp.com"
    echo "4. Update DNS at your domain registrar"
    echo ""
    echo "🔍 Check logs with: heroku logs --tail"
    echo "🩺 Health check: curl https://swelly-app.herokuapp.com/health"
else
    echo "❌ Deployment failed. Check the logs above for errors."
    exit 1
fi