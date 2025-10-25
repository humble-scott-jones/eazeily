# Acceptance Testing Guide

## Overview
This guide outlines acceptance tests that should be run before deploying Togetherly to production and periodically thereafter to ensure the application meets business requirements.

## Test Environments

### Staging Environment
- Mirror of production configuration
- Uses Stripe test mode
- Separate database from production
- All production secrets configured (test versions)

### Production Environment
- Live user-facing application
- Uses Stripe live mode
- Production database
- All production monitoring enabled

## Pre-Production Acceptance Tests

### 1. User Authentication Flow

#### Test Case 1.1: User Signup
**Steps:**
1. Navigate to the application homepage
2. Click "Sign up" or equivalent
3. Enter valid email and password (min 6 characters)
4. Submit the form

**Expected Result:**
- User is created successfully
- User is automatically logged in
- User is redirected to the main application page
- Session is established

**Acceptance Criteria:**
- Email validation works (rejects invalid emails)
- Password validation works (rejects passwords < 6 chars)
- Duplicate email signup shows appropriate error
- User can immediately use the application

#### Test Case 1.2: User Login
**Steps:**
1. Navigate to login page
2. Enter registered email and password
3. Submit the form

**Expected Result:**
- User is authenticated
- User is redirected to the main application
- Session persists across page refreshes

**Acceptance Criteria:**
- Invalid credentials show clear error message
- Case-insensitive email matching works
- Session timeout is reasonable (configurable)

#### Test Case 1.3: User Logout
**Steps:**
1. While logged in, click "Logout"

**Expected Result:**
- User session is terminated
- User is redirected to homepage or login page
- Protected pages are no longer accessible

#### Test Case 1.4: Password Reset Flow
**Steps:**
1. Click "Forgot Password"
2. Enter registered email address
3. Retrieve reset token (check email in staging, logs in dev)
4. Use reset link with token
5. Enter new password
6. Login with new password

**Expected Result:**
- Reset email is sent (or token is generated)
- Token is valid for reasonable time (1 hour)
- New password is accepted and works
- Old password no longer works
- Token is invalidated after use

### 2. Content Generation Flow

#### Test Case 2.1: Basic Profile Setup
**Steps:**
1. Log in as a user
2. Complete the profile setup wizard:
   - Select industry (e.g., "Technology")
   - Select tone (e.g., "Professional")
   - Select platforms (e.g., Instagram, LinkedIn)
   - Add brand keywords (e.g., "innovation", "quality")
   - Add company name
3. Save profile

**Expected Result:**
- All fields are saved correctly
- Profile persists across sessions
- User can edit profile later

**Acceptance Criteria:**
- Company name validation works (max 100 chars, valid characters)
- All selections are saved
- Profile data is available for content generation

#### Test Case 2.2: Content Generation (Free User)
**Steps:**
1. Log in as a free user
2. Complete profile if not done
3. Request content generation for 3 days
4. View generated content

**Expected Result:**
- Content is generated for 3 days
- Content matches selected tone and industry
- Brand keywords are incorporated
- Posts are appropriate for selected platforms
- Generation completes within reasonable time (< 30 seconds)

**Acceptance Criteria:**
- Generated content quality is acceptable
- Different platforms get different content
- Posts are unique (not duplicated)

#### Test Case 2.3: Extended Generation (Paid User)
**Steps:**
1. Log in as a paid user
2. Request content generation for 7+ days (e.g., 30 days)
3. View generated content

**Expected Result:**
- Content is generated for all requested days
- No errors occur during extended generation
- Content maintains quality across all days

**Acceptance Criteria:**
- Free users are blocked from 7+ day generation
- Paid users can generate extended content
- Content remains diverse and relevant

### 3. Subscription & Payment Flow

#### Test Case 3.1: View Subscription Plans
**Steps:**
1. Navigate to pricing page
2. View available subscription tiers

**Expected Result:**
- All tiers are clearly displayed
- Pricing is accurate
- Features are listed for each tier
- Call-to-action buttons are present

#### Test Case 3.2: Subscribe to Paid Plan (Checkout)
**Steps:**
1. Log in as a free user
2. Select a paid subscription plan
3. Click "Subscribe" or "Upgrade"
4. Enter Stripe test card: 4242 4242 4242 4242
5. Complete payment form (any future date, any CVC)
6. Submit payment

**Expected Result:**
- Stripe Checkout page loads correctly
- Payment is processed successfully
- User is redirected back to app with success message
- User account is upgraded to paid status
- Subscription is created in database
- Webhook is received and processed

**Acceptance Criteria:**
- User can immediately access paid features
- Subscription status is reflected in account page
- Stripe dashboard shows the subscription
- Failed payments show appropriate errors

#### Test Case 3.3: Subscribe to Paid Plan (Direct Payment)
**Steps:**
1. Log in as a free user
2. Navigate to payment page
3. Enter payment details directly (using Stripe Elements)
4. Submit payment

**Expected Result:**
- Payment method is attached to customer
- Subscription is created and active
- User is upgraded to paid status
- SCA (3D Secure) is handled if required

#### Test Case 3.4: View Account & Subscription Details
**Steps:**
1. Log in as a paid user
2. Navigate to account page
3. View subscription details

**Expected Result:**
- Subscription status is displayed (active, canceled, etc.)
- Current period end date is shown
- Payment method is displayed
- Billing history is accessible

#### Test Case 3.5: Cancel Subscription
**Steps:**
1. Log in as a paid user with active subscription
2. Navigate to account page
3. Click "Cancel Subscription"
4. Confirm cancellation

**Expected Result:**
- Subscription is canceled in Stripe
- User retains access until period end
- Cancellation is reflected in account page
- User receives confirmation

**Acceptance Criteria:**
- Cancellation is processed immediately
- User is not charged for next period
- Access is maintained until current period ends

#### Test Case 3.6: Manage Subscription via Customer Portal
**Steps:**
1. Log in as a paid user
2. Navigate to account page
3. Click "Manage Subscription" or "Billing Portal"
4. Redirected to Stripe Customer Portal
5. Update payment method or cancel subscription

**Expected Result:**
- Portal opens successfully
- User can update payment information
- User can cancel subscription
- Changes sync back to app database

### 4. Admin Functionality

#### Test Case 4.1: Admin Access
**Steps:**
1. Log in as a user in ADMIN_EMAILS list
2. Navigate to /admin page

**Expected Result:**
- Admin page is accessible
- Admin controls are visible
- Non-admin users cannot access

#### Test Case 4.2: Subscription Reconciliation
**Steps:**
1. Log in as admin
2. Navigate to admin panel
3. Trigger subscription reconciliation
4. Wait for job completion

**Expected Result:**
- Reconciliation job starts successfully
- Job queries Stripe API for subscription statuses
- Local database is updated with latest data
- Job completion is reported
- Results show any discrepancies

**Acceptance Criteria:**
- CSRF protection works (requires valid token)
- Only admins can trigger reconciliation
- Errors are logged appropriately

### 5. Webhook Processing

#### Test Case 5.1: Checkout Session Completed
**Steps:**
1. Complete a checkout session (Test Case 3.2)
2. Verify webhook is received

**Expected Result:**
- Webhook endpoint receives `checkout.session.completed` event
- User is marked as paid
- Subscription record is created
- Stripe customer ID is stored

#### Test Case 5.2: Subscription Updated
**Steps:**
1. Using Stripe Dashboard, update subscription status
2. Verify webhook is received

**Expected Result:**
- Webhook endpoint receives `customer.subscription.updated` event
- Local subscription status is updated
- User paid status is updated accordingly

#### Test Case 5.3: Subscription Deleted
**Steps:**
1. Cancel a subscription in Stripe
2. Verify webhook is received

**Expected Result:**
- Webhook endpoint receives `customer.subscription.deleted` event
- Local subscription status is updated to canceled
- User is marked as not paid (after period ends)

#### Test Case 5.4: Invoice Payment Succeeded
**Steps:**
1. Simulate recurring payment in Stripe
2. Verify webhook is received

**Expected Result:**
- Webhook endpoint receives `invoice.payment_succeeded` event
- User remains marked as paid
- Subscription period is extended

#### Test Case 5.5: Webhook Signature Verification
**Steps:**
1. Send webhook with invalid signature
2. Verify it is rejected

**Expected Result:**
- Invalid signature webhooks are rejected with 400 status
- Event is not processed
- Error is logged

### 6. Error Handling & Edge Cases

#### Test Case 6.1: Database Connection Failure
**Steps:**
1. Simulate database connection issue
2. Attempt to access the application

**Expected Result:**
- Graceful error message shown to user
- Error is logged for monitoring
- Application doesn't crash
- Connection is retried

#### Test Case 6.2: Stripe API Failure
**Steps:**
1. Temporarily disable Stripe API access or use invalid key
2. Attempt to create subscription

**Expected Result:**
- Appropriate error message shown to user
- No partial state is created
- Error is logged
- User can retry

#### Test Case 6.3: Invalid Input Handling
**Steps:**
1. Submit forms with various invalid inputs:
   - SQL injection attempts
   - XSS payloads
   - Extremely long strings
   - Invalid character encodings

**Expected Result:**
- All inputs are properly validated and sanitized
- Malicious inputs are rejected
- No security vulnerabilities exploited
- Appropriate error messages shown

#### Test Case 6.4: Session Timeout
**Steps:**
1. Log in to application
2. Wait for session timeout period
3. Attempt to access protected page

**Expected Result:**
- User is redirected to login page
- Clear message about session expiration
- After re-login, user can continue

### 7. Performance & Load Testing

#### Test Case 7.1: Concurrent User Signup
**Steps:**
1. Simulate 50 users signing up simultaneously
2. Monitor response times and error rates

**Expected Result:**
- All signups are processed successfully
- Response times remain acceptable (< 2s)
- No database deadlocks or race conditions
- Error rate < 1%

#### Test Case 7.2: Content Generation Under Load
**Steps:**
1. Simulate 20 users generating content simultaneously
2. Monitor completion times

**Expected Result:**
- All requests complete successfully
- No timeouts occur
- Quality of generated content is maintained
- Server resources (CPU, memory) remain healthy

#### Test Case 7.3: Payment Processing Load
**Steps:**
1. Process 100 test payments in quick succession
2. Verify all are processed correctly

**Expected Result:**
- All payments are processed
- No duplicate charges
- All webhooks are received
- Database remains consistent

### 8. Cross-Browser & Mobile Testing

#### Test Case 8.1: Browser Compatibility
**Browsers to Test:**
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

**Expected Result:**
- Application functions identically across all browsers
- UI renders correctly
- No JavaScript errors in console
- All interactive elements work

#### Test Case 8.2: Mobile Responsiveness
**Devices to Test:**
- iPhone (iOS Safari)
- Android phone (Chrome)
- Tablet (iPad)

**Expected Result:**
- Application is fully responsive
- Touch interactions work properly
- Forms are easy to use on mobile
- No horizontal scrolling
- Text is readable without zooming

### 9. Security Testing

#### Test Case 9.1: Authentication Security
**Tests:**
1. Attempt to access protected pages without login
2. Attempt to use another user's session token
3. Attempt password brute force attack

**Expected Result:**
- Unauthorized access is blocked
- Session tokens are secure
- Rate limiting prevents brute force

#### Test Case 9.2: Data Privacy
**Tests:**
1. Verify user can only access their own data
2. Attempt to access another user's profile/content
3. Verify admin can only access admin features

**Expected Result:**
- Proper authorization checks in place
- No data leakage between users
- Admin access is properly gated

#### Test Case 9.3: HTTPS & TLS
**Tests:**
1. Verify all pages load over HTTPS
2. Attempt HTTP access
3. Verify SSL certificate is valid

**Expected Result:**
- All traffic is encrypted
- HTTP redirects to HTTPS
- Valid SSL certificate with correct domain

## Production Smoke Tests

Run these tests immediately after production deployment:

1. **Health Check:** GET / returns 200
2. **User Login:** Existing user can log in
3. **Content Generation:** Generate 3-day content successfully
4. **Payment Flow:** Complete test payment (use Stripe test mode initially)
5. **Webhook Reception:** Send test webhook from Stripe dashboard

## Automated vs Manual Testing

### Automated (via pytest)
- Unit tests for all business logic
- API endpoint tests
- Database integration tests
- Webhook processing tests

### Manual (this guide)
- End-to-end user flows
- UI/UX verification
- Cross-browser testing
- Payment flow with real Stripe
- Admin functionality

## Test Data Cleanup

After testing in staging:
1. Delete test user accounts
2. Clean up test subscriptions in Stripe
3. Reset database to clean state
4. Verify no test data in production

## Acceptance Criteria for Production Release

All tests must pass with:
- ✅ 0 critical bugs
- ✅ 0 payment processing issues
- ✅ 0 security vulnerabilities
- ✅ < 2 minor UI issues (acceptable to fix post-launch)
- ✅ All webhooks processing correctly
- ✅ Performance targets met
- ✅ Cross-browser compatibility verified
- ✅ Mobile responsiveness verified

## Sign-Off

Before production deployment, obtain sign-off from:
- [ ] Engineering Lead
- [ ] Product Manager
- [ ] QA Team
- [ ] Security Team (if applicable)
- [ ] Business Stakeholder

---

**Note:** This guide should be reviewed and updated after each release based on new features and lessons learned.
