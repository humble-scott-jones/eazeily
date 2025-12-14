/**
 * Publishing Queue State Initializer
 * 
 * This module provides a global, idempotent queue state initializer that can be
 * safely included multiple times and works even if the queue UI isn't on the page.
 * 
 * Usage:
 *   - Include this script before any other scripts that reference queue state
 *   - Access the queue state via window.__EAZEILY__.publishingQueueState
 *   - Legacy code can use window.publishingQueueState (back-compat alias)
 */

(function() {
  'use strict';

  // Create the global namespace if it doesn't exist
  if (typeof window !== 'undefined') {
    window.__EAZEILY__ = window.__EAZEILY__ || {};
    
    // Only initialize if not already set (idempotent)
    if (!window.__EAZEILY__.publishingQueueState) {
      window.__EAZEILY__.publishingQueueState = {
        items: [],      // Primary queue items array
        entries: [],    // Secondary queue entries array (some code uses this)
        status: 'idle',
        lastError: null,
        lastUpdatedAt: null
      };
      
      console.debug('[Eazeily] Publishing queue state initialized');
    } else {
      console.debug('[Eazeily] Publishing queue state already exists, skipping initialization');
    }
    
    // Back-compat: Create legacy alias if undefined
    if (typeof window.publishingQueueState === 'undefined') {
      window.publishingQueueState = window.__EAZEILY__.publishingQueueState;
      console.debug('[Eazeily] Back-compat alias window.publishingQueueState created');
    }
  }
})();
