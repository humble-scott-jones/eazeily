# Swelly Design System

## Color Palette

### Primary Colors
- **Brand Purple**: `#6366F1` (--brand)
  - Used for primary CTAs, highlights, and brand elements
  - Hover: `#5458e8` (--brand-600)
  - Light: `#eef2ff` (--brand-50)
  
- **Background**: 
  - Main: `#fbfbfd` (--sand) - Soft off-white
  - Card: `#ffffff` - Pure white for content cards

### Neutral Colors
- **Text**:
  - Primary: `#0f172a` (slate-900)
  - Secondary: `#64748b` (slate-500)
  - Tertiary: `#94a3b8` (slate-400)
  
- **Borders & Dividers**:
  - Light: `#eaeaf0`
  - Medium: `#d1d5db`
  - Focus: Brand purple with light shadow

### Accent Colors
- **Success**: `#10b981` (green-500)
- **Warning**: `#f59e0b` (amber-500)
- **Error**: `#ef4444` (red-500)
- **Info**: Brand purple

## Typography

### Font Stack
- **Primary**: System font stack for optimal performance
  - `-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif`

### Font Sizes
- **Hero Heading**: `3.5rem` (56px) on desktop, `2.5rem` (40px) on mobile
- **H1**: `2.5rem` (40px)
- **H2**: `2rem` (32px)
- **H3**: `1.5rem` (24px)
- **H4**: `1.25rem` (20px)
- **Body**: `1rem` (16px)
- **Small**: `0.875rem` (14px)
- **Tiny**: `0.75rem` (12px)

### Font Weights
- **Regular**: 400
- **Medium**: 500
- **Semibold**: 600
- **Bold**: 700

### Line Heights
- **Tight**: 1.25
- **Normal**: 1.5
- **Relaxed**: 1.75

## Spacing Scale

Based on 4px base unit:
- `xs`: 4px
- `sm`: 8px
- `md`: 12px
- `base`: 16px
- `lg`: 24px
- `xl`: 32px
- `2xl`: 48px
- `3xl`: 64px
- `4xl`: 96px

## Component Styles

### Buttons

#### Primary Button
- Background: Brand purple (#6366F1)
- Text: White
- Padding: 10px 14px
- Border radius: 10px
- Font weight: 600
- Shadow: `0 8px 22px rgba(99,102,241,.25)`
- Hover: Darker brand purple (#5458e8)

#### Secondary Button
- Background: `#f3f4f6`
- Text: `#111827`
- Border: `1px solid #e5e7eb`
- Padding: 10px 14px
- Border radius: 10px

#### Ghost Button
- Background: White
- Text: Dark gray
- Border: `1px solid #e5e7eb`
- Padding: 10px 14px
- Border radius: 10px

### Cards
- Background: White
- Border: `1px solid #eaeaf0`
- Border radius: 16px
- Padding: 18px
- Shadow: `0 4px 14px rgba(15,23,42,.04)`

### Inputs
- Border: `1px solid #d1d5db`
- Border radius: 10px
- Padding: 10px 12px
- Focus border: Brand purple
- Focus shadow: `0 0 0 3px var(--brand-50)`

## Logo

### Gradient Logo Icon
- Size: 32x32px
- Border radius: 10px
- Gradient: `radial-gradient(100% 100% at 30% 20%, #a5b4fc 0%, #6366F1 60%, #1d4ed8 100%)`
- Shadow: `0 4px 18px rgba(99,102,241,.35)`

### Logo Usage
- Always pair with "Swelly" wordmark
- Maintain minimum clear space of 8px around logo
- Do not alter gradient colors
- Use on light backgrounds only

## Accessibility

### Contrast Ratios
- All text meets WCAG AA standards (4.5:1 for normal text)
- Interactive elements have 3:1 contrast with backgrounds
- Focus states clearly visible with purple outline

### Focus States
- All interactive elements have visible focus indicators
- Focus ring: `0 0 0 3px var(--brand-50)` with brand border

### Semantic HTML
- Use proper heading hierarchy (h1, h2, h3)
- Include alt text for all images
- Use ARIA labels where appropriate
- Ensure keyboard navigation works throughout

## Responsive Breakpoints

- **Mobile**: < 640px
- **Tablet**: 640px - 1024px
- **Desktop**: > 1024px
- **Max width**: 1200px for content containers

## Animation & Transitions

### Standard Transition
- Duration: `200ms`
- Timing: `ease-in-out`

### Hover Effects
- Buttons: Background color change + subtle transform
- Cards: Border color + shadow enhancement
- Links: Underline or color change

## Icons

- Use emoji or SVG icons
- Size: 20-24px for inline icons
- Color: Match text color or brand purple
- Maintain consistent visual weight

## Best Practices

1. **Mobile First**: Design and develop for mobile, then enhance for larger screens
2. **Performance**: Keep asset sizes small, use system fonts, minimize custom CSS
3. **Consistency**: Use design tokens consistently across all pages
4. **Accessibility**: Test with keyboard, screen readers, and color contrast tools
5. **Whitespace**: Use generous spacing to improve readability and visual hierarchy
