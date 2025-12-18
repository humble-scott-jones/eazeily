# Google Cloud Platform Deployment for Swelly

## Quick Google App Engine Setup

### 1. Install Google Cloud SDK
```bash
# Download and install gcloud CLI
curl https://sdk.cloud.google.com | bash
exec -l $SHELL

# Initialize and login
gcloud init
gcloud auth login
```

### 2. Create GCP Project
```bash
# Create new project
gcloud projects create swelly-app

# Set as default
gcloud config set project swelly-app
```

### 3. Enable Required APIs
```bash
# Enable App Engine and Cloud Build
gcloud services enable appengine.googleapis.com
gcloud services enable cloudbuild.googleapis.com
```

### 4. Create App Engine App
```bash
# Create App Engine app (choose region)
gcloud app create --region=us-central
```

### 5. Deploy Your App
```bash
# Deploy to App Engine
gcloud app deploy

# Your app will be live at: https://swelly-app.uc.r.appspot.com
```

## Required Files for App Engine

Create `app.yaml` in your project root:

```yaml
runtime: python3
instance_class: F1
automatic_scaling:
  target_cpu_utilization: 0.65
  min_instances: 1
  max_instances: 3

handlers:
- url: /static
  static_dir: static
  secure: always

- url: /.*
  script: auto
  secure: always

env_variables:
  SECRET_KEY: "your-secret-key-here"
  FLASK_ENV: "production"
  PORT: "8080"
```

## Domain Setup (swellyapp.com)

### 1. Verify Domain Ownership
```bash
# Add domain to GCP
gcloud domains verify swellyapp.com
```

### 2. Map Custom Domain
```bash
# Map your domain
gcloud app domain-mappings create swellyapp.com
```

### 3. Update DNS Records
- Go to your domain registrar
- Add CNAME record: `www.swellyapp.com -> ghs.googlehosted.com`
- Add A records for root domain (check GCP console for values)

## Environment Variables

Set production environment variables:
```bash
# Stripe (if using payments)
gcloud app deploy --set-env-vars STRIPE_SECRET_KEY=sk_test_...,STRIPE_PUBLISHABLE_KEY=pk_test_...

# Gemini (if using AI features)
gcloud app deploy --set-env-vars GEMINI_API_KEY=your-gemini-api-key
```

## Cost Comparison: Google vs Other Platforms

| Platform | Free Tier | Paid Plans | Complexity | Best For |
|----------|-----------|------------|------------|----------|
| **Google App Engine** | 28 hours/month | $0.05/hour after | Medium | Google ecosystem users |
| **Heroku** | 550 hours/month | $7+/month | Low | Beginners |
| **Railway** | $5 credit | $5+/month | Low | Simple apps |
| **DigitalOcean** | None | $12+/month | Medium | Full control |

## Google App Engine Pros/Cons

### ✅ Pros:
- Scales automatically
- Integrated with other Google services
- Good performance
- Free SSL certificates
- Built-in monitoring

### ❌ Cons:
- More complex setup than Heroku/Railway
- Google Cloud billing can be confusing
- Cold starts can be slow
- Less beginner-friendly

## Alternative: Firebase Hosting (Static Only)

If you only want to host the static landing page (not the full app), use Firebase:

```bash
# Install Firebase CLI
npm install -g firebase-tools

# Initialize project
firebase init hosting

# Deploy static files
firebase deploy
```

**⚠️ Note:** Firebase Hosting is only for static sites. Your Flask app needs a server like App Engine.

## Recommendation

For your Flask application, I'd recommend **Railway** or **Heroku** over Google App Engine because:

1. **Simpler setup** - Less configuration required
2. **Better developer experience** - Easier to debug and manage
3. **Clearer pricing** - No complex GCP billing
4. **Faster deployment** - Less steps to get started

However, if you're already using Google services or want to learn GCP, App Engine is a solid choice.

Would you like me to help you set up Google App Engine, or would you prefer to stick with the simpler Heroku/Railway options?