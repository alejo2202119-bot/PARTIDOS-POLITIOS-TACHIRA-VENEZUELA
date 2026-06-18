/* ============================================================================
   VPID — API client
   Tries the FastAPI backend (/api/v1). If unreachable or unauthenticated,
   transparently falls back to the bundled demo dataset (mock.js) so the
   dashboard is always functional. Tracks connection mode for the UI badge.
   ============================================================================ */
VPID.api = (function () {
  const base = VPID.config.apiBase;
  let mode = 'desconocido'; // 'live' | 'demo'
  let token = localStorage.getItem('vpid_token') || null;

  const listeners = [];
  function setMode(m) { if (m !== mode) { mode = m; listeners.forEach(fn => fn(m)); } }

  async function http(path, opts = {}) {
    const ctrl = new AbortController();
    const t = setTimeout(() => ctrl.abort(), 4000);
    try {
      const res = await fetch(base + path, {
        ...opts,
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: 'Bearer ' + token } : {}),
          ...(opts.headers || {}),
        },
        signal: ctrl.signal,
      });
      clearTimeout(t);
      if (!res.ok) throw new Error('HTTP ' + res.status);
      setMode('live');
      return await res.json();
    } catch (err) {
      clearTimeout(t);
      setMode('demo');
      throw err;
    }
  }

  // Wrap a live call with a demo fallback producer.
  async function withFallback(path, fallbackFn, opts) {
    try { return await http(path, opts); }
    catch { return fallbackFn(); }
  }

  const M = () => VPID.mock;

  return {
    onModeChange: (fn) => listeners.push(fn),
    getMode: () => mode,
    isAuthed: () => !!token,

    async login(email, password) {
      try {
        const r = await http('/auth/login', { method: 'POST', body: JSON.stringify({ email, password }) });
        token = r.access_token; localStorage.setItem('vpid_token', token);
        return r;
      } catch {
        // Demo auth — accept any credentials
        token = 'demo-token'; localStorage.setItem('vpid_token', token);
        setMode('demo');
        return { access_token: token, user: { nombre: 'Administrador', email, rol: 'admin' } };
      }
    },
    logout() { token = null; localStorage.removeItem('vpid_token'); },

    // ── Read endpoints (live → demo fallback) ──────────────────────────────
    kpis:        () => withFallback('/dashboard/kpis', () => M().kpis),
    overview:    () => withFallback('/dashboard/overview', () => ({
      actores: M().actores.slice(0, 5), narrativas: M().narrativas.slice(0, 4),
      alertas: M().alertas.slice(0, 4), sentimiento: M().sentimiento.resumen,
    })),
    articulos:   (q = {}) => withFallback('/articulos?' + new URLSearchParams(q), () => {
      let items = [...M().articulos];
      if (q.q) items = items.filter(a => (a.titulo + a.actor + a.fuente).toLowerCase().includes(q.q.toLowerCase()));
      if (q.tema) items = items.filter(a => a.tema === q.tema);
      if (q.estado) items = items.filter(a => a.estado === q.estado);
      if (q.relevancia) items = items.filter(a => a.relevancia === q.relevancia);
      if (q.sentimiento) items = items.filter(a => a.sentimiento === q.sentimiento);
      return { items, total: items.length, page: 1, size: items.length };
    }),
    tendencias:  () => withFallback('/tendencias', () => M().tendencias),
    emergentes:  () => withFallback('/tendencias/emergentes', () => M().tendencias.emergentes),
    narrativas:  () => withFallback('/narrativas', () => ({ items: M().narrativas })),
    sentimiento: () => withFallback('/sentimiento/resumen', () => M().sentimiento),
    ranking:     () => withFallback('/actores/ranking', () => ({ items: M().actores })),
    territorial: () => withFallback('/territorial/resumen', () => ({ items: M().estados })),
    alertas:     () => withFallback('/alertas', () => ({ items: M().alertas })),
    fuentes:     () => withFallback('/fuentes', () => ({ items: M().fuentes })),
    reportes:    () => withFallback('/reportes', () => ({ items: M().reportes })),
    correlaciones: () => withFallback('/comparativos/correlaciones', () => ({ items: M().correlaciones })),

    buscar: async (q) => {
      const ql = q.toLowerCase();
      const r = [];
      M().actores.filter(a => a.nombre.toLowerCase().includes(ql)).slice(0, 4)
        .forEach(a => r.push({ tipo: 'Actor', icon: 'user', label: a.nombre, sub: a.cargo, view: 'actors' }));
      M().narrativas.filter(n => n.titulo.toLowerCase().includes(ql)).slice(0, 3)
        .forEach(n => r.push({ tipo: 'Narrativa', icon: 'git-branch', label: n.titulo, sub: 'Narrativa', view: 'narratives' }));
      M().fuentes.filter(f => f.nombre.toLowerCase().includes(ql)).slice(0, 3)
        .forEach(f => r.push({ tipo: 'Fuente', icon: 'database', label: f.nombre, sub: f.tipo, view: 'sources' }));
      M().temas.filter(t => t.nombre.toLowerCase().includes(ql)).slice(0, 3)
        .forEach(t => r.push({ tipo: 'Tema', icon: 'tag', label: t.nombre, sub: 'Tema', view: 'trends' }));
      return r;
    },

    // ── Report generation (PDF only) ───────────────────────────────────────
    async generarReporte(params) {
      try { return await http('/reportes/generar', { method: 'POST', body: JSON.stringify(params) }); }
      catch {
        return { id: 'demo', estado: 'completado', demo: true,
          titulo: 'Informe Ejecutivo Diario (demostración)' };
      }
    },
  };
})();
