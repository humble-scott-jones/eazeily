/**
 * Profile Hydrator V2
 * 
 * A stable, cacheable profile hydration module for generator pages.
 * Provides deterministic UX when profile data is missing, partial, or unavailable.
 * 
 * Usage:
 *   import { hydrateProfileV2 } from '/static/js/profile_hydrator_v2.js';
 *   const result = await hydrateProfileV2({ timeoutMs: 10000 });
 */

(function(window) {
  'use strict';

  const PROFILE_CACHE_KEY_V2 = 'eazeily_profile_v2_cache';
  const PROFILE_CACHE_TTL_MS = 24 * 60 * 60 * 1000; // 24 hours
  const DEFAULT_TIMEOUT_MS = 10000;

  // State machine: idle → loading → loaded/error
  let hydrationState = {
    state: 'idle',
    profile: null,
    profile_status: null,
    warnings: [],
    request_id: null,
    error: null,
    timestamp: null
  };

  /**
   * Hydrate profile from /api/profile_v2 endpoint with caching and fallback
   * @param {Object} options - Configuration options
   * @param {number} options.timeoutMs - Request timeout in milliseconds (default: 10000)
   * @param {boolean} options.bypassCache - Skip cache and force fresh fetch (default: false)
   * @returns {Promise<Object>} Hydration result with state, profile, warnings, etc.
   */
  async function hydrateProfileV2(options = {}) {
    const { timeoutMs = DEFAULT_TIMEOUT_MS, bypassCache = false } = options;

    // Check if already loading
    if (hydrationState.state === 'loading') {
      console.debug('[ProfileHydratorV2] Already loading, waiting for current request');
      // Wait for current request to complete
      await new Promise(resolve => {
        const check = setInterval(() => {
          if (hydrationState.state !== 'loading') {
            clearInterval(check);
            resolve();
          }
        }, 100);
      });
      return { ...hydrationState };
    }

    // Return cached result if available and not bypassing cache
    if (!bypassCache && hydrationState.state !== 'idle') {
      console.debug('[ProfileHydratorV2] Returning cached hydration state:', hydrationState.state);
      return { ...hydrationState };
    }

    // Try to use cached profile first (unless bypassing)
    if (!bypassCache) {
      const cached = getCachedProfile();
      if (cached) {
        console.debug('[ProfileHydratorV2] Using cached profile from localStorage');
        hydrationState = {
          state: 'loaded',
          profile: cached.profile,
          profile_status: cached.profile_status,
          warnings: cached.warnings || [],
          request_id: cached.request_id || null,
          error: null,
          timestamp: cached.timestamp
        };
        return { ...hydrationState };
      }
    }

    // Start fresh fetch
    hydrationState.state = 'loading';
    hydrationState.error = null;

    const controller = new AbortController();
    const timeoutId = setTimeout(() => {
      controller.abort();
    }, timeoutMs);

    try {
      const response = await fetch('/api/profile_v2', {
        method: 'GET',
        credentials: 'include',
        signal: controller.signal,
        headers: {
          'Accept': 'application/json'
        }
      });

      clearTimeout(timeoutId);

      const body = await response.json();

      // Check for endpoint not found (404) - fallback to legacy
      if (response.status === 404) {
        console.debug('[ProfileHydratorV2] Endpoint not found, trying legacy /api/profile');
        return await fallbackToLegacyProfile(timeoutMs);
      }

      // Check for auth error (401)
      if (response.status === 401) {
        hydrationState = {
          state: 'error',
          profile: null,
          profile_status: 'missing',
          warnings: ['Authentication required'],
          request_id: body.request_id || null,
          error: {
            code: 'auth_required',
            message: body.error?.message || 'Authentication required'
          },
          timestamp: Date.now()
        };
        return { ...hydrationState };
      }

      // Check for other errors
      if (!response.ok || body.ok === false) {
        const errorMessage = body.error?.message || `HTTP ${response.status}`;
        hydrationState = {
          state: 'error',
          profile: null,
          profile_status: null,
          warnings: [],
          request_id: body.request_id || null,
          error: {
            code: body.error?.code || 'fetch_failed',
            message: errorMessage
          },
          timestamp: Date.now()
        };
        return { ...hydrationState };
      }

      // Success - normalize and cache the profile
      const profile = body.profile || {};
      const profile_status = body.profile_status || 'ready';
      const warnings = body.warnings || [];

      hydrationState = {
        state: 'loaded',
        profile,
        profile_status,
        warnings,
        request_id: body.request_id || null,
        error: null,
        timestamp: Date.now()
      };

      // Cache successful result
      cacheProfile({
        profile,
        profile_status,
        warnings,
        request_id: body.request_id,
        timestamp: Date.now()
      });

      return { ...hydrationState };

    } catch (err) {
      clearTimeout(timeoutId);

      // Check if it was a timeout
      const isTimeout = err.name === 'AbortError';
      const errorMessage = isTimeout 
        ? 'Request timed out. Please check your connection and retry.'
        : err.message || 'Network error';

      // Try to use cached profile as fallback
      const cached = getCachedProfile();
      if (cached) {
        console.debug('[ProfileHydratorV2] Using stale cache due to fetch error');
        hydrationState = {
          state: 'loaded',
          profile: cached.profile,
          profile_status: cached.profile_status,
          warnings: [...(cached.warnings || []), `Using cached data (${errorMessage})`],
          request_id: cached.request_id || null,
          error: null,
          timestamp: cached.timestamp
        };
        return { ...hydrationState };
      }

      // No cache available - return error
      hydrationState = {
        state: 'error',
        profile: null,
        profile_status: null,
        warnings: [],
        request_id: null,
        error: {
          code: isTimeout ? 'timeout' : 'network_error',
          message: errorMessage
        },
        timestamp: Date.now()
      };

      return { ...hydrationState };
    }
  }

  /**
   * Fallback to legacy /api/profile endpoint
   */
  async function fallbackToLegacyProfile(timeoutMs) {
    console.debug('[ProfileHydratorV2] Falling back to legacy /api/profile endpoint');
    
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

    try {
      const response = await fetch('/api/profile', {
        method: 'GET',
        credentials: 'include',
        signal: controller.signal
      });

      clearTimeout(timeoutId);
      const body = await response.json();

      if (!response.ok || body.ok === false) {
        throw new Error(body.error?.message || `HTTP ${response.status}`);
      }

      // Normalize legacy response to v2 format
      const profile = body.profile || {};
      const profile_status = body.profile_status || 'ready';

      hydrationState = {
        state: 'loaded',
        profile,
        profile_status,
        warnings: body.warnings || [],
        request_id: body.request_id || null,
        error: null,
        timestamp: Date.now()
      };

      return { ...hydrationState };

    } catch (err) {
      clearTimeout(timeoutId);
      
      hydrationState = {
        state: 'error',
        profile: null,
        profile_status: null,
        warnings: [],
        request_id: null,
        error: {
          code: 'legacy_fallback_failed',
          message: err.message || 'Legacy endpoint failed'
        },
        timestamp: Date.now()
      };

      return { ...hydrationState };
    }
  }

  /**
   * Cache profile to localStorage
   */
  function cacheProfile(data) {
    try {
      localStorage.setItem(PROFILE_CACHE_KEY_V2, JSON.stringify(data));
      console.debug('[ProfileHydratorV2] Profile cached successfully');
    } catch (err) {
      console.warn('[ProfileHydratorV2] Failed to cache profile:', err);
    }
  }

  /**
   * Get cached profile from localStorage (with TTL check)
   */
  function getCachedProfile() {
    try {
      const raw = localStorage.getItem(PROFILE_CACHE_KEY_V2);
      if (!raw) return null;

      const cached = JSON.parse(raw);
      const age = Date.now() - (cached.timestamp || 0);

      // Check if cache is expired
      if (age > PROFILE_CACHE_TTL_MS) {
        console.debug('[ProfileHydratorV2] Cache expired, removing');
        localStorage.removeItem(PROFILE_CACHE_KEY_V2);
        return null;
      }

      return cached;
    } catch (err) {
      console.warn('[ProfileHydratorV2] Failed to read cache:', err);
      return null;
    }
  }

  /**
   * Clear cached profile
   */
  function clearProfileCache() {
    try {
      localStorage.removeItem(PROFILE_CACHE_KEY_V2);
      hydrationState = {
        state: 'idle',
        profile: null,
        profile_status: null,
        warnings: [],
        request_id: null,
        error: null,
        timestamp: null
      };
      console.debug('[ProfileHydratorV2] Cache cleared');
    } catch (err) {
      console.warn('[ProfileHydratorV2] Failed to clear cache:', err);
    }
  }

  // Export API
  if (typeof window !== 'undefined') {
    window.__EAZEILY__ = window.__EAZEILY__ || {};
    window.__EAZEILY__.profileHydrator = {
      hydrateProfileV2,
      clearProfileCache,
      getState: () => ({ ...hydrationState })
    };
  }

  // Also export as global for easier access (optional)
  if (typeof window !== 'undefined') {
    window.hydrateProfileV2 = hydrateProfileV2;
  }

})(typeof window !== 'undefined' ? window : {});
