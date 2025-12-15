/**
 * E2E Notes Collapsed By Default Spec
 * 
 * Tests that the premium results renderer:
 * - Renders notes in a collapsed <details> element
 * - Notes are not mixed into the caption
 * - Notes summary shows "Strategy notes (optional)"
 * - Notes can be expanded by clicking the summary
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

function assertNotEqual(actual, expected, message) {
  if (actual === expected) {
    throw new Error(`${message || 'Assertion failed'}: expected ${actual} to not equal ${expected}`);
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

function assertFalse(value, message) {
  if (value) {
    throw new Error(message || 'Expected value to be falsy');
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

function assertNotContains(haystack, needle, message) {
  if (!haystack || typeof haystack !== 'string') {
    throw new Error(`${message || 'Assertion failed'}: haystack must be a string`);
  }
  if (haystack.includes(needle)) {
    throw new Error(`${message || 'String should not be found'}: "${needle}" was found in "${haystack}"`);
  }
}

// Mock social post card data with notes
const mockPostCardWithNotes = {
  platform: 'instagram',
  caption: 'Check out our latest product launch! 🚀\n\nWe\'re excited to share this with you.',
  hashtags: ['#product', '#launch', '#excited'],
  notes: [
    'This is a promotional post',
    'Target audience: early adopters',
    'Best time to post: 9am EST'
  ]
};

const mockPostCardWithoutNotes = {
  platform: 'facebook',
  caption: 'Happy Friday everyone! Hope you have a great weekend.',
  hashtags: ['#Friday', '#Weekend']
};

// Helper to render a test card
function renderTestCard(card) {
  const container = document.createElement('div');
  container.id = 'test-notes-container';
  document.body.appendChild(container);
  
  if (window.SocialCopyFirstRenderer) {
    const cardEl = window.SocialCopyFirstRenderer.renderSocialPostCard(card, 0);
    container.appendChild(cardEl);
  }
  
  return container;
}

// Helper to clean up test elements
function cleanupTestElements() {
  const container = document.getElementById('test-notes-container');
  if (container) {
    container.remove();
  }
}

// Tests
test('Notes are rendered in a <details> element', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const detailsEl = container.querySelector('details.notes-details');
  assertNotNull(detailsEl, 'Notes should be in a <details> element with notes-details class');
  
  cleanupTestElements();
});

test('Notes <details> element is closed by default', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const detailsEl = container.querySelector('details.notes-details');
  assertNotNull(detailsEl, 'Notes details element should exist');
  assertFalse(detailsEl.open, 'Details element should be closed by default');
  
  cleanupTestElements();
});

test('Notes summary shows correct text', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const summaryEl = container.querySelector('details.notes-details summary');
  assertNotNull(summaryEl, 'Summary element should exist');
  assertContains(summaryEl.textContent, 'Strategy notes', 'Summary should contain "Strategy notes"');
  assertContains(summaryEl.textContent, 'optional', 'Summary should indicate notes are optional');
  
  cleanupTestElements();
});

test('Notes are rendered in a list', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const notesList = container.querySelector('.notes-list');
  assertNotNull(notesList, 'Notes list should exist');
  
  const listItems = notesList.querySelectorAll('li');
  assertEqual(listItems.length, 3, 'Should have 3 note items');
  
  cleanupTestElements();
});

test('Notes content is correct', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const notesList = container.querySelector('.notes-list');
  const listItems = notesList.querySelectorAll('li');
  
  assertContains(listItems[0].textContent, 'promotional post', 'First note should contain expected text');
  assertContains(listItems[1].textContent, 'early adopters', 'Second note should contain expected text');
  assertContains(listItems[2].textContent, 'Best time to post', 'Third note should contain expected text');
  
  cleanupTestElements();
});

test('Notes are not mixed into the caption', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const captionText = container.querySelector('.caption-text');
  assertNotNull(captionText, 'Caption text should exist');
  
  // Check that caption doesn't contain any note text
  assertNotContains(captionText.textContent, 'promotional post', 'Caption should not contain note text');
  assertNotContains(captionText.textContent, 'early adopters', 'Caption should not contain note text');
  assertNotContains(captionText.textContent, 'Best time to post', 'Caption should not contain note text');
  
  // Check that caption only contains the actual caption content
  assertContains(captionText.textContent, 'Check out our latest product', 'Caption should contain caption text');
  
  cleanupTestElements();
});

test('No notes element when notes are not present', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithoutNotes);
  
  const detailsEl = container.querySelector('details.notes-details');
  assertEqual(detailsEl, null, 'Notes details should not exist when no notes are present');
  
  cleanupTestElements();
});

test('Notes section is positioned after main content', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const cardEl = container.querySelector('.social-post-card');
  const children = Array.from(cardEl.children);
  
  const detailsEl = cardEl.querySelector('details.notes-details');
  const detailsIndex = children.indexOf(detailsEl);
  
  // Details should be one of the last elements (after caption, hashtags, copy buttons)
  assertTrue(detailsIndex > 2, 'Notes should appear after main content elements');
  
  cleanupTestElements();
});

test('Notes details has correct CSS class', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const detailsEl = container.querySelector('details.notes-details');
  assertTrue(detailsEl.classList.contains('notes-details'), 'Details should have notes-details class');
  
  cleanupTestElements();
});

test('Can expand notes by opening details', () => {
  cleanupTestElements();
  const container = renderTestCard(mockPostCardWithNotes);
  
  const detailsEl = container.querySelector('details.notes-details');
  assertNotNull(detailsEl, 'Details element should exist');
  
  // Initially closed
  assertFalse(detailsEl.open, 'Should be closed initially');
  
  // Open it
  detailsEl.open = true;
  assertTrue(detailsEl.open, 'Should be open after setting open=true');
  
  // Verify notes list is now visible
  const notesList = detailsEl.querySelector('.notes-list');
  assertNotNull(notesList, 'Notes list should be accessible when open');
  
  cleanupTestElements();
});

// Run all tests
async function runTests() {
  console.log('Running E2E Notes Collapsed By Default Tests...\n');
  
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
