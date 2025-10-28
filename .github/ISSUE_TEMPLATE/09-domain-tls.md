---
name: 🌐 Must-Have 9 - Domain, TLS, and Canonical Production URL
about: Domain setup, valid TLS certs, redirect rules, and canonical host config
title: '[LAUNCH] Domain, TLS, and Canonical Production URL'
labels: ['launch', 'infra', 'high-priority']
assignees: []
---

## Priority
**Must-Have #9** - Complete before launch

## Description
Set up production domain with valid TLS certificates, configure redirect rules, and ensure canonical URL configuration. Site must be reachable at production domain over HTTPS with correct metadata.

## Acceptance Criteria
- [ ] Production domain purchased and configured
- [ ] DNS records properly configured
- [ ] Valid TLS/SSL certificate installed
- [ ] HTTPS enforced (HTTP redirects to HTTPS)
- [ ] www and non-www redirect rules configured
- [ ] Canonical URL set correctly
- [ ] Site reachable at production domain over HTTPS
- [ ] OG/meta tags configured correctly
- [ ] SSL certificate auto-renewal configured
- [ ] Security headers configured (HSTS, CSP, etc.)

## Implementation Tasks
- [ ] Purchase/configure production domain
- [ ] Set up DNS records (A, AAAA, CNAME)
- [ ] Obtain SSL/TLS certificate (Let's Encrypt or managed)
- [ ] Configure domain in hosting platform
- [ ] Set up HTTPS redirect
- [ ] Configure canonical URL in application
- [ ] Update OG tags and metadata
- [ ] Configure security headers
- [ ] Test domain resolution and HTTPS
- [ ] Set up certificate monitoring/renewal
- [ ] Configure subdomain strategy (www, api, etc.)

## DNS Configuration

```
# Example DNS records
swelly.app          A     <IP_ADDRESS>
www.swelly.app      CNAME swelly.app
```

## Security Headers

```python
# Flask security headers
@app.after_request
def set_security_headers(response):
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Content-Security-Policy'] = "default-src 'self'"
    return response
```

## Metadata Requirements
```html
<!-- Update in HTML templates -->
<meta property="og:url" content="https://swelly.app" />
<meta property="og:title" content="Swelly - Social Media Content Generator" />
<meta property="og:description" content="..." />
<link rel="canonical" href="https://swelly.app" />
```

## Redirect Strategy
- HTTP → HTTPS (all traffic)
- www.swelly.app → swelly.app (or vice versa, choose one)
- Trailing slashes handled consistently

## Current State
- ⚠️ Domain not configured
- ⚠️ TLS not set up
- ⚠️ Need security headers

## Dependencies
- Production environment (#4)

## Resources
- [Let's Encrypt](https://letsencrypt.org/)
- [Cloud Run Custom Domains](https://cloud.google.com/run/docs/mapping-custom-domains)
- [Security Headers Best Practices](https://securityheaders.com/)
- [HSTS Preload](https://hstspreload.org/)

## Definition of Done
- All acceptance criteria met
- Domain accessible over HTTPS
- SSL Labs grade A or higher
- Security headers verified
- Metadata validated
