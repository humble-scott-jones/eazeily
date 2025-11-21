// Dashboard functionality for generating content and managing responses
const DASHBOARD_SEED_STORAGE_KEY = (typeof window !== 'undefined' && window.SEED_STORAGE_KEY) ? window.SEED_STORAGE_KEY : '__swelly_seed_posts';
const DASHBOARD_PLAN_CACHE_KEY = 'swelly_dashboard_plan_cache';
const DASHBOARD_PLAN_TTL_MS = 1000 * 60 * 60 * 72; // 72 hours
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
let profileDefaults = { tone: 'friendly', industry: 'Business', keywords: [], goals: [], id: 'anon' };
let lastGeneratorState = null;
let generatorHydratedFromProfile = false;

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

  // Template library and presets
  setupTemplateLibrary();

  // One-click generation defaults
  setupOneClickGeneration();

  // Inspiration image uploads
  setupImageUpload();

  // Feedback form in sidebar
  setupFeedbackForm();

  // Activity and ownership feed
  hydrateActivityFeed();

  hydrateVoiceSummary({});
  hydrateSeedPosts();
  seedPresetStateFromWizardDefaults();
});

async function loadUserProfile() {
  try {
    await ensureAccountFormFields();
    const response = await fetch('/api/profile', { credentials: 'include' });
    let profile = {};
    if (response.ok) {
      profile = await response.json();
      applyProfileToAccountForm(profile);
    }
    profileDefaults = {
      tone: profile.tone || 'friendly',
      industry: profile.industry || profile.industry_key || 'Business',
      keywords: Array.isArray(profile.brand_keywords) ? profile.brand_keywords : [],
      goals: Array.isArray(profile.goals) ? profile.goals : [],
      id: profile.id || (window.CURRENT_USER && window.CURRENT_USER.id) || 'anon'
    };
    setTemplateProfileKey(profileDefaults.id);
    renderProfileDefaultsSummary(profileDefaults);
    hydrateTemplateLibrary();
    renderCollaborationSummary();
    applyProfileDefaultsToGenerator(profileDefaults);
    hydrateStoredGeneratorState({ apply: true, preferProfile: true });
    hydrateVoiceSummary(profile || {});
  } catch (error) {
    console.error('Failed to load user profile:', error);
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
  const { reelOptions } = generatorUI;
  if (!reelOptions) return;
  const selected = getGeneratorPlatformSelections();
  const hasVideo = selected.some(key => VIDEO_PLATFORM_KEYS.has(key));
  if (hasVideo) {
    reelOptions.classList.remove('hidden');
  } else {
    reelOptions.classList.add('hidden');
  }
}

function setupContentGeneration() {
  const generateBtn = document.getElementById('generate-content');
  const loadingDiv = document.getElementById('content-loading');
  const resultsDiv = document.getElementById('generated-content');
  const contentResults = document.getElementById('content-results');
  const reelOptions = document.getElementById('reel-options');
  const planLengthWrap = document.getElementById('plan-length-buttons');
  const daySelect = document.getElementById('gen-days');

  generatorUI = { generateBtn, loadingDiv, resultsDiv, contentResults, reelOptions };
  initGeneratorPlatformPicker();
  refreshReelOptionsVisibility();
  syncPreferredPlatformButtons();

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

async function executeContentGeneration(options = {}){
  const { daysOverride } = options;
  const {
    generateBtn,
    loadingDiv,
    resultsDiv,
    contentResults,
    reelOptions
  } = generatorUI;
  if (!document.getElementById('gen-days')){
    showToast('Generator unavailable. Refresh and try again.');
    return;
  }
  if (!ensureDashboardAuth('Create a free account to generate content.')) return;
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

  const includeReelDetails = reelOptions && !reelOptions.classList.contains('hidden') && platforms.some(key => VIDEO_PLATFORM_KEYS.has(key));
  let details = {};
  if (includeReelDetails) {
    details = {
      reel_style: document.getElementById('reel-style').value,
      reel_length: parseInt(document.getElementById('reel-length').value, 10),
      production_tier: document.getElementById('production-tier').value
    };
  }

  generateBtn?.classList.add('hidden');
  loadingDiv?.classList.remove('hidden');

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
  if (contentResults) contentResults.innerHTML = '';
  renderPosts(data);
  const meta = buildPlanMetadataFromPayload(data);
  cacheGeneratedPlan(data, meta);
  lastGeneratorState = { platforms, tone, goals, keywords, planLength: days };
  persistTemplateLibraryState();
  applyPlanMetadata(meta);
    resultsDiv?.classList.remove('hidden');
    resultsDiv?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } catch (error) {
    console.error('Content generation failed:', error);
    showToast('Failed to generate content. Please try again.');
  } finally {
    generateBtn?.classList.remove('hidden');
    loadingDiv?.classList.add('hidden');
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

function hydrateTemplateLibrary() {
  loadTemplateLibraryState();
  renderTemplatePicker();
  renderPresetButtons();
  renderCollaborationSummary();
}

function setupTemplateLibrary() {
  const saveBtn = document.getElementById('save-template');
  const applyBtn = document.getElementById('apply-template');
  const picker = document.getElementById('template-picker');
  hydrateTemplateLibrary();

  saveBtn?.addEventListener('click', () => saveCurrentTemplate());
  applyBtn?.addEventListener('click', () => applySelectedTemplate());
  picker?.addEventListener('change', () => updateTemplateEmptyState());
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
    opt.textContent = template.author ? `${template.name} • ${template.author}` : template.name;
    opt.dataset.platforms = (template.platforms || []).join(',');
    picker.appendChild(opt);
  });
  updateTemplateEmptyState(emptyState);
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

function saveCurrentTemplate() {
  const nameField = document.getElementById('template-name');
  const name = (nameField?.value || '').trim();
  if (!name) {
    showToast('Name your template first.');
    nameField?.focus();
    return;
  }
  const baseTemplate = {
    id: `tpl-${Date.now()}`,
    name,
    tone: document.getElementById('gen-tone')?.value || 'friendly',
    platforms: getGeneratorPlatformSelections(),
    goals: getCurrentGoals(),
    keywords: getCurrentKeywords(),
    author: getCurrentUserName() || 'Shared profile',
    updatedAt: Date.now()
  };
  const existingIdx = (templateLibraryState.templates || []).findIndex(t => t.name.toLowerCase() === name.toLowerCase());
  if (existingIdx >= 0) {
    const existing = templateLibraryState.templates[existingIdx] || {};
    templateLibraryState.templates[existingIdx] = Object.assign({}, existing, baseTemplate, {
      id: existing.id || baseTemplate.id
    });
  } else {
    templateLibraryState.templates = [...(templateLibraryState.templates || []), baseTemplate];
  }
  lastGeneratorState = Object.assign({}, baseTemplate, { planLength: getCurrentPlanLength() });
  persistTemplateLibraryState();
  renderTemplatePicker();
  renderCollaborationSummary();
  showToast('Template saved for this profile.');
}

function applySelectedTemplate() {
  const picker = document.getElementById('template-picker');
  if (!picker) return;
  const selectedId = picker.value;
  const tpl = (templateLibraryState.templates || []).find(t => t.id === selectedId);
  if (!tpl) {
    showToast('Pick a template to apply.');
    return;
  }
  applyTemplateToGenerator(tpl);
  renderCollaborationSummary();
}

function applyPresetTemplate(preset) {
  const tpl = {
    id: preset.id,
    name: preset.label,
    tone: preset.tone,
    platforms: getGeneratorPlatformSelections(),
    goals: preset.goals,
    keywords: preset.keywords,
    author: 'Team preset',
    updatedAt: Date.now()
  };
  applyTemplateToGenerator(tpl, { skipPlatform: false });
  renderCollaborationSummary();
}

function applyTemplateToGenerator(tpl, opts = {}) {
  if (!tpl) return;
  if (tpl.tone) {
    const toneField = document.getElementById('gen-tone');
    if (toneField) toneField.value = tpl.tone;
  }
  if (!opts.skipPlatform && Array.isArray(tpl.platforms) && tpl.platforms.length) {
    setGeneratorPlatformSelections(tpl.platforms);
  }
  if (Array.isArray(tpl.goals)) setCurrentGoals(tpl.goals);
  if (Array.isArray(tpl.keywords)) setCurrentKeywords(tpl.keywords);
  syncPreferredPlatformButtons();
  refreshReelOptionsVisibility();
  lastGeneratorState = Object.assign({}, tpl, {
    planLength: getCurrentPlanLength(),
    updatedAt: tpl.updatedAt || Date.now(),
    author: tpl.author || getCurrentUserName() || 'Shared profile'
  });
  persistTemplateLibraryState();
  showToast('Template applied.');
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
  target.textContent = details.join(' • ');
}

function applyProfileDefaultsToGenerator(defaults = {}) {
  if (generatorHydratedFromProfile && !defaults.force) return;
  const toneField = document.getElementById('gen-tone');
  if (toneField && defaults.tone) {
    toneField.value = defaults.tone;
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

  // Group posts by day
  const byDay = posts.reduce((acc, post) => {
    (acc[post.day_index] ||= []).push(post);
    return acc;
  }, {});

  const sortedDays = Object.keys(byDay).sort((a, b) => +a - +b);
  const platformMetaMap = new Map();
  posts.forEach(post => {
    const key = String(post.platform || '').toLowerCase();
    if (!key || platformMetaMap.has(key)) return;
    platformMetaMap.set(key, formatPlatformLabel(post.platform));
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
}

function buildPostSnapshot(post = {}) {
  const lines = [];
  const platformLabel = formatPlatformLabel(post.platform || '');
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
      lines.push(post.variants[key]);
    });
  }
  return lines.join('\n');
}

function buildPostSummary(post = {}) {
  const platformLabel = formatPlatformLabel(post.platform || '');
  const day = post.day_index ? `day ${post.day_index}` : '';
  const pillar = post.pillar ? ` • ${post.pillar}` : '';
  const firstLine = (post.caption || '').split('\n')[0].trim();
  const snippet = firstLine.length > 60 ? `${firstLine.slice(0, 57)}…` : firstLine;
  return `${platformLabel} ${day}`.trim() + (pillar || '') + (snippet ? ` • ${snippet}` : '');
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

  const platformColor = platformColors[post.platform.toLowerCase()] || 'from-gray-500 to-gray-600';
  const editorId = `post-editor-${post.day_index}-${post.platform}-${Math.random().toString(36).slice(2,7)}`;
  const stampId = `${editorId}-stamp`;
  const variantsMarkup = post.variants ? renderPlatformVariants(post.variants, post.platform) : '';

  // Check if this post has variants (multiple platforms)
  const hasVariants = post.variants && Object.keys(post.variants).length > 1;

  card.innerHTML = `
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2">
        <div class="w-8 h-8 bg-gradient-to-r ${platformColor} rounded-full flex items-center justify-center">
          <span class="text-white text-xs font-bold">${post.platform.charAt(0).toUpperCase()}</span>
        </div>
        <span class="font-medium text-slate-900">${formatPlatformLabel(post.platform)}</span>
        ${hasVariants ? '<span class="text-xs text-purple-600 font-medium">• Multi-platform</span>' : ''}
      </div>
      <div class="flex gap-2">
        <button class="btn-ghost text-xs" data-copy-target="${editorId}" data-stamp-target="${stampId}">Copy</button>
        <span id="${stampId}" class="copy-timestamp"></span>
        <button class="btn-ghost text-xs" data-like="1" data-day="${post.day_index}" data-platform="${post.platform}">👍</button>
        <button class="btn-ghost text-xs" data-like="-1" data-day="${post.day_index}" data-platform="${post.platform}">👎</button>
      </div>
    </div>

    ${post.image_url ? `<img class="w-full h-32 object-cover rounded mb-3" src="${post.image_url}" alt="Suggested image" />` : ''}

    <div class="text-xs text-slate-500 mb-2"><strong>Image prompt:</strong> ${escapeHtml(post.image_prompt)}</div>

    <label class="text-xs font-semibold text-slate-500 tracking-wide">Caption</label>
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

  return card;
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

  const stampScript = `reel-stamp-script-${Math.random().toString(36).slice(2,8)}`;
  const stampSrt = `reel-stamp-srt-${Math.random().toString(36).slice(2,8)}`;
  const stampThumb = `reel-stamp-thumb-${Math.random().toString(36).slice(2,8)}`;

  return `
    <div class="mt-3 p-3 bg-slate-50 rounded border-l-4 border-purple-400">
      <div class="flex items-center gap-2 mb-2">
        <svg class="w-4 h-4 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"></path>
        </svg>
        <span class="text-sm font-medium text-purple-900">Reel Plan</span>
        <span class="text-xs text-purple-600">(${reel.length_seconds}s • ${reel.style})</span>
      </div>

      <div class="text-sm mb-2"><strong>Hook:</strong> ${escapeHtml(hook)}</div>

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
        ${otherPlatforms.map(platform => {
          const editorId = `variant-${platform}-${Math.random().toString(36).slice(2,8)}`;
          const stampId = `${editorId}-stamp`;
          return `
            <div class="space-y-1">
              <div class="flex items-center gap-2 flex-wrap">
                <span class="text-xs font-medium text-blue-700 capitalize">${platform}:</span>
                <button class="btn-ghost text-xs" data-copy-target="${editorId}" data-stamp-target="${stampId}">Copy</button>
                <span id="${stampId}" class="copy-timestamp"></span>
              </div>
              <textarea id="${editorId}" class="post-editor post-editor--compact">${escapeHtml(variants[platform])}</textarea>
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
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
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

function hydrateVoiceSummary(data = {}){
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
  setVoiceSummaryField('company', source.company || 'Not set');
  setVoiceSummaryField('industry', resolveIndustryLabel(source.industry || source.industry_key));
  setVoiceSummaryField('tone', formatToneLabel(source.tone));
  setVoiceSummaryField('platforms', source.platforms.map(formatPlatformLabel).join(', '));
  const pill = document.getElementById('voice-pill');
  if (pill){
    pill.textContent = source.company ? `Voice locked: ${source.company}` : 'Voice ready to sync';
  }
  updateToneNote(source.tone);
}

function setVoiceSummaryField(key, value){
  const el = document.querySelector(`[data-voice-${key}]`);
  if (el) el.textContent = value && value.trim() ? value : '—';
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