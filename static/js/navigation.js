/**
 * Navigation and Menu Management
 * Handles slide-out menu, action buttons, and profile navigation
 */

// Initialize menu toggle on page load
document.addEventListener('DOMContentLoaded', function() {
    const menuToggle = document.getElementById('menu-toggle');
    if (menuToggle) {
        menuToggle.addEventListener('click', openMenu);
    }
});

/**
 * Open slide-out navigation menu
 */
function openMenu() {
    const navMenu = document.getElementById('nav-menu');
    const navOverlay = document.getElementById('nav-overlay');
    
    if (navMenu) navMenu.classList.add('open');
    if (navOverlay) {
        navOverlay.classList.remove('hidden');
        setTimeout(() => {
            navOverlay.classList.add('visible');
        }, 10);
    }
    
    // Prevent body scroll when menu is open
    document.body.style.overflow = 'hidden';
}

/**
 * Close slide-out navigation menu
 */
function closeMenu() {
    const navMenu = document.getElementById('nav-menu');
    const navOverlay = document.getElementById('nav-overlay');
    
    if (navMenu) navMenu.classList.remove('open');
    if (navOverlay) {
        navOverlay.classList.remove('visible');
        setTimeout(() => {
            navOverlay.classList.add('hidden');
        }, 300);
    }
    
    // Restore body scroll
    document.body.style.overflow = '';
}

/**
 * Handle menu item actions
 * @param {string} action - Action to perform (profile, saved, help, etc.)
 */
function menuAction(action) {
    closeMenu();
    
    switch (action) {
        case 'profile':
            // Fill chat input with /profile command
            const input = document.getElementById('chat-input');
            if (input) {
                input.value = '/profile';
                input.focus();
                input.dispatchEvent(new Event('input', { bubbles: true }));
                
                // Auto-resize textarea if it has that capability
                if (typeof autoResizeTextarea === 'function') {
                    autoResizeTextarea(input);
                }
                
                // Enable send button
                const sendBtn = document.getElementById('send-btn');
                if (sendBtn) {
                    sendBtn.disabled = false;
                }
            }
            break;
            
        case 'calendar':
            showContentCalendarModal();
            break;
            
        case 'help':
            const helpInput = document.getElementById('chat-input');
            if (helpInput) {
                helpInput.value = '/help';
                helpInput.focus();
                
                // Enable send button
                const helpSendBtn = document.getElementById('send-btn');
                if (helpSendBtn) {
                    helpSendBtn.disabled = false;
                }
            }
            break;
    }
}

/**
 * Handle action buttons (regenerate, shorter, casual, different)
 * @param {string} action - Action type
 */
function handleAction(action) {
    const input = document.getElementById('chat-input');
    if (!input) return;
    
    const prompts = {
        'regenerate': 'regenerate that',
        'shorter': 'make it shorter',
        'casual': 'make it more casual',
        'different': 'try a different angle'
    };
    
    input.value = prompts[action] || action;
    input.focus();
    
    // Auto-resize if function exists
    if (typeof autoResizeTextarea === 'function') {
        autoResizeTextarea(input);
    }
    
    // Enable and auto-submit
    const sendBtn = document.getElementById('send-btn');
    if (sendBtn) {
        sendBtn.disabled = false;
        // Auto-submit after a brief delay
        setTimeout(() => {
            sendBtn.click();
        }, 100);
    }
}

/**
 * Handle profile badge click
 * Opens profile view in chat
 */
function handleProfileBadgeClick() {
    menuAction('profile');
}

/**
 * Show toast notification
 * @param {string} message - Message to display
 * @param {string} type - Type of toast (success, error)
 */
function showToast(message, type = 'success') {
    // Remove existing toast if any
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();
    
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.textContent = message;
    
    document.body.appendChild(toast);
    
    // Auto-remove after 2 seconds
    setTimeout(() => {
        toast.style.animation = 'toastOut 0.3s ease forwards';
        setTimeout(() => toast.remove(), 300);
    }, 2000);
}

/**
 * Copy individual option content
 * @param {number} index - Index of the option to copy
 */
async function copyOption(index) {
    // Defensive check for state
    if (!window.lastGeneratedOptions) {
        console.warn('No generated options available to copy');
        showToast('No content to copy', 'error');
        return;
    }
    
    const options = window.lastGeneratedOptions;
    if (!options[index]) {
        console.warn(`Option ${index} not found`);
        showToast('Option not found', 'error');
        return;
    }
    
    const text = options[index].text || options[index];
    
    try {
        await navigator.clipboard.writeText(text);
        
        // Haptic feedback (if supported)
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        // Visual feedback on button
        const btn = document.querySelector(`.copy-btn[data-index="${index}"]`);
        if (btn) {
            btn.classList.add('copied');
            btn.querySelector('.copy-text').textContent = 'Copied!';
            btn.querySelector('.copy-icon').textContent = '✓';
            
            setTimeout(() => {
                btn.classList.remove('copied');
                btn.querySelector('.copy-text').textContent = 'Copy';
                btn.querySelector('.copy-icon').textContent = '📋';
            }, 2000);
        }
        
        showToast('Copied to clipboard! ✓');
    } catch (err) {
        console.error('Copy failed:', err);
        showToast('Failed to copy', 'error');
    }
}

/**
 * Copy single content (when there are no options)
 */
async function copySingleContent() {
    // Defensive check for state
    if (!window.lastGeneratedContent) {
        console.warn('No generated content available to copy');
        showToast('No content to copy', 'error');
        return;
    }
    
    const content = window.lastGeneratedContent;
    
    try {
        await navigator.clipboard.writeText(content);
        
        // Haptic feedback
        if (navigator.vibrate) {
            navigator.vibrate(50);
        }
        
        showToast('Copied to clipboard! ✓');
    } catch (err) {
        console.error('Copy failed:', err);
        showToast('Failed to copy', 'error');
    }
}

/**
 * Auto-resize textarea based on content
 * @param {HTMLTextAreaElement} textarea - Textarea element
 */
function autoResizeTextarea(textarea) {
    if (!textarea) return;
    
    textarea.style.height = 'auto';
    const minHeight = 44;
    const maxHeight = 120;
    const newHeight = Math.max(minHeight, Math.min(textarea.scrollHeight, maxHeight));
    textarea.style.height = `${newHeight}px`;
}

/**
 * Show Content Calendar modal (premium feature placeholder)
 */
function showContentCalendarModal() {
    // Remove existing modal if any
    const existing = document.getElementById('calendar-modal');
    if (existing) existing.remove();
    
    const modal = document.createElement('div');
    modal.id = 'calendar-modal';
    modal.className = 'modal-overlay';
    modal.innerHTML = `
        <div class="modal-content calendar-modal">
            <button class="modal-close" onclick="closeCalendarModal()">&times;</button>
            <div class="calendar-header">
                <span class="calendar-icon">📅</span>
                <h2>Content Calendar</h2>
                <span class="pro-badge">PRO</span>
            </div>
            <p class="calendar-description">
                Plan your content ahead of time! Save generated posts to specific dates 
                and visualize your content schedule at a glance.
            </p>
            <div class="calendar-features">
                <div class="feature-item">
                    <span class="feature-icon">⏰</span>
                    <span>Schedule posts for specific dates & times</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">📊</span>
                    <span>See gaps in your content schedule</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🔄</span>
                    <span>Drag & drop to reschedule</span>
                </div>
                <div class="feature-item">
                    <span class="feature-icon">🔔</span>
                    <span>Get reminders before scheduled posts</span>
                </div>
            </div>
            <div class="calendar-cta">
                <p class="coming-soon">Coming Soon!</p>
                <button class="btn-notify" onclick="notifyCalendarInterest()">
                    🔔 Notify me when it's ready
                </button>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    // Close on overlay click
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeCalendarModal();
    });
    
    // Close on escape key
    document.addEventListener('keydown', function escHandler(e) {
        if (e.key === 'Escape') {
            closeCalendarModal();
            document.removeEventListener('keydown', escHandler);
        }
    });
}

/**
 * Close Content Calendar modal
 */
function closeCalendarModal() {
    const modal = document.getElementById('calendar-modal');
    if (modal) modal.remove();
}

/**
 * Track interest in Content Calendar feature
 */
function notifyCalendarInterest() {
    // Could send to analytics or save preference
    showToast('Thanks! We\'ll notify you when Content Calendar launches. 🎉');
    closeCalendarModal();
}

// Export functions to window for inline onclick handlers
if (typeof window !== 'undefined') {
    window.openMenu = openMenu;
    window.closeMenu = closeMenu;
    window.menuAction = menuAction;
    window.handleAction = handleAction;
    window.handleProfileBadgeClick = handleProfileBadgeClick;
    window.showToast = showToast;
    window.copyOption = copyOption;
    window.copySingleContent = copySingleContent;
    window.autoResizeTextarea = autoResizeTextarea;
    window.showContentCalendarModal = showContentCalendarModal;
    window.closeCalendarModal = closeCalendarModal;
    window.notifyCalendarInterest = notifyCalendarInterest;
}
