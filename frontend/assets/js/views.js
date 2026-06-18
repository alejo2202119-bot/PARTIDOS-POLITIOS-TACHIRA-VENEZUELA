/* ============================================================================
   VPID — View renderers for the 12 modules.
   Each view: VPID.views[name](container) renders HTML, then wires charts/maps.
   ============================================================================ */
VPID.views = {};

/* ─────────────────────────── Shared UI builders ───────────────────────── */
const C = {
  header(title, sub, right = '') {
    return `<div class="flex flex-wrap items-end justify-between gap-3 mb-5">
      <div><h2 class="section-title">${title}</h2>${sub ? `<p class="section-sub mt-0.5">${sub}</p>` : ''}</div>
      <div class="flex items-center gap-2">${right}</div></div>`;
  },
  card(title, body, opts = {}) {
    const icon = opts.icon ? `<i data-lucide="${opts.icon}" class="h-4 w-4 text-muted"></i>` : '';
    const actions = opts.actions || '';
    const head = title ? `<div class="card-h"><h3>${icon}${title}</h3>${actions}</div>` : '';
    return `<div class="card ${opts.class || ''}">${head}<div class="card-b ${opts.bodyClass || ''}">${body}</div></div>`;
  },
  kpi(label, value, opts = {}) {
    const d = opts.delta;
    let pill = '';
    if (d !== undefined && d !== null) {
      const cls = d > 0 ? 'delta-up' : d < 0 ? 'delta-down' : 'delta-flat';
      const ic = d > 0 ? 'trending-up' : d < 0 ? 'trending-down' : 'minus';
      pill = `<span class="delta ${cls}"><i data-lucide="${ic}" style="width:12px;height:12px"></i>${VPID.fmt.pct(d)}</span>`;
    }
    return `<div class="card kpi"><div class="card-b">
      <div class="flex items-start justify-between">
        <div><div class="kpi-label">${label}</div>
          <div class="kpi-value mt-1">${value}</div>
          <div class="mt-1">${pill}</div></div>
        <div class="kpi-icon"><i data-lucide="${opts.icon || 'activity'}" style="width:18px;height:18px"></i></div>
      </div>
      ${opts.spark ? `<div class="kpi-spark" id="${opts.spark}"></div>` : ''}
    </div></div>`;
  },
  badgeSent(score) { const s = VPID.fmt.sentimentLabel(score); return `<span class="badge ${s.cls}">${s.label}</span>`; },
  badgeRelev(l) { return `<span class="badge badge-${l}">${l[0].toUpperCase() + l.slice(1)}</span>`; },
  badgeSev(l) { const m = { info: 'badge-info', baja: 'badge-baja', media: 'badge-media', alta: 'badge-alta', critica: 'badge-critica' }; return `<span class="badge ${m[l] || 'badge-neu'}">${l}</span>`; },
  orgPill(o) { return `<span class="mono text-xs px-1.5 py-0.5 rounded" style="background:var(--surface-2);color:var(--text-muted)">${o || '—'}</span>`; },
};
VPID.C = C;

/* ════════════════════════════ 1. DASHBOARD ════════════════════════════ */
VPID.views.dashboard = async function (c) {
  VPID.ui.loading(c);
  const [k, ov, tr] = await Promise.all([VPID.api.kpis(), VPID.api.overview(), VPID.api.tendencias()]);

  c.innerHTML = C.header('Dashboard Ejecutivo', 'Panorama consolidado de la información pública monitoreada · ' + VPID.fmt.date(new Date()),
    `<button class="btn" id="btn-refresh"><i data-lucide="refresh-cw" class="h-4 w-4"></i> Actualizar</button>
     <button class="btn btn-primary" data-go="reports"><i data-lucide="file-down" class="h-4 w-4"></i> Informe PDF</button>`) +
    `<div class="grid-kpi">
       ${C.kpi('Artículos (período)', VPID.fmt.num(k.total_articulos), { icon: 'newspaper', delta: k.deltas?.total_articulos, spark: 'sp1' })}
       ${C.kpi('Menciones', VPID.fmt.num(k.total_menciones), { icon: 'at-sign', delta: k.deltas?.total_menciones, spark: 'sp2' })}
       ${C.kpi('Alcance estimado', VPID.fmt.compact(k.alcance_total), { icon: 'radio', delta: k.deltas?.alcance_total, spark: 'sp3' })}
       ${C.kpi('Sentimiento global', VPID.fmt.score(k.sentimiento_global), { icon: 'gauge', delta: k.deltas?.sentimiento_global, spark: 'sp4' })}
       ${C.kpi('Alertas abiertas', VPID.fmt.num(k.alertas_abiertas), { icon: 'bell-ring' })}
     </div>
     <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
       <div class="lg:col-span-2">${C.card('Evolución de la cobertura', '<div id="ch-evo"></div>', { icon: 'line-chart', actions: '<span class="text-xs text-muted">por tema · período</span>' })}</div>
       <div>${C.card('Distribución de sentimiento', '<div id="ch-sent"></div>', { icon: 'pie-chart' })}</div>
     </div>
     <div class="grid grid-cols-1 lg:grid-cols-3 gap-4 mt-4">
       <div>${C.card('Actores más mencionados', '<div id="ch-actors"></div>', { icon: 'users' })}</div>
       <div>${C.card('Narrativas predominantes', narrList(ov.narrativas), { icon: 'git-branch' })}</div>
       <div>${C.card('Temas emergentes', emergeList(VPID.mock.tendencias.emergentes), { icon: 'flame' })}</div>
     </div>
     <div class="mt-4">${C.card('Alertas recientes', alertStrip(ov.alertas), { icon: 'bell-ring', actions: '<button class="btn btn-ghost text-xs" data-go="alerts">Ver todas →</button>' })}</div>`;

  VPID.ui.icons();
  // charts
  if (k.spark) {
    VPID.charts.spark(document.getElementById('sp1'), k.spark.total_articulos, VPID.palette.accent);
    VPID.charts.spark(document.getElementById('sp2'), k.spark.total_menciones, VPID.palette.accent2);
    VPID.charts.spark(document.getElementById('sp3'), k.spark.alcance_total, '#a855f7');
    VPID.charts.spark(document.getElementById('sp4'), k.spark.sentimiento_global.map(v => v * 100), '#34d399');
  }
  VPID.charts.area(document.getElementById('ch-evo'), tr.series.slice(0, 4).map(s => ({ name: s.name, data: s.data })),
    { colors: tr.series.slice(0, 4).map(s => s.color), height: 320 });
  const sr = ov.sentimiento;
  VPID.charts.donut(document.getElementById('ch-sent'), ['Positivo', 'Neutral', 'Negativo'], [sr.positivo, sr.neutral, sr.negativo]);
  const top = ov.actores.slice(0, 6);
  VPID.charts.barsH(document.getElementById('ch-actors'), top.map(a => a.nombre.split(' ').slice(0, 2).join(' ')), top.map(a => a.menciones), { name: 'Menciones', distributed: true, height: 300 });
};

function narrList(items) {
  return `<div class="space-y-3">${items.map(n => `
    <div class="flex items-start gap-3">
      <span class="mt-1 ${n.emergente ? 'tag-emergent' : ''} badge ${n.emergente ? '' : 'badge-neu'}">${n.emergente ? 'Emergente' : 'Activa'}</span>
      <div class="min-w-0 flex-1">
        <div class="text-sm font-medium truncate">${n.titulo}</div>
        <div class="text-xs text-muted">${VPID.fmt.num(n.total_articulos)} artículos · ${VPID.fmt.compact(n.alcance_estimado)} alcance</div>
      </div>
      ${C.badgeSent(n.sentimiento === 'negativo' ? -0.5 : n.sentimiento === 'positivo' ? 0.5 : 0)}
    </div>`).join('')}</div>`;
}
function emergeList(items) {
  return `<div class="space-y-3">${items.map(e => `
    <div class="flex items-center gap-3">
      <div class="flex-1 min-w-0"><div class="text-sm font-medium truncate">${e.tema}</div>
        <div class="bar mt-1"><span style="width:${Math.min(100, e.crecimiento / 2.2)}%"></span></div></div>
      <span class="delta delta-up"><i data-lucide="trending-up" style="width:12px;height:12px"></i>${VPID.fmt.pct(e.crecimiento, 0)}</span>
    </div>`).join('')}</div>`;
}
function alertStrip(items) {
  return `<div class="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">${items.map(a => `
    <div class="rounded-lg p-3 border border-[var(--border)] bg-[var(--surface-2)]">
      <div class="flex items-center justify-between mb-1">${C.badgeSev(a.severidad)}<span class="text-[11px] text-muted">${VPID.fmt.ago(a.created_at)}</span></div>
      <div class="text-sm font-semibold">${a.titulo}</div>
      <div class="text-xs text-muted line-clamp-2 mt-0.5">${a.descripcion}</div>
    </div>`).join('')}</div>`;
}

/* ════════════════════════════ 2. NEWS ════════════════════════════ */
VPID.views.news = async function (c) {
  VPID.ui.loading(c);
  const data = await VPID.api.articulos({});
  const temas = [...new Set(VPID.mock.articulos.map(a => a.tema))];
  const estados = [...new Set(VPID.mock.articulos.map(a => a.estado))];

  c.innerHTML = C.header('Monitoreo de Noticias', `${VPID.fmt.num(data.total)} artículos clasificados de fuentes públicas`,
    `<div class="search-wrap" style="width:240px"><i data-lucide="search" class="h-4 w-4 text-muted"></i><input id="news-q" class="search-input" placeholder="Filtrar titulares…"></div>`) +
    `<div class="flex flex-wrap gap-2 mb-4">
       <select class="filter-select" id="f-tema"><option value="">Todos los temas</option>${temas.map(t => `<option>${t}</option>`).join('')}</select>
       <select class="filter-select" id="f-estado"><option value="">Todos los estados</option>${estados.map(e => `<option>${e}</option>`).join('')}</select>
       <select class="filter-select" id="f-sent"><option value="">Sentimiento</option><option value="positivo">Positivo</option><option value="neutral">Neutral</option><option value="negativo">Negativo</option></select>
       <select class="filter-select" id="f-relev"><option value="">Relevancia</option><option value="critica">Crítica</option><option value="alta">Alta</option><option value="media">Media</option><option value="baja">Baja</option></select>
     </div>
     ${C.card('', '<div class="scroll-x"><table class="tbl" id="news-tbl"></table></div>', { bodyClass: 'p-0' })}`;
  VPID.ui.icons();

  function paint(rows) {
    document.getElementById('news-tbl').innerHTML =
      `<thead><tr><th>Titular</th><th>Fuente</th><th>Tema</th><th>Estado</th><th>Sentimiento</th><th>Relevancia</th><th>Alcance</th><th>Publicado</th></tr></thead>
       <tbody>${rows.map(a => `<tr>
         <td class="max-w-[360px]"><div class="font-medium truncate">${a.titulo}</div><div class="text-xs text-muted">${a.actor}</div></td>
         <td><div class="text-sm">${a.fuente}</div><div class="text-[11px] text-muted">${a.tipo_fuente}</div></td>
         <td><span class="badge" style="background:${a.tema_color}22;color:${a.tema_color}">${a.tema}</span></td>
         <td class="text-sm">${a.estado}</td>
         <td>${C.badgeSent(a.score)}</td>
         <td>${C.badgeRelev(a.relevancia)}</td>
         <td class="mono text-sm">${VPID.fmt.compact(a.alcance_estimado)}</td>
         <td class="text-xs text-muted whitespace-nowrap">${VPID.fmt.ago(a.publicado_en)}</td></tr>`).join('')}</tbody>`;
    VPID.ui.icons();
  }
  function apply() {
    let rows = [...VPID.mock.articulos];
    const q = document.getElementById('news-q').value.toLowerCase();
    const ft = document.getElementById('f-tema').value, fe = document.getElementById('f-estado').value;
    const fs = document.getElementById('f-sent').value, fr = document.getElementById('f-relev').value;
    if (q) rows = rows.filter(a => (a.titulo + a.actor + a.fuente).toLowerCase().includes(q));
    if (ft) rows = rows.filter(a => a.tema === ft);
    if (fe) rows = rows.filter(a => a.estado === fe);
    if (fs) rows = rows.filter(a => a.sentimiento === fs);
    if (fr) rows = rows.filter(a => a.relevancia === fr);
    paint(rows);
  }
  ['news-q', 'f-tema', 'f-estado', 'f-sent', 'f-relev'].forEach(id => {
    document.getElementById(id).addEventListener('input', apply);
  });
  paint(data.items);
};

/* ════════════════════════════ 3. TRENDS ════════════════════════════ */
VPID.views.trends = async function (c) {
  VPID.ui.loading(c);
  const tr = await VPID.api.tendencias();
  c.innerHTML = C.header('Análisis de Tendencias', 'Evolución temporal de menciones, crecimiento y temas emergentes') +
    `<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
       <div class="lg:col-span-2">${C.card('Volumen de menciones por tema (30 días)', '<div id="t-area"></div>', { icon: 'activity' })}</div>
       <div>${C.card('Temas emergentes', emergeList(tr.emergentes), { icon: 'flame' })}</div>
     </div>
     <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
       <div>${C.card('Crecimiento por tema', '<div id="t-bars"></div>', { icon: 'bar-chart-3' })}</div>
       <div>${C.card('Patrón semanal de actividad', '<div id="t-week"></div>', { icon: 'calendar-days' })}</div>
     </div>`;
  VPID.ui.icons();
  VPID.charts.area(document.getElementById('t-area'), tr.series.map(s => ({ name: s.name, data: s.data })), { colors: tr.series.map(s => s.color), height: 340 });
  VPID.charts.barsH(document.getElementById('t-bars'), tr.emergentes.map(e => e.tema), tr.emergentes.map(e => e.crecimiento), { name: 'Crecimiento %', distributed: true, height: 300 });
  const dias = ['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'];
  VPID.charts.bars(document.getElementById('t-week'), dias, [{ name: 'Menciones', data: dias.map(() => Math.round(Math.random() * 400 + 200)) }], { colors: [VPID.palette.accent2], height: 300 });
};

/* ════════════════════════════ 4. NARRATIVES ════════════════════════════ */
VPID.views.narratives = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.narrativas();
  c.innerHTML = C.header('Detección de Narrativas', 'Agrupación temática y de encuadre detectada en la cobertura pública',
    `<span class="chip active"><i data-lucide="sparkles" style="width:14px;height:14px"></i> ${items.filter(n => n.emergente).length} emergentes</span>`) +
    `<div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">${items.map((n, i) => `
      <div class="card fade-in">
        <div class="card-b">
          <div class="flex items-center justify-between mb-2">
            ${n.emergente ? '<span class="badge tag-emergent"><i data-lucide="trending-up" style="width:12px;height:12px"></i> Emergente</span>' : C.badgeRelev(n.relevancia)}
            <span class="delta ${n.variacion >= 0 ? 'delta-up' : 'delta-down'}">${VPID.fmt.pct(n.variacion, 0)}</span>
          </div>
          <h3 class="font-semibold leading-snug mb-1">${n.titulo}</h3>
          <div class="flex flex-wrap gap-1 my-2">${(n.palabras_clave || []).map(k => `<span class="text-[11px] px-1.5 py-0.5 rounded bg-[var(--surface-2)] text-muted">#${k}</span>`).join('')}</div>
          <div id="nspark-${i}" class="my-1"></div>
          <div class="flex items-center justify-between text-xs text-muted mt-2">
            <span>${VPID.fmt.num(n.total_articulos)} artículos</span>
            <span>${VPID.fmt.compact(n.alcance_estimado)} alcance</span>
            ${C.badgeSent(n.sentimiento === 'negativo' ? -0.5 : n.sentimiento === 'positivo' ? 0.5 : 0)}
          </div>
        </div>
      </div>`).join('')}</div>`;
  VPID.ui.icons();
  items.forEach((n, i) => VPID.charts.spark(document.getElementById('nspark-' + i), n.serie.map(p => p.y), n.emergente ? VPID.palette.accent2 : VPID.palette.accent));
};

/* ════════════════════════════ 5. SENTIMENT ════════════════════════════ */
VPID.views.sentiment = async function (c) {
  VPID.ui.loading(c);
  const s = await VPID.api.sentimiento();
  const idx = Math.round(((s.resumen.score_global + 1) / 2) * 100);
  c.innerHTML = C.header('Análisis de Sentimiento', 'Tono de la cobertura mediática pública, estimado mediante IA / léxico') +
    `<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
       <div>${C.card('Índice de sentimiento', '<div id="s-gauge"></div><p class="text-center text-xs text-muted -mt-2">Escala 0 (negativo) – 100 (positivo)</p>', { icon: 'gauge' })}</div>
       <div>${C.card('Distribución', '<div id="s-donut"></div>', { icon: 'pie-chart' })}</div>
       <div>${C.card('Resumen', sentSummary(s.resumen), { icon: 'sparkles' })}</div>
     </div>
     <div class="mt-4">${C.card('Evolución del sentimiento por tema', '<div id="s-series"></div>', { icon: 'line-chart' })}</div>`;
  VPID.ui.icons();
  VPID.charts.gauge(document.getElementById('s-gauge'), idx, { label: 'Índice', color: idx >= 50 ? VPID.palette.pos : VPID.palette.neg, color2: VPID.palette.accent2 });
  VPID.charts.donut(document.getElementById('s-donut'), ['Positivo', 'Neutral', 'Negativo'], [s.resumen.positivo, s.resumen.neutral, s.resumen.negativo]);
  VPID.charts.area(document.getElementById('s-series'), s.series.map(x => ({ name: x.name, data: x.data })), { colors: s.series.map(x => x.color), height: 320 });
};
function sentSummary(r) {
  return `<div class="space-y-3">
    <div class="flex items-center justify-between"><span class="text-sm text-muted">Positivo</span><span class="font-semibold" style="color:var(--pos)">${r.positivo}%</span></div>
    <div class="bar"><span style="width:${r.positivo}%;background:var(--pos)"></span></div>
    <div class="flex items-center justify-between"><span class="text-sm text-muted">Neutral</span><span class="font-semibold" style="color:var(--neu)">${r.neutral}%</span></div>
    <div class="bar"><span style="width:${r.neutral}%;background:var(--neu)"></span></div>
    <div class="flex items-center justify-between"><span class="text-sm text-muted">Negativo</span><span class="font-semibold" style="color:var(--neg)">${r.negativo}%</span></div>
    <div class="bar"><span style="width:${r.negativo}%;background:var(--neg)"></span></div>
    <p class="text-xs text-muted pt-2 border-t border-[var(--border)]">Predomina un tono <b>${r.negativo > r.positivo ? 'crítico' : 'equilibrado'}</b> en la cobertura del período. Valores sintéticos de demostración.</p>
  </div>`;
}

/* ════════════════════════════ 6. ACTORS ════════════════════════════ */
VPID.views.actors = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.ranking();
  c.innerHTML = C.header('Ranking de Actores Públicos', 'Figuras públicas por volumen de menciones en información pública') +
    `<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
       <div class="lg:col-span-2">${C.card('Tabla de ranking', '<div class="scroll-x"><table class="tbl" id="rk-tbl"></table></div>', { icon: 'list-ordered', bodyClass: 'p-0' })}</div>
       <div>${C.card('Perfil comparativo (top 3)', '<div style="height:300px"><canvas id="rk-radar"></canvas></div>', { icon: 'radar' })}</div>
     </div>`;
  VPID.ui.icons();
  document.getElementById('rk-tbl').innerHTML =
    `<thead><tr><th>#</th><th>Actor</th><th>Org.</th><th>Menciones</th><th>Tendencia</th><th>Sentimiento</th><th>Alcance</th></tr></thead>
     <tbody>${items.map((a, i) => `<tr>
       <td class="mono text-muted">${i + 1}</td>
       <td><div class="flex items-center gap-2"><span class="avatar" style="width:28px;height:28px;font-size:10px">${a.nombre.split(' ').map(x => x[0]).slice(0, 2).join('')}</span>
         <div><div class="font-medium text-sm">${a.nombre}</div><div class="text-[11px] text-muted">${a.cargo}</div></div></div></td>
       <td>${C.orgPill(a.organizacion)}</td>
       <td class="mono font-semibold">${VPID.fmt.num(a.menciones)}</td>
       <td><div id="rkspark-${i}" style="width:90px"></div></td>
       <td>${C.badgeSent(a.sentimiento_prom)}</td>
       <td class="mono text-sm">${VPID.fmt.compact(a.alcance_estimado)}</td></tr>`).join('')}</tbody>`;
  VPID.ui.icons();
  items.forEach((a, i) => a.trend && VPID.charts.spark(document.getElementById('rkspark-' + i), a.trend.map(p => p.y), a.sentimiento_prom >= 0 ? VPID.palette.pos : VPID.palette.neg));
  const temas = VPID.mock.temas.slice(0, 6).map(t => t.nombre);
  VPID.charts.radar(document.getElementById('rk-radar'), temas,
    items.slice(0, 3).map(a => ({ label: a.nombre.split(' ')[0], data: temas.map(() => Math.round(Math.random() * 80 + 20)) })));
};

/* ════════════════════════════ 7. TERRITORIAL ════════════════════════════ */
VPID.views.territorial = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.territorial();
  c.innerHTML = C.header('Monitoreo Territorial', 'Distribución geográfica de la cobertura pública por estado') +
    `<div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
       <div class="lg:col-span-2">${C.card('Mapa de cobertura', '<div id="terr-map" style="height:460px"></div>', { icon: 'map-pinned', bodyClass: 'p-2' })}</div>
       <div>${C.card('Ranking por estado', '<div class="scroll-x" style="max-height:460px;overflow-y:auto"><table class="tbl" id="terr-tbl"></table></div>', { icon: 'list', bodyClass: 'p-0' })}</div>
     </div>
     <div class="mt-4">${C.card('Volumen de cobertura por estado', '<div id="terr-bars"></div>', { icon: 'bar-chart-3' })}</div>`;
  VPID.ui.icons();
  const sorted = [...items].sort((a, b) => b.articulos - a.articulos);
  document.getElementById('terr-tbl').innerHTML =
    `<thead><tr><th>Estado</th><th>Artículos</th><th>Sentimiento</th></tr></thead>
     <tbody>${sorted.map(r => `<tr><td class="font-medium text-sm">${r.estado}</td>
       <td class="mono">${VPID.fmt.num(r.articulos)}</td>
       <td>${C.badgeSent(r.sent ?? r.sentimiento_prom ?? 0)}</td></tr>`).join('')}</tbody>`;
  VPID.maps.render('terr-map', items, { center: [8.4, -68], zoom: 6 });
  VPID.charts.barsH(document.getElementById('terr-bars'), sorted.map(r => r.estado), sorted.map(r => r.articulos), { name: 'Artículos', distributed: true, height: 360 });
};

/* ════════════════════════════ 8. MAPS ════════════════════════════ */
VPID.views.maps = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.territorial();
  c.innerHTML = C.header('Mapas Interactivos', 'Exploración geoespacial de la actividad informativa pública') +
    C.card('', '<div id="full-map" style="height:600px"></div>', { bodyClass: 'p-2' });
  VPID.maps.render('full-map', items, { center: [8.0, -66], zoom: 6 });
};

/* ════════════════════════════ 9. ALERTS ════════════════════════════ */
VPID.views.alerts = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.alertas();
  c.innerHTML = C.header('Sistema de Alertas Tempranas', 'Detección automática de picos, narrativas emergentes y anomalías') +
    `<div class="space-y-3">${items.map(a => `
      <div class="card"><div class="card-b flex items-start gap-4">
        <div class="kpi-icon shrink-0" style="background:color-mix(in srgb, var(--warn) 16%, transparent);color:var(--warn)"><i data-lucide="${alertIcon(a.tipo)}" style="width:18px;height:18px"></i></div>
        <div class="flex-1 min-w-0">
          <div class="flex flex-wrap items-center gap-2 mb-1">${C.badgeSev(a.severidad)}<span class="badge badge-neu">${a.estado.replace('_', ' ')}</span><span class="text-[11px] text-muted ml-auto">${VPID.fmt.datetime(a.created_at)}</span></div>
          <h3 class="font-semibold">${a.titulo}</h3>
          <p class="text-sm text-muted mt-0.5">${a.descripcion}</p>
        </div>
        <div class="flex flex-col gap-2 shrink-0">
          <button class="btn btn-ghost text-xs" data-ack="${a.id}"><i data-lucide="check" class="h-3.5 w-3.5"></i> Reconocer</button>
        </div>
      </div></div>`).join('')}</div>`;
  VPID.ui.icons();
  c.querySelectorAll('[data-ack]').forEach(b => b.addEventListener('click', () => VPID.ui.toast('Alerta reconocida', 'ok')));
};
function alertIcon(t) { return { pico_menciones: 'trending-up', narrativa_emergente: 'git-branch', sentimiento: 'gauge', territorial: 'map-pin', correlacion: 'network' }[t] || 'bell'; }

/* ════════════════════════════ 10. COMPARE ════════════════════════════ */
VPID.views.compare = async function (c) {
  VPID.ui.loading(c);
  const tr = await VPID.api.tendencias();
  const cor = await VPID.api.correlaciones();
  c.innerHTML = C.header('Comparativos Históricos', 'Contraste de períodos y correlaciones entre temas',
    `<select class="filter-select" id="cmp-range"><option>Esta semana vs. anterior</option><option>Este mes vs. anterior</option><option>Trimestre vs. anterior</option></select>`) +
    `<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
       <div>${C.card('Comparación de volumen', '<div id="cmp-bars"></div>', { icon: 'bar-chart-3' })}</div>
       <div>${C.card('Matriz de correlación de temas', '<div id="cmp-heat"></div>', { icon: 'grid-3x3' })}</div>
     </div>
     <div class="mt-4">${C.card('Series superpuestas', '<div id="cmp-area"></div>', { icon: 'line-chart' })}</div>`;
  VPID.ui.icons();
  const temas = tr.series.slice(0, 5);
  VPID.charts.bars(document.getElementById('cmp-bars'), temas.map(t => t.name),
    [{ name: 'Período actual', data: temas.map(t => t.data.slice(-7).reduce((a, b) => a + b.y, 0)) },
     { name: 'Período anterior', data: temas.map(t => t.data.slice(-14, -7).reduce((a, b) => a + b.y, 0)) }],
    { colors: [VPID.palette.accent, VPID.palette.muted || '#64748b'], height: 320 });
  // heatmap matrix
  const cats = ['Elecciones', 'Negociación', 'Economía', 'Servicios', 'Migración'];
  const heat = cats.map(a => ({ name: a, data: cats.map(b => ({ x: b, y: a === b ? 1 : +(Math.random() * 0.7 + 0.1).toFixed(2) })) }));
  VPID.charts.heatmap(document.getElementById('cmp-heat'), heat);
  VPID.charts.area(document.getElementById('cmp-area'), temas.slice(0, 3).map(s => ({ name: s.name, data: s.data })), { colors: temas.map(s => s.color), height: 300 });
};

/* ════════════════════════════ 11. INTELLIGENCE ════════════════════════════ */
VPID.views.intelligence = async function (c) {
  VPID.ui.loading(c);
  const [{ items: fuentes }, k, cor] = await Promise.all([VPID.api.fuentes(), VPID.api.kpis(), VPID.api.correlaciones()]);
  const topFuentes = [...fuentes].sort((a, b) => (b.articulos_30d || 0) - (a.articulos_30d || 0)).slice(0, 8);
  const keywords = ['elecciones', 'unidad', 'frontera', 'servicios', 'derechos', 'economía', 'negociación', 'migración', 'observación', 'diálogo', 'comicios', 'región'];
  c.innerHTML = C.header('Centro de Inteligencia Digital', 'Visión integrada de fuentes, señales y correlaciones de la información pública') +
    `<div class="grid-kpi mb-4">
       ${C.kpi('Fuentes monitoreadas', VPID.fmt.num(fuentes.length), { icon: 'database' })}
       ${C.kpi('Fuentes activas', VPID.fmt.num(fuentes.filter(f => f.estado === 'activa').length), { icon: 'wifi' })}
       ${C.kpi('Cobertura diaria', VPID.fmt.num(Math.round(k.total_articulos / 7)), { icon: 'newspaper' })}
       ${C.kpi('Alcance acumulado', VPID.fmt.compact(k.alcance_total), { icon: 'radio' })}
     </div>
     <div class="grid grid-cols-1 lg:grid-cols-3 gap-4">
       <div class="lg:col-span-2">${C.card('Fuentes más activas (30 días)', '<div id="int-bars"></div>', { icon: 'bar-chart-3' })}</div>
       <div>${C.card('Mapa de términos', `<div class="flex flex-wrap gap-2">${keywords.map(w => `<span class="chip" style="font-size:${Math.random() * 8 + 12}px">${w}</span>`).join('')}</div>`, { icon: 'tags' })}</div>
     </div>
     <div class="grid grid-cols-1 lg:grid-cols-2 gap-4 mt-4">
       <div>${C.card('Correlaciones entre temas', corrList(cor.items), { icon: 'network' })}</div>
       <div>${C.card('Distribución por tipo de fuente', '<div id="int-types"></div>', { icon: 'pie-chart' })}</div>
     </div>`;
  VPID.ui.icons();
  VPID.charts.barsH(document.getElementById('int-bars'), topFuentes.map(f => f.nombre), topFuentes.map(f => f.articulos_30d || 0), { name: 'Artículos', distributed: true, height: 320 });
  const tipos = {}; fuentes.forEach(f => tipos[f.tipo] = (tipos[f.tipo] || 0) + 1);
  VPID.charts.donut(document.getElementById('int-types'), Object.keys(tipos), Object.values(tipos), VPID.palette.series);
};
function corrList(items) {
  return `<div class="space-y-3">${items.map(r => `
    <div class="flex items-center gap-3">
      <div class="flex-1 text-sm"><b>${r.a}</b> <span class="text-muted">↔</span> <b>${r.b}</b></div>
      <div class="bar" style="width:120px"><span style="width:${r.r * 100}%"></span></div>
      <span class="mono text-sm" style="width:40px;text-align:right">${r.r.toFixed(2)}</span>
    </div>`).join('')}</div>`;
}

/* ════════════════════════════ 12. REPORTS ════════════════════════════ */
VPID.views.reports = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.reportes();
  c.innerHTML = C.header('Informes Ejecutivos', 'Generación y archivo de informes — exportación únicamente en PDF',
    `<button class="btn btn-primary" id="gen-report"><i data-lucide="file-plus-2" class="h-4 w-4"></i> Generar informe diario</button>`) +
    `<div class="card mb-4"><div class="card-b flex items-center gap-3 text-sm text-muted">
       <i data-lucide="shield-check" class="h-5 w-5" style="color:var(--pos)"></i>
       El sistema genera automáticamente un Informe Ejecutivo PDF cada día a las 06:00 (VET), con portada institucional, KPIs, tendencias, actores, narrativas, análisis territorial, alertas, conclusiones y recomendaciones por IA. <b>PDF es el único formato de exportación.</b>
     </div></div>
     <div class="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4">${items.map(r => `
       <div class="card fade-in"><div class="card-b">
         <div class="flex items-start justify-between mb-3">
           <div class="kpi-icon" style="background:rgba(239,68,68,.14);color:#ef4444"><i data-lucide="file-text" style="width:18px;height:18px"></i></div>
           <span class="badge badge-pos">${r.estado}</span>
         </div>
         <h3 class="font-semibold leading-snug text-sm">${r.titulo}</h3>
         <div class="text-xs text-muted mt-1">${VPID.fmt.date(r.created_at)} · ${VPID.fmt.compact(r.archivo_bytes)}B · PDF</div>
         <div class="flex gap-2 mt-3">
           <button class="btn btn-primary flex-1 justify-center text-xs" data-dl="${r.id}"><i data-lucide="download" class="h-3.5 w-3.5"></i> Descargar PDF</button>
         </div>
       </div></div>`).join('')}</div>`;
  VPID.ui.icons();
  document.getElementById('gen-report').addEventListener('click', async () => {
    VPID.ui.toast('Generando informe ejecutivo…', 'info');
    await VPID.api.generarReporte({ tipo: 'ejecutivo_diario' });
    VPID.report.printable();
  });
  c.querySelectorAll('[data-dl]').forEach(b => b.addEventListener('click', () => VPID.report.printable()));
};

/* ════════════════════════════ SOURCES (fuentes admin) ════════════════════════════ */
VPID.views.sources = async function (c) {
  VPID.ui.loading(c);
  const { items } = await VPID.api.fuentes();
  c.innerHTML = C.header('Fuentes', 'Administración de medios, portales y fuentes abiertas verificables',
    `<button class="btn btn-primary" id="add-src"><i data-lucide="plus" class="h-4 w-4"></i> Nueva fuente</button>`) +
    `<div class="grid-kpi mb-4">
       ${C.kpi('Total de fuentes', VPID.fmt.num(items.length), { icon: 'database' })}
       ${C.kpi('Activas', VPID.fmt.num(items.filter(f => f.estado === 'activa').length), { icon: 'wifi' })}
       ${C.kpi('Verificadas', VPID.fmt.num(items.filter(f => f.verificada).length), { icon: 'badge-check' })}
       ${C.kpi('Credibilidad media', Math.round(items.reduce((a, b) => a + b.credibilidad, 0) / items.length) + '%', { icon: 'shield' })}
     </div>
     ${C.card('', '<div class="scroll-x"><table class="tbl" id="src-tbl"></table></div>', { bodyClass: 'p-0' })}`;
  VPID.ui.icons();
  document.getElementById('src-tbl').innerHTML =
    `<thead><tr><th>Fuente</th><th>Tipo</th><th>Alcance</th><th>Credibilidad</th><th>Verificada</th><th>Estado</th><th>Artículos 30d</th><th>Última lectura</th><th></th></tr></thead>
     <tbody>${items.map(f => `<tr>
       <td class="font-medium text-sm">${f.nombre}</td>
       <td><span class="badge badge-info">${f.tipo}</span></td>
       <td class="text-sm">${f.alcance}</td>
       <td><div class="flex items-center gap-2"><div class="bar" style="width:60px"><span style="width:${f.credibilidad}%"></span></div><span class="mono text-xs">${f.credibilidad}</span></div></td>
       <td>${f.verificada ? '<i data-lucide="badge-check" style="width:16px;height:16px;color:var(--pos)"></i>' : '<span class="text-muted text-xs">—</span>'}</td>
       <td><span class="badge ${f.estado === 'activa' ? 'badge-pos' : 'badge-neu'}">${f.estado}</span></td>
       <td class="mono text-sm">${VPID.fmt.num(f.articulos_30d || 0)}</td>
       <td class="text-xs text-muted">${VPID.fmt.ago(f.ultima_lectura)}</td>
       <td><button class="icon-btn" style="width:30px;height:30px"><i data-lucide="more-horizontal" style="width:16px;height:16px"></i></button></td></tr>`).join('')}</tbody>`;
  VPID.ui.icons();
  document.getElementById('add-src').addEventListener('click', () => VPID.ui.toast('Formulario de nueva fuente (demo)', 'info'));
};

/* ════════════════════════════ CONFIG ════════════════════════════ */
VPID.views.configuracion = async function (c) {
  c.innerHTML = C.header('Configuración', 'Preferencias de la plataforma y del usuario') +
    `<div class="grid grid-cols-1 lg:grid-cols-2 gap-4">
       ${C.card('Apariencia', `<div class="space-y-3">
         <div class="flex items-center justify-between"><span class="text-sm">Tema</span>
           <button class="btn" onclick="VPID.theme.toggle()"><i data-lucide="moon" class="h-4 w-4"></i> Alternar</button></div>
         <div class="flex items-center justify-between"><span class="text-sm">Idioma</span><select class="filter-select"><option>Español</option><option>English</option></select></div>
       </div>`, { icon: 'palette' })}
       ${C.card('Datos y privacidad', `<p class="text-sm text-muted">Esta plataforma procesa exclusivamente <b>información pública</b>. La exportación está limitada a <b>PDF</b>. Consulte la política de uso ético.</p>`, { icon: 'shield' })}
       ${C.card('Roles y acceso', `<div class="space-y-2 text-sm">
         ${['admin — acceso total', 'analista — análisis y reportes', 'editor — gestión de fuentes', 'lector — solo lectura'].map(r => `<div class="flex items-center gap-2"><i data-lucide="user-check" class="h-4 w-4 text-muted"></i>${r}</div>`).join('')}
       </div>`, { icon: 'users' })}
       ${C.card('Estado del sistema', `<div class="space-y-2 text-sm">
         <div class="flex items-center gap-2"><span class="status-dot status-dot--live"></span> API conectada (modo <span id="cfg-mode" class="mono">${VPID.api.getMode()}</span>)</div>
         <div class="flex items-center gap-2"><span class="status-dot status-dot--live"></span> ETL programado · 05:00 VET</div>
         <div class="flex items-center gap-2"><span class="status-dot status-dot--live"></span> Informe diario · 06:00 VET</div>
       </div>`, { icon: 'activity' })}
     </div>`;
  VPID.ui.icons();
};
