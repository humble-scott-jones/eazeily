let CFG = null;
let FLAGS = null;
const SEED_STORAGE_KEY = '__swelly_seed_posts';
if (typeof window !== 'undefined') {
  window.SEED_STORAGE_KEY = SEED_STORAGE_KEY;
}

function setCurrentUser(user){
  if (user && user.id){
    window.CURRENT_USER = {
      id: user.id,
      email: user.email,
      is_paid: !!user.is_paid,
      free_sample_used: !!user.free_sample_used
    };
  } else {
    window.CURRENT_USER = null;
  }
  renderAuthUi();
  updateAccessUi();
}

function userFromResponse(payload){
  if (!payload) return null;
  if (payload.user && payload.user.id) return payload.user;
  if (payload.active_user && payload.active_user.id) return payload.active_user;
  if (payload.id) return payload;
  return null;
}

const AUTH_FORM_IDS = {
  login: 'login-form',
  signup: 'signup-form',
  reset: 'reset-form',
  'confirm-reset': 'confirm-reset-form'
};

const AUTH_VIEW_META = {
  login: {
    title: 'Sign in',
    subtitle: 'Access your saved brand voice and content plans.'
  },
  signup: {
    title: 'Create your account',
    subtitle: 'Free to start — no credit card required.'
  },
  reset: {
    title: 'Reset password',
    subtitle: 'Send yourself a secure reset link.'
  },
  'confirm-reset': {
    title: 'Set a new password',
    subtitle: 'Paste the token from your email and pick a fresh password.'
  }
};

const EMAIL_INPUT_IDS = ['auth-email','signup-email','reset-email','paywall-email'];

const MESSAGE_CLASS_POOL = ['bg-red-50','text-red-700','border','border-red-200','bg-green-50','text-green-700','border-green-200','bg-blue-50','text-blue-700','border-blue-200'];
const MESSAGE_PALETTES = {
  success: ['bg-green-50','text-green-700','border','border-green-200'],
  info: ['bg-blue-50','text-blue-700','border','border-blue-200'],
  error: ['bg-red-50','text-red-700','border','border-red-200']
};

const VOICE_CREATIVITY_LABELS = {1: 'Conservative', 2: 'Safe', 3: 'Balanced', 4: 'Creative', 5: 'Wildly Creative'};
const VOICE_INTENSITY_LABELS = {1: 'Subtle', 2: 'Gentle', 3: 'Moderate', 4: 'Bold', 5: 'Strong'};

function resetMessageElement(el){
  if (!el) return;
  MESSAGE_CLASS_POOL.forEach(cls => el.classList.remove(cls));
  el.textContent = '';
  el.classList.add('hidden');
}

function setStatusMessage(el, message, type = 'error'){
  if (!el) return;
  if (!message){
    resetMessageElement(el);
    return;
  }
  resetMessageElement(el);
  const palette = MESSAGE_PALETTES[type] || MESSAGE_PALETTES.error;
  palette.forEach(cls => el.classList.add(cls));
  el.textContent = message;
  el.classList.remove('hidden');
}

function clearAuthMessage(){
  resetMessageElement(document.getElementById('auth-message'));
}

function setAuthMessage(message, type = 'error'){
  setStatusMessage(document.getElementById('auth-message'), message, type);
}

function clearPaywallMessage(){
  resetMessageElement(document.getElementById('paywall-message'));
}

function setPaywallMessage(message, type = 'error'){
  setStatusMessage(document.getElementById('paywall-message'), message, type);
}

function prefillAuthEmail(value){
  if (!value) return;
  EMAIL_INPUT_IDS.forEach(id => {
    const field = document.getElementById(id);
    if (field && !field.value){
      field.value = value;
    }
  });
}

function getKnownEmailValue(){
  for (const id of EMAIL_INPUT_IDS){
    const field = document.getElementById(id);
    const val = field?.value?.trim();
    if (val) return val;
  }
  return '';
}

function broadcastEmailValue(sourceId, value){
  EMAIL_INPUT_IDS.forEach(id => {
    if (id === sourceId) return;
    const input = document.getElementById(id);
    if (!input) return;
    const active = document.activeElement === input;
    if (active && input.value && input.value !== value) return;
    input.value = value;
  });
}

function initEmailSync(){
  EMAIL_INPUT_IDS.forEach(id => {
    const input = document.getElementById(id);
    if (!input) return;
    input.addEventListener('input', () => {
      broadcastEmailValue(id, input.value);
    });
  });
}

function setAuthView(view = 'login', opts = {}){
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.dataset.authView = view;
  const meta = AUTH_VIEW_META[view] || AUTH_VIEW_META.login;
  const titleEl = document.getElementById('auth-title');
  if (titleEl) titleEl.textContent = meta.title;
  const subtitleEl = document.getElementById('auth-subtitle');
  if (subtitleEl){
    if (meta.subtitle){
      subtitleEl.textContent = meta.subtitle;
      subtitleEl.classList.remove('hidden');
    } else {
      subtitleEl.classList.add('hidden');
    }
  }
  Object.entries(AUTH_FORM_IDS).forEach(([key, formId]) => {
    const form = document.getElementById(formId);
    if (form) form.classList.toggle('hidden', key !== view);
  });
  document.querySelectorAll('[data-auth-tab]').forEach(tab => {
    const isActive = tab.dataset.authTab === view;
    tab.classList.toggle('auth-tab--active', isActive);
    tab.classList.toggle('bg-white', isActive);
    tab.classList.toggle('shadow', isActive);
    tab.classList.toggle('text-slate-900', isActive);
    tab.classList.toggle('text-slate-500', !isActive);
    tab.setAttribute('aria-selected', isActive ? 'true' : 'false');
  });
  requestAnimationFrame(() => {
    let target = null;
    if (opts.focusField === 'password'){
      if (view === 'login') target = document.getElementById('auth-password');
      else if (view === 'signup') target = document.getElementById('signup-password');
      else if (view === 'confirm-reset') target = document.getElementById('confirm-password');
    }
    if (!target){
      const activeForm = document.getElementById(AUTH_FORM_IDS[view]);
      target = activeForm?.querySelector('[data-autofocus]') || activeForm?.querySelector('input, select, textarea, button');
    }
    if (target && typeof target.focus === 'function'){
      target.focus({ preventScroll: true });
    }
  });
}

(function bootstrapInitialUser(){
  if (typeof window === 'undefined') return;
  try {
    const attr = document?.body?.dataset?.initialUser;
    if (typeof attr !== 'undefined') {
      const parsed = attr ? JSON.parse(attr) : null;
      setCurrentUser(parsed);
      delete document.body.dataset.initialUser;
      return;
    }
  } catch (err) {
    console.debug('initial user hydration failed', err);
  }
  if (Object.prototype.hasOwnProperty.call(window, '__INITIAL_USER')){
    setCurrentUser(window.__INITIAL_USER);
    delete window.__INITIAL_USER;
  }
})();

// Attach handlers early to server-rendered industry choices so tests that
// click them immediately after navigation will trigger the same logic as
// client-rendered choices. This runs before full config hydration.
function attachEarlyIndustryHandlers(){
  try{
    const wrap = document.getElementById('industries');
    if (!wrap) return;
    const existing = wrap.querySelectorAll('.choice');
    if (existing && existing.length > 0){
      existing.forEach(el => {
        if (el.dataset._handler_attached) return;
        el.dataset._handler_attached = '1';
        el.addEventListener('click', () => {
          const key = el.dataset.industry || el.dataset.key || el.getAttribute('data-key');
          const label = (el.querySelector && el.querySelector('.title')) ? el.querySelector('.title').textContent.trim() : el.textContent.trim();
          const opt = (CFG && CFG.industries) ? (CFG.industries.find(o => o.key === key) || { key, label }) : { key, label };
          // visual selection
          wrap.querySelectorAll('.choice').forEach(c => c.classList.remove('selected'));
          el.classList.add('selected');
          // update answers state similar to renderIndustryChoices
          answers.industry = opt.label;
          answers.industry_key = opt.key;
          const manualKeywords = answers.manual_keywords || [];
          answers.brand_keywords = [...manualKeywords];
          answers.details = {};
          try{ if (typeof renderIndustryQuestions === 'function') renderIndustryQuestions(opt.key); }catch(e){}
          try{ if (typeof fetchAndApplyGoodDefaults === 'function') fetchAndApplyGoodDefaults(opt.key).catch(()=>{}); }catch(e){}
          try{
            const noteInput = document.getElementById('note');
            const meta = (CFG && CFG.industries || []).find(i => i.key === opt.key) || {};
            const sk = document.getElementById('suggested-keywords');
            if (sk){ sk.innerHTML = ''; const kws = meta.suggested_keywords || []; kws.forEach(k => { const btn = document.createElement('button'); btn.className = 'choice text-sm preselected'; btn.textContent = k; btn.title = 'Preselected keyword for this industry'; btn.addEventListener('click', () => { toggleKeyword(k); btn.classList.toggle('selected'); }); sk.appendChild(btn); }); }
            if (noteInput) noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
            const suggestedKeywords = meta.suggested_keywords || [];
            if (suggestedKeywords.length > 0) { answers.brand_keywords = answers.brand_keywords || []; suggestedKeywords.forEach(kw => { if (!answers.brand_keywords.includes(kw)) answers.brand_keywords.push(kw); }); }
            try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
          }catch(e){}
          updateSummary();
          if (step === 1 && nextBtn && typeof nextBtn.focus === 'function') nextBtn.focus();
        });
      });
    }
  }catch(e){ /* safe no-op */ }
}

if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', attachEarlyIndustryHandlers);
else attachEarlyIndustryHandlers();

async function refreshCurrentUser(){
  try{
    const res = await fetch('/api/current_user', { credentials: 'include' });
    if (!res.ok){ setCurrentUser(null); return null; }
    const data = await res.json().catch(()=>null);
    if (data && data.id){ setCurrentUser(data); }
    else { setCurrentUser(null); }
    return window.CURRENT_USER;
  }catch(e){ return null; }
}

function isLoggedIn(){
  return !!(window.CURRENT_USER && window.CURRENT_USER.id);
}

function updateAccessUi(){
  const user = window.CURRENT_USER || {};
  const isPaid = !!user.is_paid;
  const sampleUsed = !!user.free_sample_used;
  const sampleButtons = [document.getElementById('btn-sample'), document.getElementById('modal-generate-1')];
  sampleButtons.forEach(btn => {
    if (!btn) return;
    if (!isPaid && sampleUsed){
      btn.disabled = true;
      btn.classList.add('opacity-60');
      btn.textContent = 'Free sample used';
    } else {
      btn.disabled = false;
      btn.classList.remove('opacity-60');
      if (btn.id === 'btn-sample' || btn.id === 'modal-generate-1') btn.textContent = 'Generate 1-day sample';
    }
  });
  const gatedButtons = [document.getElementById('btn-30'), document.getElementById('modal-generate-7'), document.getElementById('modal-generate-30'), document.getElementById('modal-generate-reels')];
  gatedButtons.forEach(btn => {
    if (!btn) return;
    if (!isPaid){
      btn.dataset.requiresPaid = '1';
      if (btn.id === 'modal-generate-7') btn.textContent = 'Unlock 7-day plan';
      if (btn.id === 'modal-generate-30' || btn.id === 'btn-30') btn.textContent = 'Unlock 30-day plan';
      if (btn.id === 'modal-generate-reels') btn.textContent = 'Get 7-day plan';
    } else {
      delete btn.dataset.requiresPaid;
      if (btn.id === 'modal-generate-7') btn.textContent = 'Generate 7-day plan';
      if (btn.id === 'modal-generate-30' || btn.id === 'btn-30') btn.textContent = 'Generate 30-day plan';
      if (btn.id === 'modal-generate-reels') btn.textContent = 'Generate 7-day plan';
    }
  });
}

async function loadFlags(){
  try{
    const r = await fetch('/static/content/flags.json', { cache: 'no-store' });
    if (r.ok) FLAGS = await r.json();
  }catch(e){ /* swallow */ }
}

async function loadConfig(){
  const res = await fetch('/static/content/config.json', { cache: 'no-store' });
  if (!res.ok) throw new Error('Could not load config.json');
  CFG = await res.json();
  window.CFG = CFG; // handy for debugging
  window.FLAGS = FLAGS;

  // populate paywall price UI if present
  try{
    const priceEl = document.getElementById('paywall-price');
    const descEl = document.getElementById('paywall-price-desc');
    if (priceEl && CFG && CFG.pricing && CFG.pricing.monthly_display) priceEl.textContent = CFG.pricing.monthly_display;
    if (descEl && CFG && CFG.pricing && CFG.pricing.description) descEl.textContent = CFG.pricing.description;
  }catch(e){/* ignore */}
  // prefer authoritative price from server (Stripe) when available
  try{
    const r2 = await fetch('/api/stripe-price', { credentials: 'include' });
    if (r2.ok){
      const j2 = await r2.json().catch(()=>null);
      const priceEl = document.getElementById('paywall-price');
      const descEl = document.getElementById('paywall-price-desc');
      if (j2 && j2.ok && j2.price && j2.price.display){
        if (priceEl) priceEl.textContent = j2.price.display;
        // show product name or keep description
        if (descEl) descEl.textContent = (j2.price.product && j2.price.product.name) ? j2.price.product.name : (CFG && CFG.pricing && CFG.pricing.description) || '';
        // also update subscribe button copy if present
        try{
          const subBtn = document.getElementById('paywall-subscribe');
          if (subBtn) subBtn.innerHTML = `Subscribe for ${j2.price.display}`;
        }catch(e){/* ignore */}
      }
    }
  }catch(e){ /* ignore */ }

  // render using CFG
  renderIndustryChoices(CFG.industries || []);
  renderToneChoices(CFG.tones || []);
  renderPlatformChoices(CFG.platforms || []);
  showStep(step);
  updateSummary();
  // now that config is rendered, try to load any saved profile (so industries map correctly)
  try{ await loadSavedProfile(); }catch(e){/* ignore */}
}

// Step registry - single source of truth for wizard steps
function getWizardSteps() {
  const steps = [
    { id: 'industry', stepNumber: 1, dataStep: '1', title: 'Choose your industry', isEnabled: true },
    { id: 'brand-kit', stepNumber: 2, dataStep: '2', title: 'Brand Kit (Recommended)', isEnabled: true },
    { id: 'context', stepNumber: 3, dataStep: '3', title: 'Add quick context', isEnabled: !skipStep2 },
    { id: 'tone-platforms', stepNumber: 4, dataStep: '4', title: 'Dial in your tone and channels', isEnabled: true },
    { id: 'brand-inspiration', stepNumber: 5, dataStep: '5', title: 'Brand Inspiration', isEnabled: true },
    { id: 'keywords', stepNumber: 6, dataStep: '6', title: 'Lock in keywords & notes', isEnabled: true }
  ];
  
  // Filter to enabled steps only
  const enabledSteps = steps.filter(s => s.isEnabled);
  
  // Renumber to consecutive indices for display
  enabledSteps.forEach((s, idx) => {
    s.displayIndex = idx + 1;
  });
  
  return enabledSteps;
}

function getTotalSteps() {
  return getWizardSteps().length;
}

function getCurrentStepIndex() {
  // Find current step in the enabled steps list
  const steps = getWizardSteps();
  const currentStepData = step; // This is the data-step value
  const foundIndex = steps.findIndex(s => parseInt(s.dataStep) === currentStepData);
  return foundIndex >= 0 ? foundIndex : 0;
}

let step = 1;
const answers = {
  industry: "", tone: "", platforms: ["instagram"],
  brand_keywords: [], niche_keywords: [], include_images: true,
  company: "",
  goals: [], details: {},
  brand_inspirations: [],
  brand_anti_inspirations: [],
  vibe_preset: null,
  brand_kit: {
    business_name: "",
    services: [],
    audience: "",
    pain: "",
    outcome: "",
    differentiators: [],
    proof: "",
    email: { name: "", title: "", contact: "" },
    quotes: { deposit: "", turnaround: "", validity: "", payment_methods: "" },
    logo: null
  },
  selected_focus_topic_ids: [],
  selected_audience_ids: [],
  selected_offer_ids: [],
  selected_proof_ids: [],
  selected_cta_intent_id: null,
  custom_chips: {
    focus_topics: [],
    audience: [],
    offers: [],
    proof: [],
    ctas: []
  }
};

// Bridge function exposed on window that allows server-rendered buttons to
// select an industry and update the closure-scoped `answers` variable.
// This function runs inside the same closure as the rest of the app so it
// can mutate local vars like `answers`, call internal helpers, and keep
// behavior consistent with client-rendered selections.
window.__selectIndustryBridge = function(key, label){
  try{
    const wrap = document.getElementById('industries') || document.getElementById('qb-industries');
    if (wrap) wrap.querySelectorAll('.choice').forEach(c=>c.classList.remove('selected'));
    const el = document.querySelector('[data-industry="'+key+'"]');
    if (el) el.classList.add('selected');
    answers.industry = label;
    answers.industry_key = key;
    const manualKeywords = answers.manual_keywords || [];
    answers.brand_keywords = [...manualKeywords];
    answers.details = {};
    try{ renderIndustryQuestions && renderIndustryQuestions(key); }catch(e){}
    try{ if (typeof fetchAndApplyGoodDefaults === 'function') fetchAndApplyGoodDefaults(key).catch(()=>{}); }catch(e){}
    try{
      const noteInput = document.getElementById('note');
      const meta = (CFG && CFG.industries || []).find(i => i.key === key) || {};
      const sk = document.getElementById('suggested-keywords');
      if (sk){ sk.innerHTML = ''; const kws = meta.suggested_keywords || []; kws.forEach(k => { const btn = document.createElement('button'); btn.className = 'choice text-sm preselected'; btn.textContent = k; btn.title = 'Preselected keyword for this industry'; btn.addEventListener('click', () => { toggleKeyword(k); btn.classList.toggle('selected'); }); sk.appendChild(btn); }); }
      if (noteInput) noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
      const suggestedKeywords = meta.suggested_keywords || [];
      if (suggestedKeywords.length > 0) { answers.brand_keywords = answers.brand_keywords || []; suggestedKeywords.forEach(kw => { if (!answers.brand_keywords.includes(kw)) answers.brand_keywords.push(kw); }); }
      try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
    }catch(e){}
    updateSummary();
    if (step === 1 && nextBtn && typeof nextBtn.focus === 'function') nextBtn.focus();
  }catch(e){/* ignore */}
};
// Diagnostic accessor for tests/debug scripts to read the internal wizard step
window.__getWizardStep = function(){ try{ return typeof step !== 'undefined' ? step : null; }catch(e){ return null; } };

// Also listen for a custom event so server-side buttons (or test helpers)
// can dispatch an 'industry-selected' event and the app will update its
// closure-scoped state accordingly. This is a resilient way to bridge
// server-rendered markup and the in-closure data model.
document.addEventListener('industry-selected', (ev) => {
  try{
    const d = ev && ev.detail ? ev.detail : null;
    if (!d) return;
    const key = d.key;
    const label = d.label;
    const wrap = document.getElementById('industries') || document.getElementById('qb-industries');
    if (wrap) wrap.querySelectorAll('.choice').forEach(c=>c.classList.remove('selected'));
    const el = document.querySelector('[data-industry="'+key+'"]');
    if (el) el.classList.add('selected');
    answers.industry = label;
    answers.industry_key = key;
    const manualKeywords = answers.manual_keywords || [];
    answers.brand_keywords = [...manualKeywords];
    answers.details = {};
    try{ renderIndustryQuestions && renderIndustryQuestions(key); }catch(e){}
    try{ if (typeof fetchAndApplyGoodDefaults === 'function') fetchAndApplyGoodDefaults(key).catch(()=>{}); }catch(e){}
    try{
      const noteInput = document.getElementById('note');
      const meta = (CFG && CFG.industries || []).find(i => i.key === key) || {};
      const sk = document.getElementById('suggested-keywords');
      if (sk){ sk.innerHTML = ''; const kws = meta.suggested_keywords || []; kws.forEach(k => { const btn = document.createElement('button'); btn.className = 'choice text-sm preselected'; btn.textContent = k; btn.title = 'Preselected keyword for this industry'; btn.addEventListener('click', () => { toggleKeyword(k); btn.classList.toggle('selected'); }); sk.appendChild(btn); }); }
      if (noteInput) noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
      const suggestedKeywords = meta.suggested_keywords || [];
      if (suggestedKeywords.length > 0) { answers.brand_keywords = answers.brand_keywords || []; suggestedKeywords.forEach(kw => { if (!answers.brand_keywords.includes(kw)) answers.brand_keywords.push(kw); }); }
      try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
    }catch(e){}
    updateSummary();
    if (step === 1 && nextBtn && typeof nextBtn.focus === 'function') nextBtn.focus();
  }catch(e){/* ignore */}
});

// Allow external scripts to request brand-kit hydration if the main
// bootstrap path hasn't run yet. Tests and server-side fallbacks can
// dispatch the 'hydrate-brand-kit' event to initialize listeners.
document.addEventListener('hydrate-brand-kit', () => {
  try{
    if (typeof hydrateBrandKitUI === 'function') hydrateBrandKitUI();
    else if (typeof setupBrandKitListeners === 'function') setupBrandKitListeners();
  }catch(e){/* ignore */}
});

const prevBtn = document.getElementById("prev");
const nextBtn = document.getElementById("next");
const results = document.getElementById("results");
const stepsBar = document.getElementById("steps");
const btnSample = document.getElementById("btn-sample");
const btn30 = document.getElementById("btn-30");
const finishStatus = document.getElementById('finish-status');
const finishStatusIcon = document.getElementById('finish-status-icon');
const finishStatusTitle = document.getElementById('finish-status-title');
const finishStatusDetail = document.getElementById('finish-status-detail');
const previewHint = document.getElementById('preview-hint');
const previewJumpBtn = document.getElementById('jump-to-preview');
const previewGenerateLink = document.getElementById('generate-after-preview');
let finishCountdownInterval = null;
let skipStep2 = false;

// Helper: attempt to boot TierWizard with a short retry loop so we are
// tolerant of script load order and hydration races. Returns true on
// successful boot, false otherwise.
async function safeBootTierWizard(flags, profile){
  try{
    const maxMs = 5000;
    const interval = 100;
    const start = Date.now();
    while (Date.now() - start < maxMs) {
      if (window.TierWizard && typeof window.TierWizard.boot === 'function') {
        try{
          await window.TierWizard.boot({ flags, profile });
          return true;
        }catch(e){
          console.error('TierWizard.boot failed', e);
          return false;
        }
      }
      await new Promise(r => setTimeout(r, interval));
    }
    console.warn('TierWizard.boot not available after timeout');
    return false;
  }catch(e){
    console.error('safeBootTierWizard error', e);
    return false;
  }
}

// load optional flags then config (share promise for later waits)
const bootPromise = loadFlags().then(loadConfig).catch(err => { console.error(err); });
bootPromise
  .then(async () => {
    // Hydrate legacy preview UI first (non-destructive)
    await hydrateWizardPreview();

    // If we're on the /app route, and tier_wizard flag is enabled, prefer TierWizard
    try {
      const path = window.location && window.location.pathname ? window.location.pathname : '';
      if (path.startsWith('/app')) {
        const flags = window.FLAGS || {};
        if (flags.tierWizard) {
          // Try to safely boot the TierWizard (wait a short time if the
          // bundle hasn't parsed yet). If boot succeeds, hide legacy
          // containers and avoid running the legacy boot path.
          let profile = null;
          try { profile = await loadSavedProfile(); } catch (e) { /* ignore */ }
          const booted = await safeBootTierWizard(flags, profile);
          if (booted) {
            // Hide legacy containers used by the step wizard
            const legacySelectors = ['#wiz', '#steps', '#steps-mobile', '.step-panel', '.steps'];
            legacySelectors.forEach(sel => {
              document.querySelectorAll(sel).forEach(el => {
                try { el.style.display = 'none'; } catch (e) { /* ignore */ }
              });
            });

            // Ensure tier root exists and is visible
            const tw = document.getElementById('tier-wizard-root');
            if (tw) tw.style.display = '';

            // Early return: do not run legacy showStep boot path for /app
            return;
          }
        }
      }
    } catch (err) {
      console.error('Error while deciding tier wizard boot:', err);
    }
  })
  .catch(() => hydrateWizardPreview());

// attempt to load saved profile for this session and prefill fields
async function loadSavedProfile(){
  try{
  const res = await fetch('/api/profile', { credentials: 'include' });
    if (!res.ok) return;
    const body = await res.json().catch(()=>null);
    if (!body || body.ok === false) return;
    const p = body.profile || body;
    if (!p || !p.id) return;
    // prefill inputs
    if (p.company) {
      const c = document.getElementById('company');
      if (c && !c.value) c.value = p.company;
      answers.company = p.company;
    }
    if (p.brand_keywords && p.brand_keywords.length){
      // load saved keywords but we'll reconcile with industry suggested keywords when industry is set
      answers.brand_keywords = p.brand_keywords || [];
    }
    if (p.platforms && p.platforms.length) answers.platforms = p.platforms;
    if (p.industry) answers.industry = p.industry;
    if (p.tone) answers.tone = p.tone;
    if (p.goals && p.goals.length) answers.goals = p.goals;
    if (p.details) {
      answers.details = p.details || {};
      if (answers.details.creativity) {
        const el = document.getElementById('voice-creativity');
        const label = document.getElementById('creativity-val');
        if (el) el.value = answers.details.creativity;
        if (label) label.textContent = VOICE_CREATIVITY_LABELS[answers.details.creativity] || 'Balanced';
      }
      if (answers.details.intensity) {
        const el = document.getElementById('voice-intensity');
        const label = document.getElementById('intensity-val');
        if (el) el.value = answers.details.intensity;
        if (label) label.textContent = VOICE_INTENSITY_LABELS[answers.details.intensity] || 'Moderate';
      }
    }
    // Load brand inspiration data
    if (p.brand_inspirations && Array.isArray(p.brand_inspirations)) {
      answers.brand_inspirations = p.brand_inspirations;
    }
    if (p.brand_anti_inspirations && Array.isArray(p.brand_anti_inspirations)) {
      answers.brand_anti_inspirations = p.brand_anti_inspirations;
    }
    if (p.vibe_preset) {
      answers.vibe_preset = p.vibe_preset;
    }
    // Load chip selections
    if (p.selected_focus_topic_ids && Array.isArray(p.selected_focus_topic_ids)) {
      answers.selected_focus_topic_ids = p.selected_focus_topic_ids;
    }
    if (p.selected_audience_ids && Array.isArray(p.selected_audience_ids)) {
      answers.selected_audience_ids = p.selected_audience_ids;
    }
    if (p.selected_offer_ids && Array.isArray(p.selected_offer_ids)) {
      answers.selected_offer_ids = p.selected_offer_ids;
    }
    if (p.selected_proof_ids && Array.isArray(p.selected_proof_ids)) {
      answers.selected_proof_ids = p.selected_proof_ids;
    }
    if (p.selected_cta_intent_id) {
      answers.selected_cta_intent_id = p.selected_cta_intent_id;
    }
    // Load custom chips
    if (p.custom_chips && typeof p.custom_chips === 'object') {
      answers.custom_chips = p.custom_chips;
    }
    updateSummary();
  }catch(e){/* ignore */}
}

document.addEventListener('DOMContentLoaded', () => {
  // load content metadata
  (async ()=>{
    try{
  const r = await fetch('/api/content', { credentials: 'include' });
      if (!r.ok) return;
      const j = await r.json();
      const el = document.getElementById('content-version');
      if (el) el.textContent = j.version || 'local';
      window.CONTENT_META = j;
    }catch(e){/* ignore */}
    // query server for current user
    try{
      await refreshCurrentUser();
    }catch(e){/* ignore */}
    const quickStartBtn = document.getElementById('quick-start');
    if (quickStartBtn){
      quickStartBtn.addEventListener('click', async (event) => {
        event.preventDefault();
        await handleQuickStart(quickStartBtn);
      });
    }
    const scrollBtn = document.getElementById('scroll-to-wizard');
    if (scrollBtn){
      scrollBtn.addEventListener('click', () => {
        document.getElementById('wiz')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
    }
    const createAcctBtn = document.getElementById('cta-create-account');
    if (createAcctBtn){
      createAcctBtn.addEventListener('click', () => openAuthModal('signup'));
    }
    const signInBtn = document.getElementById('cta-sign-in');
    if (signInBtn){
      signInBtn.addEventListener('click', () => openAuthModal('login'));
    }

    // Voice Dials Logic
    const creativitySlider = document.getElementById('voice-creativity');
    const intensitySlider = document.getElementById('voice-intensity');
    const creativityVal = document.getElementById('creativity-val');
    const intensityVal = document.getElementById('intensity-val');

    if (creativitySlider && creativityVal) {
        creativitySlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            creativityVal.textContent = VOICE_CREATIVITY_LABELS[val] || 'Balanced';
            answers.details = answers.details || {};
            answers.details.creativity = val;
            updateSummary();
        });
    }

    if (intensitySlider && intensityVal) {
        intensitySlider.addEventListener('input', (e) => {
            const val = parseInt(e.target.value);
            intensityVal.textContent = VOICE_INTENSITY_LABELS[val] || 'Moderate';
            answers.details = answers.details || {};
            answers.details.intensity = val;
            updateSummary();
        });
    }
  })();

  // Smart defaults to reduce clicks
  setTimeout(() => {
    // Pre-select "Friendly" tone (most common)
    const friendlyTone = document.querySelector('#tones .choice[data-key="friendly"]');
    if (friendlyTone && !document.querySelector('#tones .choice.selected')) {
      friendlyTone.click();
    }

    // Pre-select Instagram platform (most common)
    const instagramPlatform = document.querySelector('#platforms .choice[data-key="instagram"]');
    if (instagramPlatform && !document.querySelector('#platforms .choice.selected')) {
      instagramPlatform.click();
    }

    // Pre-select "Custom" industry if no other is selected (gives users flexibility)
    const customIndustry = document.querySelector('#industries .choice[data-key="other"]');
    if (customIndustry && !document.querySelector('#industries .choice.selected')) {
      setTimeout(() => customIndustry.click(), 500); // Small delay to ensure UI is ready
    }
  }, 1000);

  // normalize company on blur
  const c = document.getElementById('company');
  if (c){
    c.addEventListener('blur', () => { c.value = c.value.trim().replace(/\s+/g,' ').split(' ').map(w=>w[0]?w[0].toUpperCase()+w.slice(1):'').join(' '); answers.company = c.value; updateSummary(); });
  }

  // dev create-user form (if present)
  const devForm = document.getElementById('dev-create-form');
  if (devForm){
    devForm.addEventListener('submit', async (ev) => {
      ev.preventDefault();
      const email = document.getElementById('dev-email').value.trim();
      const pw = document.getElementById('dev-password').value || 'password';
      const select = document.getElementById('dev-templates');
      const chosen = Array.from(select?.selectedOptions || []).map(opt => opt.value).filter(Boolean);
      const templates = chosen.length ? chosen : ['free'];
      const btn = document.getElementById('dev-create-btn'); setButtonLoading(btn, true);
      try{
        const payload = { email, password: pw };
        if (templates.length === 1) payload.template = templates[0];
        else payload.templates = templates;
        const r = await fetch('/__dev__/create_user', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify(payload) });
        const j = await r.json().catch(()=>null);
        if (!r.ok){ alert((j && j.error) || 'Could not create dev user'); return; }
        const active = j?.active_user || j;
        if (active && active.id){ setCurrentUser(active); }
        const created = Array.isArray(j?.created) ? j.created.length : 1;
        showToast(created > 1 ? `Created ${created} dev users` : 'Dev user created and signed in');
      }catch(e){ alert('Dev create failed'); }
      finally{ setButtonLoading(btn, false); }
    });
  }
  // localize next-billing display on account page if present
  try{
    const nb = document.getElementById('next-billing');
    if (nb){
      const iso = nb.getAttribute('data-iso') || '';
      if (iso){
        const dt = new Date(iso);
        if (!isNaN(dt.getTime())){
          const human = dt.toLocaleString(undefined, { year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
          const now = new Date();
          const diff = Math.max(0, Math.floor((dt - now) / (1000*60*60*24)));
          nb.textContent = human + (isFinite(diff) ? (' (in ' + diff + ' days)') : '');
        }
      }
    }
  }catch(e){/* ignore */}
});

function renderAuthUi(){
  const link = document.querySelector('header .auth-link');
  if (!link) return;
  // ensure we don't attach duplicate handlers
  link.replaceWith(link.cloneNode(true));
  const newLink = document.querySelector('header .auth-link');
  if (window.CURRENT_USER && window.CURRENT_USER.id){
    newLink.textContent = window.CURRENT_USER.email || 'Account';
    newLink.href = '/account';
    // left-click navigates to account; right-click still opens portal
    newLink.addEventListener('click', (e)=>{});
  } else {
    newLink.textContent = 'Sign in';
    newLink.href = '#';
    newLink.addEventListener('click', async (e)=>{ e.preventDefault(); openAuthModal('login'); });
  }
}

// Auth modal helpers
function openAuthModal(view = 'login', opts = {}){
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  if (!document.body.contains(modal)) {
    document.body.appendChild(modal);
  }
  modal.classList.remove('hidden');
  const container = modal.querySelector('[tabindex="-1"]');
  if (container && typeof container.focus === 'function') container.focus();
  clearAuthMessage();
  const knownEmail = opts.prefillEmail || getKnownEmailValue();
  if (knownEmail) prefillAuthEmail(knownEmail);
  setAuthView(view, opts);
  trapFocus(modal);
}
function closeAuthModal(){
  const modal = document.getElementById('auth-modal');
  if (!modal) return;
  modal.classList.add('hidden');
  modal.dataset.authView = 'login';
  clearAuthMessage();
  _restoreLastFocus();
}

// restore focus helper for modals
function _restoreLastFocus(){
  try{
    const prev = window.__lastFocusedBeforeModal;
    if (prev && typeof prev.focus === 'function') prev.focus({preventScroll:true});
  }catch(e){ /* ignore */ }
  try{ delete window.__lastFocusedBeforeModal; }catch(e){}
}

function navigateAuthView(view = 'login', opts = {}){
  const modal = document.getElementById('auth-modal');
  if (modal && !modal.classList.contains('hidden')){
    clearAuthMessage();
    const knownEmail = opts.prefillEmail || getKnownEmailValue();
    if (knownEmail) prefillAuthEmail(knownEmail);
    setAuthView(view, opts);
    return;
  }
  openAuthModal(view, opts);
}

document.addEventListener('DOMContentLoaded', () => {
  // modal switch buttons
  document.querySelectorAll('[data-auth-tab]').forEach(btn => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      navigateAuthView(btn.dataset.authTab || 'login');
    });
  });
  document.querySelectorAll('[data-auth-action]').forEach(btn => {
    btn.addEventListener('click', (event) => {
      event.preventDefault();
      const targetView = btn.dataset.authAction || 'login';
      const opts = {};
      const emailField = btn.closest('form')?.querySelector('input[type="email"]');
      if (emailField && emailField.value){
        opts.prefillEmail = emailField.value.trim();
      }
      navigateAuthView(targetView, opts);
    });
  });
  document.getElementById('auth-close')?.addEventListener('click', (event) => {
    event.preventDefault();
    closeAuthModal();
  });
  const authModal = document.getElementById('auth-modal');
  authModal?.addEventListener('click', (event) => {
    if (event.target === authModal){
      closeAuthModal();
    }
  });

  initEmailSync();

  // navigation: mark current page links with aria-current for assistive tech
  try{
    const loc = window.location && window.location.pathname ? window.location.pathname.replace(/\/$/, '') : '/';
    document.querySelectorAll('header a[href]').forEach(a => {
      try{
        const href = a.getAttribute('href') || '';
        const url = new URL(href, window.location.origin);
        const path = url.pathname.replace(/\/$/, '');
        if (path === loc){ a.setAttribute('aria-current', 'page'); }
        else { a.removeAttribute('aria-current'); }
      }catch(e){}
    });
  }catch(e){}

  // paywall sign-in link (for users who already have an account)
  const paywallSigninLink = document.getElementById('paywall-signin-link');
  if (paywallSigninLink){
    paywallSigninLink.addEventListener('click', () => {
      const email = document.getElementById('paywall-email')?.value?.trim();
      if (email) broadcastEmailValue('paywall-email', email);
      openAuthModal('login', { prefillEmail: email || getKnownEmailValue() });
    });
  }

  // paywall close buttons / backdrop
  document.querySelectorAll('[data-paywall-close]').forEach(btn => btn.addEventListener('click', (e) => { e.preventDefault(); closePaywall(); }));
  const payModal = document.getElementById('paywall-modal');
  payModal?.addEventListener('click', (e) => { if (e.target === payModal) closePaywall(); });

  // login submit
  const loginForm = document.getElementById('login-form');
  loginForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthMessage();
    const email = document.getElementById('auth-email').value.trim();
    const pw = document.getElementById('auth-password').value;
    if (!email || !pw){
      setAuthMessage('Enter both email and password to continue.', 'error');
      return;
    }
    const submitBtn = e.submitter || loginForm.querySelector('button[type=submit]');
    try{
      setButtonLoading(submitBtn, true);
  const r = await fetch('/api/login', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ email, password: pw }) });
      const j = await r.json().catch(()=>null);
    if (!r.ok){ setAuthMessage((j && j.error) || 'Sign in failed', 'error'); return; }
  setCurrentUser(userFromResponse(j)); closeAuthModal(); showToast('Signed in');
      // If the paywall modal is open, continue to the subscribe flow automatically
      try{
        const payModal = document.getElementById('paywall-modal');
        if (payModal && !payModal.classList.contains('hidden')){
          const subBtn = document.getElementById('paywall-subscribe');
          if (subBtn) subBtn.click();
        }
      }catch(e){}
    }catch(err){ setAuthMessage('Sign in failed. Please try again.', 'error'); }
    finally{ setButtonLoading(submitBtn, false); }
  });

  // signup submit
  const signupForm = document.getElementById('signup-form');
  signupForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthMessage();
    const email = document.getElementById('signup-email').value.trim();
    const pw = document.getElementById('signup-password').value;
    if (!email){
      setAuthMessage('Enter your email to create an account.', 'error');
      return;
    }
    if (!pw || pw.length < 6){
      setAuthMessage('Passwords need at least 6 characters.', 'error');
      return;
    }
    const btn = e.submitter || signupForm.querySelector('button[type=submit]');
    try{
      setButtonLoading(btn, true);
  const r = await fetch('/api/signup', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ email, password: pw }) });
      const j = await r.json().catch(()=>null);
    if (!r.ok){ setAuthMessage((j && j.error) || 'Sign up failed', 'error'); return; }
  setCurrentUser(userFromResponse(j)); closeAuthModal(); showToast('Account created');
    }catch(err){ setAuthMessage('Sign up failed. Please try again.', 'error'); }
    finally{ setButtonLoading(btn, false); }
  });

  // password reset request submit
  const resetForm = document.getElementById('reset-form');
  resetForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthMessage();
    const emailInput = document.getElementById('reset-email');
    const email = emailInput?.value.trim();
    if (!email){
      setAuthMessage('Enter your account email to continue.', 'error');
      emailInput?.focus();
      return;
    }
    const btn = e.submitter || resetForm.querySelector('button[type=submit]');
    try{
      setButtonLoading(btn, true);
  const r = await fetch('/api/request-password-reset', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ email }) });
      const j = await r.json().catch(()=>null);
      if (!r.ok){ setAuthMessage((j && j.error) || 'Could not send reset email', 'error'); return; }
      prefillAuthEmail(email);
      if (j && j.token){
        const tokenField = document.getElementById('confirm-token');
        if (tokenField) tokenField.value = j.token;
      }
      setAuthMessage('Check your email for a reset link. Paste the token below to finish up.', 'success');
      setAuthView('confirm-reset');
    }catch(err){
      console.error('password reset request failed', err);
      setAuthMessage('Reset request failed. Try again shortly.', 'error');
    }finally{
      setButtonLoading(btn, false);
    }
  });

  // confirm reset submit
  const confirmResetForm = document.getElementById('confirm-reset-form');
  confirmResetForm?.addEventListener('submit', async (e) => {
    e.preventDefault();
    clearAuthMessage();
    const tokenInput = document.getElementById('confirm-token');
    const passwordInput = document.getElementById('confirm-password');
    const token = tokenInput?.value.trim();
    const pw = passwordInput?.value;
    if (!token){
      setAuthMessage('Enter the reset token from your email.', 'error');
      tokenInput?.focus();
      return;
    }
        // If server-side rendered choices are present, attach handlers instead of
        // recreating elements to avoid race/duplication during e2e tests.
        const existing = wrap.querySelectorAll('.choice');
        if (existing && existing.length > 0) {
          existing.forEach(el => {
            // prefer data-key, fallback to data-industry for serverside markup
            const key = el.dataset.key || el.dataset.industry || el.getAttribute('data-key') || el.getAttribute('data-industry');
            // find matching opt if available
            const opt = list.find(o => o.key === key);
            el.addEventListener('click', () => {
              wrap.querySelectorAll('.choice').forEach(c=>c.classList.remove('selected'));
              el.classList.add('selected');
              if (opt) {
                answers.industry = opt.label;
                answers.industry_key = opt.key;
                const manualKeywords = answers.manual_keywords || [];
                answers.brand_keywords = [...manualKeywords];
                answers.details = {};
                renderIndustryQuestions(opt.key);
                fetchAndApplyGoodDefaults(opt.key).catch(err => console.error('Failed to apply good defaults:', err));
                // suggested keywords
                try{
                  const noteInput = document.getElementById('note');
                  const meta = (CFG && CFG.industries || []).find(i => i.key === opt.key) || {};
                  const sk = document.getElementById('suggested-keywords');
                  if (sk){ sk.innerHTML = ''; const kws = meta.suggested_keywords || []; kws.forEach(k => { const btn = document.createElement('button'); btn.className = 'choice text-sm preselected'; btn.textContent = k; btn.title = 'Preselected keyword for this industry'; btn.addEventListener('click', () => { toggleKeyword(k); btn.classList.toggle('selected'); }); sk.appendChild(btn); }); }
                  if (noteInput) noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
                  const suggestedKeywords = meta.suggested_keywords || [];
                  if (suggestedKeywords.length > 0) { answers.brand_keywords = answers.brand_keywords || []; suggestedKeywords.forEach(kw => { if (!answers.brand_keywords.includes(kw)) answers.brand_keywords.push(kw); }); }
                  try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
                }catch(e){/* ignore */}
              }
              updateSummary();
              if (step === 1 && nextBtn && typeof nextBtn.focus === 'function') nextBtn.focus();
            });
          });
          return;
        }

        // Otherwise render choices from scratch
        list.forEach(opt => {
          const div = document.createElement("button");
          div.className = "choice"; div.setAttribute("data-key", opt.key);
          div.innerHTML = `<div class="emoji">${opt.icon}</div><div class="title">${opt.label}</div>`;
          div.addEventListener("click", () => {
            wrap.querySelectorAll(".choice").forEach(c=>c.classList.remove("selected"));
            div.classList.add("selected");
            // store both key and label for reliable lookups
            answers.industry = opt.label;
            answers.industry_key = opt.key;
            // preserve manually entered keywords, clear industry-specific data
            const manualKeywords = answers.manual_keywords || [];
            answers.brand_keywords = [...manualKeywords];
            answers.details = {};
            renderIndustryQuestions(opt.key);
      
            // Fetch and apply GOOD defaults for this industry
            fetchAndApplyGoodDefaults(opt.key).catch(err => {
              console.error('Failed to apply good defaults:', err);
            });
      
            // set suggested keywords and note placeholder for this industry
            try{
              const noteInput = document.getElementById('note');
              const meta = (CFG && CFG.industries || []).find(i => i.key === opt.key) || {};
              // render suggested keywords as chips
              const sk = document.getElementById('suggested-keywords');
              if (sk){
                sk.innerHTML = '';
                const kws = meta.suggested_keywords || [];
                kws.forEach(k => {
                  const btn = document.createElement('button');
                  btn.className = 'choice text-sm preselected'; btn.textContent = k;
                  btn.title = 'Preselected keyword for this industry';
                  btn.addEventListener('click', () => {
                    toggleKeyword(k);
                    btn.classList.toggle('selected');
                  });
                  sk.appendChild(btn);
                });
              }
              if (noteInput){
                noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
              }
              // set answers.brand_keywords to include the suggested keywords for this industry
              // always add industry-specific keywords to ensure they're preselected
              const suggestedKeywords = meta.suggested_keywords || [];
              if (suggestedKeywords.length > 0) {
                answers.brand_keywords = answers.brand_keywords || [];
                // Add suggested keywords that aren't already in the list
                suggestedKeywords.forEach(kw => {
                  if (!answers.brand_keywords.includes(kw)) {
                    answers.brand_keywords.push(kw);
                  }
                });
              }
              // mark selected state on the rendered chips
              try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
            }catch(e){/* ignore */}
            updateSummary();
            if (step === 1 && nextBtn && typeof nextBtn.focus === 'function'){
              nextBtn.focus();
            }
          });
          wrap.appendChild(div);
        });
  clearPaywallMessage();
  _restoreLastFocus();
}
function showToast(msg){ const t = document.createElement('div'); t.className='fixed bottom-6 right-6 bg-slate-800 text-white px-4 py-2 rounded shadow'; t.textContent=msg; document.body.appendChild(t); setTimeout(()=>t.classList.add('opacity-0'), 2200); setTimeout(()=>t.remove(), 2800); }

function showGlobalAlert(msg, type='error'){
  if (!msg) return;
  let el = document.getElementById('global-alert');
  if (!el){
    el = document.createElement('div');
    el.id = 'global-alert';
    el.setAttribute('role','alert');
    el.setAttribute('aria-live','assertive');
    el.className = 'fixed top-4 left-1/2 -translate-x-1/2 z-50 p-3 rounded-xl shadow';
    document.body.appendChild(el);
  }
  el.textContent = msg;
  // basic color palette mapping
  el.classList.remove('bg-red-50','text-red-700','bg-green-50','text-green-700','bg-blue-50','text-blue-700');
  if (type === 'success') el.classList.add('bg-green-50','text-green-700');
  else if (type === 'info') el.classList.add('bg-blue-50','text-blue-700');
  else el.classList.add('bg-red-50','text-red-700');
  // auto-dismiss
  setTimeout(()=>{ try{ el.remove(); }catch(e){} }, 5000);
}
function showSavingFeedback() {
  const stepTitle = document.getElementById('step-title');
  if (stepTitle) {
    const originalText = stepTitle.textContent;
    stepTitle.textContent = 'Saving...';
    stepTitle.classList.add('text-purple-500');
    setTimeout(() => {
      stepTitle.classList.remove('text-purple-500');
      // Text will be updated by showStep
    }, 600);
  }
}

function setButtonLoading(btn, loading){
  if (!btn) return; 
  if (loading){ btn.dataset.orig = btn.innerHTML; btn.disabled = true; btn.innerHTML = btn.dataset.loadingText || 'Loading…'; }
  else { if (btn.dataset.orig) btn.innerHTML = btn.dataset.orig; btn.disabled = false; }
}

// focus trap helper (basic)
function trapFocus(modal){
  // capture the element that had focus before opening the modal so we can
  // restore it when the modal closes
  try{ window.__lastFocusedBeforeModal = document.activeElement; }catch(e){}
  const focusable = modal.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
  const first = focusable[0];
  const last = focusable[focusable.length-1];
  function keyHandler(e){
    if (e.key === 'Escape') {
      modal.classList.add('hidden');
      document.removeEventListener('keydown', keyHandler);
      try{ if (window.__lastFocusedBeforeModal && typeof window.__lastFocusedBeforeModal.focus === 'function') window.__lastFocusedBeforeModal.focus({preventScroll:true}); }catch(e){}
      try{ delete window.__lastFocusedBeforeModal; }catch(e){}
    }
    if (e.key === 'Tab'){
      if (e.shiftKey && document.activeElement === first){ e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last){ e.preventDefault(); first.focus(); }
    }
  }
  document.addEventListener('keydown', keyHandler);
}

// client-side company validation: returns error message or empty
function validateCompany(name){
  if (!name) return '';
  if (name.length > 100) return 'Company name is too long (max 100 chars).';
  // disallow angle brackets and control characters which are commonly problematic
  if (/[*<>\\\x00-\x1F]/.test(name)) return 'Company name contains invalid characters.';
  if (!/^[\w \-\'\.\&]+$/.test(name)) return 'Company name contains invalid characters.';
  return '';
}

function renderIndustryChoices(list){
  const wrap = document.getElementById("industries");
  if (!wrap) return;
  // If server-side rendered choices exist, attach handlers and avoid
  // re-rendering to prevent races where tests click server elements
  // that don't yet have listeners.
  const existing = wrap.querySelectorAll('.choice');
  if (existing && existing.length > 0) {
    existing.forEach(el => {
      const key = el.dataset.key || el.dataset.industry || el.getAttribute('data-key') || el.getAttribute('data-industry');
      const opt = list.find(o => o.key === key);
      el.addEventListener('click', () => {
        wrap.querySelectorAll('.choice').forEach(c=>c.classList.remove('selected'));
        el.classList.add('selected');
        if (opt) {
          answers.industry = opt.label;
          answers.industry_key = opt.key;
          const manualKeywords = answers.manual_keywords || [];
          answers.brand_keywords = [...manualKeywords];
          answers.details = {};
          renderIndustryQuestions(opt.key);
          fetchAndApplyGoodDefaults(opt.key).catch(err => console.error('Failed to apply good defaults:', err));
          try{
            const noteInput = document.getElementById('note');
            const meta = (CFG && CFG.industries || []).find(i => i.key === opt.key) || {};
            const sk = document.getElementById('suggested-keywords');
            if (sk){ sk.innerHTML = ''; const kws = meta.suggested_keywords || []; kws.forEach(k => { const btn = document.createElement('button'); btn.className = 'choice text-sm preselected'; btn.textContent = k; btn.title = 'Preselected keyword for this industry'; btn.addEventListener('click', () => { toggleKeyword(k); btn.classList.toggle('selected'); }); sk.appendChild(btn); }); }
            if (noteInput) noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
            const suggestedKeywords = meta.suggested_keywords || [];
            if (suggestedKeywords.length > 0) { answers.brand_keywords = answers.brand_keywords || []; suggestedKeywords.forEach(kw => { if (!answers.brand_keywords.includes(kw)) answers.brand_keywords.push(kw); }); }
            try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
          }catch(e){}
        }
        updateSummary();
        if (step === 1 && nextBtn && typeof nextBtn.focus === 'function') nextBtn.focus();
      });
    });
    return;
  }
  wrap.innerHTML = "";
  list.forEach(opt => {
    const div = document.createElement("button");
    div.className = "choice"; div.setAttribute("data-key", opt.key);
    div.innerHTML = `<div class="emoji">${opt.icon}</div><div class="title">${opt.label}</div>`;
    div.addEventListener("click", () => {
      wrap.querySelectorAll(".choice").forEach(c=>c.classList.remove("selected"));
      div.classList.add("selected");
      // store both key and label for reliable lookups
      answers.industry = opt.label;
      answers.industry_key = opt.key;
      // preserve manually entered keywords, clear industry-specific data
      const manualKeywords = answers.manual_keywords || [];
      answers.brand_keywords = [...manualKeywords];
      answers.details = {};
      renderIndustryQuestions(opt.key);
      
      // Fetch and apply GOOD defaults for this industry
      fetchAndApplyGoodDefaults(opt.key).catch(err => {
        console.error('Failed to apply good defaults:', err);
      });
      
      // set suggested keywords and note placeholder for this industry
      try{
        const noteInput = document.getElementById('note');
        const meta = (CFG && CFG.industries || []).find(i => i.key === opt.key) || {};
        // render suggested keywords as chips
        const sk = document.getElementById('suggested-keywords');
        if (sk){
          sk.innerHTML = '';
          const kws = meta.suggested_keywords || [];
          kws.forEach(k => {
            const btn = document.createElement('button');
            btn.className = 'choice text-sm preselected'; btn.textContent = k;
            btn.title = 'Preselected keyword for this industry';
            btn.addEventListener('click', () => {
              toggleKeyword(k);
              btn.classList.toggle('selected');
            });
            sk.appendChild(btn);
          });
        }
        if (noteInput){
          noteInput.placeholder = meta.note_placeholder || noteInput.placeholder;
        }
        // set answers.brand_keywords to include the suggested keywords for this industry
        // always add industry-specific keywords to ensure they're preselected
        const suggestedKeywords = meta.suggested_keywords || [];
        if (suggestedKeywords.length > 0) {
          answers.brand_keywords = answers.brand_keywords || [];
          // Add suggested keywords that aren't already in the list
          suggestedKeywords.forEach(kw => {
            if (!answers.brand_keywords.includes(kw)) {
              answers.brand_keywords.push(kw);
            }
          });
        }
        // mark selected state on the rendered chips
        try{ const sk2 = document.getElementById('suggested-keywords'); if (sk2){ Array.from(sk2.children).forEach(btn => { if (answers.brand_keywords.includes(btn.textContent)) btn.classList.add('selected'); }) } }catch(e){}
      }catch(e){/* ignore */}
      updateSummary();
      if (step === 1 && nextBtn && typeof nextBtn.focus === 'function'){
        nextBtn.focus();
      }
    });
    // if this industry matches the already-selected industry, mark it as selected
    if ((answers.industry_key && answers.industry_key === opt.key) || (!answers.industry_key && answers.industry === opt.label)){
      div.classList.add('selected');
      // ensure questions and placeholders render for the preselected industry
      try{ renderIndustryQuestions(opt.key); const kwInput = document.getElementById('keywords'); const meta = (CFG && CFG.industries || []).find(i => i.key === opt.key) || {}; if (kwInput && !kwInput.value && meta.suggested_keywords) kwInput.value = meta.suggested_keywords.slice(0,4).join(', '); }catch(e){}
    }
    wrap.appendChild(div);
  });
}

// keyword helpers
function toggleKeyword(k){
  answers.brand_keywords = answers.brand_keywords || [];
  const idx = answers.brand_keywords.indexOf(k);
  if (idx === -1) answers.brand_keywords.push(k);
  else answers.brand_keywords.splice(idx,1);
  updateSummary();
}

function clearKeywords(){
  answers.brand_keywords = [];
  answers.manual_keywords = [];
  // Clear visual selection state
  const keywordChips = document.querySelectorAll('#suggested-keywords .choice');
  keywordChips.forEach(chip => chip.classList.remove('selected'));
  updateSummary();
}

// Fetch and apply GOOD defaults for an industry
async function fetchAndApplyGoodDefaults(industryKey){
  if (!industryKey) return;
  
  try {
    const response = await fetch(`/api/industry_packs/${industryKey}/good_defaults`, {
      credentials: 'include'
    });
    
    if (!response.ok) {
      console.warn(`Failed to fetch good_defaults for ${industryKey}`);
      return;
    }
    
    const data = await response.json();
    if (!data.ok || !data.good_defaults) {
      console.warn(`Invalid good_defaults response for ${industryKey}`);
      return;
    }
    
    const chipPresets = data.good_defaults.chip_presets || {};
    
    // Helper function to auto-select chips
    const autoSelectChips = (answersKey, presetKey, count) => {
      if (!answers[answersKey] || answers[answersKey].length === 0) {
        const chips = chipPresets[presetKey] || [];
        answers[answersKey] = chips.slice(0, count).map(chip => chip.id);
      }
    };
    
    // Auto-apply recommended chip selections (but keep them editable)
    // Only apply if user hasn't already made selections
    autoSelectChips('selected_focus_topic_ids', 'focus_topics', 3);
    autoSelectChips('selected_audience_ids', 'audience_chips', 2);
    autoSelectChips('selected_offer_ids', 'offer_chips', 2);
    autoSelectChips('selected_proof_ids', 'proof_chips', 2);
    
    // Store the full chip presets for rendering later if needed
    window.__industryChipPresets = chipPresets;
    
    console.log('Applied GOOD defaults for', industryKey, answers.selected_focus_topic_ids);
    
    // Render chip groups with the fetched presets
    renderChipGroups(chipPresets);
  } catch (error) {
    console.error('Error fetching good_defaults:', error);
  }
}

// Store chip group instances globally for easy access
window.__chipGroups = {};

// Helper function to merge custom chips with presets
function mergeCustomChips(presetChips, customChips) {
  const chips = [...presetChips];
  if (customChips && customChips.length > 0) {
    customChips.forEach(custom => {
      if (!chips.find(c => c.id === custom.id)) {
        chips.push(custom);
      }
    });
  }
  return chips;
}

// Render chip groups with industry presets
function renderChipGroups(chipPresets) {
  if (!chipPresets || !window.ChipGroup) {
    console.warn('ChipGroup not available or no chip presets');
    return;
  }
  
  // Focus Topics
  const focusChips = mergeCustomChips(
    chipPresets.focus_topics || [],
    answers.custom_chips?.focus_topics || []
  );
  window.__chipGroups.focus = new window.ChipGroup({
    containerId: 'chip-group-focus-topics',
    title: 'Focus Topics',
    subtitle: 'What topics do you post about most?',
    chips: focusChips,
    selectedIds: answers.selected_focus_topic_ids || [],
    maxSelect: 3,
    allowWriteIn: true,
    groupKey: 'focus_topics',
    onChangeSelectedIds: (ids) => {
      answers.selected_focus_topic_ids = ids;
    }
  });
  
  // Audience
  const audienceChips = mergeCustomChips(
    chipPresets.audience_chips || [],
    answers.custom_chips?.audience || []
  );
  window.__chipGroups.audience = new window.ChipGroup({
    containerId: 'chip-group-audience',
    title: 'Audience',
    subtitle: 'Who are you trying to reach?',
    chips: audienceChips,
    selectedIds: answers.selected_audience_ids || [],
    maxSelect: 2,
    allowWriteIn: true,
    groupKey: 'audience',
    onChangeSelectedIds: (ids) => {
      answers.selected_audience_ids = ids;
    }
  });
  
  // Offers
  const offerChips = mergeCustomChips(
    chipPresets.offer_chips || [],
    answers.custom_chips?.offers || []
  );
  window.__chipGroups.offers = new window.ChipGroup({
    containerId: 'chip-group-offers',
    title: 'Offers & Services',
    subtitle: 'What do you want to promote?',
    chips: offerChips,
    selectedIds: answers.selected_offer_ids || [],
    maxSelect: 2,
    allowWriteIn: true,
    groupKey: 'offers',
    onChangeSelectedIds: (ids) => {
      answers.selected_offer_ids = ids;
    }
  });
  
  // Proof
  const proofChips = mergeCustomChips(
    chipPresets.proof_chips || [],
    answers.custom_chips?.proof || []
  );
  window.__chipGroups.proof = new window.ChipGroup({
    containerId: 'chip-group-proof',
    title: 'Proof & Credibility',
    subtitle: 'What makes you trustworthy?',
    chips: proofChips,
    selectedIds: answers.selected_proof_ids || [],
    maxSelect: 2,
    allowWriteIn: true,
    groupKey: 'proof',
    onChangeSelectedIds: (ids) => {
      answers.selected_proof_ids = ids;
    }
  });
  
  // Show the chip selection section
  const chipSection = document.getElementById('chip-selection-section');
  if (chipSection) {
    chipSection.classList.remove('hidden');
  }
}

// handle extra keywords input (comma-separated or Enter)
document.addEventListener('DOMContentLoaded', () => {
  setPreviewCTAState(false);
  if (previewJumpBtn){
    previewJumpBtn.addEventListener('click', () => {
      const target = document.getElementById('results') || results;
      if (target){ target.scrollIntoView({ behavior: 'smooth', block: 'start' }); }
    });
  }
  const extra = document.getElementById('extra-keywords');
  if (extra){
    extra.addEventListener('keydown', (e) => {
      if (e.key === 'Enter'){
        e.preventDefault();
        const parts = extra.value.split(',').map(s=>s.trim()).filter(Boolean);
        answers.manual_keywords = (answers.manual_keywords || []).concat(parts);
        answers.brand_keywords = (answers.brand_keywords || []).concat(parts);
        extra.value = '';
        updateSummary();
      }
    });
    extra.addEventListener('blur', () => {
      const parts = extra.value.split(',').map(s=>s.trim()).filter(Boolean);
      if (parts.length){
        answers.manual_keywords = (answers.manual_keywords || []).concat(parts);
        answers.brand_keywords = (answers.brand_keywords || []).concat(parts);
        extra.value = '';
        updateSummary();
      }
    });
  }

  // Clear keywords button
  const clearBtn = document.getElementById('clear-keywords');
  if (clearBtn){
    clearBtn.addEventListener('click', (e) => {
      e.preventDefault();
      clearKeywords();
    });
  }
});

function renderToneChoices(list){
  const wrap = document.getElementById("tones");
  if (!wrap) return;
  wrap.innerHTML = "";
  list.forEach(opt => {
    const div = document.createElement("button");
    div.className = "choice"; div.setAttribute("data-key", opt.key);
    div.innerHTML = `<div class="title">${opt.label}</div>`;
    div.addEventListener("click", () => {
      wrap.querySelectorAll(".choice").forEach(c=>c.classList.remove("selected"));
      div.classList.add("selected");
      answers.tone = opt.key;
      updateSummary();
    });
    wrap.appendChild(div);
  });
}

function renderPlatformChoices(list){
  const wrap = document.getElementById("platforms");
  if (!wrap) return;
  wrap.innerHTML = "";
  list.forEach(opt => {
    const div = document.createElement("button");
    div.className = "choice"; div.setAttribute("data-key", opt.key);
    div.innerHTML = `<div class="title">${opt.label}</div>`;
    div.addEventListener("click", () => {
      const k = opt.key;
      const idx = answers.platforms.indexOf(k);
      if (idx === -1) { answers.platforms.push(k); div.classList.add("selected"); }
      else { answers.platforms.splice(idx,1); div.classList.remove("selected"); }
      if (answers.platforms.length === 0) answers.platforms = ["instagram"];
      updateSummary();
    });
    if (answers.platforms.includes(opt.key)) div.classList.add("selected");
    wrap.appendChild(div);
  });
}

// Initialize Stripe Elements if publishable key is available. Safe to call multiple times.
async function ensureStripeElementsInitialized(){
  try{
    if (window.STRIPE && window.__card) return true;
    const r = await fetch('/api/stripe-publishable-key');
    if (!r.ok) return false;
    const j = await r.json().catch(()=>null);
    if (!j || !j.ok || !j.publishableKey) return false;
    const pk = j.publishableKey;
    if (!window.STRIPE){
      const script = document.createElement('script');
      script.src = 'https://js.stripe.com/v3/';
      document.head.appendChild(script);
      await new Promise(res => { script.onload = res; script.onerror = () => res(); });
      window.STRIPE = Stripe(pk);
    }
    const elements = window.STRIPE.elements();
    if (!window.__card){
      window.__card = elements.create('card');
      const wrap = document.getElementById('stripe-elements-wrap');
      if (wrap) wrap.classList.remove('hidden');
      window.__card.mount('#card-element');
      window.__card.on('change', (ev) => {
        const ce = document.getElementById('card-errors');
        if (!ev.complete && ev.error){ ce.textContent = ev.error.message; ce.classList.remove('hidden'); }
        else { if (ce){ ce.textContent = ''; ce.classList.add('hidden'); } }
      });
    }
    return true;
  }catch(e){ console.error('ensureStripeElementsInitialized failed', e); return false; }
}

function renderIndustryQuestions(key){
  const wrap = document.getElementById("industry-questions");
  if (!wrap) return;
  wrap.innerHTML = "";
  // preserve existing answers.goals and answers.details when switching industries
  const map = (CFG && CFG.questions) || {};
  (map[key] || []).forEach(q => {
    if (q.type === "chips"){
      const box = document.createElement("div");
      box.innerHTML = `<div class="text-sm font-medium mb-1">${q.label}</div>`;
      const grid = document.createElement("div");
      grid.className = "grid grid-cols-2 md:grid-cols-3 gap-2";
      q.options.forEach(opt => {
        const chip = document.createElement("button");
        chip.className = "choice"; chip.textContent = opt;
        // initialize selected state
        try{
          if (q.key === 'goals'){
            if ((answers.goals || []).indexOf(opt) !== -1) chip.classList.add('selected');
          } else {
            if ((answers.details && answers.details[q.key]) === opt) chip.classList.add('selected');
          }
        }catch(e){}
        chip.addEventListener("click", () => {
          // if this is the 'goals' question, allow multi-select
          if (q.key === 'goals'){
            answers.goals = answers.goals || [];
            const idx = answers.goals.indexOf(opt);
            if (idx === -1){ answers.goals.push(opt); chip.classList.add("selected"); }
            else { answers.goals.splice(idx,1); chip.classList.remove("selected"); }
          } else {
            // single-select behavior stored under answers.details[q.key]
            answers.details = answers.details || {};
            if (answers.details[q.key] === opt){
              // toggle off
              delete answers.details[q.key];
              chip.classList.remove('selected');
            } else {
              // deselect other chips in this grid
              Array.from(grid.children).forEach(c => c.classList.remove('selected'));
              answers.details[q.key] = opt;
              chip.classList.add('selected');
            }
          }
          updateSummary();
        });
        grid.appendChild(chip);
      });
      box.appendChild(grid);
      wrap.appendChild(box);
    }
    if (q.type === "text"){
      const box = document.createElement("div");
      box.innerHTML = `<label class="block text-sm font-medium mb-1">${q.label}</label>\n      <input class="input" placeholder="${q.placeholder||""}" />`;
      const input = box.querySelector("input");
      // prefill if previously saved
      try{ if (answers.details && answers.details[q.key]) input.value = answers.details[q.key]; }catch(e){}
      input.addEventListener("input", () => { answers.details = answers.details || {}; answers.details[q.key] = input.value.trim(); updateSummary(); });
      wrap.appendChild(box);
    }
  });
  skipStep2 = wrap.children.length === 0;
  updateStepTwoState();
}

function showStep(n){
  // If context step (3) should be skipped and we're navigating to it, skip to step 4
  if (skipStep2 && n === 3){
    n = 4;
  }
  step = n;
  if (nextBtn) setButtonLoading(nextBtn, false);
  const panels = document.querySelectorAll('.step-panel');
  if (panels && panels.length){
    panels.forEach(s=>s.classList.add('hidden'));
    const active = document.querySelector(`.step-panel[data-step="${n}"]`);
    if (active) active.classList.remove('hidden');
  }
  
  // Use dynamic step calculations
  const totalSteps = getTotalSteps();
  const currentIndex = getCurrentStepIndex();
  const currentDisplay = currentIndex + 1;
  
  if (prevBtn) prevBtn.disabled = step === 1;
  if (nextBtn) nextBtn.textContent = currentDisplay >= totalSteps ? 'Finish' : 'Next';
  
  // Update step indicators
  updateStepIndicators();

  const progressBar = document.getElementById('progress-bar');
  const progressText = document.getElementById('progress-text');
  const stepTitle = document.getElementById('step-title');
  if (progressBar && progressText) {
    const progressPercent = (currentDisplay / totalSteps) * 100;
    progressBar.style.width = progressPercent + '%';
    progressText.textContent = `Step ${currentDisplay} of ${totalSteps}`;
    
    // Update step title
    if (stepTitle) {
      const steps = getWizardSteps();
      const currentStepData = steps.find(s => parseInt(s.dataStep) === n);
      if (currentStepData) {
        stepTitle.textContent = currentStepData.title;
      }
    }
  }

  // Persist current step to localStorage
  try {
    localStorage.setItem('wizard_current_step', step.toString());
    localStorage.setItem('wizard_step_timestamp', Date.now().toString());
  } catch (e) {
    // Ignore localStorage errors
  }

  // Hydrate Brand Kit UI when showing step 2
  if (n === 2) {
    hydrateBrandKitUI();
  }

  // Hydrate brand inspiration UI when showing step 5
  if (n === 5) {
    hydrateBrandInspirationUI();
  }

  if (currentDisplay !== totalSteps){
    clearFinishStatus();
  }
}

// Restore wizard progress from localStorage (with TTL)
function restoreWizardProgress() {
  try {
    const savedStep = localStorage.getItem('wizard_current_step');
    const timestamp = localStorage.getItem('wizard_step_timestamp');
    
    if (savedStep && timestamp) {
      const age = Date.now() - parseInt(timestamp);
      const TTL = 24 * 60 * 60 * 1000; // 24 hours
      
      // Only restore if within TTL and not explicitly navigating via hash
      if (age < TTL && !window.location.hash) {
        const restoredStep = parseInt(savedStep);
        if (restoredStep > 1 && restoredStep <= 5) {
          step = restoredStep;
          // Don't call showStep yet - will be called after boot
          console.log('Restored wizard progress to step', step);
        }
      } else if (age >= TTL) {
        // Clear stale data
        localStorage.removeItem('wizard_current_step');
        localStorage.removeItem('wizard_step_timestamp');
      }
    }
  } catch (e) {
    // Ignore localStorage errors
  }
}

// Restore progress on load (before hash navigation)
restoreWizardProgress();

// Add exit confirmation for mid-wizard navigation
let wizardCompleted = false;
window.addEventListener('beforeunload', (e) => {
  // Only show confirmation if user is in the wizard (step 1-4) and hasn't completed
  if (step >= 1 && step < 5 && !wizardCompleted) {
    // Check if user has made any progress (selected industry or beyond)
    if (answers.industry) {
      e.preventDefault();
      e.returnValue = 'You can finish later—progress saved.';
      return e.returnValue;
    }
  }
});

// Mark wizard as completed when user finishes
function markWizardCompleted() {
  wizardCompleted = true;
}

// Check for hash navigation
if (window.location.hash === '#step4') {
    setTimeout(() => {
        step = 4;
        showStep(4);
        document.getElementById('wiz')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 200);
}

if (prevBtn) prevBtn.addEventListener("click", ()=>{
  if (step === 4 && skipStep2){
    step = 2; // Skip back over context step (3) to Brand Kit
  } else {
    step = Math.max(1, step-1);
  }
  showStep(step);
});
if (nextBtn) nextBtn.addEventListener("click", async ()=>{
  // Check if we're on the last step
  const totalSteps = getTotalSteps();
  const currentIndex = getCurrentStepIndex();
  const currentDisplay = currentIndex + 1;
  const isLastStep = currentDisplay >= totalSteps;
  
  if (step === 1){
    if (!answers.industry){ showToast('Pick an industry to keep going'); return; }
    // Show saving feedback briefly
    showSavingFeedback();
    step = 2; // Always go to Brand Kit step
    showStep(step);
    return;
  }
  if (step === 2){
    // Brand Kit step - collect data and save
    collectBrandKitData();
    await saveBrandKit();
    // Show saving feedback briefly
    showSavingFeedback();
    step = skipStep2 ? 4 : 3; // Skip context if empty
    showStep(step);
    return;
  }
  if (step === 3){
    if (!skipStep2 && !hasStepTwoAnswer()){
      showToast('Choose at least one focus so we can tailor ideas');
      return;
    }
    // Show saving feedback briefly
    showSavingFeedback();
    step = 4;
    showStep(step);
    return;
  }
  if (step === 4){
    if (!answers.tone){ showToast('Pick a tone to keep going'); return; }
    if (!answers.platforms || !answers.platforms.length){ showToast('Choose at least one platform'); return; }
    // Show saving feedback briefly
    showSavingFeedback();
    step = 5;
    showStep(step);
    return;
  }
  if (step === 5){
    // Brand inspiration step - collect data and move to step 6
    collectBrandInspirationData();
    // Show saving feedback briefly
    showSavingFeedback();
    step = 6;
    showStep(step);
    return;
  }
  if (isLastStep){
    // This is the final step - save profile and finish
    // collect keywords from selected chips and extra input
    const extra = document.getElementById('extra-keywords');
    if (extra && extra.value.trim()){
      const parts = extra.value.split(',').map(s=>s.trim()).filter(Boolean);
      answers.manual_keywords = (answers.manual_keywords || []).concat(parts);
      answers.brand_keywords = (answers.brand_keywords || []).concat(parts);
      extra.value = '';
    }
    // ensure niche_keywords mirrors brand_keywords for now
    answers.niche_keywords = answers.brand_keywords || [];
    answers.include_images = document.getElementById("include_images").checked;
    clearFieldError('company');
    clearFormError();
    if (nextBtn){
      nextBtn.dataset.loadingText = 'Saving…';
      setButtonLoading(nextBtn, true);
    }
    updateFinishStatus('info', 'Saving your brand voice…', 'Hang tight while we prepare your dashboard.');
    try{
      await saveProfile();
      updateFinishStatus('info', 'Generating your first post…', "We're creating a sample so your dashboard feels ready.");
      await seedInitialPosts();
      markWizardCompleted(); // Mark wizard as completed to prevent exit confirmation
      updateFinishStatus('success', 'Brand voice saved', 'Redirecting in 3 seconds…');
      startFinishCountdown(3, () => { window.location.href = '/generate'; });
    }catch(err){
      console.error('saveProfile failed', err);
      const msg = (err && err.message) ? err.message : 'Save failed — please try again.';
      showFormError(msg);
      updateFinishStatus('error', 'Could not save profile', msg);
      setButtonLoading(nextBtn, false);
    }
    return;
  }
});

function collectBrandInspirationData() {
  // Collect brand inspirations
  const brandInputs = document.querySelectorAll('#wizard-brand-inspirations .brand-name');
  const brandWhyInputs = document.querySelectorAll('#wizard-brand-inspirations .brand-why');
  answers.brand_inspirations = Array.from(brandInputs).map((input, i) => ({
    name: input.value.trim(),
    why: brandWhyInputs[i]?.value.trim() || ''
  })).filter(b => b.name);
  
  // Collect anti-inspirations
  const antiInputs = document.querySelectorAll('#wizard-brand-anti-inspirations .anti-brand-name');
  const antiWhyInputs = document.querySelectorAll('#wizard-brand-anti-inspirations .anti-brand-why');
  answers.brand_anti_inspirations = Array.from(antiInputs).map((input, i) => ({
    name: input.value.trim(),
    why: antiWhyInputs[i]?.value.trim() || ''
  })).filter(b => b.name);
  
  // Get selected vibe preset
  const selectedVibe = document.querySelector('.wizard-vibe-preset-btn.border-indigo-500');
  answers.vibe_preset = selectedVibe ? selectedVibe.dataset.vibe : null;
}

async function saveProfile(){
  const version = (CFG && CFG.version) ? CFG.version : "local";
  // ensure the latest company value is captured
  const companyInput = document.getElementById('company');
  if (companyInput) answers.company = companyInput.value.trim();
  // validate company before saving
  const err = validateCompany(answers.company);
  clearFieldError('company');
  if (err){
    showFieldError('company', err);
    throw new Error(err);
  }

  let resp;
  try{
    resp = await fetch("/api/profile?content_version=" + encodeURIComponent(version), {
      method: "POST",
      credentials: 'include',
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(answers)
    });
  }catch(networkErr){
    const msg = 'Network error: unable to save your profile right now. Please check your connection and try again.';
    showFormError(msg);
    throw new Error(msg);
  }
  let body = null;
  try{ body = await resp.json(); }catch(e){ body = null; }
  if (resp.status === 401){
    const msg = 'Please sign in to save your profile.';
    showFormError(msg);
    if (typeof openAuthModal === 'function') openAuthModal('login');
    throw new Error(msg);
  }
  if (resp.status === 403){
    const msg = (body && body.error) ? body.error : 'You do not have permission to save this profile.';
    showFormError(msg);
    throw new Error(msg);
  }
  if (!resp.ok){
    if (body && body.errors){
      Object.keys(body.errors).forEach(f => showFieldError(f, body.errors[f]));
      const formMsg = body.error || 'Please correct the highlighted fields.';
      showFormError(formMsg);
      throw new Error(formMsg);
    }
    const msg = (body && body.error) ? body.error : `Save failed (HTTP ${resp.status})`;
    showFormError(msg);
    throw new Error(msg);
  }
  if (btn30) btn30.disabled = false;
  updateSummary();
  clearFormError();
  return body;
}

// wire company input to answers
document.addEventListener('DOMContentLoaded', () => {
  const c = document.getElementById('company');
  if (c){
    c.addEventListener('input', (e) => {
      answers.company = e.target.value.trim();
      // show immediate inline validation feedback
      clearFieldError('company');
      const msg = validateCompany(answers.company);
      if (msg){
        showFieldError('company', msg);
        // also visually disable Next/Finish button
        if (nextBtn) nextBtn.disabled = true;
      } else {
        if (nextBtn) nextBtn.disabled = false;
      }
      updateSummary();
    });
  }
});

// helper functions for field and form errors
function showFieldError(field, message){
  const id = `error-${field}`;
  const el = document.getElementById(id);
  if (el){ el.textContent = message || ''; el.classList.remove('hidden'); }
  else {
    // fallback: create a small inline element after the field
    const f = document.getElementById(field);
    if (f && f.parentElement){
      const div = document.createElement('div'); div.id = id; div.className = 'text-xs text-red-600 mt-1'; div.textContent = message || '';
      f.parentElement.appendChild(div);
    }
  }
}
function clearFieldError(field){
  const id = `error-${field}`;
  const el = document.getElementById(id);
  if (el){ el.textContent = ''; el.classList.add('hidden'); }
}
function showFormError(message){
  const el = document.getElementById('error-form');
  if (el){ el.textContent = message || ''; el.classList.remove('hidden'); }
}
function clearFormError(){
  const el = document.getElementById('error-form');
  if (el){ el.textContent = ''; el.classList.add('hidden'); }
}

function setPreviewCTAState(hasPosts){
  if (previewHint){
    previewHint.textContent = hasPosts
      ? 'Sample loaded — open the Generate dashboard once you like what you see.'
      : 'We’ll drop a sample plan below once you save. Give it a quick look before heading to your dashboard.';
  }
  if (previewGenerateLink){
    previewGenerateLink.classList.toggle('hidden', !hasPosts);
    previewGenerateLink.setAttribute('aria-disabled', hasPosts ? 'false' : 'true');
  }
  if (previewJumpBtn){
    previewJumpBtn.textContent = hasPosts ? 'Jump to preview again' : 'Jump to preview';
  }
}

function updateFinishStatus(state, title, detail){
  if (!finishStatus) return;
  if (state) finishStatus.dataset.state = state;
  finishStatus.classList.remove('hidden');
  if (finishStatusIcon){
    finishStatusIcon.textContent = state === 'success' ? '✅' : (state === 'error' ? '⚠️' : '⏳');
  }
  if (finishStatusTitle) finishStatusTitle.textContent = title || '';
  if (finishStatusDetail && typeof detail === 'string') finishStatusDetail.textContent = detail;
}

function clearFinishStatus(){
  if (!finishStatus) return;
  finishStatus.classList.add('hidden');
  finishStatus.removeAttribute('data-state');
  if (finishStatusIcon) finishStatusIcon.textContent = '⏳';
  if (finishStatusTitle) finishStatusTitle.textContent = '';
  if (finishStatusDetail) finishStatusDetail.textContent = '';
  if (finishCountdownInterval){ clearInterval(finishCountdownInterval); finishCountdownInterval = null; }
}

function startFinishCountdown(seconds, done){
  if (finishCountdownInterval){ clearInterval(finishCountdownInterval); finishCountdownInterval = null; }
  if (!finishStatusDetail){
    if (typeof done === 'function') setTimeout(done, seconds * 1000);
    return;
  }
  let remaining = seconds;
  finishStatusDetail.textContent = `Redirecting in ${remaining} seconds…`;
  finishCountdownInterval = setInterval(() => {
    remaining -= 1;
    if (remaining <= 0){
      clearInterval(finishCountdownInterval);
      finishCountdownInterval = null;
      finishStatusDetail.textContent = 'Redirecting now…';
      if (typeof done === 'function') done();
    } else {
      finishStatusDetail.textContent = `Redirecting in ${remaining} seconds…`;
    }
  }, 1000);
}

function updateStepTwoState(){
  const panel = document.querySelector('[data-step="2"]');
  const empty = document.getElementById('step-2-empty');
  if (!panel || !empty) return;
  panel.classList.toggle('step-panel--empty', skipStep2);
  if (skipStep2){
    empty.classList.remove('hidden');
  } else {
    empty.classList.add('hidden');
  }
  // Update stepper indicators after step count may have changed
  updateStepIndicators();
}

function updateStepIndicators() {
  // Update both desktop and mobile step indicators
  const desktopSteps = document.getElementById('steps');
  const mobileSteps = document.getElementById('steps-mobile');
  const totalSteps = getTotalSteps();
  const currentIndex = getCurrentStepIndex();
  const currentDisplay = currentIndex + 1;
  
  [desktopSteps, mobileSteps].forEach(container => {
    if (!container) return;
    const dots = container.querySelectorAll('.step');
    dots.forEach((dot, i) => {
      if (i < totalSteps) {
        dot.style.display = '';
        dot.classList.toggle('active', (i + 1) <= currentDisplay);
      } else {
        dot.style.display = 'none';
      }
    });
  });
}

function hasStepTwoAnswer(){
  const goalsReady = Array.isArray(answers.goals) && answers.goals.length > 0;
  const detailReady = answers.details && Object.keys(answers.details).some(key => key !== '_content_version' && answers.details[key]);
  return goalsReady || detailReady;
}

async function handleQuickStart(btn){
  try{
    if (!ensureQuickStartAuth()) return;
    setButtonLoading(btn, true);
    await bootPromise;
    if (!selectIndustryChoice('other')){
      const fallback = document.querySelector('#industries .choice');
      fallback?.click();
    }
    await new Promise(res => setTimeout(res, 50));
    const firstDetailInput = document.querySelector('#industry-questions input');
    if (firstDetailInput && !firstDetailInput.value){
      firstDetailInput.value = 'Quick overview of our work';
      firstDetailInput.dispatchEvent(new Event('input', { bubbles: true }));
    }
    const firstQuestionChip = document.querySelector('#industry-questions .choice');
    if (firstQuestionChip && !firstQuestionChip.classList.contains('selected')){
      firstQuestionChip.click();
    }
    ensureToneChoice('friendly');
    ensurePlatformChoice('instagram');
    ensurePlatformChoice('facebook');
    answers.brand_keywords = ['behind the scenes', 'community updates', 'customer stories'];
    answers.niche_keywords = answers.brand_keywords.slice();
    answers.goals = answers.goals && answers.goals.length ? answers.goals : ['Community'];
    if (!answers.company){
      answers.company = 'My Business';
      const companyInput = document.getElementById('company');
      if (companyInput && !companyInput.value){
        companyInput.value = answers.company;
      }
    }
    updateSummary();
    step = 4;
    showStep(4);
    updateFinishStatus('info', 'Saving your preferences…', 'We’re also preloading a fresh sample for your dashboard.');
    await saveProfile();
    await seedInitialPosts();
    showToast('Setup complete — redirecting to Generate');
    window.location.href = '/generate';
  }catch(err){
    console.error('handleQuickStart failed', err);
    showToast('Quick start unavailable — please finish the steps manually.');
  }finally{
    setButtonLoading(btn, false);
  }
}

function selectIndustryChoice(key){
  const target = document.querySelector(`#industries .choice[data-key="${key}"]`);
  if (!target) return false;
  target.click();
  return true;
}

function ensureToneChoice(key){
  const btn = document.querySelector(`#tones .choice[data-key="${key}"]`);
  if (btn && !btn.classList.contains('selected')){
    btn.click();
  }
}

function ensurePlatformChoice(key){
  const btn = document.querySelector(`#platforms .choice[data-key="${key}"]`);
  if (!btn) return;
  if (!answers.platforms.includes(key)){
    btn.click();
  }
}

if (btnSample) btnSample.addEventListener("click", () => {
  handlePlanGeneration(1, { planLabel: '1-day sample', button: btnSample });
});
if (btn30) btn30.addEventListener("click", () => {
  handlePlanGeneration(30, { requiresPaid: true, planLabel: '30-day plan', button: btn30 });
});

async function maybeSaveDefaults(){
  if (!answers.industry) answers.industry = "Business";
  if (!answers.tone) answers.tone = "friendly";
  if (!answers.platforms || answers.platforms.length === 0) answers.platforms = ["instagram"];
  await saveProfile();
}

function ensurePlanAccess({ requiresPaid = false, planLabel = 'this plan' } = {}){
  if (!isLoggedIn()){
    showToast(`Sign in to unlock the ${planLabel}.`);
    openAuthModal('signup', { prefillEmail: getKnownEmailValue() });
    return false;
  }
  if (requiresPaid && (!window.CURRENT_USER || !window.CURRENT_USER.is_paid)){
    showPaywall(`Subscribe to unlock the ${planLabel}.`, { prefillEmail: getKnownEmailValue() });
    return false;
  }
  return true;
}

async function handlePlanGeneration(days, { requiresPaid = false, planLabel = `${days}-day plan`, button = null, generateOptions = {} } = {}){
  if (!ensurePlanAccess({ requiresPaid, planLabel })) return;
  try{
    if (button) setButtonLoading(button, true);
    await maybeSaveDefaults();
    const data = await generate(days, generateOptions);
    renderPosts(data);
    await refreshCurrentUser();
  }catch(err){
    if (err && err.message) console.debug(err.message);
  }finally{
    if (button) setButtonLoading(button, false);
  }
}

async function generate(days){
  // allow an optional override for platforms or other opts by passing
  // generate(days, { platforms: ['short_video'] })
  const opts = arguments[1] || {};
  const payload = Object.assign({}, answers, { days }, opts);
  let res;
  try{
    res = await fetch("/api/generate", {
      method: "POST",
      credentials: 'include',
      headers: {"Content-Type":"application/json"},
      body: JSON.stringify(payload)
    });
  }catch(e){
    // network-level error (server down, CORS, connection refused)
    const msg = 'Network error: could not reach the server. Ensure the dev server is running and your browser can reach http://localhost:'+ (window.location.port || '5001') +'.';
    showFormError(msg);
    console.error('generate() network error', e);
    throw new Error(msg);
  }

  // handle auth/paywall responses gracefully in the UI
  if (res.status === 401){
    // not authenticated -> open auth modal
    openAuthModal('login');
    throw new Error('Authentication required');
  }
  if (res.status === 403){
    let msg = 'Paid subscription required';
    try{
      const payload = await res.json().catch(()=>null);
      if (payload && payload.error) msg = payload.error;
    }catch(e){}
    showPaywall(msg);
    throw new Error(msg);
  }

  if (!res.ok){
    // try to parse JSON error body for a helpful message
    try{
      const body = await res.json().catch(()=>null);
      const msg = (body && body.error) ? body.error : `Server error: HTTP ${res.status}`;
      showFormError(msg);
      throw new Error(msg);
    }catch(e){
      const msg = `Server error: HTTP ${res.status}`;
      showFormError(msg);
      throw new Error(msg);
    }
  }

  let body;
  try{
    body = await res.json();
  }catch(e){
    const msg = 'Received invalid response from server.';
    showFormError(msg);
    console.error('generate() invalid json', e);
    throw new Error(msg);
  }

  if (body && body.ok === false){
    const msg = (body.error && body.error.message) || body.error || 'Unable to generate content.';
    showFormError(msg);
    throw new Error(msg);
  }

  // Store source information for banner display
  if (body) {
    body.__source = body.source || 'unknown';
    body.__mode = body.mode || 'unknown';
    body.__warnings = body.warnings || [];
  }

  return body;
}

function showFallbackBanner(warnings = []) {
  let banner = document.getElementById('fallback-banner');
  
  // Create banner if it doesn't exist
  if (!banner) {
    const resultsContainer = document.getElementById('content-results');
    if (!resultsContainer) return;
    
    banner = document.createElement('div');
    banner.id = 'fallback-banner';
    banner.className = 'bg-amber-50 border border-amber-200 rounded-lg p-4 mb-4';
    banner.innerHTML = `
      <div class="flex items-start gap-3">
        <div class="flex-shrink-0">
          <svg class="w-5 h-5 text-amber-600" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clip-rule="evenodd"></path>
          </svg>
        </div>
        <div class="flex-1">
          <h3 class="text-sm font-medium text-amber-800 mb-1">AI generation temporarily unavailable</h3>
          <p class="text-sm text-amber-700 mb-3">
            Showing template-based suggestions instead. These are general-purpose posts that may not match your specific brand voice.
          </p>
          <div class="flex gap-2 flex-wrap">
            <button id="retry-with-ai" class="btn-primary text-sm px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-md">
              Retry with AI
            </button>
            <button id="continue-with-suggestions" class="btn-ghost text-sm px-4 py-2 text-amber-800 hover:bg-amber-100 rounded-md">
              Continue with suggestions
            </button>
          </div>
        </div>
        <button id="dismiss-fallback-banner" class="flex-shrink-0 text-amber-600 hover:text-amber-800">
          <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
            <path fill-rule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clip-rule="evenodd"></path>
          </svg>
        </button>
      </div>
    `;
    
    // Insert before results
    resultsContainer.parentNode.insertBefore(banner, resultsContainer);
    
    // Add event listeners
    const retryBtn = banner.querySelector('#retry-with-ai');
    const continueBtn = banner.querySelector('#continue-with-suggestions');
    const dismissBtn = banner.querySelector('#dismiss-fallback-banner');
    
    if (retryBtn) {
      retryBtn.addEventListener('click', async () => {
        hideFallbackBanner();
        // Trigger regeneration
        const generateBtn = document.querySelector('[data-generate-1]') || document.querySelector('button[onclick*="generate"]');
        if (generateBtn) {
          generateBtn.click();
        } else {
          // Fallback: try to regenerate with last known parameters
          try {
            setButtonLoading(retryBtn, true);
            const data = await generate(7);
            renderPosts(data);
          } catch (err) {
            console.error('Retry failed:', err);
          } finally {
            setButtonLoading(retryBtn, false);
          }
        }
      });
    }
    
    if (continueBtn) {
      continueBtn.addEventListener('click', () => {
        hideFallbackBanner();
      });
    }
    
    if (dismissBtn) {
      dismissBtn.addEventListener('click', () => {
        hideFallbackBanner();
      });
    }
  }
  
  banner.classList.remove('hidden');
}

function hideFallbackBanner() {
  const banner = document.getElementById('fallback-banner');
  if (banner) {
    banner.classList.add('hidden');
  }
}

async function seedInitialPosts(){
  if (typeof sessionStorage === 'undefined') return;
  try{
    const data = await generate(1);
    if (data && data.posts && data.posts.length){
      sessionStorage.setItem(SEED_STORAGE_KEY, JSON.stringify({ ts: Date.now(), payload: data }));
    }
  }catch(err){
    console.debug('seedInitialPosts skipped', err && err.message ? err.message : err);
  }
}

const PREVIEW_SAMPLE_PAYLOAD = {
  posts: [
    {
      day_index: 1,
      date: 'Mon',
      platform: 'instagram',
      pillar: 'Behind-the-scenes',
      image_prompt: 'Warm morning light over a local cafe counter filled with pastries and flowers',
      image_url: '',
      caption: 'Fresh croissants just left the oven and the whole shop smells like butter. Drop by on your morning walk and we’ll save you one ☕️🥐',
      hashtags: ['#localsmallbusiness','#morningritual'],
      reel: null
    },
    {
      day_index: 1,
      date: 'Mon',
      platform: 'short_video',
      pillar: 'Reel spotlight',
      image_prompt: 'Vertical shot of barista pouring latte art, handheld phone POV',
      image_url: '',
      caption: 'Your daily latte ritual in 12 seconds. Film the steam, the pour, and that final swirl.',
      reel: {
        hook: 'Walk with us behind the counter before doors open',
        script_beats: ['Unlock the cafe at sunrise','Grind beans + linger on the aroma','Pour the first latte with silky art'],
        shot_list: [
          { type: 'Wide entrance', description: 'Unlocking the door with sun flare' },
          { type: 'Close-up', description: 'Freshly ground espresso falling into the portafilter' },
          { type: 'POV', description: 'Milk swirl + slow reveal of the latte art' }
        ],
        on_screen_text: ['Doors open at 7', 'House-made syrups daily'],
        hashtags: ['#reelideas','#coffeeclub'],
        cta: 'DM us “latte” for the flavor of the week',
        thumbnail_prompt: 'Latte art heart on wooden counter with morning light',
        srt_prompt: 'Upbeat, percussive captions matching coffee prep beats'
      }
    },
    {
      day_index: 2,
      date: 'Tue',
      platform: 'facebook',
      pillar: 'Testimonial',
      image_prompt: 'Smiling customer picking up a pastry box at the counter, candid photo',
      image_url: '',
      caption: '“Their seasonal danishes taste like a buttery postcard from Europe.” — Maya, neighborhood regular. Leave a note below if we’ve made your morning!'
    }
  ]
};

function getSeedPreviewData(){
  if (typeof sessionStorage === 'undefined') return null;
  try{
    const raw = sessionStorage.getItem(SEED_STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw);
    const data = parsed?.payload || parsed?.data || parsed;
    if (data && Array.isArray(data.posts) && data.posts.length){
      return data;
    }
  }catch(err){ console.debug('preview seed unavailable', err); }
  return null;
}

function hydrateWizardPreview(){
  const target = results || document.getElementById('results');
  if (!target) return;
  const seeded = getSeedPreviewData();
  if (seeded){
    renderPosts(seeded);
    return;
  }
  if (PREVIEW_SAMPLE_PAYLOAD.posts && PREVIEW_SAMPLE_PAYLOAD.posts.length){
    renderPosts(PREVIEW_SAMPLE_PAYLOAD);
  }
}

function renderPosts(data){
  const posts = data.posts || [];
  const target = results || document.getElementById('content-results');
  if (!target) return;
  const isWizardPreview = target === results;
  target.innerHTML = "";
  
  // Check if this is fallback content and show banner
  const source = data.__source || data.source || 'unknown';
  const mode = data.__mode || data.mode || 'unknown';
  const warnings = data.__warnings || data.warnings || [];
  
  if (source === 'fallback' && mode === 'fallback_suggestions') {
    showFallbackBanner(warnings);
  } else {
    hideFallbackBanner();
  }
  
  if (!posts.length){
    target.innerHTML = `<div class="text-sm text-slate-600">No posts yet.</div>`;
    if (isWizardPreview) setPreviewCTAState(false);
    return;
  }
  const byDay = groupBy(posts, "day_index");
  for (const day of Object.keys(byDay).sort((a,b)=>+a-+b)){
    const items = byDay[day];
    const section = document.createElement("section");
    section.className = "post";
    section.innerHTML = `<div class="flex items-baseline justify-between mb-2">
      <h4 class="font-medium">Day ${day} • ${items[0].date}</h4>
      <span class="text-xs text-slate-500">${items.length} platform(s)</span>
    </div>`;
    items.forEach(p => section.appendChild(renderCard(p)));
    target.appendChild(section);
  }
  if (isWizardPreview) setPreviewCTAState(true);
}

function renderCard(post){
  const card = document.createElement("div");
  card.className = "card border rounded-lg p-3 mt-2";
  card.__feedbackSnapshot = buildFeedbackSnapshot(post);
  card.__feedbackSummary = buildFeedbackSummary(post);
  // normalize reel object to the legacy view shape so older UI keeps working
  function normalizeReel(r){
    if (!r) return null;
    const out = {};
    out.hook = r.hook || r.hooks || (Array.isArray(r.ranked_hooks) ? r.ranked_hooks[0] : '');
    out.script_beats = r.script_beats || r.scriptBeats || r.script || [];
    // normalize shot_list items to {type, description}
    out.shot_list = [];
    const rawShots = r.shot_list || r.shots || [];
    rawShots.forEach(s => {
      if (!s) return;
      if (typeof s === 'string'){
        out.shot_list.push({ type: s, description: '' });
      } else if (s.type && s.description){
        out.shot_list.push({ type: s.type, description: s.description });
      } else if (s.shot_type){
        out.shot_list.push({ type: s.shot_type, description: s.notes || '' });
      } else if (s.type){
        out.shot_list.push({ type: s.type, description: s.notes || '' });
      } else {
        // fallback stringify
        out.shot_list.push({ type: JSON.stringify(s), description: '' });
      }
    });
    out.on_screen_text = r.on_screen_text || r.onScreenText || r.onScreen || [];
    // hashtags: support both array and {primary, optional}
    if (Array.isArray(r.hashtags)) out.hashtags = r.hashtags;
    else if (r.hashtags && (r.hashtags.primary || r.hashtags.optional)) out.hashtags = [(r.hashtags.primary||[]).join(' '), (r.hashtags.optional||[]).join(' ')].filter(Boolean).join(' ').split(' ').filter(Boolean);
    else out.hashtags = [];
    out.cta = r.cta || '';
    out.thumbnail_prompt = r.thumbnail_prompt || r.thumbnail || r.thumbnailPrompt || '';
    out.srt_prompt = r.srt_prompt || r.srt || r.srtText || '';
    out.ranked_hooks = r.ranked_hooks || [];
    return out;
  }

  const r = normalizeReel(post.reel);

  card.innerHTML = `
    <div class="text-sm font-medium mb-1">${capitalize(post.platform)} • ${post.pillar}</div>
    ${post.image_url ? `<img class="w-full h-40 object-cover rounded mb-2" src="${post.image_url}" alt="Suggested image" />` : ""}
    <div class="text-xs text-slate-500 mb-2"><strong>Image prompt:</strong> ${escapeHtml(post.image_prompt)}</div>
    <pre class="caption text-sm">${escapeHtml(post.caption)}</pre>
    ${r ? `
      <div class="mt-3 p-3 bg-slate-50 rounded">
        <div class="text-sm font-medium mb-1">Reel plan</div>
        <div class="text-sm mb-2"><strong>Hook:</strong> ${escapeHtml(r.hook)}</div>
        <div class="text-sm mb-2"><strong>Script beats:</strong>
          <ol class="list-decimal ml-5 text-sm text-slate-700">${(r.script_beats||[]).map(b => `<li>${escapeHtml(b)}</li>`).join('')}</ol>
        </div>
        <div class="text-sm mb-2"><strong>Shot list:</strong>
          <ul class="list-disc ml-5 text-sm text-slate-700">${(r.shot_list||[]).map(s => `<li>${escapeHtml((s.type||'') + (s.description ? ': ' + s.description : ''))}</li>`).join('')}</ul>
        </div>
        <div class="text-sm mb-2"><strong>On-screen text:</strong> ${escapeHtml((r.on_screen_text||[]).join(' • '))}</div>
        <div class="text-sm mb-2"><strong>Hashtags:</strong> ${escapeHtml((r.hashtags||[]).join(' '))}</div>
        <div class="text-sm mb-2"><strong>CTA:</strong> ${escapeHtml(r.cta || '')}</div>
        <div class="flex gap-2 mt-2">
          <button class="btn-ghost text-xs" data-copy-reel-script aria-label="Copy reel script">Copy Reel Script</button>
          <button class="btn-ghost text-xs" data-copy-srt aria-label="Copy SRT prompt">Copy SRT Prompt</button>
          <button class="btn-ghost text-xs" data-copy-thumb aria-label="Copy thumbnail prompt">Copy Thumbnail Prompt</button>
        </div>
      </div>
    ` : ''}
    <div class="mt-3 flex items-center gap-2">
  <button class="btn-ghost text-xs" data-copy="${escapeAttr(post.caption)}" aria-label="Copy post caption">Copy</button>
  <button class="btn-ghost text-xs" data-like="1" data-day="${post.day_index}" data-platform="${post.platform}" aria-label="Like this post">👍</button>
  <button class="btn-ghost text-xs" data-like="-1" data-day="${post.day_index}" data-platform="${post.platform}" aria-label="Dislike this post">👎</button>
    </div>
  `;
  card.querySelector("[data-copy]")?.addEventListener("click", async (ev) => {
    const txt = ev.currentTarget.getAttribute("data-copy") || "";
    await navigator.clipboard.writeText(txt);
    ev.currentTarget.textContent = "Copied!";
    setTimeout(() => (ev.currentTarget.textContent = "Copy"), 1200);
  });
  // reel copy buttons
  if (post.reel){
    // use normalized reel if present
    const reelNode = (function(){
      // try to find the normalized block we rendered above
      const container = card.querySelector('.mt-3.p-3');
      return container ? (post.reel && (post.reel._normalized || null)) : null;
    })();
    // fallback to constructing values from post.reel
    const hook = (post.reel && (post.reel.hook || (post.reel.ranked_hooks && post.reel.ranked_hooks[0]) || ''));
    const scriptArr = (post.reel && (post.reel.script_beats || post.reel.scriptBeats || post.reel.script || []));
    const scriptText = `${hook}\n\n${(scriptArr||[]).join('\n')}`;
    const srtText = (post.reel && (post.reel.srt_prompt || post.reel.srt || ''));
    const thumbText = (post.reel && (post.reel.thumbnail_prompt || post.reel.thumbnail || ''));

    const btnScript = card.querySelector('[data-copy-reel-script]');
    const btnSrt = card.querySelector('[data-copy-srt]');
    const btnThumb = card.querySelector('[data-copy-thumb]');
    btnScript?.addEventListener('click', async (ev) => {
      try{ await navigator.clipboard.writeText(scriptText); ev.currentTarget.textContent = 'Copied!'; setTimeout(()=>ev.currentTarget.textContent='Copy Reel Script',1200);}catch(e){console.error(e)}
    });
    btnSrt?.addEventListener('click', async (ev) => {
      try{ await navigator.clipboard.writeText(srtText || ''); ev.currentTarget.textContent = 'Copied!'; setTimeout(()=>ev.currentTarget.textContent='Copy SRT Prompt',1200);}catch(e){console.error(e)}
    });
    btnThumb?.addEventListener('click', async (ev) => {
      try{ await navigator.clipboard.writeText(thumbText || ''); ev.currentTarget.textContent = 'Copied!'; setTimeout(()=>ev.currentTarget.textContent='Copy Thumbnail Prompt',1200);}catch(e){console.error(e)}
    });
  }
  card.querySelectorAll("[data-like]").forEach(btn => {
    btn.addEventListener("click", async () => {
      if (btn.disabled) return;
      const rating = +btn.getAttribute("data-like");
      const post_day = +btn.getAttribute("data-day") || 0;
      const platform = btn.getAttribute("data-platform") || '';
      let note = '';
      if (rating < 0 && typeof requestFeedbackNote === 'function'){
        note = await requestFeedbackNote({
          platform,
          post_day,
          source: 'wizard',
          captionPreview: card.__feedbackSummary || ''
        });
        if (note === null) return;
      }
      const ok = await submitFeedback({
        rating,
        postDay: post_day,
        platform,
        note,
        source: 'wizard',
        planLength: answers?.plan_length || answers?.planLength || null,
        postSnapshot: card.__feedbackSnapshot,
        summary: card.__feedbackSummary
      });
      if (ok){
        finalizeFeedbackButtons(card, platform, post_day, rating);
      }
    });
  });
  return card;
}

function updateSummary(){
  // Keep a small copy of the computed rows in memory; modal will render them when opened
  window.__setup_summary = [
    ["Industry", answers.industry || "—"],
    ["Tone", answers.tone || "—"],
    ["Platforms", answers.platforms.join(", ") || "—"],
    ["Goals", (answers.goals||[]).join(", ") || "—"],
    ["Company", answers.company || "—"]
  ];
  // If there's an inline summary card, render per-section progress
  try{ renderInlineSummary(); }catch(e){/* ignore */}
}

function renderInlineSummary(){
  const container = document.getElementById('modal-summary');
  if (!container) return;
  container.innerHTML = '';
  const sections = [
    { key: 'Industry', step: 1, value: answers.industry },
    { key: 'Details', step: 2, value: Object.keys(answers.details || {}).length || (answers.goals && answers.goals.length) },
    { key: 'Tone & Platforms', step: 3, value: answers.tone && answers.platforms && answers.platforms.length ? true : false },
    { key: 'Keywords & Note', step: 4, value: (answers.brand_keywords && answers.brand_keywords.length) || (answers.details && answers.details.note) || answers.company }
  ];
  sections.forEach(s => {
    const li = document.createElement('li');
    li.className = 'flex items-center justify-between';
    const left = document.createElement('div');
    left.className = 'flex items-center gap-3';
    const status = document.createElement('span');
    const done = !!s.value && s.value !== 0 && s.value !== '—';
    // nicer emoji status
    status.textContent = done ? '✅' : '◻️';
    status.className = done ? 'text-green-600' : 'text-slate-400';
    const label = document.createElement('button');
    label.className = 'text-left text-sm text-slate-700 hover:underline';
    label.textContent = s.key;
    label.addEventListener('click', () => { step = s.step; showStep(step); const wiz = document.getElementById('wiz'); if (wiz) wiz.scrollIntoView({ behavior: 'smooth', block: 'start' }); });
    left.appendChild(status);
    left.appendChild(label);
    const right = document.createElement('div');
    right.className = 'text-sm text-slate-500 text-right';
    // friendly summaries per section
    let summary = '';
    if (s.step === 1) summary = answers.industry || '—';
    else if (s.step === 2) summary = (answers.goals && answers.goals.length) ? answers.goals.join(', ') : '—';
    else if (s.step === 3) {
        let parts = [];
        if (answers.tone) parts.push(answers.tone);
        if (answers.platforms && answers.platforms.length) parts.push(answers.platforms.join(', '));
        if (answers.details && answers.details.creativity) parts.push(VOICE_CREATIVITY_LABELS[answers.details.creativity]);
        summary = parts.join(' • ') || '—';
    }
    else if (s.step === 4) summary = (answers.brand_keywords && answers.brand_keywords.length) ? answers.brand_keywords.slice(0,3).join(', ') : (answers.company || '—');
    right.textContent = summary;
    li.appendChild(left);
    li.appendChild(right);
    container.appendChild(li);
  });
}

async function submitFeedback(options = {}){
  try{
    const {
      rating,
      postDay,
      platform,
      note,
      source,
      planLength,
      postSnapshot,
      summary
    } = options;
    const payload = {
      rating,
      post_day: postDay,
      platform
    };
    const trimmedNote = typeof note === 'string' ? note.trim() : '';
    if (trimmedNote) payload.note = trimmedNote;
    if (source) payload.source = source;
    if (planLength) payload.plan_length = planLength;
    if (postSnapshot) payload.post_snapshot = postSnapshot;
    if (summary) payload.summary = summary;
    const res = await fetch('/api/feedback', {
      method: 'POST',
      credentials: 'include',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });
    if (!res.ok){
      showToast('Unable to save your feedback right now.');
      return false;
    }
    return true;
  }catch(err){
    console.error('submitFeedback failed', err);
    showToast('Unable to save your feedback right now.');
    return false;
  }
}
window.submitFeedback = submitFeedback;

function finalizeFeedbackButtons(container, platform, dayIndex, rating){
  if (!container) return;
  const label = rating > 0 ? '👍 Thanks' : '👎 Logged';
  const buttons = container.querySelectorAll(`[data-like][data-platform="${platform}"][data-day="${dayIndex}"]`);
  buttons.forEach(btn => {
    btn.disabled = true;
    btn.textContent = label;
  });
}

function requestFeedbackNote(meta = {}){
  return new Promise(resolve => {
    const overlay = document.createElement('div');
    overlay.className = 'fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-4';
    const reasons = ['Not relevant', 'Too generic', 'Off brand', 'Wrong platform', 'Needs more detail'];
    const previewBlock = meta.captionPreview
      ? `<div class="bg-slate-50 border border-slate-200 rounded-xl p-3 text-xs text-slate-600">${escapeHtml(meta.captionPreview)}</div>`
      : '';
    overlay.innerHTML = `
      <div class="bg-white rounded-2xl shadow-2xl max-w-md w-full p-6">
        <form class="space-y-4" id="feedback-note-form">
          <div>
            <p class="text-lg font-semibold text-slate-900 mb-1">Help us tune your results</p>
            <p class="text-sm text-slate-600">Tell us what missed for ${meta.platform || 'this post'} so we can make the next one better.</p>
          </div>
          ${previewBlock}
          <div class="flex flex-wrap gap-2">
            ${reasons.map(reason => `<button type="button" data-reason="${reason}" class="choice text-xs px-3 py-1">${reason}</button>`).join('')}
          </div>
          <div>
            <label class="text-xs uppercase tracking-wide text-slate-500">Quick note (optional)</label>
            <textarea id="feedback-note-input" class="w-full mt-1 input text-sm" rows="3" placeholder="e.g. This looks like it's for a restaurant, not a gym"></textarea>
          </div>
          <div class="flex justify-end gap-3">
            <button type="button" data-cancel class="btn-ghost">Skip</button>
            <button type="submit" class="btn-primary btn-sm">Send feedback</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(overlay);
    const textarea = overlay.querySelector('#feedback-note-input');
    const form = overlay.querySelector('#feedback-note-form');
    const cleanup = (value) => {
      overlay.remove();
      resolve(value);
    };
    overlay.querySelector('[data-cancel]')?.addEventListener('click', () => cleanup(''));
    overlay.addEventListener('keydown', (ev) => {
      if (ev.key === 'Escape'){
        ev.preventDefault();
        cleanup(null);
      }
    });
    overlay.addEventListener('click', (ev) => {
      if (ev.target === overlay){
        cleanup(null);
      }
    });
    overlay.querySelectorAll('[data-reason]').forEach(btn => {
      btn.addEventListener('click', () => {
        const reason = btn.getAttribute('data-reason') || '';
        textarea.value = reason;
        textarea.focus();
      });
    });
    form.addEventListener('submit', (ev) => {
      ev.preventDefault();
      const note = textarea.value.trim();
      if (!note){
        textarea.focus();
        return;
      }
      cleanup(note);
    });
    textarea.focus();
  });
}
window.requestFeedbackNote = requestFeedbackNote;

function buildFeedbackSnapshot(post = {}){
  const lines = [];
  lines.push(`Platform: ${formatPlatformLabel(post.platform || '')}`);
  if (post.pillar) lines.push(`Pillar: ${post.pillar}`);
  if (post.day_index || post.dayIndex) lines.push(`Day: ${post.day_index || post.dayIndex}`);
  if (post.image_prompt) lines.push(`Image prompt: ${post.image_prompt}`);
  lines.push('');
  lines.push('Caption:');
  lines.push(post.caption || '(empty)');
  if (post.reel){
    const reel = post.reel;
    lines.push('');
    if (reel.hook) lines.push(`Reel hook: ${reel.hook}`);
    const beats = reel.script_beats || reel.scriptBeats || reel.script || [];
    if (beats.length){
      lines.push('Reel beats:');
      beats.forEach((beat, idx) => lines.push(`${idx + 1}. ${beat}`));
    }
    if (reel.thumbnail_prompt) lines.push(`Thumbnail: ${reel.thumbnail_prompt}`);
    if (reel.srt_prompt) lines.push(`SRT prompt: ${reel.srt_prompt}`);
  }
  return lines.join('\n');
}

function buildFeedbackSummary(post = {}){
  const platformLabel = formatPlatformLabel(post.platform || '');
  const day = post.day_index || post.dayIndex;
  const pillar = post.pillar ? ` • ${post.pillar}` : '';
  const primaryLine = (post.caption || '').split('\n')[0].trim();
  const snippet = primaryLine.length > 60 ? `${primaryLine.slice(0, 57)}…` : primaryLine;
  const dayPart = day ? ` day ${day}` : '';
  return `${platformLabel}${dayPart}${pillar}`.trim() + (snippet ? ` • ${snippet}` : '');
}

function groupBy(arr, key){
  return arr.reduce((acc, x) => { (acc[x[key]] ||= []).push(x); return acc; }, {});
}
function capitalize(s){ return s ? s[0].toUpperCase() + s.slice(1) : s; }
function escapeHtml(s){ return (s||"").replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch])); }
function escapeAttr(s){ return (s||"").replace(/"/g, "&quot;"); }

// Summary wiring (inline or modal): attach handlers once DOM is ready
document.addEventListener('DOMContentLoaded', () => {
  const inline = document.getElementById('setup-summary-inline');
  const modal = document.getElementById('setup-modal') || document.getElementById('modal');
  const closeBtn = document.getElementById('modal-close');
  const xBtn = document.getElementById('modal-x');
  const gen1Btn = document.getElementById('modal-generate-1');
  const gen30Btn = document.getElementById('modal-generate-30');
  const gen7Btn = document.getElementById('modal-generate-7');
  const genReelsBtn = document.getElementById('modal-generate-reels');

  gen1Btn?.addEventListener('click', () => {
    handlePlanGeneration(1, { planLabel: '1-day sample', button: gen1Btn });
  });
  gen7Btn?.addEventListener('click', () => {
    handlePlanGeneration(7, { requiresPaid: true, planLabel: '7-day plan', button: gen7Btn });
  });
  gen30Btn?.addEventListener('click', () => {
    handlePlanGeneration(30, { requiresPaid: true, planLabel: '30-day plan', button: gen30Btn });
  });
  genReelsBtn?.addEventListener('click', () => {
    handlePlanGeneration(7, { requiresPaid: true, planLabel: 'Reels calendar', button: genReelsBtn, generateOptions: { platforms: ['short_video'] } });
  });

  // Close handlers: hide inline or modal depending on what exists
  closeBtn?.addEventListener('click', () => { if (inline) inline.classList.add('hidden'); if (modal) modal.classList.add('hidden'); });
  xBtn?.addEventListener('click', () => { if (inline) inline.classList.add('hidden'); if (modal) modal.classList.add('hidden'); });
  // paywall modal handlers
  const payModal = document.getElementById('paywall-modal');
  const payCancel = document.getElementById('paywall-cancel');
  const paySubscribe = document.getElementById('paywall-subscribe');
  document.querySelectorAll('[data-paywall-close]').forEach(btn => btn.addEventListener('click', closePaywall));
  payModal?.addEventListener('click', (event) => { if (event.target === payModal) closePaywall(); });
  payCancel?.addEventListener('click', closePaywall);
  paySubscribe?.addEventListener('click', async () => {
      // One-step signup + subscribe flow.
      // If user isn't signed in, create account first using the paywall inputs, then proceed to initialize Elements and create subscription.
  const wrap = document.getElementById('stripe-elements-wrap');
  const emailInput = document.getElementById('paywall-email');
  const passInput = document.getElementById('paywall-password');
  const signupError = document.getElementById('paywall-signup-error');
  const cardErrors = document.getElementById('card-errors');
  clearPaywallMessage();
  if (signupError){ signupError.classList.add('hidden'); signupError.textContent = ''; }
  if (cardErrors){ cardErrors.classList.add('hidden'); cardErrors.textContent = ''; }

      // helper to fallback to Checkout redirect
      const checkoutFallback = async () => {
        try{
          setButtonLoading(paySubscribe, true);
          const priceId = null;
          setPaywallMessage('Redirecting to secure checkout…', 'info');
          const r2 = await fetch('/api/create-checkout-session', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ price_id: priceId, success_url: window.location.href, cancel_url: window.location.href }) });
          const j = await r2.json().catch(()=>null);
          if (r2.ok && j && j.url){ window.location.href = j.url; return true; }
        }catch(e){ console.error('checkout redirect failed', e); }
        finally{ setButtonLoading(paySubscribe, false); }
        setPaywallMessage('Could not open secure checkout. Please try again.', 'error');
        return false;
      };

      try{
        // If user not signed in, attempt to sign them up first using supplied email/password.
        if (!window.CURRENT_USER || !window.CURRENT_USER.id){
          const email = emailInput ? emailInput.value.trim() : '';
          const pw = passInput ? passInput.value : '';
          if (!email || !pw){
            const msg = 'Please provide an email and password to create an account.';
            if (signupError){ signupError.textContent = msg; signupError.classList.remove('hidden'); }
            setPaywallMessage(msg, 'error');
            return;
          }
          setButtonLoading(paySubscribe, true);
          const r = await fetch('/api/signup', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ email, password: pw }) });
      const j = await r.json().catch(()=>null);
    if (!r.ok){
                const msg = (j && j.error) ? j.error : 'Sign up failed';
                // if server returned structured field errors, prioritize those
                if (j && j.errors){
                  const vals = Object.values(j.errors).filter(Boolean);
                  if (vals.length) signupError.textContent = vals.join(' — ');
                  else signupError.textContent = msg;
                } else {
                  if (signupError) signupError.textContent = msg;
                }
        if (signupError) signupError.classList.remove('hidden');
        setPaywallMessage(msg, 'error');
            setButtonLoading(paySubscribe, false);
            return;
          }
          // success — server should set session cookie; update client state
      setCurrentUser(userFromResponse(j)); showToast('Account created');
      setPaywallMessage('Account created. Add your card details to finish checkout.', 'success');
              // disable signup inputs to prevent duplicate submissions
              try{ if (emailInput) { emailInput.disabled = true; emailInput.classList.add('opacity-50'); } if (passInput) { passInput.disabled = true; passInput.classList.add('opacity-50'); } }catch(e){}
              setButtonLoading(paySubscribe, false);
        }

        // Initialize Elements (prefer embedded flow)
        const elementsReady = await ensureStripeElementsInitialized();
        if (!elementsReady){
          // fallback to Checkout redirect
          await checkoutFallback();
          return;
        }

        // create payment method with card element
        setButtonLoading(paySubscribe, true);
        setPaywallMessage('Securing your payment details…', 'info');
        const pmRes = await window.STRIPE.createPaymentMethod({ type: 'card', card: window.__card });
        if (pmRes.error){
          if (cardErrors){ cardErrors.textContent = pmRes.error.message; cardErrors.classList.remove('hidden'); }
          setPaywallMessage(pmRes.error.message || 'Payment details incomplete.', 'error');
          setButtonLoading(paySubscribe,false);
          return;
        }
        const payment_method = pmRes.paymentMethod.id;

        // create subscription server-side (server will use its configured STRIPE_TEST_PRICE_ID when price_id null)
  setPaywallMessage('Creating your subscription…', 'info');
  const r2 = await fetch('/api/create-subscription', { method: 'POST', credentials: 'include', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ price_id: null, payment_method }) });
        const j2 = await r2.json().catch(()=>null);
        if (!r2.ok || !j2 || !j2.ok){
          const msg = (j2 && j2.error) ? j2.error : 'Subscription creation failed';
          setPaywallMessage(msg, 'error');
          setButtonLoading(paySubscribe,false);
          return;
        }
        // if SCA required, confirm payment
        if (j2.client_secret){
          const ci = await window.STRIPE.confirmCardPayment(j2.client_secret, { payment_method: payment_method });
          if (ci.error){
            setPaywallMessage(ci.error.message || 'Payment confirmation failed', 'error');
            setButtonLoading(paySubscribe,false);
            return;
          }
        }

        // success
        await refreshCurrentUser();
        setPaywallMessage('Subscription active! Redirecting you…', 'success');
        showToast('Subscription active');
        closePaywall();
      }catch(e){ console.error(e); setPaywallMessage('Subscription failed — please try again.', 'error'); }
      finally{ setButtonLoading(paySubscribe, false); }
  });
  // Manage subscription: attach to header account link via context menu (right-click)
  const headerLink = document.querySelector('header .auth-link');
  headerLink?.addEventListener('contextmenu', async (e) => {
    e.preventDefault();
    // try to open portal
    try{
  const r = await fetch('/api/create-portal-session', { method: 'POST', credentials: 'include' });
      if (!r.ok){ const j = await r.json().catch(()=>null); alert((j && j.error) || 'Could not open billing portal'); return; }
      const j = await r.json(); if (j && j.url) window.location.href = j.url;
    }catch(err){ console.error(err); alert('Could not open billing portal'); }
  });
});

// Floating Action Button functionality - REMOVED: All generation now happens on /generate dashboard

// Review Insights functionality
function initReviewInsights() {
  const toggleBtn = document.getElementById('toggle-review-insights');
  const reviewSection = document.getElementById('review-insights-section');
  const reviewText = document.getElementById('review-text');
  const analyzeBtn = document.getElementById('analyze-review');
  const reviewLoading = document.getElementById('review-loading');
  const reviewInsights = document.getElementById('review-insights');
  const reviewKeywords = document.getElementById('review-keywords');
  const reviewSuggestions = document.getElementById('review-suggestions');
  const chevron = document.getElementById('review-chevron');

  // Toggle review insights section
  toggleBtn?.addEventListener('click', () => {
    const isHidden = reviewSection.classList.contains('hidden');
    reviewSection.classList.toggle('hidden');
    chevron.style.transform = isHidden ? 'rotate(180deg)' : 'rotate(0deg)';
  });

  // Analyze review text
  analyzeBtn?.addEventListener('click', async () => {
    const text = reviewText.value.trim();
    if (!text) {
      showToast('Please paste a customer review first');
      return;
    }

    // Show loading state
    analyzeBtn.disabled = true;
    reviewLoading.classList.remove('hidden');
    reviewInsights.classList.add('hidden');

    try {
      // Simple client-side analysis (could be enhanced with AI later)
      const insights = analyzeReviewText(text);

      // Display results
      reviewKeywords.innerHTML = '';
      insights.keywords.forEach(keyword => {
        const chip = document.createElement('button');
        chip.className = 'choice text-xs py-1 px-2 rounded-full bg-blue-100 text-blue-800 hover:bg-blue-200';
        chip.textContent = keyword;
        chip.addEventListener('click', () => {
          toggleKeyword(keyword);
          chip.classList.toggle('selected');
          chip.classList.toggle('bg-blue-100');
          chip.classList.toggle('bg-blue-200');
        });
        reviewKeywords.appendChild(chip);
      });

      reviewSuggestions.innerHTML = '';
      insights.suggestions.forEach(suggestion => {
        const div = document.createElement('div');
        div.className = 'flex items-start gap-2 mb-1';
        div.innerHTML = `
          <span class="text-green-600 mt-0.5">•</span>
          <span class="text-sm">${suggestion}</span>
        `;
        reviewSuggestions.appendChild(div);
      });

      reviewInsights.classList.remove('hidden');
      showToast('Review analyzed! Keywords and suggestions added.');

    } catch (error) {
      console.error('Review analysis failed:', error);
      showToast('Failed to analyze review. Please try again.');
    } finally {
      analyzeBtn.disabled = false;
      reviewLoading.classList.add('hidden');
    }
  });
}



async function hydrateWizardVoicePanel() {
  const status = document.getElementById('wizard-voice-status');
  const helper = document.getElementById('wizard-voice-helper');
  const toast = document.getElementById('wizard-voice-toast');
  if (toast) toast.textContent = '';
  try {
    const res = await fetch('/api/voice-profile', { credentials: 'include' });
    if (!res.ok) return;
    const data = await res.json();
    const vp = data.voice_profile || null;
    if (vp && typeof answers !== 'undefined') {
      answers.voice_profile = vp;
    }
    const sampleCount = Array.isArray(data.samples) ? data.samples.length : 0;
    if (status) {
      status.textContent = vp ? `Trained • ${sampleCount} samples` : 'Optional';
      status.className = vp
        ? 'px-2 py-1 rounded-full text-xs font-medium bg-emerald-50 text-emerald-700'
        : 'px-2 py-1 rounded-full text-xs font-medium bg-purple-50 text-purple-700';
    }
    if (helper && vp) {
      helper.textContent = 'We’ll keep tone, cadence, and vocab synced with these samples.';
    }
  } catch (err) {
    console.error('Wizard voice panel fetch failed', err);
  }
}

function parseWizardSamples(raw = '') {
  return (raw || '')
    .split('\n')
    .map(line => line.trim())
    .filter(Boolean);
}

// Wizard Voice Profile functionality
function initWizardVoiceProfile() {
  const btn = document.getElementById('wizard-train-voice');
  const input = document.getElementById('wizard-voice-samples');
  const toast = document.getElementById('wizard-voice-toast');
  if (!btn || !input) return;

  hydrateWizardVoicePanel();

  btn.addEventListener('click', async () => {
    const samples = parseWizardSamples(input.value || '');
    if (samples.length < 5 || samples.length > 10) {
      if (toast) toast.textContent = 'Add between 5 and 10 posts so we can map your voice.';
      return;
    }
    btn.disabled = true;
    btn.textContent = 'Saving…';
    try {
      const res = await fetch('/api/voice-profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ samples })
      });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        throw new Error(data.error || 'Unable to save samples');
      }
      if (toast) {
        toast.textContent = 'Voice saved. Future plans will use this cadence.';
        toast.className = 'text-sm text-green-600 mt-2 font-medium';
      }
      hydrateWizardVoicePanel();
    } catch (err) {
      console.error('Wizard voice training failed', err);
      if (toast) {
        toast.textContent = 'Could not save samples right now.';
        toast.className = 'text-sm text-red-600 mt-2 font-medium';
      }
    } finally {
      btn.disabled = false;
      btn.textContent = 'Save voice samples';
    }
  });
}

// Consolidated DOMContentLoaded handler
document.addEventListener('DOMContentLoaded', () => {
  initReviewInsights();
  initWizardVoiceProfile();
  initDashboardModes();
});

function initDashboardModes() {
  const modes = {
    social: { btn: 'mode-social', section: 'content-generator', hide: ['review-response'] },
    reviews: { btn: 'mode-reviews', section: 'review-response', hide: ['content-generator'] },
    reels: { btn: 'mode-reels', section: 'content-generator', hide: ['review-response'] }
  };

  const preferredMode = (document.body?.dataset?.generatorMode || 'social').toLowerCase();
  const buttons = Object.values(modes).map(m => document.getElementById(m.btn)).filter(Boolean);

  function applyMode(modeKey) {
    if (!modes[modeKey]) return;
    const mode = modes[modeKey];

    // Update buttons (if present on this page)
    buttons.forEach(b => {
      const isSelected = b.id === mode.btn;
      b.setAttribute('aria-selected', isSelected);
      if (isSelected) {
        b.classList.remove('text-slate-600', 'hover:text-slate-900', 'hover:bg-white/60');
        b.classList.add('text-slate-900', 'bg-white', 'shadow-sm', 'ring-1', 'ring-slate-200', 'font-semibold');
        b.classList.remove('font-medium');
      } else {
        b.classList.add('text-slate-600', 'hover:text-slate-900', 'hover:bg-white/60', 'font-medium');
        b.classList.remove('text-slate-900', 'bg-white', 'shadow-sm', 'ring-1', 'ring-slate-200', 'font-semibold');
      }
    });

    // Update sections
    const activeSection = document.getElementById(mode.section);
    if (activeSection) activeSection.classList.remove('hidden');

    mode.hide.forEach(id => {
      const el = document.getElementById(id);
      if (el) el.classList.add('hidden');
    });

    // Mode specific logic
    if (modeKey === 'reels') {
      // Force select short_video/tiktok/instagram
      const platformGroup = document.getElementById('generator-platforms');
      if (platformGroup) {
        const videoPlatforms = ['short_video', 'tiktok', 'instagram'];
        platformGroup.querySelectorAll('button').forEach(b => {
          const p = b.dataset.generatorPlatform;
          if (videoPlatforms.includes(p)) {
            if (b.getAttribute('aria-pressed') !== 'true') b.click();
          } else if (b.getAttribute('aria-pressed') === 'true') {
            b.click();
          }
        });
      }

      // Update generate button text
      const genBtn = document.getElementById('generate-content');
      if (genBtn) genBtn.textContent = 'Generate Reels Plan';
    } else if (modeKey === 'social') {
      // Update generate button text
      const genBtn = document.getElementById('generate-content');
      if (genBtn) genBtn.textContent = 'Generate Content';
    }
  }

  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const modeKey = Object.keys(modes).find(k => modes[k].btn === btn.id);
      if (!modeKey) return;
      applyMode(modeKey);
    });
  });

  if (modes[preferredMode]) {
    applyMode(preferredMode);
  }
}

// Brand inspiration constants
const MAX_BRANDS = 4;
const MAX_ANTI_BRANDS = 3;

// Initialize brand inspiration step
function initBrandInspiration() {
  const addBrandBtn = document.getElementById('wizard-add-brand-btn');
  const addAntiBrandBtn = document.getElementById('wizard-add-anti-brand-btn');
  
  if (!addBrandBtn || !addAntiBrandBtn) return; // Not on wizard page
  
  // Add initial brand input
  addWizardBrandInput();
  
  // Initialize anti-brand counter (even though there are 0 items)
  updateAntiBrandCounter();
  
  // Add brand button handler
  addBrandBtn.addEventListener('click', () => addWizardBrandInput());
  
  // Add anti-brand button handler
  addAntiBrandBtn.addEventListener('click', () => addWizardAntiBrandInput());
  
  // Vibe preset button handlers
  document.querySelectorAll('.wizard-vibe-preset-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const vibe = btn.dataset.vibe;
      // Toggle selection
      const isSelected = btn.classList.contains('border-indigo-500');
      
      // Clear all selections
      document.querySelectorAll('.wizard-vibe-preset-btn').forEach(b => {
        b.classList.remove('border-indigo-500', 'text-indigo-700', 'bg-indigo-50');
        b.classList.add('border-slate-200', 'text-slate-700');
      });
      
      // Toggle this one
      if (!isSelected) {
        btn.classList.add('border-indigo-500', 'text-indigo-700', 'bg-indigo-50');
        btn.classList.remove('border-slate-200', 'text-slate-700');
      }
    });
  });
}

function updateBrandCounter() {
  const container = document.getElementById('wizard-brand-inspirations');
  const addBtn = document.getElementById('wizard-add-brand-btn');
  if (!container || !addBtn) return;
  
  const count = container.children.length;
  
  // Update button text with counter
  const btnText = addBtn.querySelector('span');
  if (btnText) {
    btnText.textContent = `+ Add brand (${count}/${MAX_BRANDS})`;
  }
  
  // Disable button if at max
  if (count >= MAX_BRANDS) {
    addBtn.disabled = true;
    addBtn.classList.add('opacity-50', 'cursor-not-allowed');
  } else {
    addBtn.disabled = false;
    addBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

function updateAntiBrandCounter() {
  const container = document.getElementById('wizard-brand-anti-inspirations');
  const addBtn = document.getElementById('wizard-add-anti-brand-btn');
  if (!container || !addBtn) return;
  
  const count = container.children.length;
  
  // Update button text with counter
  const btnText = addBtn.querySelector('span');
  if (btnText) {
    btnText.textContent = `+ Add brand to avoid (${count}/${MAX_ANTI_BRANDS})`;
  }
  
  // Disable button if at max
  if (count >= MAX_ANTI_BRANDS) {
    addBtn.disabled = true;
    addBtn.classList.add('opacity-50', 'cursor-not-allowed');
  } else {
    addBtn.disabled = false;
    addBtn.classList.remove('opacity-50', 'cursor-not-allowed');
  }
}

function addWizardBrandInput(name = '', why = '') {
  const container = document.getElementById('wizard-brand-inspirations');
  if (!container) return;
  
  if (container.children.length >= MAX_BRANDS) return;
  
  const div = document.createElement('div');
  div.className = 'space-y-2';
  div.innerHTML = `
    <div class="flex gap-2">
      <input 
        type="text" 
        placeholder="Brand name (e.g., Apple)" 
        class="brand-name flex-1 rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 text-slate-700"
        value="${escapeHtml(name)}"
      />
      <button type="button" class="remove-brand-btn px-3 py-2 text-slate-400 hover:text-red-500 transition">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <input 
      type="text" 
      placeholder="Why? (e.g., clean and minimal)" 
      class="brand-why w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 text-slate-700 text-sm"
      value="${escapeHtml(why)}"
    />
  `;
  
  container.appendChild(div);
  
  // Add remove handler
  div.querySelector('.remove-brand-btn').addEventListener('click', () => {
    div.remove();
    updateBrandCounter();
  });
  
  updateBrandCounter();
}

function addWizardAntiBrandInput(name = '', why = '') {
  const container = document.getElementById('wizard-brand-anti-inspirations');
  if (!container) return;
  
  if (container.children.length >= MAX_ANTI_BRANDS) return;
  
  const div = document.createElement('div');
  div.className = 'space-y-2';
  div.innerHTML = `
    <div class="flex gap-2">
      <input 
        type="text" 
        placeholder="Brand name" 
        class="anti-brand-name flex-1 rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 text-slate-700"
        value="${escapeHtml(name)}"
      />
      <button type="button" class="remove-anti-brand-btn px-3 py-2 text-slate-400 hover:text-red-500 transition">
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
        </svg>
      </button>
    </div>
    <input 
      type="text" 
      placeholder="Why avoid?" 
      class="anti-brand-why w-full rounded-lg border-slate-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 p-3 text-slate-700 text-sm"
      value="${escapeHtml(why)}"
    />
  `;
  
  container.appendChild(div);
  
  // Add remove handler
  div.querySelector('.remove-anti-brand-btn').addEventListener('click', () => {
    div.remove();
    updateAntiBrandCounter();
  });
  
  updateAntiBrandCounter();
}

// Hydrate brand inspiration UI with saved data
function hydrateBrandInspirationUI() {
  const brandContainer = document.getElementById('wizard-brand-inspirations');
  const antiBrandContainer = document.getElementById('wizard-brand-anti-inspirations');
  
  if (!brandContainer || !antiBrandContainer) return;
  
  // Clear existing inputs
  brandContainer.innerHTML = '';
  antiBrandContainer.innerHTML = '';
  
  // Hydrate brand inspirations
  if (answers.brand_inspirations && answers.brand_inspirations.length > 0) {
    answers.brand_inspirations.forEach(brand => {
      addWizardBrandInput(brand.name || '', brand.why || '');
    });
  } else {
    // Add at least one empty input
    addWizardBrandInput();
  }
  
  // Hydrate anti-inspirations
  if (answers.brand_anti_inspirations && answers.brand_anti_inspirations.length > 0) {
    answers.brand_anti_inspirations.forEach(brand => {
      addWizardAntiBrandInput(brand.name || '', brand.why || '');
    });
  }
  
  // Hydrate vibe preset
  if (answers.vibe_preset) {
    // Use safer attribute selector to avoid CSS injection
    const vibeButtons = document.querySelectorAll('.wizard-vibe-preset-btn');
    vibeButtons.forEach(btn => {
      if (btn.dataset.vibe === answers.vibe_preset) {
        btn.classList.add('border-indigo-500', 'text-indigo-700', 'bg-indigo-50');
        btn.classList.remove('border-slate-200', 'text-slate-700');
      }
    });
  }
  
  // Update counters
  updateBrandCounter();
  updateAntiBrandCounter();
}

// ============================================================================
// Brand Kit Wizard Functions
// ============================================================================

function hydrateBrandKitUI() {
  // Load existing brand kit data from backend
  loadBrandKit();
  
  // Setup event listeners for Brand Kit UI
  setupBrandKitListeners();
}

async function loadBrandKit() {
  try {
    const response = await fetch('/api/brand_kit');
    const data = await response.json();
    
    if (data.ok && data.brand_kit) {
      const kit = data.brand_kit;
      
      // Hydrate business name
      const businessNameInput = document.getElementById('bk-business-name');
      if (businessNameInput && kit.business && kit.business.company_name) {
        businessNameInput.value = kit.business.company_name;
      }
      
      // Hydrate services
      if (kit.services && kit.services.primary_services) {
        answers.brand_kit.services = kit.services.primary_services;
        renderBrandKitChips('bk-services-chips', answers.brand_kit.services, 'services');
      }
      
      // Hydrate audience
      const audienceInput = document.getElementById('bk-audience');
      if (audienceInput && kit.audience && kit.audience.target_roles && kit.audience.target_roles.length > 0) {
        audienceInput.value = kit.audience.target_roles[0];
      }
      
      // Hydrate pain
      const painInput = document.getElementById('bk-pain');
      if (painInput && kit.audience && kit.audience.top_pains && kit.audience.top_pains.length > 0) {
        painInput.value = kit.audience.top_pains[0];
      }
      
      // Hydrate outcome
      const outcomeInput = document.getElementById('bk-outcome');
      if (outcomeInput && kit.audience && kit.audience.desired_outcomes && kit.audience.desired_outcomes.length > 0) {
        outcomeInput.value = kit.audience.desired_outcomes[0];
      }
      
      // Hydrate differentiators
      if (kit.positioning && kit.positioning.differentiators) {
        answers.brand_kit.differentiators = kit.positioning.differentiators;
        renderBrandKitChips('bk-differentiators-chips', answers.brand_kit.differentiators, 'differentiators');
      }
      
      // Hydrate proof
      const proofInput = document.getElementById('bk-proof');
      if (proofInput && kit.proof) {
        const proofParts = [];
        if (kit.proof.years_in_business) proofParts.push(`${kit.proof.years_in_business} years experience`);
        if (kit.proof.credentials && kit.proof.credentials.length > 0) proofParts.push(kit.proof.credentials.join(', '));
        if (proofParts.length > 0) {
          proofInput.value = proofParts.join(', ');
        }
      }
      
      // Hydrate email fields
      if (kit.email) {
        const emailNameInput = document.getElementById('bk-email-name');
        const emailTitleInput = document.getElementById('bk-email-title');
        const emailContactInput = document.getElementById('bk-email-contact');
        if (emailNameInput && kit.email.sender_name) emailNameInput.value = kit.email.sender_name;
        if (emailTitleInput && kit.email.signoff_style) emailTitleInput.value = kit.email.signoff_style;
        if (emailContactInput && kit.email.signature_lines) emailContactInput.value = kit.email.signature_lines;
      }
      
      // Hydrate quote fields
      if (kit.quotes) {
        const depositInput = document.getElementById('bk-deposit');
        const turnaroundInput = document.getElementById('bk-turnaround');
        const validityInput = document.getElementById('bk-validity');
        const paymentInput = document.getElementById('bk-payment-methods');
        if (depositInput && kit.quotes.deposit_policy) depositInput.value = kit.quotes.deposit_policy;
        if (turnaroundInput && kit.quotes.turnaround_time) turnaroundInput.value = kit.quotes.turnaround_time;
        if (validityInput && kit.quotes.default_validity_days) validityInput.value = `${kit.quotes.default_validity_days} days`;
        if (paymentInput && kit.quotes.payment_methods) paymentInput.value = kit.quotes.payment_methods;
      }
      
      // Update meter based on loaded data
      updateBrandKitMeter(kit.meta?.tier || 'minimum', kit.meta?.completeness_score || 0);
    }
  } catch (error) {
    console.error('Failed to load brand kit:', error);
  }
}

function setupBrandKitListeners() {
  // Services input - Enter key to add
  const servicesInput = document.getElementById('bk-services-input');
  if (servicesInput) {
    servicesInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const value = servicesInput.value.trim();
        if (value && answers.brand_kit.services.length < 5) {
          answers.brand_kit.services.push(value);
          renderBrandKitChips('bk-services-chips', answers.brand_kit.services, 'services');
          servicesInput.value = '';
          calculateBrandKitTier();
        }
      }
    });
  }
  
  // Differentiators input - Enter key to add
  const diffInput = document.getElementById('bk-differentiators-input');
  if (diffInput) {
    diffInput.addEventListener('keypress', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        const value = diffInput.value.trim();
        if (value && answers.brand_kit.differentiators.length < 3) {
          answers.brand_kit.differentiators.push(value);
          renderBrandKitChips('bk-differentiators-chips', answers.brand_kit.differentiators, 'differentiators');
          diffInput.value = '';
          calculateBrandKitTier();
        }
      }
    });
  }
  
  // Chip suggestion buttons
  const chipSuggestions = document.querySelectorAll('.chip-suggestion');
  chipSuggestions.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.target;
      const value = btn.dataset.value;
      const input = document.getElementById(targetId);
      if (input) {
        input.value = value;
        input.dispatchEvent(new Event('input'));
      }
    });
  });
  
  // Suggestion buttons that insert predefined values
  const suggestionButtons = document.querySelectorAll('[data-suggestion-target]');
  suggestionButtons.forEach(btn => {
    btn.addEventListener('click', () => {
      const targetId = btn.dataset.suggestionTarget;
      const suggestions = JSON.parse(btn.dataset.suggestions || '[]');
      const input = document.getElementById(targetId);
      if (input && suggestions.length > 0) {
        // Insert first suggestion
        input.value = suggestions[0];
        input.dispatchEvent(new Event('input'));
      }
    });
  });
  
  // Example toggle
  const exampleToggle = document.getElementById('show-example-toggle');
  const exampleComparison = document.getElementById('example-comparison');
  if (exampleToggle && exampleComparison) {
    exampleToggle.addEventListener('click', () => {
      exampleComparison.classList.toggle('hidden');
      const icon = exampleToggle.querySelector('span');
      if (icon) {
        icon.textContent = exampleComparison.classList.contains('hidden') ? '▶' : '▼';
      }
    });
  }
  
  // Skip button
  const skipBtn = document.getElementById('skip-brand-kit');
  if (skipBtn) {
    skipBtn.addEventListener('click', () => {
      // Just proceed to next step without saving
      step = skipStep2 ? 4 : 3;
      showStep(step);
    });
  }
  
  // Logo upload validation
  const logoUpload = document.getElementById('bk-logo-upload');
  if (logoUpload) {
    logoUpload.addEventListener('change', handleLogoUpload);
  }
  
  // Input change listeners for meter updates
  const inputIds = ['bk-business-name', 'bk-audience', 'bk-pain', 'bk-outcome', 'bk-proof', 
                    'bk-email-name', 'bk-email-title', 'bk-email-contact',
                    'bk-deposit', 'bk-turnaround', 'bk-validity', 'bk-payment-methods'];
  inputIds.forEach(id => {
    const input = document.getElementById(id);
    if (input) {
      input.addEventListener('input', calculateBrandKitTier);
    }
  });
  
  // Event delegation for chip removal buttons
  document.addEventListener('click', (e) => {
    const removeBtn = e.target.closest('[data-remove-chip]');
    if (removeBtn) {
      const type = removeBtn.dataset.removeChip;
      const index = parseInt(removeBtn.dataset.chipIndex, 10);
      if (!isNaN(index)) {
        removeBrandKitChip(type, index);
      }
    }
  });
}

function renderBrandKitChips(containerId, items, type) {
  const container = document.getElementById(containerId);
  if (!container) return;
  
  container.innerHTML = '';
  items.forEach((item, index) => {
    const chip = document.createElement('span');
    chip.className = 'inline-flex items-center gap-1 px-3 py-1 rounded-full text-sm bg-purple-100 text-purple-700';
    
    // Create text node for the item to prevent XSS
    const itemText = document.createTextNode(item);
    chip.appendChild(itemText);
    
    // Create button element
    const removeBtn = document.createElement('button');
    removeBtn.type = 'button';
    removeBtn.className = 'ml-1 text-purple-500 hover:text-purple-700';
    removeBtn.dataset.removeChip = type;
    removeBtn.dataset.chipIndex = index.toString();
    removeBtn.textContent = '×';
    
    chip.appendChild(document.createTextNode(' '));
    chip.appendChild(removeBtn);
    container.appendChild(chip);
  });
}

function removeBrandKitChip(type, index) {
  if (type === 'services') {
    answers.brand_kit.services.splice(index, 1);
    renderBrandKitChips('bk-services-chips', answers.brand_kit.services, 'services');
  } else if (type === 'differentiators') {
    answers.brand_kit.differentiators.splice(index, 1);
    renderBrandKitChips('bk-differentiators-chips', answers.brand_kit.differentiators, 'differentiators');
  }
  calculateBrandKitTier();
}

function calculateBrandKitTier() {
  // Count filled fields
  let score = 0;
  const maxScore = 100;
  
  // GOOD tier (25 points)
  const businessName = document.getElementById('bk-business-name')?.value.trim() || '';
  if (businessName) score += 5;
  if (answers.brand_kit.services.length >= 2) score += 10;
  else if (answers.brand_kit.services.length === 1) score += 5;
  if (document.getElementById('bk-audience')?.value.trim()) score += 5;
  if (document.getElementById('bk-pain')?.value.trim()) score += 3;
  if (document.getElementById('bk-outcome')?.value.trim()) score += 2;
  
  // BETTER tier (25 points)
  if (answers.brand_kit.differentiators.length >= 2) score += 15;
  else if (answers.brand_kit.differentiators.length === 1) score += 7;
  if (document.getElementById('bk-proof')?.value.trim()) score += 10;
  
  // BEST tier (50 points)
  if (document.getElementById('bk-email-name')?.value.trim()) score += 5;
  if (document.getElementById('bk-email-title')?.value.trim()) score += 5;
  if (document.getElementById('bk-email-contact')?.value.trim()) score += 5;
  if (document.getElementById('bk-deposit')?.value.trim()) score += 5;
  if (document.getElementById('bk-turnaround')?.value.trim()) score += 5;
  if (document.getElementById('bk-validity')?.value.trim()) score += 5;
  if (document.getElementById('bk-payment-methods')?.value.trim()) score += 5;
  if (answers.brand_kit.logo) score += 10;
  
  // Determine tier based on score thresholds
  let tier = 'minimum';
  if (score >= 75) {
    tier = 'best';
  } else if (score >= 50) {
    tier = 'stronger';
  }
  // else tier remains 'minimum' (for scores 0-49)
  
  updateBrandKitMeter(tier, score);
}

function updateBrandKitMeter(tier, score) {
  const meterEl = document.getElementById('brand-kit-meter');
  const tierEl = document.getElementById('brand-kit-tier');
  const helperEl = document.getElementById('brand-kit-helper');
  
  if (meterEl) {
    meterEl.style.width = `${score}%`;
    
    // Update color based on tier
    meterEl.className = 'h-full rounded-full transition-all duration-500';
    if (tier === 'best') {
      meterEl.classList.add('bg-gradient-to-r', 'from-purple-500', 'to-purple-600');
    } else if (tier === 'stronger') {
      meterEl.classList.add('bg-gradient-to-r', 'from-blue-500', 'to-blue-600');
    } else {
      meterEl.classList.add('bg-gradient-to-r', 'from-yellow-400', 'to-yellow-500');
    }
  }
  
  if (tierEl) {
    tierEl.textContent = tier === 'minimum' ? 'Good' : tier === 'stronger' ? 'Better' : 'Best';
    tierEl.className = 'px-3 py-1 rounded-full text-sm font-medium';
    if (tier === 'best') {
      tierEl.classList.add('bg-purple-100', 'text-purple-700');
    } else if (tier === 'stronger') {
      tierEl.classList.add('bg-blue-100', 'text-blue-700');
    } else {
      tierEl.classList.add('bg-yellow-100', 'text-yellow-700');
    }
  }
  
  if (helperEl) {
    if (tier === 'best') {
      helperEl.textContent = "Amazing! Your Brand Kit is complete. We'll generate ready-to-send emails and quotes for you.";
    } else if (tier === 'stronger') {
      helperEl.textContent = "Add 2 more and your posts will feel more credible (we'll include proof and why someone should choose you).";
    } else {
      helperEl.textContent = "Fill these 5 fields and you'll get posts you can copy/paste with your services and results included.";
    }
  }
}

function collectBrandKitData() {
  // Collect all Brand Kit form data into answers.brand_kit
  answers.brand_kit.business_name = document.getElementById('bk-business-name')?.value.trim() || '';
  answers.brand_kit.audience = document.getElementById('bk-audience')?.value.trim() || '';
  answers.brand_kit.pain = document.getElementById('bk-pain')?.value.trim() || '';
  answers.brand_kit.outcome = document.getElementById('bk-outcome')?.value.trim() || '';
  answers.brand_kit.proof = document.getElementById('bk-proof')?.value.trim() || '';
  
  answers.brand_kit.email = {
    name: document.getElementById('bk-email-name')?.value.trim() || '',
    title: document.getElementById('bk-email-title')?.value.trim() || '',
    contact: document.getElementById('bk-email-contact')?.value.trim() || ''
  };
  
  answers.brand_kit.quotes = {
    deposit: document.getElementById('bk-deposit')?.value.trim() || '',
    turnaround: document.getElementById('bk-turnaround')?.value.trim() || '',
    validity: document.getElementById('bk-validity')?.value.trim() || '',
    payment_methods: document.getElementById('bk-payment-methods')?.value.trim() || ''
  };
}

async function saveBrandKit() {
  try {
    // Build brand kit payload matching backend schema
    const brandKitPayload = {
      version: 1,
      business: {
        company_name: answers.brand_kit.business_name || null,
        industry_id: answers.industry || '',
        service_area: null,
        timezone: null,
        booking_url: null,
        contact_email: answers.brand_kit.email.contact || null,
        contact_phone: null
      },
      services: {
        primary_services: answers.brand_kit.services || [],
        addons: [],
        pricing_style: null,
        service_constraints: []
      },
      audience: {
        target_roles: answers.brand_kit.audience ? [answers.brand_kit.audience] : [],
        top_pains: answers.brand_kit.pain ? [answers.brand_kit.pain] : [],
        desired_outcomes: answers.brand_kit.outcome ? [answers.brand_kit.outcome] : [],
        sophistication: null,
        objections: []
      },
      positioning: {
        differentiators: answers.brand_kit.differentiators || [],
        values: [],
        boundaries: []
      },
      proof: {
        credentials: [],
        years_in_business: null,
        volume_markers: [],
        testimonials: answers.brand_kit.proof ? [answers.brand_kit.proof] : []
      },
      email: {
        sender_name: answers.brand_kit.email.name || null,
        signoff_style: answers.brand_kit.email.title || null,
        signature_lines: answers.brand_kit.email.contact || null,
        preferred_cta: null,
        links: null
      },
      quotes: {
        default_validity_days: null,
        deposit_policy: answers.brand_kit.quotes.deposit || null,
        payment_methods: answers.brand_kit.quotes.payment_methods || null,
        turnaround_time: answers.brand_kit.quotes.turnaround || null,
        terms_bullets: null,
        disclaimer: null
      },
      assets: {
        logo_asset_id: answers.brand_kit.logo || null,
        logo_url: null
      }
    };
    
    const response = await fetch('/api/brand_kit', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ brand_kit: brandKitPayload })
    });
    
    const data = await response.json();
    if (!data.ok) {
      console.error('Failed to save brand kit:', data.error);
    }
  } catch (error) {
    console.error('Error saving brand kit:', error);
  }
}

async function handleLogoUpload(event) {
  const file = event.target.files[0];
  const errorEl = document.getElementById('bk-logo-error');
  const successEl = document.getElementById('bk-logo-success');
  
  // Reset messages
  if (errorEl) errorEl.classList.add('hidden');
  if (successEl) successEl.classList.add('hidden');
  
  if (!file) return;
  
  // Validate file type
  const validTypes = ['image/png', 'image/jpeg', 'image/webp'];
  if (!validTypes.includes(file.type)) {
    if (errorEl) {
      errorEl.textContent = 'Please upload a PNG, JPG, or WebP image.';
      errorEl.classList.remove('hidden');
    }
    event.target.value = '';
    return;
  }
  
  // Validate file size (2MB max)
  const maxSize = 2 * 1024 * 1024; // 2MB
  if (file.size > maxSize) {
    if (errorEl) {
      errorEl.textContent = 'File size must be under 2MB.';
      errorEl.classList.remove('hidden');
    }
    event.target.value = '';
    return;
  }
  
  // Validate dimensions
  const img = new Image();
  const reader = new FileReader();
  
  reader.onload = (e) => {
    img.onload = () => {
      const maxDim = 2000;
      if (img.width > maxDim || img.height > maxDim) {
        if (errorEl) {
          errorEl.textContent = `Image dimensions must be ${maxDim}x${maxDim} or smaller. Your image is ${img.width}x${img.height}.`;
          errorEl.classList.remove('hidden');
        }
        event.target.value = '';
        return;
      }
      
      // All validations passed
      if (successEl) {
        successEl.textContent = 'Logo validated successfully! (Upload will complete when you save Brand Kit)';
        successEl.classList.remove('hidden');
      }
      
      // Don't store file reference yet - actual upload would happen on save
      // For now, just mark that a logo was selected and validated
      answers.brand_kit.logo = null; // Will be uploaded on save in future implementation
      calculateBrandKitTier();
    };
    img.src = e.target.result;
  };
  
  reader.readAsDataURL(file);
}

// ============================================================================
// End Brand Kit Functions
// ============================================================================

// Call initialization
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initBrandInspiration);
} else {
  initBrandInspiration();
}
