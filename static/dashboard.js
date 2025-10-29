// Dashboard functionality for generating content and managing responses

document.addEventListener('DOMContentLoaded', () => {
  // Load user profile and settings
  loadUserProfile();

  // Review Response Generation
  setupReviewResponse();

  // Content Generation
  setupContentGeneration();

  // Account Settings
  setupAccountSettings();

  // Quick Actions
  setupQuickActions();
});

async function loadUserProfile() {
  try {
    const response = await fetch('/api/profile', { credentials: 'include' });
    if (response.ok) {
      const profile = await response.json();
      // Populate account settings with current profile data
      if (profile.company) {
        document.getElementById('account-company').value = profile.company;
      }
      if (profile.industry) {
        document.getElementById('account-industry').value = profile.industry;
      }
      if (profile.tone) {
        document.getElementById('account-tone').value = profile.tone;
      }
      if (profile.platforms && Array.isArray(profile.platforms)) {
        // Uncheck all platforms first
        document.querySelectorAll('input[id^="platform-"]').forEach(cb => cb.checked = false);
        // Check selected platforms
        profile.platforms.forEach(platform => {
          const checkbox = document.getElementById(`platform-${platform}`);
          if (checkbox) checkbox.checked = true;
        });
      }
    }
  } catch (error) {
    console.error('Failed to load user profile:', error);
  }
}

function setupReviewResponse() {
  const generateBtn = document.getElementById('generate-response');
  const loadingDiv = document.getElementById('response-loading');
  const resultDiv = document.getElementById('response-result');
  const responseText = document.getElementById('response-text');
  const responseMethod = document.getElementById('response-method');
  const copyBtn = document.getElementById('copy-response');

  generateBtn?.addEventListener('click', async () => {
    const review = document.getElementById('review-text').value.trim();
    const tone = document.getElementById('response-tone').value;
    const company = document.getElementById('company-name').value.trim();

    if (!review) {
      showToast('Please paste a customer review first');
      return;
    }

    // Show loading state
    generateBtn.classList.add('hidden');
    loadingDiv.classList.remove('hidden');
    resultDiv.classList.add('hidden');

    try {
      const response = await generateReviewResponse(review, tone, company);

      responseText.textContent = response.text;
      responseMethod.textContent = response.method === 'ai' ? 'AI Enhanced' : 'Smart Template';
      responseMethod.className = `px-2 py-1 text-xs rounded-full ${
        response.method === 'ai'
          ? 'bg-purple-100 text-purple-800'
          : 'bg-green-100 text-green-800'
      }`;
      resultDiv.classList.remove('hidden');
      showToast('Response generated successfully!');

    } catch (error) {
      console.error('Response generation failed:', error);
      showToast('Failed to generate response. Please try again.');
    } finally {
      generateBtn.classList.remove('hidden');
      loadingDiv.classList.add('hidden');
    }
  });

  // Copy response to clipboard
  copyBtn?.addEventListener('click', async () => {
    const text = responseText.textContent;
    try {
      await navigator.clipboard.writeText(text);
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = '<svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" /></svg> Copied!';
      setTimeout(() => {
        copyBtn.innerHTML = originalText;
      }, 2000);
    } catch (err) {
      showToast('Failed to copy to clipboard');
    }
  });
}

function setupContentGeneration() {
  const generateBtn = document.getElementById('generate-content');
  const loadingDiv = document.getElementById('content-loading');
  const resultsDiv = document.getElementById('generated-content');
  const contentResults = document.getElementById('content-results');
  const platformSelect = document.getElementById('gen-platform');
  const reelOptions = document.getElementById('reel-options');

  // Show/hide reel options based on platform selection
  platformSelect?.addEventListener('change', () => {
    const platform = platformSelect.value;
    const isVideoPlatform = ['instagram', 'tiktok'].includes(platform.toLowerCase());
    if (isVideoPlatform) {
      reelOptions.classList.remove('hidden');
    } else {
      reelOptions.classList.add('hidden');
    }
  });

  generateBtn?.addEventListener('click', async () => {
    const days = parseInt(document.getElementById('gen-days').value);
    const platform = document.getElementById('gen-platform').value;
    const tone = document.getElementById('gen-tone').value;

    // Get reel options if visible
    let details = {};
    if (!reelOptions.classList.contains('hidden')) {
      details = {
        reel_style: document.getElementById('reel-style').value,
        reel_length: parseInt(document.getElementById('reel-length').value),
        production_tier: document.getElementById('production-tier').value
      };
    }

    // Show loading state
    generateBtn.classList.add('hidden');
    loadingDiv.classList.remove('hidden');

    try {
      const data = await generate(days, {
        platforms: [platform],
        tone: tone,
        details: details
      });

      // Display results
      contentResults.innerHTML = '';
      renderPosts(data);
      resultsDiv.classList.remove('hidden');

      // Scroll to results
      resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });

    } catch (error) {
      console.error('Content generation failed:', error);
      showToast('Failed to generate content. Please try again.');
    } finally {
      generateBtn.classList.remove('hidden');
      loadingDiv.classList.add('hidden');
    }
  });
}

function setupAccountSettings() {
  const saveBtn = document.getElementById('save-settings');

  saveBtn?.addEventListener('click', async () => {
    const company = document.getElementById('account-company').value.trim();
    const industry = document.getElementById('account-industry').value;
    const tone = document.getElementById('account-tone').value;

    // Get selected platforms
    const platforms = [];
    document.querySelectorAll('input[id^="platform-"]:checked').forEach(cb => {
      platforms.push(cb.id.replace('platform-', ''));
    });

    if (platforms.length === 0) {
      platforms.push('instagram'); // Default to Instagram
    }

    // Update answers object
    answers.company = company;
    answers.industry = industry;
    answers.tone = tone;
    answers.platforms = platforms;

    try {
      await saveProfile();
      showToast('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      showToast('Failed to save settings. Please try again.');
    }
  });
}

function setupQuickActions() {
  const quickSample = document.getElementById('quick-sample');
  const quick7Day = document.getElementById('quick-7day');
  const quick30Day = document.getElementById('quick-30day');

  quickSample?.addEventListener('click', async () => {
    try {
      const data = await generate(1);
      document.getElementById('generated-content').classList.remove('hidden');
      renderPosts(data);
      document.getElementById('generated-content').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      console.error('Quick sample generation failed:', error);
      showToast('Failed to generate sample. Please try again.');
    }
  });

  quick7Day?.addEventListener('click', async () => {
    try {
      const data = await generate(7);
      document.getElementById('generated-content').classList.remove('hidden');
      renderPosts(data);
      document.getElementById('generated-content').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      console.error('7-day generation failed:', error);
      showToast('Failed to generate 7-day plan. Please try again.');
    }
  });

  quick30Day?.addEventListener('click', async () => {
    try {
      const data = await generate(30);
      document.getElementById('generated-content').classList.remove('hidden');
      renderPosts(data);
      document.getElementById('generated-content').scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      console.error('30-day generation failed:', error);
      showToast('Failed to generate 30-day plan. Please try again.');
    }
  });
}

// Generate review response using the API
async function generateReviewResponse(reviewText, tone, companyName = '') {
  try {
    const response = await fetch('/api/generate-review-response', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        review_text: reviewText,
        tone: tone,
        company_name: companyName
      })
    });

    if (!response.ok) {
      throw new Error('Failed to generate response');
    }

    const data = await response.json();
    return {
      text: data.response,
      method: data.method || 'template'
    };
  } catch (error) {
    console.error('API call failed, falling back to template:', error);
    // Fallback to client-side template
    return {
      text: generateReviewResponseTemplate(reviewText, tone, companyName),
      method: 'template'
    };
  }
}

// Helper function to show toast messages
function showToast(message) {
  const toast = document.createElement('div');
  toast.className = 'fixed bottom-6 right-6 bg-slate-800 text-white px-4 py-2 rounded shadow z-50';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.classList.add('opacity-0'), 2200);
  setTimeout(() => toast.remove(), 2800);
}

// Render generated posts with enhanced features
function renderPosts(data) {
  const posts = data.posts || [];
  const resultsDiv = document.getElementById('content-results');
  resultsDiv.innerHTML = '';

  if (!posts.length) {
    resultsDiv.innerHTML = `<div class="text-sm text-slate-600">No posts yet.</div>`;
    return;
  }

  // Group posts by day
  const byDay = posts.reduce((acc, post) => {
    (acc[post.day_index] ||= []).push(post);
    return acc;
  }, {});

  for (const day of Object.keys(byDay).sort((a, b) => +a - +b)) {
    const dayPosts = byDay[day];
    const section = document.createElement('section');
    section.className = 'post mb-8';

    // Day header with pillar info
    const firstPost = dayPosts[0];
    section.innerHTML = `
      <div class="flex items-baseline justify-between mb-4">
        <div class="flex items-center gap-3">
          <h4 class="font-medium text-lg">Day ${day} • ${firstPost.date}</h4>
          <span class="px-2 py-1 bg-purple-100 text-purple-800 text-xs rounded-full font-medium">
            ${firstPost.pillar}
          </span>
        </div>
        <span class="text-xs text-slate-500">${dayPosts.length} platform(s)</span>
      </div>
    `;

    // Render each post for this day
    dayPosts.forEach(post => section.appendChild(renderPostCard(post)));

    resultsDiv.appendChild(section);
  }
}

// Render individual post card with enhanced features
function renderPostCard(post) {
  const card = document.createElement('div');
  card.className = 'border rounded-lg p-4 mt-3 bg-white';

  // Platform-specific styling
  const platformColors = {
    instagram: 'from-pink-500 to-purple-500',
    facebook: 'from-blue-600 to-blue-800',
    linkedin: 'from-blue-700 to-blue-900',
    twitter: 'from-sky-500 to-sky-600',
    tiktok: 'from-black to-gray-800'
  };

  const platformColor = platformColors[post.platform.toLowerCase()] || 'from-gray-500 to-gray-600';

  // Check if this post has variants (multiple platforms)
  const hasVariants = post.variants && Object.keys(post.variants).length > 1;

  card.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-gradient-to-r ${platformColor} rounded-full flex items-center justify-center">
          <span class="text-white text-xs font-bold">${post.platform.charAt(0).toUpperCase()}</span>
        </div>
        <span class="font-medium capitalize text-slate-900">${post.platform}</span>
        ${hasVariants ? '<span class="text-xs text-purple-600 font-medium">• Multi-platform</span>' : ''}
      </div>
      <div class="flex gap-2">
        <button class="btn-ghost text-xs" data-copy="${escapeAttr(post.caption)}">Copy</button>
        <button class="btn-ghost text-xs" data-like="1" data-day="${post.day_index}" data-platform="${post.platform}">👍</button>
        <button class="btn-ghost text-xs" data-like="-1" data-day="${post.day_index}" data-platform="${post.platform}">👎</button>
      </div>
    </div>

    ${post.image_url ? `<img class="w-full h-32 object-cover rounded mb-3" src="${post.image_url}" alt="Suggested image" />` : ''}

    <div class="text-xs text-slate-500 mb-2"><strong>Image prompt:</strong> ${escapeHtml(post.image_prompt)}</div>

    <pre class="caption text-sm mb-3 whitespace-pre-wrap">${escapeHtml(post.caption)}</pre>

    ${post.reel ? renderReelSection(post.reel) : ''}

    ${hasVariants ? renderPlatformVariants(post.variants, post.platform) : ''}
  `;

  // Add event listeners
  card.querySelector('[data-copy]')?.addEventListener('click', async (ev) => {
    const text = ev.currentTarget.getAttribute('data-copy') || '';
    try {
      await navigator.clipboard.writeText(text);
      ev.currentTarget.textContent = 'Copied!';
      setTimeout(() => (ev.currentTarget.textContent = 'Copy'), 1200);
    } catch (err) {
      showToast('Failed to copy to clipboard');
    }
  });

  card.querySelectorAll('[data-like]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const rating = +btn.getAttribute('data-like');
      const post_day = +btn.getAttribute('data-day');
      const platform = btn.getAttribute('data-platform');
      await submitFeedback(rating, post_day, platform);
      if (btn) {
        btn.textContent = rating > 0 ? '👍 Thanks' : '👎 Noted';
        btn.disabled = true;
      }
    });
  });

  return card;
}

// Render reel section for video content
function renderReelSection(reel) {
  if (!reel) return '';

  return `
    <div class="mt-3 p-3 bg-slate-50 rounded border-l-4 border-purple-400">
      <div class="flex items-center gap-2 mb-2">
        <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
        </svg>
        <span class="text-sm font-medium text-purple-900">Reel Plan</span>
        <span class="text-xs text-purple-600">(${reel.length_seconds}s • ${reel.style})</span>
      </div>

      <div class="text-sm mb-2"><strong>Hook:</strong> ${escapeHtml(reel.hook || '')}</div>

      <div class="text-sm mb-2"><strong>Script:</strong>
        <ol class="list-decimal ml-5 text-xs text-slate-700">
          ${(reel.script_beats || []).map(beat => `<li>${escapeHtml(beat)}</li>`).join('')}
        </ol>
      </div>

      <div class="flex gap-2 mt-2">
        <button class="btn-ghost text-xs" data-copy-reel-script>Copy Script</button>
        <button class="btn-ghost text-xs" data-copy-srt>Copy SRT</button>
        <button class="btn-ghost text-xs" data-copy-thumb>Copy Thumbnail</button>
      </div>
    </div>
  `;
}

// Render platform variants when multiple platforms are selected
function renderPlatformVariants(variants, currentPlatform) {
  if (!variants) return '';

  const otherPlatforms = Object.keys(variants).filter(p => p !== currentPlatform);
  if (otherPlatforms.length === 0) return '';

  return `
    <div class="mt-3 p-3 bg-blue-50 rounded border-l-4 border-blue-400">
      <div class="text-sm font-medium text-blue-900 mb-2">Platform Variants:</div>
      <div class="space-y-2">
        ${otherPlatforms.map(platform => `
          <div class="flex items-start gap-2">
            <span class="text-xs font-medium text-blue-700 capitalize min-w-[60px]">${platform}:</span>
            <pre class="text-xs text-blue-800 whitespace-pre-wrap flex-1">${escapeHtml(variants[platform])}</pre>
            <button class="btn-ghost text-xs" data-copy-variant="${escapeAttr(variants[platform])}">Copy</button>
          </div>
        `).join('')}
      </div>
    </div>
  `;
}

// Submit feedback for a post
async function submitFeedback(rating, postDay, platform) {
  try {
    await fetch('/api/feedback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ rating, post_day: postDay, platform })
    });
  } catch (error) {
    console.error('Failed to submit feedback:', error);
  }
}

// Utility functions
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function escapeAttr(text) {
  return (text || '').replace(/"/g, '&quot;');
}