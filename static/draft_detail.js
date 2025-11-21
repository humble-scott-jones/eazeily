(function () {
  const statusMap = {
    draft: { label: 'Draft', classes: 'bg-slate-100 text-slate-700 border border-slate-200' },
    in_review: { label: 'In Review', classes: 'bg-amber-100 text-amber-800 border border-amber-200' },
    approved: { label: 'Approved', classes: 'bg-emerald-100 text-emerald-700 border border-emerald-200' },
    scheduled: { label: 'Scheduled', classes: 'bg-blue-100 text-blue-700 border border-blue-200' },
  };

  const draftId = (window.DRAFT_VIEW && window.DRAFT_VIEW.draftId) || document.body.dataset.draftId;
  const titleEl = document.getElementById('draft-title');
  const metaEl = document.getElementById('draft-meta');
  const chipWrap = document.getElementById('detail-chips');
  const statusChipWrap = document.getElementById('status-chip');
  const statusActions = document.getElementById('status-actions');
  const sectionsEl = document.getElementById('content-sections');
  const revisionList = document.getElementById('revision-list');
  const revisionCount = document.getElementById('revision-count');
  let lastStatus = null;

  async function loadDraft() {
    if (!draftId) return;
    try {
      const res = await fetch(`/api/team/drafts/${draftId}`, { credentials: 'include' });
      if (!res.ok) throw new Error('Unable to load draft');
      const data = await res.json();
      lastStatus = data.draft ? data.draft.status : null;
      renderDraft(data.draft || {}, data.threads || [], data.revisions || []);
    } catch (err) {
      console.error(err);
      if (sectionsEl) {
        sectionsEl.innerHTML = `<div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">${err.message}</div>`;
      }
    }
  }

  function renderDraft(draft, threads, revisions) {
    if (titleEl) titleEl.textContent = draft.title || 'Untitled draft';
    if (metaEl) metaEl.textContent = `${draft.campaign || 'Uncategorized'} • Due ${formatDate(draft.due_date)} • ${draft.assignee_email || 'Unassigned'}`;
    renderStatusChip(draft.status);
    renderDetailChips(draft);
    renderStatusActions(draft);
    renderSections(draft.content || [], threads || []);
    renderRevisions(revisions || []);
  }

  function renderStatusChip(statusKey) {
    if (!statusChipWrap) return;
    statusChipWrap.innerHTML = '';
    const meta = statusMap[(statusKey || '').toLowerCase()] || statusMap.draft;
    const badge = document.createElement('span');
    badge.className = `px-3 py-1 rounded-full text-xs font-semibold ${meta.classes}`;
    badge.textContent = meta.label;
    statusChipWrap.appendChild(badge);
  }

  function renderDetailChips(draft) {
    if (!chipWrap) return;
    chipWrap.innerHTML = '';
    const chips = [
      { label: 'Assignee', value: draft.assignee_email || 'Unassigned' },
      { label: 'Campaign', value: draft.campaign || 'Uncategorized' },
      { label: 'Due', value: formatDate(draft.due_date) },
    ];
    chips.forEach((chip) => {
      const el = document.createElement('div');
      el.className = 'bg-slate-100 text-slate-700 text-xs px-3 py-1 rounded-full border border-slate-200';
      el.textContent = `${chip.label}: ${chip.value}`;
      chipWrap.appendChild(el);
    });
  }

  function renderStatusActions(draft) {
    if (!statusActions) return;
    statusActions.innerHTML = '';
    const approveBtn = button('Approve', 'bg-emerald-600 hover:bg-emerald-700 text-white', () => updateStatus('approve'));
    const changesBtn = button('Request changes', 'bg-amber-600 hover:bg-amber-700 text-white', () => updateStatus('request_changes'));
    const undoBtn = button('Undo', 'bg-slate-100 text-slate-700 border border-slate-200', () => updateStatus('undo'));
    statusActions.appendChild(approveBtn);
    statusActions.appendChild(changesBtn);
    statusActions.appendChild(undoBtn);
    if ((draft.status || '').toLowerCase() === 'approved') {
      changesBtn.classList.add('opacity-80');
    }
  }

  function button(label, classes, onClick) {
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = `px-4 py-2 rounded-lg text-sm font-semibold transition ${classes}`;
    btn.textContent = label;
    btn.addEventListener('click', onClick);
    return btn;
  }

  async function updateStatus(action) {
    if (!draftId) return;
    try {
      const res = await fetch(`/api/team/drafts/${draftId}/status`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ action, status: action === 'undo' ? lastStatus : undefined }),
      });
      if (!res.ok) throw new Error('Unable to update status');
      const data = await res.json();
      if (data.previous_status) lastStatus = data.previous_status;
      renderDraft(data.draft || {}, data.threads || [], data.revisions || []);
    } catch (err) {
      console.error(err);
      alert(err.message);
    }
  }

  function renderSections(content, threads) {
    if (!sectionsEl) return;
    sectionsEl.innerHTML = '';
    const threadMap = buildThreadMap(threads || []);
    (content || []).forEach((section) => {
      const card = document.createElement('article');
      card.className = 'bg-white border border-slate-200 rounded-2xl shadow-sm p-5 space-y-3';
      card.innerHTML = `
        <div class="flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.3em] text-slate-500">${section.heading || 'Section'}</p>
            <h3 class="text-xl font-semibold text-slate-900">${section.text || ''}</h3>
          </div>
          <span class="text-xs text-slate-500">Paragraph ID: ${section.id}</span>
        </div>
      `;
      const threadContainer = document.createElement('div');
      threadContainer.className = 'space-y-3';
      (threadMap.get(section.id) || []).forEach((thread) => {
        threadContainer.appendChild(renderThread(thread));
      });
      const composer = document.createElement('div');
      composer.className = 'border border-slate-200 rounded-xl p-3 bg-slate-50 space-y-2';
      const label = document.createElement('div');
      label.className = 'text-xs text-slate-500';
      label.textContent = 'Add a comment';
      const textarea = document.createElement('textarea');
      textarea.className = 'w-full border border-slate-200 rounded-lg p-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand/60';
      textarea.rows = 2;
      textarea.placeholder = 'Leave feedback and @mention teammates';
      const submit = button('Post', 'bg-brand text-white hover:opacity-90', async () => {
        const body = textarea.value.trim();
        if (!body) return;
        await postComment(section.id, body);
        textarea.value = '';
        await loadDraft();
      });
      composer.appendChild(label);
      composer.appendChild(textarea);
      composer.appendChild(submit);
      card.appendChild(threadContainer);
      card.appendChild(composer);
      sectionsEl.appendChild(card);
    });
  }

  function renderThread(thread) {
    const tpl = document.getElementById('comment-thread-template');
    const clone = tpl.content.firstElementChild.cloneNode(true);
    const meta = clone.querySelector('[data-thread-meta]');
    const commentsWrap = clone.querySelector('[data-thread-comments]');
    meta.textContent = `Thread ${thread.thread_id.slice(0, 6)} • ${thread.paragraph_id || 'General'}`;
    (thread.comments || []).forEach((comment) => {
      const block = document.createElement('div');
      block.className = 'bg-white rounded-lg border border-slate-200 px-3 py-2 text-sm';
      const mentions = (comment.mentions || []).length ? ` • Mentions: ${(comment.mentions || []).join(', ')}` : '';
      block.innerHTML = `
        <div class="flex items-center justify-between text-xs text-slate-500 mb-1">
          <span>${comment.author_user_id || 'You'}</span>
          <span>${formatDate(comment.created_at || '')}</span>
        </div>
        <p class="text-slate-800">${comment.body}</p>
        <p class="text-xs text-slate-500">${mentions}</p>
      `;
      commentsWrap.appendChild(block);
    });
    return clone;
  }

  function renderRevisions(revisions) {
    if (!revisionList) return;
    revisionList.innerHTML = '';
    if (revisionCount) revisionCount.textContent = `${revisions.length} items`;
    if (!revisions.length) {
      revisionList.innerHTML = '<p class="text-sm text-slate-500">No revisions yet.</p>';
      return;
    }
    revisions.forEach((rev) => {
      const item = document.createElement('div');
      item.className = 'border border-slate-200 rounded-xl p-3 bg-slate-50';
      const detail = rev.details || {};
      const statusText = detail.to ? `${detail.from || 'draft'} → ${detail.to}` : '';
      const meta = document.createElement('div');
      meta.className = 'text-xs text-slate-500 flex items-center justify-between';

      const dateSpan = document.createElement('span');
      dateSpan.textContent = formatDateTime(rev.created_at);
      const authorSpan = document.createElement('span');
      authorSpan.textContent = rev.author_user_id || 'System';

      meta.appendChild(dateSpan);
      meta.appendChild(authorSpan);

      const title = document.createElement('p');
      title.className = 'font-semibold text-slate-900 mt-1';
      title.textContent = rev.summary || 'Update';

      const status = document.createElement('p');
      status.className = 'text-sm text-slate-600';
      status.textContent = statusText;

      item.appendChild(meta);
      item.appendChild(title);
      item.appendChild(status);
      revisionList.appendChild(item);
    });
  }

  function buildThreadMap(threads) {
    const map = new Map();
    (threads || []).forEach((thread) => {
      const key = thread.paragraph_id || 'general';
      if (!map.has(key)) map.set(key, []);
      map.get(key).push(thread);
    });
    return map;
  }

  async function postComment(paragraphId, body) {
    const mentions = extractMentions(body);
    const res = await fetch(`/api/team/drafts/${draftId}/comment`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ paragraph_id: paragraphId, body, mentions }),
    });
    if (!res.ok) throw new Error('Unable to post comment');
    return res.json();
  }

  function extractMentions(text) {
    if (!text) return [];
    const matches = text.match(/@([\w._-]+)/g) || [];
    return matches.map((m) => m.replace('@', ''));
  }

  function formatDate(value) {
    if (!value) return '—';
    try {
      const d = new Date(value);
      return d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    } catch (err) {
      return value;
    }
  }

  function formatDateTime(value) {
    if (!value) return '—';
    try {
      const d = new Date(value);
      return d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' });
    } catch (err) {
      return value;
    }
  }

  loadDraft();
})();
