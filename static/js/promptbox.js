/**
 * PromptBox - Unified conversational UI component
 * Provides Copilot-style interface for onboarding and content creation
 */

// Slash command definitions
const SLASH_COMMANDS = [
  // Content commands
  { command: '/post', description: 'Create a social media post', icon: '📝', category: 'content' },
  { command: '/caption', description: 'Write an image caption', icon: '📸', category: 'content' },
  { command: '/script', description: 'Write a video script', icon: '🎬', category: 'content' },
  { command: '/reel', description: 'Create a reel/short video script', icon: '🎥', category: 'content' },
  { command: '/email', description: 'Draft an email', icon: '✉️', category: 'content' },
  { command: '/review', description: 'Respond to a review', icon: '⭐', category: 'content' },
  { command: '/ad', description: 'Create ad copy', icon: '📢', category: 'content' },
  { command: '/blog', description: 'Write a blog post', icon: '📰', category: 'content' },
  
  // Profile management commands
  { command: '/profile', description: 'View and manage your brand profile', icon: '👤', category: 'profile' },
  { command: '/update', description: 'Update a profile field', icon: '✏️', category: 'profile' },
  { command: '/voice', description: 'Update your brand voice/tone', icon: '🎤', category: 'profile' },
  { command: '/audience', description: 'Define your target audience', icon: '🎯', category: 'profile' },
  { command: '/offer', description: 'Set your key offer/value proposition', icon: '💎', category: 'profile' },
  { command: '/samples', description: 'Add writing samples to match your style', icon: '✍️', category: 'profile' },
  { command: '/rules', description: 'Set voice rules and guidelines', icon: '📋', category: 'profile' },
  { command: '/import', description: 'Import profile from your website URL', icon: '🔗', category: 'profile' },
  
  // Help command
  { command: '/help', description: 'Show all available commands', icon: '❓', category: 'help' },
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
    this.pendingProfileSuggestions = null; // Track pending profile suggestions for selection
    this.hasUsedSlashCommand = localStorage.getItem('eazeily_used_slash') === 'true'; // Track if user has used slash commands

    // Get suggestions based on context
    this.suggestions = this.getSuggestions();

    // Initialize component
    this.render();
    this.attachEventListeners();
    this.startSuggestionRotation();
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
    textarea.style.height = 'auto';
    const minHeight = 44; // Min height for touch targets
    const maxHeight = 120; // Max 4 lines approx (30px per line)
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = `${newHeight}px`;
  }

  updateSendButton(textarea, sendBtn) {
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
      // Check if this is a profile command that should be handled client-side
      const profileCommands = ['/profile', '/voice', '/audience', '/offer', '/samples', '/rules', '/import', '/help'];
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
      this.addMessage('assistant', 'Sorry, something went wrong. Please try again.', true);
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
      this.addMessage('assistant', 'Sorry, something went wrong. Please try again.', true);
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
    
    // Add assistant message
    const isGenerated = data.action === 'generated' || (data.content && data.content.length > 100);
    this.addMessage('assistant', data.response, false, isGenerated);
    
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

  addMessage(role, content, isError = false, isGenerated = false, buttons = null) {
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

    // For assistant messages, render markdown
    if (role === 'assistant') {
      bubbleDiv.innerHTML = this.renderMarkdown(content);
      
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
    } else {
      bubbleDiv.textContent = content;
    }

    messageDiv.appendChild(bubbleDiv);
    
    // Add buttons if provided
    if (buttons && buttons.length > 0) {
      this.renderMessageButtons(buttons, messageDiv);
    }
    
    conversation.appendChild(messageDiv);

    // Auto-scroll to latest message
    this.scrollToBottom();
  }
  
  renderMessageButtons(buttons, messageEl) {
    if (!buttons || !buttons.length) return;
    
    const btnContainer = document.createElement('div');
    btnContainer.className = 'promptbox-button-container flex flex-wrap gap-2 mt-3';
    
    buttons.forEach(btn => {
      const button = document.createElement('button');
      button.className = 'promptbox-action-btn px-3 py-1.5 text-sm bg-indigo-50 text-indigo-700 rounded-lg border border-indigo-200 hover:bg-indigo-100 transition-colors';
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
        
        if (btn.action === 'prompt') {
          // Pre-fill the input with the value
          const textarea = document.getElementById(`${this.container.id}-textarea`);
          if (textarea) {
            textarea.value = btn.value;
            this.autoResizeTextarea(textarea);
            const sendBtn = document.getElementById(`${this.container.id}-send`);
            this.updateSendButton(textarea, sendBtn);
            textarea.focus();
          }
        } else if (btn.action === 'focus') {
          const textarea = document.getElementById(`${this.container.id}-textarea`);
          if (textarea) textarea.focus();
        } else if (btn.action === 'command') {
          // Execute command directly
          const textarea = document.getElementById(`${this.container.id}-textarea`);
          if (textarea) {
            textarea.value = btn.value;
            this.handleSend();
          }
        }
      };
      
      btnContainer.appendChild(button);
    });
    
    messageEl.appendChild(btnContainer);
  }

  renderMarkdown(text) {
    // Simple markdown rendering (bold, italic, code, lists)
    let html = this.escapeHtml(text);

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
    const conversation = document.getElementById(`${this.container.id}-conversation`);
    if (conversation) {
      // Smooth scroll to bottom
      conversation.scrollTo({
        top: conversation.scrollHeight,
        behavior: 'smooth'
      });
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
    const loadingEl = document.getElementById(`${this.container.id}-loading`);
    const textarea = document.getElementById(`${this.container.id}-textarea`);
    const sendBtn = document.getElementById(`${this.container.id}-send`);

    if (isLoading) {
      loadingEl.classList.remove('hidden');
      textarea.disabled = true;
      sendBtn.disabled = true;
    } else {
      loadingEl.classList.add('hidden');
      textarea.disabled = false;
      this.updateSendButton(textarea, sendBtn);
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
      
      const { isComplete, missing, percent } = this.checkProfileCompleteness(data.profile);
      
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
   * Check profile completeness
   * Returns completion percentage and list of missing fields
   */
  checkProfileCompleteness(profile) {
    const requiredFields = [
      { key: 'business_name', value: profile.company || profile.business_name, command: '/update business_name ' },
      { key: 'industry', value: profile.industry, command: '/update industry ' },
      { key: 'brand_voice', value: profile.tone || profile.brand_voice, command: '/voice ' },
    ];
    
    const optionalFields = [
      { key: 'target_audience', value: profile.target_audience, command: '/audience ' },
      { key: 'key_offer', value: profile.key_offer, command: '/update key_offer ' },
      { key: 'writing_samples', value: profile.writing_samples && profile.writing_samples.length > 0, command: '/profile ' },
      { key: 'brand_keywords', value: profile.brand_keywords && profile.brand_keywords.length > 0, command: '/profile ' },
      { key: 'goals', value: profile.goals && profile.goals.length > 0, command: '/profile ' },
    ];
    
    const missing = [];
    let filled = 0;
    const total = requiredFields.length + optionalFields.length;
    
    // Check required
    for (const field of requiredFields) {
      if (field.value && String(field.value).trim()) {
        filled++;
      } else {
        missing.push({
          name: this.formatFieldName(field.key),
          key: field.key,
          command: field.command,
          isRequired: true
        });
      }
    }
    
    // Check optional
    for (const field of optionalFields) {
      if (field.value && (typeof field.value === 'boolean' ? field.value : String(field.value).trim())) {
        filled++;
      } else {
        missing.push({
          name: this.formatFieldName(field.key),
          key: field.key,
          command: field.command,
          isRequired: false
        });
      }
    }
    
    return {
      isComplete: missing.filter(m => m.isRequired).length === 0,
      missing,
      percent: Math.round((filled / total) * 100)
    };
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
    // missing is now an array of objects with {name, key, command, isRequired}
    const missingNames = missing.slice(0, 3).map(m => m.name);
    const content = `Welcome back! 👋 Your profile is **${percent}% complete**.

To help me write content that sounds like you, consider adding:
${missingNames.map(name => `• ${name}`).join('\n')}

${missing.some(m => m.key === 'writing_samples') ? 
  "**Tip:** Sharing 2-3 examples of your past posts helps me match your unique style!" : ""}

Want to complete your profile now, or jump straight to creating content?`;
    
    const buttons = [
      { label: `Add ${missing[0].name}`, action: 'prompt', value: missing[0].command },
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

    // Auto-scroll to latest message
    this.scrollToBottom();
  }

  /**
   * Check profile completeness
   * @param {object} profile - Profile object
   * @returns {object} - {missing: [], percent: number}
   */
  checkProfileCompleteness(profile) {
    const missing = [];
    let foundCount = 0;
    
    // Check business name and industry (required)
    if (!profile.business_name && !profile.company) {
      missing.push('Business Name');
    } else {
      foundCount++;
    }
    
    if (!profile.industry) {
      missing.push('Industry');
    } else {
      foundCount++;
    }
    
    // Check brand voice (can be tone or brand_voice)
    if (!profile.brand_voice && !profile.tone) {
      missing.push('Brand Voice');
    } else {
      foundCount++;
    }
    
    // Check target audience
    if (!profile.target_audience) {
      missing.push('Target Audience');
    } else {
      foundCount++;
    }
    
    // Check key offer
    if (!profile.key_offer) {
      missing.push('Key Offer');
    } else {
      foundCount++;
    }
    
    // Check writing samples
    const samples = profile.writing_samples || [];
    if (!samples || samples.length === 0) {
      missing.push('Writing Samples');
    } else {
      foundCount++;
    }
    
    // Check brand keywords
    const keywords = profile.brand_keywords || [];
    if (!keywords || keywords.length === 0) {
      missing.push('Brand Keywords');
    } else {
      foundCount++;
    }
    
    // Check goals
    const goals = profile.goals || [];
    if (!goals || goals.length === 0) {
      missing.push('Goals');
    } else {
      foundCount++;
    }
    
    // Calculate total dynamically based on all checks
    const total = foundCount + missing.length;
    const percent = Math.round((foundCount / total) * 100);
    
    return { missing, percent };
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
    
    // Show thinking message with personality
    this.addMessage('assistant', `Let me analyze your profile and create personalized suggestions for **${emoji} ${label}**...`);
    this.showLoading();
    
    try {
      // Fetch current profile for before/after comparison
      const profileResponse = await fetch('/api/profile', { credentials: 'include' });
      const profileData = await profileResponse.json();
      const currentValue = profileData.profile?.[field];
      
      const response = await fetch('/api/profile/suggest', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ field })
      });
      
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
        
        this.addMessage('assistant', message, false, false, buttons);
        
        // Store suggestions for selection as instance property
        this.pendingProfileSuggestions = {
          field: field,
          suggestions: data.suggestions,
          currentValue: currentValue
        };
        
      } else {
        // Fallback with helpful context
        const errorMsg = data.error || "I couldn't generate suggestions right now.";
        this.addMessage('assistant', 
          `${errorMsg}\n\n💡 **${WHY_IT_MATTERS[field]}**\n\nWhat would you like your **${label}** to be?\n\nJust type it below:`
        );
      }
      
    } catch (error) {
      this.hideLoading();
      console.error('Error getting profile suggestions:', error);
      this.addMessage('assistant', 
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
      const beforeCompleteness = beforeData.profile ? 
        this.checkProfileCompleteness(beforeData.profile).percent : 0;
      
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
        const afterCompleteness = afterData.profile ? 
          this.checkProfileCompleteness(afterData.profile).percent : 0;
        
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
  const { missing, percent } = promptBox.checkProfileCompleteness(p);
  
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
    promptBox.addMessage('assistant', `Analyzing ${url}... 🔍`);
    
    try {
      const response = await fetch('/onboarding/social-style', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ url: url.trim(), consent: true })
      });
      
      const data = await response.json();
      
      if (data.suggestions) {
        let message = `## Found your brand! 🎉\n\n`;
        if (data.suggestions.business_name) message += `**Business:** ${data.suggestions.business_name}\n`;
        if (data.suggestions.industry) message += `**Industry:** ${data.suggestions.industry}\n`;
        if (data.suggestions.brand_voice) message += `**Voice:** ${data.suggestions.brand_voice}\n`;
        if (data.suggestions.key_customers) message += `**Audience:** ${data.suggestions.key_customers}\n`;
        
        message += `\nWant me to save this to your profile?`;
        
        const buttons = [
          { label: '✓ Save to profile', action: 'command', value: '/import-confirm' },
          { label: '✏️ Edit first', action: 'prompt', value: '/profile' }
        ];
        
        promptBox.addMessage('assistant', message, false, false, buttons);
        
        // Store for confirmation using instance state
        promptBox.pendingImport = data.suggestions;
      } else {
        promptBox.addMessage('assistant', `Couldn't extract data from that URL. Try a different page, or just tell me about your business!`);
      }
    } catch (error) {
      promptBox.addMessage('assistant', `Error analyzing URL: ${error.message}. Try again or describe your business instead.`);
    }
  } else {
    // No URL - prompt for one
    promptBox.addMessage('assistant', `## Import from URL 🔗\n\nPaste your website or social media URL and I'll extract your brand info:\n\n\`/import https://yourwebsite.com\``);
  }
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
    
    if (data.ok && data.profile) {
      const badgeEl = document.querySelector('.profile-completeness-badge');
      if (badgeEl) {
        // Assuming PromptBox instance is accessible
        const promptBox = window.dashboardPromptBox || new PromptBox('promptbox-container');
        const { percent } = promptBox.checkProfileCompleteness(data.profile);
        
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
