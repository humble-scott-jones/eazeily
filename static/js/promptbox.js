/**
 * PromptBox - Unified conversational UI component
 * Provides Copilot-style interface for onboarding and content creation
 */

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

  getSuggestions() {
    if (this.context === 'onboarding') {
      return [
        "Drop your website URL",
        "Describe your brand in 3 words",
        "What makes your business unique?",
        "Who is your target customer?",
        "Paste an existing social post you love"
      ];
    } else {
      return [
        "/post - Create a social media post",
        "/caption - Generate an image caption",
        "/reel - Script a short video",
        "/email - Draft an email or newsletter",
        "/review - Respond to a customer review",
        "/blog - Write a blog post",
        "/ad - Create social ads copy",
        "/proposal - Generate a business proposal"
      ];
    }
  }

  render() {
    const html = `
      <div class="promptbox">
        <!-- Conversation History -->
        <div class="promptbox__conversation" id="${this.container.id}-conversation">
          <!-- Messages will be appended here -->
        </div>

        <!-- Input Area -->
        <div class="promptbox__input-area">
          <!-- Rotating Suggestions -->
          <div class="promptbox__suggestions" id="${this.container.id}-suggestions">
            <!-- Suggestions will be rendered here -->
          </div>

          <!-- Input Field -->
          <div class="promptbox__input-wrapper">
            <textarea
              id="${this.container.id}-textarea"
              class="promptbox__textarea"
              placeholder="${this.placeholder}"
              rows="1"
            ></textarea>
            <button
              id="${this.container.id}-send"
              class="promptbox__send-btn"
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
        <div class="promptbox__loading hidden" id="${this.container.id}-loading">
          <div class="promptbox__typing">
            <span></span>
            <span></span>
            <span></span>
          </div>
          <span class="promptbox__loading-text">Thinking...</span>
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
        class="promptbox__suggestion ${index === this.suggestionIndex ? 'active' : ''}"
        data-suggestion="${this.escapeHtml(suggestion)}"
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

    // Auto-resize textarea
    textarea.addEventListener('input', () => {
      this.autoResizeTextarea(textarea);
      this.updateSendButton(textarea, sendBtn);
      this.highlightSlashCommands(textarea);
    });

    // Send on Enter (Shift+Enter for new line)
    textarea.addEventListener('keydown', (e) => {
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
      const suggestionBtn = e.target.closest('.promptbox__suggestion');
      if (suggestionBtn) {
        const suggestion = suggestionBtn.dataset.suggestion;
        this.fillSuggestion(suggestion);
      }
    });
  }

  autoResizeTextarea(textarea) {
    textarea.style.height = 'auto';
    const maxHeight = 150; // Max height in pixels
    const newHeight = Math.min(textarea.scrollHeight, maxHeight);
    textarea.style.height = `${newHeight}px`;
  }

  updateSendButton(textarea, sendBtn) {
    const hasContent = textarea.value.trim().length > 0;
    sendBtn.disabled = !hasContent;
  }

  highlightSlashCommands(textarea) {
    const value = textarea.value;
    // Check if the message starts with a slash command
    if (value.match(/^\/\w+/)) {
      textarea.classList.add('has-slash-command');
    } else {
      textarea.classList.remove('has-slash-command');
    }
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
    
    if (data.status === 'success') {
      this.addMessage('assistant', data.message);
      
      // Update pending task if provided
      if (data.pending_task) {
        this.pendingTask = data.pending_task;
      }

      // Handle redirect if provided
      if (data.redirect) {
        setTimeout(() => {
          window.location.href = data.redirect;
        }, 1000);
      }
    } else {
      throw new Error(data.error || 'Unknown error');
    }
  }

  addMessage(role, content, isError = false) {
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
    messageDiv.className = `promptbox__message promptbox__message--${role}`;
    if (isError) messageDiv.classList.add('promptbox__message--error');

    const bubbleDiv = document.createElement('div');
    bubbleDiv.className = 'promptbox__bubble';

    // For assistant messages, render markdown
    if (role === 'assistant') {
      bubbleDiv.innerHTML = this.renderMarkdown(content);
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
      conversation.scrollTop = conversation.scrollHeight;
    }
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
