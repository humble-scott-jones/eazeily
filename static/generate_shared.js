(function(global){
  const SAFE_STATES = new Set(['idle', 'running', 'success', 'error']);

  function createAsyncStateMachine(root, { initialState = 'idle', onChange } = {}) {
    let current = SAFE_STATES.has(initialState) ? initialState : 'idle';
    const listeners = new Set();
    if (typeof onChange === 'function') listeners.add(onChange);

    const notify = (state, meta = {}) => {
      if (root && root.dataset) {
        root.dataset.asyncState = state;
      }
      listeners.forEach(fn => {
        try { fn(state, meta); } catch (err) { console.error('async-state listener failed', err); }
      });
    };

    const setState = (next, meta = {}) => {
      if (!SAFE_STATES.has(next)) return current;
      current = next;
      notify(current, meta);
      return current;
    };

    notify(current, {});

    return {
      get state() { return current; },
      onChange(fn){ if (typeof fn === 'function') listeners.add(fn); },
      setIdle(meta){ return setState('idle', meta); },
      setRunning(meta){ return setState('running', meta); },
      setSuccess(meta){ return setState('success', meta); },
      setError(meta){ return setState('error', meta); }
    };
  }

  function attachLoadingOverlay(root, { id, defaultMessage = 'Working on it…' } = {}) {
    const overlay = id ? document.getElementById(id) : null;
    if (!overlay) {
      return {
        show(){},
        hide(){},
        setMessage(){},
      };
    }
    const messageEl = overlay.querySelector('[data-loading-copy]');
    overlay.classList.add('hidden');
    overlay.setAttribute('aria-live', 'polite');
    overlay.setAttribute('role', 'status');

    const setMessage = (copy = defaultMessage) => {
      if (messageEl) messageEl.textContent = copy;
    };

    const show = (copy = defaultMessage) => {
      setMessage(copy);
      overlay.classList.remove('hidden');
    };

    const hide = () => {
      overlay.classList.add('hidden');
    };

    hide();
    return { show, hide, setMessage };
  }

  function formatDebugInfo({ requestId, endpoint, payloadSummary, timestamp }) {
    const lines = [
      `Request ID: ${requestId || 'unknown'}`,
      `Endpoint: ${endpoint || 'n/a'}`,
      `Timestamp: ${timestamp || new Date().toISOString()}`,
      `Payload: ${payloadSummary || 'no payload recorded'}`
    ];
    return lines.join('\n');
  }

  function attachErrorBanner(root, {
    id,
    onRetry,
    onCopy,
    defaultTitle = 'We hit a snag',
  } = {}) {
    const banner = id ? document.getElementById(id) : null;
    if (!banner) {
      return {
        hide(){},
        show(){},
        setMessage(){},
      };
    }
    const titleEl = banner.querySelector('[data-error-title]');
    const messageEl = banner.querySelector('[data-error-message]');
    const copyBtn = banner.querySelector('[data-error-copy]');
    const retryBtn = banner.querySelector('[data-error-retry]');

    let currentDebugText = '';

    const hide = () => {
      banner.classList.add('hidden');
      banner.setAttribute('aria-hidden', 'true');
    };

    const show = (message, meta = {}) => {
      if (titleEl) titleEl.textContent = defaultTitle;
      if (messageEl) messageEl.textContent = message || 'Something went wrong. Please try again.';
      banner.classList.remove('hidden');
      banner.setAttribute('aria-hidden', 'false');
      currentDebugText = formatDebugInfo(meta);
      requestAnimationFrame(() => {
        if (retryBtn) retryBtn.focus({ preventScroll: true });
        else if (copyBtn) copyBtn.focus({ preventScroll: true });
      });
    };

    // Set up event handlers once during initialization
    if (copyBtn) {
      copyBtn.addEventListener('click', async () => {
        try {
          await navigator.clipboard.writeText(currentDebugText);
          renderToast('Debug info copied');
          if (typeof onCopy === 'function') onCopy();
        } catch (err) {
          renderToast('Clipboard unavailable — please try manually.');
        }
      });
    }
    if (retryBtn) {
      retryBtn.addEventListener('click', () => {
        if (typeof onRetry === 'function') onRetry();
      });
    }

    hide();
    return { hide, show };
  }

  function renderToast(message, { duration = 2800 } = {}) {
    const toast = document.createElement('div');
    toast.className = 'fixed bottom-6 right-6 bg-slate-800 text-white px-4 py-2 rounded shadow z-50 transition-opacity focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500';
    toast.tabIndex = 0;
    toast.setAttribute('role', 'status');
    toast.setAttribute('aria-live', 'polite');
    toast.textContent = message;
    document.body.appendChild(toast);
    setTimeout(() => toast.classList.add('opacity-0'), duration - 600);
    setTimeout(() => toast.remove(), duration);
    return toast;
  }

  global.AsyncUi = {
    createAsyncStateMachine,
    attachLoadingOverlay,
    attachErrorBanner,
    formatDebugInfo,
    renderToast,
  };
  global.renderToast = renderToast;
})(window);
