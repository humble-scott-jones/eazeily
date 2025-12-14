/**
 * ChipGroup - A reusable component for displaying and managing chip selections
 * 
 * Features:
 * - Single/multi-select with max limit enforcement
 * - "Show more" for large lists (>10 chips)
 * - "Other..." write-in capability
 * - Custom chip creation and persistence
 */

class ChipGroup {
  /**
   * @param {Object} config
   * @param {string} config.containerId - DOM element ID for the chip group
   * @param {string} config.title - Title of the chip group
   * @param {string} config.subtitle - Subtitle/description
   * @param {Array<{id: string, label: string}>} config.chips - Available chips
   * @param {Array<string>} config.selectedIds - Currently selected chip IDs
   * @param {number} config.maxSelect - Maximum number of chips that can be selected
   * @param {function(Array<string>): void} config.onChangeSelectedIds - Callback when selection changes
   * @param {boolean} config.allowWriteIn - Whether to show "Other..." option
   * @param {string} config.groupKey - Key for storing custom chips (e.g., 'focus_topics')
   */
  constructor(config) {
    this.containerId = config.containerId;
    this.title = config.title;
    this.subtitle = config.subtitle;
    this.chips = config.chips || [];
    this.selectedIds = new Set(config.selectedIds || []);
    this.maxSelect = config.maxSelect || 5;
    this.onChangeSelectedIds = config.onChangeSelectedIds || (() => {});
    this.allowWriteIn = config.allowWriteIn !== false;
    this.groupKey = config.groupKey;
    
    this.showingAll = false;
    this.writeInMode = false;
    
    this.render();
  }
  
  /**
   * Update the selected IDs and re-render
   */
  setSelectedIds(ids) {
    this.selectedIds = new Set(ids || []);
    this.render();
  }
  
  /**
   * Add a custom chip to the list
   */
  addCustomChip(label) {
    // Generate a stable ID for the custom chip
    const id = this._generateChipId(label);
    
    // Add to chips list if not already present
    if (!this.chips.find(c => c.id === id)) {
      this.chips.push({ id, label, custom: true });
    }
    
    // Auto-select the new chip
    this.selectedIds.add(id);
    
    // Save custom chip to profile
    this._saveCustomChip({ id, label });
    
    // Notify change
    this.onChangeSelectedIds(Array.from(this.selectedIds));
    
    this.render();
  }
  
  /**
   * Generate a stable ID from a label
   */
  _generateChipId(label) {
    // Simple slugify + hash to ensure uniqueness
    const slug = label.toLowerCase()
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
    
    // Add a simple hash to avoid collisions
    const hash = this._simpleHash(label) % 1000;
    return `custom_${slug}_${hash}`;
  }
  
  /**
   * Simple hash function for generating IDs
   */
  _simpleHash(str) {
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return Math.abs(hash);
  }
  
  /**
   * Save custom chip to window.answers.custom_chips
   */
  _saveCustomChip(chip) {
    if (!window.answers) return;
    
    if (!window.answers.custom_chips) {
      window.answers.custom_chips = {};
    }
    
    if (!window.answers.custom_chips[this.groupKey]) {
      window.answers.custom_chips[this.groupKey] = [];
    }
    
    // Add if not already present
    const existing = window.answers.custom_chips[this.groupKey].find(c => c.id === chip.id);
    if (!existing) {
      window.answers.custom_chips[this.groupKey].push(chip);
    }
  }
  
  /**
   * Toggle chip selection
   */
  _toggleChip(chipId) {
    if (this.selectedIds.has(chipId)) {
      // Deselect
      this.selectedIds.delete(chipId);
    } else {
      // Select if under max
      if (this.selectedIds.size < this.maxSelect) {
        this.selectedIds.add(chipId);
      } else {
        // Show tooltip or feedback
        this._showMaxSelectFeedback();
        return;
      }
    }
    
    this.onChangeSelectedIds(Array.from(this.selectedIds));
    this.render();
  }
  
  /**
   * Show feedback when max selection reached
   */
  _showMaxSelectFeedback() {
    const container = document.getElementById(this.containerId);
    if (!container) return;
    
    // Find or create feedback element
    let feedback = container.querySelector('.chip-max-feedback');
    if (!feedback) {
      feedback = document.createElement('div');
      feedback.className = 'chip-max-feedback text-xs text-amber-600 mt-2 transition-opacity';
      container.appendChild(feedback);
    }
    
    feedback.textContent = `Maximum ${this.maxSelect} selections allowed`;
    feedback.style.opacity = '1';
    
    // Fade out after 2 seconds
    setTimeout(() => {
      feedback.style.opacity = '0';
    }, 2000);
  }
  
  /**
   * Render the chip group
   */
  render() {
    const container = document.getElementById(this.containerId);
    if (!container) {
      console.warn(`ChipGroup: Container #${this.containerId} not found`);
      return;
    }
    
    // Determine which chips to show
    const visibleChips = this.showingAll ? this.chips : this.chips.slice(0, 10);
    const hasMore = this.chips.length > 10;
    
    let html = `
      <div class="space-y-3">
        <div class="flex items-baseline justify-between">
          <div>
            <h3 class="text-base font-semibold text-slate-900">${this.title}</h3>
            ${this.subtitle ? `<p class="text-xs text-slate-600 mt-1">${this.subtitle}</p>` : ''}
          </div>
          <p class="text-xs text-slate-500">
            Choose up to ${this.maxSelect}
            ${this.selectedIds.size > 0 ? ` • <span class="font-medium text-purple-600">${this.selectedIds.size} selected</span>` : ''}
          </p>
        </div>
        
        <div class="flex flex-wrap gap-2">
    `;
    
    // Render chips
    visibleChips.forEach(chip => {
      const isSelected = this.selectedIds.has(chip.id);
      const isDisabled = !isSelected && this.selectedIds.size >= this.maxSelect;
      
      html += `
        <button
          type="button"
          class="chip-btn ${isSelected ? 'chip-selected' : ''} ${isDisabled ? 'chip-disabled' : ''}"
          data-chip-id="${chip.id}"
          ${isDisabled ? 'title="Maximum selections reached"' : ''}
        >
          ${chip.label}
        </button>
      `;
    });
    
    // Show more button
    if (hasMore && !this.showingAll) {
      html += `
        <button
          type="button"
          class="chip-show-more"
          data-action="show-more"
        >
          Show more (${this.chips.length - 10})
        </button>
      `;
    }
    
    // Other... button
    if (this.allowWriteIn && !this.writeInMode) {
      html += `
        <button
          type="button"
          class="chip-other-btn"
          data-action="write-in"
        >
          Other…
        </button>
      `;
    }
    
    html += `</div>`;
    
    // Write-in input
    if (this.writeInMode) {
      html += `
        <div class="write-in-input bg-slate-50 rounded-lg p-3 border border-slate-300">
          <input
            type="text"
            id="${this.containerId}-write-in"
            class="w-full input text-sm py-2 px-3 rounded border-slate-300 focus:border-purple-500 focus:ring-purple-500"
            placeholder="Type your own (2–6 words)…"
            maxlength="50"
          />
          <div class="flex gap-2 mt-2">
            <button
              type="button"
              class="btn-sm bg-purple-600 text-white hover:bg-purple-700 rounded px-3 py-1 text-sm"
              data-action="add-write-in"
            >
              Add
            </button>
            <button
              type="button"
              class="btn-sm bg-slate-200 text-slate-700 hover:bg-slate-300 rounded px-3 py-1 text-sm"
              data-action="cancel-write-in"
            >
              Cancel
            </button>
          </div>
        </div>
      `;
    }
    
    html += `</div>`;
    
    container.innerHTML = html;
    
    // Attach event listeners
    this._attachEventListeners();
  }
  
  /**
   * Attach event listeners to rendered elements
   */
  _attachEventListeners() {
    const container = document.getElementById(this.containerId);
    if (!container) return;
    
    // Chip click handlers
    container.querySelectorAll('.chip-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const chipId = btn.dataset.chipId;
        this._toggleChip(chipId);
      });
    });
    
    // Show more handler
    const showMoreBtn = container.querySelector('[data-action="show-more"]');
    if (showMoreBtn) {
      showMoreBtn.addEventListener('click', () => {
        this.showingAll = true;
        this.render();
      });
    }
    
    // Write-in handlers
    const writeInBtn = container.querySelector('[data-action="write-in"]');
    if (writeInBtn) {
      writeInBtn.addEventListener('click', () => {
        this.writeInMode = true;
        this.render();
        // Focus the input after render
        setTimeout(() => {
          const input = document.getElementById(`${this.containerId}-write-in`);
          if (input) input.focus();
        }, 50);
      });
    }
    
    const addBtn = container.querySelector('[data-action="add-write-in"]');
    if (addBtn) {
      addBtn.addEventListener('click', () => {
        const input = document.getElementById(`${this.containerId}-write-in`);
        if (input && input.value.trim()) {
          this.addCustomChip(input.value.trim());
          this.writeInMode = false;
        }
      });
    }
    
    const cancelBtn = container.querySelector('[data-action="cancel-write-in"]');
    if (cancelBtn) {
      cancelBtn.addEventListener('click', () => {
        this.writeInMode = false;
        this.render();
      });
    }
    
    // Enter key on write-in input
    const writeInInput = document.getElementById(`${this.containerId}-write-in`);
    if (writeInInput) {
      writeInInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && writeInInput.value.trim()) {
          this.addCustomChip(writeInInput.value.trim());
          this.writeInMode = false;
        } else if (e.key === 'Escape') {
          this.writeInMode = false;
          this.render();
        }
      });
    }
  }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
  window.ChipGroup = ChipGroup;
}
