/**
 * PromptBox - Unified conversational UI component
 * Provides Copilot-style interface for onboarding and content creation
 */

// Slash command definitions
const SLASH_COMMANDS = [
  { command: '/post', description: 'Create a social media post', icon: '📝' },
  { command: '/caption', description: 'Write an image caption', icon: '📸' },
  { command: '/script', description: 'Write a video script', icon: '🎬' },
  { command: '/reel', description: 'Create a reel/short video script', icon: '🎥' },
  { command: '/email', description: 'Draft an email', icon: '✉️' },
  { command: '/review', description: 'Respond to a review', icon: '⭐' },
  { command: '/ad', description: 'Create ad copy', icon: '📢' },
  { command: '/blog', description: 'Write a blog post', icon: '📰' },
  { command: '/profile', description: 'View or edit your brand profile', icon: '👤' },
  { command: '/update', description: 'Update a profile field', icon: '✏️' },
  { command: '/voice', description: 'Change your brand voice', icon: '🎤' },
  { command: '/audience', description: 'Update your target audience', icon: '🎯' },
];

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
    
    // State
    this.conversationHistory = [];
    this.pendingTask = null;
    this.isLoading = false;
    this.suggestionIndex = 0;
    this.suggestionTimer = null;
    this.lastAction = null; // Track last action for contextual suggestions
    this.selectedAutocompleteIndex = -1; // Track selected autocomplete item
    this.lastGeneratedContent = null; // Track last generated content for copy

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
        'Update brand voice',
        'Update target audience',
        'Update key offer',
        'Create content',
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

  addMessage(role, content, isError = false, isGenerated = false) {
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
    conversation.appendChild(messageDiv);

    // Auto-scroll to latest message
    this.scrollToBottom();
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
}
