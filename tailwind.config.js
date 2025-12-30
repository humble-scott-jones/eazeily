/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./templates/**/*.html",
    "./static/**/*.js",
  ],
  theme: {
    extend: {
      colors: {
        'brand-primary': '#4F46E5', // Primary action color
        'surface-base': '#FFFFFF',  // White for backgrounds
        'surface-light': '#F9FAFB', // Off-white for backgrounds
      },
      fontSize: {
        'h1': ['3rem', { lineHeight: '1.2' }],   // H1 size
        'h2': ['2.25rem', { lineHeight: '1.25' }], // H2 size
        'h3': ['1.75rem', { lineHeight: '1.3' }],  // H3 size
        'body-lg': ['1.125rem', { lineHeight: '1.6' }], // Larger body text
        'body-base': ['1rem', { lineHeight: '1.5' }],   // Base body text
        'body-sm': ['0.875rem', { lineHeight: '1.4' }], // Small body text
      },
    },
  },
  plugins: [],
}
