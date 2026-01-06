# Eazeily Hosting Guide

## Your Flask App Needs a Server

Your Eazeily application is a **full Flask web application** with:
- User authentication & accounts
- Database (SQLite)
- Payment processing (Stripe)
- Content generation features
- Admin dashboard

You **cannot** just host the static HTML file - you need to deploy the entire Python application.

## Quick Hosting Options

### 1. **Heroku** (Easiest - Free to start)
```bash
# Install Heroku CLI
brew install heroku/brew/heroku

# Login and create app
heroku login
heroku create swelly-app

# Set required environment variables
heroku config:set SECRET_KEY=your-random-secret-key-here
heroku config:set PORT=5000

# Optional: Add Stripe & OpenAI
heroku config:set STRIPE_SECRET_KEY=sk_test_...
heroku config:set GEMINI_API_KEY=sk-...

# Deploy
git add .
git commit -m "Ready for deployment"
git push heroku main
```

**Cost:** Free tier (550 hours/month), then $7+/month

### 2. **Railway** (Simple & Fast)
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Set environment variables in Railway dashboard
# SECRET_KEY, PORT=5000, etc.
```

**Cost:** $5/month (includes database)

### 3. **DigitalOcean App Platform** (Good balance)
- Connect your GitHub repo
- Automatic deployments
- Built-in database options

**Cost:** $12+/month

### 4. **Vercel** (Static parts only - NOT recommended)
Vercel only works for static sites. Your app needs a server for:
- User logins
- Database operations
- Payment processing

## Domain Setup (swellyapp.com)

### With Heroku:
```bash
# Add custom domain
heroku domains:add swellyapp.com
heroku domains:add www.swellyapp.com

# Get DNS target from Heroku
heroku domains

# At your domain registrar, add CNAME records:
# swellyapp.com -> [heroku-target].herokudns.com
# www.swellyapp.com -> [heroku-target].herokudns.com
```

### With Railway:
- Go to Settings → Domains
- Add `swellyapp.com`
- Update DNS records as instructed

## Required Environment Variables

Create a `.env` file locally and set these in your hosting platform:

```bash
# Required
SECRET_KEY=generate-a-random-string-here
PORT=5000
FLASK_ENV=production

# Optional - Payments
STRIPE_SECRET_KEY=sk_test_your_stripe_secret
STRIPE_PUBLISHABLE_KEY=pk_test_your_stripe_public
STRIPE_PRICE_ID=price_your_price_id

# Optional - AI Features
GEMINI_API_KEY=sk-your_openai_key

# Optional - Admin Access
ADMIN_EMAILS=your@email.com
```

## Database Considerations

Your app uses SQLite (works fine for small apps). For growth:
- Railway & DigitalOcean provide managed databases
- Heroku has Postgres add-ons
- Consider PostgreSQL for 1000+ users

## Testing Your Deployment

After deploying:

1. **Health Check:**
   ```bash
   curl https://swellyapp.com/health
   ```

2. **Test Key Features:**
   - Visit `https://swellyapp.com/`
   - Try creating an account
   - Test content generation (if paid features enabled)

3. **Check Logs:**
   ```bash
   # Heroku
   heroku logs --tail

   # Railway
   railway logs
   ```

## Cost Comparison

| Platform | Setup Time | Free Tier | Paid Plans | Best For |
|----------|------------|-----------|------------|----------|
| **Heroku** | 10 minutes | 550 hrs/month | $7+/month | Beginners |
| **Railway** | 5 minutes | $5 credit | $5+/month | Simple apps |
| **DigitalOcean** | 15 minutes | None | $12+/month | Full control |
| **Manual Server** | 1+ hours | None | $5-50+/month | Advanced |

## Quick Start with Heroku

1. **Install Heroku CLI:**
   ```bash
   brew install heroku/brew/heroku
   ```

2. **Prepare your app:**
   ```bash
   cd /Users/daniellejones/Documents/togetherly_v2
   echo "web: python app.py" > Procfile
   ```

3. **Deploy:**
   ```bash
   heroku login
   heroku create swelly-app
   heroku config:set SECRET_KEY=$(openssl rand -hex 32)
   heroku config:set PORT=5000
   git push heroku main
   ```

4. **Add domain:**
   ```bash
   heroku domains:add swellyapp.com
   # Then update DNS at your registrar
   ```

## Troubleshooting

### Common Issues:

1. **"Application Error" on Heroku:**
   ```bash
   heroku logs --tail
   # Look for Python errors
   ```

2. **Database errors:**
   - Check if SQLite file has write permissions
   - For production, consider PostgreSQL

3. **Static files not loading:**
   - Flask serves static files automatically
   - Check file paths in templates

4. **Payments not working:**
   - Verify Stripe keys are set correctly
   - Check webhook endpoints

### Debug Commands:

```bash
# Check app status
curl https://your-app.com/health

# View recent logs
heroku logs -n 100

# Check environment variables
heroku config

# Test database
heroku run python -c "import sqlite3; print('DB works')"
```

## Next Steps

1. Choose a hosting platform (I'd recommend **Railway** for simplicity)
2. Deploy your app
3. Set up your domain (swellyapp.com)
4. Test all features
5. Set up monitoring (optional)

Need help with any specific platform?