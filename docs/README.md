# Eazeily Documentation

This directory contains comprehensive documentation for Eazeily, the AI-powered social media content generator.

## Core Documentation

### 📖 [User Journey Documentation](user-journey.md)
**Complete end-to-end flow from profile setup through content generation**

Covers:
- Full user flow: Profile completion → DB save → Generator dashboard → Gemini prompt → Content output
- Current pain points and known issues
- Comprehensive QA checklist
- Technical data flow diagrams
- Content type taxonomy
- Platform support matrix

### 🚀 Setup & Configuration

- [Gemini Setup Guide](GEMINI_SETUP.md) - Configure Google Gemini API for AI-powered content generation
- [Gemini Quick Start](GEMINI_QUICK_START.md) - Fast setup guide for Gemini API

### 🔧 Development

- [Content Generation API](CONTENT_GENERATION_API.md) - API reference for content generation endpoints
- [Prompt Compiler](PROMPT_COMPILER.md) - How prompts are constructed and compiled
- [Flow Comparison](FLOW_COMPARISON.md) - Compare different content generation flows

### 📦 Deployment & Operations

- [Runbooks](runbooks/) - Operational runbooks for production deployment
  - [Priority 0 Runbook](runbooks/priority0.md) - Critical production setup
  - [Deploy to App Engine](runbooks/deploy-appengine.md) - GCP App Engine deployment
  - [Production Secrets](runbooks/production_secrets.md) - Secret management
  - [Railway & GAE Secrets](runbooks/railway_gae_secrets.md) - Multi-platform secrets

### 📝 Project Management

- [Branching Strategy](branching.md) - Git workflow and branching conventions
- [GitHub Workflow](github_workflow.md) - CI/CD and GitHub automation
- [Changelog](changelog.md) - Version history and changes
- [Branch Sync Plan](branch_sync_plan.md) - Strategy for syncing branches
- [Staging Delivery Plan](staging_delivery_plan.md) - Staging environment delivery

### 🎨 UX & Features

- [Mobile UX Improvements](MOBILE_UX_IMPROVEMENTS.md) - Mobile optimization guide
- [Quality Builder Summary](QUALITY_BUILDER_SUMMARY.md) - Content quality features

### ✅ Completion Status

- [Implementation Complete](IMPLEMENTATION_COMPLETE.md) - Completed features and milestones

## Additional Documentation

For additional documentation, see the root-level docs:

- [README.md](../README.md) - Main project README
- [TESTING.md](../TESTING.md) - Testing guide
- [SECURITY.md](../SECURITY.md) - Security guidelines
- [LAUNCH_CHECKLIST.md](../LAUNCH_CHECKLIST.md) - Production launch checklist
- [DEPLOYMENT.md](../DEPLOYMENT.md) - Deployment procedures

## Quick Start

1. **New to the project?** Start with [User Journey Documentation](user-journey.md) to understand the full user experience
2. **Setting up AI?** See [Gemini Quick Start](GEMINI_QUICK_START.md)
3. **Deploying?** Check [runbooks/priority0.md](runbooks/priority0.md)
4. **Contributing?** Review [GitHub Workflow](github_workflow.md) and [Branching Strategy](branching.md)
