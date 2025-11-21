(function () {
  const statusMap = {
    draft: { label: 'Draft', classes: 'bg-slate-100 text-slate-700' },
    in_review: { label: 'In Review', classes: 'bg-amber-100 text-amber-800' },
    approved: { label: 'Approved', classes: 'bg-emerald-100 text-emerald-700' },
    scheduled: { label: 'Scheduled', classes: 'bg-blue-100 text-blue-700' },
  };

  const gridEl = document.getElementById('planner-grid');
  const summaryEl = document.getElementById('planner-summary');
  const filters = {
    campaign: document.getElementById('filter-campaign'),
    assignee: document.getElementById('filter-assignee'),
    status: document.getElementById('filter-status'),
  };

  async function fetchDrafts() {
    const params = new URLSearchParams();
    if (filters.campaign && filters.campaign.value) params.set('campaign', filters.campaign.value);
    if (filters.assignee && filters.assignee.value) params.set('assignee', filters.assignee.value);
    if (filters.status && filters.status.value) params.set('status', filters.status.value);
    const url = `${(window.PLANNER_VIEW && window.PLANNER_VIEW.fetchUrl) || '/api/team/drafts'}?${params.toString()}`;
    try {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load planner data');
      const data = await res.json();
      renderFilters(data.filters || {});
      renderPlanner(data.drafts || []);
    } catch (err) {
      console.error(err);
      if (gridEl) gridEl.innerHTML = `<div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">${err.message}</div>`;
    }
  }

  function renderFilters(filtersData) {
    populateSelect(filters.campaign, filtersData.campaigns || [], 'All campaigns');
    populateSelect(filters.assignee, filtersData.assignees || [], 'All teammates');
    if (filters.status && !filters.status.value && Array.isArray(filtersData.statuses)) {
      const desired = ['draft', 'in_review', 'approved', 'scheduled'];
      filtersData.statuses.forEach((s) => {
        if (!desired.includes(s)) desired.push(s);
      });
    }
  }

  function populateSelect(select, values, placeholder) {
    if (!select || !Array.isArray(values)) return;
    const current = select.value;
    select.innerHTML = '';
    const defaultOpt = document.createElement('option');
    defaultOpt.value = '';
    defaultOpt.textContent = placeholder || 'All';
    select.appendChild(defaultOpt);
    values.forEach((val) => {
      if (!val) return;
      const opt = document.createElement('option');
      opt.value = val;
      opt.textContent = val;
      select.appendChild(opt);
    });
    select.value = current;
  }

  function renderPlanner(drafts) {
    renderSummary(drafts);
    renderBuckets(drafts);
  }

  function renderSummary(drafts) {
    if (!summaryEl) return;
    const counts = drafts.reduce(
      (acc, draft) => {
        const status = (draft.status || 'draft').toLowerCase();
        acc.total += 1;
        acc[status] = (acc[status] || 0) + 1;
        return acc;
      },
      { total: 0 }
    );
    const cards = [
      { label: 'Total items', count: counts.total || 0, accent: 'bg-slate-100 text-slate-800 border-slate-200' },
      { label: 'Draft', count: counts.draft || 0, accent: 'bg-slate-100 text-slate-700 border-slate-200' },
      { label: 'In Review', count: counts.in_review || 0, accent: 'bg-amber-50 text-amber-800 border-amber-200' },
      { label: 'Approved/Scheduled', count: (counts.approved || 0) + (counts.scheduled || 0), accent: 'bg-emerald-50 text-emerald-800 border-emerald-200' },
    ];
    // Clear previous content
    summaryEl.innerHTML = '';
    cards.forEach((card) => {
      const cardDiv = document.createElement('div');
      cardDiv.className = `border ${card.accent} rounded-2xl p-4 shadow-sm`;

      const labelP = document.createElement('p');
      labelP.className = 'text-xs uppercase tracking-[0.2em]';
      labelP.textContent = card.label;

      const countP = document.createElement('p');
      countP.className = 'text-3xl font-bold mt-1';
      countP.textContent = card.count;

      cardDiv.appendChild(labelP);
      cardDiv.appendChild(countP);
      summaryEl.appendChild(cardDiv);
    });
  }

  function renderBuckets(drafts) {
    if (!gridEl) return;
    if (!drafts || !drafts.length) {
      gridEl.innerHTML = '<div class="text-slate-500 text-sm">No planner items match the selected filters.</div>';
      return;
    }

    const buckets = {
      this_week: { label: 'This week', items: [] },
      next_week: { label: 'Next week', items: [] },
      later: { label: 'Later', items: [] },
      unscheduled: { label: 'Unscheduled', items: [] },
    };

    drafts.forEach((draft) => {
      const bucketKey = bucketForDraft(draft);
      buckets[bucketKey].items.push(draft);
    });

    Object.values(buckets).forEach((bucket) => {
      bucket.items.sort((a, b) => new Date(a.due_date || a.created_at) - new Date(b.due_date || b.created_at));
    });

    gridEl.innerHTML = '';
    Object.entries(buckets).forEach(([key, bucket]) => {
      const container = document.createElement('div');
      container.className = 'bg-white border border-slate-200 rounded-2xl shadow-sm flex flex-col';
      container.innerHTML = `
        <div class="border-b border-slate-100 px-5 py-3 flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">${bucket.label}</p>
            <h2 class="text-lg font-semibold text-slate-900">${bucket.items.length} item${bucket.items.length === 1 ? '' : 's'}</h2>
          </div>
          ${dueRangeLabel(key)}
        </div>
      `;

      const list = document.createElement('div');
      list.className = 'divide-y divide-slate-100';
      if (!bucket.items.length) {
        list.innerHTML = '<div class="text-sm text-slate-500 px-5 py-4">No drafts in this window.</div>';
      } else {
        bucket.items.forEach((draft) => list.appendChild(renderCard(draft)));
      }

      container.appendChild(list);
      gridEl.appendChild(container);
    });
  }

  function dueRangeLabel(key) {
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    const nextWeekEnd = new Date(endOfWeek);
    nextWeekEnd.setDate(endOfWeek.getDate() + 7);

    if (key === 'this_week') {
      return `<span class="text-xs text-slate-500">Due by ${formatDate(endOfWeek.toISOString())}</span>`;
    }
    if (key === 'next_week') {
      return `<span class="text-xs text-slate-500">${formatDate(endOfWeek.toISOString())} → ${formatDate(nextWeekEnd.toISOString())}</span>`;
    }
    if (key === 'later') {
      return '<span class="text-xs text-slate-500">2+ weeks out</span>';
    }
    return '<span class="text-xs text-slate-500">No due date</span>';
  }

  function bucketForDraft(draft) {
    if (!draft.due_date) return 'unscheduled';
    const due = new Date(draft.due_date);
    const now = new Date();
    const startOfWeek = new Date(now);
    startOfWeek.setDate(now.getDate() - now.getDay());
    const endOfWeek = new Date(startOfWeek);
    endOfWeek.setDate(startOfWeek.getDate() + 6);
    const nextWeekEnd = new Date(endOfWeek);
    nextWeekEnd.setDate(endOfWeek.getDate() + 7);

    if (due <= endOfWeek) return 'this_week';
    if (due <= nextWeekEnd) return 'next_week';
    return 'later';
  }

  function renderCard(draft) {
    const status = statusMap[(draft.status || '').toLowerCase()] || statusMap.draft;
    const card = document.createElement('button');
    card.className = 'w-full text-left px-5 py-4 hover:bg-slate-50 transition flex items-start gap-4';
    card.addEventListener('click', () => {
      window.location.href = `/drafts/${draft.id}`;
    });

    const dueDate = draft.due_date ? formatDate(draft.due_date) : 'No due date';
    card.innerHTML = `
      <div class="flex-1 space-y-1">
        <div class="flex items-center gap-3 flex-wrap">
          <p class="font-semibold text-slate-900">${draft.title || 'Untitled draft'}</p>
          <span class="px-2 py-1 rounded-full text-xs font-medium ${status.classes}">${status.label}</span>
        </div>
        <p class="text-sm text-slate-600">Campaign: ${draft.campaign || 'Uncategorized'} • Assignee: ${draft.assignee_email || 'Unassigned'}</p>
        <p class="text-xs text-slate-500">${draft.comment_count || 0} comment${draft.comment_count === 1 ? '' : 's'} • Due ${dueDate}</p>
      </div>
      <div class="text-right text-sm text-slate-500">
        <p>${formatDate(draft.updated_at || draft.created_at)}</p>
        <p class="text-xs">Updated</p>
      </div>
    `;
    return card;
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

  Object.values(filters).forEach((select) => {
    if (!select) return;
    select.addEventListener('change', fetchDrafts);
  });

  fetchDrafts();
})();
