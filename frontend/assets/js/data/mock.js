/* ============================================================================
   VPID — Bundled demo dataset (Táchira / Venezuela, public-information theme)
   Powers the dashboard when no backend is reachable. All sentiment / mention
   figures here are SYNTHETIC and illustrative — not real measurements.
   ============================================================================ */
(function () {
  const rnd = (min, max) => Math.random() * (max - min) + min;
  const irnd = (min, max) => Math.floor(rnd(min, max + 1));
  const today = new Date();

  // Build a daily time-series for the last N days
  function series(days, base, volatility, trend = 0) {
    const out = [];
    let v = base;
    for (let i = days - 1; i >= 0; i--) {
      const d = new Date(today); d.setDate(d.getDate() - i);
      v = Math.max(0, v + rnd(-volatility, volatility) + trend);
      out.push({ x: d.toISOString().slice(0, 10), y: Math.round(v) });
    }
    return out;
  }

  const temas = [
    { id: 't1', nombre: 'Elecciones', color: '#6366f1' },
    { id: 't2', nombre: 'Derechos Humanos', color: '#ef4444' },
    { id: 't3', nombre: 'Economía', color: '#22c55e' },
    { id: 't4', nombre: 'Servicios Públicos', color: '#f59e0b' },
    { id: 't5', nombre: 'Negociación Política', color: '#06b6d4' },
    { id: 't6', nombre: 'Migración', color: '#a855f7' },
    { id: 't7', nombre: 'Seguridad', color: '#64748b' },
  ];

  const estados = [
    { id: 'e-tac', estado: 'Táchira', lat: 7.7669, lon: -72.2250, articulos: irnd(180, 320), sent: rnd(-0.3, 0.2) },
    { id: 'e-zul', estado: 'Zulia', lat: 10.6427, lon: -71.6125, articulos: irnd(150, 280), sent: rnd(-0.3, 0.1) },
    { id: 'e-dc',  estado: 'Distrito Capital', lat: 10.4806, lon: -66.9036, articulos: irnd(220, 400), sent: rnd(-0.35, 0.15) },
    { id: 'e-mir', estado: 'Miranda', lat: 10.3417, lon: -67.0407, articulos: irnd(120, 240), sent: rnd(-0.25, 0.1) },
    { id: 'e-car', estado: 'Carabobo', lat: 10.1620, lon: -68.0077, articulos: irnd(90, 200), sent: rnd(-0.2, 0.1) },
    { id: 'e-lar', estado: 'Lara', lat: 10.0731, lon: -69.3220, articulos: irnd(80, 180), sent: rnd(-0.2, 0.15) },
    { id: 'e-mer', estado: 'Mérida', lat: 8.5897, lon: -71.1561, articulos: irnd(70, 150), sent: rnd(-0.15, 0.2) },
    { id: 'e-tru', estado: 'Trujillo', lat: 9.3667, lon: -70.4333, articulos: irnd(50, 120), sent: rnd(-0.15, 0.15) },
    { id: 'e-bol', estado: 'Bolívar', lat: 8.1222, lon: -63.5497, articulos: irnd(60, 140), sent: rnd(-0.25, 0.05) },
    { id: 'e-anz', estado: 'Anzoátegui', lat: 10.1340, lon: -64.6853, articulos: irnd(50, 130), sent: rnd(-0.2, 0.1) },
  ];

  const actores = [
    { id: 'a1', nombre: 'María Corina Machado', cargo: 'Líder político', organizacion: 'VV' },
    { id: 'a2', nombre: 'Edmundo González Urrutia', cargo: 'Figura pública', organizacion: 'PUD' },
    { id: 'a3', nombre: 'Henrique Capriles', cargo: 'Dirigente', organizacion: 'PJ' },
    { id: 'a4', nombre: 'Manuel Rosales', cargo: 'Gobernador', organizacion: 'UNT' },
    { id: 'a5', nombre: 'Juan Pablo Guanipa', cargo: 'Dirigente', organizacion: 'PJ' },
    { id: 'a6', nombre: 'Laidy Gómez', cargo: 'Dirigente regional', organizacion: 'AD' },
    { id: 'a7', nombre: 'Roberto Enríquez', cargo: 'Dirigente', organizacion: 'COPEI' },
    { id: 'a8', nombre: 'Tomás Guanipa', cargo: 'Dirigente', organizacion: 'PJ' },
  ].map((a, i) => ({
    ...a,
    menciones: irnd(40, 480) - i * 20,
    sentimiento_prom: rnd(-0.4, 0.4),
    alcance_estimado: irnd(120000, 2400000),
    trend: series(14, irnd(20, 60), 8, rnd(-1, 2)),
  })).sort((a, b) => b.menciones - a.menciones);

  const fuentesNombres = [
    ['El Nacional', 'medio', 'nacional', 70], ['El Universal', 'medio', 'nacional', 68],
    ['Tal Cual', 'medio', 'nacional', 72], ['Efecto Cocuyo', 'portal', 'nacional', 78],
    ['Runrun.es', 'portal', 'nacional', 75], ['La Patilla', 'portal', 'nacional', 66],
    ['Crónica.Uno', 'portal', 'nacional', 77], ['Diario La Nación', 'medio', 'regional', 69],
    ['La Prensa del Táchira', 'medio', 'regional', 60], ['Diario de Los Andes', 'medio', 'regional', 62],
    ['Reuters (AL)', 'agencia', 'internacional', 85], ['France 24 Español', 'medio', 'internacional', 82],
  ];
  const fuentes = fuentesNombres.map((f, i) => ({
    id: 'f' + (i + 1), nombre: f[0], tipo: f[1], alcance: f[2],
    credibilidad: f[3], verificada: f[3] >= 65,
    estado: Math.random() > 0.12 ? 'activa' : 'pausada',
    url: 'https://example.org/' + f[0].toLowerCase().replace(/[^a-z]/g, ''),
    articulos_30d: irnd(20, 320), ultima_lectura: new Date(today - irnd(1, 600) * 60000).toISOString(),
  }));

  const narrativaTitulos = [
    ['Llamado a la unidad opositora de cara al proceso electoral', 't1', 'neutral', 'alta', true],
    ['Crisis de servicios públicos en la región andina', 't4', 'negativo', 'alta', false],
    ['Debate sobre condiciones electorales y observación', 't1', 'neutral', 'media', false],
    ['Situación de derechos y libertades civiles', 't2', 'negativo', 'critica', true],
    ['Expectativas económicas y poder adquisitivo', 't3', 'negativo', 'media', false],
    ['Dinámica migratoria y retorno en la frontera', 't6', 'neutral', 'media', false],
    ['Diálogo y posibles acuerdos políticos', 't5', 'positivo', 'media', false],
  ];
  const narrativas = narrativaTitulos.map((n, i) => ({
    id: 'n' + (i + 1), titulo: n[0], tema_id: n[1], sentimiento: n[2], relevancia: n[3],
    emergente: n[4], total_articulos: irnd(8, 140), alcance_estimado: irnd(80000, 1800000),
    variacion: rnd(-30, 180), ultima_vista: new Date(today - irnd(1, 72) * 3600000).toISOString(),
    palabras_clave: ['unidad', 'elecciones', 'región', 'frontera', 'derechos'].slice(0, irnd(3, 5)),
    serie: series(14, irnd(5, 25), 5, n[4] ? 2 : 0.2),
  }));

  const titularesDemo = [
    'Dirigentes opositores presentan agenda regional en San Cristóbal',
    'Análisis: cobertura mediática sobre el proceso electoral',
    'Organizaciones civiles publican comunicado sobre servicios públicos',
    'Foro público aborda economía y empleo en la región andina',
    'Cobertura internacional sobre la situación política venezolana',
    'Actividad partidista en municipios fronterizos del Táchira',
    'Debate público sobre derechos y participación ciudadana',
    'Medios regionales reportan jornada de organización vecinal',
    'Encuentro de factores políticos discute hoja de ruta',
    'Reportan expectativas por anuncios de cara a comicios',
  ];
  const sentLabels = ['positivo', 'neutral', 'negativo'];
  const relev = ['baja', 'media', 'alta', 'critica'];
  const articulos = Array.from({ length: 60 }, (_, i) => {
    const f = fuentes[irnd(0, fuentes.length - 1)];
    const t = temas[irnd(0, temas.length - 1)];
    const e = estados[irnd(0, estados.length - 1)];
    const a = actores[irnd(0, actores.length - 1)];
    const score = rnd(-1, 1);
    return {
      id: 'art' + (i + 1),
      titulo: titularesDemo[i % titularesDemo.length],
      resumen: 'Resumen sintético de demostración para el panel de monitoreo de información pública.',
      fuente: f.nombre, fuente_id: f.id, tipo_fuente: f.tipo,
      tema: t.nombre, tema_color: t.color, estado: e.estado,
      actor: a.nombre,
      publicado_en: new Date(today - i * irnd(20, 90) * 60000).toISOString(),
      relevancia: relev[Math.min(3, irnd(0, 3))],
      sentimiento: score > 0.15 ? 'positivo' : score < -0.15 ? 'negativo' : 'neutral',
      score: score,
      alcance_estimado: irnd(2000, 180000),
      url: '#',
    };
  });

  const alertas = [
    { id: 'al1', titulo: 'Pico de menciones detectado', descripcion: 'Incremento del 142% en menciones sobre "Elecciones" en las últimas 24h.', tipo: 'pico_menciones', severidad: 'alta', estado: 'abierta', valor: 142, created_at: new Date(today - 2 * 3600000).toISOString() },
    { id: 'al2', titulo: 'Narrativa emergente', descripcion: 'Nueva narrativa sobre servicios públicos ganando tracción en la región andina.', tipo: 'narrativa_emergente', severidad: 'media', estado: 'en_revision', valor: 38, created_at: new Date(today - 6 * 3600000).toISOString() },
    { id: 'al3', titulo: 'Caída de sentimiento', descripcion: 'El sentimiento global descendió 0.18 puntos respecto a la semana previa.', tipo: 'sentimiento', severidad: 'media', estado: 'abierta', valor: -0.18, created_at: new Date(today - 11 * 3600000).toISOString() },
    { id: 'al4', titulo: 'Concentración territorial', descripcion: 'Concentración inusual de cobertura en municipios fronterizos del Táchira.', tipo: 'territorial', severidad: 'baja', estado: 'reconocida', valor: 27, created_at: new Date(today - 26 * 3600000).toISOString() },
    { id: 'al5', titulo: 'Alta correlación de eventos', descripcion: 'Correlación elevada entre cobertura de "Negociación" y "Elecciones".', tipo: 'correlacion', severidad: 'info', estado: 'abierta', valor: 0.82, created_at: new Date(today - 40 * 3600000).toISOString() },
  ];

  const reportes = Array.from({ length: 8 }, (_, i) => {
    const d = new Date(today); d.setDate(d.getDate() - i);
    return {
      id: 'rep' + (i + 1),
      titulo: `Informe Ejecutivo Diario — ${d.toLocaleDateString('es-VE', { day: '2-digit', month: 'long', year: 'numeric' })}`,
      tipo: 'ejecutivo_diario', estado: i === 0 ? 'completado' : 'completado',
      periodo_hasta: d.toISOString().slice(0, 10),
      archivo_bytes: irnd(420000, 1200000),
      created_at: d.toISOString(),
    };
  });

  const sentScore = -0.06;
  const kpis = {
    fecha: today.toISOString().slice(0, 10),
    total_articulos: 1248, total_menciones: 3962, fuentes_activas: 11,
    sentimiento_global: sentScore, narrativas_activas: 7, narrativas_emergentes: 2,
    alertas_abiertas: alertas.filter(a => a.estado === 'abierta').length,
    alcance_total: 18940000,
    deltas: { total_articulos: 12.4, total_menciones: 18.1, fuentes_activas: 0, sentimiento_global: -8.2, alcance_total: 9.7 },
    spark: {
      total_articulos: series(14, 80, 18, 1).map(p => p.y),
      total_menciones: series(14, 260, 40, 2).map(p => p.y),
      alcance_total: series(14, 1.1e6, 2e5, 1e4).map(p => p.y),
      sentimiento_global: series(14, 50, 8).map(p => (p.y - 50) / 100),
    },
  };

  VPID.mock = {
    temas, estados, actores, fuentes, narrativas, articulos, alertas, reportes, kpis,
    series,
    sentimiento: {
      resumen: { positivo: 28, neutral: 41, negativo: 31, score_global: sentScore },
      series: temas.slice(0, 4).map((t, i) => ({
        name: t.nombre, color: t.color, data: series(14, 50, 10, i - 1.5).map(p => ({ x: p.x, y: +(rnd(-0.5, 0.4)).toFixed(2) })),
      })),
    },
    tendencias: {
      series: temas.map(t => ({ name: t.nombre, color: t.color, data: series(30, irnd(20, 90), 10, rnd(-1, 2)) })),
      emergentes: [
        { tema: 'Observación electoral', crecimiento: 214, menciones: 342 },
        { tema: 'Servicios en la frontera', crecimiento: 158, menciones: 221 },
        { tema: 'Unidad opositora', crecimiento: 96, menciones: 588 },
        { tema: 'Poder adquisitivo', crecimiento: 73, menciones: 410 },
        { tema: 'Retorno migratorio', crecimiento: 41, menciones: 187 },
      ],
    },
    correlaciones: [
      { a: 'Elecciones', b: 'Negociación', r: 0.82 },
      { a: 'Servicios', b: 'Economía', r: 0.74 },
      { a: 'Migración', b: 'Economía', r: 0.61 },
      { a: 'DDHH', b: 'Negociación', r: 0.57 },
      { a: 'Seguridad', b: 'Migración', r: 0.49 },
    ],
  };
})();
