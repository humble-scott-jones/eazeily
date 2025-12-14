// Dashboard functionality for generating content and managing responses
const DASHBOARD_SEED_STORAGE_KEY = (typeof window !== 'undefined' && window.SEED_STORAGE_KEY) ? window.SEED_STORAGE_KEY : '__swelly_seed_posts';
const DASHBOARD_PLAN_CACHE_KEY = 'swelly_dashboard_plan_cache';
const DASHBOARD_PLAN_TTL_MS = 1000 * 60 * 60 * 72; // 72 hours
const PROFILE_CACHE_KEY = 'swelly_profile_cache';
const PROFILE_CACHE_TTL_MS = 1000 * 60 * 60 * 24; // 24 hours
const imageAttachmentState = { dataUrl: null, fileName: '' };
let generatorUI = {};
let dashboardConfigCache = null;
let dashboardConfigPromise = null;
let accountFormReadyPromise = null;
let lastPlanLength = 1;
const GENERATED_VIEW_PREFS_KEY = 'swelly_generated_view';
const generatedViewPrefs = {
  collapsedDays: new Set(),
  hiddenPlatforms: new Set(),
  loaded: false
};
const PROFILE_FETCH_TIMEOUT_MS = 9000;
// Profile load state tracks the status of fetching user profile
// status: 'idle' | 'loaded' | 'loaded_from_cache' | 'error'
// profileStatus: 'missing' | 'partial' | 'ready' | 'acknowledged' (from backend or user dismissal)
const profileLoadState = { 
  status: 'idle', 
  error: null, 
  requestId: null, 
  profileStatus: null,
  reason: null,
  recommendedAction: null
};
const ACTIVITY_TYPE_META = {
  generated: { label: 'Generated', icon: '✨', color: 'emerald' },
  edited: { label: 'Edited', icon: '✏️', color: 'blue' },
  commented: { label: 'Commented', icon: '💬', color: 'purple' },
  approved: { label: 'Approved', icon: '✅', color: 'emerald' },
  scheduled: { label: 'Scheduled', icon: '📅', color: 'amber' }
};
const activityEvents = [
  {
    id: 'act-1',
    type: 'generated',
    title: '3-day draft generated',
    summary: 'IG + TikTok plan using “evergreen nurture” voice.',
    campaign: 'Evergreen nurture',
    assignee: 'Mia Nguyen',
    actor: { name: 'Mia Nguyen', role: 'Strategist' },
    time: '2m ago',
    status: 'draft',
    needsInputFrom: 'Tyler (client)',
    platforms: ['instagram', 'short_video']
  },
  {
    id: 'act-2',
    type: 'edited',
    title: 'Caption tightened for LinkedIn',
    summary: 'Removed extra hashtags and added CTA for newsletter.',
    campaign: 'Evergreen nurture',
    assignee: 'Priya Shah',
    actor: { name: 'Priya Shah', role: 'Editor' },
    time: '8m ago',
    status: 'in_progress',
    platforms: ['linkedin']
  },
  {
    id: 'act-3',
    type: 'commented',
    title: 'Client comment on carousel',
    summary: '“Swap frame 1 hook for pain-point first.”',
    campaign: 'Q4 product launch',
    assignee: 'Mia Nguyen',
    actor: { name: 'Daniel Brooks', role: 'Client' },
    time: '24m ago',
    status: 'draft',
    needsInputFrom: 'Mia',
    platforms: ['instagram']
  },
  {
    id: 'act-4',
    type: 'approved',
    title: 'Legal approval granted',
    summary: 'Scripts cleared for reels with promo language.',
    campaign: 'Q4 product launch',
    assignee: 'Tyler James',
    actor: { name: 'Amelia Chen', role: 'Legal reviewer' },
    time: '1h ago',
    status: 'approved',
    platforms: ['short_video']
  },
  {
    id: 'act-5',
    type: 'scheduled',
    title: 'Two posts scheduled',
    summary: 'Queued for Wed 9am and Fri 3pm with UTM swap.',
    campaign: 'Retail holiday',
    assignee: 'Priya Shah',
    actor: { name: 'Jonas Lee', role: 'Marketing ops' },
    time: '3h ago',
    status: 'scheduled',
    platforms: ['facebook', 'instagram']
  }
];
const activityFilterState = {
  types: new Set(Object.keys(ACTIVITY_TYPE_META)),
  campaign: 'all',
  assignee: 'all'
};
const planCacheState = {
  meta: null
};
const templateLibraryState = {
  templates: [],
  lastUsed: null,
  profileKey: 'anon'
};
let lastTemplateUndoState = null;
const platformPresetState = {
  wizard: [],
  lastPlan: null
};
const DEFAULT_GENERATOR_PLATFORM = 'instagram';
const VIDEO_PLATFORM_KEYS = new Set(['instagram', 'short_video', 'tiktok']);
const TEMPLATE_LIBRARY_STORAGE_KEY = 'swelly_template_library';
const DEFAULT_PRESETS = [
  { id: 'product-launch', label: 'Product launch', goals: ['Product launch'], tone: 'inspirational', keywords: ['launch', 'new feature'] },
  { id: 'weekly-update', label: 'Weekly update', goals: ['Weekly update'], tone: 'friendly', keywords: ['community', 'newsletter'] }
];
let profileDefaults = { tone: 'friendly', industry: 'Business', keywords: [], goals: [], platforms: [], company: '', timezone: '', id: 'anon', hasProfile: false };
let lastGeneratorState = null;
let generatorHydratedFromProfile = false;

// Publishing queue state initialization
const PUBLISHING_QUEUE_STORAGE_KEY = 'eazeily_publishing_queue';

// Use the global namespaced queue state (initialized by publishing_queue_state_init.js)
// This provides a reference to the namespaced state for backward compatibility
function getPublishingQueueState() {
  if (window.__EAZEILY__ && window.__EAZEILY__.publishingQueueState) {
    return window.__EAZEILY__.publishingQueueState;
  }
  // Fallback: return a safe empty state if not initialized
  console.warn('[Eazeily] Publishing queue state not initialized. Returning empty state.');
  return { entries: [], items: [], status: 'idle', lastError: null };
}

// Note: publishing_queue_state_init.js MUST be loaded before dashboard.js (enforced in templates)
// This ensures the namespaced state is initialized before we create any references to it.

function logGeneratorEvent(event, meta = {}) {
  try {
    console.info(`[generator] ${event}`, meta);
    if (Array.isArray(window.dataLayer)) {
      window.dataLayer.push({ event: `generator.${event}`, meta });
    }
  } catch (err) {
    // ignore client logging failures
  }
}

function setGeneratorStatus(message, tone = 'muted') {
  const statusEl = generatorUI.statusEl || document.getElementById('generator-status');
  if (!statusEl) return;
  if (!message) {
    statusEl.classList.add('hidden');
    statusEl.textContent = '';
    return;
  }

  const toneClasses = {
    muted: 'text-slate-600',
    success: 'text-green-700',
    error: 'text-red-700'
  };
  const base = 'text-sm mt-2';
  statusEl.className = `${base} ${toneClasses[tone] || toneClasses.muted}`;
  statusEl.textContent = message;
  statusEl.classList.remove('hidden');
}

function getCurrentUserName() {
  const user = window.CURRENT_USER || {};
  return user.name || user.full_name || user.fullName || user.email || '';
}

function formatRelativeTimestamp(ts) {
  if (!ts) return '';
  const now = Date.now();
  const diff = now - ts;
  if (diff < 60 * 1000) return 'Just now';
  const minutes = Math.floor(diff / (60 * 1000));
  if (minutes < 60) return `${minutes} min${minutes === 1 ? '' : 's'} ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours} hr${hours === 1 ? '' : 's'} ago`;
  const days = Math.floor(hours / 24);
  return `${days} day${days === 1 ? '' : 's'} ago`;
}

async function getDashboardConfig() {
  if (dashboardConfigCache) return dashboardConfigCache;
  if (window.CFG && typeof window.CFG === 'object') {
    dashboardConfigCache = window.CFG;
    return dashboardConfigCache;
  }
  if (!dashboardConfigPromise) {
    dashboardConfigPromise = fetch('/static/content/config.json', { cache: 'no-store' })
      .then(res => res.ok ? res.json() : { industries: [], platforms: [] })
      .catch(() => ({ industries: [], platforms: [] }))
      .then(cfg => {
        dashboardConfigCache = cfg;
        return cfg;
      });
  }
  return dashboardConfigPromise;
}

async function ensureAccountFormFields() {
  if (accountFormReadyPromise) return accountFormReadyPromise;
  accountFormReadyPromise = (async () => {
    const cfg = await getDashboardConfig();
    populateAccountIndustryOptions(cfg.industries || []);
    populateAccountPlatformOptions(cfg.platforms || []);
  })();
  return accountFormReadyPromise;
}

function populateAccountIndustryOptions(list) {
  const select = document.getElementById('account-industry');
  if (!select) return;
  if (select.dataset.hydrated === '1') return;
  const fragment = document.createDocumentFragment();
  (list || []).forEach(item => {
    if (!item || !item.key) return;
    const opt = document.createElement('option');
    opt.value = item.key;
    opt.textContent = item.label;
    opt.dataset.label = item.label;
    fragment.appendChild(opt);
  });
  select.appendChild(fragment);
  select.dataset.hydrated = '1';
}

function populateAccountPlatformOptions(list) {
  const wrap = document.getElementById('account-platforms');
  if (!wrap) return;
  if (wrap.dataset.hydrated === '1') return;
  wrap.innerHTML = '';
  (list || []).forEach(item => {
    if (!item || !item.key) return;
    const id = `platform-${item.key}`;
  const label = document.createElement('label');
  label.className = 'flex items-center gap-2 bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-700 cursor-pointer select-none';
    const input = document.createElement('input');
    input.type = 'checkbox';
    input.value = item.key;
    input.id = id;
    input.dataset.platformCheckbox = '1';
    input.className = 'w-4 h-4 text-purple-600 bg-white border-slate-300 rounded focus:ring-purple-500';
    if (item.key === 'instagram') {
      input.checked = true;
    }
    const span = document.createElement('span');
    span.textContent = item.label;
    label.appendChild(input);
    label.appendChild(span);
    wrap.appendChild(label);
  });
  wrap.dataset.hydrated = '1';
}

document.addEventListener('DOMContentLoaded', () => {
  // Dev mode runtime check for queue state
  if (typeof window !== 'undefined' && (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')) {
    const queueState = getPublishingQueueState();
    if (!queueState) {
      console.warn('[Eazeily Dev Warning] publishingQueueState is not properly initialized. Queue features may not work.');
    } else if (!queueState.entries || !Array.isArray(queueState.entries)) {
      console.warn('[Eazeily Dev Warning] publishingQueueState.entries is not an array. Queue features may not work correctly.');
    }
  }

  const hasGenerator = Boolean(document.getElementById('content-generator'));
  const hasReviewPanel = Boolean(document.getElementById('review-response'));
  const hasSettings = Boolean(document.getElementById('account-company'));
  const hasVoiceCoach = Boolean(document.getElementById('voice-coach'));
  const hasFeedbackForm = Boolean(document.getElementById('feedback-form'));
  const hasActivityPanel = Boolean(document.getElementById('activity-panel'));

  setupProfileLoadBannerActions();

  loadUserProfile({ hydrateGenerator: hasGenerator, hydrateVoice: hasVoiceCoach || document.getElementById('voice-coach-summary') });

  if (hasReviewPanel) {
    setupReviewResponse();
  }

  if (hasGenerator) {
    setupContentGeneration();
    setupQuickActions();
    setupTemplateLibrary();
    setupOneClickGeneration();
    setupImageUpload();
    hydrateSeedPosts();
    seedPresetStateFromWizardDefaults();
    loadPublishingQueueFromStorage();
    renderPublishingQueue();
    updateQueueTimezoneLabel();
  }

  if (hasSettings) {
    setupAccountSettings();
  }

  const lazyHydrate = () => {
    if (hasFeedbackForm) setupFeedbackForm();
    if (hasVoiceCoach) setupVoiceCoach();
    if (hasActivityPanel) hydrateActivityFeed();
  };

  if ('requestIdleCallback' in window) {
    requestIdleCallback(lazyHydrate);
  } else {
    setTimeout(lazyHydrate, 250);
  }
});

async function loadUserProfile(options = {}) {
  const { hydrateGenerator = true, hydrateVoice = true, force = false } = options;
  if (profileLoadState.status === 'loading' && !force) return;

  profileLoadState.status = 'loading';
  profileLoadState.error = null;
  renderProfileLoadBanner();

  try {
    await ensureAccountFormFields();
  } catch (err) {
    /* ignore form prep errors */
  }

  let profile = null;
  let response = null;
  let body = null;
  let fetchError = null;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(new Error('profile-timeout')), PROFILE_FETCH_TIMEOUT_MS);

  try {
    response = await fetch('/api/profile', { credentials: 'include', signal: controller.signal });
    body = await response.json().catch(() => null);
  } catch (error) {
    fetchError = error;
  } finally {
    clearTimeout(timeoutId);
  }

  if (response && response.ok && body && body.ok !== false) {
    profile = normalizeProfileResponse(body);
    profileLoadState.status = 'loaded';
    profileLoadState.requestId = body.request_id || null;
    profileLoadState.profileStatus = body.profile_status || null;
    profileLoadState.reason = body.reason || null;
    profileLoadState.recommendedAction = body.recommended_action || null;
    
    // Cache the successfully loaded profile
    if (profile && profileLoadState.profileStatus === 'ready') {
      cacheProfile(profile, profileLoadState.profileStatus);
    }
  } else {
    // Try to use cached profile on failure
    const cached = getCachedProfile();
    if (cached && cached.profile) {
      console.log('Using cached profile due to fetch failure');
      profile = cached.profile;
      profileLoadState.profileStatus = cached.profileStatus || 'ready';
      profileLoadState.status = 'loaded_from_cache';
    }
    
    const timedOut = fetchError && fetchError.name === 'AbortError';
    const errorMessage = (body && body.error && body.error.message)
      || (timedOut ? 'Profile request timed out. Please retry.' : (fetchError && fetchError.message))
      || (response ? `Profile request failed (HTTP ${response.status})` : 'Profile request failed.');
    
    // Only set error state if we don't have a cached fallback
    if (!profile) {
      profileLoadState.status = 'error';
      profileLoadState.error = errorMessage;
      profileLoadState.requestId = (body && body.request_id) || null;
      profileLoadState.profileStatus = null;
      profileLoadState.reason = null;
      profileLoadState.recommendedAction = null;
    } else {
      // We have cached data, but note there was an issue
      profileLoadState.error = `${errorMessage} (using cached profile)`;
    }
  }

  if (profile && typeof profile === 'object') {
    try { applyProfileToAccountForm(profile); } catch (err) { /* ignore */ }
  }

  profileDefaults = buildProfileDefaults(profile);
  setTemplateProfileKey(profileDefaults.id);
  renderProfileDefaultsSummary(profileDefaults);
  renderProfileLoadBanner();
  hydrateTemplateLibrary();
  renderCollaborationSummary();

  if (hydrateGenerator) {
    applyProfileDefaultsToGenerator(profileDefaults);
    hydrateStoredGeneratorState({ apply: true, preferProfile: true });
  }

  if (hydrateVoice) {
    hydrateVoiceSummary(profileDefaults, { profileMissing: !profileDefaults.hasProfile });
  }

  const statusEl = document.getElementById('generator-status');
  if (statusEl && profileLoadState.status !== 'error') {
    statusEl.classList.add('hidden');
    statusEl.textContent = '';
  }

  if (profileLoadState.status === 'error') {
    if (statusEl) {
      statusEl.textContent = `${profileLoadState.error} Using defaults for now.`;
      statusEl.classList.remove('hidden');
    }
    console.error('Failed to load user profile:', profileLoadState.error);
  }
}

function normalizeProfileResponse(payload = {}) {
  if (!payload) return null;
  if (typeof payload === 'object' && Object.prototype.hasOwnProperty.call(payload, 'profile')) {
    return payload.profile;
  }
  return payload;
}

function cacheProfile(profile, profileStatus) {
  if (!profile || typeof profile !== 'object') return;
  try {
    const cacheData = {
      profile,
      profileStatus,
      timestamp: Date.now()
    };
    localStorage.setItem(PROFILE_CACHE_KEY, JSON.stringify(cacheData));
  } catch (err) {
    // Ignore cache failures (e.g., localStorage full or disabled)
    console.warn('Failed to cache profile:', err);
  }
}

function getCachedProfile() {
  try {
    const raw = localStorage.getItem(PROFILE_CACHE_KEY);
    if (!raw) return null;
    const cacheData = JSON.parse(raw);
    const age = Date.now() - (cacheData.timestamp || 0);
    if (age > PROFILE_CACHE_TTL_MS) {
      // Cache expired
      localStorage.removeItem(PROFILE_CACHE_KEY);
      return null;
    }
    return cacheData;
  } catch (err) {
    // Ignore cache read failures
    return null;
  }
}

function buildProfileDefaults(profile = null) {
  const source = profile && typeof profile === 'object' ? profile : {};
  const platforms = Array.isArray(source.platforms) ? source.platforms : [];
  const keywords = Array.isArray(source.brand_keywords) ? source.brand_keywords : [];
  const goals = Array.isArray(source.goals) ? source.goals : [];
  const hasProfile = Boolean(source.id || source.company || source.industry || source.industry_key || source.tone || platforms.length || keywords.length || goals.length);
  return {
    tone: source.tone || 'friendly',
    industry: source.industry || source.industry_key || 'Business',
    keywords,
    goals,
    platforms,
    company: source.company || '',
    timezone: source.timezone || '',
    id: source.id || (window.CURRENT_USER && window.CURRENT_USER.id) || 'anon',
    hasProfile,
    voice_profile: source.voice_profile || {}
  };
}

function renderProfileLoadBanner() {
  const banner = document.getElementById('profile-load-banner');
  if (!banner) return;
  const title = document.getElementById('profile-banner-title');
  const message = document.getElementById('profile-banner-message');
  const retryBtn = document.getElementById('profile-banner-retry');
  const continueBtn = document.getElementById('profile-banner-continue');
  
  // Show banner for errors OR when profile is missing/partial
  const shouldShow = profileLoadState.status === 'error' 
    || profileLoadState.profileStatus === 'missing' 
    || profileLoadState.profileStatus === 'partial';
  
  banner.classList.toggle('hidden', !shouldShow);
  if (!shouldShow) return;
  
  // Customize message based on profile status
  if (profileLoadState.status === 'error') {
    // Network/server error
    if (title) title.textContent = 'Unable to load your profile';
    if (message) {
      const detail = profileLoadState.error || 'Something went wrong while loading your profile.';
      const rid = profileLoadState.requestId ? ` (request ${profileLoadState.requestId})` : '';
      message.textContent = `${detail}${rid}`;
    }
    // Show retry button for errors
    if (retryBtn) retryBtn.classList.remove('hidden');
    if (continueBtn) continueBtn.classList.remove('hidden');
  } else if (profileLoadState.profileStatus === 'missing') {
    // No profile saved yet
    if (title) title.textContent = 'Profile not set up yet';
    if (message) {
      message.textContent = profileLoadState.reason || 'Complete the Setup Wizard to personalize your content and make it sound like you.';
    }
    // Hide retry button for missing profile (nothing to retry)
    if (retryBtn) retryBtn.classList.add('hidden');
    if (continueBtn) continueBtn.classList.remove('hidden');
  } else if (profileLoadState.profileStatus === 'partial') {
    // Profile exists but incomplete
    if (title) title.textContent = 'Profile incomplete';
    if (message) {
      const reason = profileLoadState.reason || 'Some settings are missing.';
      const action = profileLoadState.recommendedAction || 'Complete your profile in Settings to get better results.';
      message.textContent = `${reason} ${action}`;
    }
    // Hide retry button for partial profile (already loaded successfully)
    if (retryBtn) retryBtn.classList.add('hidden');
    if (continueBtn) continueBtn.classList.remove('hidden');
  }
}

function setupProfileLoadBannerActions() {
  const retry = document.getElementById('profile-banner-retry');
  if (retry) {
    retry.addEventListener('click', () => loadUserProfile({ hydrateGenerator: true, hydrateVoice: true, force: true }));
  }
  const cont = document.getElementById('profile-banner-continue');
  if (cont) {
    cont.addEventListener('click', () => {
      // Clear error state and dismiss banner
      if (profileLoadState.status === 'error') {
        profileLoadState.status = 'loaded';
        profileLoadState.error = null;
      }
      // For missing/partial, user acknowledges and wants to continue
      profileLoadState.profileStatus = 'acknowledged';
      renderProfileLoadBanner();
    });
  }
}

function applyProfileToAccountForm(profile = {}) {
  try {
    if (!profile || typeof profile !== 'object') return;
    const companyField = document.getElementById('account-company');
    if (companyField && profile.company) {
      companyField.value = profile.company;
    }
    setIndustryFieldValue(profile.industry);
    try {
      answers.industry = resolveIndustryLabel(profile.industry || profile.industry_key);
      const industries = getCachedIndustries();
      const normalizedIndustry = String(profile.industry_key || profile.industry || '').trim().toLowerCase();
      const keyMatch = industries.find(opt => (opt.key || '').toLowerCase() === normalizedIndustry);
      if (keyMatch) {
        answers.industry_key = keyMatch.key;
      } else {
        const labelMatch = industries.find(opt => (opt.label || '').toLowerCase() === normalizedIndustry);
        if (labelMatch) answers.industry_key = labelMatch.key;
      }
    } catch (err) {
      /* ignore */
    }
    if (profile.tone) {
      const toneField = document.getElementById('account-tone');
      if (toneField) toneField.value = profile.tone;
      try {
        answers.tone = profile.tone;
      } catch (err) {
        /* ignore */
      }
    }
    if (Array.isArray(profile.platforms) && profile.platforms.length) {
      setPlatformFieldValues(profile.platforms);
      applyPlatformPreferences(profile.platforms);
      try {
        answers.platforms = profile.platforms;
      } catch (err) {
        /* ignore */
      }
    } else {
      setPlatformFieldValues([]);
    }
    if (Array.isArray(profile.brand_keywords)) {
      setCurrentKeywords(profile.brand_keywords);
    }
    if (Array.isArray(profile.goals)) {
      setCurrentGoals(profile.goals);
    }
    if (profile.voice_profile) {
      try {
        answers.voice_profile = profile.voice_profile;
      } catch (err) {
        /* ignore */
      }
    }
  } catch (err) {
    console.error('applyProfileToAccountForm failed', err);
  }
}

function setIndustryFieldValue(value) {
  const select = document.getElementById('account-industry');
  if (!select) return;
  if (!value) {
    select.value = '';
    return;
  }
  const normalized = String(value).trim().toLowerCase();
  const options = Array.from(select.options || []);
  let match = options.find(opt => (opt.value || '').toLowerCase() === normalized);
  if (!match) {
    match = options.find(opt => (opt.dataset.label || '').trim().toLowerCase() === normalized);
  }
  if (match) {
    select.value = match.value;
  } else {
    const opt = document.createElement('option');
    opt.value = value;
    opt.textContent = value;
    opt.dataset.label = value;
    select.appendChild(opt);
    select.value = value;
  }
}

function setPlatformFieldValues(platforms = []) {
  const checkboxes = document.querySelectorAll('[data-platform-checkbox]');
  if (!checkboxes.length) return;
  const normalized = new Set((platforms || []).map(p => String(p).toLowerCase()));
  let anyChecked = false;
  checkboxes.forEach(cb => {
    const isChecked = normalized.has(cb.value.toLowerCase());
    cb.checked = isChecked;
    if (isChecked) anyChecked = true;
  });
  if (!anyChecked) {
    const insta = Array.from(checkboxes).find(cb => cb.value === 'instagram');
    if (insta) insta.checked = true;
  }
}

function setupReviewResponse() {
  const generateBtn = document.getElementById('generate-response');
  const loadingDiv = document.getElementById('response-loading');
  const resultDiv = document.getElementById('response-result');
  const responseText = document.getElementById('response-text');
  const responseMethod = document.getElementById('response-method');
  const copyBtn = document.getElementById('copy-response');

  if (!generateBtn || !loadingDiv || !resultDiv || !responseText || !responseMethod) return;

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

function normalizePlatformKey(value) {
  return String(value || '').trim().toLowerCase();
}

function getGeneratorPlatformButtons() {
  const wrap = document.getElementById('generator-platforms');
  if (!wrap) return [];
  return Array.from(wrap.querySelectorAll('[data-generator-platform]'));
}

function getGeneratorPlatformSelections() {
  const buttons = getGeneratorPlatformButtons();
  const active = buttons.filter(btn => btn.classList.contains('chip--active'));
  if (!active.length) return [DEFAULT_GENERATOR_PLATFORM];
  return active.map(btn => normalizePlatformKey(btn.dataset.generatorPlatform));
}

function setGeneratorPlatformSelections(platforms = []) {
  const buttons = getGeneratorPlatformButtons();
  if (!buttons.length) return [DEFAULT_GENERATOR_PLATFORM];
  const normalized = Array.from(new Set(platforms.map(normalizePlatformKey).filter(Boolean)));
  buttons.forEach(btn => {
    const key = normalizePlatformKey(btn.dataset.generatorPlatform);
    const isActive = normalized.includes(key);
    btn.classList.toggle('chip--active', isActive);
    btn.dataset.selected = isActive ? '1' : '0';
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
  if (!buttons.some(btn => btn.classList.contains('chip--active'))) {
    const fallback = buttons.find(btn => normalizePlatformKey(btn.dataset.generatorPlatform) === DEFAULT_GENERATOR_PLATFORM) || buttons[0];
    if (fallback) {
      fallback.classList.add('chip--active');
      fallback.dataset.selected = '1';
      fallback.setAttribute('aria-pressed', 'true');
    }
  }
  const selection = getGeneratorPlatformSelections();
  answers.platforms = selection;
  refreshReelOptionsVisibility();
  syncPreferredPlatformButtons();
  return selection;
}

function toggleGeneratorPlatformSelection(platform) {
  const buttons = getGeneratorPlatformButtons();
  if (!buttons.length) return;
  const normalizedTarget = normalizePlatformKey(platform);
  const targetBtn = buttons.find(btn => normalizePlatformKey(btn.dataset.generatorPlatform) === normalizedTarget);
  if (!targetBtn) return;
  const isActive = targetBtn.classList.contains('chip--active');
  if (isActive) {
    const activeCount = buttons.filter(btn => btn.classList.contains('chip--active')).length;
    if (activeCount <= 1) {
      showToast('Keep at least one platform selected.');
      return;
    }
  }
  targetBtn.classList.toggle('chip--active');
  const nowActive = targetBtn.classList.contains('chip--active');
  targetBtn.dataset.selected = nowActive ? '1' : '0';
  targetBtn.setAttribute('aria-pressed', nowActive ? 'true' : 'false');
  answers.platforms = getGeneratorPlatformSelections();
  refreshReelOptionsVisibility();
  syncPreferredPlatformButtons();
}

function initGeneratorPlatformPicker() {
  const buttons = getGeneratorPlatformButtons();
  if (!buttons.length) return;
  buttons.forEach(btn => {
    btn.addEventListener('click', () => toggleGeneratorPlatformSelection(btn.dataset.generatorPlatform));
  });
  if (answers?.platforms?.length) {
    setGeneratorPlatformSelections(answers.platforms);
  } else {
    setGeneratorPlatformSelections([DEFAULT_GENERATOR_PLATFORM]);
  }
}

function refreshReelOptionsVisibility() {
  const reelsCtaNotice = document.getElementById('reels-cta-notice');
  if (!reelsCtaNotice) return;
  
  const generatorMode = (document.body.dataset.generatorMode || '').toLowerCase();
  
  // Only show CTA in social mode when video platforms are selected
  if (generatorMode === 'social') {
    const selected = getGeneratorPlatformSelections();
    const hasVideo = selected.some(key => VIDEO_PLATFORM_KEYS.has(key));
    if (hasVideo) {
      reelsCtaNotice.classList.remove('hidden');
    } else {
      reelsCtaNotice.classList.add('hidden');
    }
  } else {
    // Never show CTA in reels mode
    reelsCtaNotice.classList.add('hidden');
  }
}

function setupContentGeneration() {
  const generateBtn = document.getElementById('generate-content') || document.getElementById('generate-plan');
  const loadingDiv = document.getElementById('content-loading') || document.getElementById('generator-loading');
  const resultsDiv = document.getElementById('generated-content');
  const contentResults = document.getElementById('content-results');
  const statusEl = document.getElementById('generator-status');
  const planLengthWrap = document.getElementById('plan-length-buttons');
  const daySelect = document.getElementById('gen-days');

  if (!generateBtn || !daySelect) return;

  // Hide 30-day option for free users
  const user = JSON.parse(document.body.dataset.initialUser || '{}');
  if (!user.is_paid) {
    const btn30 = planLengthWrap?.querySelector('button[data-plan-length="30"]');
    if (btn30) btn30.classList.add('hidden');
  }

  generatorUI = { generateBtn, loadingDiv, resultsDiv, contentResults, statusEl };
  initGeneratorPlatformPicker();
  refreshReelOptionsVisibility();
  syncPreferredPlatformButtons();

  const generatorMode = (document.body.dataset.generatorMode || '').toLowerCase();
  if (generatorMode === 'reels') {
    setGeneratorPlatformSelections(['short_video', 'tiktok']);
    refreshReelOptionsVisibility();
  }

  if (daySelect) {
    const initialDays = parseInt(daySelect.value, 10);
    if (!Number.isNaN(initialDays)) {
      lastPlanLength = initialDays;
    }
  }

  planLengthWrap?.querySelectorAll('button[data-plan-length]').forEach(btn => {
    btn.addEventListener('click', () => {
      const days = parseInt(btn.dataset.planLength || '0', 10);
      if (Number.isNaN(days)) return;
      updateGeneratorShortcut(days, { skipScroll: true, skipFocus: true });
    });
  });

  daySelect?.addEventListener('change', () => syncPlanLengthButtons());
  syncPlanLengthButtons();

  generateBtn?.addEventListener('click', () => {
    executeContentGeneration();
  });
}

  async function executeContentGeneration(options = {}) {
    const { daysOverride } = options;
    const {
      generateBtn,
      loadingDiv,
      resultsDiv,
      contentResults,
      statusEl
    } = generatorUI;
    if (!document.getElementById('gen-days')){
      showToast('Generator unavailable. Refresh and try again.');
      return;
    }
    if (!ensureDashboardAuth('Create a free account to generate content.')) return;
    if (generateBtn?.dataset.busy === '1') return;
    const days = typeof daysOverride === 'number'
      ? daysOverride
      : parseInt(document.getElementById('gen-days').value);
  if (!Number.isNaN(days)) {
    lastPlanLength = days;
  }
  const platforms = getGeneratorPlatformSelections();
  const tone = document.getElementById('gen-tone').value;
  const goals = getCurrentGoals();
  const keywords = getCurrentKeywords();
  if (!platforms.length) {
    showToast('Pick at least one platform to keep going.');
    return;
  }

  // Only include reel details on the dedicated reels page (not on social page)
  const includeReelDetails = false;
  let details = {};

    generateBtn?.classList.add('hidden');
    loadingDiv?.classList.remove('hidden');
    setGeneratorStatus('Sending request to the generator…', 'muted');
    if (generateBtn) generateBtn.dataset.busy = '1';
    logGeneratorEvent('click', { planLength: days, platforms, tone, goalsCount: goals.length, keywordsCount: keywords.length });

    try {
      const overrides = {
        platforms,
        tone,
        details,
        goals,
        brand_keywords: keywords
      };
    if (imageAttachmentState.dataUrl) {
      overrides.image_data_url = imageAttachmentState.dataUrl;
      const imageContext = document.getElementById('image-context')?.value.trim();
      if (imageContext) overrides.image_context = imageContext;
    }

      const data = await generate(days, overrides);
      if (!data || data.ok === false || !Array.isArray(data.posts)) {
        const msg = (data && data.error) ? data.error : 'Generator returned no posts.';
        throw new Error(msg);
      }
      if (contentResults) contentResults.innerHTML = '';
      renderPosts(data);
      const meta = buildPlanMetadataFromPayload(data);
      cacheGeneratedPlan(data, meta);
      lastGeneratorState = { platforms, tone, goals, keywords, planLength: days };
      persistTemplateLibraryState();
      applyPlanMetadata(meta);
      const totalPosts = data.count || (Array.isArray(data.posts) ? data.posts.length : 0);
      setGeneratorStatus(`Plan ready: ${totalPosts || 'draft'} posts generated.`, 'success');
      logGeneratorEvent('success', { planLength: days, platforms, totalPosts });
      resultsDiv?.classList.remove('hidden');
      resultsDiv?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (error) {
      console.error('Content generation failed:', error);
      const message = (error && error.message) ? error.message : 'Failed to generate content. Please try again.';
      setGeneratorStatus(message, 'error');
      logGeneratorEvent('error', { message, planLength: days, platforms });
      showToast(message);
    } finally {
      generateBtn?.classList.remove('hidden');
      loadingDiv?.classList.add('hidden');
      if (generateBtn) delete generateBtn.dataset.busy;
    }
  }

function setupImageUpload() {
  const input = document.getElementById('image-upload');
  if (!input) return;
  const trigger = document.getElementById('image-upload-trigger');
  const clearBtn = document.getElementById('image-upload-clear');
  const preview = document.getElementById('image-upload-preview');
  const nameEl = document.getElementById('image-upload-name');

  const resetAttachment = () => {
    imageAttachmentState.dataUrl = null;
    imageAttachmentState.fileName = '';
    if (input) input.value = '';
    if (preview) {
      preview.classList.add('hidden');
      preview.removeAttribute('src');
    }
    if (nameEl) nameEl.textContent = 'No image attached';
    clearBtn?.classList.add('hidden');
  };

  trigger?.addEventListener('click', (e) => {
    e.preventDefault();
    input.click();
  });

  clearBtn?.addEventListener('click', (e) => {
    e.preventDefault();
    resetAttachment();
  });

  input.addEventListener('change', () => {
    const file = input.files && input.files[0];
    if (!file) {
      resetAttachment();
      return;
    }
    if (file.size > 2.5 * 1024 * 1024) {
      showToast('Image is too large (max 2.5MB).');
      resetAttachment();
      return;
    }
    const reader = new FileReader();
    reader.onload = (ev) => {
      imageAttachmentState.dataUrl = ev.target?.result;
      imageAttachmentState.fileName = file.name;
      if (preview && typeof imageAttachmentState.dataUrl === 'string') {
        preview.src = imageAttachmentState.dataUrl;
        preview.classList.remove('hidden');
      }
      if (nameEl) {
        const kb = Math.round(file.size / 1024);
        nameEl.textContent = `${file.name} (${kb} KB)`;
      }
      clearBtn?.classList.remove('hidden');
    };
    reader.readAsDataURL(file);
  });
}

async function setupAccountSettings() {
  await ensureAccountFormFields();
  const saveBtn = document.getElementById('save-settings');
  const syncSummary = () => hydrateVoiceSummary(collectAccountFormProfile());

  ['account-company','account-industry','account-tone'].forEach(id => {
    const field = document.getElementById(id);
    field?.addEventListener('input', syncSummary);
    field?.addEventListener('change', syncSummary);
  });
  document.querySelectorAll('[data-platform-checkbox]').forEach(cb => {
    cb.addEventListener('change', syncSummary);
  });

  saveBtn?.addEventListener('click', async () => {
    const snapshot = collectAccountFormProfile();
    if (!snapshot.platforms.length) {
      snapshot.platforms = ['instagram'];
    }

    answers.company = snapshot.company;
    answers.industry = snapshot.industry;
    answers.industry_key = snapshot.industry_key;
    answers.tone = snapshot.tone;
    answers.platforms = snapshot.platforms;

    try {
      await saveProfile();
      applyPlatformPreferences(snapshot.platforms);
      hydrateVoiceSummary(snapshot);
      updateToneNote(snapshot.tone);
      showToast('Settings saved successfully!');
    } catch (error) {
      console.error('Failed to save settings:', error);
      showToast('Failed to save settings. Please try again.');
    }
  });
}

async function setupFeedbackForm() {
  const form = document.getElementById('feedback-form');
  if (!form) return;
  const summaryField = document.getElementById('feedback-summary');
  const detailsField = document.getElementById('feedback-details');
  const categoryField = document.getElementById('feedback-category');
  const contactField = document.getElementById('feedback-contact-ok');
  const statusEl = document.getElementById('feedback-status');
  const submitBtn = form.querySelector('[data-feedback-submit]');

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    if (!summaryField?.value.trim() || !detailsField?.value.trim()) {
      showToast('Add a summary and some details first.');
      return;
    }
    if (form.dataset.submitting === '1') {
      return;
    }
    const generatorPlatforms = getGeneratorPlatformSelections();
    const payload = {
      summary: summaryField.value.trim(),
      details: detailsField.value.trim(),
      category: categoryField?.value || 'idea',
      allow_contact: !!contactField?.checked,
      platform: generatorPlatforms[0] || DEFAULT_GENERATOR_PLATFORM,
      platforms: generatorPlatforms,
      plan_length: getCurrentPlanLength(),
      tone: (answers && answers.tone) || document.getElementById('account-tone')?.value,
      industry: answers?.industry_key || answers?.industry || document.getElementById('account-industry')?.value,
      source: 'dashboard-settings'
    };
    statusEl?.classList.add('hidden');
    form.dataset.submitting = '1';
    if (submitBtn) {
      submitBtn.disabled = true;
      submitBtn.textContent = 'Sending…';
    }
    try {
      const res = await fetch('/api/feedback/report', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify(payload)
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        throw new Error(data.error || 'Unable to send feedback');
      }
      if (statusEl) {
        statusEl.textContent = 'Thanks! Your note is on our roadmap list.';
        statusEl.className = 'text-xs text-green-600';
        statusEl.classList.remove('hidden');
      }
      form.reset();
      showToast('Feedback sent!');
    } catch (error) {
      console.error('Feedback form failed', error);
      if (statusEl) {
        statusEl.textContent = 'We could not send that yet. Please try again.';
        statusEl.className = 'text-xs text-red-600';
        statusEl.classList.remove('hidden');
      }
      showToast('Unable to send feedback right now.');
    } finally {
      form.dataset.submitting = '0';
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = 'Send to team';
      }
    }
  });
}

async function fetchVoiceCoachProfile() {
  try {
    const res = await fetch('/api/voice-profile', { credentials: 'include' });
    if (!res.ok) return null;
    return await res.json();
  } catch (err) {
    console.error('voice profile fetch failed', err);
    return null;
  }
}

function renderVoiceCoachPanel(payload = {}) {
  const status = document.getElementById('voice-coach-status');
  const include = document.getElementById('voice-coach-include');
  const avoid = document.getElementById('voice-coach-avoid');
  const example = document.getElementById('voice-coach-example');
  const toast = document.getElementById('voice-coach-toast');
  if (toast) toast.textContent = '';
  const vp = payload.voice_profile || payload.profile || null;
  voiceCoachState.profile = vp;
  voiceCoachState.samples = payload.samples || [];

  if (status) {
    const sampleCount = Array.isArray(payload.samples) ? payload.samples.length : 0;
    status.textContent = vp ? `Trained • ${sampleCount} samples` : 'Not trained';
    status.className = vp
      ? 'px-2 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700'
      : 'px-2 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700';
  }

  if (include) {
    const phrases = (vp?.include_phrases || []).slice(0, 3).join(', ');
    include.textContent = phrases || 'Add samples to see your top phrases.';
  }
  if (avoid) {
    const phrases = (vp?.avoid_phrases || []).slice(0, 3).join(', ');
    avoid.textContent = phrases || 'We’ll flag repeated filler once trained.';
  }
  if (example) {
    const line = (vp?.example_lines || [])[0];
    example.textContent = line || 'Save samples to generate a reference line.';
  }
}

function parseVoiceSamples(raw = '') {
  return (raw || '')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean);
}

async function setupVoiceCoach() {
  const input = document.getElementById('voice-sample-input');
  const btn = document.getElementById('save-voice-samples');
  if (!input || !btn) return;

  const data = await fetchVoiceCoachProfile();
  if (data) renderVoiceCoachPanel(data);

  btn.addEventListener('click', async () => {
    const toast = document.getElementById('voice-coach-toast');
    const samples = parseVoiceSamples(input.value || '');
    if (samples.length < 5 || samples.length > 10) {
      if (toast) toast.textContent = 'Add between 5 and 10 samples so we can train your voice.';
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Training…';
    try {
      const res = await fetch('/api/voice-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ samples })
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok || !body.ok) {
        throw new Error(body.error || 'Unable to save voice samples');
      }
      renderVoiceCoachPanel(body);
      if (toast) toast.textContent = 'Voice updated—new generations will stay on-brand.';
    } catch (error) {
      console.error('voice coach save failed', error);
      if (toast) toast.textContent = 'Could not train right now. Please try again.';
    } finally {
      btn.disabled = false;
      btn.textContent = 'Train voice';
    }
  });
}

function setupQuickActions() {
  const quickSample = document.getElementById('quick-sample');
  const quick7Day = document.getElementById('quick-7day');
  const quick30Day = document.getElementById('quick-30day');
  const handleShortcut = async (days, authMessage) => {
    const preferredPlatforms = getPreferredGeneratorPlatforms();
    if (preferredPlatforms.length) {
      setGeneratorPlatformSelections(preferredPlatforms);
    }
    updateGeneratorShortcut(days);
    if (!ensureDashboardAuth(authMessage)) return;
    await executeContentGeneration({ daysOverride: days });
  };

  quickSample?.addEventListener('click', () => handleShortcut(1, 'Create a free account to see sample content.'));
  quick7Day?.addEventListener('click', () => handleShortcut(7, 'Create a free account to unlock plans.'));
  quick30Day?.addEventListener('click', () => handleShortcut(30, 'Create a free account to unlock plans.'));
}

async function hydrateTemplateLibrary() {
  loadTemplateLibraryState();
  renderTemplatePicker();
  renderPresetButtons();
  renderCollaborationSummary();
  await refreshTemplatesFromServer();
}

function setupTemplateLibrary() {
  const saveBtn = document.getElementById('save-template');
  const applyBtn = document.getElementById('apply-template');
  const picker = document.getElementById('template-picker');
  const openModalBtn = document.getElementById('open-template-modal');
  const modalClose = document.getElementById('template-modal-close');
  const modalCancel = document.getElementById('template-modal-cancel');
  const modalSave = document.getElementById('template-modal-save');
  const undoBtn = document.getElementById('undo-template');

  hydrateTemplateLibrary();

  saveBtn?.addEventListener('click', () => openTemplateModal());
  openModalBtn?.addEventListener('click', () => openTemplateModal());
  modalClose?.addEventListener('click', () => closeTemplateModal());
  modalCancel?.addEventListener('click', () => closeTemplateModal());
  modalSave?.addEventListener('click', () => saveCurrentTemplateFromModal());
  applyBtn?.addEventListener('click', () => applySelectedTemplate());
  picker?.addEventListener('change', () => handleTemplateSelectionChange());
  undoBtn?.addEventListener('click', () => undoTemplateApplication());
}

async function refreshTemplatesFromServer() {
  try {
    const res = await fetch('/api/templates', { credentials: 'same-origin' });
    if (!res.ok) throw new Error('Failed to load templates');
    const data = await res.json();
    if (Array.isArray(data.templates)) {
      templateLibraryState.templates = data.templates.map(tpl => Object.assign({
        updatedAt: tpl.updated_at || tpl.updatedAt || Date.now(),
        author: tpl.author || getCurrentUserName() || 'Shared profile'
      }, tpl));
      renderTemplatePicker();
      renderCollaborationSummary();
      renderTemplatePreview(getSelectedTemplate());
      persistTemplateLibraryState();
    }
  } catch (err) {
    // fallback to local storage when offline
    renderTemplatePicker();
    renderTemplatePreview(getSelectedTemplate());
  }
}

function renderTemplatePicker() {
  const picker = document.getElementById('template-picker');
  const emptyState = document.getElementById('template-empty');
  if (!picker) return;
  picker.innerHTML = '';
  const placeholder = document.createElement('option');
  placeholder.value = '';
  placeholder.textContent = 'Choose saved template';
  picker.appendChild(placeholder);
  (templateLibraryState.templates || []).forEach(tpl => {
    const template = Object.assign({ updatedAt: Date.now() }, tpl);
    const opt = document.createElement('option');
    opt.value = template.id;
    const scopeLabel = template.scope === 'workspace' ? 'Workspace' : 'Personal';
    opt.textContent = template.author ? `${template.name} • ${scopeLabel}` : `${template.name} (${scopeLabel})`;
    opt.dataset.platforms = (template.platforms || []).join(',');
    opt.dataset.scope = template.scope || 'personal';
    picker.appendChild(opt);
  });
  updateTemplateEmptyState(emptyState);
  handleTemplateSelectionChange();
}

function renderCollaborationSummary() {
  const presence = document.getElementById('collab-presence');
  const nameEl = document.getElementById('collab-template-name');
  const authorEl = document.getElementById('collab-template-author');
  const timeEl = document.getElementById('collab-template-time');
  const templates = Array.isArray(templateLibraryState.templates) ? templateLibraryState.templates : [];
  const latest = templates.reduce((acc, tpl) => {
    const updated = tpl.updatedAt || 0;
    if (!acc || updated > (acc.updatedAt || 0)) return tpl;
    return acc;
  }, null);
  const active = (lastGeneratorState && lastGeneratorState.updatedAt) ? lastGeneratorState : latest;
  const authorName = active?.author || getCurrentUserName() || 'Shared profile';
  const timeLabel = active?.updatedAt ? `Updated ${formatRelativeTimestamp(active.updatedAt)}` : 'Waiting for your first save.';

  if (presence) {
    presence.textContent = templates.length
      ? `${templates.length} shared preset${templates.length === 1 ? '' : 's'} ready for the team`
      : 'No shared presets yet—save one to match the solo flow.';
  }
  if (nameEl) nameEl.textContent = active?.name || 'No presets yet';
  if (authorEl) authorEl.textContent = active ? `Saved by ${authorName}` : 'Save one to see it here.';
  if (timeEl) timeEl.textContent = timeLabel;
}

function renderPresetButtons() {
  const wrap = document.getElementById('template-preset-buttons');
  if (!wrap) return;
  wrap.innerHTML = '';
  DEFAULT_PRESETS.forEach(preset => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chip chip--ghost';
    btn.dataset.templatePreset = preset.id;
    btn.textContent = preset.label;
    btn.addEventListener('click', () => applyPresetTemplate(preset));
    wrap.appendChild(btn);
  });
}

function updateTemplateEmptyState(target) {
  const emptyState = target || document.getElementById('template-empty');
  if (!emptyState) return;
  const hasItems = Array.isArray(templateLibraryState.templates) && templateLibraryState.templates.length;
  emptyState.classList.toggle('hidden', !!hasItems);
}

function getSelectedTemplate() {
  const picker = document.getElementById('template-picker');
  if (!picker) return null;
  const selectedId = picker.value;
  if (!selectedId) return null;
  return (templateLibraryState.templates || []).find(t => t.id === selectedId) || null;
}

function handleTemplateSelectionChange() {
  renderTemplatePreview(getSelectedTemplate());
  updateTemplateEmptyState();
}

function buildTemplatePreviewText(state = {}) {
  const parts = [];
  if (state.tone) parts.push(`Tone: ${state.tone}`);
  if (Array.isArray(state.platforms) && state.platforms.length) {
    parts.push(`Platforms: ${state.platforms.join(', ')}`);
  }
  if (Array.isArray(state.goals) && state.goals.length) {
    parts.push(`Goals: ${state.goals.join(', ')}`);
  }
  if (Array.isArray(state.keywords) && state.keywords.length) {
    parts.push(`Keywords: ${state.keywords.join(', ')}`);
  }
  return parts.join(' • ') || 'Tone, platforms, and goals from your current draft will be saved.';
}

function captureCurrentGeneratorState() {
  return {
    tone: document.getElementById('gen-tone')?.value || 'friendly',
    platforms: getGeneratorPlatformSelections(),
    goals: getCurrentGoals(),
    keywords: getCurrentKeywords(),
    planLength: getCurrentPlanLength()
  };
}

function openTemplateModal() {
  const modal = document.getElementById('template-modal');
  const nameField = document.getElementById('template-modal-name');
  const preview = document.getElementById('template-modal-preview');
  if (!modal) return;
  preview.textContent = buildTemplatePreviewText(captureCurrentGeneratorState());
  modal.classList.remove('hidden');
  modal.setAttribute('aria-hidden', 'false');
  nameField.value = '';
  nameField.focus();
}

function closeTemplateModal() {
  const modal = document.getElementById('template-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.setAttribute('aria-hidden', 'true');
}

async function saveCurrentTemplateFromModal() {
  const nameField = document.getElementById('template-modal-name');
  const scopeField = document.getElementById('template-modal-scope');
  const name = (nameField?.value || '').trim();
  const scope = (scopeField?.value || 'personal').trim();
  await saveCurrentTemplate({ name, scope });
}

function addTemplateToState(template) {
  const nameKey = (template.name || '').toLowerCase();
  const existingIdx = (templateLibraryState.templates || []).findIndex(t => (t.name || '').toLowerCase() === nameKey);
  if (existingIdx >= 0) {
    templateLibraryState.templates[existingIdx] = Object.assign({}, templateLibraryState.templates[existingIdx], template);
  } else {
    templateLibraryState.templates = [...(templateLibraryState.templates || []), template];
  }
  renderTemplatePicker();
  renderCollaborationSummary();
  renderTemplatePreview(getSelectedTemplate());
  persistTemplateLibraryState();
}

async function saveCurrentTemplate(opts = {}) {
  const name = (opts.name || '').trim();
  if (!name) {
    showToast('Name your template first.');
    return;
  }
  const generatorState = captureCurrentGeneratorState();
  const payload = {
    generator: generatorState,
    profile_defaults: profileDefaults || {},
    draft: planCacheState.meta || {}
  };
  const baseTemplate = {
    id: opts.id || `tpl-${Date.now()}`,
    name,
    scope: opts.scope || 'personal',
    author: getCurrentUserName() || 'Shared profile',
    payload,
    preview: buildTemplatePreviewText(generatorState),
    updatedAt: Date.now()
  };
  let savedTemplate = baseTemplate;
  try {
    const res = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'same-origin',
      body: JSON.stringify({
        name,
        scope: baseTemplate.scope,
        payload,
        preview: baseTemplate.preview
      })
    });
    if (res.ok) {
      const data = await res.json();
      if (data?.template) {
        savedTemplate = Object.assign({}, baseTemplate, data.template, {
          payload: data.template.payload || baseTemplate.payload
        });
      }
    }
  } catch (error) {
    console.error('Template save failed, keeping local copy', error);
  }

  lastGeneratorState = Object.assign({}, generatorState, {
    planLength: generatorState.planLength,
    updatedAt: savedTemplate.updatedAt,
    author: savedTemplate.author,
    name: savedTemplate.name
  });
  addTemplateToState(savedTemplate);
  closeTemplateModal();
  showToast('Template saved for this profile.');
}

function renderTemplatePreview(tpl) {
  const preview = document.getElementById('template-preview');
  if (!preview) return;
  if (!tpl) {
    preview.innerHTML = '<p class="text-sm font-semibold text-slate-900">No templates yet</p><p class="text-xs text-slate-600">Save your first template to preview tone, platforms, and goals before applying.</p>';
    document.getElementById('undo-template')?.classList.add('hidden');
    return;
  }
  const generatorPayload = extractGeneratorPayload(tpl);
  const previewText = buildTemplatePreviewText(generatorPayload || {});
  const scopeLabel = tpl.scope === 'workspace' ? 'Workspace' : 'Personal';
  preview.innerHTML = `
    <div class="flex items-start justify-between gap-3">
      <div>
        <p class="text-xs uppercase tracking-wide text-slate-500">${scopeLabel} template</p>
        <p class="text-sm font-semibold text-slate-900">${escapeHtml(tpl.name || 'Untitled')}</p>
        <p class="text-xs text-slate-600">${escapeHtml(previewText)}</p>
      </div>
      <span class="text-[11px] px-2 py-1 rounded-full bg-slate-100 text-slate-600">${tpl.author || 'Shared profile'}</span>
    </div>`;
}

function applySelectedTemplate() {
  const tpl = getSelectedTemplate();
  if (!tpl) {
    showToast('Pick a template to apply.');
    return;
  }
  applyTemplateWithUndo(tpl);
  renderCollaborationSummary();
}

function extractGeneratorPayload(tpl = {}) {
  if (tpl.payload && typeof tpl.payload === 'object') {
    if (tpl.payload.generator) return tpl.payload.generator;
    if (tpl.payload.config) return tpl.payload.config;
  }
  if (tpl.generator) return tpl.generator;
  return tpl;
}

function applyTemplateWithUndo(tpl) {
  const generatorPayload = extractGeneratorPayload(tpl);
  const previousState = captureCurrentGeneratorState();
  applyTemplateToGenerator(generatorPayload);
  lastTemplateUndoState = previousState;
  const undoBtn = document.getElementById('undo-template');
  undoBtn?.classList.remove('hidden');
  showToast('Template applied. Undo to restore previous draft.');
}

function undoTemplateApplication() {
  if (!lastTemplateUndoState) {
    showToast('No template change to undo.');
    return;
  }
  applyGeneratorState(lastTemplateUndoState, { sync: true });
  lastTemplateUndoState = null;
  document.getElementById('undo-template')?.classList.add('hidden');
  showToast('Template reverted.');
}

function applyPresetTemplate(preset) {
  const tpl = {
    id: preset.id,
    name: preset.label,
    payload: {
      generator: {
        tone: preset.tone,
        platforms: getGeneratorPlatformSelections(),
        goals: preset.goals,
        keywords: preset.keywords
      }
    },
    author: 'Team preset',
    updatedAt: Date.now()
  };
  applyTemplateWithUndo(tpl);
  renderCollaborationSummary();
}

function applyTemplateToGenerator(tpl, opts = {}) {
  if (!tpl) return;
  const generatorConfig = tpl.generator || tpl.payload?.generator || tpl;
  if (generatorConfig.tone) {
    const toneField = document.getElementById('gen-tone');
    if (toneField) toneField.value = generatorConfig.tone;
  }
  if (!opts.skipPlatform && Array.isArray(generatorConfig.platforms) && generatorConfig.platforms.length) {
    setGeneratorPlatformSelections(generatorConfig.platforms);
  }
  if (Array.isArray(generatorConfig.goals)) setCurrentGoals(generatorConfig.goals);
  if (Array.isArray(generatorConfig.keywords)) setCurrentKeywords(generatorConfig.keywords);
  if (generatorConfig.planLength) {
    updateGeneratorShortcut(generatorConfig.planLength, { skipFocus: true, skipScroll: true });
  }
  syncPreferredPlatformButtons();
  refreshReelOptionsVisibility();
  lastGeneratorState = Object.assign({}, generatorConfig, {
    planLength: generatorConfig.planLength || getCurrentPlanLength(),
    updatedAt: generatorConfig.updatedAt || Date.now(),
    author: generatorConfig.author || tpl.author || getCurrentUserName() || 'Shared profile',
    name: tpl.name || generatorConfig.name
  });
  persistTemplateLibraryState();
}

function setupOneClickGeneration() {
  const btn = document.getElementById('one-click-generate');
  if (!btn) return;
  btn.addEventListener('click', async () => {
    if (lastGeneratorState) {
      applyGeneratorState(lastGeneratorState, { sync: true });
    } else {
      applyProfileDefaultsToGenerator(Object.assign({}, profileDefaults, { force: true }));
    }
    await executeContentGeneration();
  });
}

function updateGeneratorShortcut(days, opts = {}){
  const select = document.getElementById('gen-days');
  if (select){
    select.value = String(days);
    select.dispatchEvent(new Event('change'));
  }
  if (!opts.skipScroll){
    const generatorSection = document.getElementById('content-generator');
    generatorSection?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
  if (!opts.skipFocus){
    document.getElementById('generate-content')?.focus();
  }
  syncPlanLengthButtons();
}

function syncPlanLengthButtons(){
  const select = document.getElementById('gen-days');
  const wrap = document.getElementById('plan-length-buttons');
  if (!select || !wrap) return;
  const current = select.value;
  wrap.querySelectorAll('button[data-plan-length]').forEach(btn => {
    const isActive = btn.dataset.planLength === current;
    btn.classList.toggle('chip--active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
}

function getCurrentPlanLength(){
  const select = document.getElementById('gen-days');
  if (select){
    const val = parseInt(select.value, 10);
    if (!Number.isNaN(val)){
      return val;
    }
  }
  return lastPlanLength || 1;
}

function ensureDashboardAuth(message){
  if (typeof isLoggedIn === 'function' && isLoggedIn()) return true;
  if (typeof openAuthModal === 'function') openAuthModal('signup');
  showToast(message || 'Sign up to continue.');
  return false;
}

function cacheGeneratedPlan(data, metaOverride) {
  if (typeof localStorage === 'undefined') return;
  try {
    const meta = metaOverride || buildPlanMetadataFromPayload(data);
    planCacheState.meta = meta;
    localStorage.setItem(DASHBOARD_PLAN_CACHE_KEY, JSON.stringify({ ts: Date.now(), payload: data, meta }));
  } catch (error) {
    /* ignore */
  }
}

function loadCachedGeneratedPlan() {
  if (typeof localStorage === 'undefined') return null;
  try {
    const raw = localStorage.getItem(DASHBOARD_PLAN_CACHE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    if (!parsed || (!parsed.payload && !parsed.posts)) return null;
    if (parsed.ts && (Date.now() - parsed.ts) > DASHBOARD_PLAN_TTL_MS) {
      localStorage.removeItem(DASHBOARD_PLAN_CACHE_KEY);
      return null;
    }
    const payload = parsed.payload || parsed;
    if (!payload || !Array.isArray(payload.posts)) return null;
    const meta = parsed.meta || buildPlanMetadataFromPayload(payload);
    planCacheState.meta = meta;
    return { payload, meta, ts: parsed.ts || Date.now() };
  } catch (error) {
    return null;
  }
}

function buildPlanMetadataFromPayload(payload = {}) {
  if (!payload || typeof payload !== 'object') {
    return { note: '', platforms: [], planLength: null, tone: '', company: '', generatedAt: Date.now() };
  }
  const profile = (payload.profile && typeof payload.profile === 'object') ? payload.profile : {};
  const details = (profile.details && typeof profile.details === 'object')
    ? profile.details
    : ((payload.details && typeof payload.details === 'object') ? payload.details : {});
  const note = typeof details.note === 'string' ? details.note.trim() : '';
  const rawPlatforms = Array.isArray(profile.platforms) && profile.platforms.length
    ? profile.platforms
    : (Array.isArray(payload.platforms) ? payload.platforms : []);
  const platforms = dedupePlatforms(rawPlatforms);
  const planLength = profile.days || payload.days || derivePlanLengthFromPayload(payload) || null;
  const tone = profile.tone || payload.tone || '';
  const company = profile.company || payload.company || '';
  return {
    note,
    platforms,
    planLength,
    tone,
    company,
    generatedAt: Date.now()
  };
}

function dedupePlatforms(list = []) {
  const out = [];
  const seen = new Set();
  (Array.isArray(list) ? list : []).forEach(value => {
    const key = normalizePlatformKey(value);
    if (!key || seen.has(key)) return;
    seen.add(key);
    out.push(key);
  });
  return out;
}

function parseCommaList(value = '') {
  return String(value || '')
    .split(/[\n,]/)
    .map(item => item.trim())
    .filter(Boolean);
}

function getActiveProfileKey() {
  return templateLibraryState.profileKey || profileDefaults.id || (window.CURRENT_USER && window.CURRENT_USER.id) || 'anon';
}

function setTemplateProfileKey(key) {
  templateLibraryState.profileKey = key || 'anon';
}

function getTemplateStorageKey() {
  return `${TEMPLATE_LIBRARY_STORAGE_KEY}:${getActiveProfileKey()}`;
}

function getCurrentGoals() {
  const input = document.getElementById('gen-goals');
  return parseCommaList(input ? input.value : '');
}

function setCurrentGoals(list = []) {
  const input = document.getElementById('gen-goals');
  if (input) {
    input.value = (list || []).join(', ');
  }
  try {
    answers.goals = list;
  } catch (err) {
    /* ignore */
  }
}

function getCurrentKeywords() {
  const input = document.getElementById('gen-keywords');
  return parseCommaList(input ? input.value : '');
}

function setCurrentKeywords(list = []) {
  const input = document.getElementById('gen-keywords');
  if (input) {
    input.value = (list || []).join(', ');
  }
  try {
    answers.brand_keywords = list;
  } catch (err) {
    /* ignore */
  }
}

function persistTemplateLibraryState() {
  if (typeof localStorage === 'undefined') return;
  try {
    const templates = (templateLibraryState.templates || []).map(tpl => Object.assign({
      updatedAt: tpl.updatedAt || Date.now()
    }, tpl));
    const payload = {
      templates,
      lastUsed: lastGeneratorState
    };
    localStorage.setItem(getTemplateStorageKey(), JSON.stringify(payload));
  } catch (error) {
    /* ignore */
  }
}

function loadTemplateLibraryState() {
  if (typeof localStorage === 'undefined') return;
  try {
    const raw = localStorage.getItem(getTemplateStorageKey());
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed.templates)) {
      templateLibraryState.templates = parsed.templates.map(tpl => Object.assign({
        updatedAt: tpl.updatedAt || Date.now(),
        author: tpl.author || 'Shared profile'
      }, tpl));
    }
    if (parsed.lastUsed) {
      lastGeneratorState = Object.assign({ updatedAt: parsed.lastUsed.updatedAt || Date.now() }, parsed.lastUsed);
    }
  } catch (error) {
    /* ignore */
  }
}

function renderProfileDefaultsSummary(defaults = {}) {
  const target = document.getElementById('profile-defaults-summary');
  if (!target) return;
  const tone = defaults.tone || 'friendly';
  const industry = defaults.industry || 'Business';
  const keywords = (defaults.keywords || []).slice(0, 4);
  const goalSnippet = (defaults.goals || []).slice(0, 2);
  const details = [];
  details.push(`Tone: ${tone}`);
  details.push(`Industry: ${industry}`);
  if (keywords.length) details.push(`Keywords: ${keywords.join(', ')}`);
  if (goalSnippet.length) details.push(`Goals: ${goalSnippet.join(', ')}`);
  target.textContent = (defaults.hasProfile ? '' : 'Using defaults — ') + details.join(' • ');
}

function applyProfileDefaultsToGenerator(defaults = {}) {
  if (generatorHydratedFromProfile && !defaults.force) return;
  const toneField = document.getElementById('gen-tone');
  if (toneField && defaults.tone) {
    toneField.value = defaults.tone;
  }
  if (Array.isArray(defaults.platforms) && defaults.platforms.length) {
    setGeneratorPlatformSelections(defaults.platforms);
  }
  if (defaults.industry) {
    try { answers.industry = defaults.industry; } catch (err) { /* ignore */ }
  }
  if (Array.isArray(defaults.keywords)) {
    setCurrentKeywords(defaults.keywords);
  }
  if (Array.isArray(defaults.goals)) {
    setCurrentGoals(defaults.goals);
  }
  generatorHydratedFromProfile = true;
}

function applyGeneratorState(state = {}, opts = {}) {
  if (!state || typeof state !== 'object') return;
  if (state.tone) {
    const toneField = document.getElementById('gen-tone');
    if (toneField) toneField.value = state.tone;
  }
  if (Array.isArray(state.platforms) && state.platforms.length) {
    setGeneratorPlatformSelections(state.platforms);
  }
  if (Array.isArray(state.goals)) {
    setCurrentGoals(state.goals);
  }
  if (Array.isArray(state.keywords)) {
    setCurrentKeywords(state.keywords);
  }
  if (state.planLength) {
    updateGeneratorShortcut(state.planLength, { skipFocus: true, skipScroll: true });
  }
  if (opts.sync) {
    syncPlanLengthButtons();
    refreshReelOptionsVisibility();
    syncPreferredPlatformButtons();
  }
}

function hydrateStoredGeneratorState(opts = {}) {
  loadTemplateLibraryState();
  if (lastGeneratorState && opts.apply) {
    if (opts.preferProfile) {
      const merged = Object.assign({}, profileDefaults || {}, lastGeneratorState);
      applyGeneratorState(merged, { sync: true });
    } else {
      applyGeneratorState(lastGeneratorState, { sync: true });
    }
  }
}

function getWizardDefaultPlatforms() {
  try {
    if (Array.isArray(answers?.platforms) && answers.platforms.length) {
      return dedupePlatforms(answers.platforms);
    }
  } catch (err) {
    /* ignore */
  }
  return [];
}

async function seedPresetStateFromWizardDefaults() {
  const wizardDefaults = getWizardDefaultPlatforms();
  if (!wizardDefaults.length) return;
  try {
    await ensureAccountFormFields();
  } catch (err) {
    /* ignore */
  }
  const hasLastPlanPreset = !!(platformPresetState.lastPlan && Array.isArray(platformPresetState.lastPlan.platforms) && platformPresetState.lastPlan.platforms.length);
  applyPlatformPreferences(wizardDefaults, { skipSelection: hasLastPlanPreset });
}

function derivePlanLengthFromPayload(data) {
  if (!data) return null;
  if (data?.profile?.days) return data.profile.days;
  if (data?.days) return data.days;
  if (Array.isArray(data.posts) && data.posts.length) {
    return Math.max(...data.posts.map(post => +post.day_index || 0));
  }
  return null;
}

function hydrateSeedPosts() {
  let payload = null;
  let meta = null;
  let shouldScroll = false;
  if (typeof sessionStorage !== 'undefined') {
    const raw = sessionStorage.getItem(DASHBOARD_SEED_STORAGE_KEY);
    if (raw) {
      sessionStorage.removeItem(DASHBOARD_SEED_STORAGE_KEY);
      try {
        const parsed = JSON.parse(raw);
        payload = parsed?.payload || parsed?.data || parsed;
        if (parsed && parsed.meta) meta = parsed.meta;
        shouldScroll = true;
      } catch (error) {
        console.error('seed hydration failed', error);
      }
    }
  }
  if (!payload) {
    const cached = loadCachedGeneratedPlan();
    if (cached) {
      payload = cached.payload;
      meta = cached.meta;
    }
  }
  if (!payload || !Array.isArray(payload.posts) || !payload.posts.length) return;
  const derivedMeta = meta || buildPlanMetadataFromPayload(payload);
  cacheGeneratedPlan(payload, derivedMeta);
  applyPlanMetadata(derivedMeta);
  const resultsWrap = document.getElementById('generated-content');
  resultsWrap?.classList.remove('hidden');
  renderPosts(payload);
  const derivedPlanLength = derivedMeta.planLength || derivePlanLengthFromPayload(payload);
  if (derivedPlanLength) {
    lastPlanLength = derivedPlanLength;
  }
  if (shouldScroll) {
    resultsWrap?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  }
}

function applyPlanMetadata(meta) {
  if (!meta || typeof meta !== 'object') return;
  planCacheState.meta = meta;
  if (Array.isArray(meta.platforms) && meta.platforms.length) {
    platformPresetState.lastPlan = {
      platforms: dedupePlatforms(meta.platforms),
      note: meta.note || '',
      planLength: meta.planLength || null,
      generatedAt: meta.generatedAt || Date.now()
    };
  } else {
    platformPresetState.lastPlan = null;
  }
  setPlanNoteBanner(meta.note);
  renderPlatformPresetButtons();
}

function setPlanNoteBanner(note, meta = {}) {
  const banner = document.getElementById('plan-note-banner');
  const textEl = document.getElementById('plan-note-text');
  if (!banner || !textEl) return;
  const trimmed = typeof note === 'string' ? note.trim() : '';
  if (!trimmed) {
    banner.classList.add('hidden');
    textEl.textContent = '';
    return;
  }
  textEl.textContent = trimmed;
  banner.classList.remove('hidden');
}

function ensureGeneratedViewPrefsLoaded() {
  if (generatedViewPrefs.loaded) return;
  generatedViewPrefs.loaded = true;
  if (typeof localStorage === 'undefined') return;
  try {
    const raw = localStorage.getItem(GENERATED_VIEW_PREFS_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed.collapsedDays)) {
      generatedViewPrefs.collapsedDays = new Set(parsed.collapsedDays.map(String));
    }
    if (Array.isArray(parsed.hiddenPlatforms)) {
      generatedViewPrefs.hiddenPlatforms = new Set(parsed.hiddenPlatforms.map(key => String(key).toLowerCase()));
    }
  } catch (error) {
    /* ignore */
  }
}

function persistGeneratedViewPrefs() {
  if (typeof localStorage === 'undefined') return;
  try {
    const payload = {
      collapsedDays: Array.from(generatedViewPrefs.collapsedDays),
      hiddenPlatforms: Array.from(generatedViewPrefs.hiddenPlatforms)
    };
    localStorage.setItem(GENERATED_VIEW_PREFS_KEY, JSON.stringify(payload));
  } catch (error) {
    /* ignore */
  }
}

function isDayCollapsed(day) {
  ensureGeneratedViewPrefsLoaded();
  return generatedViewPrefs.collapsedDays.has(String(day));
}

function setDayCollapsed(day, collapsed) {
  ensureGeneratedViewPrefsLoaded();
  const key = String(day);
  if (collapsed) {
    generatedViewPrefs.collapsedDays.add(key);
  } else {
    generatedViewPrefs.collapsedDays.delete(key);
  }
  persistGeneratedViewPrefs();
}

function expandOrCollapseAllDays(collapsed) {
  ensureGeneratedViewPrefsLoaded();
  const sections = Array.from(document.querySelectorAll('[data-day-section]'));
  if (!sections.length) return;
  generatedViewPrefs.collapsedDays = collapsed
    ? new Set(sections.map(section => String(section.dataset.daySection || '')))
    : new Set();
  persistGeneratedViewPrefs();
  sections.forEach(section => applyDayCollapse(section, collapsed));
}

function applyDayCollapse(section, collapsed) {
  if (!section) return;
  const body = section.querySelector('.generated-day__body');
  const toggle = section.querySelector('[data-day-toggle]');
  section.classList.toggle('is-collapsed', collapsed);
  if (body) body.hidden = collapsed;
  if (toggle) {
    toggle.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
    toggle.setAttribute('aria-label', collapsed ? 'Expand day' : 'Collapse day');
  }
}

function handleDayToggle(day, section) {
  const nextState = !section?.classList.contains('is-collapsed');
  applyDayCollapse(section, nextState);
  setDayCollapsed(day, nextState);
}

function renderGeneratedFilters(platforms = []) {
  const toolbar = document.getElementById('generated-toolbar');
  const chipsWrap = document.getElementById('platform-filter-chips');
  if (!toolbar || !chipsWrap) return;
  if (!platforms.length) {
    toolbar.classList.add('hidden');
    chipsWrap.innerHTML = '';
    return;
  }

  ensureGeneratedViewPrefsLoaded();
  toolbar.classList.remove('hidden');
  chipsWrap.innerHTML = '';
  const total = platforms.length;
  const currentKeys = new Set(platforms.map(({ key }) => String(key).toLowerCase()));
  platforms.forEach(({ key, label }) => {
    const normalized = String(key).toLowerCase();
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.platformFilter = normalized;
    btn.className = 'filter-chip';
    const isVisible = !generatedViewPrefs.hiddenPlatforms.has(normalized);
    btn.classList.toggle('filter-chip--active', isVisible);
    btn.setAttribute('aria-pressed', isVisible ? 'true' : 'false');
    btn.textContent = label;
    btn.addEventListener('click', () => handlePlatformFilterClick(normalized, btn, currentKeys));
    chipsWrap.appendChild(btn);
  });

  const expandBtn = document.getElementById('expand-all-days');
  const collapseBtn = document.getElementById('collapse-all-days');
  if (expandBtn) expandBtn.onclick = () => expandOrCollapseAllDays(false);
  if (collapseBtn) collapseBtn.onclick = () => expandOrCollapseAllDays(true);
}

function resetHiddenPlatformsFor(platforms = []) {
  ensureGeneratedViewPrefsLoaded();
  if (!platforms.length) return;
  let mutated = false;
  platforms.forEach(({ key }) => {
    const normalized = String(key || '').toLowerCase();
    if (generatedViewPrefs.hiddenPlatforms.has(normalized)) {
      generatedViewPrefs.hiddenPlatforms.delete(normalized);
      mutated = true;
    }
  });
  if (mutated) {
    persistGeneratedViewPrefs();
  }
}

function handlePlatformFilterClick(platform, button, currentKeys) {
  ensureGeneratedViewPrefsLoaded();
  const hidden = generatedViewPrefs.hiddenPlatforms;
  const activeHiddenCount = Array.from(hidden).filter(key => currentKeys.has(key)).length;
  if (hidden.has(platform)) {
    hidden.delete(platform);
  } else {
    if (activeHiddenCount + 1 >= currentKeys.size) {
      showToast('Keep at least one platform visible.');
      return;
    }
    hidden.add(platform);
  }
  button.classList.toggle('filter-chip--active', !hidden.has(platform));
  button.setAttribute('aria-pressed', hidden.has(platform) ? 'false' : 'true');
  persistGeneratedViewPrefs();
  applyPlatformFilters();
}

function applyPlatformFilters() {
  ensureGeneratedViewPrefsLoaded();
  const hidden = generatedViewPrefs.hiddenPlatforms;
  document.querySelectorAll('[data-platform-key]').forEach(card => {
    const platform = (card.dataset.platformKey || '').toLowerCase();
    const shouldHide = hidden.has(platform);
    card.classList.toggle('generated-post-card--hidden', shouldHide);
  });
  refreshDayEmptyStates();
}

function refreshDayEmptyStates() {
  document.querySelectorAll('[data-day-section]').forEach(section => {
    const cards = Array.from(section.querySelectorAll('[data-platform-key]'));
    const hasVisible = cards.some(card => !card.classList.contains('generated-post-card--hidden'));
    const emptyEl = section.querySelector('[data-day-empty]');
    if (emptyEl) {
      emptyEl.classList.toggle('hidden', hasVisible);
    }
    section.classList.toggle('is-filter-empty', !hasVisible);
  });
}

function loadPublishingQueueFromStorage() {
  if (typeof localStorage === 'undefined') return;
  const queueState = getPublishingQueueState();
  if (!queueState) return;
  try {
    const raw = localStorage.getItem(PUBLISHING_QUEUE_STORAGE_KEY);
    if (!raw) return;
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      queueState.entries = parsed.map(normalizeQueueEntry).filter(Boolean);
    }
  } catch (error) {
    /* ignore */
  }
}

function persistPublishingQueue() {
  if (typeof localStorage === 'undefined') return;
  const queueState = getPublishingQueueState();
  if (!queueState || !queueState.entries) return;
  try {
    localStorage.setItem(PUBLISHING_QUEUE_STORAGE_KEY, JSON.stringify(queueState.entries));
  } catch (error) {
    /* ignore */
  }
}

function normalizeQueueEntry(entry = {}) {
  if (!entry || typeof entry !== 'object') return null;
  const normalizedPlatform = normalizePlatformKey(entry.platform || DEFAULT_GENERATOR_PLATFORM);
  return {
    key: entry.key || '',
    platform: normalizedPlatform,
    platformLabel: entry.platformLabel || formatPlatformLabel(normalizedPlatform),
    day: entry.day || 0,
    pillar: entry.pillar || '',
    caption: entry.caption || '',
    status: entry.status || 'draft',
    scheduledAt: entry.scheduledAt || null,
    lastUpdated: entry.lastUpdated || Date.now(),
    error: entry.error || '',
    timezoneLabel: entry.timezoneLabel || getTimezoneLabel()
  };
}

function ensureQueueEntryForPost(post = {}) {
  const queueState = getPublishingQueueState();
  if (!queueState || !queueState.entries) return null;
  const key = buildQueueKey(post);
  let existing = findQueueEntry(key);
  if (existing) return existing;
  const created = buildQueueEntryFromPost(post, key);
  queueState.entries.push(created);
  persistPublishingQueue();
  return created;
}

function buildQueueEntryFromPost(post = {}, keyOverride = null) {
  const key = keyOverride || buildQueueKey(post);
  const platform = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
  return normalizeQueueEntry({
    key,
    platform,
    platformLabel: formatPlatformLabel(platform),
    day: post.day_index || 0,
    pillar: post.pillar || '',
    caption: post.caption || '',
    status: 'draft',
    scheduledAt: null,
    lastUpdated: Date.now()
  });
}

function buildQueueKey(post = {}) {
  const platform = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
  const day = post.day_index || 0;
  const captionHash = hashCaption(post.caption || '');
  return `${day}-${platform}-${captionHash}`;
}

function hashCaption(value = '') {
  let hash = 0;
  for (let i = 0; i < value.length; i += 1) {
    hash = (hash * 31 + value.charCodeAt(i)) >>> 0;
  }
  return hash.toString(16);
}

function updatePublishingQueueEntry(key, updates = {}) {
  if (!key) return null;
  const existing = findQueueEntry(key);
  if (!existing) return null;
  Object.assign(existing, updates, {
    lastUpdated: updates.lastUpdated || Date.now(),
    timezoneLabel: existing.timezoneLabel || getTimezoneLabel()
  });
  persistPublishingQueue();
  return existing;
}

function findQueueEntry(key) {
  const queueState = getPublishingQueueState();
  if (!queueState || !queueState.entries) return null;
  return queueState.entries.find(entry => entry.key === key);
}

function renderPublishingQueue() {
  const wrap = document.getElementById('publishing-queue');
  const list = document.getElementById('publishing-queue-list');
  const empty = document.getElementById('publishing-queue-empty');
  if (!wrap || !list || !empty) return;
  
  const queueState = getPublishingQueueState();
  
  // Safety: If queue state is completely unavailable, show empty state with message
  if (!queueState || !queueState.entries) {
    list.innerHTML = '';
    empty.textContent = queueState ? 'No scheduled items yet' : 'Queue unavailable';
    empty.classList.remove('hidden');
    wrap.classList.add('hidden'); // Hide wrapper for consistency
    return;
  }

  list.innerHTML = '';
  if (!queueState.entries.length) {
    wrap.classList.add('hidden');
    empty.classList.remove('hidden');
    // Restore default message
    empty.textContent = 'Use "Publish now" or "Schedule" on any card to add it to the queue.';
    return;
  }

  wrap.classList.remove('hidden');
  empty.classList.add('hidden');

  const sorted = [...queueState.entries].sort((a, b) => (b.lastUpdated || 0) - (a.lastUpdated || 0));
  sorted.forEach(entry => list.appendChild(renderQueueItem(entry)));
}

function renderQueueItem(entry) {
  const item = document.createElement('div');
  item.className = 'border border-slate-200 rounded-xl p-4 bg-white/80 flex flex-col gap-2';

  const header = document.createElement('div');
  header.className = 'flex flex-wrap items-center justify-between gap-3';

  const left = document.createElement('div');
  left.className = 'flex items-center gap-2';
  const badge = document.createElement('span');
  badge.className = `text-[11px] font-semibold px-2 py-1 rounded-full border ${queueStatusClass(entry.status)}`;
  badge.textContent = formatQueueStatusLabel(entry.status);
  const label = document.createElement('div');
  label.className = 'text-sm text-slate-700';
  label.textContent = `${entry.platformLabel || formatPlatformLabel(entry.platform)} • Day ${entry.day || 0}`;

  const detail = document.createElement('div');
  detail.className = 'text-xs text-slate-500';
  detail.textContent = formatQueueDetail(entry);

  left.appendChild(badge);
  left.appendChild(label);

  const actions = document.createElement('div');
  actions.className = 'flex items-center gap-2';

  const retry = document.createElement('button');
  retry.type = 'button';
  retry.className = `btn-secondary btn-xs ${entry.status === 'failed' ? '' : 'hidden'}`;
  retry.textContent = 'Retry publish';
  retry.addEventListener('click', () => {
    const updated = updatePublishingQueueEntry(entry.key, {
      status: entry.scheduledAt ? 'scheduled' : 'published',
      error: '',
      lastUpdated: Date.now()
    });
    renderPublishingQueue();
    applyQueueStatusToCards(updated);
    showToast('Retry saved to the queue.');
  });

  const copyBtn = document.createElement('button');
  copyBtn.type = 'button';
  copyBtn.className = 'btn-ghost btn-xs';
  copyBtn.textContent = 'Copy text';
  copyBtn.addEventListener('click', async () => {
    const ok = await copyToClipboard(entry.caption || '');
    if (ok) {
      showToast('Copied caption from queue');
    } else {
      showToast('Clipboard unavailable — you can still select the text.');
    }
  });

  actions.appendChild(copyBtn);
  actions.appendChild(retry);

  header.appendChild(left);
  header.appendChild(actions);

  const body = document.createElement('div');
  body.className = 'text-sm text-slate-600';
  const preview = (entry.caption || '').slice(0, 140) || 'No caption saved yet.';
  body.textContent = preview;

  item.appendChild(header);
  item.appendChild(detail);
  item.appendChild(body);

  return item;
}

function queueStatusClass(status) {
  switch (status) {
    case 'published':
      return 'bg-emerald-50 text-emerald-700 border-emerald-200';
    case 'scheduled':
      return 'bg-blue-50 text-blue-700 border-blue-200';
    case 'failed':
      return 'bg-rose-50 text-rose-700 border-rose-200';
    default:
      return 'bg-slate-50 text-slate-700 border-slate-200';
  }
}

function formatQueueStatusLabel(status) {
  if (status === 'published') return 'Published';
  if (status === 'scheduled') return 'Scheduled';
  if (status === 'failed') return 'Failed';
  return 'Ready';
}

function formatQueueDetail(entry = {}) {
  if (entry.status === 'scheduled' && entry.scheduledAt) {
    return `Scheduled for ${formatScheduleLabel(entry.scheduledAt)}`;
  }
  if (entry.status === 'published') {
    return `Published ${formatRelativeTime(entry.lastUpdated || Date.now())}`;
  }
  if (entry.status === 'failed') {
    return entry.error || 'Needs attention';
  }
  return entry.pillar ? `Queued from ${entry.pillar}` : 'Queued from generator';
}

function formatScheduleLabel(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return '—';
  const tz = getTimezoneLabel();
  return `${date.toLocaleString([], { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}${tz ? ` (${tz})` : ''}`;
}

function formatDateTimeLocal(value) {
  const date = value instanceof Date ? value : new Date(value);
  if (Number.isNaN(date.getTime())) return '';
  const pad = n => String(n).padStart(2, '0');
  const yyyy = date.getFullYear();
  const mm = pad(date.getMonth() + 1);
  const dd = pad(date.getDate());
  const hh = pad(date.getHours());
  const mi = pad(date.getMinutes());
  return `${yyyy}-${mm}-${dd}T${hh}:${mi}`;
}

function formatTimezoneOffset(date = new Date()) {
  const offsetMinutes = date.getTimezoneOffset();
  const sign = offsetMinutes <= 0 ? '+' : '-';
  const abs = Math.abs(offsetMinutes);
  const hours = String(Math.floor(abs / 60)).padStart(2, '0');
  const minutes = String(abs % 60).padStart(2, '0');
  return `UTC${sign}${hours}:${minutes}`;
}

function getTimezoneLabel() {
  try {
    const { timeZone } = Intl.DateTimeFormat().resolvedOptions();
    return timeZone ? `${timeZone} (${formatTimezoneOffset()})` : '';
  } catch (error) {
    return '';
  }
}

function updateQueueTimezoneLabel() {
  const el = document.getElementById('queue-timezone');
  if (!el) return;
  el.textContent = getTimezoneLabel() || 'Timezone unavailable';
}

function syncQueueWithPosts(posts = []) {
  let changed = false;
  posts.forEach(post => {
    const entry = ensureQueueEntryForPost(post);
    if (entry && !entry.caption && post.caption) {
      entry.caption = post.caption;
      changed = true;
    }
  });
  if (changed) persistPublishingQueue();
}

function applyQueueStatusToCard(card, entry) {
  if (!card || !entry) return;
  const badge = card.querySelector(`[data-queue-badge="${entry.key}"]`);
  const note = card.querySelector(`[data-queue-note="${entry.key}"]`);
  if (badge) {
    badge.textContent = formatQueueStatusLabel(entry.status);
    badge.className = `text-[11px] font-semibold px-2 py-1 rounded-full border ${queueStatusClass(entry.status)}`;
  }
  if (note) {
    note.textContent = formatQueueDetail(entry);
  }
}

function applyQueueStatusToCards(entry) {
  if (!entry) return;
  const cards = Array.from(document.querySelectorAll(`[data-queue-key="${entry.key}"]`));
  cards.forEach(card => applyQueueStatusToCard(card, entry));
}

function formatRelativeTime(ts) {
  const diffMs = Date.now() - ts;
  const diffMinutes = Math.floor(diffMs / 60000);
  if (diffMinutes < 1) return 'just now';
  if (diffMinutes < 60) return `${diffMinutes} min ago`;
  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours} hr ago`;
  const diffDays = Math.floor(diffHours / 24);
  return `${diffDays} day${diffDays === 1 ? '' : 's'} ago`;
}

function buildPlatformMetadata(post = {}) {
  const normalized = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
  const limit = PLATFORM_CHARACTER_LIMITS[normalized] || 0;
  const caption = post.caption || '';
  const charCount = caption.length;
  const hashtags = extractHashtags(post) || [];
  const preview = (caption.split('\n')[0] || '').trim() || 'First line will show here.';
  return { limit, charCount, hashtags, preview, platform: normalized };
}

function extractHashtags(post = {}) {
  if (Array.isArray(post.hashtags) && post.hashtags.length) return post.hashtags;
  const caption = post.caption || '';
  const matches = caption.match(/#[\w-]+/g);
  return matches || [];
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

function hydrateActivityFeed() {
  const wrap = document.getElementById('activity-panel');
  if (!wrap) return;
  renderActivityTypeChips();
  populateActivityFilterSelects();
  bindActivityReset();
  renderActivityFeed();
}

function renderActivityTypeChips() {
  const wrap = document.getElementById('activity-type-filters');
  if (!wrap) return;
  wrap.innerHTML = '';
  Object.entries(ACTIVITY_TYPE_META).forEach(([key, meta]) => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.dataset.activityType = key;
    btn.className = 'activity-chip';
    btn.innerHTML = `<span class="activity-chip__icon">${meta.icon}</span><span>${meta.label}</span>`;
    btn.classList.toggle('activity-chip--active', activityFilterState.types.has(key));
    btn.setAttribute('aria-pressed', activityFilterState.types.has(key) ? 'true' : 'false');
    btn.addEventListener('click', () => {
      if (activityFilterState.types.has(key)) {
        activityFilterState.types.delete(key);
        btn.classList.remove('activity-chip--active');
      } else {
        activityFilterState.types.add(key);
        btn.classList.add('activity-chip--active');
      }
      renderActivityFeed();
    });
    wrap.appendChild(btn);
  });
}

function populateActivityFilterSelects() {
  const campaignSelect = document.getElementById('activity-campaign-filter');
  const assigneeSelect = document.getElementById('activity-assignee-filter');
  const campaigns = Array.from(new Set(activityEvents.map(evt => evt.campaign).filter(Boolean)));
  const assignees = Array.from(new Set(activityEvents.map(evt => evt.assignee).filter(Boolean)));

  if (campaignSelect) {
    campaignSelect.innerHTML = '<option value="all">All campaigns</option>' + campaigns.map(c => `<option value="${escapeAttr(c)}">${escapeHtml(c)}</option>`).join('');
    campaignSelect.value = activityFilterState.campaign;
    if (!campaignSelect.dataset.bound) {
      campaignSelect.addEventListener('change', () => {
        activityFilterState.campaign = campaignSelect.value;
        renderActivityFeed();
      });
      campaignSelect.dataset.bound = '1';
    }
  }

  if (assigneeSelect) {
    assigneeSelect.innerHTML = '<option value="all">All teammates</option>' + assignees.map(a => `<option value="${escapeAttr(a)}">${escapeHtml(a)}</option>`).join('');
    assigneeSelect.value = activityFilterState.assignee;
    if (!assigneeSelect.dataset.bound) {
      assigneeSelect.addEventListener('change', () => {
        activityFilterState.assignee = assigneeSelect.value;
        renderActivityFeed();
      });
      assigneeSelect.dataset.bound = '1';
    }
  }
}

function bindActivityReset() {
  const btn = document.getElementById('activity-reset');
  if (!btn) return;
  btn.addEventListener('click', () => {
    activityFilterState.types = new Set(Object.keys(ACTIVITY_TYPE_META));
    activityFilterState.campaign = 'all';
    activityFilterState.assignee = 'all';
    syncActivitySelects();
    renderActivityTypeChips();
    renderActivityFeed();
  });
}

function syncActivitySelects() {
  const campaignSelect = document.getElementById('activity-campaign-filter');
  const assigneeSelect = document.getElementById('activity-assignee-filter');
  if (campaignSelect) campaignSelect.value = activityFilterState.campaign;
  if (assigneeSelect) assigneeSelect.value = activityFilterState.assignee;
}

function renderActivityFeed() {
  const list = document.getElementById('activity-feed');
  const empty = document.getElementById('activity-empty');
  if (!list) return;
  list.innerHTML = '';
  const filtered = activityEvents.filter(evt => {
    if (activityFilterState.types.size && !activityFilterState.types.has(evt.type)) return false;
    if (activityFilterState.campaign !== 'all' && evt.campaign !== activityFilterState.campaign) return false;
    if (activityFilterState.assignee !== 'all' && evt.assignee !== activityFilterState.assignee) return false;
    return true;
  });

  filtered.forEach(evt => {
    list.appendChild(buildActivityItem(evt));
  });

  if (empty) {
    empty.classList.toggle('hidden', filtered.length > 0);
  }
}

function buildActivityItem(evt) {
  const meta = ACTIVITY_TYPE_META[evt.type] || { label: 'Update', icon: '•', color: 'slate' };
  const item = document.createElement('article');
  item.className = 'activity-item';
  const role = evt.actor?.role ? `<span class="activity-role">${escapeHtml(evt.actor.role)}</span>` : '';
  const needsInput = evt.status === 'draft' && evt.needsInputFrom ? `<span class="needs-input-pill">Needs input from ${escapeHtml(evt.needsInputFrom)}</span>` : '';
  const campaignTag = evt.campaign ? `<span class="activity-pill">${escapeHtml(evt.campaign)}</span>` : '';
  const assigneeTag = evt.assignee ? `<span class="activity-pill">Assignee: ${escapeHtml(evt.assignee)}</span>` : '';
  const platforms = Array.isArray(evt.platforms) && evt.platforms.length ? `<div class="activity-platforms">${evt.platforms.map(p => escapeHtml(formatPlatformLabel(p))).join(' • ')}</div>` : '';
  item.innerHTML = `
    <div class="activity-item__header">
      <span class="activity-type-badge activity-type-${meta.color}">${escapeHtml(meta.icon)} ${escapeHtml(meta.label)}</span>
      <span class="activity-time">${escapeHtml(evt.time || '')}</span>
    </div>
    <div class="activity-item__body">
      <div class="activity-avatar" aria-hidden="true">${escapeHtml(getInitials(evt.actor?.name))}</div>
      <div class="activity-item__content">
        <div class="activity-item__title">${escapeHtml(evt.title || 'Untitled update')}</div>
        <div class="activity-item__meta">
          <span class="activity-actor">${escapeHtml(evt.actor?.name || 'Unassigned')}</span>
          ${role}
          ${campaignTag}
          ${assigneeTag}
          ${needsInput}
        </div>
        <p class="activity-item__summary">${escapeHtml(evt.summary || '')}</p>
        ${platforms}
      </div>
    </div>
  `;
  return item;
}

function getInitials(name = '') {
  const parts = String(name || '').trim().split(/\s+/).filter(Boolean);
  if (!parts.length) return '•';
  const first = parts[0].charAt(0) || '';
  const last = parts.length > 1 ? parts[parts.length - 1].charAt(0) : '';
  return (first + last).toUpperCase();
}

// Render generated posts with enhanced features
function renderPosts(data) {
  const posts = data.posts || [];
  const resultsDiv = document.getElementById('content-results');
  resultsDiv.innerHTML = '';

  if (!posts.length) {
    resultsDiv.innerHTML = `<div class="text-sm text-slate-600">No posts yet.</div>`;
    renderGeneratedFilters([]);
    return;
  }

  // Check if response is in post-ready format (SocialPostCard)
  // If so, use the copy-first renderer
  if (window.SocialCopyFirstRenderer && window.SocialCopyFirstRenderer.isPostReadyFormat(data)) {
    window.SocialCopyFirstRenderer.renderSocialPostCards(posts, resultsDiv);
    
    // Still render the publishing queue for compatibility
    syncQueueWithPosts(posts);
    renderPublishingQueue();
    setupQueueToggle();
    
    // Display generation timestamp
    updateGenerationTimestamp();
    
    return;
  }

  // Otherwise use legacy renderer (existing code below)
  syncQueueWithPosts(posts);
  renderPublishingQueue();

  // Group posts by day
  const byDay = posts.reduce((acc, post) => {
    (acc[post.day_index] ||= []).push(post);
    return acc;
  }, {});

  const sortedDays = Object.keys(byDay).sort((a, b) => +a - +b);
  const platformMetaMap = new Map();
  posts.forEach(post => {
    const key = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
    if (!key || platformMetaMap.has(key)) return;
    platformMetaMap.set(key, formatPlatformLabel(key));
  });
  const platforms = Array.from(platformMetaMap.entries()).map(([key, label]) => ({ key, label }));
  ensureGeneratedViewPrefsLoaded();
  resetHiddenPlatformsFor(platforms);
  renderGeneratedFilters(platforms);

  sortedDays.forEach(day => {
    const dayPosts = byDay[day];
    const section = document.createElement('section');
    section.className = 'generated-day mb-8';
    section.dataset.daySection = day;

  const firstPost = dayPosts[0];
  const collapsed = isDayCollapsed(day);
    const header = document.createElement('div');
    header.className = 'generated-day__header';

    const titleWrap = document.createElement('div');
    titleWrap.className = 'generated-day__title-wrap';
    const heading = document.createElement('h4');
    heading.className = 'generated-day__title';
    const dateLabel = firstPost.date ? ` • ${firstPost.date}` : '';
    heading.textContent = `Day ${day}${dateLabel}`;
    const pillarBadge = document.createElement('span');
  pillarBadge.className = 'generated-day__pillar';
  pillarBadge.textContent = firstPost.pillar || 'Content';
    titleWrap.appendChild(heading);
    titleWrap.appendChild(pillarBadge);

    const headerActions = document.createElement('div');
    headerActions.className = 'generated-day__header-actions';
    const platformCount = document.createElement('span');
    platformCount.className = 'generated-day__platform-count';
    platformCount.textContent = `${dayPosts.length} platform${dayPosts.length === 1 ? '' : 's'}`;
    const toggleBtn = document.createElement('button');
    toggleBtn.type = 'button';
    toggleBtn.className = 'generated-day__toggle';
    toggleBtn.dataset.dayToggle = day;
  toggleBtn.setAttribute('aria-expanded', collapsed ? 'false' : 'true');
  toggleBtn.setAttribute('aria-label', collapsed ? 'Expand day' : 'Collapse day');
    toggleBtn.innerHTML = '<span class="generated-day__chevron" aria-hidden="true">▾</span>';
    toggleBtn.addEventListener('click', () => handleDayToggle(day, section));
    headerActions.appendChild(platformCount);
    headerActions.appendChild(toggleBtn);

    header.appendChild(titleWrap);
    header.appendChild(headerActions);

    const body = document.createElement('div');
    body.className = 'generated-day__body space-y-4';
    const postsWrap = document.createElement('div');
    postsWrap.className = 'generated-day__posts space-y-4';

    dayPosts.forEach(post => {
      const card = renderPostCard(post);
      card.dataset.platformKey = String(post.platform || '').toLowerCase();
      card.dataset.day = day;
      card.classList.add('generated-post-card');
      postsWrap.appendChild(card);
    });

    const emptyState = document.createElement('div');
    emptyState.className = 'generated-day__empty hidden';
    emptyState.dataset.dayEmpty = '';
    emptyState.textContent = 'No posts for the selected platforms.';

    body.appendChild(postsWrap);
    body.appendChild(emptyState);

  section.appendChild(header);
  section.appendChild(body);
  applyDayCollapse(section, collapsed);

    resultsDiv.appendChild(section);
  });

  applyPlatformFilters();
  
  // Set up queue toggle functionality
  setupQueueToggle();
  
  // Set up toolbar filter toggle (collapsed by default for 1-day plans)
  setupToolbarFilterToggle(data);
  
  // Display generation timestamp
  updateGenerationTimestamp();
}

function setupQueueToggle() {
  const toggleBtn = document.getElementById('toggle-queue');
  const queueContent = document.getElementById('queue-content');
  const toggleIcon = document.getElementById('queue-toggle-icon');
  const toggleText = document.getElementById('queue-toggle-text');
  
  if (!toggleBtn || !queueContent) return;
  
  // Start collapsed by default
  const isExpanded = localStorage.getItem('queue-expanded') === 'true';
  if (isExpanded) {
    queueContent.classList.remove('hidden');
    toggleIcon.textContent = '▾';
    toggleText.textContent = 'Hide queue';
    toggleBtn.setAttribute('aria-expanded', 'true');
  }
  
  toggleBtn.addEventListener('click', () => {
    const nowExpanded = queueContent.classList.toggle('hidden');
    const expanded = !nowExpanded;
    toggleIcon.textContent = expanded ? '▾' : '▸';
    toggleText.textContent = expanded ? 'Hide queue' : 'Show queue';
    toggleBtn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
    localStorage.setItem('queue-expanded', expanded ? 'true' : 'false');
  });
}

function setupToolbarFilterToggle(data) {
  const toolbar = document.getElementById('generated-toolbar');
  const toggleBtn = document.getElementById('toggle-toolbar-filters');
  const filtersContent = document.getElementById('toolbar-filters-content');
  const toggleIcon = document.getElementById('toolbar-toggle-icon');
  
  if (!toggleBtn || !filtersContent || !toolbar) return;
  
  // For 1-day plans, start collapsed by default
  const planLength = (data && data.days) || lastPlanLength || 1;
  const shouldStartCollapsed = planLength === 1;
  
  const savedState = localStorage.getItem('toolbar-filters-expanded');
  const isExpanded = savedState !== null ? savedState === 'true' : !shouldStartCollapsed;
  
  if (!isExpanded) {
    filtersContent.classList.add('hidden');
    toggleIcon.textContent = '▸';
  } else {
    filtersContent.classList.remove('hidden');
    toggleIcon.textContent = '▾';
  }
  
  toggleBtn.addEventListener('click', () => {
    const nowHidden = filtersContent.classList.toggle('hidden');
    const expanded = !nowHidden;
    toggleIcon.textContent = expanded ? '▾' : '▸';
    localStorage.setItem('toolbar-filters-expanded', expanded ? 'true' : 'false');
  });
}

function updateGenerationTimestamp() {
  const timestampEl = document.getElementById('generation-timestamp');
  if (!timestampEl) return;
  
  const now = new Date();
  const timeStr = now.toLocaleTimeString([], { hour: 'numeric', minute: '2-digit' });
  timestampEl.textContent = `Generated just now (${timeStr})`;
  
  // Store timestamp in localStorage for persistence
  localStorage.setItem('last-generation-time', now.toISOString());
}

function buildPostSnapshot(post = {}) {
  const lines = [];
  const platformKey = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
  const platformLabel = formatPlatformLabel(platformKey);
  lines.push(`Platform: ${platformLabel || 'Unknown'}`);
  if (post.pillar) lines.push(`Pillar: ${post.pillar}`);
  if (post.day_index) lines.push(`Day: ${post.day_index}`);
  if (post.image_prompt) lines.push(`Image prompt: ${post.image_prompt}`);
  lines.push('');
  lines.push('Caption:');
  lines.push(post.caption || '(empty)');
  if (post.reel) {
    const reel = post.reel;
    lines.push('');
    if (reel.hook) lines.push(`Reel hook: ${reel.hook}`);
    const beats = reel.script_beats || reel.scriptBeats || reel.script || [];
    if (beats.length) {
      lines.push('Reel beats:');
      beats.forEach((beat, idx) => lines.push(`${idx + 1}. ${beat}`));
    }
    if (reel.thumbnail_prompt) lines.push(`Thumbnail: ${reel.thumbnail_prompt}`);
    if (reel.srt_prompt) lines.push(`SRT prompt: ${reel.srt_prompt}`);
  }
  if (post.variants) {
    lines.push('');
    lines.push('Platform variants:');
    Object.keys(post.variants).forEach(key => {
      lines.push(`- ${formatPlatformLabel(key)}:`);
      const entry = normalizeVariantPayload(post.variants[key]);
      lines.push(entry.text || '');
    });
  }
  return lines.join('\n');
}

function normalizeVariantPayload(entry) {
  if (!entry) return { text: '', warnings: [] };
  if (typeof entry === 'string') return { text: entry, warnings: [] };
  return {
    text: entry.text || '',
    warnings: Array.isArray(entry.warnings) ? entry.warnings : [],
    cta: entry.cta || '',
    thumbnail_note: entry.thumbnail_note || '',
    platform: entry.platform || '',
    platform_label: entry.platform_label || formatPlatformLabel(entry.platform || '')
  };
}

function buildPostSummary(post = {}) {
  const platformKey = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
  const platformLabel = formatPlatformLabel(platformKey);
  const day = post.day_index ? `day ${post.day_index}` : '';
  const pillar = post.pillar ? ` • ${post.pillar}` : '';
  const firstLine = (post.caption || '').split('\n')[0].trim();
  const snippet = firstLine.length > 60 ? `${firstLine.slice(0, 57)}…` : firstLine;
  return `${platformLabel} ${day}`.trim() + (pillar || '') + (snippet ? ` • ${snippet}` : '');
}

function renderWarningList(warnings) {
  if (!warnings || !warnings.length) return '';
  return `<div class="flex flex-col gap-1 my-2">${warnings.map(note => `<div class=\"flex items-center gap-2 text-xs text-amber-800 bg-amber-50 border border-amber-200 rounded-lg px-3 py-2\"><span aria-hidden=\"true\">⚠️</span><span>${escapeHtml(note)}</span></div>`).join('')}</div>`;
}

// Render individual post card with enhanced features
function renderPostCard(post) {
  const card = document.createElement('div');
  card.className = 'card border rounded-lg p-4 mt-3 bg-white';
  card.__feedbackSnapshot = buildPostSnapshot(post);
  card.__feedbackSummary = buildPostSummary(post);

  // Platform-specific styling
  const platformColors = {
    instagram: 'from-pink-500 to-purple-500',
    facebook: 'from-blue-600 to-blue-800',
    linkedin: 'from-blue-700 to-blue-900',
    twitter: 'from-sky-500 to-sky-600',
    tiktok: 'from-black to-gray-800',
    short_video: 'from-purple-600 to-pink-500'
  };

  const platformKey = normalizePlatformKey(post.platform || DEFAULT_GENERATOR_PLATFORM);
  const platformColor = platformColors[platformKey] || 'from-gray-500 to-gray-600';
  const editorId = `post-editor-${post.day_index}-${platformKey}-${Math.random().toString(36).slice(2,7)}`;
  const stampId = `${editorId}-stamp`;
  const variantsMarkup = post.variants ? renderPlatformVariants(post.variants, post.platform) : '';
  const voiceScore = typeof post.voice_match_score === 'number' ? post.voice_match_score : null;
  const guardrail = post.voice_guardrail || '';
  const voiceSuggestions = Array.isArray(post.voice_suggestions) ? post.voice_suggestions : [];
  const guardrailBlock = guardrail
    ? `<div class="p-3 mb-3 bg-amber-50 border border-amber-200 rounded">
        <p class="text-xs font-semibold text-amber-900">${escapeHtml(guardrail)}</p>
        ${voiceSuggestions.map(s => `<p class="text-xs text-amber-800 mt-1">${escapeHtml(s)}</p>`).join('')}
      </div>`
    : '';
  const voiceScoreBlock = voiceScore !== null
    ? `<div class="text-xs text-slate-500 mb-1">Voice match: ${(voiceScore * 100).toFixed(0)}%</div>`
    : '';
  const warningMarkup = renderWarningList(post.warnings);

  // Check if this post has variants (multiple platforms)
  const hasVariants = post.variants && Object.keys(post.variants).length > 1;
  const queueEntry = ensureQueueEntryForPost(post);
  const metadata = buildPlatformMetadata(post);
  const queueStatus = queueStatusClass(queueEntry.status);
  const fallbackStampId = `${stampId}-fallback`;

  card.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-gradient-to-r ${platformColor} rounded-full flex items-center justify-center">
          <span class="text-white text-xs font-bold">${(platformKey.charAt(0) || 'S').toUpperCase()}</span>
        </div>
        <span class="font-medium text-slate-900">${formatPlatformLabel(platformKey)}</span>
        ${hasVariants ? '<span class="text-xs text-purple-600 font-medium">• Multi-platform</span>' : ''}
      </div>
      <button class="btn-primary text-sm py-2 px-4" data-copy-target="${editorId}" data-stamp-target="${stampId}">📋 Copy</button>
    </div>

    <div class="flex gap-2 mb-3">
      <span id="${stampId}" class="copy-timestamp text-xs text-slate-500"></span>
      <div class="ml-auto flex gap-2">
        <button class="btn-ghost text-xs" data-like="1" data-day="${post.day_index}" data-platform="${post.platform}">👍</button>
        <button class="btn-ghost text-xs" data-like="-1" data-day="${post.day_index}" data-platform="${post.platform}">👎</button>
      </div>
    </div>

    ${post.image_url ? `<img class="w-full h-32 object-cover rounded mb-3" src="${post.image_url}" alt="Suggested image" />` : ''}

    ${voiceScoreBlock}
    ${guardrailBlock}

    <div class="text-xs text-slate-500 mb-2"><strong>Image prompt:</strong> ${escapeHtml(post.image_prompt)}</div>

    <label class="text-xs font-semibold text-slate-500 tracking-wide">Caption</label>
    ${warningMarkup}
    <textarea id="${editorId}" class="post-editor mb-3" data-platform="${post.platform}">${escapeHtml(post.caption)}</textarea>

    ${post.reel ? renderReelSection(post.reel) : ''}

    ${hasVariants ? variantsMarkup : ''}

    <div class="flex flex-wrap gap-2 mt-3">
      <button class="btn-ghost btn-sm" data-generate-variants>Generate variants</button>
      <button class="btn-ghost btn-sm" data-regenerate-hook>Regenerate hook</button>
      <button class="btn-ghost btn-sm" data-regenerate-cta>Regenerate CTA</button>
    </div>
    <div class="grid md:grid-cols-3 gap-3 mt-2 hidden" data-variant-wrap></div>
    <div class="bg-slate-50 border border-slate-200 rounded-xl p-3 mt-3" data-quality-hints></div>
  `;

  card.querySelectorAll('textarea.post-editor').forEach(area => {
    const scheduleResize = () => autoSizeEditor(area);
    if (typeof requestAnimationFrame === 'function') {
      requestAnimationFrame(scheduleResize);
    } else {
      setTimeout(scheduleResize, 0);
    }
    area.addEventListener('input', () => {
      autoSizeEditor(area);
      clearCopyState(area, card);
    });
  });

  const editor = card.querySelector(`#${editorId}`);
  const qualityWrap = card.querySelector('[data-quality-hints]');
  if (editor && qualityWrap) {
    renderQualityHints(qualityWrap, editor, post, card);
    editor.addEventListener('input', () => renderQualityHints(qualityWrap, editor, post, card));
  }

  const variantsWrap = card.querySelector('[data-variant-wrap]');
  const variantBtn = card.querySelector('[data-generate-variants]');
  if (variantBtn && editor) {
    variantBtn.addEventListener('click', () => handleGenerateVariants(post, card, editor, variantsWrap));
  }
  const hookBtn = card.querySelector('[data-regenerate-hook]');
  if (hookBtn && editor) {
    hookBtn.addEventListener('click', () => {
      editor.value = regenerateHookText(editor.value, post);
      autoSizeEditor(editor);
      clearCopyState(editor, card);
      if (qualityWrap) renderQualityHints(qualityWrap, editor, post, card);
    });
  }
  const ctaBtn = card.querySelector('[data-regenerate-cta]');
  if (ctaBtn && editor) {
    ctaBtn.addEventListener('click', () => {
      editor.value = regenerateCtaText(editor.value, post);
      autoSizeEditor(editor);
      clearCopyState(editor, card);
      if (qualityWrap) renderQualityHints(qualityWrap, editor, post, card);
    });
  }

  card.querySelectorAll('[data-copy-target], [data-copy-text]').forEach(btn => {
    const targetId = btn.getAttribute('data-copy-target');
    const stampTarget = btn.getAttribute('data-stamp-target');
    const targetEditor = targetId ? card.querySelector(`#${targetId}`) : null;
    const stampEl = stampTarget ? card.querySelector(`#${stampTarget}`) : null;
    bindCopyButton(btn, targetEditor, stampEl, card);
  });

  card.querySelectorAll('[data-download-ref]').forEach(btn => {
    bindDownloadButton(btn, card);
  });
  card.querySelectorAll('[data-export-variants]').forEach(btn => {
    btn.addEventListener('click', async () => {
      const chunks = [];
      card.querySelectorAll('[data-variant-text]').forEach(area => {
        const platform = area.getAttribute('data-variant-platform') || 'Platform';
        const label = formatPlatformLabel(platform) || platform;
        chunks.push(`${label}:\n${area.value.trim()}`);
      });
      const exportText = chunks.join('\n\n');
      try {
        await navigator.clipboard.writeText(exportText);
        showToast('Copied all variants to clipboard');
      } catch (err) {
        console.error('Failed to export variants', err);
        showToast('Unable to copy variants right now.');
      }
    });
  });

  card.querySelectorAll('[data-like]').forEach(btn => {
    btn.addEventListener('click', async () => {
      if (btn.disabled) return;
      const rating = +btn.getAttribute('data-like');
      const post_day = +btn.getAttribute('data-day') || 0;
      const platform = btn.getAttribute('data-platform') || '';
      let note = '';
      if (rating < 0 && typeof requestFeedbackNote === 'function') {
        note = await requestFeedbackNote({
          platform,
          post_day,
          source: 'dashboard',
          captionPreview: card.__feedbackSummary || ''
        });
        if (note === null) {
          return;
        }
      }
      const ok = await submitFeedback({
        rating,
        postDay: post_day,
        platform,
        note,
        source: 'dashboard',
        planLength: getCurrentPlanLength(),
        postSnapshot: card.__feedbackSnapshot,
        summary: card.__feedbackSummary
      });
      if (ok) {
        finalizeFeedbackButtons(card, platform, post_day, rating);
      }
    });
  });

  card.dataset.queueKey = queueEntry.key;
  wirePublishingControls(card, queueEntry, editorId);
  applyQueueStatusToCard(card, queueEntry);

  return card;
}

function wirePublishingControls(card, queueEntry, editorId) {
  const publishBtn = card.querySelector(`[data-publish-now="${queueEntry.key}"]`);
  const scheduleBtn = card.querySelector(`[data-schedule-btn="${queueEntry.key}"]`);
  const retryBtn = card.querySelector(`[data-retry-btn="${queueEntry.key}"]`);
  const scheduleInput = card.querySelector(`[data-schedule-input="${queueEntry.key}"]`);
  const editor = card.querySelector(`#${editorId}`);

  if (scheduleInput && !scheduleInput.value) {
    const defaultDate = queueEntry.scheduledAt ? new Date(queueEntry.scheduledAt) : new Date(Date.now() + 60 * 60 * 1000);
    scheduleInput.value = formatDateTimeLocal(defaultDate);
  }

  const refreshStatus = (entry) => {
    if (!entry) return;
    applyQueueStatusToCard(card, entry);
    if (retryBtn) retryBtn.classList.toggle('hidden', entry.status !== 'failed');
    renderPublishingQueue();
  };

  publishBtn?.addEventListener('click', () => {
    const updated = updatePublishingQueueEntry(queueEntry.key, {
      status: 'published',
      scheduledAt: new Date().toISOString(),
      caption: editor?.value || queueEntry.caption,
      error: ''
    });
    refreshStatus(updated);
    showToast('Marked as published in your queue.');
  });

  scheduleBtn?.addEventListener('click', () => {
    const value = scheduleInput?.value;
    if (!value) {
      const failed = updatePublishingQueueEntry(queueEntry.key, { status: 'failed', error: 'Add a schedule time to continue.' });
      refreshStatus(failed);
      showToast('Add a schedule time before scheduling.');
      return;
    }
    const scheduledDate = new Date(value);
    if (Number.isNaN(scheduledDate.getTime()) || scheduledDate.getTime() < Date.now()) {
      const failed = updatePublishingQueueEntry(queueEntry.key, { status: 'failed', error: 'Pick a time in the future.' });
      refreshStatus(failed);
      showToast('Pick a time in the future.');
      return;
    }
    const updated = updatePublishingQueueEntry(queueEntry.key, {
      status: 'scheduled',
      scheduledAt: scheduledDate.toISOString(),
      caption: editor?.value || queueEntry.caption,
      error: ''
    });
    refreshStatus(updated);
    showToast('Scheduled from this card.');
  });

  retryBtn?.addEventListener('click', () => {
    const fallbackDate = scheduleInput?.value ? new Date(scheduleInput.value) : new Date();
    const status = scheduleInput?.value ? 'scheduled' : 'published';
    const updated = updatePublishingQueueEntry(queueEntry.key, {
      status,
      scheduledAt: fallbackDate.toISOString(),
      caption: editor?.value || queueEntry.caption,
      error: ''
    });
    refreshStatus(updated);
    showToast('Retry saved.');
  });

  editor?.addEventListener('blur', () => {
    updatePublishingQueueEntry(queueEntry.key, { caption: editor.value });
    renderPublishingQueue();
  });
}

// Render reel section for video content
function renderReelSection(reel) {
  if (!reel) return '';

  const hook = reel.hook || (reel.ranked_hooks && reel.ranked_hooks[0]) || '';
  const rawScript = reel.script_beats || reel.scriptBeats || reel.script || [];
  const scriptArr = Array.isArray(rawScript) ? rawScript : (rawScript ? [rawScript] : []);
  const scriptTextParts = [];
  if (hook) scriptTextParts.push(hook);
  if (hook && scriptArr.length) scriptTextParts.push('');
  scriptArr.forEach(beat => scriptTextParts.push(beat));
  const scriptText = scriptTextParts.join('\n');
  const srtText = reel.srt_prompt || reel.srt || '';
  const thumbText = reel.thumbnail_prompt || reel.thumbnail || '';
  const overlays = Array.isArray(reel.caption_overlays) ? reel.caption_overlays : [];
  const broll = Array.isArray(reel.broll_suggestions) ? reel.broll_suggestions : [];
  const shootList = Array.isArray(reel.shoot_list) ? reel.shoot_list : [];
  const firstFrame = reel.first_frame_idea || '';
  const engagementPrompts = Array.isArray(reel.engagement_prompts) ? reel.engagement_prompts : [];
  const postingChecklist = Array.isArray(reel.posting_checklist) ? reel.posting_checklist : [];
  const loopHint = reel.looping_hint || '';
  const platformSpecs = Array.isArray(reel.platform_specs) ? reel.platform_specs : [];
  const formatSpecChip = (spec = {}) => {
    const name = formatPlatformLabel(spec.platform || '') || (spec.platform || '').replace('_', ' ');
    const ratio = spec.aspect_ratio || '';
    const safeChars = spec.title_safe_chars || spec.safe_title_chars;
    const note = spec.note || '';
    const safeLabel = safeChars ? ` • title ≤ ${safeChars} chars` : '';
    return `<div class="px-2 py-1 bg-slate-100 rounded-full text-[11px] text-slate-700 border border-slate-200">${escapeHtml(name)}${ratio ? `: ${escapeHtml(ratio)}` : ''}${safeLabel}${note ? ` • ${escapeHtml(note)}` : ''}</div>`;
  };
  const thumbnailIdeas = Array.isArray(reel.thumbnail_title_ideas) ? reel.thumbnail_title_ideas : [];
  const exportsCsv = reel.shoot_list_exports && reel.shoot_list_exports.csv;
  const exportsPdf = reel.shoot_list_exports && reel.shoot_list_exports.pdf_text;

  const stampScript = `reel-stamp-script-${Math.random().toString(36).slice(2,8)}`;
  const stampSrt = `reel-stamp-srt-${Math.random().toString(36).slice(2,8)}`;
  const stampThumb = `reel-stamp-thumb-${Math.random().toString(36).slice(2,8)}`;
  const exportCsvId = `shoot-csv-${Math.random().toString(36).slice(2,8)}`;
  const exportPdfId = `shoot-pdf-${Math.random().toString(36).slice(2,8)}`;

  const reelMeta = [
    reel.length_seconds ? `${reel.length_seconds}s` : null,
    reel.style || ''
  ].filter(Boolean).join(' • ');

  return `
    <div class="mt-3 p-3 bg-slate-50 rounded border-l-4 border-purple-400">
      <div class="flex items-center gap-2 mb-2">
        <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
        </svg>
        <span class="text-sm font-medium text-purple-900">Reel Plan</span>
        ${reelMeta ? `<span class="text-xs text-purple-600">(${escapeHtml(reelMeta)})</span>` : ''}
      </div>

      <div class="text-sm mb-2"><strong>Hook:</strong> ${escapeHtml(hook)}</div>

      ${firstFrame ? `<div class="text-xs text-slate-700 mb-2"><span class="font-semibold text-slate-800">First frame:</span> ${escapeHtml(firstFrame)}</div>` : ''}

      <div class="text-sm mb-2"><strong>Script:</strong>
        <ol class="list-decimal ml-5 text-xs text-slate-700">
          ${scriptArr.map(beat => `<li>${escapeHtml(beat)}</li>`).join('')}
        </ol>
      </div>

      <div class="flex flex-wrap gap-4 items-center mt-2">
        <div class="flex items-center gap-2">
          <button class="btn-ghost text-xs" data-copy-text="${escapeAttr(scriptText)}" data-stamp-target="${stampScript}">Copy Script</button>
          <span id="${stampScript}" class="copy-timestamp"></span>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-ghost text-xs" data-copy-text="${escapeAttr(srtText)}" data-stamp-target="${stampSrt}">Copy SRT</button>
          <span id="${stampSrt}" class="copy-timestamp"></span>
        </div>
        <div class="flex items-center gap-2">
          <button class="btn-ghost text-xs" data-copy-text="${escapeAttr(thumbText)}" data-stamp-target="${stampThumb}">Copy Thumbnail</button>
          <span id="${stampThumb}" class="copy-timestamp"></span>
        </div>
      </div>

      ${overlays.length ? `
        <div class="mt-3 text-xs text-slate-700">
          <div class="font-semibold text-slate-800 mb-1">Caption overlays (safe for crops)</div>
          <ul class="list-disc ml-4 space-y-1">
            ${overlays.map(item => `<li><span class="text-slate-500">${escapeHtml(item.beat || 'Beat')}:</span> ${escapeHtml(item.text || '')} <span class="text-slate-400">(${item.safe_chars || 0} chars)</span></li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${engagementPrompts.length ? `
        <div class="mt-3 text-xs text-slate-700">
          <div class="font-semibold text-slate-800 mb-1">Engagement prompts</div>
          <ul class="list-disc ml-4 space-y-1">
            ${engagementPrompts.map(item => `<li><span class="text-slate-500">${escapeHtml(item.type || '')}:</span> ${escapeHtml(item.prompt || '')}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${shootList.length ? `
        <div class="mt-4 text-xs text-slate-700 border border-purple-100 rounded-lg p-3 bg-white">
          <div class="flex items-center justify-between mb-2">
            <div class="font-semibold text-slate-900">Shoot list (${escapeHtml(reel.variant || 'resource_light')})</div>
            <div class="flex gap-2 flex-wrap">
              ${exportsCsv ? `<button class="btn-ghost text-xs" data-download-ref="${exportCsvId}" data-download-filename="shoot-list.csv" data-download-type="text/csv">Download CSV</button>` : ''}
              ${exportsPdf ? `<button class="btn-ghost text-xs" data-download-ref="${exportPdfId}" data-download-filename="shoot-list.pdf" data-download-type="application/pdf">Export PDF</button>` : ''}
            </div>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full text-[11px]">
              <thead>
                <tr class="text-slate-500 text-left">
                  <th class="py-1 pr-2">Beat</th>
                  <th class="py-1 pr-2">Shot</th>
                  <th class="py-1 pr-2">Overlay</th>
                  <th class="py-1 pr-2">Timing</th>
                  <th class="py-1 pr-2">Aspect</th>
                </tr>
              </thead>
              <tbody class="divide-y divide-slate-100">
                ${shootList.map(item => `
                  <tr>
                    <td class="py-1 pr-2 text-slate-700">${escapeHtml(item.beat || '')}</td>
                    <td class="py-1 pr-2 text-slate-700">${escapeHtml(item.shot || '')}</td>
                    <td class="py-1 pr-2 text-slate-700">${escapeHtml(item.overlay || '')}</td>
                    <td class="py-1 pr-2 text-slate-500">${escapeHtml(item.timing_cue || '')}</td>
                    <td class="py-1 pr-2 text-slate-500">${escapeHtml(item.aspect_ratio || '9:16')}</td>
                  </tr>
                `).join('')}
              </tbody>
            </table>
          </div>
        </div>
        <textarea id="${exportCsvId}" class="hidden">${escapeHtml(exportsCsv || '')}</textarea>
        <textarea id="${exportPdfId}" class="hidden">${escapeHtml(exportsPdf || '')}</textarea>
      ` : ''}

      ${postingChecklist.length ? `
        <div class="mt-3 text-xs text-slate-700">
          <div class="font-semibold text-slate-800 mb-1">Posting checklist</div>
          <ul class="list-disc ml-4 space-y-1">
            ${postingChecklist.map(item => `<li>${escapeHtml(item)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${loopHint ? `<div class="mt-2 text-[11px] text-slate-500">Looping tip: ${escapeHtml(loopHint)}</div>` : ''}

      ${broll.length ? `
        <div class="mt-3 text-xs text-slate-700">
          <div class="font-semibold text-slate-800 mb-1">B-roll / supporting shots</div>
          <ul class="list-disc ml-4 space-y-1">
            ${broll.map(line => `<li>${escapeHtml(line)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${platformSpecs.length ? `
        <div class="mt-3 text-xs text-slate-700">
          <div class="font-semibold text-slate-800 mb-1">Platform sizing</div>
          <div class="flex flex-wrap gap-2">
            ${platformSpecs.map(formatSpecChip).join('')}
          </div>
        </div>
      ` : ''}

      ${thumbnailIdeas.length ? `
        <div class="mt-3 text-xs text-slate-700">
          <div class="font-semibold text-slate-800 mb-1">Thumbnail / title ideas</div>
          <ul class="list-disc ml-4 space-y-1">
            ${thumbnailIdeas.map(t => `<li><span class="text-slate-500">${escapeHtml(t.platform || '')}:</span> ${escapeHtml(t.title || '')} <span class="text-slate-400">(${escapeHtml(t.aspect_ratio || '9:16')})</span></li>`).join('')}
          </ul>
        </div>
      ` : ''}
    </div>
  `;
}

// Render platform variants when multiple platforms are selected
// Only show if variants were explicitly requested and present
function renderPlatformVariants(variants, currentPlatform) {
  if (!variants) return '';

  const entries = Object.entries(variants).map(([platform, value]) => {
    return { platform, data: normalizeVariantPayload(value) };
  });
  
  // Don't show variants section if empty or only contains current platform
  if (!entries.length) return '';
  if (entries.length === 1 && entries[0].platform === currentPlatform) return '';

  return `
    <div class="mt-3 p-3 bg-blue-50 rounded-2xl border border-blue-100">
      <div class="flex flex-wrap items-center justify-between gap-2 mb-3">
        <div class="flex items-center gap-2 text-sm font-medium text-blue-900">
          <span>Platform variants</span>
          <span class="text-xs text-blue-700">Tuned for each channel</span>
        </div>
        <button type="button" class="btn-ghost text-xs" data-export-variants>Export all</button>
      </div>
      <div class="grid gap-3 md:grid-cols-2">
        ${entries.map(({ platform, data }) => {
          const editorId = `variant-${platform}-${Math.random().toString(36).slice(2,8)}`;
          const stampId = `${editorId}-stamp`;
          const warnings = renderWarningList(data.warnings);
          const badge = platform === currentPlatform ? '<span class="text-[11px] text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">Selected</span>' : '';
          const thumb = data.thumbnail_note ? `<p class="text-[11px] text-blue-800 bg-blue-100 rounded px-2 py-1">Thumbnail: ${escapeHtml(data.thumbnail_note)}</p>` : '';
          return `
            <div class="bg-white rounded-xl border border-blue-100 p-3 shadow-sm" data-variant-card>
              <div class="flex items-center justify-between gap-2 mb-2">
                <div class="flex items-center gap-2">
                  <span class="text-xs font-semibold text-blue-900">${formatPlatformLabel(platform)}</span>
                  ${badge}
                </div>
                <div class="flex items-center gap-2">
                  <button class="btn-ghost text-[11px]" data-copy-target="${editorId}" data-stamp-target="${stampId}">Copy</button>
                  <span id="${stampId}" class="copy-timestamp"></span>
                </div>
              </div>
              ${thumb}
              ${warnings}
              <textarea id="${editorId}" class="post-editor post-editor--compact" data-variant-text data-variant-platform="${platform}">${escapeHtml(data.text)}</textarea>
              ${data.cta ? `<p class="text-[11px] text-slate-600 mt-2">CTA: ${escapeHtml(data.cta)}</p>` : ''}
            </div>
          `;
        }).join('')}
      </div>
    </div>
  `;
}

function applyPlatformPreferences(platforms = [], opts = {}) {
  const options = (typeof opts === 'object' && opts) ? opts : {};
  const skipSelection = !!options.skipSelection;
  const note = document.getElementById('platform-prefs-note');
  const emptyState = document.getElementById('platform-preset-empty');
  const buttons = getGeneratorPlatformButtons();
  if (!buttons.length) return;
  const allowed = new Set(buttons.map(btn => normalizePlatformKey(btn.dataset.generatorPlatform)));
  const normalized = Array.from(new Set((platforms || []).map(normalizePlatformKey).filter(key => allowed.has(key))));
  platformPresetState.wizard = normalized;
  if (!normalized.length) {
    emptyState?.classList.remove('hidden');
    note?.classList.add('hidden');
    if (!skipSelection) {
      setGeneratorPlatformSelections([DEFAULT_GENERATOR_PLATFORM]);
    }
    renderPlatformPresetButtons();
    return;
  }

  emptyState?.classList.add('hidden');
  if (skipSelection) {
    syncPreferredPlatformButtons();
  } else {
    setGeneratorPlatformSelections(normalized);
  }

  if (note) {
    note.textContent = `Personalized from your wizard: ${normalized.map(formatPlatformLabel).join(', ')}`;
    note.classList.remove('hidden');
  }

  renderPlatformPresetButtons();
}

function syncPreferredPlatformButtons() {
  const wrap = document.getElementById('platform-preset-buttons');
  if (!wrap) return;
  const selected = dedupePlatforms(getGeneratorPlatformSelections());
  wrap.querySelectorAll('[data-platform-preset]').forEach(btn => {
    const presetList = dedupePlatforms((btn.dataset.platformList || '').split(','));
    const isActive = platformListsMatch(selected, presetList);
    btn.classList.toggle('chip--active', isActive);
    btn.setAttribute('aria-pressed', isActive ? 'true' : 'false');
  });
}

function renderPlatformPresetButtons() {
  const wrap = document.getElementById('platform-preset-buttons');
  const emptyState = document.getElementById('platform-preset-empty');
  if (!wrap) return;
  wrap.innerHTML = '';
  const presets = [];
  if (platformPresetState.wizard && platformPresetState.wizard.length) {
    presets.push({
      id: 'wizard-default',
      label: 'Saved mix',
      subtitle: formatPlatformPresetSummary(platformPresetState.wizard),
      platforms: platformPresetState.wizard
    });
  }
  const lastPlan = platformPresetState.lastPlan;
  if (lastPlan && Array.isArray(lastPlan.platforms) && lastPlan.platforms.length) {
    const duplicate = presets.some(preset => platformListsMatch(preset.platforms, lastPlan.platforms));
    if (!duplicate) {
      presets.push({
        id: 'last-plan',
        label: lastPlan.planLength ? `Last plan • ${lastPlan.planLength}d` : 'Last plan',
        subtitle: lastPlan.note ? `Focus: ${truncateText(lastPlan.note, 60)}` : formatPlatformPresetSummary(lastPlan.platforms),
        platforms: lastPlan.platforms
      });
    }
  }

  if (!presets.length) {
    wrap.classList.add('hidden');
    emptyState?.classList.remove('hidden');
    return;
  }

  emptyState?.classList.add('hidden');
  presets.forEach(preset => {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'chip flex flex-col items-start text-left gap-0.5';
    btn.dataset.platformPreset = preset.id;
    btn.dataset.platformList = dedupePlatforms(preset.platforms).join(',');
    btn.setAttribute('aria-pressed', 'false');
    btn.innerHTML = `<span class="font-medium">${preset.label}</span><span class="text-xs text-slate-500">${preset.subtitle}</span>`;
    btn.addEventListener('click', () => {
      setGeneratorPlatformSelections(preset.platforms);
      syncPreferredPlatformButtons();
      document.getElementById('generate-content')?.focus();
    });
    wrap.appendChild(btn);
  });
  wrap.classList.remove('hidden');
  syncPreferredPlatformButtons();
}

function platformListsMatch(a = [], b = []) {
  if (a.length !== b.length) return false;
  const mapA = new Set(dedupePlatforms(a));
  const mapB = new Set(dedupePlatforms(b));
  if (mapA.size !== mapB.size) return false;
  for (const key of mapA) {
    if (!mapB.has(key)) return false;
  }
  return true;
}

function formatPlatformPresetSummary(list = []) {
  return dedupePlatforms(list).map(formatPlatformLabel).join(', ');
}

function truncateText(text = '', limit = 60) {
  if (!text) return '';
  const trimmed = text.trim();
  if (trimmed.length <= limit) return trimmed;
  return `${trimmed.slice(0, limit).trim()}…`;
}

function bindCopyButton(btn, editor, timestampEl, card){
  if (!btn) return;
  btn.addEventListener('click', async () => {
    const textSource = editor ? editor.value : btn.dataset.copyText || '';
    const ok = await copyToClipboard(textSource);
    if (!ok){
      showToast('Failed to copy to clipboard');
      return;
    }
    markCopied(editor, card, timestampEl);
    const original = btn.textContent;
    btn.textContent = 'Copied!';
    setTimeout(() => { btn.textContent = original || 'Copy'; }, 1500);
  });
}

function bindDownloadButton(btn, card){
  if (!btn) return;
  btn.addEventListener('click', () => {
    const ref = btn.getAttribute('data-download-ref');
    const filename = btn.getAttribute('data-download-filename') || 'shoot-list.txt';
    const mime = btn.getAttribute('data-download-type') || 'text/plain';
    const refNode = ref ? card.querySelector(`#${ref}`) : null;
    const content = refNode ? (refNode.value || refNode.textContent || '') : '';
    if (!content || !content.trim()) {
      showToast('Nothing to download yet');
      return;
    }
    const blob = new Blob([content], { type: mime });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(url);
  });
}

function markCopied(editor, card, timestampEl){
  if (editor) {
    editor.classList.add('post-editor--copied');
    if (timestampEl?.id) {
      editor.dataset.copyStamp = timestampEl.id;
    }
  }
  if (card) card.classList.add('card--copied');
  if (timestampEl){
    const stamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    timestampEl.textContent = `Copied ${stamp}`;
  }
}

function clearCopyState(editor, card){
  if (!editor || !editor.classList.contains('post-editor--copied')) return;
  editor.classList.remove('post-editor--copied');
  if (card && !card.querySelector('.post-editor--copied')) {
    card.classList.remove('card--copied');
  }
  const stampId = editor.dataset.copyStamp;
  if (stampId && card){
    const stamp = card.querySelector(`#${stampId}`);
    if (stamp) stamp.textContent = '';
  }
}

function buildVariantCardContent(variants, editor, card) {
  if (!variants || !variants.length) return '';
  return variants.map((variant, idx) => {
    const stampId = `${editor.id}-variant-${idx}`;
    return `
      <div class="p-3 rounded-xl border border-slate-200 bg-white shadow-sm">
        <div class="flex items-center justify-between mb-2">
          <div class="text-xs font-semibold text-slate-600">Option ${idx + 1}</div>
          <button class="btn-ghost btn-xs" data-variant-apply="${idx}" data-stamp-target="${stampId}">Use</button>
        </div>
        <textarea class="post-editor post-editor--compact" data-variant-index="${idx}">${escapeHtml(variant.caption || variant.text || '')}</textarea>
        <div class="flex items-center gap-2 mt-2">
          <button class="btn-ghost btn-xs" data-copy-variant="${idx}" data-stamp-target="${stampId}">Copy</button>
          <span id="${stampId}" class="copy-timestamp"></span>
        </div>
      </div>
    `;
  }).join('');
}

async function handleGenerateVariants(post, card, editor, wrap){
  if (!wrap) return;
  wrap.innerHTML = '<div class="text-sm text-slate-600">Generating variants…</div>';
  wrap.classList.remove('hidden');
  try {
    const payload = {
      platform: post.platform || 'instagram',
      tone: document.getElementById('gen-tone')?.value || profileDefaults.tone,
      industry: profileDefaults.industry || answers?.industry || 'Business',
      brand_keywords: getCurrentKeywords(),
      goals: getCurrentGoals(),
      count: 3
    };
    const res = await fetch('/api/generate-variants', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify(payload)
    });
    if (!res.ok) throw new Error('Failed to generate variants');
    const data = await res.json();
    const variants = data?.variants || [];
    wrap.innerHTML = buildVariantCardContent(variants, editor, card);
    wrap.querySelectorAll('[data-variant-apply]').forEach(btn => {
      btn.addEventListener('click', () => {
        const idx = parseInt(btn.dataset.variantApply || '0', 10);
        const textArea = wrap.querySelector(`textarea[data-variant-index="${idx}"]`);
        if (textArea) {
          editor.value = textArea.value;
          autoSizeEditor(editor);
          clearCopyState(editor, card);
          const qualityWrap = card?.querySelector('[data-quality-hints]');
          if (qualityWrap) renderQualityHints(qualityWrap, editor, post, card);
        }
      });
    });
    wrap.querySelectorAll('[data-copy-variant]').forEach(btn => {
      btn.addEventListener('click', async () => {
        const idx = parseInt(btn.dataset.copyVariant || '0', 10);
        const textArea = wrap.querySelector(`textarea[data-variant-index="${idx}"]`);
        const stampTarget = btn.dataset.stampTarget ? wrap.querySelector(`#${btn.dataset.stampTarget}`) : null;
        const ok = await copyToClipboard(textArea?.value || '');
        if (ok && stampTarget) stampTarget.textContent = 'Copied';
      });
    });
  } catch (err) {
    console.error(err);
    wrap.innerHTML = '<div class="text-sm text-red-600">Could not generate variants right now.</div>';
  }
}

function regenerateHookText(text = '', post = {}) {
  const sentences = (text || '').split(/(?<=[.!?])\s+/).filter(Boolean);
  const rest = sentences.slice(1).join(' ');
  const keywords = getCurrentKeywords();
  const platform = formatPlatformLabel(post.platform || '');
  const pillar = post.pillar || 'Update';
  const hook = `Fresh ${platform} ${pillar.toLowerCase()}: ${keywords[0] || 'see what’s new'}${keywords[1] ? ' + ' + keywords[1] : ''}`;
  return [hook, rest || sentences[0] || ''].filter(Boolean).join(' ');
}

function regenerateCtaText(text = '', post = {}) {
  const ctaVariants = (post.cta_variants || []).map(v => v.text).filter(Boolean);
  if (post?.reel?.cta) ctaVariants.push(post.reel.cta);
  ctaVariants.push('Tap the link to learn more.', 'Comment with your question and we will DM you.', 'Save this for later and share with a friend.');
  const chosen = ctaVariants[Math.floor(Math.random() * ctaVariants.length)] || 'Let us know what you think.';
  const parts = (text || '').split(/(?<=[.!?])\s+/).filter(Boolean);
  const body = parts.slice(0, -1).join(' ') || text;
  return `${body.trim()} ${chosen}`.trim();
}

// --- Inclusive Language Batch Fix UX Improvement ---
// Assumes: inclusiveLanguageIssues is an array of detected issues for the current text,
// and applyInclusiveLanguageFix(issue) applies a single fix.
// The following adds a "Fix all" button and handler.

function renderInclusiveLanguageIssues(issues, text, onTextUpdate) {
  const container = document.createElement('div');
  container.className = 'inclusive-language-issues';

  if (issues.length > 1) {
    const fixAllBtn = document.createElement('button');
    fixAllBtn.textContent = 'Fix all';
    fixAllBtn.className = 'btn btn-sm btn-primary';
    fixAllBtn.onclick = function() {
      let newText = text;
      // Apply all fixes in order, updating the text each time
      issues.forEach(issue => {
        newText = applyInclusiveLanguageFix(issue, newText);
      });
      onTextUpdate(newText);
    };
    container.appendChild(fixAllBtn);
  }

  issues.forEach((issue, idx) => {
    const issueDiv = document.createElement('div');
    issueDiv.className = 'inclusive-language-issue';
    issueDiv.textContent = issue.message;
    const fixBtn = document.createElement('button');
    fixBtn.textContent = 'Apply fix';
    fixBtn.className = 'btn btn-xs btn-secondary';
    fixBtn.onclick = function() {
      const newText = applyInclusiveLanguageFix(issue, text);
      onTextUpdate(newText);
    };
    issueDiv.appendChild(fixBtn);
    container.appendChild(issueDiv);
  });
  return container;
}

// Helper: applies a single inclusive language fix to the text
function applyInclusiveLanguageFix(issue, text) {
  // Example: replace the problematic word/phrase with the suggested fix
  // Assumes issue has {start, end, replacement}
  if (typeof issue.start === 'number' && typeof issue.end === 'number' && issue.replacement) {
    return text.slice(0, issue.start) + issue.replacement + text.slice(issue.end);
  }
  // Fallback: return text unchanged
  return text;
}
function readabilityMetrics(text = '') {
  const sentences = (text.match(/[^.!?]+[.!?]*/g) || []).filter(Boolean);
  const words = (text.match(/\b[\w']+\b/g) || []);
  const syllables = words.reduce((total, word) => total + countSyllables(word), 0);
  const sentenceCount = sentences.length || 1;
  const wordCount = words.length || 1;
  const wordsPerSentence = wordCount / sentenceCount;
  const syllablesPerWord = syllables / wordCount;
  const readingEase = Math.max(0, Math.min(121, 206.835 - 1.015 * wordsPerSentence - 84.6 * syllablesPerWord));
  let grade = '10+';
  if (readingEase >= 90) grade = '5';
  else if (readingEase >= 80) grade = '6';
  else if (readingEase >= 70) grade = '7';
  else if (readingEase >= 60) grade = '8';
  else if (readingEase >= 50) grade = '10';
  else if (readingEase >= 40) grade = '12';
  return { readingEase: Math.round(readingEase), grade, wordsPerSentence, syllablesPerWord };
}

function countSyllables(word = '') {
  const sanitized = word.toLowerCase().replace(/[^a-z]/g, '');
  if (!sanitized) return 1;
  const matches = sanitized.match(/[aeiouy]+/g);
  const count = matches ? matches.length : 1;
  return Math.max(1, count);
}

// Utility to escape HTML special characters
function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = String(str);
  return div.innerHTML;
}
function analyzeDraftQuality(text = '') {
  const checks = [];
  const metrics = readabilityMetrics(text);
  checks.push({
    type: 'readability',
    label: `Readability grade ~${metrics.grade}`,
    detail: `Flesch score ${metrics.readingEase}`,
    apply: (current) => simplifySentences(current)
  });

  const ctaRegex = /(buy|shop|click|tap|sign up|join|book|register|dm|comment|link in bio|learn more|download)/i;
  if (!ctaRegex.test(text)) {
    const suggestion = 'Add a clear CTA like “Tap to claim your spot.”';
    checks.push({
      type: 'cta',
      label: 'CTA missing',
      detail: suggestion,
      apply: (current) => `${current.trim()} Tap to claim your spot.`.trim()
    });
  }

  const inclusiveMap = {
    guys: 'everyone',
    chairman: 'chair',
    manpower: 'team',
    insane: 'incredible',
    crazy: 'unexpected'
  };
  Object.entries(inclusiveMap).forEach(([term, replacement]) => {
    const regex = new RegExp(`\b${term}\b`, 'i');
    if (regex.test(text)) {
      checks.push({
        type: 'inclusive',
        label: 'Inclusive wording',
        detail: `Swap “${term}” for “${replacement}”.`,
        apply: (current) => current.replace(regex, replacement)
      });
    }
  });

  return { metrics, checks };
}

function simplifySentences(text = '') {
  return (text || '').split(/(?<=[.!?])\s+/).map(sentence => {
    const words = sentence.trim().split(/\s+/);
    if (words.length > 24) {
      return words.slice(0, 20).join(' ') + '…';
    }
    return sentence;
  }).join(' ');
}

function renderQualityHints(container, editor, post, card) {
  if (!container || !editor) return;
  const { metrics, checks } = analyzeDraftQuality(editor.value || '');
  const hintItems = checks.map((check, idx) => {
    const actionLabel = check.type === 'cta' ? 'Insert CTA' : 'Apply fix';
    return `
      <div class="flex items-start gap-3 py-2 border-b border-slate-100 last:border-0">
        <div class="text-sm font-semibold text-slate-800">${check.label}</div>
        <div class="text-xs text-slate-600 flex-1">${check.detail}</div>
        <button class="btn-ghost btn-xs" data-quality-apply="${idx}">${actionLabel}</button>
      </div>`;
  }).join('');
  container.innerHTML = `
    <div class="flex items-center justify-between mb-2">
      <div class="text-xs font-semibold text-slate-700">Readability: Grade ${metrics.grade} • Score ${metrics.readingEase}</div>
      <div class="text-[10px] text-slate-500">${metrics.wordsPerSentence.toFixed(1)} words / sentence</div>
    </div>
    ${hintItems || '<p class="text-xs text-slate-500">No issues detected.</p>'}
  `;
  container.querySelectorAll('[data-quality-apply]').forEach(btn => {
    btn.addEventListener('click', () => {
      const idx = parseInt(btn.dataset.qualityApply || '0', 10);
      const check = checks[idx];
      if (!check || typeof check.apply !== 'function') return;
      editor.value = check.apply(editor.value || '');
      autoSizeEditor(editor);
      clearCopyState(editor, card);
      renderQualityHints(container, editor, post, card);
    });
  });
}

function autoSizeEditor(editor){
  if (!editor) return;
  editor.style.height = 'auto';
  editor.style.height = `${editor.scrollHeight}px`;
}

async function copyToClipboard(text){
  try{
    if (navigator.clipboard && window.isSecureContext){
      await navigator.clipboard.writeText(text);
      return true;
    }
  }catch(err){/* fallback below */}
  try{
    const helper = document.createElement('textarea');
    helper.value = text;
    helper.style.position = 'fixed';
    helper.style.left = '-9999px';
    document.body.appendChild(helper);
    helper.focus();
    helper.select();
    document.execCommand('copy');
    helper.remove();
    return true;
  }catch(err){
    console.error('Legacy clipboard copy failed', err);
    return false;
  }
}


// Utility functions
function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text || '';
  return div.innerHTML;
}

function escapeAttr(text) {
  return (text || '')
    .replace(/&/g, '&amp;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/\n/g, '&#10;');
}

const PLATFORM_LABEL_OVERRIDES = {
  twitter: 'X / Twitter',
  short_video: 'Reels / Shorts'
};
const PLATFORM_CHARACTER_LIMITS = {
  twitter: 280,
  instagram: 2200,
  facebook: 63206,
  linkedin: 3000,
  tiktok: 2200,
  short_video: 2200
};

function getCachedIndustries(){
  if (dashboardConfigCache && Array.isArray(dashboardConfigCache.industries)) return dashboardConfigCache.industries;
  if (window.CFG && Array.isArray(window.CFG.industries)) return window.CFG.industries;
  return [];
}

function resolveIndustryLabel(value){
  if (!value) return 'Not set';
  const industries = getCachedIndustries();
  const normalized = String(value).trim().toLowerCase();
  if (industries.length){
    const keyMatch = industries.find(opt => (opt.key || '').toLowerCase() === normalized);
    if (keyMatch) return keyMatch.label;
    const labelMatch = industries.find(opt => (opt.label || '').toLowerCase() === normalized);
    if (labelMatch) return labelMatch.label;
  }
  return formatIndustryLabel(value);
}

function formatPlatformLabel(value) {
  if (!value) return '';
  const normalized = value.toLowerCase();
  if (PLATFORM_LABEL_OVERRIDES[normalized]) return PLATFORM_LABEL_OVERRIDES[normalized];
  return value.replace(/_/g, ' ').replace(/\b\w/g, (ch) => ch.toUpperCase());
}

function collectAccountFormProfile(){
  const companyInput = document.getElementById('account-company');
  const industrySelect = document.getElementById('account-industry');
  const toneSelect = document.getElementById('account-tone');
  const platforms = [];
  document.querySelectorAll('[data-platform-checkbox]:checked').forEach(cb => {
    platforms.push(cb.value);
  });
  const selectedOption = industrySelect?.selectedOptions?.[0];
  const industryKey = selectedOption?.value || '';
  const industryLabel = selectedOption?.dataset?.label || industryKey || '';
  return {
    company: companyInput?.value?.trim() || '',
    industry: industryLabel,
    industry_key: industryKey,
    tone: toneSelect?.value || '',
    platforms
  };
}

function getPreferredGeneratorPlatforms() {
  if (platformPresetState.lastPlan && Array.isArray(platformPresetState.lastPlan.platforms) && platformPresetState.lastPlan.platforms.length) {
    return dedupePlatforms(platformPresetState.lastPlan.platforms);
  }
  if (platformPresetState.wizard && platformPresetState.wizard.length) {
    return dedupePlatforms(platformPresetState.wizard);
  }
  const snapshot = collectAccountFormProfile();
  if (snapshot.platforms && snapshot.platforms.length) {
    return snapshot.platforms.map(normalizePlatformKey);
  }
  if (answers?.platforms?.length) {
    return answers.platforms.map(normalizePlatformKey);
  }
  return [DEFAULT_GENERATOR_PLATFORM];
}

function hydrateVoiceSummary(data = {}, options = {}){
  const fallbackAnswers = (typeof answers !== 'undefined') ? answers : {};
  const source = { ...data };
  const formSnapshot = collectAccountFormProfile();
  if (!source.company){
    source.company = formSnapshot.company || fallbackAnswers.company || '';
  }
  if (!source.industry){
    source.industry = formSnapshot.industry || fallbackAnswers.industry || fallbackAnswers.industry_key || '';
  }
  if (!source.industry_key){
    source.industry_key = formSnapshot.industry_key || fallbackAnswers.industry_key || '';
  }
  if (!source.tone){
    source.tone = formSnapshot.tone || fallbackAnswers.tone || '';
  }
  if (!source.platforms || !source.platforms.length){
    if (formSnapshot.platforms.length) source.platforms = formSnapshot.platforms;
    else if (Array.isArray(fallbackAnswers.platforms) && fallbackAnswers.platforms.length) source.platforms = fallbackAnswers.platforms;
    else source.platforms = ['instagram'];
  }
  const missingLabel = options.profileMissing ? 'Not set — ' : 'Not set — ';
  const ctaLabel = options.profileMissing ? 'Set voice' : 'Update voice';
  setVoiceSummaryField('company', source.company || '', { missingLabel, ctaLabel });
  setVoiceSummaryField('industry', resolveIndustryLabel(source.industry || source.industry_key), { missingLabel, ctaLabel });
  setVoiceSummaryField('tone', formatToneLabel(source.tone), { missingLabel, ctaLabel });
  setVoiceSummaryField('platforms', source.platforms.map(formatPlatformLabel).join(', '), { missingLabel, ctaLabel });
  const pill = document.getElementById('voice-pill');
  if (pill){
    pill.textContent = source.company ? `Voice locked: ${source.company}` : 'Voice ready to sync';
  }
  updateToneNote(source.tone);
}

function setVoiceSummaryField(key, value, opts = {}){
  const el = document.querySelector(`[data-voice-${key}]`);
  if (!el) return;
  const hasValue = value && String(value).trim();
  if (hasValue) {
    el.textContent = value;
    el.classList.remove('text-amber-700');
    return;
  }
  el.textContent = '';
  el.classList.add('text-amber-700');
  const prefix = document.createElement('span');
  prefix.textContent = opts.missingLabel || 'Not set — ';
  const link = document.createElement('a');
  link.href = '/settings';
  link.className = 'text-indigo-600 underline';
  link.textContent = opts.ctaLabel || 'Set now';
  el.appendChild(prefix);
  el.appendChild(link);
}

function formatToneLabel(value){
  if (!value) return 'Friendly';
  return value.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().replace(/\b\w/g, ch => ch.toUpperCase());
}

function formatIndustryLabel(value){
  if (!value) return 'Not set';
  return value.replace(/[_-]+/g, ' ').replace(/\s+/g, ' ').trim().replace(/\b\w/g, ch => ch.toUpperCase());
}

function updateToneNote(tone){
  const note = document.getElementById('tone-prefs-note');
  if (!note) return;
  if (!tone){
    note.classList.add('hidden');
    note.textContent = '';
    return;
  }
  note.textContent = `Default tone from wizard: ${formatToneLabel(tone)}.`;
  note.classList.remove('hidden');
}