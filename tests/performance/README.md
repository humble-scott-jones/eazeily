# Performance and Load Testing

## Overview

This directory contains performance and load testing scripts and documentation for Togetherly.

## Tools

We use **Locust** for load testing. Install with:
```bash
pip install locust
```

## Running Load Tests

### Local Testing
```bash
# Start the application
PORT=5001 python app.py

# In another terminal, run locust
cd tests/performance
locust -f locustfile.py --host=http://localhost:5001
```

Then open http://localhost:8089 to configure and run the load test.

### Headless Mode (CI/CD)
```bash
locust -f locustfile.py --host=http://localhost:5001 \
  --users 100 --spawn-rate 10 --run-time 5m --headless \
  --csv=results/load_test
```

## Test Scenarios

### Scenario 1: Normal Load
- **Users:** 50 concurrent users
- **Duration:** 10 minutes
- **Spawn Rate:** 5 users/second
- **Purpose:** Baseline performance under normal conditions

### Scenario 2: Peak Load
- **Users:** 200 concurrent users
- **Duration:** 10 minutes
- **Spawn Rate:** 20 users/second
- **Purpose:** Simulate peak traffic (holidays, promotions)

### Scenario 3: Stress Test
- **Users:** 500+ concurrent users
- **Duration:** 5 minutes
- **Spawn Rate:** 50 users/second
- **Purpose:** Find breaking point and failure modes

### Scenario 4: Spike Test
- **Pattern:** Ramp up quickly from 0 to 300 users
- **Duration:** 3 minutes
- **Purpose:** Test auto-scaling and recovery

## Performance KPIs

### Response Time Targets
- **p50:** < 500ms
- **p95:** < 2s
- **p99:** < 5s
- **Max:** < 10s

### Throughput Targets
- **Normal Load:** 50 requests/second
- **Peak Load:** 100 requests/second
- **Burst:** 200 requests/second

### Error Rate Targets
- **Normal Load:** < 0.1%
- **Peak Load:** < 0.5%
- **Stress Test:** < 5% (acceptable degradation)

### Resource Utilization Targets
- **CPU:** < 70% under normal load
- **Memory:** < 80% under normal load
- **Database Connections:** < 80% of pool

## Baseline Metrics

Document baseline metrics here after initial performance test:

| Endpoint | p50 | p95 | p99 | Throughput |
|----------|-----|-----|-----|------------|
| GET / | TBD | TBD | TBD | TBD |
| POST /api/generate | TBD | TBD | TBD | TBD |
| POST /api/profile | TBD | TBD | TBD | TBD |
| POST /api/auth/login | TBD | TBD | TBD | TBD |

## Performance Testing Checklist

Before running performance tests:
- [ ] Test against staging environment (never production)
- [ ] Use realistic test data
- [ ] Warm up the system (run for 2-3 minutes before measuring)
- [ ] Monitor system resources during test
- [ ] Document configuration and environment

After running performance tests:
- [ ] Analyze results and compare to baseline
- [ ] Identify bottlenecks (database queries, external APIs)
- [ ] Document findings and recommendations
- [ ] Create tickets for performance improvements if needed

## Interpreting Results

### Good Results
- All response times within targets
- Error rate < 0.1%
- Resources well within limits
- Linear scaling with user count

### Warning Signs
- Response times increasing with load
- Error rate climbing
- Resource utilization > 80%
- Non-linear performance degradation

### Critical Issues
- Response times > 10s
- Error rate > 5%
- System crashes or becomes unresponsive
- Database connection pool exhausted

## Continuous Performance Monitoring

Run automated performance tests:
- **Weekly:** Baseline test on staging
- **Before Major Release:** Full performance suite
- **After Infrastructure Changes:** Validation test

## Example Locust File

See `locustfile.py` for the actual implementation. Key test scenarios:

1. **User Journey Test:** Signup → Login → Create Profile → Generate Content
2. **Content Generation Load:** Heavy load on /api/generate
3. **Read-Heavy Load:** Browsing, viewing accounts
4. **Write-Heavy Load:** Saving profiles, providing feedback

## Performance Optimization Tips

If performance tests reveal issues:

1. **Database:**
   - Add indexes on frequently queried columns
   - Optimize slow queries (use EXPLAIN)
   - Consider connection pooling
   - Cache frequently accessed data

2. **Application:**
   - Implement caching (Redis)
   - Optimize hot paths
   - Use async processing for long-running tasks
   - Implement rate limiting

3. **Infrastructure:**
   - Scale horizontally (add more servers)
   - Upgrade resources (CPU, memory)
   - Use CDN for static assets
   - Optimize network configuration

4. **External APIs:**
   - Implement circuit breakers
   - Use caching where appropriate
   - Consider bulk operations
   - Implement retry logic with backoff

## Next Steps

1. Create initial `locustfile.py` with basic scenarios
2. Run baseline performance test on staging
3. Document baseline metrics
4. Set up automated performance testing in CI/CD
5. Create performance dashboard
