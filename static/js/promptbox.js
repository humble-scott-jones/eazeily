/**
 * PromptBox - Unified conversational UI component
 * Provides Copilot-style interface for onboarding and content creation
 */

// Slash command definitions
const SLASH_COMMANDS = [
  // Content commands
  { command: '/post', description: 'Create a social media post', icon: '📝', category: 'content', placeholder: 'topic', example: '/post our weekend sale', requiresInput: true },
  { command: '/caption', description: 'Write an image caption', icon: '📸', category: 'content', placeholder: 'describe the image', example: '/caption sunset beach photo', requiresInput: true },
  { command: '/script', description: 'Write a video script', icon: '🎬', category: 'content', placeholder: 'topic', example: '/script product demo video', requiresInput: true },
  { command: '/reel', description: 'Create a reel/short video script', icon: '🎥', category: 'content', placeholder: 'topic', example: '/reel behind the scenes tour', requiresInput: true },
  { command: '/email', description: 'Draft an email', icon: '✉️', category: 'content', placeholder: 'topic or recipient', example: '/email follow-up with client', requiresInput: true },
  { command: '/review', description: 'Respond to a review', icon: '⭐', category: 'content', placeholder: 'paste the review text', example: '/review "Great product but slow shipping"', requiresInput: true },
  { command: '/ad', description: 'Create ad copy', icon: '📢', category: 'content', placeholder: 'product or service', example: '/ad our new fitness app', requiresInput: true },
  { command: '/blog', description: 'Write a blog post', icon: '📰', category: 'content', placeholder: 'topic', example: '/blog 5 tips for productivity', requiresInput: true },
  
  // Profile management commands
  { command: '/profile', description: 'View and manage your brand profile', icon: '👤', category: 'profile', placeholder: null, example: '/profile', requiresInput: false },
  { command: '/update', description: 'Update a profile field', icon: '✏️', category: 'profile', placeholder: 'field and value', example: '/update voice warm and friendly', requiresInput: true },
  { command: '/voice', description: 'Update your brand voice/tone', icon: '🎤', category: 'profile', placeholder: 'how you want to sound', example: '/voice warm and professional', requiresInput: true },
  { command: '/audience', description: 'Define your target audience', icon: '🎯', category: 'profile', placeholder: 'who you serve', example: '/audience busy working parents', requiresInput: true },
  { command: '/offer', description: 'Set your key offer/value proposition', icon: '💎', category: 'profile', placeholder: 'your value proposition', example: '/offer free 30-day trial', requiresInput: true },
  { command: '/samples', description: 'Add writing samples to match your style', icon: '✍️', category: 'profile', placeholder: 'paste your writing', example: '/samples Check out our new collection!', requiresInput: true },
  { command: '/rules', description: 'Set voice rules and guidelines', icon: '📋', category: 'profile', placeholder: 'your guidelines', example: '/rules always use emojis', requiresInput: true },
  { command: '/import', description: 'Import profile from your website URL', icon: '🔗', category: 'profile', placeholder: 'url', example: '/import https://mybusiness.com', requiresInput: true },
  
  // Help command
  { command: '/help', description: 'Show all available commands', icon: '❓', category: 'help', placeholder: null, example: '/help', requiresInput: false },
];

// Profile field command mapping
const PROFILE_FIELD_MAP = {
  '/voice': 'brand_voice',
  '/audience': 'target_audience',
  '/offer': 'key_offer',
  '/samples': 'writing_samples',
  '/rules': 'voice_rules',
};

const FIELD_LABELS = {
  'brand_voice': 'Brand Voice',
  'target_audience': 'Target Audience',
  'key_offer': 'Key Offer',
  'writing_samples': 'Writing Samples',
  'voice_rules': 'Voice Rules',
  'brand_keywords': 'Brand Keywords',
  'goals': 'Goals',
};

const FIELD_EMOJI = {
  'brand_voice': '🎤',
  'target_audience': '🎯',
  'key_offer': '💎',
  'writing_samples': '✍️',
  'voice_rules': '📋',
};

// Mapping from profile field names (used by server) to slash commands
const FIELD_TO_COMMAND = {
  'Business Name': '/name',
  'Industry': '/industry',
  'Brand Voice': '/voice',
  'Target Audience': '/audience',
  'Key Offer': '/offer',
  'Writing Samples': '/samples',
  'Brand Keywords': '/keywords',
  'Goals': '/goals'
};

const WHY_IT_MATTERS = {
  'brand_voice': 'Your brand voice sets the tone for all content, ensuring consistency across posts, emails, and campaigns.',
  'target_audience': 'Knowing your audience helps me create content that speaks directly to their needs and pain points.',
  'key_offer': 'Your key offer gives me a clear hook - what makes you unique and worth choosing.',
  'writing_samples': 'Writing samples help me match your unique style so content sounds authentically like YOU.',
  'voice_rules': 'Voice rules give me specific do\'s and don\'ts to ensure content always stays on-brand.',
};

const CONTENT_IMPACT = {
  'brand_voice': 'All your content will now match this tone consistently.',
  'target_audience': 'Content will now speak directly to your ideal customers.',
  'key_offer': 'Posts will highlight what makes you unique and compelling.',
  'writing_samples': 'Generated content will sound more authentically like you.',
  'voice_rules': 'Content will follow your specific guidelines and constraints.',
};

// Configuration constants
const AI_SUGGESTION_TIMEOUT_MS = 15000; // 15 seconds for AI suggestion calls
const TYPEWRITER_SPEED_MS = 25; // Milliseconds per character for typewriter effect
const TYPEWRITER_SHORT_MESSAGE_THRESHOLD = 50; // Messages shorter than this skip typewriter effect
const AUTO_SCROLL_DELAY_MS = 100; // Delay before auto-scrolling to ensure smooth rendering


/**
 * ScrollManager - Handles scroll position and scroll-to-bottom button
 */
class ScrollManager {
  constructor(containerSelector) {
    this.container = document.querySelector(containerSelector);
    this.scrollButton = null;
    this.isAtBottom = true;
    this.lastScrollTop = 0;
    
    this.init();
  }
  
  init() {
    if (!this.container) return;
    
    // Create scroll-to-bottom button with text
    this.scrollButton = document.createElement('button');
    this.scrollButton.className = 'scroll-to-bottom';
    this.scrollButton.innerHTML = '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 5v14M19 12l-7 7-7-7"/></svg><span>New messages</span>';
    this.scrollButton.setAttribute('aria-label', 'Scroll to bottom to see new messages');
    this.scrollButton.addEventListener('click', () => this.scrollToBottom(true));
    
    // Append to parent element (not the scrollable container itself)
    if (this.container.parentElement) {
      this.container.parentElement.appendChild(this.scrollButton);
    }
    
    // Listen to scroll events
    this.container.addEventListener('scroll', () => this.handleScroll());
  }
  
  handleScroll() {
    const scrollTop = this.container.scrollTop;
    const scrollHeight = this.container.scrollHeight;
    const clientHeight = this.container.clientHeight;
    
    // Check if user is at bottom (within 100px)
    this.isAtBottom = (scrollHeight - scrollTop - clientHeight) < 100;
    
    // Show/hide scroll button
    if (this.isAtBottom) {
      this.scrollButton.classList.remove('visible');
    } else if (scrollTop < this.lastScrollTop || scrollTop > 100) {
      // Show button if scrolled up or past 100px
      this.scrollButton.classList.add('visible');
    }
    
    this.lastScrollTop = scrollTop;
  }
  
  scrollToBottom(smooth = true) {
    if (!this.container) return;
    
    this.container.scrollTo({
      top: this.container.scrollHeight,
      behavior: smooth ? 'smooth' : 'auto'
    });
  }
  
  shouldAutoScroll() {
    return this.isAtBottom;
  }
}


/**
 * TypewriterEffect - Enhanced typewriter with skip button and chunk rendering
 */
class TypewriterEffect {
  constructor(element, text, options = {}) {
    this.element = element;
    this.text = text;
    this.speed = options.speed || 25;
    this.skipCallback = options.onSkip || null;
    this.completeCallback = options.onComplete || null;
    this.isSkipped = false;
    this.skipButton = null;
    this.timeoutId = null;
  }
  
  async start() {
    // Check for reduced motion preference
    const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    if (prefersReducedMotion) {
      this.skip();
      return;
    }
    
    // Add skip button
    this.addSkipButton();
    
    // Chunk-based typing (3 chars per tick for performance)
    const chunkSize = 3;
    let currentIndex = 0;
    
    const typeChunk = () => {
      if (this.isSkipped) return;
      
      const nextChunk = this.text.slice(currentIndex, currentIndex + chunkSize);
      if (nextChunk) {
        this.element.textContent += nextChunk;
        currentIndex += chunkSize;
        
        // Continue typing
        this.timeoutId = setTimeout(typeChunk, this.speed);
      } else {
        // Typing complete
        this.complete();
      }
    };
    
    typeChunk();
  }
  
  addSkipButton() {
    this.skipButton = document.createElement('button');
    this.skipButton.className = 'typewriter-skip';
    this.skipButton.textContent = 'Skip';
    this.skipButton.setAttribute('aria-label', 'Skip typewriter animation');
    this.skipButton.addEventListener('click', () => this.skip());
    
    // Add to message element (assuming element is inside a message container)
    const messageContainer = this.element.closest('.promptbox-message') || this.element.parentElement;
    if (messageContainer) {
      messageContainer.style.position = 'relative';
      messageContainer.appendChild(this.skipButton);
    }
  }
  
  skip() {
    this.isSkipped = true;
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    this.element.textContent = this.text;
    this.complete();
  }
  
  complete() {
    if (this.skipButton && this.skipButton.parentElement) {
      this.skipButton.remove();
    }
    if (this.timeoutId) {
      clearTimeout(this.timeoutId);
      this.timeoutId = null;
    }
    if (this.completeCallback) {
      this.completeCallback();
    }
  }
}


/**
 * hapticFeedback - Trigger haptic feedback on supported devices
 */
function hapticFeedback(type = 'light') {
  // Check if Vibration API is available
  if (!navigator.vibrate) return;
  
  const patterns = {
    light: 10,
    medium: 20,
    success: [10, 50, 10],
    error: [20, 100, 20],
    warning: [10, 50, 10, 50, 10]
  };
  
  const pattern = patterns[type] || patterns.light;
  navigator.vibrate(pattern);
}


/**
 * showToast - Display toast notification
 * Uses textContent instead of innerHTML to prevent XSS
 * @param {string} message - Message to display (must be a string)
 * @param {string} type - Type of toast (info, success, error, warning)
 */
function showToast(message, type = 'info') {
  // Validate that message is a string
  if (typeof message !== 'string') {
    console.error('showToast: message must be a string');
    return;
  }
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  toast.textContent = message; // XSS safe - use textContent instead of innerHTML
  
  document.body.appendChild(toast);
  
  // Trigger haptic feedback
  hapticFeedback(type === 'error' ? 'error' : type === 'success' ? 'success' : 'light');
  
  // Auto-dismiss after 3 seconds
  setTimeout(() => {
    toast.style.animation = 'toastOut 0.3s ease';
    setTimeout(() => toast.remove(), 300);
  }, 3000);
}


class PromptBox {
  constructor(containerId, options = {}) {
    this.container = document.getElementById(containerId);
    if (!this.container) {
      console.error(`PromptBox: Container #${containerId} not found`);
      return;
    }

    // Configuration
    this.context = options.context || 'dashboard'; // 'dashboard' or 'onboarding'
    this.placeholder = options.placeholder || this.getDefaultPlaceholder();
    this.onSend = options.onSend || null;
    this.embedded = options.embedded || false; // NEW: When true, only render messages area
    this.typewriterSpeed = options.typewriterSpeed || TYPEWRITER_SPEED_MS; // Allow override
    this.typewriterThreshold = options.typewriterThreshold || TYPEWRITER_SHORT_MESSAGE_THRESHOLD; // Allow override
    
    // State
    this.conversationHistory = [];
    this.pendingTask = null;
    this.isLoading = false;
    this.suggestionIndex = 0;
    this.suggestionTimer = null;
    this.lastAction = null; // Track last action for contextual suggestions
    this.selectedAutocompleteIndex = -1; // Track selected autocomplete item
    this.lastGeneratedContent = null; // Track last generated content for copy
    this.collectionState = null; // Track multi-step collection flows (e.g., writing samples)
    this.pendingImport = null; // Track pending import data for confirmation
    this.pendingImportUrl = null; // Track URL of pending import
    this.editMode = null; // Track edit mode ('import', etc.)
    this.editFields = null; // Track fields being edited
    this.editingField = null; // Track currently editing field
    this.pendingProfileSuggestions = null; // Track pending profile suggestions for selection
    this.hasUsedSlashCommand = localStorage.getItem('eazeily_used_slash') === 'true'; // Track if user has used slash commands
    this.scrollManager = null; // Track scroll manager
    this.thinkingIndicator = null; // Track thinking indicator element

    // Get suggestions based on context
    this.suggestions = this.getSuggestions();

    // Initialize component
    this.render();
    this.attachEventListeners();
    this.startSuggestionRotation();
    
    // Initialize scroll manager after render (only for non-embedded mode)
    if (!this.embedded) {
      this.scrollManager = new ScrollManager('.promptbox-messages');
    }
  }

  getDefaultPlaceholder() {
    return this.context === 'onboarding'
      ? "Drop your website URL and I'll help build your brand profile"
      : "What do you want to create today?";
  }

  getSuggestions(contextOverride, lastAction) {
    // Use provided context or instance context
    const ctx = contextOverride || this.context;
    const action = lastAction || this.lastAction;
    
    // Onboarding context
    if (ctx === 'onboarding') {
      return [
        "Drop your website URL",
        "Describe your brand in a few sentences",
        "Tell me about your ideal customer",
        "What makes your business unique?"
      ];
    }
    
    // Profile view/update context
    if (action === 'profile_view' || action === 'profile_updated') {
      return [
        '/voice - Update brand voice',
        '/audience - Define target audience',
        '/samples - Add writing samples',
        '/import - Import from URL',
      ];
    }
    
    // Post-generation context - show refinement suggestions
    if (action === 'generated') {
      return [
        "Regenerate",
        "Make it shorter",
        "Make it more casual",
        "Try a different angle"
      ];
    }
    
    // Default dashboard suggestions - rotate through content types
    return [
      "/post about your latest product",
      "/caption for a behind-the-scenes photo",
      "/email announcing your summer sale",
      "/script for a 30s Instagram reel"
    ];
  }

  render() {
    const showHint = !this.hasUsedSlashCommand;
    
    // In embedded mode, only render the messages container
    if (this.embedded) {
      const html = `
        <div class="promptbox-container promptbox-embedded">
          <!-- Conversation History (embedded mode - messages only) -->
          <div class="promptbox-messages" id="${this.container.id}-conversation">
            <!-- Messages will be appended here -->
          </div>
        </div>
      `;
      this.container.innerHTML = html;
      return; // Skip input area and suggestions rendering
    }
    
    const html = `
      <div class="promptbox-container">
        <!-- Conversation History -->
        <div class="promptbox-messages" id="${this.container.id}-conversation">
          <!-- Messages will be appended here -->
        </div>

        <!-- Input Area -->
        <div class="promptbox-input-area">
          <!-- Autocomplete Dropdown (hidden by default) -->
          <div class="promptbox-autocomplete hidden" id="${this.container.id}-autocomplete" role="listbox"></div>
          
          <!-- Rotating Suggestions -->
          <div class="promptbox-suggestions" id="${this.container.id}-suggestions" role="region" aria-label="Suggestions">
            <!-- Suggestions will be rendered here -->
          </div>

          ${showHint ? `
          <!-- Slash Command Hint -->
          <div id="${this.container.id}-slash-hint" class="promptbox-slash-hint">
            💡 Type <kbd>/</kbd> to see commands
          </div>
          ` : ''}

          <!-- Input Field -->
          <div class="promptbox-input-wrapper">
            <textarea
              id="${this.container.id}-textarea"
              class="promptbox-textarea"
              placeholder="${this.placeholder}"
              rows="1"
              aria-label="Message input"
              aria-describedby="${this.container.id}-suggestions"
            ></textarea>
            <button
              id="${this.container.id}-send"
              class="promptbox-send-btn"
              aria-label="Send message"
              disabled
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path d="M22 2L11 13M22 2L15 22L11 13L2 9L22 2Z" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </button>
          </div>
        </div>

        <!-- Loading Indicator -->
        <div class="promptbox-loading hidden" id="${this.container.id}-loading" role="status" aria-live="polite">
          <div class="promptbox-typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="promptbox-loading-text">Thinking...</span>
        </div>
      </div>
    `;

    this.container.innerHTML = html;
    this.renderSuggestions();
  }

  renderSuggestions() {
    // Skip suggestions in embedded mode (page handles input)
    if (this.embedded) {
      return;
    }
    
    const suggestionsContainer = document.getElementById(`${this.container.id}-suggestions`);
    if (!suggestionsContainer) return;

    const html = this.suggestions.map((suggestion, index) => `
      <button
        class="promptbox-suggestion ${index === this.suggestionIndex ? 'active' : ''}"
        data-suggestion="${this.escapeHtml(suggestion)}"
        aria-label="${this.escapeHtml(suggestion)}"
      >
        ${this.escapeHtml(suggestion)}
      </button>
    `).join('');

    suggestionsContainer.innerHTML = html;
  }

  attachEventListeners() {
    // Skip event listeners in embedded mode (page handles input)
    if (this.embedded) {
      return;
    }
    
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    const sendBtn = document.getElementById(`${this.container.id}-send`);
    const suggestionsContainer = document.getElementById(`${this.container.id}-suggestions`);

    // Auto-resize textarea and handle slash commands
    textarea.addEventListener('input', (e) => {
      this.autoResizeTextarea(textarea);
      this.updateSendButton(textarea, sendBtn);
      this.handleSlashCommand(e.target.value);
    });

    // Send on Enter (Shift+Enter for new line)
    textarea.addEventListener('keydown', (e) => {
      // Handle autocomplete navigation
      const autocomplete = document.getElementById(`${this.container.id}-autocomplete`);
      if (!autocomplete.classList.contains('hidden')) {
        if (e.key === 'ArrowDown') {
          e.preventDefault();
          this.navigateAutocomplete('down');
          return;
        } else if (e.key === 'ArrowUp') {
          e.preventDefault();
          this.navigateAutocomplete('up');
          return;
        } else if (e.key === 'Enter' || e.key === 'Tab') {
          if (this.selectedAutocompleteIndex >= 0) {
            e.preventDefault();
            this.selectAutocompleteItem(this.selectedAutocompleteIndex);
            return;
          }
        } else if (e.key === 'Escape') {
          e.preventDefault();
          this.hideAutocomplete();
          return;
        }
      }
      
      // Normal enter handling
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        if (textarea.value.trim()) {
          this.handleSend();
        }
      }
    });

    // Send button click
    sendBtn.addEventListener('click', () => {
      if (!sendBtn.disabled) {
        this.handleSend();
      }
    });

    // Suggestion clicks
    suggestionsContainer.addEventListener('click', (e) => {
      const suggestionBtn = e.target.closest('.promptbox-suggestion');
      if (suggestionBtn) {
        const suggestion = suggestionBtn.dataset.suggestion;
        this.fillSuggestion(suggestion);
      }
    });
  }

  autoResizeTextarea(textarea) {
    if (!textarea) return;  // Add null check
    textarea.style.height = 'auto';
    const minHeight = 44; // Min height for touch targets
    const maxHeight = 120; // Max 4 lines approx (30px per line)
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = `${newHeight}px`;
  }

  updateSendButton(textarea, sendBtn) {
    if (!textarea || !sendBtn) return;  // Add null check
    const hasContent = textarea.value.trim().length > 0;
    sendBtn.disabled = !hasContent;
  }

  handleSlashCommand(value) {
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    
    // Check if value starts with /
    if (value.startsWith('/')) {
      // Hide slash hint on first use
      if (!this.hasUsedSlashCommand) {
        this.hasUsedSlashCommand = true;
        localStorage.setItem('eazeily_used_slash', 'true');
        
        const hint = document.getElementById(`${this.container.id}-slash-hint`);
        if (hint) {
          hint.classList.add('fade-out');
          setTimeout(() => hint.classList.add('hidden'), 300);
        }
      }
      
      const query = value.slice(1).toLowerCase();
      const matches = SLASH_COMMANDS.filter(cmd => 
        cmd.command.slice(1).toLowerCase().startsWith(query)
      );
      
      if (matches.length > 0) {
        this.showAutocomplete(matches);
        textarea.classList.add('has-slash-command');
      } else {
        this.hideAutocomplete();
        textarea.classList.remove('has-slash-command');
      }
    } else {
      this.hideAutocomplete();
      textarea.classList.remove('has-slash-command');
    }
  }

  showAutocomplete(commands) {
    const autocomplete = document.getElementById(`${this.container.id}-autocomplete`);
    if (!autocomplete) return;

    const html = commands.map((cmd, index) => `
      <div 
        class="promptbox-autocomplete-item ${index === this.selectedAutocompleteIndex ? 'selected' : ''}" 
        data-index="${index}"
        data-command="${this.escapeHtml(cmd.command)}"
        role="option"
        aria-selected="${index === this.selectedAutocompleteIndex}"
      >
        <span class="icon">${cmd.icon}</span>
        <div class="autocomplete-text">
          <span class="command">${this.escapeHtml(cmd.command)}</span>
          <span class="description">${this.escapeHtml(cmd.description)}</span>
        </div>
      </div>
    `).join('');

    autocomplete.innerHTML = html;
    autocomplete.classList.remove('hidden');
    this.selectedAutocompleteIndex = 0; // Auto-select first item

    // Add click handlers to autocomplete items
    autocomplete.querySelectorAll('.promptbox-autocomplete-item').forEach((item, index) => {
      item.addEventListener('click', () => {
        this.selectAutocompleteItem(index);
      });
    });
  }

  hideAutocomplete() {
    const autocomplete = document.getElementById(`${this.container.id}-autocomplete`);
    if (autocomplete) {
      autocomplete.classList.add('hidden');
      autocomplete.innerHTML = '';
    }
    this.selectedAutocompleteIndex = -1;
  }

  navigateAutocomplete(direction) {
    const autocomplete = document.getElementById(`${this.container.id}-autocomplete`);
    if (!autocomplete || autocomplete.classList.contains('hidden')) return;

    const items = autocomplete.querySelectorAll('.promptbox-autocomplete-item');
    if (items.length === 0) return;

    // Remove current selection
    if (this.selectedAutocompleteIndex >= 0 && this.selectedAutocompleteIndex < items.length) {
      items[this.selectedAutocompleteIndex].classList.remove('selected');
      items[this.selectedAutocompleteIndex].setAttribute('aria-selected', 'false');
    }

    // Update index
    if (direction === 'down') {
      this.selectedAutocompleteIndex = (this.selectedAutocompleteIndex + 1) % items.length;
    } else if (direction === 'up') {
      this.selectedAutocompleteIndex = this.selectedAutocompleteIndex <= 0 
        ? items.length - 1 
        : this.selectedAutocompleteIndex - 1;
    }

    // Add new selection
    items[this.selectedAutocompleteIndex].classList.add('selected');
    items[this.selectedAutocompleteIndex].setAttribute('aria-selected', 'true');
    
    // Scroll into view
    items[this.selectedAutocompleteIndex].scrollIntoView({ block: 'nearest', behavior: 'smooth' });
  }

  selectAutocompleteItem(index) {
    const autocomplete = document.getElementById(`${this.container.id}-autocomplete`);
    if (!autocomplete) return;

    const items = autocomplete.querySelectorAll('.promptbox-autocomplete-item');
    if (index < 0 || index >= items.length) return;

    const command = items[index].dataset.command;
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    const sendBtn = document.getElementById(`${this.container.id}-send`);

    // Fill input with command + space
    textarea.value = command + ' ';
    this.autoResizeTextarea(textarea);
    this.updateSendButton(textarea, sendBtn);
    this.hideAutocomplete();
    textarea.focus();
  }

  fillSuggestion(suggestion) {
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    const sendBtn = document.getElementById(`${this.container.id}-send`);
    
    textarea.value = suggestion;
    this.autoResizeTextarea(textarea);
    this.updateSendButton(textarea, sendBtn);
    textarea.focus();

    // Stop rotation temporarily
    this.stopSuggestionRotation();
    setTimeout(() => this.startSuggestionRotation(), 10000); // Resume after 10s
  }

  startSuggestionRotation() {
    this.suggestionTimer = setInterval(() => {
      this.suggestionIndex = (this.suggestionIndex + 1) % this.suggestions.length;
      this.renderSuggestions();
    }, 5000); // Rotate every 5 seconds
  }

  stopSuggestionRotation() {
    if (this.suggestionTimer) {
      clearInterval(this.suggestionTimer);
      this.suggestionTimer = null;
    }
  }

  async handleSend() {
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    const message = textarea.value.trim();
    
    if (!message || this.isLoading) return;

    // Add user message to conversation
    this.addMessage('user', message);

    // Clear input
    textarea.value = '';
    this.autoResizeTextarea(textarea);
    const sendBtn = document.getElementById(`${this.container.id}-send`);
    this.updateSendButton(textarea, sendBtn);

    // Show loading
    this.setLoading(true);

    try {
      // Handle edit mode for import flow
      if (this.editMode === 'import' && this.editFields && this.pendingImport) {
        await handleImportEditInput(this, message);
        this.setLoading(false);
        return;
      }
      
      // Check if this is a profile command that should be handled client-side
      const profileCommands = ['/profile', '/voice', '/audience', '/offer', '/samples', '/rules', '/import', '/import-confirm', '/import-edit', '/import-cancel', '/help'];
      const isProfileCommand = profileCommands.some(cmd => message.startsWith(cmd));
      
      if (isProfileCommand) {
        // Extract command and args
        const parts = message.split(/\s+/);
        const command = parts[0];
        const args = parts.slice(1).join(' ');
        
        // Check if this is a profile field AI command
        if (PROFILE_FIELD_MAP[command]) {
          await this.handleProfileFieldCommand(command);
          this.setLoading(false);
          return;
        }
        
        // Handle profile command
        await handleProfileCommand(this, command, args);
        
        // Update suggestions to show profile commands after handling profile action
        this.lastAction = 'profile_view';
        this.suggestions = this.getSuggestions(null, 'profile_view');
        this.renderSuggestions();
        
        this.setLoading(false);
        return;
      }
      
      // Call custom handler if provided, otherwise use API
      if (this.onSend && typeof this.onSend === 'function') {
        await this.onSend(message, this);
      } else {
        await this.sendToAPI(message);
      }
    } catch (error) {
      console.error('PromptBox error:', error);
      await this.addMessage('assistant', 'Sorry, something went wrong. Please try again.', true);
    } finally {
      this.setLoading(false);
    }
  }

  /**
   * Send a message from external source (e.g., page input when in embedded mode)
   * @param {string} message - Message text to send
   */
  async sendMessage(message) {
    if (!message || this.isLoading) return;

    // Add user message to conversation
    this.addMessage('user', message);

    // Show loading
    this.setLoading(true);

    try {
      // Check if we're in onboarding mode
      if (window.onboardingState && window.onboardingState !== 'complete') {
        const handled = await this.handleOnboardingInput(message);
        if (handled) {
          this.setLoading(false);
          return;
        }
      }
      
      // Check if this is a profile command that should be handled client-side
      const profileCommands = ['/profile', '/voice', '/audience', '/offer', '/samples', '/rules', '/import', '/help'];
      const isProfileCommand = profileCommands.some(cmd => message.startsWith(cmd));
      
      if (isProfileCommand) {
        // Extract command and args
        const parts = message.split(/\s+/);
        const command = parts[0];
        const args = parts.slice(1).join(' ');
        
        // Handle profile command
        await handleProfileCommand(this, command, args);
        
        // Update suggestions to show profile commands after handling profile action
        this.lastAction = 'profile_view';
        this.suggestions = this.getSuggestions(null, 'profile_view');
        this.renderSuggestions();
        
        this.setLoading(false);
        return;
      }
      
      // Call custom handler if provided, otherwise use API
      if (this.onSend && typeof this.onSend === 'function') {
        await this.onSend(message, this);
      } else {
        await this.sendToAPI(message);
      }
    } catch (error) {
      console.error('PromptBox error:', error);
      await this.addMessage('assistant', 'Sorry, something went wrong. Please try again.', true);
    } finally {
      this.setLoading(false);
    }
  }

  async sendToAPI(message) {
    const payload = {
      message: message,
      history: this.conversationHistory,
      pending_task: this.pendingTask,
      context: this.context
    };

    const response = await fetch('/api/chat', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    const data = await response.json();
    
    // Handle profile_prompt_with_skip action with buttons
    if (data.action === 'profile_prompt_with_skip' && data.actions) {
      // Convert server actions to button format
      const buttons = data.actions.map(action => ({
        label: action.text,
        action: 'command',  // All buttons execute as commands
        value: action.action === 'generate_anyway' ? 'generate_anyway' : 'complete_profile',
        style: action.style
      }));
      
      // Add assistant message with buttons
      await this.addMessage('assistant', data.response, false, false, buttons);
      
      // Store pending task
      if (data.pending_task) {
        this.pendingTask = data.pending_task;
      }
      
      return; // Early return after handling skip prompt
    }
    
    // Add assistant message
    const isGenerated = data.action === 'generated' || (data.content && data.content.length > 100);
    await this.addMessage('assistant', data.response, false, isGenerated);
    
    // Store generated content for copy
    if (isGenerated && data.content) {
      this.lastGeneratedContent = data.content;
      this.lastAction = 'generated';
      // Update suggestions to show refinement options
      this.suggestions = this.getSuggestions(null, 'generated');
      this.renderSuggestions();
    }
    
    // Handle profile actions
    if (data.action === 'profile_view' || data.action === 'profile_updated') {
      this.lastAction = data.action;
      // Update suggestions for profile context
      this.suggestions = this.getSuggestions(null, data.action);
      this.renderSuggestions();
    }
    
    // Update pending task if provided
    if (data.pending_task) {
      this.pendingTask = data.pending_task;
    } else {
      this.pendingTask = null;
    }

    // Handle different actions
    if (data.action === 'onboarding_complete' || data.redirect) {
      // Profile complete - redirect after a short delay
      setTimeout(() => {
        window.location.href = data.redirect || '/dashboard';
      }, 1500);
    } else if (data.action === 'error') {
      // Error occurred - already displayed in response
    }
  }

  async addMessage(role, content, isError = false, isGenerated = false, buttons = null) {
    const timestamp = Date.now();
    
    // Add to history
    this.conversationHistory.push({
      role: role,
      message: content,
      timestamp: timestamp
    });

    // Render message
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `promptbox-message promptbox-message-${role}`;
    if (isError) messageDiv.classList.add('promptbox-message-error');

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'promptbox-bubble';

    // For assistant messages, apply typewriter effect
    if (role === 'assistant') {
      // Show thinking indicator
      bubbleDiv.innerHTML = '<em class="thinking">Thinking... 🤔</em>';
      messageDiv.appendChild(bubbleDiv);
      conversation.appendChild(messageDiv);
      await new Promise(resolve => setTimeout(resolve, 300));
      
      // Clear and apply typewriter effect
      bubbleDiv.innerHTML = '';
      bubbleDiv.classList.add('typing');
      await this.typewriterEffect(bubbleDiv, content, 25);
      bubbleDiv.classList.remove('typing');
      
      // Add copy button for generated content
      if (isGenerated) {
        const copyBtn = document.createElement('button');
        copyBtn.className = 'promptbox-copy-btn';
        copyBtn.setAttribute('aria-label', 'Copy content');
        copyBtn.innerHTML = `
          <span class="copy-icon">📋</span>
          <span class="copy-text">Copy</span>
        `;
        copyBtn.onclick = () => this.copyContent(content, copyBtn);
        messageDiv.appendChild(copyBtn);
      }
      
      // Add buttons if provided
      if (buttons && buttons.length > 0) {
        this.renderMessageButtons(buttons, messageDiv);
      }
    } else {
      // User messages - no typewriter effect
      bubbleDiv.textContent = content;
      messageDiv.appendChild(bubbleDiv);
      
      // Add buttons if provided
      if (buttons && buttons.length > 0) {
        this.renderMessageButtons(buttons, messageDiv);
      }
      
      conversation.appendChild(messageDiv);
    }

    // Auto-scroll to latest message if user is near bottom
    this.conditionalAutoScroll();
  }
  
  renderMessageButtons(buttons, messageEl) {
    if (!buttons || !buttons.length) return;
    
    const btnContainer = document.createElement('div');
    btnContainer.className = 'promptbox-button-container flex flex-wrap gap-2 mt-3';
    
    buttons.forEach(btn => {
      const button = document.createElement('button');
      
      // Apply different styles based on button style attribute
      if (btn.style === 'primary') {
        button.className = 'promptbox-action-btn px-4 py-2 text-sm font-medium bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition-colors shadow-sm';
      } else if (btn.style === 'secondary') {
        button.className = 'promptbox-action-btn px-4 py-2 text-sm font-medium bg-white text-indigo-700 rounded-lg border border-indigo-200 hover:bg-indigo-50 transition-colors';
      } else {
        button.className = 'promptbox-action-btn px-3 py-1.5 text-sm bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-200 hover:bg-indigo-100 transition-colors';
      }
      
      button.textContent = btn.label;
      
      // Store button data for click handler
      button.dataset.action = btn.action;
      if (btn.field) button.dataset.field = btn.field;
      if (btn.value) button.dataset.value = btn.value;
      
      button.onclick = () => {
        if (btn.action === 'select-profile-suggestion' && btn.field && btn.value) {
          this.selectProfileSuggestion(btn.field, btn.value);
          return;
        }
        
        // Use correct textarea and send button IDs based on embedded mode
        const textareaId = this.embedded ? 'chat-input' : `${this.container.id}-textarea`;
        const sendBtnId = this.embedded ? 'send-btn' : `${this.container.id}-send`;
        
        const textarea = document.getElementById(textareaId);
        const sendBtn = document.getElementById(sendBtnId);
        
        if (btn.action === 'prompt') {
          // Pre-fill the input with the value
          if (textarea) {
            textarea.value = btn.value;
            
            // Use appropriate resize function based on mode
            if (this.embedded && typeof autoResizeTextarea === 'function') {
              autoResizeTextarea(textarea);
            } else {
              this.autoResizeTextarea(textarea);
            }
            
            // Enable send button
            if (sendBtn) {
              sendBtn.disabled = false;
            }
            
            textarea.focus();
          }
        } else if (btn.action === 'focus') {
          if (textarea) {
            textarea.focus();
          }
        } else if (btn.action === 'command') {
          // Execute command directly using sendMessage
          if (textarea) {
            textarea.value = btn.value;
            this.sendMessage(btn.value);
          }
        }
      };
      
      btnContainer.appendChild(button);
    });
    
    messageEl.appendChild(btnContainer);
  }

  renderMarkdown(text) {
    // Simple markdown rendering (bold, italic, code, lists, headers, hr)
    let html = this.escapeHtml(text);

    // Headers: ## text, ### text, #### text (must be processed before bold/italic)
    html = html.replace(/^#### (.+)$/gm, '<h4>$1</h4>');
    html = html.replace(/^### (.+)$/gm, '<h3>$1</h3>');
    html = html.replace(/^## (.+)$/gm, '<h2>$1</h2>');

    // Horizontal rules: ---
    html = html.replace(/^---$/gm, '<hr>');

    // Bold: **text** or __text__
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
    html = html.replace(/__([^_]+)__/g, '<strong>$1</strong>');

    // Italic: *text* or _text_
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
    html = html.replace(/_([^_]+)_/g, '<em>$1</em>');

    // Code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // Line breaks
    html = html.replace(/\n/g, '<br>');

    // Lists (simple bullets)
    html = html.replace(/^- (.+)$/gm, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/s, '<ul>$1</ul>');

    return html;
  }

  scrollToBottom() {
    // In embedded mode, scroll the parent container (chat-container)
    // In standalone mode, scroll the conversation div itself
    let scrollContainer;
    
    if (this.embedded) {
      // Find the actual scrollable parent container
      // Try ID first (faster, more specific)
      scrollContainer = document.getElementById('chat-container');
      if (!scrollContainer) {
        // Fallback: use class selector to find parent with same class name
        // This handles edge cases where ID might not be set
        const conversation = document.getElementById(`${this.container.id}-conversation`);
        if (conversation) {
          scrollContainer = conversation.closest('.chat-container');
        }
      }
    } else {
      // Standalone mode: scroll the conversation div
      scrollContainer = document.getElementById(`${this.container.id}-conversation`);
    }
    
    if (scrollContainer) {
      // Smooth scroll to bottom
      scrollContainer.scrollTo({
        top: scrollContainer.scrollHeight,
        behavior: 'smooth'
      });
    }
  }
  
  /**
   * Conditionally auto-scroll to bottom if user is near the end
   * Prevents unwanted scrolling when user is reading older messages
   */
  conditionalAutoScroll() {
    if (this.scrollManager && this.scrollManager.shouldAutoScroll()) {
      // Small delay to let content render
      setTimeout(() => {
        this.scrollToBottom();
      }, AUTO_SCROLL_DELAY_MS);
    }
  }
  
  /**
   * Show skeleton loader thinking indicator
   */
  showThinkingIndicator() {
    // Check if thinking indicator already exists
    if (this.thinkingIndicator && this.thinkingIndicator.parentElement) {
      return; // Already showing
    }
    
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    if (!conversation) return;
    
    // Create thinking indicator with skeleton loader (using DOM methods for safety)
    const thinkingDiv = document.createElement('div');
    thinkingDiv.className = 'promptbox-message thinking';
    
    const loaderDiv = document.createElement('div');
    loaderDiv.className = 'skeleton-loader';
    
    // Add three skeleton lines
    for (let i = 0; i < 3; i++) {
      const line = document.createElement('div');
      line.className = 'skeleton-line';
      loaderDiv.appendChild(line);
    }
    
    thinkingDiv.appendChild(loaderDiv);
    conversation.appendChild(thinkingDiv);
    this.thinkingIndicator = thinkingDiv;
    
    // Auto-scroll to latest message if user is near bottom
    this.conditionalAutoScroll();
  }
  
  /**
   * Hide skeleton loader thinking indicator
   */
  hideThinkingIndicator() {
    if (this.thinkingIndicator && this.thinkingIndicator.parentElement) {
      this.thinkingIndicator.remove();
      this.thinkingIndicator = null;
    }
  }

  /**
   * Typewriter effect for AI responses
   * @param {HTMLElement} element - The element to type into
   * @param {string} text - The text to type
   * @param {number} speed - Speed in milliseconds per character (default: from config)
   * @returns {Promise} - Resolves when typing is complete
   */
  async typewriterEffect(element, text, speed = null) {
    // Use instance speed if not provided
    speed = speed || this.typewriterSpeed;
    
    // Skip typewriter for short messages
    if (text.length < this.typewriterThreshold) {
      element.innerHTML = this.renderMarkdown(text);
      return Promise.resolve();
    }
    
    element.innerHTML = '';
    let currentIndex = 0;
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    
    return new Promise((resolve) => {
      const typeInterval = setInterval(() => {
        if (currentIndex < text.length) {
          const partialText = text.substring(0, currentIndex + 1);
          const fixedPartial = this._fixPartialMarkdown(partialText);
          element.innerHTML = this.renderMarkdown(fixedPartial);
          
          // Auto-scroll every 5 characters
          if (currentIndex % 5 === 0) {
            this._autoScrollToBottom(conversation, element);
          }
          currentIndex++;
        } else {
          clearInterval(typeInterval);
          element.innerHTML = this.renderMarkdown(text);
          conversation.scrollTop = conversation.scrollHeight;
          resolve();
        }
      }, speed);
    });
  }

  /**
   * Fix partial markdown to avoid broken syntax during typing
   * @param {string} text - Partial text that may have incomplete markdown
   * @returns {string} - Fixed text with closed markdown tags
   */
  _fixPartialMarkdown(text) {
    let fixed = text;
    
    // Handle bold (**text**)
    const boldCount = (text.match(/\*\*/g) || []).length;
    if (boldCount % 2 !== 0) fixed += '**';
    
    // Handle code (`code`)
    const codeCount = (text.match(/`/g) || []).length;
    if (codeCount % 2 !== 0) fixed += '`';
    
    // Handle italic (*text* or _text_) - but only if not part of bold
    // Count single asterisks that aren't part of **
    const singleAsterisks = (text.match(/(?<!\*)\*(?!\*)/g) || []).length;
    if (singleAsterisks % 2 !== 0) fixed += '*';
    
    const underscoreCount = (text.match(/_/g) || []).length;
    if (underscoreCount % 2 !== 0) fixed += '_';
    
    return fixed;
  }

  /**
   * Auto-scroll to keep typing visible
   * @param {HTMLElement} container - The scrollable container
   * @param {HTMLElement} element - The element being typed into
   */
  _autoScrollToBottom(container, element) {
    const messageBottom = element.getBoundingClientRect().bottom;
    const containerBottom = container.getBoundingClientRect().bottom;
    if (messageBottom > containerBottom - 50) {
      container.scrollTop = container.scrollHeight;
    }
  }

  copyContent(content, button) {
    // Use Clipboard API
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(content).then(() => {
        this.showCopyFeedback(button);
      }).catch(err => {
        console.error('Failed to copy:', err);
        // Fallback for older browsers
        this.fallbackCopy(content, button);
      });
    } else {
      this.fallbackCopy(content, button);
    }
  }

  fallbackCopy(content, button) {
    // Fallback method for browsers without Clipboard API
    const textarea = document.createElement('textarea');
    textarea.value = content;
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    document.body.appendChild(textarea);
    textarea.select();
    try {
      document.execCommand('copy');
      this.showCopyFeedback(button);
    } catch (err) {
      console.error('Fallback copy failed:', err);
    }
    document.body.removeChild(textarea);
  }

  showCopyFeedback(button) {
    const originalHTML = button.innerHTML;
    button.innerHTML = `
      <span class="copy-icon">✓</span>
      <span class="copy-text">Copied!</span>
    `;
    button.classList.add('copied');
    
    setTimeout(() => {
      button.innerHTML = originalHTML;
      button.classList.remove('copied');
    }, 2000);
  }

  setLoading(isLoading) {
    this.isLoading = isLoading;
    
    // In embedded mode, use dashboard's loading indicator
    if (this.embedded) {
      const dashboardLoadingEl = document.getElementById('chat-loading');
      if (dashboardLoadingEl) {
        if (isLoading) {
          dashboardLoadingEl.classList.remove('hidden');
        } else {
          dashboardLoadingEl.classList.add('hidden');
        }
      }
      
      // Optionally emit event for page to handle
      if (typeof window.handleLoadingStateChange === 'function') {
        window.handleLoadingStateChange(isLoading);
      }
      return;
    }
    
    // Non-embedded mode: manage our own loading state
    const loadingEl = document.getElementById(`${this.container.id}-loading`);
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    const sendBtn = document.getElementById(`${this.container.id}-send`);

    // Additional safety: check if elements exist before accessing
    if (isLoading) {
      if (loadingEl) loadingEl.classList.remove('hidden');
      if (textarea) textarea.disabled = true;
      if (sendBtn) sendBtn.disabled = true;
    } else {
      if (loadingEl) loadingEl.classList.add('hidden');
      if (textarea) textarea.disabled = false;
      if (textarea && sendBtn) this.updateSendButton(textarea, sendBtn);
    }
  }

  /**
   * Update an existing message by its ID or the last message
   * @param {string|number} messageId - Message ID or index to update (or 'last' for last message)
   * @param {string} newContent - New content for the message
   */
  updateMessage(messageId, newContent) {
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    if (!conversation) return;
    
    const messages = conversation.querySelectorAll('.promptbox-message-assistant');
    if (!messages.length) return;
    
    // Get the message to update (default to last message)
    let targetMessage = messages[messages.length - 1];
    
    // Update the bubble content
    const bubble = targetMessage.querySelector('.promptbox-bubble');
    if (bubble) {
      // Remove loading class if present
      bubble.classList.remove('message-loading');
      bubble.innerHTML = this.renderMarkdown(newContent);
    }
    
    // Update conversation history
    if (this.conversationHistory.length > 0) {
      this.conversationHistory[this.conversationHistory.length - 1].message = newContent;
    }
  }

  clearHistory() {
    this.conversationHistory = [];
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    if (conversation) {
      conversation.innerHTML = '';
    }
  }

  getPendingTask() {
    return this.pendingTask;
  }

  escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  }
  
  /**
   * Initialize PromptBox with profile context
   * Checks user's profile completeness and shows appropriate welcome message
   */
  async initWithProfileContext() {
    try {
      const response = await fetch('/api/profile', { credentials: 'include' });
      const data = await response.json();
      
      if (!data.ok || !data.profile) {
        // No profile - show onboarding welcome
        this.showOnboardingWelcome();
        return;
      }
      
      // Use server-provided completeness data
      const completeness = data.completeness || { percent: 0, missing_fields: [], is_complete: false };
      const percent = completeness.percent;
      const isComplete = completeness.is_complete;
      const missing = completeness.missing_fields;
      
      if (percent < 30) {
        // Very incomplete - guide through setup
        this.showOnboardingWelcome();
      } else if (missing.length > 0) {
        // Partially complete - nudge to finish
        this.showCompletionNudge(missing, percent);
      } else {
        // Complete - ready to create
        this.showReadyState(data.profile);
      }
    } catch (error) {
      console.error('Failed to check profile:', error);
      // Fail gracefully - show default state (no message)
    }
  }
  
  /**
   * Format field name for display
   */
  formatFieldName(key) {
    const labels = {
      'business_name': 'Business Name',
      'industry': 'Industry',
      'brand_voice': 'Brand Voice',
      'target_audience': 'Target Audience',
      'key_offer': 'Key Offer',
      'writing_samples': 'Writing Samples',
      'brand_keywords': 'Brand Keywords',
      'goals': 'Goals',
    };
    return labels[key] || key.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
  }
  
  /**
   * Show onboarding welcome for new/incomplete users
   */
  showOnboardingWelcome() {
    const welcomeMessage = `# Welcome to Eazeily! 👋

I'm your AI content assistant. I can help you create:
- 📝 Social media posts
- ✉️ Emails and newsletters
- 📷 Image captions
- 📄 Proposals and more

**Let's get started!** First, tell me a bit about your business:

**What's your business name?**`;
    
    this.addMessage('assistant', welcomeMessage, false, false, null);
  }
  
  /**
   * Show completion nudge for partially complete profiles
   */
  showCompletionNudge(missing, percent) {
    // Handle both formats: array of strings (from server) or array of objects
    const normalizedMissing = missing.map(item => {
        if (typeof item === 'string') {
            // Server format: array of strings like ["Brand Keywords", "Goals"]
            return {
                name: item,
                key: item.toLowerCase().replace(/ /g, '_'),
                command: FIELD_TO_COMMAND[item] || '/profile'
            };
        }
        // Already an object format
        return item;
    });
    
    const missingNames = normalizedMissing.slice(0, 3).map(m => m.name);
    const firstMissing = normalizedMissing[0];
    
    const content = `Welcome back! 👋 Your profile is **${percent}% complete**.

To help me write content that sounds like you, consider adding:
${missingNames.map(name => `• ${name}`).join('\n')}

${normalizedMissing.some(m => m.key === 'writing_samples') ? 
  "**Tip:** Sharing 2-3 examples of your past posts helps me match your unique style!" : ""}

Want to complete your profile now, or jump straight to creating content?`;
    
    const buttons = firstMissing ? [
      { label: `Add ${firstMissing.name}`, action: 'command', value: firstMissing.command },
      { label: 'Start creating →', action: 'focus' }
    ] : [
      { label: 'Start creating →', action: 'focus' }
    ];
    
    this.addMessage('assistant', content, false, false, buttons);
  }
  
  /**
   * Show ready state for complete profiles
   */
  showReadyState(profile) {
    const businessName = profile.company || profile.business_name || 'your business';
    const content = `Ready to create content for **${businessName}**! ✨

Try something like:
• "Write a post about our weekend sale"
• "Create an Instagram caption for this photo"
• "/post about our new product launch"

What would you like to create?`;
    
    this.addMessage('assistant', content, false, false, null);
  }

  /**
   * Add a message with optional button actions
   * @param {string} role - 'user' or 'assistant'
   * @param {string} content - Message content
   * @param {object} options - Optional config with buttons, isError, isGenerated
   */
  addAssistantMessage(content, options = {}) {
    const { buttons = [], isError = false, isGenerated = false } = options;
    
    const timestamp = Date.now();
    
    // Add to history
    this.conversationHistory.push({
      role: 'assistant',
      message: content,
      timestamp: timestamp
    });

    // Render message
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    
    const messageDiv = document.createElement('div');
    messageDiv.className = 'promptbox-message promptbox-message-assistant';
    if (isError) messageDiv.classList.add('promptbox-message-error');

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'promptbox-bubble';
    bubbleDiv.innerHTML = this.renderMarkdown(content);
    
    messageDiv.appendChild(bubbleDiv);
    
    // Add buttons if provided
    if (buttons && buttons.length > 0) {
      const buttonContainer = document.createElement('div');
      buttonContainer.className = 'promptbox-buttons';
      buttonContainer.style.cssText = 'display: flex; gap: 8px; margin-top: 12px; flex-wrap: wrap;';
      
      buttons.forEach(btn => {
        const button = document.createElement('button');
        button.className = 'promptbox-action-btn';
        button.textContent = btn.label;
        button.style.cssText = 'padding: 8px 16px; border: 1px solid #ddd; border-radius: 6px; background: white; cursor: pointer; font-size: 14px;';
        
        button.onclick = () => {
          if (btn.action === 'command') {
            // Execute command directly
            const textarea = document.getElementById(`${this.container.id}-textarea`);
            textarea.value = btn.value;
            this.handleSend();
          } else if (btn.action === 'prompt') {
            // Fill input for user to edit
            const textarea = document.getElementById(`${this.container.id}-textarea`);
            textarea.value = btn.value;
            const sendBtn = document.getElementById(`${this.container.id}-send`);
            this.updateSendButton(textarea, sendBtn);
            textarea.focus();
          }
        };
        
        buttonContainer.appendChild(button);
      });
      
      messageDiv.appendChild(buttonContainer);
    }
    
    // Add copy button for generated content
    if (isGenerated) {
      const copyBtn = document.createElement('button');
      copyBtn.className = 'promptbox-copy-btn';
      copyBtn.setAttribute('aria-label', 'Copy content');
      copyBtn.innerHTML = `
        <span class="copy-icon">📋</span>
        <span class="copy-text">Copy</span>
      `;
      copyBtn.onclick = () => this.copyContent(content, copyBtn);
      messageDiv.appendChild(copyBtn);
    }
    
    conversation.appendChild(messageDiv);

    // Auto-scroll to latest message if user is near bottom
    this.conditionalAutoScroll();
  }

  /**
   * Get completeness data from API response
   * @param {object} apiData - Full API response with completeness
   * @returns {object} - {missing: [], percent: number}
   */
  getCompletenessFromAPI(apiData) {
    if (apiData && apiData.completeness) {
      return {
        missing: apiData.completeness.missing_fields || [],
        percent: apiData.completeness.percent || 0,
        isComplete: apiData.completeness.is_complete || false
      };
    }
    // Fallback for empty/missing data
    return { missing: [], percent: 0, isComplete: false };
  }

  /**
   * Get voice suggestions based on industry
   * @param {string} industry - Industry name
   * @returns {array} - Array of voice suggestion strings
   */
  getVoiceSuggestionsForIndustry(industry) {
    const industryVoices = {
      'Restaurant / Café': ['Warm & welcoming', 'Fun & energetic', 'Sophisticated & refined'],
      'Fitness / Wellness': ['Motivating & bold', 'Calm & supportive', 'Expert & educational'],
      'Realtor / Real Estate': ['Professional & trustworthy', 'Friendly & approachable', 'Luxury & exclusive'],
      'Software / Tech / Startup': ['Innovative & bold', 'Clear & helpful', 'Casual & friendly'],
      'Retail / Boutique': ['Trendy & fun', 'Elegant & refined', 'Friendly & personal'],
      'Coach / Consultant': ['Expert & authoritative', 'Warm & encouraging', 'Bold & transformational'],
    };
    
    return industryVoices[industry] || [
      'Professional & friendly',
      'Casual & conversational', 
      'Bold & confident',
      'Warm & approachable'
    ];
  }

  /**
   * Render generated content with per-option copy buttons
   * @param {string} content - Raw content (may contain options)
   * @param {array} options - Array of option objects with text/label
   * @returns {string} HTML string for rendering
   */
  renderGeneratedContent(content, options) {
    if (options && options.length > 0) {
      // Store for copy functionality
      window.lastGeneratedOptions = options;
      
      let html = `
        <div class="message-assistant">
          <p class="message-intro">📝 Your post is ready!</p>
          <div class="options-container">
      `;
      
      options.forEach((opt, index) => {
        html += `
          <div class="option-card" data-option-index="${index}">
            <div class="option-header">
              <span class="option-label">Option ${index + 1}${opt.label ? ': ' + opt.label : ''}</span>
              <button class="copy-btn" onclick="copyOption(${index})" data-index="${index}">
                <span class="copy-icon">📋</span>
                <span class="copy-text">Copy</span>
              </button>
            </div>
            <div class="option-content">${this.escapeHtml(opt.text || opt)}</div>
          </div>
        `;
      });
      
      html += `
          </div>
          <div class="action-bar">
            <button class="action-btn" onclick="handleAction('regenerate')" title="Regenerate">
              <span class="action-icon">🔄</span>
              <span class="action-label">Regenerate</span>
            </button>
            <button class="action-btn" onclick="handleAction('shorter')" title="Make shorter">
              <span class="action-icon">✂️</span>
              <span class="action-label">Shorter</span>
            </button>
            <button class="action-btn" onclick="handleAction('casual')" title="More casual">
              <span class="action-icon">😊</span>
              <span class="action-label">Casual</span>
            </button>
            <button class="action-btn" onclick="handleAction('different')" title="Different angle">
              <span class="action-icon">🎨</span>
              <span class="action-label">Different</span>
            </button>
          </div>
        </div>
      `;
      
      return html;
    }
    
    // Single content (no options)
    window.lastGeneratedContent = content;
    return `
      <div class="message-assistant">
        <div class="option-card">
          <div class="option-header">
            <span class="option-label">Your content</span>
            <button class="copy-btn" onclick="copySingleContent()">
              <span class="copy-icon">📋</span>
              <span class="copy-text">Copy</span>
            </button>
          </div>
          <div class="option-content">${this.escapeHtml(content)}</div>
        </div>
      </div>
    `;
  }

  /**
   * Handle profile field commands like /voice, /audience, /offer
   */
  async handleProfileFieldCommand(command) {
    const field = PROFILE_FIELD_MAP[command];
    if (!field) return false;
    
    const label = FIELD_LABELS[field] || field;
    const emoji = FIELD_EMOJI[field] || '✨';
    
    // Show loading message (will be replaced with actual content)
    const loadingMsgId = this.addMessage('assistant', `Analyzing your profile for **${emoji} ${label}** suggestions...`);
    
    // Add loading animation to the message
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    const messages = conversation?.querySelectorAll('.promptbox-message-assistant');
    if (messages && messages.length > 0) {
      const lastMessage = messages[messages.length - 1];
      const bubble = lastMessage.querySelector('.promptbox-bubble');
      if (bubble) {
        bubble.classList.add('message-loading');
        const loadingSpan = document.createElement('span');
        loadingSpan.className = 'loading-dots';
        bubble.appendChild(document.createTextNode(' '));
        bubble.appendChild(loadingSpan);
      }
    }
    
    this.showLoading();
    
    try {
      // Fetch current profile for before/after comparison
      const profileResponse = await fetch('/api/profile', { credentials: 'include' });
      const profileData = await profileResponse.json();
      const currentValue = profileData.profile?.[field];
      
      // Make API call with timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), AI_SUGGESTION_TIMEOUT_MS);
      
      try {
        const response = await fetch('/api/profile/suggest', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          credentials: 'include',
          body: JSON.stringify({ field }),
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        const data = await response.json();
        this.hideLoading();
        
        if (data.success && data.suggestions && data.suggestions.length > 0) {
          // Enhanced message with context
          let message = `## Update ${emoji} ${label}\n\n`;
          
          // Show current value if exists
          if (currentValue) {
            message += `**Current:** ${currentValue}\n\n---\n\n`;
          }
          
          message += `Based on your profile for **${data.context.business_name}** in **${data.context.industry}**, here are 3 tailored suggestions:\n\n`;
          
          data.suggestions.forEach((suggestion, i) => {
            message += `**Option ${i + 1}:**\n${suggestion}\n\n`;
          });
          
          message += `---\n\n💡 **Why this matters:** ${WHY_IT_MATTERS[field]}\n\n`;
          message += `Which option resonates with your brand?\n`;
          
          // Create buttons for each suggestion
          const buttons = data.suggestions.map((suggestion, i) => ({
            label: `Use Option ${i + 1}`,
            action: 'select-profile-suggestion',
            field: field,
            value: suggestion
          }));
          
          buttons.push({
            label: '✏️ Write my own',
            action: 'focus'
          });
          
          // Replace loading message with actual suggestions including buttons
          this.updateMessage('last', message);
          
          // Render buttons into the same message
          if (messages && messages.length > 0) {
            const lastMessage = messages[messages.length - 1];
            this.renderMessageButtons(buttons, lastMessage);
          }
          
          // Store suggestions for selection as instance property
          this.pendingProfileSuggestions = {
            field: field,
            suggestions: data.suggestions,
            currentValue: currentValue
          };
          
        } else {
          // Fallback with helpful context
          const errorMsg = data.error || "I couldn't generate suggestions right now.";
          this.updateMessage('last', 
            `${errorMsg}\n\n💡 **${WHY_IT_MATTERS[field]}**\n\nWhat would you like your **${label}** to be?\n\nJust type it below:`
          );
        }
      } catch (fetchError) {
        clearTimeout(timeoutId);
        
        if (fetchError.name === 'AbortError') {
          // Timeout error
          this.hideLoading();
          this.updateMessage('last',
            `The suggestion request timed out after ${AI_SUGGESTION_TIMEOUT_MS / 1000} seconds. ⏱️\n\nYou can still update your **${label}** manually!\n\n💡 ${WHY_IT_MATTERS[field]}\n\nWhat would you like to set it to?`
          );
        } else {
          throw fetchError; // Re-throw for outer catch
        }
      }
      
    } catch (error) {
      this.hideLoading();
      console.error('Error getting profile suggestions:', error);
      this.updateMessage('last',
        `Something went wrong. 😕\n\nBut you can still update your **${label}** manually!\n\n💡 ${WHY_IT_MATTERS[field]}\n\nWhat would you like to set it to?`
      );
    }
    
    return true;
  }

  /**
   * Handle when user clicks a suggestion button
   */
  async selectProfileSuggestion(field, suggestion) {
    // Show what they selected (truncated)
    const truncated = suggestion.length > 60 ? suggestion.substring(0, 60) + '...' : suggestion;
    this.addMessage('user', `Use: "${truncated}"`);
    
    this.showLoading();
    
    try {
      // Get current profile state for before/after
      const beforeResponse = await fetch('/api/profile', { credentials: 'include' });
      const beforeData = await beforeResponse.json();
      const beforeCompleteness = this.getCompletenessFromAPI(beforeData).percent;
      
      // Save to profile using the field name directly
      const response = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          [field]: suggestion
        })
      });
      
      const data = await response.json();
      this.hideLoading();
      
      if (data.ok) {
        const label = FIELD_LABELS[field] || field;
        const emoji = FIELD_EMOJI[field] || '✨';
        
        // Get updated profile state
        const afterResponse = await fetch('/api/profile', { credentials: 'include' });
        const afterData = await afterResponse.json();
        const afterCompleteness = this.getCompletenessFromAPI(afterData).percent;
        
        // Build rich confirmation
        let message = `✅ **${emoji} ${label}** updated!\n\n`;
        
        // Show before/after if there was a change
        if (this.pendingProfileSuggestions?.currentValue) {
          message += `~~${this.pendingProfileSuggestions.currentValue}~~ → **${suggestion}**\n\n`;
        } else {
          message += `**${suggestion}**\n\n`;
        }
        
        // Show impact on content
        message += `💡 **Impact:** ${CONTENT_IMPACT[field]}\n\n`;
        
        // Show completeness change
        if (afterCompleteness > beforeCompleteness) {
          message += `📊 Profile Completeness: ${beforeCompleteness}% → ${afterCompleteness}% ⬆️\n\n`;
          
          // Celebrate milestones
          if (afterCompleteness >= 100) {
            message += `🎉 **Your profile is now complete!** Ready to create amazing content!\n\n`;
          } else if (afterCompleteness >= 66 && beforeCompleteness < 66) {
            message += `🎯 **Great progress!** Your profile is now sufficient for quality content generation.\n\n`;
          }
        }
        
        message += `What would you like to do next?`;
        
        this.addMessage('assistant', 
          message,
          false,
          false,
          [
            { label: '✨ Create content', action: 'focus' },
            { label: '👤 View profile', action: 'prompt', value: '/profile' },
            { label: '🔄 Update another field', action: 'prompt', value: '/update' }
          ]
        );
        
        // Refresh profile badge if exists
        if (typeof refreshProfileBadge === 'function') {
          refreshProfileBadge();
        }
        if (typeof initProfileBadge === 'function') {
          initProfileBadge();
        }
        
        // Clear pending state
        this.pendingProfileSuggestions = null;
        
      } else {
        throw new Error(data.error?.message || 'Failed to update profile');
      }
      
    } catch (error) {
      this.hideLoading();
      console.error('Error saving profile field:', error);
      this.addMessage('assistant', 
        `❌ I couldn't save that update.\n\n**Error:** ${error.message}\n\nPlease try again, or type \`/profile\` to edit manually.`
      );
    }
  }

  showLoading() {
    this.setLoading(true);
  }

  hideLoading() {
    this.setLoading(false);
  }

  /**
   * Handle onboarding input during chat-based profile setup
   * @param {string} userMessage - User's message
   * @returns {boolean} - True if handled, false otherwise
   */
  async handleOnboardingInput(userMessage) {
    // Helper function for escaping HTML in template strings
    const escapeHtml = (text) => this.escapeHtml(text);
    
    const ONBOARDING_STATES = {
      'awaiting_business_name': {
        field: 'business_name',
        next: 'awaiting_industry',
        getPrompt: (data) => `Great! Now, what industry or type of business is **${escapeHtml(data.business_name)}**? (e.g., Restaurant, Software, Fitness, Retail)`
      },
      'awaiting_industry': {
        field: 'industry',
        next: 'awaiting_voice',
        getPrompt: (data) => "Perfect! How would you describe your brand's personality? Choose one or describe your own:\n\n• **Friendly** - Warm, approachable, conversational\n• **Professional** - Clear, confident, authoritative\n• **Playful** - Fun, witty, energetic\n• **Inspirational** - Uplifting, motivational, mission-driven"
      },
      'awaiting_voice': {
        field: 'brand_voice',
        next: 'complete',
        getPrompt: (data) => `Awesome! Your profile is set up. Here's what I know:

**${escapeHtml(data.business_name)}** | ${escapeHtml(data.industry)} | ${escapeHtml(data.brand_voice)}

You're ready to create content! Try:
- "Write an Instagram post about our latest product"
- Type \`/post\` for a quick social post
- Type \`/audience\` to refine who you're targeting

**What would you like to create first?**`
      }
    };
    
    const state = window.onboardingState;
    if (!state || !ONBOARDING_STATES[state]) {
      return false;
    }
    
    const stateConfig = ONBOARDING_STATES[state];
    
    try {
      // Save the field
      const saveResponse = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({
          [stateConfig.field]: userMessage.trim()
        })
      });
      
      if (!saveResponse.ok) {
        const errorData = await saveResponse.json().catch(() => ({}));
        const errorMessage = errorData.error?.message || "I couldn't save that. Please try again.";
        this.addMessage('assistant', `Hmm, ${errorMessage}`);
        return true;
      }
      
      // Store for template substitution
      if (!window.onboardingData) window.onboardingData = {};
      window.onboardingData[stateConfig.field] = userMessage.trim();
      
      // Move to next state
      if (stateConfig.next === 'complete') {
        window.onboardingState = null;
        
        // Refresh profile badge if function exists
        if (typeof updateProfileBadge === 'function') {
          try {
            const profileResponse = await fetch('/api/profile', { credentials: 'include' });
            const profileData = await profileResponse.json();
            if (profileData.ok && profileData.profile) {
              updateProfileBadge(profileData.profile);
            }
          } catch (err) {
            console.error('Failed to refresh profile badge:', err);
          }
        }
      } else {
        window.onboardingState = stateConfig.next;
      }
      
      // Show next prompt
      const nextPrompt = stateConfig.getPrompt(window.onboardingData);
      this.addMessage('assistant', nextPrompt);
      
      return true;
    } catch (error) {
      console.error('Error in onboarding:', error);
      this.addMessage('assistant', "Sorry, something went wrong. Please try again.");
      return true;
    }
  }

  destroy() {
    this.stopSuggestionRotation();
    if (this.container) {
      this.container.innerHTML = '';
    }
  }
}

// Export for use in other scripts
if (typeof window !== 'undefined') {
  window.PromptBox = PromptBox;
  window.SLASH_COMMANDS = SLASH_COMMANDS; // Export slash commands for dashboard
}

/**
 * Profile command handlers
 * These functions handle the new profile management slash commands
 */

async function showProfileSummary(promptBox) {
  const response = await fetch('/api/profile', { credentials: 'include' });
  const data = await response.json();
  
  if (!data.ok || !data.profile) {
    promptBox.addMessage('assistant', `You don't have a profile yet! Let's create one.\n\nTell me about your business, or use \`/import <url>\` to import from your website.`);
    return;
  }
  
  const p = data.profile;
  const completenessData = data.completeness || { percent: 0, missing_fields: [] };
  const { missing, percent } = { missing: completenessData.missing_fields, percent: completenessData.percent };
  
  // Build rich profile summary
  let summary = `## 👤 Your Brand Profile\n\n`;
  
  // Completeness header with visual indicator
  const completenessBar = '█'.repeat(Math.floor(percent / 10)) + '░'.repeat(10 - Math.floor(percent / 10));
  summary += `**Completeness:** ${percent}% ${completenessBar}\n\n`;
  
  if (percent === 100) {
    summary += `🎉 **Your profile is complete!** You're ready to create amazing content.\n\n`;
  } else if (percent >= 66) {
    summary += `🎯 **Looking good!** Your profile is sufficient for quality content.\n\n`;
  } else if (percent >= 33) {
    summary += `⚡ **Good start!** Adding more details will improve content quality.\n\n`;
  } else {
    summary += `🚀 **Let's build your profile!** Add a few more details to unlock better content.\n\n`;
  }
  
  summary += `---\n\n`;
  
  // Required fields section
  summary += `### Required Fields\n\n`;
  summary += `**Business Name:** ${p.company || p.business_name || '❌ Not set'}\n`;
  summary += `**Industry:** ${p.industry || '❌ Not set'}\n`;
  summary += `**Brand Voice:** ${p.tone || p.brand_voice || '❌ Not set'}\n\n`;
  
  // Recommended fields section
  summary += `### Recommended Fields\n\n`;
  summary += `**Target Audience:** ${p.target_audience || '➖ Not set (helps target content to your customers)'}\n`;
  summary += `**Key Offer:** ${p.key_offer || '➖ Not set (highlights what makes you unique)'}\n\n`;
  
  // Advanced fields section
  summary += `### Advanced Fields\n\n`;
  const sampleCount = p.writing_samples?.length || 0;
  summary += `**Writing Samples:** ${sampleCount} sample${sampleCount !== 1 ? 's' : ''}`;
  if (sampleCount === 0) {
    summary += ` (adding samples helps match your unique style)`;
  }
  summary += `\n`;
  summary += `**Voice Rules:** ${p.voice_rules || '➖ Not set (optional guidelines)'}\n\n`;
  
  // Quick actions
  const buttons = [];
  
  if (missing.length > 0) {
    summary += `---\n\n### 🎯 Quick Actions to Improve Your Profile\n\n`;
    
    // Add button for first missing field
    const firstMissing = missing[0];
    const commandMap = {
      'Brand Voice': '/voice',
      'Target Audience': '/audience',
      'Key Offer': '/offer',
      'Writing Samples': '/samples',
      'Voice Rules': '/rules'
    };
    
    if (commandMap[firstMissing]) {
      summary += `• \`${commandMap[firstMissing]}\` - Add ${firstMissing}\n`;
      buttons.push({ 
        label: `Add ${firstMissing}`, 
        action: 'prompt', 
        value: commandMap[firstMissing] 
      });
    }
    
    // Add button for writing samples if missing
    if (sampleCount === 0 && firstMissing !== 'Writing Samples') {
      summary += `• \`/samples\` - Add writing examples\n`;
      buttons.push({ 
        label: '✍️ Add Writing Samples', 
        action: 'prompt', 
        value: '/samples' 
      });
    }
    
    buttons.push({ 
      label: '✨ Create Content', 
      action: 'focus' 
    });
  } else {
    buttons.push({ 
      label: '✨ Create Content', 
      action: 'focus' 
    });
    buttons.push({ 
      label: '🔄 Update a field', 
      action: 'prompt', 
      value: '/update' 
    });
  }
  
  promptBox.addMessage('assistant', summary, false, false, buttons);
}

async function showVoiceUpdateFlow(promptBox, existingValue) {
  // Get current profile for industry context
  const response = await fetch('/api/profile', { credentials: 'include' });
  const data = await response.json();
  const industry = data.profile?.industry || '';
  
  // Industry-specific suggestions
  const suggestions = promptBox.getVoiceSuggestionsForIndustry(industry);
  
  let message = `## Update Brand Voice 🎤\n\n`;
  if (data.profile?.tone || data.profile?.brand_voice) {
    message += `**Current:** ${data.profile.tone || data.profile.brand_voice}\n\n`;
  }
  message += `How would you like your brand to sound? Pick one or describe your own:\n`;
  
  const buttons = suggestions.map(s => ({
    label: s,
    action: 'command',
    value: `/voice ${s}`
  }));
  
  promptBox.addMessage('assistant', message, false, false, buttons);
}

async function showAudienceUpdateFlow(promptBox, existingValue) {
  const response = await fetch('/api/profile', { credentials: 'include' });
  const data = await response.json();
  
  let message = `## Define Target Audience 🎯\n\n`;
  if (data.profile?.target_audience) {
    message += `**Current:** ${data.profile.target_audience}\n\n`;
  }
  message += `Who is your ideal customer? Be specific! Examples:\n`;
  message += `• "Busy professionals aged 30-45 looking for quick healthy meals"\n`;
  message += `• "First-time homebuyers in Austin with $400k budget"\n`;
  message += `• "Small business owners who struggle with social media"\n\n`;
  message += `Type your target audience description:`;
  
  promptBox.addMessage('assistant', message);
}

async function showSamplesCollectionFlow(promptBox) {
  const response = await fetch('/api/profile', { credentials: 'include' });
  const data = await response.json();
  const currentCount = data.profile?.writing_samples?.length || 0;
  
  let message = `## Add Writing Samples ✍️\n\n`;
  message += `**Current samples:** ${currentCount}\n\n`;
  message += `Paste 2-3 examples of your best writing - social posts, emails, or website copy.\n\n`;
  message += `**Why this matters:** I'll analyze your style and match it when creating content.\n\n`;
  message += `**Tips for good samples:**\n`;
  message += `• Choose posts that got good engagement\n`;
  message += `• Pick ones that "sound like you"\n`;
  message += `• Include different types (promotional, educational, personal)\n\n`;
  message += `Paste your first sample:`;
  
  promptBox.addMessage('assistant', message);
  
  // Set state to collect samples using instance state
  promptBox.collectionState = { collecting: 'writing_samples', samples: [] };
}

async function showImportFlow(promptBox, url) {
  if (url && url.trim()) {
    // URL provided - start import
    promptBox.addMessage('assistant', `Great! Let me analyze your website... 🔍\n\nScraping ${url}...`);
    
    try {
      const response = await fetch('/onboarding/social-style', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ url: url.trim(), consent: true })
      });
      
      const data = await response.json();
      
      if (data.suggestions) {
        // Build complete preview with ALL extracted fields
        let message = `I analyzed your website and here's what I found:\n\n📋 **Extracted Profile Data:**\n\n`;
        
        const foundFields = [];
        const missingFields = [];
        
        // Check and display each field
        if (data.suggestions.business_name) {
          message += `**Business Name:** ${data.suggestions.business_name}\n`;
          foundFields.push('Business Name');
        } else {
          missingFields.push('Business Name');
        }
        
        if (data.suggestions.industry) {
          message += `**Industry:** ${data.suggestions.industry}\n`;
          foundFields.push('Industry');
        } else {
          missingFields.push('Industry');
        }
        
        // Handle brand_voice from either brand_voice or voice_tone_and_style
        const brandVoice = data.suggestions.brand_voice || data.suggestions.voice_tone_and_style;
        if (brandVoice) {
          message += `**Brand Voice:** ${brandVoice}\n`;
          foundFields.push('Brand Voice');
        } else {
          missingFields.push('Brand Voice');
        }
        
        if (data.suggestions.key_customers) {
          message += `**Target Audience:** ${data.suggestions.key_customers}\n`;
          foundFields.push('Target Audience');
        } else {
          missingFields.push('Target Audience');
        }
        
        if (data.suggestions.key_offer) {
          message += `**Key Offer:** ${data.suggestions.key_offer}\n`;
          foundFields.push('Key Offer');
        } else {
          missingFields.push('Key Offer');
        }
        
        // Keywords
        if (data.suggestions.brand_keywords && data.suggestions.brand_keywords.length > 0) {
          message += `**Brand Keywords:** ${data.suggestions.brand_keywords.join(', ')}\n`;
          foundFields.push('Brand Keywords');
        }
        
        if (data.suggestions.niche_keywords && data.suggestions.niche_keywords.length > 0) {
          message += `**Niche Keywords:** ${data.suggestions.niche_keywords.join(', ')}\n`;
          foundFields.push('Niche Keywords');
        }
        
        // Writing samples (from sample_posts or sample_copy)
        const samples = data.suggestions.sample_posts || data.suggestions.sample_copy || [];
        if (samples.length > 0) {
          message += `\n**Writing Sample Found:**\n"${samples[0].substring(0, 150)}${samples[0].length > 150 ? '...' : ''}"`;
          if (samples.length > 1) {
            message += `\n\n_Plus ${samples.length - 1} more sample${samples.length - 1 > 1 ? 's' : ''}_`;
          }
          foundFields.push('Writing Samples');
        }
        
        // Show what was successfully extracted
        if (foundFields.length > 0) {
          message += `\n\n✅ **Successfully extracted:** ${foundFields.join(', ')}`;
        }
        
        // Show partial scrape info with helpful suggestions if missing required fields
        if (missingFields.length > 0) {
          message += `\n\n⚠️ **Couldn't extract:** ${missingFields.join(', ')}\n`;
          message += `\n💡 **Tip:** These fields might not be visible on your homepage. You can:`;
          message += `\n• Save what I found and manually add the rest later`;
          message += `\n• Try a different page (like your "About" page)`;
          message += `\n• Just tell me the missing information directly`;
          message += `\n\nWant to save what I found?`;
          
          const buttons = [
            { label: '✅ Save & fill rest later', action: 'command', value: '/import-confirm' },
            { label: '✏️ Edit now', action: 'command', value: '/import-edit' },
            { label: '🔄 Try different URL', action: 'message', value: '/import ' },
            { label: '❌ Cancel', action: 'command', value: '/import-cancel' }
          ];
          
          promptBox.addMessage('assistant', message, false, false, buttons);
        } else {
          // Complete scrape
          message += `\n\n✨ **Great! I found everything!**\n\nDoes this look accurate?`;
          
          const buttons = [
            { label: '✅ Save all', action: 'command', value: '/import-confirm' },
            { label: '✏️ Edit before saving', action: 'command', value: '/import-edit' },
            { label: '❌ Cancel', action: 'command', value: '/import-cancel' }
          ];
          
          promptBox.addMessage('assistant', message, false, false, buttons);
        }
        
        // Store for confirmation using instance state
        promptBox.pendingImport = data.suggestions;
        promptBox.pendingImportUrl = url.trim();
      } else {
        // No data extracted at all
        promptBox.addMessage('assistant', `I couldn't extract business information from that URL. This might happen if:\n\n• The page has mostly images/videos\n• It's behind a login wall\n• The content is dynamically loaded\n\nYou can:\n• Try a different page (like "About" or "Services")\n• Tell me about your business instead\n• Use the profile form to enter details manually\n\nWhat would you like to do?`);
      }
    } catch (error) {
      promptBox.addMessage('assistant', `Error analyzing URL: ${error.message}. Try again or describe your business instead.`);
    }
  } else {
    // No URL - prompt for one
    promptBox.addMessage('assistant', `## Import from URL 🔗\n\nPaste your website or social media URL and I'll extract your brand info:\n\n\`/import https://yourwebsite.com\``);
  }
}

/**
 * Handle /import-confirm - Save imported data to profile
 */
async function handleImportConfirm(promptBox) {
  if (!promptBox.pendingImport) {
    promptBox.addMessage('assistant', `No pending import data. Use \`/import [url]\` to start.`);
    return;
  }
  
  try {
    // Get current profile for before completeness
    const beforeResponse = await fetch('/api/profile', { credentials: 'include' });
    const beforeData = await beforeResponse.json();
    const beforePercent = beforeData.ok && beforeData.completeness 
      ? beforeData.completeness.percent 
      : 0;
    
    // Map imported data to profile format
    const importData = promptBox.pendingImport;
    const profileData = {
      company: importData.business_name || '',
      industry: importData.industry || '',
      brand_voice: importData.brand_voice || importData.voice_tone_and_style || '',
      target_audience: importData.key_customers || '',
      key_offer: importData.key_offer || '',
      brand_keywords: importData.brand_keywords || [],
      niche_keywords: importData.niche_keywords || [],
      voice_rules: importData.voice_rules || '',
      goals: importData.goals || [],
      scraped_url: promptBox.pendingImportUrl || ''
    };
    
    // Map sample_posts to writing_samples
    const samples = importData.sample_posts || importData.sample_copy || [];
    if (samples.length > 0) {
      profileData.writing_samples = samples;
    }
    
    // Save to profile
    const saveResponse = await fetch('/api/profile', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(profileData)
    });
    
    if (!saveResponse.ok) {
      throw new Error('Failed to save profile');
    }
    
    const saveData = await saveResponse.json();
    
    // Get updated profile for after completeness
    const afterResponse = await fetch('/api/profile', { credentials: 'include' });
    const afterData = await afterResponse.json();
    const afterPercent = afterData.ok && afterData.completeness 
      ? afterData.completeness.percent 
      : 0;
    
    // Build success message
    let message = `Excellent! I've imported all that data into your profile. ✨\n\n`;
    
    // Show completeness change
    if (afterPercent > beforePercent) {
      message += `**Profile Completeness:** ${beforePercent}% → ${afterPercent}% ⬆️\n\n`;
    }
    
    message += `Here's your updated profile:\n`;
    if (profileData.company) message += `✅ **Business Name:** ${profileData.company}\n`;
    if (profileData.industry) message += `✅ **Industry:** ${profileData.industry}\n`;
    if (profileData.brand_voice) message += `✅ **Brand Voice:** ${profileData.brand_voice}\n`;
    if (profileData.target_audience) message += `✅ **Target Audience:** ${profileData.target_audience.substring(0, 80)}${profileData.target_audience.length > 80 ? '...' : ''}\n`;
    if (profileData.key_offer) message += `✅ **Key Offer:** ${profileData.key_offer.substring(0, 80)}${profileData.key_offer.length > 80 ? '...' : ''}\n`;
    if (samples.length > 0) message += `✅ **Writing Samples:** ${samples.length} sample${samples.length > 1 ? 's' : ''}\n`;
    
    // Check for missing required fields and offer to auto-trigger suggestions
    const missingFields = [];
    if (!profileData.brand_voice) missingFields.push('brand_voice');
    if (!profileData.target_audience) missingFields.push('target_audience');
    if (!profileData.key_offer) missingFields.push('key_offer');
    
    if (missingFields.length === 0) {
      message += `\nYou're all set to create content! Want to:`;
      
      const buttons = [
        { label: '📝 Create a post', action: 'command', value: '/post' },
        { label: '✍️ Add more writing samples', action: 'command', value: '/samples' },
        { label: '👤 View full profile', action: 'command', value: '/profile' }
      ];
      
      promptBox.addMessage('assistant', message, false, false, buttons);
    } else {
      message += `\nLet me help you fill in the missing fields!`;
      promptBox.addMessage('assistant', message);
      
      // Auto-trigger suggestions for first missing field
      if (missingFields.includes('brand_voice')) {
        await promptBox.handleProfileFieldCommand('/voice');
      } else if (missingFields.includes('target_audience')) {
        await promptBox.handleProfileFieldCommand('/audience');
      } else if (missingFields.includes('key_offer')) {
        await promptBox.handleProfileFieldCommand('/offer');
      }
    }
    
    // Clear pending import
    promptBox.pendingImport = null;
    promptBox.pendingImportUrl = null;
    
    // Refresh profile badge
    if (typeof refreshProfileBadge === 'function') {
      refreshProfileBadge();
    }
    
  } catch (error) {
    console.error('Error saving import:', error);
    promptBox.addMessage('assistant', `Sorry, there was an error saving your profile: ${error.message}. Please try again.`);
  }
}

/**
 * Handle /import-edit - Start in-chat edit flow
 */
async function handleImportEdit(promptBox) {
  if (!promptBox.pendingImport) {
    promptBox.addMessage('assistant', `No pending import data. Use \`/import [url]\` to start.`);
    return;
  }
  
  const importData = promptBox.pendingImport;
  
  // Build field list
  const fields = [];
  if (importData.business_name) {
    fields.push({ num: fields.length + 1, key: 'business_name', label: 'Business Name', value: importData.business_name });
  }
  if (importData.industry) {
    fields.push({ num: fields.length + 1, key: 'industry', label: 'Industry', value: importData.industry });
  }
  const brandVoice = importData.brand_voice || importData.voice_tone_and_style;
  if (brandVoice) {
    fields.push({ num: fields.length + 1, key: 'brand_voice', label: 'Brand Voice', value: brandVoice });
  }
  if (importData.key_customers) {
    fields.push({ num: fields.length + 1, key: 'key_customers', label: 'Target Audience', value: importData.key_customers });
  }
  if (importData.key_offer) {
    fields.push({ num: fields.length + 1, key: 'key_offer', label: 'Key Offer', value: importData.key_offer });
  }
  
  let message = `No problem! Let's refine the extracted data. What would you like to change?\n\n**Current fields:**\n`;
  fields.forEach(f => {
    const displayValue = f.value.length > 60 ? f.value.substring(0, 60) + '...' : f.value;
    message += `${f.num}. **${f.label}:** ${displayValue}\n`;
  });
  
  message += `\nTell me which number to edit, or type 'save' when you're happy with it.`;
  
  // Store edit state
  promptBox.editMode = 'import';
  promptBox.editFields = fields;
  
  promptBox.addMessage('assistant', message);
}

/**
 * Handle /import-cancel - Cancel import flow
 */
async function handleImportCancel(promptBox) {
  promptBox.pendingImport = null;
  promptBox.pendingImportUrl = null;
  promptBox.editMode = null;
  promptBox.editFields = null;
  promptBox.editingField = null;
  
  promptBox.addMessage('assistant', `Import cancelled. You can try again with \`/import [url]\` or tell me about your business manually.`);
}

/**
 * Handle user input during import edit mode
 */
async function handleImportEditInput(promptBox, message) {
  const input = message.trim().toLowerCase();
  
  // Check if user wants to save
  if (input === 'save') {
    // Exit edit mode and save
    promptBox.editMode = null;
    promptBox.editFields = null;
    promptBox.editingField = null;
    await handleImportConfirm(promptBox);
    return;
  }
  
  // Check if it's a field number
  const fieldNum = parseInt(input);
  if (!isNaN(fieldNum) && fieldNum > 0 && fieldNum <= promptBox.editFields.length) {
    const field = promptBox.editFields[fieldNum - 1];
    
    // Store which field we're editing
    promptBox.editingField = field;
    
    promptBox.addMessage('assistant', `**Current ${field.label}:** "${field.value}"\n\nHow would you like to update it?`);
    return;
  }
  
  // Check if we're in the middle of editing a specific field
  if (promptBox.editingField) {
    const field = promptBox.editingField;
    
    // Update the field value in pendingImport
    if (field.key === 'brand_voice') {
      promptBox.pendingImport.brand_voice = message;
      if (promptBox.pendingImport.voice_tone_and_style) {
        promptBox.pendingImport.voice_tone_and_style = message;
      }
    } else {
      promptBox.pendingImport[field.key] = message;
    }
    
    // Update the field in editFields too
    field.value = message;
    
    promptBox.addMessage('assistant', `Updated! ✅\n\n**${field.label}** is now: "${message}"\n\nWant to edit anything else? (Choose a number, or type 'save')`);
    
    // Clear editing field
    promptBox.editingField = null;
    return;
  }
  
  // Invalid input
  promptBox.addMessage('assistant', `Please enter a field number (1-${promptBox.editFields.length}) to edit, or type 'save' to save your changes.`);
}

async function handleHelpCommand(promptBox) {
  const helpMessage = `## ❓ Available Commands

### 📝 Content Creation
| Command | Description |
|---------|-------------|
| \`/post\` | Create a social media post |
| \`/caption\` | Write an image caption |
| \`/script\` | Write a video script |
| \`/reel\` | Create a reel/short video script |
| \`/email\` | Draft an email |
| \`/review\` | Respond to a review |
| \`/ad\` | Create ad copy |
| \`/blog\` | Write a blog post |

### 👤 Profile Management
| Command | Description |
|---------|-------------|
| \`/profile\` | View your brand profile |
| \`/voice\` | Update your brand voice/tone |
| \`/audience\` | Define your target audience |
| \`/offer\` | Set your key offer/value proposition |
| \`/samples\` | Add writing samples |
| \`/rules\` | Set voice rules and guidelines |
| \`/import [url]\` | Import profile from website |

---
💡 **Tip:** You can also just describe what you want in plain English and I'll figure out the rest!`;

  promptBox.addMessage('assistant', helpMessage);
}

async function handleProfileCommand(promptBox, command, args) {
  switch (command) {
    case '/help':
      await handleHelpCommand(promptBox);
      break;
    case '/profile':
      await showProfileSummary(promptBox);
      break;
    case '/voice':
      await showVoiceUpdateFlow(promptBox, args);
      break;
    case '/audience':
      await showAudienceUpdateFlow(promptBox, args);
      break;
    case '/offer':
      // Delegate to handleProfileFieldCommand which has AI suggestions
      await promptBox.handleProfileFieldCommand('/offer');
      break;
    case '/rules':
      // Delegate to handleProfileFieldCommand which has AI suggestions
      await promptBox.handleProfileFieldCommand('/rules');
      break;
    case '/samples':
      await showSamplesCollectionFlow(promptBox);
      break;
    case '/import':
      await showImportFlow(promptBox, args);
      break;
    case '/import-confirm':
      await handleImportConfirm(promptBox);
      break;
    case '/import-edit':
      await handleImportEdit(promptBox);
      break;
    case '/import-cancel':
      await handleImportCancel(promptBox);
      break;
  }
}

// Export profile command handlers
if (typeof window !== 'undefined') {
  window.handleProfileCommand = handleProfileCommand;
  window.handleHelpCommand = handleHelpCommand;
  window.showProfileSummary = showProfileSummary;
  window.showVoiceUpdateFlow = showVoiceUpdateFlow;
  window.showAudienceUpdateFlow = showAudienceUpdateFlow;
  window.showSamplesCollectionFlow = showSamplesCollectionFlow;
  window.showImportFlow = showImportFlow;
}

/**
 * Refresh the profile completeness badge with current data
 */
async function refreshProfileBadge() {
  try {
    const response = await fetch('/api/profile', { credentials: 'include' });
    const data = await response.json();
    
    if (data.ok && data.completeness) {
      const badgeEl = document.querySelector('.profile-completeness-badge');
      if (badgeEl) {
        const percent = data.completeness.percent || 0;
        
        // Update badge
        badgeEl.textContent = `${percent}%`;
        badgeEl.className = 'profile-completeness-badge';
        
        // Add color coding
        if (percent >= 100) {
          badgeEl.classList.add('complete');
        } else if (percent >= 66) {
          badgeEl.classList.add('sufficient');
        } else if (percent >= 33) {
          badgeEl.classList.add('started');
        } else {
          badgeEl.classList.add('minimal');
        }
        
        // Animate change
        badgeEl.classList.add('updated');
        setTimeout(() => badgeEl.classList.remove('updated'), 1000);
      }
    }
  } catch (error) {
    console.error('Failed to refresh profile badge:', error);
  }
}

// Export for global access
if (typeof window !== 'undefined') {
  window.refreshProfileBadge = refreshProfileBadge;
}
