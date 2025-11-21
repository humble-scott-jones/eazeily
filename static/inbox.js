(function () {
  const statusMap = {
    draft: { label: 'Draft', classes: 'bg-slate-100 text-slate-700' },
    in_review: { label: 'In Review', classes: 'bg-amber-100 text-amber-800' },
    approved: { label: 'Approved', classes: 'bg-emerald-100 text-emerald-700' },
    scheduled: { label: 'Scheduled', classes: 'bg-blue-100 text-blue-700' },
  };

  const listEl = document.getElementById('inbox-list');
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
    const url = `${(window.INBOX_VIEW && window.INBOX_VIEW.fetchUrl) || '/api/team/drafts'}?${params.toString()}`;
    try {
      const res = await fetch(url, { credentials: 'include' });
      if (!res.ok) throw new Error('Failed to load drafts');
      const data = await res.json();
      renderFilters(data.filters || {});
      renderDrafts(data.drafts || []);
    } catch (err) {
      console.error(err);
      if (listEl) listEl.innerHTML = `<div class="bg-red-50 border border-red-200 text-red-700 p-4 rounded-xl">${err.message}</div>`;
    }
  }

  function renderFilters(filtersData) {
    populateSelect(filters.campaign, filtersData.campaigns || [], 'All campaigns');
    populateSelect(filters.assignee, filtersData.assignees || [], 'All teammates');
    if (filters.status && !filters.status.value && Array.isArray(filtersData.statuses)) {
      // keep default options but highlight common flow order
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

  function renderDrafts(drafts) {
    if (!listEl) return;
    if (!drafts || !drafts.length) {
      listEl.innerHTML = '<div class="text-slate-500 text-sm">No drafts match the selected filters.</div>';
      return;
    }
    const grouped = drafts.reduce((acc, draft) => {
      const key = draft.campaign || 'Uncategorized';
      acc[key] = acc[key] || [];
      acc[key].push(draft);
      return acc;
    }, {});
    listEl.innerHTML = '';
    Object.entries(grouped).forEach(([campaign, items]) => {
      const wrapper = document.createElement('div');
      wrapper.className = 'bg-white border border-slate-200 rounded-2xl shadow-sm';
      wrapper.innerHTML = `
        <div class="border-b border-slate-100 px-5 py-3 flex items-center justify-between">
          <div>
            <p class="text-xs uppercase tracking-[0.2em] text-slate-500">Campaign</p>
            <h2 class="text-lg font-semibold text-slate-900">${campaign}</h2>
          </div>
          <span class="text-sm text-slate-500">${items.length} draft${items.length === 1 ? '' : 's'}</span>
        </div>
      `;
      const list = document.createElement('div');
      list.className = 'divide-y divide-slate-100';
      items.forEach((draft) => {
        const status = statusMap[(draft.status || '').toLowerCase()] || statusMap.draft;
        const row = document.createElement('button');
        row.className = 'w-full flex items-start gap-4 px-5 py-4 hover:bg-slate-50 text-left transition';
        row.addEventListener('click', () => {
          window.location.href = `/drafts/${draft.id}`;
        });
        const dueDate = draft.due_date ? formatDate(draft.due_date) : 'No due date';
        row.innerHTML = `
          <div class="flex-1">
            <div class="flex items-center gap-3 flex-wrap">
              <p class="font-semibold text-slate-900">${draft.title || 'Untitled draft'}</p>
              <span class="px-2 py-1 rounded-full text-xs font-medium ${status.classes}">${status.label}</span>
            </div>
            <p class="text-sm text-slate-600 mt-1">Assignee: ${draft.assignee_email || 'Unassigned'} • Due ${dueDate}</p>
            <p class="text-xs text-slate-500 mt-1">${draft.comment_count || 0} comment${draft.comment_count === 1 ? '' : 's'}</p>
          </div>
          <div class="text-right text-sm text-slate-500">
            <p>${campaign}</p>
            <p class="text-xs">Updated ${formatDate(draft.updated_at || draft.created_at)}</p>
          </div>
        `;
        list.appendChild(row);
      });
      wrapper.appendChild(list);
      listEl.appendChild(wrapper);
    });
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
