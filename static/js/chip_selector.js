/**
 * Chip Selector Module
 * 
 * Handles loading, rendering, and persisting chip selections for content generation.
 * Integrates with industry packs and user preferences.
 */

(function(window) {
  'use strict';

  const CHIP_STORAGE_KEY = 'eazeily_chip_selections_cache';
  const CHIP_STORAGE_TTL_MS = 72 * 60 * 60 * 1000; // 72 hours
  const DEBOUNCE_SAVE_MS = 1000; // Debounce saving to backend
  
  // State
  let currentIndustry = null;
  let allChipsByCategory = {}; // All available chips from industry pack
  let selectedChipIds = {}; // Currently selected chip IDs by category
  let visibleChipsByCategory = {}; // Visible chips (for "show more" feature)
  let savePendingTimeout = null;
  
  // Category configs
  const CHIP_CATEGORIES = {
    focus_topics: {
      containerId: 'focus-topics-chips',
      initialVisible: 6,
      label: 'Focus topics'
    },
    audience_chips: {
      containerId: 'audience-chips',
      initialVisible: 4,
      label: 'Audience'
    },
    offer_chips: {
      containerId: 'offer-chips',
      initialVisible: 4,
      label: 'Offers'
    },
    proof_chips: {
      containerId: 'proof-chips',
      initialVisible: 4,
      label: 'Proof'
    }
  };

  /**
   * Initialize chip selector for a given industry
   * @param {string} industry - Industry ID (e.g., 'salon', 'dentist')
   * @returns {Promise<void>}
   */
  async function initChipSelector(industry) {
    if (!industry) {
      console.debug('[ChipSelector] No industry provided, hiding chip section');
      hideChipSection();
      return;
    }

    currentIndustry = industry;
    console.debug('[ChipSelector] Initializing for industry:', industry);

    try {
      // Load industry pack chips
      const packChips = await fetchIndustryPackChips(industry);
      allChipsByCategory = packChips;

      // Try to load saved selections (user prefs first, then pack recommended)
      const savedSelections = await fetchUserChipSelections(industry);
      
      if (savedSelections.has_saved_selections) {
        console.debug('[ChipSelector] Using saved user selections');
        selectedChipIds = savedSelections.selections;
      } else {
        console.debug('[ChipSelector] No saved selections, using pack recommendations');
        selectedChipIds = getPackRecommendedSelections(packChips);
      }

      // Initialize visible chips (start with limited set)
      initializeVisibleChips();

      // Render all chip groups
      renderAllChipGroups();

      // Show chip section
      showChipSection();

      // Set up event listeners
      setupEventListeners();

    } catch (err) {
      console.error('[ChipSelector] Failed to initialize:', err);
      hideChipSection();
    }
  }

  /**
   * Fetch chip presets from industry pack API
   */
  async function fetchIndustryPackChips(industry) {
    const response = await fetch(`/api/industry_packs/${industry}/chips`, {
      method: 'GET',
      credentials: 'include',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`Failed to fetch chips: ${response.status}`);
    }

    const data = await response.json();
    if (!data.ok) {
      throw new Error(data.error?.message || 'Failed to load chips');
    }

    return data.chip_presets || {};
  }

  /**
   * Fetch saved user chip selections from backend
   */
  async function fetchUserChipSelections(industry) {
    try {
      const response = await fetch(`/api/user_chip_selections?industry=${encodeURIComponent(industry)}`, {
        method: 'GET',
        credentials: 'include',
        headers: { 'Accept': 'application/json' }
      });

      if (!response.ok) {
        console.warn('[ChipSelector] Failed to fetch saved selections, using defaults');
        return { has_saved_selections: false, selections: {} };
      }

      const data = await response.json();
      if (!data.ok) {
        return { has_saved_selections: false, selections: {} };
      }

      return data;
    } catch (err) {
      console.warn('[ChipSelector] Error fetching saved selections:', err);
      return { has_saved_selections: false, selections: {} };
    }
  }

  /**
   * Get recommended chip selections from pack (first N chips per category)
   */
  function getPackRecommendedSelections(packChips) {
    const selections = {};
    const recommendedCounts = {
      focus_topics: 3,
      audience_chips: 2,
      offer_chips: 2,
      proof_chips: 2
    };

    Object.keys(CHIP_CATEGORIES).forEach(category => {
      const chips = packChips[category] || [];
      const count = recommendedCounts[category] || 2;
      // Select first N chip IDs
      selections[category] = chips.slice(0, count).map(chip => chip.id);
    });

    return selections;
  }

  /**
   * Initialize visible chips for each category (show limited set initially)
   */
  function initializeVisibleChips() {
    Object.keys(CHIP_CATEGORIES).forEach(category => {
      const config = CHIP_CATEGORIES[category];
      const allChips = allChipsByCategory[category] || [];
      visibleChipsByCategory[category] = allChips.slice(0, config.initialVisible);
    });
  }

  /**
   * Render all chip groups
   */
  function renderAllChipGroups() {
    Object.keys(CHIP_CATEGORIES).forEach(category => {
      renderChipGroup(category);
    });
  }

  /**
   * Render a single chip group
   */
  function renderChipGroup(category) {
    const config = CHIP_CATEGORIES[category];
    const container = document.getElementById(config.containerId);
    if (!container) {
      console.warn(`[ChipSelector] Container not found: ${config.containerId}`);
      return;
    }

    // Clear existing chips
    container.innerHTML = '';

    // Get visible chips for this category
    const visibleChips = visibleChipsByCategory[category] || [];
    const selectedIds = selectedChipIds[category] || [];

    // Render each visible chip
    visibleChips.forEach(chip => {
      const chipEl = createChipElement(chip, category, selectedIds.includes(chip.id));
      container.appendChild(chipEl);
    });

    // Update "Show more" button visibility
    updateShowMoreButton(category);
  }

  /**
   * Create a chip button element
   */
  function createChipElement(chip, category, isSelected) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = isSelected ? 'chip chip--active' : 'chip';
    btn.textContent = chip.label;
    btn.dataset.chipId = chip.id;
    btn.dataset.chipCategory = category;
    btn.setAttribute('aria-pressed', isSelected ? 'true' : 'false');

    btn.addEventListener('click', () => {
      toggleChipSelection(chip.id, category);
    });

    return btn;
  }

  /**
   * Toggle chip selection
   */
  function toggleChipSelection(chipId, category) {
    if (!selectedChipIds[category]) {
      selectedChipIds[category] = [];
    }

    const idx = selectedChipIds[category].indexOf(chipId);
    if (idx >= 0) {
      // Deselect
      selectedChipIds[category].splice(idx, 1);
    } else {
      // Select
      selectedChipIds[category].push(chipId);
    }

    // Re-render this chip group
    renderChipGroup(category);

    // Save to localStorage immediately
    saveToLocalStorage();

    // Debounce save to backend
    debounceSaveToBackend();
  }

  /**
   * Show more chips in a category
   */
  function showMoreChips(category) {
    const allChips = allChipsByCategory[category] || [];
    visibleChipsByCategory[category] = allChips;
    renderChipGroup(category);
  }

  /**
   * Add custom chip via write-in
   */
  function addCustomChip(category) {
    const label = prompt(`Enter a custom ${CHIP_CATEGORIES[category].label.toLowerCase()}:`);
    if (!label || !label.trim()) return;

    const trimmed = label.trim();
    
    // Generate a unique ID for custom chip
    const customId = `custom_${category}_${Date.now()}`;
    
    // Create chip object
    const customChip = { id: customId, label: trimmed };
    
    // Add to allChips for this category
    if (!allChipsByCategory[category]) {
      allChipsByCategory[category] = [];
    }
    allChipsByCategory[category].push(customChip);
    
    // Add to visible chips
    if (!visibleChipsByCategory[category]) {
      visibleChipsByCategory[category] = [];
    }
    visibleChipsByCategory[category].push(customChip);
    
    // Auto-select the custom chip
    if (!selectedChipIds[category]) {
      selectedChipIds[category] = [];
    }
    selectedChipIds[category].push(customId);
    
    // Re-render
    renderChipGroup(category);
    
    // Save
    saveToLocalStorage();
    debounceSaveToBackend();
  }

  /**
   * Update "Show more" button state
   */
  function updateShowMoreButton(category) {
    const btn = document.querySelector(`[data-show-more="${category}"]`);
    if (!btn) return;

    const allChips = allChipsByCategory[category] || [];
    const visibleChips = visibleChipsByCategory[category] || [];

    if (visibleChips.length >= allChips.length) {
      btn.style.display = 'none';
    } else {
      btn.style.display = 'inline-block';
      btn.textContent = `Show more (${allChips.length - visibleChips.length} more)`;
    }
  }

  /**
   * Save selections to localStorage
   */
  function saveToLocalStorage() {
    try {
      const data = {
        industry: currentIndustry,
        selections: selectedChipIds,
        timestamp: Date.now()
      };
      localStorage.setItem(CHIP_STORAGE_KEY, JSON.stringify(data));
      console.debug('[ChipSelector] Saved to localStorage');
    } catch (err) {
      console.warn('[ChipSelector] Failed to save to localStorage:', err);
    }
  }

  /**
   * Debounced save to backend
   */
  function debounceSaveToBackend() {
    if (savePendingTimeout) {
      clearTimeout(savePendingTimeout);
    }

    savePendingTimeout = setTimeout(() => {
      saveToBackend();
    }, DEBOUNCE_SAVE_MS);
  }

  /**
   * Save selections to backend
   */
  async function saveToBackend() {
    try {
      const response = await fetch('/api/user_chip_selections', {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json'
        },
        body: JSON.stringify({
          industry: currentIndustry,
          selections: selectedChipIds
        })
      });

      if (response.ok) {
        console.debug('[ChipSelector] Saved to backend');
      } else {
        console.warn('[ChipSelector] Failed to save to backend:', response.status);
      }
    } catch (err) {
      console.warn('[ChipSelector] Error saving to backend:', err);
    }
  }

  /**
   * Get current selections (for use by generation logic)
   */
  function getSelectedChips() {
    return { ...selectedChipIds };
  }

  /**
   * Show chip section
   */
  function showChipSection() {
    const section = document.getElementById('chip-suggestions-row');
    if (section) {
      section.style.display = '';
    }
  }

  /**
   * Hide chip section
   */
  function hideChipSection() {
    const section = document.getElementById('chip-suggestions-row');
    if (section) {
      section.style.display = 'none';
    }
  }

  /**
   * Set up event listeners for show more and add custom buttons
   */
  function setupEventListeners() {
    // Show more buttons
    document.querySelectorAll('[data-show-more]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const category = e.target.dataset.showMore;
        showMoreChips(category);
      });
    });

    // Add custom buttons
    document.querySelectorAll('[data-add-custom]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        const category = e.target.dataset.addCustom;
        addCustomChip(category);
      });
    });
  }

  /**
   * Reset chips for a new industry
   */
  async function resetForIndustry(industry) {
    await initChipSelector(industry);
  }

  // Export API
  if (typeof window !== 'undefined') {
    window.__EAZEILY__ = window.__EAZEILY__ || {};
    window.__EAZEILY__.chipSelector = {
      init: initChipSelector,
      reset: resetForIndustry,
      getSelectedChips,
      getState: () => ({
        industry: currentIndustry,
        selections: { ...selectedChipIds }
      })
    };
  }

  // Also export as global for easier access
  if (typeof window !== 'undefined') {
    window.initChipSelector = initChipSelector;
    window.getSelectedChips = getSelectedChips;
  }

})(typeof window !== 'undefined' ? window : {});
