/* ============================================================================
   VPID — Chart factories (ApexCharts + Chart.js), theme-aware.
   All instances are tracked so they can be disposed when the view changes.
   ============================================================================ */
VPID.charts = (function () {
  const registry = [];
  function track(c) { registry.push(c); return c; }
  function disposeAll() {
    while (registry.length) {
      const c = registry.pop();
      try { c.destroy(); } catch (e) { /* noop */ }
    }
  }

  function css(v) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
  function theme() {
    const dark = VPID.theme.isDark();
    return {
      dark,
      text: css('--text'),
      muted: css('--text-muted'),
      grid: dark ? 'rgba(148,163,184,.12)' : 'rgba(15,23,42,.07)',
      mode: dark ? 'dark' : 'light',
    };
  }

  const baseApex = () => {
    const t = theme();
    return {
      chart: { fontFamily: 'Inter, sans-serif', foreColor: t.muted, toolbar: { show: false }, animations: { easing: 'easeinout', speed: 500 } },
      grid: { borderColor: t.grid, strokeDashArray: 4, padding: { left: 8, right: 8 } },
      tooltip: { theme: t.mode },
      dataLabels: { enabled: false },
      legend: { labels: { colors: t.muted }, fontSize: '12px', markers: { radius: 12 } },
    };
  };

  // ── Sparkline (Apex area, minimal) ────────────────────────────────────────
  function spark(el, data, color) {
    const o = {
      chart: { type: 'area', height: 46, sparkline: { enabled: true }, animations: { enabled: true } },
      stroke: { curve: 'smooth', width: 2 },
      fill: { type: 'gradient', gradient: { opacityFrom: 0.4, opacityTo: 0 } },
      colors: [color || VPID.palette.accent],
      series: [{ data }],
      tooltip: { enabled: false },
    };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Multi-series area (trends, evolution) ─────────────────────────────────
  function area(el, series, opts = {}) {
    const o = {
      ...baseApex(),
      chart: { ...baseApex().chart, type: 'area', height: opts.height || 340, stacked: !!opts.stacked },
      series,
      colors: opts.colors || VPID.palette.series,
      stroke: { curve: 'smooth', width: 2 },
      fill: { type: 'gradient', gradient: { opacityFrom: 0.35, opacityTo: 0.02, stops: [0, 90] } },
      xaxis: { type: 'datetime', axisBorder: { show: false }, axisTicks: { show: false } },
      yaxis: { labels: { formatter: (v) => VPID.fmt.compact(v) } },
    };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Horizontal bars (ranking) ─────────────────────────────────────────────
  function barsH(el, categories, data, opts = {}) {
    const o = {
      ...baseApex(),
      chart: { ...baseApex().chart, type: 'bar', height: opts.height || 340 },
      series: [{ name: opts.name || 'Valor', data }],
      colors: [VPID.palette.accent],
      plotOptions: { bar: { horizontal: true, borderRadius: 6, barHeight: '62%', distributed: !!opts.distributed } },
      xaxis: { categories, labels: { formatter: (v) => VPID.fmt.compact(v) } },
    };
    if (opts.distributed) o.colors = VPID.palette.series;
    if (opts.distributed) o.legend = { show: false };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Vertical bars ─────────────────────────────────────────────────────────
  function bars(el, categories, series, opts = {}) {
    const o = {
      ...baseApex(),
      chart: { ...baseApex().chart, type: 'bar', height: opts.height || 320, stacked: !!opts.stacked },
      series,
      colors: opts.colors || VPID.palette.series,
      plotOptions: { bar: { borderRadius: 5, columnWidth: '55%' } },
      xaxis: { categories },
      yaxis: { labels: { formatter: (v) => VPID.fmt.compact(v) } },
    };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Donut (sentiment split) ───────────────────────────────────────────────
  function donut(el, labels, values, colors) {
    const o = {
      ...baseApex(),
      chart: { ...baseApex().chart, type: 'donut', height: 280 },
      series: values, labels, colors: colors || [VPID.palette.pos, VPID.palette.neu, VPID.palette.neg],
      stroke: { width: 0 },
      plotOptions: { pie: { donut: { size: '70%', labels: { show: true, total: { show: true, label: 'Total', formatter: () => VPID.fmt.num(values.reduce((a, b) => a + b, 0)) } } } } },
      legend: { ...baseApex().legend, position: 'bottom' },
    };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Radial gauge (sentiment index / single KPI) ──────────────────────────
  function gauge(el, value, opts = {}) {
    const o = {
      ...baseApex(),
      chart: { ...baseApex().chart, type: 'radialBar', height: opts.height || 280 },
      series: [value],
      colors: [opts.color || VPID.palette.accent],
      plotOptions: { radialBar: {
        hollow: { size: '62%' },
        track: { background: theme().grid },
        dataLabels: { name: { offsetY: 22, color: theme().muted, fontSize: '13px' },
          value: { offsetY: -10, fontSize: '30px', fontWeight: 800, color: theme().text, formatter: opts.fmt || ((v) => v + '%') } },
      } },
      labels: [opts.label || ''],
      fill: { type: 'gradient', gradient: { shade: 'dark', gradientToColors: [opts.color2 || VPID.palette.accent2], stops: [0, 100] } },
    };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Heatmap (correlations) ────────────────────────────────────────────────
  function heatmap(el, series) {
    const o = {
      ...baseApex(),
      chart: { ...baseApex().chart, type: 'heatmap', height: 320 },
      series,
      colors: [VPID.palette.accent],
      plotOptions: { heatmap: { radius: 6, colorScale: { ranges: [
        { from: -1, to: 0.3, color: '#334155', name: 'baja' },
        { from: 0.3, to: 0.6, color: '#6366f1', name: 'media' },
        { from: 0.6, to: 1, color: '#22d3ee', name: 'alta' },
      ] } } },
    };
    const c = new ApexCharts(el, o); c.render(); return track(c);
  }

  // ── Radar (Chart.js — actor profile / topic mix) ──────────────────────────
  function radar(canvas, labels, datasets) {
    const t = theme();
    const c = new Chart(canvas, {
      type: 'radar',
      data: { labels, datasets: datasets.map((d, i) => ({
        ...d, borderColor: VPID.palette.series[i], backgroundColor: VPID.palette.series[i] + '33',
        pointBackgroundColor: VPID.palette.series[i], borderWidth: 2,
      })) },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { labels: { color: t.muted } } },
        scales: { r: { grid: { color: t.grid }, angleLines: { color: t.grid }, pointLabels: { color: t.muted, font: { size: 11 } }, ticks: { display: false } } },
      },
    });
    return track(c);
  }

  return { spark, area, barsH, bars, donut, gauge, heatmap, radar, disposeAll };
})();
