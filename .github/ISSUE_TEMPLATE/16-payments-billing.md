---
name: 💳 Must-Have 16 - Payments & Billing
about: Stripe integration with test mode, tax/pricing copy ready
title: '[LAUNCH] Payments & Billing (if applicable)'
labels: ['launch', 'payments', 'high-priority', 'backend']
assignees: []
---

## Priority
**Must-Have #16** - Complete before launch (if subscriptions enabled)

## Description
Configure Stripe (or other payment processor) in production mode with proper test coverage. Ensure tax calculations, pricing copy, and webhook handling are production-ready.

## Acceptance Criteria
- [ ] Stripe configured in production mode
- [ ] Test transactions succeed in test mode
- [ ] Webhooks verified and working
- [ ] Subscription tiers configured
- [ ] Pricing copy accurate and clear
- [ ] Tax handling configured (if required)
- [ ] Failed payment handling implemented
- [ ] Invoice generation working
- [ ] Payment method updates working
- [ ] Cancellation flow tested

## Implementation Tasks
- [ ] Set up Stripe production account
- [ ] Configure production API keys in secrets manager
- [ ] Create product/price objects in Stripe
- [ ] Implement checkout flow
- [ ] Configure webhook endpoints
- [ ] Verify webhook signatures
- [ ] Handle subscription lifecycle events
- [ ] Implement failed payment retry logic
- [ ] Add invoice email notifications
- [ ] Test payment method updates
- [ ] Test subscription cancellation
- [ ] Configure tax collection (Stripe Tax)
- [ ] Update pricing page with final copy
- [ ] Test different payment methods

## Stripe Products Configuration

```yaml
Free Tier:
  price: $0/month
  features:
    - 10 posts per month
    - Basic templates
    - Single industry

Pro Tier:
  price: $19/month
  price_id: price_xxx
  features:
    - Unlimited posts
    - All templates
    - All industries
    - Priority support

Enterprise Tier:
  price: Custom
  features:
    - Everything in Pro
    - Custom templates
    - API access
    - Dedicated support
```

## Webhook Events to Handle

```python
Required Webhooks:
  - checkout.session.completed
  - customer.subscription.created
  - customer.subscription.updated
  - customer.subscription.deleted
  - invoice.payment_succeeded
  - invoice.payment_failed

Implementation in app.py:
  @app.route('/api/stripe-webhook', methods=['POST'])
  def stripe_webhook():
      # Verify signature
      # Handle events
      # Update database
      # Send notifications
```

## Payment Flow Testing

```
Test Scenarios:
1. Successful subscription creation
2. Successful one-time payment
3. Failed payment (card declined)
4. Subscription upgrade
5. Subscription downgrade
6. Subscription cancellation
7. Payment method update
8. Invoice generation
9. Refund processing
10. Webhook delivery and retries
```

## Test Cards (Stripe Test Mode)

```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Insufficient funds: 4000 0000 0000 9995
3D Secure: 4000 0027 6000 3184
```

## Subscription Lifecycle

```
1. User clicks "Subscribe"
2. Redirect to Stripe Checkout
3. Payment processed
4. Webhook received
5. Database updated
6. User redirected to success page
7. Welcome email sent
8. Subscription active
```

## Failed Payment Handling
- [ ] Retry payment automatically (Stripe Smart Retries)
- [ ] Email user about failed payment
- [ ] Grace period before downgrade (7 days recommended)
- [ ] Downgrade to free tier if payment fails
- [ ] Re-activate on successful payment

## Tax Configuration
- [ ] Enable Stripe Tax (if selling in multiple jurisdictions)
- [ ] Configure tax behavior
- [ ] Display tax-inclusive prices where required
- [ ] Collect tax IDs for business customers

## Compliance & Security
- [ ] PCI compliance (handled by Stripe Checkout)
- [ ] Store minimal payment data (only Stripe IDs)
- [ ] Webhook signature verification
- [ ] HTTPS enforced for all payment endpoints
- [ ] Rate limiting on payment endpoints

## Current State
- ✅ Stripe integration exists in `app.py`
- ✅ Documentation in `README_STRIPE.md`
- ⚠️ Need production mode configuration
- ⚠️ Webhook verification needs review
- ⚠️ Tax handling needs configuration

## Dependencies
- Secrets management (#1)
- Domain/TLS (#9)
- Monitoring (#6) - for payment failure alerts

## Resources
- [Stripe Documentation](https://stripe.com/docs)
- [Stripe Webhooks](https://stripe.com/docs/webhooks)
- [Stripe Testing](https://stripe.com/docs/testing)
- Repository: `README_STRIPE.md`

## Testing Checklist
- [ ] Test mode transactions
- [ ] Webhook delivery
- [ ] Subscription creation
- [ ] Subscription cancellation
- [ ] Failed payment handling
- [ ] Upgrade/downgrade flows
- [ ] Invoice generation
- [ ] Email notifications

## Definition of Done
- All acceptance criteria met
- All test scenarios passing
- Production Stripe account verified
- Webhooks working in production
- Payment flows tested end-to-end
- Team trained on payment handling
- Runbook for payment issues created
