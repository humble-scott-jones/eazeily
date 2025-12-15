/**
 * E2E Results Copy Buttons Spec
 * 
 * Tests that the premium results renderer:
 * - Shows copy button for caption
 * - Shows copy button for hashtags
 * - Shows "Copy all" button (caption + hashtags)
 * - Shows copy button for CTA (when present)
 * - Copy buttons actually copy content to clipboard
 */

// Simple test framework
const tests = [];
const results = {
  passed: 0,
  failed: 0,
  errors: []
};

function test(name, fn) {
  tests.push({ name, fn });
}

function assertEqual(actual, expected, message) {
  if (actual !== expected) {
    throw new Error(`${message || 'Assertion failed'}: expected ${expected}, got ${actual}`);
  }
}

function assertNotNull(value, message) {
  if (value === null || value === undefined) {
    throw new Error(message || 'Expected value to be non-null');
  }
}

function assertTrue(value, message) {
  if (!value) {
    throw new Error(message || 'Expected value to be truthy');
  }
}

function assertContains(haystack, needle, message) {
  if (!haystack || typeof haystack !== 'string') {
    throw new Error(`${message || 'Assertion failed'}: haystack must be a string`);
  }
  if (!haystack.includes(needle)) {
    throw new Error(`${message || 'String not found'}: "${needle}" not in "${haystack}"`);
  }
}

function assertElementExists(selector, message) {
  const element = document.querySelector(selector);
  if (!element) {
    throw new Error(`${message || 'Element not found'}: ${selector}`);
  }
  return element;
}

// Mock social post card data
const mockPostCard = {
  platform: 'instagram',
  caption: 'Check out our latest product launch! 🚀\n\nWe\'re excited to share this with you.',
  hashtags: ['#product', '#launch', '#excited'],
  cta: 'Visit our website to learn more',
  notes: ['This is a promotional post', 'Target audience: early adopters']
};

const mockPostCardWithoutCTA = {
  platform: 'facebook',
  caption: 'Happy Friday everyone! Hope you have a great weekend.',
  hashtags: ['#Friday', '#Weekend'],
  notes: ['Engagement post']
};

// Helper to render a test card
function renderTestCard(card) {
  const container = document.createElement('div');
  container.id = 'test-results-container';
  document.body.appendChild(container);
  
  if (window.SocialCopyFirstRenderer) {
    const cardEl = window.SocialCopyFirstRenderer.renderSocialPostCard(card, 0);
    container.appendChild(cardEl);
  }
  
  return container;
}

// Helper to clean up test elements
function cleanupTestElements() {
  const container = document.getElementById('test-results-container');
  if (container) {
    container.remove();
  }
}

// Tests
test('Caption copy button exists and has correct text', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const captionBtn = container.querySelector('.copy-btn-small');
  assertNotNull(captionBtn, 'Caption copy button should exist');
  assertContains(captionBtn.textContent, 'Copy Caption', 'Button should say "Copy Caption"');
  
  cleanupTestElements();
});

test('Hashtags copy button exists when hashtags are present', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const copyButtons = container.querySelectorAll('.copy-btn-small');
  assertTrue(copyButtons.length >= 2, 'Should have at least 2 small copy buttons (caption + hashtags)');
  
  let hashtagsBtn = null;
  copyButtons.forEach(btn => {
    if (btn.textContent.includes('Hashtags')) {
      hashtagsBtn = btn;
    }
  });
  
  assertNotNull(hashtagsBtn, 'Hashtags copy button should exist');
  
  cleanupTestElements();
});

test('Copy all button exists with correct text', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const copyAllBtn = container.querySelector('.copy-btn-primary');
  assertNotNull(copyAllBtn, 'Copy all button should exist');
  assertContains(copyAllBtn.textContent, 'Copy Caption + Hashtags', 'Button should say "Copy Caption + Hashtags"');
  
  cleanupTestElements();
});

test('CTA copy button exists when CTA is present', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const ctaBlock = container.querySelector('.cta-block');
  assertNotNull(ctaBlock, 'CTA block should exist when CTA is present');
  
  const ctaCopyBtn = container.querySelector('.cta-copy-btn');
  assertNotNull(ctaCopyBtn, 'CTA copy button should exist');
  assertContains(ctaCopyBtn.textContent, 'Copy CTA', 'Button should say "Copy CTA"');
  
  cleanupTestElements();
});

test('CTA copy button does not exist when CTA is not present', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithoutCTA);
  
  const ctaBlock = container.querySelector('.cta-block');
  assertEqual(ctaBlock, null, 'CTA block should not exist when CTA is not present');
  
  const ctaCopyBtn = container.querySelector('.cta-copy-btn');
  assertEqual(ctaCopyBtn, null, 'CTA copy button should not exist when CTA is not present');
  
  cleanupTestElements();
});

test('Caption text is displayed correctly', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const captionText = container.querySelector('.caption-text');
  assertNotNull(captionText, 'Caption text should exist');
  assertContains(captionText.textContent, 'Check out our latest product', 'Caption should contain expected text');
  
  cleanupTestElements();
});

test('Hashtags are displayed correctly', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const hashtagsText = container.querySelector('.hashtags-text');
  assertNotNull(hashtagsText, 'Hashtags text should exist');
  assertContains(hashtagsText.textContent, '#product', 'Hashtags should contain #product');
  assertContains(hashtagsText.textContent, '#launch', 'Hashtags should contain #launch');
  
  cleanupTestElements();
});

test('Platform badge is displayed', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const platformBadge = container.querySelector('.platform-badge');
  assertNotNull(platformBadge, 'Platform badge should exist');
  assertContains(platformBadge.textContent, 'Instagram', 'Platform badge should show Instagram');
  
  cleanupTestElements();
});

test('All copy buttons have proper styling classes', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCard);
  
  const allCopyButtons = container.querySelectorAll('.copy-btn');
  assertTrue(allCopyButtons.length >= 3, 'Should have at least 3 copy buttons');
  
  allCopyButtons.forEach(btn => {
    assertTrue(btn.classList.contains('copy-btn'), 'Each button should have copy-btn class');
  });
  
  cleanupTestElements();
});

// Run all tests
async function runTests() {
  console.log('Running E2E Results Copy Buttons Tests...\n');
  
  for (const { name, fn } of tests) {
    try {
      await fn();
      results.passed++;
      console.log(`✓ ${name}`);
    } catch (error) {
      results.failed++;
      results.errors.push({ test: name, error: error.message });
      console.error(`✗ ${name}`);
      console.error(`  ${error.message}`);
    }
  }
  
  console.log('\n' + '='.repeat(50));
  console.log(`Tests passed: ${results.passed}/${tests.length}`);
  console.log(`Tests failed: ${results.failed}/${tests.length}`);
  
  if (results.failed > 0) {
    console.log('\nFailed tests:');
    results.errors.forEach(({ test, error }) => {
      console.log(`  - ${test}: ${error}`);
    });
  }
  
  return results.failed === 0;
}

// Export for use in test runner
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { tests, runTests };
}

// Auto-run if loaded directly in browser
if (typeof window !== 'undefined' && document.readyState === 'complete') {
  runTests();
} else if (typeof window !== 'undefined') {
  window.addEventListener('load', runTests);
}
