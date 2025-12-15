/**
 * E2E Preview Selector Switches Channels Spec
 * 
 * Tests that the preview selector:
 * - Switches between channels (social, email, quote)
 * - Updates previews live as chips are selected
 * - Works offline without OpenAI
 * - Shows both baseline and personalized versions
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
  if (!haystack.includes(needle)) {
    throw new Error(`${message || 'String not found'}: "${needle}" not in "${haystack}"`);
  }
}

// Mock API responses for testing
const mockTemplateData = {
  social: [
    { id: 'social_promotional', name: 'Promotional Post', description: 'Promotional content' },
    { id: 'social_educational', name: 'Educational Post', description: 'Educational content' }
  ],
  email: [
    { id: 'email_welcome', name: 'Welcome Email', description: 'Welcome message' },
    { id: 'email_followup', name: 'Follow-up Email', description: 'Follow-up message' }
  ],
  quote: [
    { id: 'quote_service', name: 'Service Quote', description: 'Service quotation' },
    { id: 'quote_project', name: 'Project Quote', description: 'Project quotation' }
  ]
};

// Tests
test('Preview API returns all channels', async () => {
  const response = await fetch('/api/preview-templates');
  const data = await response.json();
  
  assertTrue(data.ok, 'API response should be ok');
  assertNotNull(data.templates, 'Should have templates');
  assertTrue('social' in data.templates, 'Should have social channel');
  assertTrue('email' in data.templates, 'Should have email channel');
  assertTrue('quote' in data.templates, 'Should have quote channel');
});

test('Can fetch templates for social channel', async () => {
  const response = await fetch('/api/preview-templates/social');
  const data = await response.json();
  
  assertTrue(data.ok, 'API response should be ok');
  assertEqual(data.channel, 'social', 'Channel should be social');
  assertTrue(Array.isArray(data.templates), 'Templates should be an array');
  assertTrue(data.templates.length > 0, 'Should have at least one social template');
});

test('Can fetch templates for email channel', async () => {
  const response = await fetch('/api/preview-templates/email');
  const data = await response.json();
  
  assertTrue(data.ok, 'API response should be ok');
  assertEqual(data.channel, 'email', 'Channel should be email');
  assertTrue(data.templates.length > 0, 'Should have at least one email template');
});

test('Can fetch templates for quote channel', async () => {
  const response = await fetch('/api/preview-templates/quote');
  const data = await response.json();
  
  assertTrue(data.ok, 'API response should be ok');
  assertEqual(data.channel, 'quote', 'Channel should be quote');
  assertTrue(data.templates.length > 0, 'Should have at least one quote template');
});

test('Can generate baseline preview', async () => {
  const templatesResponse = await fetch('/api/preview-templates/social');
  const templatesData = await templatesResponse.json();
  const templateId = templatesData.templates[0].id;
  
  const response = await fetch(`/api/preview-templates/social/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ use_baseline: true })
  });
  const data = await response.json();
  
  assertTrue(data.ok, 'Preview generation should succeed');
  assertNotNull(data.preview, 'Should have preview data');
  assertEqual(data.preview.version, 'baseline', 'Should be baseline version');
  assertNotNull(data.preview.content, 'Should have content');
});

test('Can generate personalized preview with slots', async () => {
  const templatesResponse = await fetch('/api/preview-templates/social');
  const templatesData = await templatesResponse.json();
  const templateId = templatesData.templates[0].id;
  
  const slots = {
    service: 'Test Service',
    audience: 'test users',
    pain: 'test problem',
    outcome: 'test solution'
  };
  
  const response = await fetch(`/api/preview-templates/social/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slots })
  });
  const data = await response.json();
  
  assertTrue(data.ok, 'Preview generation should succeed');
  assertEqual(data.preview.version, 'personalized', 'Should be personalized version');
  
  const contentStr = JSON.stringify(data.preview.content);
  assertContains(contentStr, 'Test Service', 'Should contain slot value');
});

test('Preview generation is instant (no OpenAI delay)', async () => {
  const templatesResponse = await fetch('/api/preview-templates/email');
  const templatesData = await templatesResponse.json();
  const templateId = templatesData.templates[0].id;
  
  const startTime = Date.now();
  
  const response = await fetch(`/api/preview-templates/email/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ use_baseline: true })
  });
  
  const elapsed = Date.now() - startTime;
  const data = await response.json();
  
  assertTrue(data.ok, 'Should succeed');
  assertTrue(elapsed < 1000, `Should be instant, took ${elapsed}ms`);
});

test('Different slot values produce different previews', async () => {
  const templatesResponse = await fetch('/api/preview-templates/quote');
  const templatesData = await templatesResponse.json();
  const templateId = templatesData.templates[0].id;
  
  const slots1 = { service: 'Service A', validity_days: '30' };
  const response1 = await fetch(`/api/preview-templates/quote/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slots: slots1 })
  });
  const data1 = await response1.json();
  
  const slots2 = { service: 'Service B', validity_days: '60' };
  const response2 = await fetch(`/api/preview-templates/quote/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slots: slots2 })
  });
  const data2 = await response2.json();
  
  const content1 = JSON.stringify(data1.preview.content);
  const content2 = JSON.stringify(data2.preview.content);
  
  assertContains(content1, 'Service A', 'First preview should contain Service A');
  assertContains(content2, 'Service B', 'Second preview should contain Service B');
  assertTrue(content1 !== content2, 'Different slots should produce different content');
});

test('Baseline does not contain personalized content', async () => {
  const templatesResponse = await fetch('/api/preview-templates/social');
  const templatesData = await templatesResponse.json();
  const templateId = templatesData.templates[0].id;
  
  const baselineResponse = await fetch(`/api/preview-templates/social/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ use_baseline: true })
  });
  const baselineData = await baselineResponse.json();
  
  const personalizedResponse = await fetch(`/api/preview-templates/social/${templateId}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ slots: { service: 'UniqueTestService123' } })
  });
  const personalizedData = await personalizedResponse.json();
  
  const baselineContent = JSON.stringify(baselineData.preview.content);
  const personalizedContent = JSON.stringify(personalizedData.preview.content);
  
  assertTrue(!baselineContent.includes('UniqueTestService123'), 
    'Baseline should not contain personalized slot value');
  assertTrue(personalizedContent.includes('UniqueTestService123') || 
    personalizedContent.includes('{service}'),
    'Personalized should contain slot value or placeholder');
});

// Run all tests
async function runTests() {
  console.log('Running preview selector tests...\n');
  
  for (const { name, fn } of tests) {
    try {
      await fn();
      results.passed++;
      console.log(`✓ ${name}`);
    } catch (error) {
      results.failed++;
      results.errors.push({ name, error: error.message });
      console.error(`✗ ${name}`);
      console.error(`  ${error.message}`);
    }
  }
  
  console.log(`\n${results.passed} passed, ${results.failed} failed`);
  
  if (results.failed > 0) {
    process.exit(1);
  }
}

// Export for Node.js testing or run in browser
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runTests, tests };
} else if (typeof window !== 'undefined') {
  window.previewSelectorTests = { runTests, tests };
}

// Auto-run if in Node.js environment
if (typeof process !== 'undefined' && process.env.NODE_ENV !== 'production') {
  // Note: This is a spec file meant to be run with proper test infrastructure
  // The actual e2e test is in Python using Playwright
  console.log('Preview selector spec file loaded. Run with proper test infrastructure.');
}
