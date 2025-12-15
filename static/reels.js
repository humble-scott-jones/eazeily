(function(){
  const form = document.getElementById('reels-form');
  const statusEl = document.getElementById('reels-status');
  const output = document.getElementById('reels-output');
  const sectionsContainer = document.getElementById('reels-sections');
  const exportBtn = document.getElementById('export-all');
  const regenHookBtn = document.getElementById('regen-hook');
  const regenCtaBtn = document.getElementById('regen-cta');
  const quickGenerateBtn = document.getElementById('quick-generate-reel');

  if (!form || !sectionsContainer) return;

  function setStatus(message, tone = 'info'){
    if (!statusEl) return;
    statusEl.textContent = message || '';
    statusEl.className = `text-sm ${tone === 'error' ? 'text-red-600' : 'text-slate-600'}`;
  }

  function sectionNode(key){
    return sectionsContainer.querySelector(`[data-section="${key}"] [data-section-text]`);
  }

  function copyText(text){
    if (!text) return;
    navigator.clipboard?.writeText(text).then(() => {
      setStatus('Copied to clipboard');
    }).catch(() => {
      setStatus('Copy failed, select and copy manually.', 'error');
    });
  }

  function serializeForm(){
    const data = new FormData(form);
    return {
      hook_style: data.get('hook_style') || 'Face-camera tips',
      format: data.get('format') || 'talking_head',
      duration_seconds: Number(data.get('duration_seconds') || 30),
      include_shot_list: data.get('include_shot_list') !== null,
      include_on_screen_text: data.get('include_on_screen_text') !== null
    };
  }

  function renderReel(reel){
    if (!reel) return;
    output?.setAttribute('aria-busy', 'false');
    const hookEl = sectionNode('hook');
    const beatsEl = sectionNode('beats');
    const ctaEl = sectionNode('cta');
    const captionEl = sectionNode('caption');
    const hashtagsEl = sectionNode('hashtags');
    const shotListEl = sectionNode('shot_list');
    const overlaysEl = sectionNode('on_screen_text');

    if (hookEl) hookEl.textContent = reel.hook || '—';
    if (beatsEl){
      beatsEl.innerHTML = '';
      const beats = Array.isArray(reel.beats) ? reel.beats : [];
      beats.forEach(beat => {
        const li = document.createElement('li');
        li.textContent = `${beat.label || beat.osd || 'Beat'} (${beat.start ?? beat.start_s ?? 0}s-${beat.end ?? beat.end_s ?? ''}s): ${beat.line || ''}`;
        li.className = 'list-disc list-inside';
        beatsEl.appendChild(li);
      });
    }
    if (ctaEl) ctaEl.textContent = reel.cta || '—';
    if (captionEl) captionEl.textContent = reel.caption || '—';
    if (hashtagsEl) hashtagsEl.textContent = (reel.hashtags || []).join(' ');

    if (shotListEl){
      shotListEl.innerHTML = '';
      const shots = Array.isArray(reel.shot_list) ? reel.shot_list : [];
      if (shots.length === 0){
        const li = document.createElement('li');
        li.textContent = 'Shot list disabled for this run.';
        li.className = 'list-disc list-inside';
        shotListEl.appendChild(li);
      }else{
        shots.forEach(item => {
          const li = document.createElement('li');
          const start = item.start ?? item.start_s ?? 0;
          const end = item.end ?? item.end_s ?? '';
          li.textContent = `${item.beat || 'Beat'} (${start}s-${end}s): ${item.shot || item.shot_type || item.overlay || ''}`;
          li.className = 'list-disc list-inside';
          shotListEl.appendChild(li);
        });
      }
    }

    if (overlaysEl){
      overlaysEl.innerHTML = '';
      const overlays = Array.isArray(reel.on_screen_text) ? reel.on_screen_text : [];
      if (overlays.length === 0){
        const li = document.createElement('li');
        li.textContent = 'On-screen text disabled for this run.';
        li.className = 'list-disc list-inside';
        overlaysEl.appendChild(li);
      }else{
        overlays.forEach(line => {
          const li = document.createElement('li');
          li.textContent = line;
          li.className = 'list-disc list-inside';
          overlaysEl.appendChild(li);
        });
      }
    }
  }

  function exportAll(){
    const parts = [];
    sectionsContainer.querySelectorAll('[data-section]').forEach(section => {
      const key = section.getAttribute('data-section');
      const heading = section.querySelector('h3')?.textContent || key;
      const textNodes = section.querySelectorAll('[data-section-text]');
      const lines = [];
      textNodes.forEach(node => {
        if (node.tagName === 'UL'){
          node.querySelectorAll('li').forEach(li => lines.push(li.textContent));
        } else {
          lines.push(node.textContent);
        }
      });
      parts.push(`${heading}\n${lines.join('\n')}`.trim());
    });
    copyText(parts.join('\n\n'));
  }

  async function requestReel(payload){
    output?.setAttribute('aria-busy', 'true');
    setStatus('Generating…');
    const res = await fetch('/api/generate/reels', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify(payload)
    });
    const data = await res.json();
    if (!data.ok){
      setStatus(data.error?.message || 'Unable to generate right now.', 'error');
      output?.setAttribute('aria-busy', 'false');
      return null;
    }
    return data;
  }

  async function handleGenerate(evt){
    evt.preventDefault();
    const payload = serializeForm();
    const data = await requestReel(payload);
    if (data && data.reel){
      renderReel(data.reel);
      setStatus('Script ready');
      regenHookBtn?.removeAttribute('disabled');
      regenCtaBtn?.removeAttribute('disabled');
    }
  }

  async function handleSectionRegen(section){
    const payload = serializeForm();
    payload.section = section;
    const data = await requestReel(payload);
    if (!data) return;
    if (section === 'hook' && data.hook){
      renderReel({
        hook: data.hook,
        beats: [],
        cta: sectionNode('cta')?.textContent,
        caption: sectionNode('caption')?.textContent,
        hashtags: (sectionNode('hashtags')?.textContent || '').split(/\s+/).filter(Boolean),
        shot_list: [],
        on_screen_text: []
      });
      setStatus('Hook regenerated');
    }
    if (section === 'cta' && data.cta){
      renderReel({
        hook: sectionNode('hook')?.textContent,
        beats: [],
        cta: data.cta,
        caption: sectionNode('caption')?.textContent,
        hashtags: (sectionNode('hashtags')?.textContent || '').split(/\s+/).filter(Boolean),
        shot_list: [],
        on_screen_text: []
      });
      setStatus('CTA regenerated');
    }
  }

  form.addEventListener('submit', handleGenerate);
  regenHookBtn?.addEventListener('click', () => handleSectionRegen('hook'));
  regenCtaBtn?.addEventListener('click', () => handleSectionRegen('cta'));
  exportBtn?.addEventListener('click', exportAll);
  
  // Quick generate handler
  quickGenerateBtn?.addEventListener('click', async () => {
    // Trigger the form submission to generate a reel with current settings
    await handleGenerate(new Event('submit'));
  });

  sectionsContainer.querySelectorAll('[data-copy-section]').forEach(btn => {
    btn.addEventListener('click', () => {
      const key = btn.getAttribute('data-copy-section');
      const target = sectionNode(key);
      if (!target) return;
      if (target.tagName === 'UL'){
        const lines = [];
        target.querySelectorAll('li').forEach(li => lines.push(li.textContent));
        copyText(lines.join('\n'));
      } else {
        copyText(target.textContent);
      }
    });
  });
})();
