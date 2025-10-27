# Security Best Practices

## Overview

This document outlines security best practices, policies, and procedures for the Togetherly application.

## Security Principles

1. **Defense in Depth:** Multiple layers of security controls
2. **Least Privilege:** Minimum necessary permissions
3. **Fail Securely:** Secure defaults, fail closed
4. **Zero Trust:** Verify everything, trust nothing
5. **Security by Design:** Build security in from the start

## Authentication & Authorization

### Password Security

**Requirements:**
- Minimum 8 characters
- Use bcrypt/PBKDF2 for hashing (already implemented)
- Salt passwords (handled by werkzeug.security)
- Never store plaintext passwords

**Implementation:**
```python
from werkzeug.security import generate_password_hash, check_password_hash

# Hash password
password_hash = generate_password_hash(password, method='pbkdf2:sha256')

# Verify password
is_valid = check_password_hash(password_hash, password)
```

### Session Management

**Best Practices:**
- Use secure session cookies (HTTPOnly, Secure, SameSite)
- Implement session timeout (30 minutes idle, 24 hours absolute)
- Regenerate session ID after login
- Clear sessions on logout

**Configuration:**
```python
app.config.update(
    SESSION_COOKIE_SECURE=True,      # HTTPS only
    SESSION_COOKIE_HTTPONLY=True,    # No JavaScript access
    SESSION_COOKIE_SAMESITE='Lax',   # CSRF protection
    PERMANENT_SESSION_LIFETIME=3600  # 1 hour
)
```

### API Authentication

**Current:** Session-based authentication  
**Future Consideration:** JWT tokens for API access

**Best Practices:**
- Require authentication for sensitive endpoints
- Implement rate limiting
- Log authentication failures
- Block after N failed attempts

## Input Validation

### Always Validate User Input

**SQL Injection Prevention:**
- ✅ Use parameterized queries (already implemented)
- ❌ Never concatenate user input into SQL

```python
# ✅ Good - parameterized query
db.execute('SELECT * FROM users WHERE email = ?', (email,))

# ❌ Bad - SQL injection risk
db.execute(f'SELECT * FROM users WHERE email = "{email}"')
```

### XSS (Cross-Site Scripting) Prevention

**Jinja2 Auto-escaping:**
- Jinja2 auto-escapes by default (enabled in Flask)
- Never use `| safe` filter on user input
- Sanitize HTML if rich text is needed

**Content Security Policy:**
```python
@app.after_request
def set_security_headers(response):
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

### CSRF Protection

**Recommendations:**
- Use Flask-WTF for form CSRF tokens
- Check `Origin` header for API requests
- Implement SameSite cookie attribute

## Data Protection

### Sensitive Data Handling

**Never Log:**
- Passwords
- API keys
- Session tokens
- Credit card numbers (full PAN)
- Personal identifying information (PII) unless necessary

**Encryption:**
- ✅ Use HTTPS for all traffic (enforce in production)
- ✅ Encrypt secrets at rest (use environment variables)
- ✅ Use Stripe for payment processing (no CC storage)

### Database Security

**Best Practices:**
- Use prepared statements (already implemented)
- Encrypt database backups
- Limit database user permissions
- Regular security updates
- Enable database audit logging

**Connection Security:**
```python
# Use environment variables for database credentials
DATABASE_URL = os.getenv('DATABASE_URL')

# Use SSL for database connections in production
# postgresql://user:pass@host:5432/db?sslmode=require
```

### Secrets Management

**Current:** Environment variables  
**Production:** Use secrets management service

**Never:**
- Commit secrets to Git
- Hardcode API keys
- Share secrets via email/Slack

**Do:**
- Use `.env` file for local development (in `.gitignore`)
- Use GitHub Secrets for CI/CD
- Rotate secrets regularly
- Use separate secrets for each environment

## API Security

### Rate Limiting

Implement rate limiting to prevent abuse:

```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@app.route("/api/generate")
@limiter.limit("10 per minute")
def generate():
    # ...
```

### Input Size Limits

Prevent DoS attacks:
```python
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max request size
```

### CORS Configuration

**Current:** CORS enabled for all origins (development)  
**Production:** Restrict to specific origins

```python
from flask_cors import CORS

# Production configuration
CORS(app, origins=[
    "https://togetherly.app",
    "https://www.togetherly.app"
])
```

## Dependency Security

### Vulnerability Scanning

**CI/CD Integration:**
- `safety check` - scan for known vulnerabilities
- `pip-audit` - audit dependencies
- Run on every PR

**Local Development:**
```bash
# Check dependencies for vulnerabilities
pip install safety pip-audit

# Run safety check
safety check

# Run pip-audit
pip-audit
```

### Dependency Management

**Best Practices:**
- Pin dependency versions in `requirements.txt`
- Review changelogs before upgrading
- Use virtual environments
- Regularly update dependencies (weekly/monthly)

**Automated Updates:**
- Use Dependabot for automated security updates
- Review and test updates before merging

## Infrastructure Security

### HTTPS/TLS

**Requirements:**
- ✅ Use HTTPS for all traffic
- ✅ Use TLS 1.2 or higher
- ✅ Use strong cipher suites
- ✅ Enable HSTS (HTTP Strict Transport Security)

**Headers:**
```python
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response
```

### Environment Separation

**Environments:**
- Development: Local, loose security for testing
- Staging: Production-like, realistic data (sanitized)
- Production: Strict security, real customer data

**Separation:**
- Different databases for each environment
- Different API keys (Stripe test vs. live)
- Different authentication (no shared users)

## Logging and Monitoring

### Security Logging

**Events to Log:**
- Authentication attempts (success/failure)
- Authorization failures
- Input validation failures
- Security exceptions
- Admin actions
- Configuration changes

**Example:**
```python
import logging

logger = logging.getLogger('security')

@app.route('/api/auth/login', methods=['POST'])
def login():
    email = request.json.get('email')
    password = request.json.get('password')
    
    user = get_user_by_email(email)
    if not user or not check_password_hash(user['password_hash'], password):
        logger.warning(f'Failed login attempt for {email}', extra={
            'event': 'login_failure',
            'email': email,
            'ip': request.remote_addr
        })
        return jsonify({'error': 'Invalid credentials'}), 401
    
    logger.info(f'Successful login for {email}', extra={
        'event': 'login_success',
        'user_id': user['id'],
        'ip': request.remote_addr
    })
    # ...
```

### Security Monitoring

**Alerts for:**
- Multiple failed login attempts from same IP
- Unusual API usage patterns
- High error rates
- Suspicious database queries
- Unauthorized access attempts

## Incident Response

### Security Incident Process

1. **Detect:** Monitoring alerts, user reports, security scans
2. **Contain:** Isolate affected systems, disable compromised accounts
3. **Investigate:** Determine scope, root cause, affected data
4. **Remediate:** Fix vulnerability, patch systems, rotate secrets
5. **Communicate:** Notify affected users (if required by law)
6. **Learn:** Post-mortem, improve security controls

### Breach Notification

**Requirements:**
- GDPR: 72 hours to notify authorities if EU users affected
- CCPA: Reasonable timeframe for California residents
- Other jurisdictions may have specific requirements

**Prepare:**
- Incident response plan
- Communication templates
- Legal counsel contact
- PR/communications plan

## Compliance

### Data Privacy

**GDPR (EU):**
- Right to access data
- Right to deletion (right to be forgotten)
- Data portability
- Privacy by design

**CCPA (California):**
- Right to know what data is collected
- Right to deletion
- Right to opt-out of sale

**Implementation:**
```python
@app.route('/api/account/delete', methods=['POST'])
@login_required
def delete_account():
    """GDPR/CCPA: Right to deletion"""
    user_id = session.get('user_id')
    # Delete user data
    db.execute('DELETE FROM profiles WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM subscriptions WHERE user_id = ?', (user_id,))
    db.execute('DELETE FROM users WHERE id = ?', (user_id,))
    db.commit()
    return jsonify({'ok': True})
```

### Payment Security (PCI-DSS)

**Stripe Integration:**
- ✅ Never store credit card numbers
- ✅ Use Stripe.js for card collection
- ✅ Use Stripe's hosted checkout or Elements
- ✅ All payment data handled by Stripe (PCI-compliant)

**Reduced PCI Scope:**
- No card data touches our servers
- Stripe handles PCI compliance
- Only store Stripe customer/subscription IDs

## Security Checklist

### Development
- [ ] Input validation on all user input
- [ ] Parameterized queries (no SQL injection)
- [ ] Output encoding (no XSS)
- [ ] CSRF protection on forms
- [ ] Strong password hashing
- [ ] Secure session management
- [ ] No secrets in code
- [ ] Security headers configured

### Deployment
- [ ] HTTPS enforced (redirect HTTP to HTTPS)
- [ ] TLS 1.2+ configured
- [ ] Security headers in place
- [ ] Rate limiting enabled
- [ ] CORS properly configured
- [ ] Environment variables for secrets
- [ ] Database credentials secured
- [ ] Backup encryption enabled

### Monitoring
- [ ] Security logging enabled
- [ ] Failed login monitoring
- [ ] Unusual activity alerts
- [ ] Dependency vulnerability scanning
- [ ] Security audit trail
- [ ] Incident response plan
- [ ] Regular security reviews

### Ongoing
- [ ] Regular dependency updates
- [ ] Security patches applied promptly
- [ ] Penetration testing (annual)
- [ ] Security training for team
- [ ] Security incident drills
- [ ] Third-party security audits
- [ ] Compliance reviews

## Security Tools

### Development Tools
- `safety` - dependency vulnerability scanner
- `pip-audit` - Python package auditing
- `bandit` - Python security linter
- `flake8` - code quality and security checks

### Testing Tools
- `OWASP ZAP` - web application security scanner
- `sqlmap` - SQL injection testing
- `Burp Suite` - web security testing

### Monitoring Tools
- `fail2ban` - intrusion prevention
- `OSSEC` - host intrusion detection
- `ModSecurity` - web application firewall

## Resources

### Training
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Flask Security Considerations](https://flask.palletsprojects.com/en/latest/security/)

### Standards
- [NIST Cybersecurity Framework](https://www.nist.gov/cyberframework)
- [CIS Security Controls](https://www.cisecurity.org/controls/)
- [SANS Top 25](https://www.sans.org/top25-software-errors/)

### Compliance
- [GDPR](https://gdpr.eu/)
- [CCPA](https://oag.ca.gov/privacy/ccpa)
- [PCI-DSS](https://www.pcisecuritystandards.org/)

## Reporting Security Issues

**DO NOT** open public GitHub issues for security vulnerabilities.

**Instead:**
- Email security@ [domain] with details
- Include steps to reproduce
- Wait for acknowledgment before public disclosure
- We aim to respond within 24 hours

## Review Schedule

This security guide should be reviewed:
- Quarterly - routine review and updates
- After security incidents - lessons learned
- When adding new features - ensure security covered
- When regulations change - update compliance sections
