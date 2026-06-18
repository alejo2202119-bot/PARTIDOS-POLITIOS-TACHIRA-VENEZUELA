/* ============================================================================
   VPID — Application bootstrap: routing, shell wiring, search, alerts, login,
   and the client-side PDF (print-to-PDF) report generator.
   ============================================================================ */
(function () {
  const view = document.getElementById('view');

  /* ─────────────────────────── Sidebar nav ────────────────────────────── */
  function buildNav() {
    const nav = document.getElementById('nav');
    nav.innerHTML = VPID.nav.map(group => `
      <div>
        <div class="nav-group-label">${group.group}</div>
        <div class="space-y-0.5">
          ${group.items.map(i => `<a class="nav-link" data-view="${i.view}" href="#${i.view}">
            <i data-lucide="${i.icon}"></i><span>${i.label}</span></a>`).join('')}
        </div>
      </div>`).join('');
    VPID.ui.icons();
  }

  /* ─────────────────────────── Router ─────────────────────────────────── */
  async function route() {
    const hash = (location.hash || '#dashboard').slice(1);
    const v = VPID.views[hash] ? hash : 'dashboard';

    // Cleanup previous view's charts/maps to avoid leaks
    VPID.charts.disposeAll();
    VPID.maps.dispose();

    document.querySelectorAll('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.view === v));
    document.getElementById('view-title').textContent = VPID.viewTitles[v] || 'VPID';
    document.title = `${VPID.viewTitles[v] || 'Dashboard'} · VPID`;

    closeSidebar();
    try {
      await VPID.views[v](view);
      view.classList.add('fade-in');
      setTimeout(() => view.classList.remove('fade-in'), 400);
    } catch (err) {
      console.error(err);
      view.innerHTML = `<div class="card"><div class="card-b text-center py-12">
        <i data-lucide="alert-triangle" class="h-8 w-8 mx-auto text-amber-400"></i>
        <p class="mt-2 font-semibold">No se pudo cargar el módulo</p>
        <p class="text-sm text-muted">${err.message}</p></div></div>`;
      VPID.ui.icons();
    }
  }

  /* ─────────────────────────── Mobile sidebar ─────────────────────────── */
  const sidebar = document.getElementById('sidebar');
  const backdrop = document.getElementById('sidebar-backdrop');
  function openSidebar() { sidebar.classList.add('open'); backdrop.classList.remove('hidden'); }
  function closeSidebar() { sidebar.classList.remove('open'); backdrop.classList.add('hidden'); }
  document.getElementById('menu-toggle').addEventListener('click', openSidebar);
  backdrop.addEventListener('click', closeSidebar);

  /* ─────────────────────────── Theme ─────────────────────────────────── */
  document.getElementById('theme-toggle').addEventListener('click', () => VPID.theme.toggle());
  // Re-render current view on theme change so charts pick up new colors
  let themeTimer;
  window.addEventListener('vpid:theme', () => { clearTimeout(themeTimer); themeTimer = setTimeout(route, 60); });

  /* ─────────────────────────── User menu ─────────────────────────────── */
  const userMenu = document.getElementById('user-menu');
  document.getElementById('user-btn').addEventListener('click', (e) => { e.stopPropagation(); userMenu.classList.toggle('hidden'); });
  document.addEventListener('click', () => userMenu.classList.add('hidden'));
  document.getElementById('logout-btn').addEventListener('click', doLogout);

  /* ─────────────────────────── Global search ─────────────────────────── */
  const search = document.getElementById('global-search');
  const results = document.getElementById('search-results');
  let searchTimer;
  search.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = search.value.trim();
    if (q.length < 2) { results.classList.add('hidden'); return; }
    searchTimer = setTimeout(async () => {
      const items = await VPID.api.buscar(q);
      results.innerHTML = items.length
        ? items.map(r => `<div class="search-item" data-view="${r.view}">
            <i data-lucide="${r.icon}" class="h-4 w-4 text-muted"></i>
            <div class="flex-1 min-w-0"><div class="truncate">${r.label}</div><div class="text-[11px] text-muted">${r.sub}</div></div>
            <span class="badge badge-neu">${r.tipo}</span></div>`).join('')
        : '<div class="search-item text-muted">Sin resultados</div>';
      results.classList.remove('hidden');
      VPID.ui.icons();
      results.querySelectorAll('[data-view]').forEach(el => el.addEventListener('click', () => {
        location.hash = '#' + el.dataset.view; results.classList.add('hidden'); search.value = '';
      }));
    }, 180);
  });
  document.addEventListener('click', (e) => { if (!e.target.closest('.search-wrap')) results.classList.add('hidden'); });
  document.addEventListener('keydown', (e) => {
    if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') { e.preventDefault(); search.focus(); }
    if (e.key === 'Escape') { results.classList.add('hidden'); closeDrawer(); }
  });

  /* ─────────────────────────── Alerts drawer ─────────────────────────── */
  const drawer = document.getElementById('alerts-drawer');
  async function openDrawer() {
    const { items } = await VPID.api.alertas();
    document.getElementById('alerts-drawer-body').innerHTML = items.map(a => `
      <div class="rounded-lg p-3 border border-[var(--border)] bg-[var(--surface-2)]">
        <div class="flex items-center justify-between mb-1">${VPID.C.badgeSev(a.severidad)}<span class="text-[11px] text-muted">${VPID.fmt.ago(a.created_at)}</span></div>
        <div class="text-sm font-semibold">${a.titulo}</div>
        <div class="text-xs text-muted mt-0.5">${a.descripcion}</div></div>`).join('');
    drawer.classList.remove('hidden');
  }
  function closeDrawer() { drawer.classList.add('hidden'); }
  document.getElementById('alerts-btn').addEventListener('click', openDrawer);
  drawer.querySelector('.drawer-backdrop').addEventListener('click', closeDrawer);
  drawer.querySelectorAll('[data-close-drawer]').forEach(b => b.addEventListener('click', closeDrawer));

  async function refreshAlertBadge() {
    const { items } = await VPID.api.alertas();
    const open = items.filter(a => a.estado === 'abierta').length;
    const badge = document.getElementById('alerts-badge');
    badge.textContent = open; badge.style.display = open ? 'grid' : 'none';
  }

  /* ─────────────────────────── data-go navigation ─────────────────────── */
  document.addEventListener('click', (e) => {
    const go = e.target.closest('[data-go]');
    if (go) location.hash = '#' + go.dataset.go;
    if (e.target.closest('#btn-refresh')) route();
  });

  /* ─────────────────────────── Connection mode badge ──────────────────── */
  VPID.api.onModeChange((m) => {
    const dot = document.querySelector('.status-dot--live');
    const cfg = document.getElementById('cfg-mode');
    if (cfg) cfg.textContent = m;
    if (m === 'demo') VPID.ui.toast('Modo demostración: usando datos de muestra (sin backend).', 'warn');
  });

  /* ─────────────────────────── Login ─────────────────────────────────── */
  const overlay = document.getElementById('login-overlay');
  const app = document.getElementById('app');
  function showApp() { overlay.classList.add('hidden'); overlay.classList.remove('flex'); app.classList.remove('hidden'); }
  function showLogin() { overlay.classList.remove('hidden'); overlay.classList.add('flex'); app.classList.add('hidden'); }
  function doLogout() { VPID.api.logout(); showLogin(); }

  document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('login-email').value;
    const pass = document.getElementById('login-password').value;
    try {
      await VPID.api.login(email, pass);
      showApp();
      boot();
      VPID.ui.toast('Sesión iniciada · bienvenido', 'ok');
    } catch (err) {
      const el = document.getElementById('login-error');
      el.textContent = 'No se pudo iniciar sesión.'; el.classList.remove('hidden');
    }
  });

  /* ─────────────────────────── Client-side PDF report ─────────────────── */
  VPID.report = {
    async printable() {
      const [k, ov] = await Promise.all([VPID.api.kpis(), VPID.api.overview()]);
      const now = new Date();
      const fecha = now.toLocaleDateString('es-VE', { weekday: 'long', day: '2-digit', month: 'long', year: 'numeric' });
      const w = window.open('', '_blank');
      if (!w) { VPID.ui.toast('Permita las ventanas emergentes para generar el PDF.', 'warn'); return; }
      const row = (a) => `<tr><td>${a.nombre}</td><td>${a.cargo || ''}</td><td style="text-align:right">${VPID.fmt.num(a.menciones)}</td><td style="text-align:right">${VPID.fmt.score(a.sentimiento_prom)}</td></tr>`;
      w.document.write(`<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Informe Ejecutivo VPID — ${fecha}</title>
        <style>
          @page { size: A4; margin: 18mm 16mm; }
          body { font-family: 'Segoe UI', Arial, sans-serif; color:#0f172a; }
          .cover { background:linear-gradient(135deg,#0b1220,#1e1b4b); color:#fff; padding:48px; border-radius:14px; margin-bottom:28px; }
          .cover h1 { font-size:30px; margin:18px 0 6px; }
          .badge { display:inline-block; background:#6366f1; color:#fff; padding:4px 10px; border-radius:99px; font-size:11px; letter-spacing:.08em; text-transform:uppercase; }
          h2 { font-size:16px; border-bottom:2px solid #e2e8f0; padding-bottom:6px; margin-top:26px; color:#4338ca; }
          .kpis { display:flex; flex-wrap:wrap; gap:12px; }
          .kpi { flex:1; min-width:150px; border:1px solid #e2e8f0; border-radius:10px; padding:14px; }
          .kpi .l { font-size:11px; color:#64748b; text-transform:uppercase; letter-spacing:.05em; }
          .kpi .v { font-size:24px; font-weight:800; margin-top:4px; }
          table { width:100%; border-collapse:collapse; font-size:12px; margin-top:8px; }
          th,td { padding:7px 8px; border-bottom:1px solid #e2e8f0; text-align:left; }
          th { background:#f8fafc; font-size:10px; text-transform:uppercase; color:#64748b; }
          .muted { color:#64748b; font-size:11px; }
          ul { font-size:12px; line-height:1.7; }
          .foot { margin-top:30px; border-top:1px solid #e2e8f0; padding-top:10px; font-size:10px; color:#94a3b8; }
        </style></head><body>
        <div class="cover">
          <span class="badge">Venezuela Political Intelligence</span>
          <h1>Informe Ejecutivo Diario</h1>
          <div style="opacity:.85">Monitoreo y análisis de información pública (OSINT)</div>
          <div style="margin-top:18px;font-size:13px;opacity:.9">Generado: ${fecha} · ${now.toLocaleTimeString('es-VE')}</div>
        </div>

        <h2>Resumen Ejecutivo</h2>
        <p style="font-size:12.5px;line-height:1.7">Durante el período analizado se procesaron <b>${VPID.fmt.num(k.total_articulos)}</b> artículos de
        <b>${VPID.fmt.num(k.fuentes_activas)}</b> fuentes públicas activas, con <b>${VPID.fmt.num(k.total_menciones)}</b> menciones a actores y organizaciones.
        El sentimiento global se ubicó en <b>${VPID.fmt.score(k.sentimiento_global)}</b> y el alcance estimado acumulado alcanzó <b>${VPID.fmt.compact(k.alcance_total)}</b>.
        Se identificaron <b>${k.narrativas_activas}</b> narrativas activas (${k.narrativas_emergentes} emergentes) y <b>${k.alertas_abiertas}</b> alertas abiertas.</p>

        <h2>Indicadores Clave</h2>
        <div class="kpis">
          <div class="kpi"><div class="l">Artículos</div><div class="v">${VPID.fmt.num(k.total_articulos)}</div></div>
          <div class="kpi"><div class="l">Menciones</div><div class="v">${VPID.fmt.num(k.total_menciones)}</div></div>
          <div class="kpi"><div class="l">Alcance</div><div class="v">${VPID.fmt.compact(k.alcance_total)}</div></div>
          <div class="kpi"><div class="l">Sentimiento</div><div class="v">${VPID.fmt.score(k.sentimiento_global)}</div></div>
          <div class="kpi"><div class="l">Alertas</div><div class="v">${VPID.fmt.num(k.alertas_abiertas)}</div></div>
        </div>

        <h2>Actores Más Mencionados</h2>
        <table><thead><tr><th>Actor</th><th>Cargo</th><th style="text-align:right">Menciones</th><th style="text-align:right">Sentimiento</th></tr></thead>
          <tbody>${ov.actores.map(row).join('')}</tbody></table>

        <h2>Narrativas Predominantes</h2>
        <ul>${ov.narrativas.map(n => `<li><b>${n.titulo}</b> — ${VPID.fmt.num(n.total_articulos)} artículos${n.emergente ? ' · <span style="color:#6366f1">emergente</span>' : ''}</li>`).join('')}</ul>

        <h2>Alertas Relevantes</h2>
        <ul>${ov.alertas.map(a => `<li><b>[${a.severidad}]</b> ${a.titulo} — ${a.descripcion}</li>`).join('')}</ul>

        <h2>Conclusiones y Recomendaciones (generadas automáticamente)</h2>
        <ul>
          <li>La conversación pública mantiene foco en procesos electorales y unidad política; conviene monitorear su evolución.</li>
          <li>El sentimiento predominante sugiere atención a temas de servicios públicos y economía en la región andina.</li>
          <li>Recomendación: priorizar verificación de narrativas emergentes y contrastar fuentes de distinta credibilidad.</li>
          <li>Análisis basado <b>exclusivamente en información pública</b>; las cifras de demostración son sintéticas.</li>
        </ul>

        <div class="foot">Documento generado por Venezuela Political Intelligence Dashboard · Exportación únicamente en PDF ·
        Uso responsable de fuentes abiertas. Esta herramienta no debe emplearse para vigilancia de personas privadas.</div>
        <script>window.onload=()=>{setTimeout(()=>window.print(),350)}<\/script>
        </body></html>`);
      w.document.close();
      VPID.ui.toast('Informe PDF generado — use «Guardar como PDF».', 'ok');
    },
  };

  /* ─────────────────────────── Boot ──────────────────────────────────── */
  function boot() {
    buildNav();
    refreshAlertBadge();
    if (!location.hash) location.hash = '#dashboard';
    route();
  }
  window.addEventListener('hashchange', route);

  // Initialize icons on the login screen, then decide auth state.
  document.addEventListener('DOMContentLoaded', () => {
    VPID.ui.icons();
    if (VPID.api.isAuthed()) { showApp(); boot(); }
    else { showLogin(); }
  });
  // Fallback if DOMContentLoaded already fired
  if (document.readyState !== 'loading') {
    VPID.ui.icons();
    if (VPID.api.isAuthed()) { showApp(); boot(); } else { showLogin(); }
  }
})();
