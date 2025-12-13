(function() {
  const form = document.getElementById('social-generator-form');
  if (!form) return;

  const goalsInput = document.getElementById('gen-goals');
  const keywordsInput = document.getElementById('gen-keywords');
  const toneSelect = document.getElementById('gen-tone');
  const daysSelect = document.getElementById('gen-days');
  const lengthSelect = document.getElementById('gen-length');
  const promoInput = document.getElementById('gen-promo');
  const imageInput = document.getElementById('gen-image');
  const platformsContainer = document.getElementById('generator-platforms');
  const generateBtn = document.getElementById('generate-plan');
  const cancelBtn = document.getElementById('cancel-generate');
  const statusEl = document.getElementById('generate-status');
  const summaryEl = document.getElementById('generator-summary-text');
  const errorBox = document.getElementById('generator-error');
  const errorMessageEl = document.getElementById('generator-error-message');
  const errorDebugEl = document.getElementById('generator-debug');
  const retryBtn = document.getElementById('retry-generate');
  const copyDebugBtn = document.getElementById('copy-debug');
  const contentResults = document.getElementById('content-results');
  const toolbar = document.getElementById('generated-toolbar');
  const platformFilterChips = document.getElementById('platform-filter-chips');
  const generatedToolbar = document.getElementById('generated-toolbar');
  const generateLabel = document.getElementById('generate-label');
  const saveAsTemplateCta = document.getElementById('save-as-template-cta');
  const addToQueueCta = document.getElementById('add-to-queue-cta');
  const generatorContainer = document.getElementById('generated-content');

  let abortController = null;
  let progressTimer = null;
  let lastRequestId = '';

  function getSelectedPlatforms() {
    const buttons = platformsContainer ? Array.from(platformsContainer.querySelectorAll('[data-generator-platform]')) : [];
    return buttons.filter(btn => btn.classList.contains('chip--active')).map(btn => btn.getAttribute('data-generator-platform'));
  }

  function setPlatformActive(button, active) {
    button.classList.toggle('chip--active', active);
    button.setAttribute('aria-pressed', active ? 'true' : 'false');
  }

  function togglePlatform(button) {
    const active = button.classList.contains('chip--active');
    const shouldActivate = !active;
    setPlatformActive(button, shouldActivate);
    updateSummary();
    validate();
  }

  function validate() {
    const hasGoals = goalsInput && goalsInput.value.trim().length > 0;
    const hasPlatform = getSelectedPlatforms().length > 0;
    const daysVal = parseInt(daysSelect ? daysSelect.value : '0', 10) || 0;
    const isValid = Boolean(hasGoals && hasPlatform && daysVal > 0);
    generateBtn.disabled = !isValid;
    generateBtn.setAttribute('aria-disabled', String(!isValid));
    return isValid;
  }

  function updateSummary() {
    if (!summaryEl) return;
    const platforms = getSelectedPlatforms();
    const goals = goalsInput ? goalsInput.value.trim() : '';
    const tone = toneSelect ? toneSelect.value : '';
    const length = lengthSelect ? lengthSelect.value : '';
    const pieces = [];
    if (goals) pieces.push(`Goals: ${goals}`);
    if (platforms.length) pieces.push(`Platforms: ${platforms.join(', ')}`);
    if (tone) pieces.push(`Tone: ${tone}`);
    if (length) pieces.push(`Length: ${length}`);
    summaryEl.textContent = pieces.length ? pieces.join(' · ') : 'Select platforms and goals to see your generation plan.';
  }

  function setStatus(text) {
    if (statusEl) {
      statusEl.textContent = text || '';
    }
  }

  function showError(message, requestId) {
    if (!errorBox) return;
    errorMessageEl.textContent = message || 'Unable to generate content right now.';
    errorDebugEl.textContent = requestId ? `request_id: ${requestId}` : '';
    errorBox.classList.remove('hidden');
    errorBox.focus({ preventScroll: true });
  }

  function hideError() {
    if (!errorBox) return;
    errorBox.classList.add('hidden');
    errorMessageEl.textContent = '';
    errorDebugEl.textContent = '';
  }

  function renderPlatformFilters(platforms) {
    if (!platformFilterChips) return;
    platformFilterChips.innerHTML = '';
    platforms.forEach(platform => {
      const btn = document.createElement('button');
      btn.type = 'button';
      btn.className = 'filter-chip';
      btn.textContent = platform;
      btn.dataset.platform = platform;
      btn.setAttribute('aria-pressed', 'true');
      btn.addEventListener('click', () => {
        const expanded = btn.getAttribute('aria-pressed') === 'true';
        btn.setAttribute('aria-pressed', expanded ? 'false' : 'true');
        const hidden = Array.from(platformFilterChips.querySelectorAll('[data-platform]'))
          .filter(el => el.getAttribute('aria-pressed') === 'false')
          .map(el => el.dataset.platform);
        Array.from(contentResults.querySelectorAll('[data-platform-entry]')).forEach(card => {
          const plat = card.getAttribute('data-platform-entry');
          card.classList.toggle('hidden', hidden.includes(plat));
        });
      });
      platformFilterChips.appendChild(btn);
    });
    generatedToolbar.classList.toggle('hidden', platforms.length === 0);
  }

  function createQuickAction(label, handler) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'btn-ghost btn-sm';
    btn.textContent = label;
    btn.addEventListener('click', handler);
    return btn;
  }

  async function copyToClipboard(text) {
    try {
      await navigator.clipboard.writeText(text);
      setStatus('Copied to clipboard');
    } catch (err) {
      setStatus('Copy failed');
    }
  }

  function renderResults(data) {
    if (!contentResults) return;
    contentResults.innerHTML = '';
    const days = data.days || [];
    const platforms = new Set();
    days.forEach(day => {
      const dayCard = document.createElement('div');
      dayCard.className = 'generated-day';
      const header = document.createElement('div');
      header.className = 'generated-day__header';
      const title = document.createElement('h3');
      title.textContent = day.label || `Day ${day.day}`;
      header.appendChild(title);
      const regenDay = createQuickAction('Regenerate day', () => runGeneration({ target_day: day.day }));
      header.appendChild(regenDay);
      dayCard.appendChild(header);

      const platformsWrap = document.createElement('div');
      platformsWrap.className = 'generated-day__platforms';
      (day.platforms || []).forEach(entry => {
        platforms.add(entry.platform);
        const card = document.createElement('div');
        card.className = 'generated-card';
        card.dataset.platformEntry = entry.platform;
        const topRow = document.createElement('div');
        topRow.className = 'generated-card__title-row';
        const platformLabel = document.createElement('p');
        platformLabel.className = 'generated-card__eyebrow';
        platformLabel.textContent = entry.platform;
        topRow.appendChild(platformLabel);
        const regenPlatform = createQuickAction('Regenerate platform', () => runGeneration({ target_platform: entry.platform, target_day: day.day }));
        topRow.appendChild(regenPlatform);
        card.appendChild(topRow);

        const caption = document.createElement('p');
        caption.className = 'generated-card__caption';
        caption.textContent = entry.caption;
        card.appendChild(caption);

        if (entry.hashtags && entry.hashtags.length) {
          const tags = document.createElement('p');
          tags.className = 'generated-card__hashtags';
          tags.textContent = entry.hashtags.join(' ');
          card.appendChild(tags);
        }

        const actions = document.createElement('div');
        actions.className = 'generated-card__actions';
        actions.appendChild(createQuickAction('Copy caption', () => copyToClipboard(entry.caption)));
        if (entry.hashtags && entry.hashtags.length) {
          actions.appendChild(createQuickAction('Copy hashtags', () => copyToClipboard(entry.hashtags.join(' '))));
        }
        actions.appendChild(createQuickAction('Add to Queue', () => setStatus('Queued for publishing')));
        card.appendChild(actions);

        platformsWrap.appendChild(card);
      });

      dayCard.appendChild(platformsWrap);
      contentResults.appendChild(dayCard);
    });

    renderPlatformFilters(Array.from(platforms));
    generatorContainer?.classList.remove('hidden');
  }

  function startProgress() {
    const steps = ['Drafting…', 'Formatting…', 'Finalizing…'];
    let idx = 0;
    setStatus(steps[idx]);
    if (progressTimer) clearInterval(progressTimer);
    progressTimer = window.setInterval(() => {
      idx = (idx + 1) % steps.length;
      setStatus(steps[idx]);
    }, 1200);
    generateBtn.disabled = true;
    cancelBtn.disabled = false;
    generateLabel.textContent = 'Generating…';
  }

  function stopProgress() {
    if (progressTimer) {
      clearInterval(progressTimer);
      progressTimer = null;
    }
    generateLabel.textContent = 'Generate plan';
    cancelBtn.disabled = true;
  }

  function buildPayload(extra = {}) {
    const keywordsRaw = (keywordsInput && keywordsInput.value) || '';
    const keywords = keywordsRaw
      .split(',')
      .map(k => k.trim())
      .filter(Boolean);
    const payload = {
      platforms: getSelectedPlatforms(),
      tone: toneSelect ? toneSelect.value : 'friendly',
      goals: goalsInput ? goalsInput.value.trim() : '',
      days: parseInt(daysSelect ? daysSelect.value : '0', 10) || 0,
      keywords,
      length: lengthSelect ? lengthSelect.value : 'medium',
      promo: promoInput ? promoInput.value.trim() : '',
      image: imageInput ? imageInput.value.trim() : '',
      request_meta: { from: 'social-planner' },
      ...extra,
    };
    return payload;
  }

  async function runGeneration(extra = {}) {
    if (!validate()) return;
    hideError();
    abortController = new AbortController();
    startProgress();
    const payload = buildPayload(extra);
    try {
      const res = await fetch('/api/generate/social', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
        signal: abortController.signal,
      });
      const body = await res.json().catch(() => ({}));
      lastRequestId = body.request_id || '';
      stopProgress();
      if (!res.ok || !body.ok) {
        showError((body.error && body.error.message) || 'Unable to generate', body.request_id);
        generateBtn.disabled = false;
        return;
      }
      renderResults(body.data || {});
      setStatus('Plan ready');
      generateBtn.disabled = false;
    } catch (err) {
      stopProgress();
      if (err.name === 'AbortError') {
        setStatus('Generation cancelled');
        return;
      }
      showError('Request failed. Please try again.', lastRequestId);
      generateBtn.disabled = false;
    }
  }

  form.addEventListener('submit', evt => {
    evt.preventDefault();
    runGeneration();
  });

  retryBtn?.addEventListener('click', () => runGeneration());
  copyDebugBtn?.addEventListener('click', () => {
    if (!lastRequestId) return;
    copyToClipboard(`request_id=${lastRequestId}`);
  });
  cancelBtn?.addEventListener('click', () => {
    if (abortController) {
      abortController.abort();
    }
  });

  if (platformsContainer) {
    platformsContainer.querySelectorAll('[data-generator-platform]').forEach(btn => {
      btn.addEventListener('click', () => togglePlatform(btn));
      btn.addEventListener('keydown', e => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          togglePlatform(btn);
        }
      });
    });
  }

  if (daysSelect) {
    daysSelect.addEventListener('change', validate);
  }
  goalsInput?.addEventListener('input', () => {
    validate();
    updateSummary();
  });
  toneSelect?.addEventListener('change', updateSummary);
  lengthSelect?.addEventListener('change', updateSummary);
  keywordsInput?.addEventListener('input', updateSummary);

  document.getElementById('quick-sample')?.addEventListener('click', () => {
    if (goalsInput) goalsInput.value = 'Preview the product launch and invite early adopters.';
    daysSelect.value = '1';
    validate();
    updateSummary();
  });
  document.getElementById('quick-7day')?.addEventListener('click', () => {
    if (goalsInput) goalsInput.value = 'Keep the pipeline warm with educational posts and founder notes.';
    daysSelect.value = '7';
    validate();
    updateSummary();
  });

  saveAsTemplateCta?.addEventListener('click', () => setStatus('Template save coming soon'));
  addToQueueCta?.addEventListener('click', () => setStatus('Added to queue'));

  updateSummary();
  validate();
})();
