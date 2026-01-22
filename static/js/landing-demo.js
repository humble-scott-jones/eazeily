// Eazeily Landing Page - Interactive Demo & UI Logic

// Mobile menu toggle
document.getElementById('mobile-menu-toggle')?.addEventListener('click', () => {
  const menu = document.getElementById('mobile-menu');
  menu.classList.toggle('hidden');
});

// Close mobile menu when clicking a link
document.querySelectorAll('#mobile-menu a').forEach(link => {
  link.addEventListener('click', () => {
    document.getElementById('mobile-menu').classList.add('hidden');
  });
});

// Mobile sticky CTA - Show on scroll
let lastScroll = 0;
const stickyCTA = document.getElementById('mobile-sticky-cta');

window.addEventListener('scroll', () => {
  const currentScroll = window.pageYOffset;
  
  // Show CTA after scrolling down 300px
  if (currentScroll > 300) {
    document.body.classList.add('scrolled');
    stickyCTA?.classList.remove('hidden');
  } else {
    document.body.classList.remove('scrolled');
    stickyCTA?.classList.add('hidden');
  }
  
  lastScroll = currentScroll;
});

// Exit intent popup
let exitIntentShown = false;

document.addEventListener('mouseleave', (e) => {
  if (e.clientY <= 0 && !exitIntentShown && window.innerWidth >= 768) {
    showExitPopup();
  }
});

// Also trigger on mobile back button (less aggressive)
let touchStartY = 0;
document.addEventListener('touchstart', (e) => {
  touchStartY = e.touches[0].clientY;
});

document.addEventListener('touchmove', (e) => {
  const touchY = e.touches[0].clientY;
  // If user is at top of page and swiping up (potential back gesture)
  if (window.scrollY === 0 && touchY > touchStartY + 50 && !exitIntentShown) {
    // Don't show on mobile as it's too aggressive
    // showExitPopup();
  }
});

function showExitPopup() {
  const popup = document.getElementById('exit-popup');
  popup.classList.remove('hidden');
  popup.classList.add('show');
  exitIntentShown = true;
  
  // Store in session so we don't show again
  sessionStorage.setItem('exitPopupShown', 'true');
}

// Check if popup was already shown this session
if (sessionStorage.getItem('exitPopupShown')) {
  exitIntentShown = true;
}

// Close exit popup
document.getElementById('exit-popup-close')?.addEventListener('click', () => {
  document.getElementById('exit-popup').classList.add('hidden');
  document.getElementById('exit-popup').classList.remove('show');
});

// Close popup when clicking demo button
document.getElementById('exit-popup-demo-btn')?.addEventListener('click', () => {
  document.getElementById('exit-popup').classList.add('hidden');
  document.getElementById('exit-popup').classList.remove('show');
});

// Close popup when clicking outside
document.getElementById('exit-popup')?.addEventListener('click', (e) => {
  if (e.target.id === 'exit-popup') {
    e.target.classList.add('hidden');
    e.target.classList.remove('show');
  }
});

// Interactive Demo Logic
const demoInput = document.getElementById('demo-input');
const demoSendBtn = document.getElementById('demo-send-btn');
const demoMessages = document.getElementById('demo-messages');

// Example buttons
document.querySelectorAll('.demo-example-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    const prompt = btn.getAttribute('data-prompt');
    demoInput.value = prompt;
    sendDemoMessage();
  });
});

// Send button click
demoSendBtn?.addEventListener('click', sendDemoMessage);

// Enter key in input
demoInput?.addEventListener('keypress', (e) => {
  if (e.key === 'Enter') {
    sendDemoMessage();
  }
});

// Track demo usage
let demoUsageCount = 0;

async function sendDemoMessage() {
  const message = demoInput.value.trim();
  
  if (!message) return;
  
  // Clear input
  demoInput.value = '';
  
  // Add user message
  addMessage(message, 'user');
  
  // Show loading indicator
  addLoadingMessage();
  
  // Disable input while processing
  demoInput.disabled = true;
  demoSendBtn.disabled = true;
  demoSendBtn.classList.add('loading');
  
  // Increment usage count
  demoUsageCount++;
  
  // Track demo usage on first use
  if (typeof gtag !== 'undefined' && demoUsageCount === 1) {
    gtag('event', 'demo_used', {
      'event_category': 'engagement',
      'value': 1
    });
  }
  
  try {
    // Call demo API
    const response = await fetch('/api/demo/generate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: message }),
    });
    
    if (!response.ok) {
      throw new Error('Failed to generate content');
    }
    
    const data = await response.json();
    
    // Remove loading indicator
    removeLoadingMessage();
    
    // Add AI response
    if (data.error) {
      addMessage(data.error, 'ai');
    } else {
      addMessage(data.content, 'ai');
    }
    
    // Show signup prompt after 2 demo messages
    if (demoUsageCount === 2) {
      setTimeout(() => {
        const signupPrompt = document.createElement('div');
        signupPrompt.className = 'flex justify-center mt-4';
        signupPrompt.innerHTML = `
          <a href="/auth/signup" class="bg-white text-purple-900 px-6 py-2 rounded-lg hover:shadow-lg transition font-semibold text-sm">
            Love it? Sign up to create real content (Free) →
          </a>
        `;
        const container = demoMessages.parentElement;
        if (container && !document.querySelector('.signup-prompt-added')) {
          signupPrompt.classList.add('signup-prompt-added');
          container.insertBefore(signupPrompt, demoMessages.nextSibling);
        }
      }, 1000);
    }
    
  } catch (error) {
    console.error('Demo error:', error);
    removeLoadingMessage();
    addMessage('Oops! Something went wrong. Please try again.', 'ai');
  } finally {
    // Re-enable input
    demoInput.disabled = false;
    demoSendBtn.disabled = false;
    demoSendBtn.classList.remove('loading');
    demoInput.focus();
  }
}

function addMessage(content, sender) {
  const messageDiv = document.createElement('div');
  messageDiv.className = sender === 'user' ? 'flex justify-end message-user' : 'flex justify-start message-ai';
  
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = sender === 'user' 
    ? 'bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-2xl rounded-tr-sm max-w-md'
    : 'bg-white/20 backdrop-blur-sm text-white px-6 py-3 rounded-2xl rounded-tl-sm max-w-md whitespace-pre-wrap';
  
  bubbleDiv.textContent = content;
  
  messageDiv.appendChild(bubbleDiv);
  demoMessages.appendChild(messageDiv);
  
  // Scroll to bottom
  demoMessages.scrollTop = demoMessages.scrollHeight;
}

function addLoadingMessage() {
  const messageDiv = document.createElement('div');
  messageDiv.className = 'flex justify-start message-ai';
  messageDiv.id = 'loading-message';
  
  const bubbleDiv = document.createElement('div');
  bubbleDiv.className = 'bg-white/20 backdrop-blur-sm text-white px-6 py-3 rounded-2xl rounded-tl-sm';
  bubbleDiv.innerHTML = `
    <div class="flex gap-1">
      <span class="demo-loading"></span>
      <span class="demo-loading"></span>
      <span class="demo-loading"></span>
    </div>
  `;
  
  messageDiv.appendChild(bubbleDiv);
  demoMessages.appendChild(messageDiv);
  
  // Scroll to bottom
  demoMessages.scrollTop = demoMessages.scrollHeight;
}

function removeLoadingMessage() {
  const loadingMsg = document.getElementById('loading-message');
  if (loadingMsg) {
    loadingMsg.remove();
  }
}

// Smooth scroll for anchor links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
  anchor.addEventListener('click', function (e) {
    const href = this.getAttribute('href');
    
    // Skip if it's just "#"
    if (href === '#') return;
    
    e.preventDefault();
    
    const target = document.querySelector(href);
    if (target) {
      const offset = 80; // Account for fixed header
      const targetPosition = target.offsetTop - offset;
      
      window.scrollTo({
        top: targetPosition,
        behavior: 'smooth'
      });
    }
  });
});

// Add analytics tracking for CTA clicks (optional - integrate with your analytics)
document.querySelectorAll('a[href*="signup"], a[href*="dashboard"]').forEach(link => {
  link.addEventListener('click', () => {
    // Track CTA clicks
    if (typeof gtag !== 'undefined') {
      gtag('event', 'cta_click', {
        'event_category': 'engagement',
        'event_label': link.textContent.trim(),
        'value': 1
      });
    }
  });
});

// Lazy load images (if any are added later)
if ('IntersectionObserver' in window) {
  const imageObserver = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target;
        img.src = img.dataset.src;
        img.classList.remove('lazy');
        observer.unobserve(img);
      }
    });
  });

  document.querySelectorAll('img.lazy').forEach(img => {
    imageObserver.observe(img);
  });
}

console.log('🚀 Eazeily Landing Page Loaded');
