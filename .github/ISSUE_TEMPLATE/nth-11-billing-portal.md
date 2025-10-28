---
name: 💳 Nice-to-Have 11 - Self-Serve Billing Portal
about: Stripe Customer Portal for self-service subscription management
title: '[LAUNCH-NTH] Self-Serve Billing Portal'
labels: ['launch', 'nice-to-have', 'payments', 'backend']
assignees: []
---

## Priority
**Nice-to-Have #11** - Lower priority, implement after must-haves

## Description
Implement Stripe Customer Portal to allow users to manage their subscriptions, payment methods, and billing information without support intervention.

## Acceptance Criteria
- [ ] Stripe Customer Portal configured
- [ ] Users can update payment methods
- [ ] Users can view invoices
- [ ] Users can upgrade/downgrade subscriptions
- [ ] Users can cancel subscriptions
- [ ] Link to portal in account page

## Implementation Tasks
- [ ] Enable Stripe Customer Portal in dashboard
- [ ] Configure portal settings (features, branding)
- [ ] Add "Manage Billing" button in account page
- [ ] Generate portal session on click
- [ ] Redirect user to portal
- [ ] Handle return URL
- [ ] Test all portal features

## Stripe Customer Portal Features
```python
# Generate portal session
import stripe

portal_session = stripe.billing_portal.Session.create(
    customer=customer_id,
    return_url='https://swelly.app/account',
)
return redirect(portal_session.url)
```

## Portal Configuration
- Allow payment method updates
- Allow subscription cancellation
- Show invoice history
- Enable subscription upgrades/downgrades
- Configure branding to match app

## Current State
- ⚠️ Users may need support for billing changes
- ⚠️ Customer Portal not implemented

## Benefits
- Reduced support burden
- Better user experience
- Faster resolution of billing issues
- Self-service preference for users

## Resources
- [Stripe Customer Portal](https://stripe.com/docs/billing/subscriptions/integrating-customer-portal)
- [Portal Configuration](https://dashboard.stripe.com/settings/billing/portal)
