/* ============================================================================
   VPID — Theme (dark/light) + shared UI utilities (toasts, icons)
   ============================================================================ */
VPID.theme = (function () {
  const KEY = 'vpid_theme';
  function current() { return localStorage.getItem(KEY) || 'dark'; }
  function apply(t) {
    document.documentElement.classList.toggle('dark', t === 'dark');
    localStorage.setItem(KEY, t);
    const icon = document.querySelector('#theme-toggle i');
    if (icon) { icon.setAttribute('data-lucide', t === 'dark' ? 'sun' : 'moon'); VPID.ui.icons(); }
    // Let charts re-theme
    window.dispatchEvent(new CustomEvent('vpid:theme', { detail: t }));
  }
  function toggle() { apply(current() === 'dark' ? 'light' : 'dark'); }
  return { current, apply, toggle, isDark: () => current() === 'dark' };
})();

VPID.ui = {
  icons() { if (window.lucide) window.lucide.createIcons(); },
  toast(msg, kind = 'info') {
    const colors = { info: 'info', ok: 'check-circle-2', warn: 'alert-triangle', error: 'x-circle' };
    const tint = { info: 'var(--accent)', ok: 'var(--pos)', warn: 'var(--warn)', error: 'var(--neg)' };
    const t = VPID.el('div', { class: 'toast' });
    t.innerHTML = `<i data-lucide="${colors[kind] || 'info'}" style="color:${tint[kind] || 'var(--accent)'};width:18px;height:18px"></i><span>${msg}</span>`;
    document.getElementById('toasts').appendChild(t);
    VPID.ui.icons();
    setTimeout(() => { t.style.opacity = '0'; t.style.transition = 'opacity .3s'; setTimeout(() => t.remove(), 300); }, 3200);
  },
  loading(container) {
    container.innerHTML = `<div class="grid-kpi">${'<div class="card"><div class="card-b"><div class="skeleton" style="height:80px"></div></div></div>'.repeat(4)}</div>
      <div class="card mt-4"><div class="card-b"><div class="skeleton" style="height:320px"></div></div></div>`;
  },
};

// Apply theme as early as possible
VPID.theme.apply(VPID.theme.current());
