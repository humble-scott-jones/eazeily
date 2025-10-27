# Monitoring and Observability Guide

## Overview

This guide describes the monitoring, logging, and observability strategy for Togetherly to ensure production reliability and quick incident response.

## Monitoring Stack

### Recommended Tools

**Metrics:** Prometheus + Grafana (or cloud provider equivalent)  
**Logging:** ELK Stack (Elasticsearch, Logstash, Kibana) or cloud logging service  
**Tracing:** Jaeger or OpenTelemetry  
**Uptime:** UptimeRobot, Pingdom, or cloud health checks  
**Alerting:** PagerDuty, Opsgenie, or integrated alerting

## Key Metrics

### Application Metrics

#### Request Metrics
```
# Total requests per endpoint
http_requests_total{method, endpoint, status_code}

# Request duration (histogram)
http_request_duration_seconds{method, endpoint}

# Request rate
rate(http_requests_total[5m])

# Error rate
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m])
```

#### Business Metrics
```
# User signups
user_signups_total

# Content generation requests
content_generation_total{industry, platform}

# Subscription conversions
subscription_conversions_total{plan}

# Active sessions
active_sessions
```

#### Performance Metrics
```
# Response time percentiles
http_request_duration_seconds{quantile="0.5"}  # p50
http_request_duration_seconds{quantile="0.95"} # p95
http_request_duration_seconds{quantile="0.99"} # p99

# Database query time
db_query_duration_seconds{query_type}

# External API latency
external_api_duration_seconds{service}
```

### Infrastructure Metrics

#### System Resources
```
# CPU usage
system_cpu_usage_percent

# Memory usage
system_memory_usage_percent
system_memory_available_bytes

# Disk usage
system_disk_usage_percent
system_disk_io_bytes{direction}

# Network
system_network_io_bytes{direction}
```

#### Application Health
```
# Process metrics
process_cpu_seconds_total
process_resident_memory_bytes
process_open_fds

# Python-specific
python_gc_objects_collected_total
python_gc_collections_total
```

### Database Metrics
```
# Connection pool
db_connection_pool_size
db_connection_pool_active
db_connection_pool_idle

# Query performance
db_query_duration_seconds{operation}
db_queries_total{operation, status}

# Database size
db_size_bytes
db_table_size_bytes{table}

# Locks and deadlocks
db_locks_total
db_deadlocks_total
```

### External Service Metrics
```
# Stripe API
stripe_api_requests_total{endpoint, status}
stripe_api_duration_seconds{endpoint}

# OpenAI API
openai_api_requests_total{model, status}
openai_api_duration_seconds{model}
openai_api_tokens_used{model}
```

## Logging Strategy

### Log Levels

Use appropriate log levels:
- **DEBUG:** Detailed debugging information (disabled in production)
- **INFO:** General informational messages (user actions, system events)
- **WARNING:** Warning messages (degraded performance, deprecated usage)
- **ERROR:** Error messages (handled exceptions, failed operations)
- **CRITICAL:** Critical errors (system failures, data corruption)

### Structured Logging

Use JSON format for logs to enable easy parsing and searching:

```python
import logging
import json
from datetime import datetime

class StructuredLogger:
    def __init__(self, name):
        self.logger = logging.getLogger(name)
        
    def log(self, level, message, **kwargs):
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'level': level,
            'message': message,
            'service': 'togetherly',
            **kwargs
        }
        self.logger.log(getattr(logging, level), json.dumps(log_entry))

# Usage
logger = StructuredLogger('togetherly')
logger.log('INFO', 'User registered', user_id='user-123', email='user@example.com')
logger.log('ERROR', 'Payment failed', user_id='user-123', error='card_declined')
```

### What to Log

**Always Log:**
- User authentication events (login, logout, failed attempts)
- Payment transactions (initiate, success, failure)
- Content generation requests (profile_id, industry, platforms)
- API errors (status code, error message, request_id)
- Security events (suspicious activity, rate limit hits)
- Database errors (query failures, connection issues)
- External service failures (Stripe, OpenAI)

**Include in Logs:**
- Request ID (for tracing)
- User/Profile ID (for user-specific issues)
- Timestamp (UTC)
- Environment (production, staging)
- Version (for deploy correlation)

**Never Log:**
- Passwords or API keys
- Full credit card numbers
- Personal identifying information (PII) unless necessary
- Full request/response bodies (may contain sensitive data)

### Example Log Entries

```json
// User registration
{
  "timestamp": "2025-10-26T14:30:00Z",
  "level": "INFO",
  "message": "User registered",
  "user_id": "user-123",
  "email": "user@example.com",
  "industry": "restaurant",
  "request_id": "req-abc-123"
}

// Content generation
{
  "timestamp": "2025-10-26T14:31:00Z",
  "level": "INFO",
  "message": "Content generation completed",
  "profile_id": "profile-456",
  "posts_generated": 7,
  "duration_ms": 2340,
  "platforms": ["instagram", "facebook"],
  "request_id": "req-def-456"
}

// Error
{
  "timestamp": "2025-10-26T14:32:00Z",
  "level": "ERROR",
  "message": "OpenAI API request failed",
  "error": "rate_limit_exceeded",
  "profile_id": "profile-789",
  "retry_attempt": 2,
  "request_id": "req-ghi-789"
}
```

## Distributed Tracing

### OpenTelemetry Integration

Add tracing to follow requests through the system:

```python
from opentelemetry import trace
from opentelemetry.instrumentation.flask import FlaskInstrumentor

# Initialize tracing
tracer = trace.get_tracer(__name__)

# Instrument Flask app
FlaskInstrumentor().instrument_app(app)

# Add custom spans
@app.route('/api/generate')
def generate():
    with tracer.start_as_current_span("generate_content") as span:
        span.set_attribute("profile_id", profile_id)
        span.set_attribute("platforms", platforms)
        
        # Generate content
        posts = generate_posts(profile)
        
        span.set_attribute("posts_generated", len(posts))
        return jsonify(posts)
```

### Trace Critical Paths
- User registration flow
- Content generation pipeline
- Payment processing
- Database queries
- External API calls

## Alerting

### Alert Thresholds

#### Critical Alerts (Immediate Response)
```
# Service down
up{service="togetherly"} == 0

# High error rate (> 5%)
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05

# Database connection failures
db_connection_errors_total > 10

# Payment failures spike (> 20%)
rate(payment_failures_total[5m]) / rate(payment_attempts_total[5m]) > 0.20

# Critical resource usage
system_cpu_usage_percent > 90
system_memory_usage_percent > 95
system_disk_usage_percent > 95
```

#### Warning Alerts (Review Required)
```
# Elevated error rate (1-5%)
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.01

# Slow response times (p95 > 3s)
histogram_quantile(0.95, http_request_duration_seconds) > 3

# High CPU usage
system_cpu_usage_percent > 70

# High memory usage
system_memory_usage_percent > 80

# Database connection pool near capacity
db_connection_pool_active / db_connection_pool_size > 0.80
```

#### Informational Alerts
```
# Unusual traffic patterns
rate(http_requests_total[5m]) > 2 * avg_over_time(rate(http_requests_total[5m])[1h])

# External API degradation
rate(openai_api_errors_total[5m]) > 5

# Approaching rate limits
openai_api_requests_total > 0.8 * openai_rate_limit
```

### Alert Routing

**Critical Alerts:**
- Send to on-call engineer via PagerDuty/phone
- Post to #incidents Slack channel
- Create incident ticket automatically

**Warning Alerts:**
- Send to #monitoring Slack channel
- Email engineering team
- Log to incident tracking

**Informational Alerts:**
- Send to #monitoring Slack channel
- Daily digest email

### Alert Best Practices

1. **Actionable:** Every alert should have a clear action
2. **Documented:** Link to runbook in alert description
3. **Tuned:** Adjust thresholds to minimize false positives
4. **Tested:** Test alerts fire correctly
5. **Reviewed:** Regularly review alert fatigue and adjust

## Dashboards

### Executive Dashboard
High-level metrics for stakeholders:
- User signups (daily/weekly/monthly)
- Content generation volume
- Subscription conversions
- Revenue metrics
- System uptime
- Error rate trend

### Operations Dashboard
Real-time system health:
- Request rate and error rate
- Response time (p50, p95, p99)
- Active users/sessions
- Resource usage (CPU, memory, disk)
- Database health
- External service status

### Application Dashboard
Application-specific metrics:
- Requests by endpoint
- Error rate by endpoint
- Content generation by industry
- User journey funnels
- Feature usage

### Database Dashboard
Database performance:
- Query duration by type
- Connection pool utilization
- Slow query count
- Database size growth
- Table-level metrics

## Health Checks

### Health Check Endpoint

Add `/health` endpoint to the application:

```python
@app.route('/health')
def health_check():
    health = {
        'status': 'healthy',
        'version': os.getenv('APP_VERSION', 'unknown'),
        'timestamp': datetime.utcnow().isoformat(),
        'checks': {}
    }
    
    # Database check
    try:
        db = get_db()
        db.execute('SELECT 1').fetchone()
        health['checks']['database'] = 'healthy'
    except Exception as e:
        health['checks']['database'] = 'unhealthy'
        health['status'] = 'unhealthy'
    
    # External services check (optional)
    health['checks']['stripe'] = check_stripe_health()
    health['checks']['openai'] = check_openai_health()
    
    status_code = 200 if health['status'] == 'healthy' else 503
    return jsonify(health), status_code
```

### Uptime Monitoring

Configure external uptime monitoring:
- **Check `/health` endpoint every 1 minute**
- **Alert if 3 consecutive failures**
- **Expect 200 status code**
- **Monitor from multiple regions**

### Synthetic Tests

Run synthetic transactions to validate critical paths:
```bash
# User flow: Create profile → Generate content
./scripts/synthetic-test.sh --flow user_journey

# Payment flow: Checkout → Webhook
./scripts/synthetic-test.sh --flow payment_journey

# Run every 5 minutes
# Alert if success rate < 95%
```

## Performance Monitoring

### Application Performance Monitoring (APM)

Use APM tools to track:
- **Transaction traces:** See exact flow of requests
- **Database query analysis:** Identify slow queries
- **External calls:** Track API call latency
- **Memory profiling:** Find memory leaks
- **CPU profiling:** Identify hot paths

### Real User Monitoring (RUM)

Track actual user experience:
- Page load time
- Time to interactive
- User interactions
- JavaScript errors
- Browser/device distribution

## Security Monitoring

### Security Events to Monitor

- Failed login attempts (rate and pattern)
- Unusual API usage patterns
- Rate limit violations
- SQL injection attempts (invalid queries)
- XSS attempts
- Authentication token issues
- Privilege escalation attempts

### Security Alerts

```
# Failed login spike
rate(failed_login_attempts[5m]) > 20

# Unusual API access pattern
rate(api_rate_limit_exceeded[5m]) > 10

# Security vulnerability detected
vulnerability_scan_critical_count > 0
```

## Capacity Planning

### Metrics for Capacity Planning

- **Request rate trend:** Plan for 3x peak capacity
- **Database growth rate:** Project 6 months ahead
- **User growth rate:** Correlate with infrastructure needs
- **Resource utilization trends:** Scale before hitting limits

### Scaling Indicators

**Scale Up When:**
- CPU consistently > 70%
- Memory consistently > 80%
- Response time p95 > 2 seconds
- Database connection pool > 80% utilized

## Log Retention

### Retention Policies

- **Application logs:** 30 days hot, 90 days archive
- **Access logs:** 90 days hot, 1 year archive
- **Audit logs:** 1 year hot, 7 years archive
- **Metrics:** 15 days high-resolution, 1 year downsampled

### Compliance

Ensure logging meets compliance requirements:
- GDPR: Allow log data deletion on user request
- PCI-DSS: Secure and audit payment-related logs
- SOC 2: Maintain audit trail of security events

## Runbooks

Link monitoring alerts to specific runbooks:

- **High Error Rate:** See INCIDENT_RESPONSE.md → High Error Rate
- **Database Connection Issues:** See INCIDENT_RESPONSE.md → Database Issues
- **Payment Failures:** See INCIDENT_RESPONSE.md → Payment Issues
- **Slow Performance:** See INCIDENT_RESPONSE.md → Performance Degradation

## Observability Checklist

- [ ] Metrics collection configured and validated
- [ ] Structured logging implemented
- [ ] Distributed tracing enabled for critical paths
- [ ] Dashboards created for all key metrics
- [ ] Alerts configured with appropriate thresholds
- [ ] Alert routing configured to on-call rotation
- [ ] Health check endpoint implemented
- [ ] Uptime monitoring configured
- [ ] Synthetic tests running
- [ ] Log retention policies defined
- [ ] Runbooks linked from alerts
- [ ] Team trained on dashboards and alerts

## Tools and Implementation

### Python Instrumentation

```bash
# Install observability packages
pip install prometheus-client
pip install opentelemetry-api opentelemetry-sdk
pip install opentelemetry-instrumentation-flask
pip install python-json-logger
```

### Example Prometheus Metrics
```python
from prometheus_client import Counter, Histogram, generate_latest

# Define metrics
request_count = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
request_duration = Histogram('http_request_duration_seconds', 'HTTP request duration', ['method', 'endpoint'])

# Instrument endpoints
@app.before_request
def before_request():
    g.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - g.start_time
    request_count.labels(method=request.method, endpoint=request.path, status=response.status_code).inc()
    request_duration.labels(method=request.method, endpoint=request.path).observe(duration)
    return response

# Metrics endpoint
@app.route('/metrics')
def metrics():
    return generate_latest()
```

## Next Steps

1. Set up monitoring infrastructure
2. Implement instrumentation in code
3. Configure dashboards
4. Set up alerts with on-call rotation
5. Test alert firing and runbook procedures
6. Train team on monitoring tools
7. Establish regular review process for metrics and alerts
