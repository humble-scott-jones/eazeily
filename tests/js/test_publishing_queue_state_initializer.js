/**
 * Tests for Publishing Queue State Initializer
 * 
 * These tests verify that the queue state initializer:
 * - Creates window.__EAZEILY__.publishingQueueState
 * - Is idempotent (can run multiple times safely)
 * - Does not overwrite existing items
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

function assertArrayEqual(actual, expected, message) {
  if (!Array.isArray(actual) || !Array.isArray(expected)) {
    throw new Error(`${message || 'Not arrays'}`);
  }
  if (actual.length !== expected.length) {
    throw new Error(`${message || 'Array length mismatch'}: expected ${expected.length}, got ${actual.length}`);
  }
  for (let i = 0; i < actual.length; i++) {
    if (actual[i] !== expected[i]) {
      throw new Error(`${message || 'Array element mismatch'} at index ${i}: expected ${expected[i]}, got ${actual[i]}`);
    }
  }
}

// Test: Initializer creates namespace
test('initializer creates window.__EAZEILY__ namespace', function() {
  assertNotNull(window.__EAZEILY__, 'window.__EAZEILY__ should exist');
  assertTrue(typeof window.__EAZEILY__ === 'object', 'window.__EAZEILY__ should be an object');
});

// Test: Initializer creates publishingQueueState
test('initializer creates publishingQueueState', function() {
  assertNotNull(window.__EAZEILY__.publishingQueueState, 'publishingQueueState should exist');
  assertTrue(typeof window.__EAZEILY__.publishingQueueState === 'object', 'publishingQueueState should be an object');
});

// Test: Queue state has required properties
test('queue state has required properties', function() {
  const state = window.__EAZEILY__.publishingQueueState;
  assertTrue(Array.isArray(state.items), 'items should be an array');
  assertTrue(Array.isArray(state.entries), 'entries should be an array (alias)');
  assertEqual(state.status, 'idle', 'status should be idle');
  assertEqual(state.lastError, null, 'lastError should be null');
});

// Test: Back-compat alias exists
test('back-compat window.publishingQueueState alias exists', function() {
  assertNotNull(window.publishingQueueState, 'window.publishingQueueState should exist for back-compat');
  assertTrue(window.publishingQueueState === window.__EAZEILY__.publishingQueueState, 
    'window.publishingQueueState should reference the same object');
});

// Test: Idempotent initialization
test('running initializer twice does not overwrite existing items', function() {
  // Add test items to the queue
  const state = window.__EAZEILY__.publishingQueueState;
  state.items.push({ test: 'item1' });
  state.entries.push({ test: 'entry1' });
  const initialItemsLength = state.items.length;
  const initialEntriesLength = state.entries.length;
  
  // Re-run the initializer code (simulate double-include)
  const scriptContent = `
    if (typeof window !== 'undefined') {
      window.__EAZEILY__ = window.__EAZEILY__ || {};
      if (!window.__EAZEILY__.publishingQueueState) {
        window.__EAZEILY__.publishingQueueState = {
          items: [],
          entries: [],
          status: 'idle',
          lastError: null,
          lastUpdatedAt: null
        };
      }
    }
  `;
  eval(scriptContent);
  
  // Items should still be there (not cleared)
  assertEqual(state.items.length, initialItemsLength, 'items should not be cleared');
  assertEqual(state.entries.length, initialEntriesLength, 'entries should not be cleared');
  assertEqual(state.items[0].test, 'item1', 'original item should be preserved');
  assertEqual(state.entries[0].test, 'entry1', 'original entry should be preserved');
});

// Test: State mutation persists
test('mutations to queue state persist', function() {
  const state = window.__EAZEILY__.publishingQueueState;
  const initialLength = state.items.length;
  
  state.items.push({ id: 'test-mutation' });
  state.status = 'processing';
  state.lastError = 'test error';
  
  // Access state again
  const sameState = window.__EAZEILY__.publishingQueueState;
  
  assertEqual(sameState.items.length, initialLength + 1, 'mutation should persist');
  assertEqual(sameState.status, 'processing', 'status mutation should persist');
  assertEqual(sameState.lastError, 'test error', 'error mutation should persist');
});

// Run all tests
function runTests() {
  console.log('Running Publishing Queue State tests...');
  
  tests.forEach(({ name, fn }) => {
    try {
      fn();
      results.passed++;
      console.log(`✓ ${name}`);
    } catch (err) {
      results.failed++;
      results.errors.push({ name, error: err.message });
      console.error(`✗ ${name}: ${err.message}`);
    }
  });
  
  console.log(`\n${results.passed} passed, ${results.failed} failed`);
  
  return results;
}

// Export for use in test runners
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runTests, tests, results };
}

// Auto-run if loaded directly
if (typeof document !== 'undefined') {
  document.addEventListener('DOMContentLoaded', runTests);
}
