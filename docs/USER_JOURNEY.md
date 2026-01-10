# User Journey & Key Use Cases

## Primary User Persona
Small business owners and entrepreneurs who need to create social media content but lack time or writing expertise.

## Key Use Cases

### Use Case 1: New User Onboarding (Happy Path)
**Goal**: Get from signup to first generated content in under 5 minutes

**Steps**:
1. User discovers Eazeily and clicks "Sign Up"
2. User enters email and password → Creates account
3. User is guided through quick 3-step brand setup:
   - **Step 1**: Business basics (name, industry) 
   - **Step 2**: Add website URL → AI auto-fills brand profile
   - **Step 3**: Review and customize voice profile
4. User is taken to dashboard with sample generated content
5. User can immediately start generating posts

**Critical Success Factors**:
- Mobile-friendly form layout
- Website URL prominently featured
- Clear progress indication
- Auto-fill reduces manual work
- Quick time-to-value

### Use Case 2: Add Website to Profile
**Goal**: User wants to enhance their brand profile with website content

**Steps**:
1. User navigates to Brand Profile from dashboard
2. User sees prominent "Add Website" field at top
3. User pastes website URL
4. AI scrapes and suggests:
   - Brand voice characteristics
   - Key messaging
   - Sample copy
   - Visual style cues
5. User reviews and applies suggestions with one click
6. Profile is updated, ready for content generation

**Mobile Considerations**:
- Large, easy-to-tap input field
- Clear loading states
- Preview of suggestions before applying
- Quick apply/dismiss actions

### Use Case 3: Quick Brand Setup (Lazy Mode)
**Goal**: User wants to start fast with minimal effort

**Steps**:
1. User selects industry from dropdown
2. System pre-fills sensible defaults for that industry
3. User tweaks 1-2 fields if desired
4. User saves and starts generating

**Benefits**:
- Reduces cognitive load
- Works for users without website
- Gets users to value faster

## Mobile-Specific Requirements

### Form Design
- Single column layout
- Large touch targets (min 44px)
- Progressive disclosure (show fields as needed)
- Step-by-step wizard over long scrolling form
- Clear "Next" and "Back" navigation

### Website Input
- Primary call-to-action position
- Auto-focus on mobile
- Clear examples/placeholder
- Paste button on mobile devices
- Permission consent inline

### AI Helper
- Collapsible by default on mobile
- Bottom sheet or modal pattern
- Non-blocking - user can continue without it
- Clear value proposition

### Navigation
- Hide sidebar on auth pages (signup/login)
- Hamburger menu with proper Z-index
- Overlay that dismisses on tap-outside
- No horizontal scroll

## Success Metrics
- Time from signup to first generated content < 5 minutes
- Mobile completion rate > 70%
- Website addition completion rate > 50%
- Mobile bounce rate < 30%
