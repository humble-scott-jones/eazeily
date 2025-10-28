# Analytics and SEO Setup Guide

This guide provides instructions for setting up analytics tracking and SEO optimization for the Swelly landing page.

## Google Analytics 4 (GA4) Setup

### 1. Create GA4 Property
1. Go to [Google Analytics](https://analytics.google.com/)
2. Create a new GA4 property
3. Get your Measurement ID (format: `G-XXXXXXXXXX`)

### 2. Update Landing Page
In `templates/landing.html`, replace the placeholder GA4 tracking code (around line 28):

```html
<!-- Replace this placeholder -->
// gtag('config', 'G-XXXXXXXXXX');

<!-- With your actual Measurement ID -->
gtag('config', 'G-YOUR-ACTUAL-ID');
```

Also add the GA4 script tag in the `<head>` section:

```html
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id=G-YOUR-ACTUAL-ID"></script>
```

### 3. Track Conversions
The landing page already tracks waitlist signups as conversions. When a user successfully joins the waitlist, this event is sent to GA4:

```javascript
gtag('event', 'conversion', {
  'event_category': 'waitlist',
  'event_label': 'email_signup'
});
```

You can configure this as a conversion event in your GA4 dashboard.

## Alternative: Segment Setup

If you prefer to use Segment instead of GA4:

### 1. Get Segment Write Key
1. Sign up at [Segment](https://segment.com/)
2. Create a new source
3. Copy your Write Key

### 2. Add Segment Script
Replace the GA4 script in `templates/landing.html` with:

```html
<script>
  !function(){var analytics=window.analytics=window.analytics||[];if(!analytics.initialize)if(analytics.invoked)window.console&&console.error&&console.error("Segment snippet included twice.");else{analytics.invoked=!0;analytics.methods=["trackSubmit","trackClick","trackLink","trackForm","pageview","identify","reset","group","track","ready","alias","debug","page","once","off","on","addSourceMiddleware","addIntegrationMiddleware","setAnonymousId","addDestinationMiddleware"];analytics.factory=function(e){return function(){var t=Array.prototype.slice.call(arguments);t.unshift(e);analytics.push(t);return analytics}};for(var e=0;e<analytics.methods.length;e++){var key=analytics.methods[e];analytics[key]=analytics.factory(key)}analytics.load=function(key,e){var t=document.createElement("script");t.type="text/javascript";t.async=!0;t.src="https://cdn.segment.com/analytics.js/v1/" + key + "/analytics.min.js";var n=document.getElementsByTagName("script")[0];n.parentNode.insertBefore(t,n);analytics._loadOptions=e};analytics._writeKey="YOUR_WRITE_KEY";analytics.SNIPPET_VERSION="4.15.3";
  analytics.load("YOUR_WRITE_KEY");
  analytics.page();
  }}();
</script>
```

### 3. Track Events with Segment
Update the waitlist form handler to use Segment's track method:

```javascript
if (typeof analytics !== 'undefined') {
  analytics.track('Waitlist Signup', {
    email: email
  });
}
```

## SEO Optimization

The landing page includes essential SEO meta tags. Update these with your actual information:

### Meta Tags to Customize

In `templates/landing.html` `<head>` section:

```html
<!-- Basic Meta Tags -->
<title>Swelly – Your Custom Title</title>
<meta name="description" content="Your custom description (155-160 chars)" />

<!-- Open Graph / Facebook -->
<meta property="og:title" content="Your Custom Title" />
<meta property="og:description" content="Your custom description" />
<meta property="og:image" content="https://yourdomain.com/static/og-image.png" />
<meta property="og:url" content="https://yourdomain.com" />

<!-- Twitter Card -->
<meta name="twitter:title" content="Your Custom Title" />
<meta name="twitter:description" content="Your custom description" />
<meta name="twitter:image" content="https://yourdomain.com/static/og-image.png" />
```

### Create OG Image

1. Design a 1200x630px image for social media previews
2. Save as `static/og-image.png`
3. Use the placeholder HTML at `static/og-image-placeholder.html` as a starting point
4. Test with [Facebook Sharing Debugger](https://developers.facebook.com/tools/debug/) and [Twitter Card Validator](https://cards-dev.twitter.com/validator)

### Additional SEO Best Practices

1. **Sitemap**: Create `sitemap.xml` in the root directory
2. **Robots.txt**: Create `robots.txt` to guide search engine crawlers
3. **Schema Markup**: Add structured data for better search results
4. **Performance**: Optimize images, minify CSS/JS
5. **Mobile-Friendly**: Already implemented with responsive design
6. **HTTPS**: Ensure SSL certificate is properly configured
7. **Page Speed**: Test with Google PageSpeed Insights

## Email Confirmation Setup

Currently, the waitlist API stores emails but doesn't send confirmations. To add email functionality:

### Option 1: Mailchimp

1. Sign up at [Mailchimp](https://mailchimp.com/)
2. Create an audience
3. Get your API key and Audience ID
4. Update `app.py` to integrate Mailchimp API

### Option 2: SendGrid

1. Sign up at [SendGrid](https://sendgrid.com/)
2. Create an API key
3. Install SendGrid Python SDK: `pip install sendgrid`
4. Update `app.py` to send confirmation emails

### Option 3: ConvertKit

1. Sign up at [ConvertKit](https://convertkit.com/)
2. Create a form
3. Use ConvertKit's API or form embed
4. Update `app.py` to integrate with ConvertKit

### Example Email Confirmation Code

Add to `app.py` in the `/api/waitlist` endpoint:

```python
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

def send_confirmation_email(email):
    message = Mail(
        from_email='noreply@yourdomain.com',
        to_emails=email,
        subject='Welcome to Swelly!',
        html_content='<strong>Thanks for joining our waitlist!</strong>')
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        response = sg.send(message)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

# In the waitlist API handler:
db.execute('INSERT INTO waitlist (email) VALUES (?)', (email,))
db.commit()
send_confirmation_email(email)  # Add this line
```

## Privacy & Compliance

### Cookie Consent
If using analytics that set cookies, add a cookie consent banner:

```html
<div id="cookie-banner" class="fixed bottom-0 left-0 right-0 bg-slate-900 text-white p-4 z-50">
  <div class="max-w-6xl mx-auto flex items-center justify-between">
    <p class="text-sm">We use cookies to improve your experience. By using our site, you agree to our cookie policy.</p>
    <button id="accept-cookies" class="btn-primary">Accept</button>
  </div>
</div>
```

### Privacy Policy & Terms
Create pages for:
- Privacy Policy (`/privacy`)
- Terms of Service (`/terms`)
- Cookie Policy (`/cookies`)

Link these in the footer (already included in landing page template).

## Testing

Before going live, test:
1. All analytics events fire correctly
2. Conversion tracking works
3. Social media previews look good
4. Email confirmations are sent
5. Forms validate properly
6. Mobile responsiveness
7. Page load speed
8. Accessibility (WCAG AA compliance)

## Environment Variables

Add these to your `.env` file or hosting platform:

```bash
# Analytics
GA4_MEASUREMENT_ID=G-XXXXXXXXXX
SEGMENT_WRITE_KEY=your_segment_key

# Email Service
SENDGRID_API_KEY=your_sendgrid_key
MAILCHIMP_API_KEY=your_mailchimp_key
MAILCHIMP_AUDIENCE_ID=your_audience_id

# SEO
SITE_URL=https://yourdomain.com
OG_IMAGE_URL=https://yourdomain.com/static/og-image.png
```

## Production Checklist

Before launching:
- [ ] Analytics tracking code added with real ID
- [ ] OG image created and uploaded
- [ ] Email confirmation working
- [ ] Privacy policy and terms pages created
- [ ] Cookie consent implemented (if needed)
- [ ] SSL certificate active
- [ ] Custom domain configured
- [ ] All meta tags updated with production URLs
- [ ] Sitemap submitted to Google Search Console
- [ ] 404 page created
- [ ] Error tracking setup (e.g., Sentry)
- [ ] Performance optimized
- [ ] Accessibility tested
