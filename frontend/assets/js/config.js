/* ============================================================================
   VPID — Global configuration, navigation map & formatting helpers
   ============================================================================ */
window.VPID = window.VPID || {};

VPID.config = {
  // When a backend is reachable this base is used; otherwise the app falls back
  // to the bundled mock dataset (mock.js) so the dashboard is always demoable.
  apiBase: (location.hostname === 'localhost' || location.hostname === '127.0.0.1')
    ? '/api/v1'
    : '/api/v1',
  brand: 'Venezuela Political Intelligence',
  defaultRangeDays: 7,
  locale: 'es-VE',
  tz: 'America/Caracas',
};

/* Navigation — drives the sidebar and the hash router. Each `view` maps to a
   render function in views.js (VPID.views[view]). */
VPID.nav = [
  { group: 'Inteligencia', items: [
    { view: 'dashboard',    label: 'Dashboard Ejecutivo',     icon: 'layout-dashboard' },
    { view: 'news',         label: 'Monitoreo de Noticias',   icon: 'newspaper' },
    { view: 'intelligence', label: 'Centro de Inteligencia',  icon: 'radar' },
  ]},
  { group: 'Análisis', items: [
    { view: 'trends',     label: 'Análisis de Tendencias',  icon: 'trending-up' },
    { view: 'narratives', label: 'Detección de Narrativas', icon: 'git-branch' },
    { view: 'sentiment',  label: 'Análisis de Sentimiento', icon: 'gauge' },
    { view: 'actors',     label: 'Ranking de Actores',      icon: 'users' },
    { view: 'compare',    label: 'Comparativos Históricos', icon: 'bar-chart-3' },
  ]},
  { group: 'Territorio', items: [
    { view: 'territorial', label: 'Monitoreo Territorial', icon: 'map-pinned' },
    { view: 'maps',        label: 'Mapas Interactivos',    icon: 'map' },
  ]},
  { group: 'Operaciones', items: [
    { view: 'alerts',  label: 'Alertas Tempranas',  icon: 'bell-ring' },
    { view: 'reports', label: 'Informes Ejecutivos', icon: 'file-text' },
    { view: 'sources', label: 'Fuentes',             icon: 'database' },
  ]},
];

VPID.viewTitles = {};
VPID.nav.forEach(g => g.items.forEach(i => { VPID.viewTitles[i.view] = i.label; }));

/* Data-viz palette (kept in sync with CSS tokens) */
VPID.palette = {
  series: ['#6366f1', '#22d3ee', '#a855f7', '#f59e0b', '#34d399', '#fb7185', '#38bdf8', '#f472b6'],
  pos: '#34d399', neu: '#94a3b8', neg: '#fb7185',
  accent: '#818cf8', accent2: '#22d3ee',
};

/* ─────────────────────────── Formatters ──────────────────────────────── */
VPID.fmt = {
  num(n) {
    if (n === null || n === undefined) return '—';
    return new Intl.NumberFormat('es-VE').format(Math.round(n));
  },
  compact(n) {
    if (n === null || n === undefined) return '—';
    return new Intl.NumberFormat('es-VE', { notation: 'compact', maximumFractionDigits: 1 }).format(n);
  },
  pct(n, digits = 1) {
    if (n === null || n === undefined) return '—';
    const s = n > 0 ? '+' : '';
    return `${s}${n.toFixed(digits)}%`;
  },
  score(n) { return (n >= 0 ? '+' : '') + Number(n).toFixed(2); },
  date(d) {
    const dt = typeof d === 'string' ? new Date(d) : d;
    return new Intl.DateTimeFormat('es-VE', { day: '2-digit', month: 'short', year: 'numeric' }).format(dt);
  },
  datetime(d) {
    const dt = typeof d === 'string' ? new Date(d) : d;
    return new Intl.DateTimeFormat('es-VE', { day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).format(dt);
  },
  ago(d) {
    const dt = typeof d === 'string' ? new Date(d) : d;
    const s = (Date.now() - dt.getTime()) / 1000;
    if (s < 60) return 'hace instantes';
    if (s < 3600) return `hace ${Math.floor(s / 60)} min`;
    if (s < 86400) return `hace ${Math.floor(s / 3600)} h`;
    return `hace ${Math.floor(s / 86400)} d`;
  },
  sentimentLabel(score) {
    if (score > 0.15) return { label: 'Positivo', cls: 'badge-pos' };
    if (score < -0.15) return { label: 'Negativo', cls: 'badge-neg' };
    return { label: 'Neutral', cls: 'badge-neu' };
  },
};

/* Tiny DOM helper */
VPID.el = (tag, attrs = {}, html = '') => {
  const e = document.createElement(tag);
  Object.entries(attrs).forEach(([k, v]) => {
    if (k === 'class') e.className = v;
    else if (k === 'html') e.innerHTML = v;
    else e.setAttribute(k, v);
  });
  if (html) e.innerHTML = html;
  return e;
};
