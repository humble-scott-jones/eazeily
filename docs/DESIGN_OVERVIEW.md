# Visual Design Summary

## New Pages Overview

This document describes the visual design and layout of the new landing and pricing pages.

## Landing Page (`/landing`)

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (Sticky Navigation)                                   │
│ [Logo] Togetherly    Features  Pricing  How It Works  Sign In│
│                                              [Get Started]    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│              HERO SECTION (Purple Gradient)                   │
│                                                               │
│           Social Media Content That Sounds Like You           │
│                                                               │
│     Stop stressing about what to post. Generate authentic,    │
│     on-brand social media content in minutes with AI.        │
│                                                               │
│        [Start Free Trial]  [See How It Works]                │
│                                                               │
│          No credit card required • 3-day free trial          │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│              SOCIAL PROOF (Light Gray Background)             │
│                                                               │
│     Trusted by creators, entrepreneurs, and small businesses  │
│                                                               │
│   🚀 Startups  🍕 Restaurants  💼 Consultants  🛍️ Retailers  │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│           FEATURES SECTION (White Background)                 │
│                                                               │
│       Everything You Need to Stay Consistent                  │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │  ✨ AI-Powered│  │ 🎯 Multi-    │  │ 📅 30-Day    │      │
│  │  Generation   │  │ Platform     │  │ Content Plans │      │
│  │               │  │ Support      │  │               │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ 🎨 Brand     │  │ 🖼️ Image     │  │ ⚡ Lightning  │      │
│  │ Keywords     │  │ Suggestions   │  │ Fast         │      │
│  │              │  │               │  │              │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│        HOW IT WORKS (Light Gray Background)                   │
│                                                               │
│                   How It Works                                │
│              Get started in 3 simple steps                    │
│                                                               │
│    ┌───┐           ┌───┐           ┌───┐                    │
│    │ 1 │           │ 2 │           │ 3 │                    │
│    └───┘           └───┘           └───┘                    │
│  Set Up Your    Generate       Review & Post                 │
│   Profile        Content                                      │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│              PRICING SECTION (White Background)               │
│                                                               │
│              Simple, Transparent Pricing                      │
│                                                               │
│  ┌──────────┐  ┌──────────────┐  ┌──────────┐              │
│  │   Free   │  │ Pro (Popular)│  │ Business  │              │
│  │   $0/mo  │  │   $19/mo     │  │  $49/mo   │              │
│  │          │  │              │  │           │              │
│  │ Features │  │  Features    │  │ Features  │              │
│  │   List   │  │    List      │  │   List    │              │
│  │          │  │              │  │           │              │
│  └──────────┘  └──────────────┘  └──────────┘              │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│           CTA SECTION (Purple Gradient)                       │
│                                                               │
│         Ready to Transform Your Social Media?                 │
│                                                               │
│      [Start Your Free Trial Now]                             │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│              FOOTER (Dark Gray Background)                    │
│                                                               │
│  [Logo] Togetherly    Product    Company    Legal            │
│                                                               │
│  © 2025 Togetherly. All rights reserved.                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Color Scheme

- **Primary Purple**: `#6366F1` (buttons, highlights)
- **Purple Gradient**: `#667eea` to `#764ba2` (hero, CTA)
- **White**: `#FFFFFF` (cards, primary background)
- **Light Gray**: `#F8F9FA` (alternating sections)
- **Dark Gray**: `#1F2937` (footer, text)
- **Text Gray**: `#64748B` (secondary text)

## Pricing Page (`/pricing`)

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│ HEADER (Same as landing page)                                │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│            PRICING HEADER (White Background)                  │
│                                                               │
│              Simple, Transparent Pricing                      │
│        Choose the plan that fits your needs.                  │
│          All plans include a 7-day free trial.               │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│         PRICING TIERS (Light Gray Background)                 │
│                                                               │
│  ┌────────────────┐ ┌────────────────┐ ┌────────────────┐  │
│  │     Free       │ │  Pro (Popular) │ │   Business     │  │
│  │                │ │                │ │                │  │
│  │     $0         │ │     $19        │ │      $49       │  │
│  │   /month       │ │   /month       │ │    /month      │  │
│  │                │ │                │ │                │  │
│  │ ✓ 3-Day Content│ │ ✓ 30-Day      │ │ ✓ 90-Day      │  │
│  │ ✓ All Platforms│ │   Content      │ │   Content      │  │
│  │ ✓ Brand        │ │ ✓ All Platforms│ │ ✓ Multiple    │  │
│  │   Keywords     │ │ ✓ Brand        │ │   Profiles     │  │
│  │ ✓ Image        │ │   Keywords     │ │ ✓ Calendar    │  │
│  │   Suggestions  │ │ ✓ Priority     │ │   Export       │  │
│  │                │ │   Support      │ │ ✓ Team        │  │
│  │                │ │ ✓ Advanced     │ │   Collaboration│  │
│  │                │ │   Customization│ │                │  │
│  │                │ │                │ │                │  │
│  │ [Get Started]  │ │ [Start Trial]  │ │ [Start Trial] │  │
│  │                │ │                │ │                │  │
│  └────────────────┘ └────────────────┘ └────────────────┘  │
│                                                               │
│                  White Card        Purple Gradient   White   │
│                                   (Scale: 105%)              │
│                                   "MOST POPULAR" Badge       │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│              FAQ SECTION (White Background)                   │
│                                                               │
│           Frequently Asked Questions                          │
│                                                               │
│  Q: Can I switch plans later?                                │
│  A: Yes! You can upgrade or downgrade at any time...         │
│                                                               │
│  Q: What payment methods do you accept?                      │
│  A: We accept all major credit cards...                      │
│                                                               │
│  [... 7 total FAQ items ...]                                 │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│           CTA SECTION (Purple Gradient)                       │
│                                                               │
│              Ready to Get Started?                            │
│      Start your free trial today. No credit card required.   │
│                                                               │
│              [Start Free Trial]                               │
│                                                               │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│              FOOTER (Same as landing page)                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Design Features

### Visual Enhancements

1. **Purple Gradient Backgrounds**
   - Hero sections: `linear-gradient(135deg, #667eea 0%, #764ba2 100%)`
   - Creates depth and visual interest
   - Consistent with brand color

2. **Card Hover Effects**
   - Smooth transitions on hover
   - Subtle lift animation (translateY(-4px))
   - Enhanced shadow on interaction

3. **Typography Hierarchy**
   - H1: 60px bold (hero titles)
   - H2: 48px bold (section headers)
   - H3: 36px bold (subsections)
   - Body: 16-20px regular
   - Clean, modern sans-serif font stack

4. **Spacing & Layout**
   - Generous whitespace between sections
   - Maximum content width: 1152px (6xl)
   - Consistent padding: 24-32px
   - Grid layouts for features (3 columns)

5. **Interactive Elements**
   - Primary CTA buttons: White on purple gradient
   - Secondary CTAs: Purple on white
   - Hover states with color transitions
   - Clear focus states for accessibility

6. **Responsive Design**
   - Mobile-first approach
   - Breakpoints: sm (640px), md (768px), lg (1024px)
   - Stack layouts on mobile
   - Touch-friendly button sizes

### Accessibility Features

- Semantic HTML structure
- ARIA labels where needed
- Proper heading hierarchy
- Sufficient color contrast (WCAG AA compliant)
- Focus indicators on interactive elements
- Alt text for images (when implemented)

## User Journey

### Landing Page Flow
1. User arrives at landing page
2. Reads hero value proposition
3. Scrolls to see features
4. Understands "How It Works"
5. Reviews pricing options
6. Clicks CTA to get started
7. Directed to main app (/index)

### Pricing Page Flow
1. User navigates to pricing
2. Compares three tiers side-by-side
3. Reads detailed feature lists
4. Reviews FAQ for questions
5. Selects appropriate tier
6. Starts free trial
7. Directed to signup/app

## Technical Implementation

### Technologies Used
- **Tailwind CSS**: Utility-first CSS framework
- **Flask Templates**: Jinja2 templating
- **Custom CSS**: Additional brand styling
- **Responsive Units**: rem, em, percentages
- **Modern CSS**: Flexbox, Grid, transitions

### Performance Considerations
- CDN-hosted Tailwind (fast loading)
- Minimal custom CSS (~100 lines)
- No JavaScript required for display
- Optimized for mobile performance
- Static content (easily cacheable)

## Next Steps for Enhancement

Potential future improvements:
1. Add actual customer testimonials
2. Include demo video or GIF
3. Add comparison table on pricing page
4. Include case studies or success stories
5. Add newsletter signup
6. Implement blog section
7. Add live chat widget
8. Include help documentation links

---

**Note**: These pages are production-ready and designed to effectively communicate the value proposition while guiding users toward conversion.
