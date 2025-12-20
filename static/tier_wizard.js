// Minimal Tier Wizard progressive enhancement
// Renders three tiers (Good, Better, Best) and a sticky quality meter.
(function () {
  console.log('Tier wizard script loaded');
  function el(tag, attrs = {}, children = []) {
    const n = document.createElement(tag);
    Object.keys(attrs).forEach(k => {
      if (k === 'class') n.className = attrs[k];
      else if (k === 'text') n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(c => { if (typeof c === 'string') n.appendChild(document.createTextNode(c)); else n.appendChild(c); });
    return n;
  }

  function createTier(id, title, note, outcome, required = false) {
    const root = el('section', { class: 'tier-section bg-white/80 rounded-2xl p-6 border border-slate-200' });
    root.id = `tier-${id}`;
    const header = el('div', { class: 'flex items-center justify-between mb-3' });
    header.appendChild(el('div', { class: 'text-lg font-semibold text-slate-900', text: title }));
    header.appendChild(el('div', { class: 'text-sm text-slate-500', text: required ? 'Required' : 'Optional' }));
    root.appendChild(header);
    root.appendChild(el('p', { class: 'text-sm text-slate-600 mb-3', text: note }));

    // outcome & progress
    const outcomeEl = el('p', { class: 'text-sm text-slate-700 mb-3', text: outcome });
    root.appendChild(outcomeEl);
    const progressWrap = el('div', { class: 'w-full bg-slate-100 rounded-full h-3 mb-3' });
    const bar = el('div', { class: 'tier-progress bg-purple-600 h-3 rounded-full', role: 'progressbar' });
    bar.style.width = '0%';
    progressWrap.appendChild(bar);
    root.appendChild(progressWrap);

    // For GOOD tier, add form fields
    if (id === 'good') {
      const form = el('div', { class: 'space-y-4 mb-4', style: 'display: block; visibility: visible;' });
      
      // Company field
      const companyGroup = el('div');
      companyGroup.appendChild(el('label', { class: 'block text-sm font-medium text-slate-700 mb-1', text: 'Company / Business name' }));
      const companyInput = el('input', { 
        type: 'text', 
        class: 'w-full input text-sm py-2 px-3 rounded-lg border-slate-300 focus:border-purple-500 focus:ring-purple-500',
        placeholder: 'e.g., Laura\'s Bakery',
        id: 'tier-company',
        style: 'display: block; width: 100%; padding: 0.5rem 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem;'
      });
      companyGroup.appendChild(companyInput);
      form.appendChild(companyGroup);
      
      // Industry field (simplified dropdown)
      const industryGroup = el('div');
      industryGroup.appendChild(el('label', { class: 'block text-sm font-medium text-slate-700 mb-1', text: 'Industry' }));
      const industrySelect = el('select', { 
        class: 'w-full input text-sm py-2 px-3 rounded-lg border-slate-300 focus:border-purple-500 focus:ring-purple-500',
        id: 'tier-industry',
        style: 'display: block; width: 100%; padding: 0.5rem 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem;'
      });
      industrySelect.appendChild(el('option', { value: '', text: 'Choose your industry...' }));
      // Add some common industries
      const industries = ['Restaurant', 'Retail', 'Healthcare', 'Education', 'Technology', 'Consulting', 'Real Estate', 'Fitness', 'Beauty', 'Other'];
      industries.forEach(ind => {
        industrySelect.appendChild(el('option', { value: ind.toLowerCase(), text: ind }));
      });
      industryGroup.appendChild(industrySelect);
      form.appendChild(industryGroup);
      
      // Tone field
      const toneGroup = el('div');
      toneGroup.appendChild(el('label', { class: 'block text-sm font-medium text-slate-700 mb-1', text: 'Tone' }));
      const toneSelect = el('select', { 
        class: 'w-full input text-sm py-2 px-3 rounded-lg border-slate-300 focus:border-purple-500 focus:ring-purple-500',
        id: 'tier-tone',
        style: 'display: block; width: 100%; padding: 0.5rem 0.75rem; border: 1px solid #d1d5db; border-radius: 0.5rem;'
      });
      toneSelect.appendChild(el('option', { value: '', text: 'Choose your tone...' }));
      const tones = ['Professional', 'Friendly', 'Casual', 'Inspirational', 'Humorous', 'Bold'];
      tones.forEach(tone => {
        toneSelect.appendChild(el('option', { value: tone.toLowerCase(), text: tone }));
      });
      toneGroup.appendChild(toneSelect);
      form.appendChild(toneGroup);
      
      root.appendChild(form);
    }

    const actions = el('div', { class: 'flex items-center gap-3' });
    const btn = el('button', { class: 'btn-primary btn-sm', text: required ? 'Complete' : 'Improve' });
    if (id === 'good') {
      btn.addEventListener('click', () => completeGoodTier());
    } else {
      btn.addEventListener('click', () => jumpToStep(id));
    }
    actions.appendChild(btn);
    if (!required) {
      const skip = el('button', { class: 'btn-ghost btn-sm', text: 'Skip for now' });
      skip.addEventListener('click', () => markSkipped(id));
      actions.appendChild(skip);
    }
    root.appendChild(actions);

    return { root, bar };
  }

  function jumpToStep(tierId) {
    // Map tierId to existing legacy step panel numbers for gradual migration
    const mapping = { good: '[data-step="1"]', better: '[data-step="3"]', best: '[data-step="4"]' };
    const selector = mapping[tierId];
    const target = document.querySelector(selector);
    if (target) target.scrollIntoView({ behavior: 'smooth', block: 'center' });
  }

  async function completeGoodTier() {
    const company = document.getElementById('tier-company')?.value?.trim();
    const industry = document.getElementById('tier-industry')?.value;
    const tone = document.getElementById('tier-tone')?.value;
    
    if (!company || !industry || !tone) {
      alert('Please fill in all required fields: company, industry, and tone.');
      return;
    }
    
    try {
      const response = await fetch('/api/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ company, industry, tone })
      });
      
      const result = await response.json();
      if (result.ok) {
        // Update progress bar
        const bar = document.querySelector('#tier-good .tier-progress');
        if (bar) bar.style.width = '100%';
        updateQualityMeter();
        
        // Show success feedback
        const btn = document.querySelector('#tier-good .btn-primary');
        if (btn) {
          const originalText = btn.textContent;
          btn.textContent = '✓ Saved!';
          btn.disabled = true;
          setTimeout(() => {
            btn.textContent = originalText;
            btn.disabled = false;
          }, 2000);
        }
      } else {
        alert('Failed to save: ' + (result.error || 'Unknown error'));
      }
    } catch (error) {
      console.error('Save error:', error);
      alert('Failed to save profile. Please try again.');
    }
  }

  function markSkipped(id) {
    const bar = document.querySelector(`#tier-${id} .tier-progress`);
    if (bar) bar.style.width = '20%';
    updateQualityMeter();
  }

  function updateQualityMeter() {
    const bars = document.querySelectorAll('.tier-progress');
    let score = 0;
    bars.forEach((b, i) => { const w = parseInt(b.style.width || '0', 10); if (w >= 80) score = Math.max(score, i + 1); });
    const meter = document.getElementById('tier-quality-meter');
    if (!meter) return;
    const labels = ['Good', 'Better', 'Best'];
    meter.textContent = labels[score] || 'Good';
  }

  async function mount() {
    console.log('Tier wizard mount function called');
    const root = document.getElementById('tier-wizard-root');
    console.log('Tier wizard root element:', root);
    if (!root) {
      console.log('Tier wizard root not found');
      return;
    }
    // Idempotency guard: if we've already mounted, do nothing
    if (root.dataset && root.dataset.tierWizardMounted) {
      console.log('Tier wizard already mounted — skipping');
      return;
    }
    if (root.dataset) root.dataset.tierWizardMounted = '1';
    
    // Add a visible test element first
    const testDiv = el('div', { 
      style: 'background: red; color: white; padding: 20px; margin: 10px; border: 2px solid black;',
      text: 'TIER WIZARD IS LOADING...'
    });
    root.appendChild(testDiv);
    console.log('Added test element to root');
    const container = el('div', { class: 'grid gap-4 lg:grid-cols-[1fr,320px]' });
    const left = el('div', { class: 'space-y-4' });
    const right = el('aside', { class: 'space-y-4' });

    const good = createTier('good', 'GOOD ✅ — 2 minutes', 'Minimum to generate great content fast', 'You’ll get copy/paste-ready posts that match your industry + what you actually offer.', true);
    const better = createTier('better', 'BETTER ⭐ — optional', '+30–50% better results', 'Posts become specific to your customers, not generic templates.');
    const best = createTier('best', 'BEST 👑 — optional', 'Highest quality + most consistent outputs', 'Premium brand kit and personalization for highest quality outputs.');

    left.appendChild(good.root);
    left.appendChild(better.root);
    left.appendChild(best.root);

    const summary = el('div', { class: 'bg-white/90 rounded-2xl p-4 border border-slate-200 sticky top-6' });
    summary.appendChild(el('h4', { class: 'text-lg font-semibold text-slate-900 mb-2', text: 'Your Content Quality' }));
    const meter = el('div', { id: 'tier-quality-meter', class: 'text-2xl font-bold text-purple-700 mb-2', text: 'Good' });
    summary.appendChild(meter);
    summary.appendChild(el('p', { class: 'text-sm text-slate-600', text: 'Shows which tier is ready and what’s missing.' }));
    summary.appendChild(el('div', { class: 'mt-3' }, []));
    right.appendChild(summary);

    container.appendChild(left);
    container.appendChild(right);
    root.appendChild(container);

    // Load existing profile data and populate form
    try {
      const response = await fetch('/api/profile');
      const data = await response.json();
      if (data.ok && data.profile) {
        const profile = data.profile;
        
        // Populate form fields
        const companyInput = document.getElementById('tier-company');
        const industrySelect = document.getElementById('tier-industry');
        const toneSelect = document.getElementById('tier-tone');
        
        if (companyInput && profile.company) companyInput.value = profile.company;
        if (industrySelect && profile.industry) industrySelect.value = profile.industry;
        if (toneSelect && profile.tone) toneSelect.value = profile.tone;
        
        // Set progress based on what's saved
        const hasBasic = profile.company && profile.industry && profile.tone;
        if (hasBasic) {
          good.bar.style.width = '100%';
        }
      }
    } catch (error) {
      console.warn('Failed to load existing profile:', error);
    }

    updateQualityMeter();
  }

  // Expose a stable, explicit boot API. Consumers should call TierWizard.boot({ flags, profile, packs })
  // Boot will be a no-op if the root element is missing or if the flag is disabled.
  window.TierWizard = {
    boot: async function boot(opts = {}) {
      try {
        const flags = opts.flags || window.FLAGS || {};
        // Respect explicit falsey flag
        // If the flag is explicitly false, do not boot. If the flag is
        // undefined (app bundle not yet loaded), allow auto-boot so the
        // wizard can initialize during deploys where app.js may run later.
        if (flags.tierWizard === false) return;
        // Provide flags globally for any legacy code that checks window.FLAGS
        window.FLAGS = flags;

        const body = document.body;
        if (body) body.setAttribute('data-tier-wizard', '1');

        // Mount into the root (mount is a local async function above)
        await mount();
      } catch (err) {
        // Do not throw — calling code should tolerate failures
        console.error('TierWizard.boot error', err);
      }
    }
  };

  // Auto-start helper: if the page path is /app and the feature flag is not
  // explicitly disabled, try to boot after a short delay. This makes the
  // tier wizard resilient to script ordering (app.js may load first or later)
  // and helps staging rollouts where the template may include the tier root
  // but the main app bundle hasn't yet invoked boot.
  (function autoBootIfAppropriate(){
    try{
      const shouldAuto = (function(){
        const path = (window.location && window.location.pathname) || '';
        if (!path.startsWith('/app')) return false;
        // if FLAGS exists and explicitly disables tierWizard, do not auto-boot
        if (typeof window.FLAGS !== 'undefined' && window.FLAGS && window.FLAGS.tierWizard === false) return false;
        return true;
      })();
      if (!shouldAuto) return;
      // wait briefly to allow DOM to be ready; if boot is called by app.js
      // it will be a no-op because of idempotency guard.
      setTimeout(() => {
        try{
          if (window.TierWizard && typeof window.TierWizard.boot === 'function') {
            window.TierWizard.boot({ flags: window.FLAGS || {} }).catch(()=>{});
          }
        }catch(e){/* ignore */}
      }, 600);
    }catch(e){/* ignore */}
  })();
})();
