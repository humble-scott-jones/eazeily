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
        const errorDiv = document.createElement('div');
        errorDiv.className = 'bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl';
        errorDiv.textContent = err.message;
        sectionsEl.innerHTML = '';
        sectionsEl.appendChild(errorDiv);
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
      // Build the card content using DOM APIs to avoid XSS
      const flexDiv = document.createElement('div');
      flexDiv.className = 'flex items-center justify-between';

      const leftDiv = document.createElement('div');

      const headingP = document.createElement('p');
      headingP.className = 'text-xs uppercase tracking-[0.3em] text-slate-500';
      headingP.textContent = section.heading || 'Section';

      const textH3 = document.createElement('h3');
      textH3.className = 'text-xl font-semibold text-slate-900';
      textH3.textContent = section.text || '';

      leftDiv.appendChild(headingP);
      leftDiv.appendChild(textH3);

      const idSpan = document.createElement('span');
      idSpan.className = 'text-xs text-slate-500';
      idSpan.textContent = `Paragraph ID: ${section.id}`;

      flexDiv.appendChild(leftDiv);
      flexDiv.appendChild(idSpan);

      card.appendChild(flexDiv);
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
    meta.textContent = `Thread ${(thread.thread_id || '').slice(0, 6)} • ${thread.paragraph_id || 'General'}`;
    (thread.comments || []).forEach((comment) => {
      const block = document.createElement('div');
      block.className = 'bg-white rounded-lg border border-slate-200 px-3 py-2 text-sm';

      // Header: author and date
      const header = document.createElement('div');
      header.className = 'flex items-center justify-between text-xs text-slate-500 mb-1';

      const authorSpan = document.createElement('span');
      authorSpan.textContent = comment.author_user_id || 'You';
      header.appendChild(authorSpan);

      const dateSpan = document.createElement('span');
      dateSpan.textContent = formatDate(comment.created_at || '');
      header.appendChild(dateSpan);

      // Body
      const bodyP = document.createElement('p');
      bodyP.className = 'text-slate-800';
      bodyP.textContent = comment.body;

      // Mentions
      const mentionsP = document.createElement('p');
      mentionsP.className = 'text-xs text-slate-500';
      if ((comment.mentions || []).length) {
        mentionsP.textContent = '• Mentions: ' + (comment.mentions || []).join(', ');
      } else {
        mentionsP.textContent = '';
      }

      block.appendChild(header);
      block.appendChild(bodyP);
      block.appendChild(mentionsP);
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
      item.innerHTML = `
        <div class="text-xs text-slate-500 flex items-center justify-between">
          <span>${formatDateTime(rev.created_at)}</span>
          <span>${rev.author_user_id || 'System'}</span>
        </div>
        <p class="font-semibold text-slate-900 mt-1">${rev.summary || 'Update'}</p>
        <p class="text-sm text-slate-600">${statusText}</p>
      `;
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
