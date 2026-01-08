#!/bin/bash
# Pre-Deployment Validation Script for PR180+
# This script automates pre-deployment checks to prevent regressions
# Usage: ./scripts/pre_deployment_check.sh [staging|production]

set -e  # Exit on any error

ENVIRONMENT=${1:-staging}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASSED=0
FAILED=0
WARNINGS=0

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Pre-Deployment Validation for ${ENVIRONMENT}${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to print test results
pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASSED++))
}

fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAILED++))
}

warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARNINGS++))
}

info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Change to project root
cd "$PROJECT_ROOT"

# 1. Check Git Status
echo ""
echo -e "${BLUE}1. Checking Git Status...${NC}"
if [ -n "$(git status --porcelain)" ]; then
    warn "Working directory has uncommitted changes"
    git status --short
else
    pass "Working directory is clean"
fi

# 2. Check Current Branch
echo ""
echo -e "${BLUE}2. Checking Current Branch...${NC}"
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
info "Current branch: $CURRENT_BRANCH"

if [ "$ENVIRONMENT" = "production" ]; then
    if [ "$CURRENT_BRANCH" != "main" ]; then
        warn "Not on main branch (production deploys from main)"
    else
        pass "On main branch"
    fi
elif [ "$ENVIRONMENT" = "staging" ]; then
    if [ "$CURRENT_BRANCH" != "staging" ]; then
        warn "Not on staging branch (staging deploys from staging)"
    else
        pass "On staging branch"
    fi
fi

# 3. Check for merge conflicts
echo ""
echo -e "${BLUE}3. Checking for Merge Conflicts...${NC}"
if git diff --check > /dev/null 2>&1; then
    pass "No merge conflict markers found"
else
    fail "Merge conflict markers detected"
fi

# 4. Check Python environment
echo ""
echo -e "${BLUE}4. Checking Python Environment...${NC}"
if [ -d ".venv" ]; then
    pass "Virtual environment exists"
else
    fail "Virtual environment not found - run: python3 -m venv .venv"
fi

# Activate virtual environment if it exists
if [ -f ".venv/bin/activate" ]; then
    source .venv/bin/activate
    pass "Virtual environment activated"
else
    fail "Cannot activate virtual environment"
fi

# Check Python version
PYTHON_VERSION=$(python --version 2>&1 | awk '{print $2}')
info "Python version: $PYTHON_VERSION"

# 5. Check Dependencies
echo ""
echo -e "${BLUE}5. Checking Dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pass "requirements.txt exists"
    
    # Try to import critical packages
    if python -c "import flask" 2>/dev/null; then
        pass "Flask is installed"
    else
        fail "Flask is not installed - run: pip install -r requirements.txt"
    fi
    
    if python -c "import flask_sqlalchemy" 2>/dev/null; then
        pass "Flask-SQLAlchemy is installed"
    else
        fail "Flask-SQLAlchemy is not installed"
    fi
    
    if python -c "import google.generativeai" 2>/dev/null; then
        pass "Google Generative AI is installed"
    else
        warn "Google Generative AI is not installed (optional)"
    fi
else
    fail "requirements.txt not found"
fi

# 6. Check Environment Variables
echo ""
echo -e "${BLUE}6. Checking Environment Variables...${NC}"

# Check for .env file
if [ -f ".env" ]; then
    pass ".env file exists"
    source .env 2>/dev/null || true
else
    warn ".env file not found (using environment variables)"
fi

# Check critical environment variables
check_env_var() {
    VAR_NAME=$1
    REQUIRED=$2
    
    if [ -n "${!VAR_NAME}" ]; then
        pass "$VAR_NAME is set"
    else
        if [ "$REQUIRED" = "required" ]; then
            fail "$VAR_NAME is not set (required)"
        else
            warn "$VAR_NAME is not set (optional)"
        fi
    fi
}

check_env_var "SECRET_KEY" "required"
check_env_var "DATABASE_URL" "optional"
check_env_var "STRIPE_SECRET_KEY" "optional"
check_env_var "STRIPE_PUBLISHABLE_KEY" "optional"
check_env_var "GENAI_API_KEY" "optional"

# 7. Run Linting
echo ""
echo -e "${BLUE}7. Running Linting (flake8)...${NC}"
if command -v flake8 > /dev/null 2>&1; then
    if flake8 --max-line-length=120 --exclude=.venv,venv,archive 2>&1 | head -20; then
        pass "Linting passed"
    else
        warn "Linting has warnings (see above)"
    fi
else
    warn "flake8 not installed - skipping lint check"
fi

# 8. Run Unit Tests
echo ""
echo -e "${BLUE}8. Running Unit Tests...${NC}"
if [ -f "pytest.ini" ] || [ -d "tests" ]; then
    info "Running pytest (excluding e2e and ui_smoke tests)..."
    if PYTHONPATH=. pytest -q -k "not e2e and not ui_smoke" --maxfail=5 2>&1 | tail -20; then
        pass "Unit tests passed"
    else
        fail "Unit tests failed (see above)"
    fi
else
    warn "No test configuration found"
fi

# 9. Check Database Migrations
echo ""
echo -e "${BLUE}9. Checking Database Migrations...${NC}"
if [ -d "alembic" ]; then
    pass "Alembic migrations directory exists"
    
    if command -v alembic > /dev/null 2>&1; then
        info "Checking migration status..."
        alembic current 2>&1 | head -5 || warn "Could not check migration status"
        
        # Check for pending migrations
        if alembic upgrade head --sql > /dev/null 2>&1; then
            pass "No migration errors detected"
        else
            warn "Potential migration issues detected"
        fi
    else
        warn "Alembic not installed - cannot check migrations"
    fi
else
    info "No Alembic migrations directory found"
fi

# 10. Check for Security Issues
echo ""
echo -e "${BLUE}10. Checking for Security Issues...${NC}"

# Check for hardcoded secrets (basic check)
if git grep -i "password.*=.*['\"]" -- "*.py" > /dev/null 2>&1; then
    warn "Potential hardcoded passwords found in Python files"
else
    pass "No obvious hardcoded passwords in Python files"
fi

if git grep -i "api[_-]key.*=.*['\"]" -- "*.py" > /dev/null 2>&1; then
    warn "Potential hardcoded API keys found in Python files"
else
    pass "No obvious hardcoded API keys in Python files"
fi

# Check for .env in git
if git ls-files | grep -q "^\.env$"; then
    fail ".env file is tracked in git (should be in .gitignore)"
else
    pass ".env file is not tracked in git"
fi

# 11. Check Documentation
echo ""
echo -e "${BLUE}11. Checking Documentation...${NC}"
if [ -f "CHANGELOG.md" ]; then
    pass "CHANGELOG.md exists"
    
    # Check if CHANGELOG was updated in the last commit
    if git diff HEAD~1 HEAD --name-only | grep -q "CHANGELOG.md"; then
        pass "CHANGELOG.md was updated in the last commit"
    else
        warn "CHANGELOG.md was not updated recently"
    fi
else
    warn "CHANGELOG.md not found"
fi

# 12. Test Health Endpoint (if server is running)
echo ""
echo -e "${BLUE}12. Testing Local Health Endpoint...${NC}"
PORT=${PORT:-5001}
if curl -s "http://127.0.0.1:$PORT/health" > /dev/null 2>&1; then
    HEALTH_RESPONSE=$(curl -s "http://127.0.0.1:$PORT/health")
    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        pass "Local health endpoint responding"
    else
        warn "Health endpoint responded but status unclear"
    fi
else
    info "Local server not running (skip this check if not needed)"
fi

# 13. Check Deployment Configuration
echo ""
echo -e "${BLUE}13. Checking Deployment Configuration...${NC}"
if [ -f ".github/workflows/deploy-railway.yml" ]; then
    pass "Railway deployment workflow exists"
else
    warn "Railway deployment workflow not found"
fi

if [ -f "Procfile" ]; then
    pass "Procfile exists"
else
    warn "Procfile not found (may be needed for deployment)"
fi

if [ -f "requirements.txt" ]; then
    pass "requirements.txt exists"
else
    fail "requirements.txt not found"
fi

# Summary
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}Summary${NC}"
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Passed:${NC}   $PASSED"
echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
echo -e "${RED}Failed:${NC}   $FAILED"
echo ""

if [ $FAILED -eq 0 ]; then
    if [ $WARNINGS -eq 0 ]; then
        echo -e "${GREEN}✓ All checks passed! Ready for deployment to $ENVIRONMENT.${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ Some warnings were found. Review them before deploying to $ENVIRONMENT.${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ Some checks failed. Fix the issues before deploying to $ENVIRONMENT.${NC}"
    exit 1
fi
