/* ============================================================================
   VPID — Interactive territorial map (Leaflet).
   Circle markers sized by article volume, colored by average sentiment.
   ============================================================================ */
VPID.maps = (function () {
  let map = null;

  function sentColor(s) {
    if (s > 0.1) return '#34d399';
    if (s < -0.1) return '#fb7185';
    return '#fbbf24';
  }
  function radius(articulos, max) { return 8 + (articulos / max) * 34; }

  function render(elId, rows, opts = {}) {
    dispose();
    const el = document.getElementById(elId);
    if (!el || !window.L) return;

    map = L.map(elId, { zoomControl: true, scrollWheelZoom: false, attributionControl: false })
      .setView(opts.center || [8.4, -68.0], opts.zoom || 6);

    L.tileLayer('https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png', {
      maxZoom: 19, subdomains: 'abcd',
    }).addTo(map);

    const max = Math.max(...rows.map(r => r.articulos), 1);
    rows.forEach(r => {
      if (r.lat == null || r.lon == null) return;
      const m = L.circleMarker([r.lat, r.lon], {
        radius: radius(r.articulos, max),
        fillColor: sentColor(r.sent ?? r.sentimiento_prom ?? 0),
        color: '#fff', weight: 1.2, fillOpacity: 0.75,
      }).addTo(map);
      const s = r.sent ?? r.sentimiento_prom ?? 0;
      m.bindPopup(
        `<div style="min-width:180px">
           <div style="font-weight:700;margin-bottom:4px">${r.estado}</div>
           <div style="font-size:12px;opacity:.8">Artículos (30d): <b>${VPID.fmt.num(r.articulos)}</b></div>
           <div style="font-size:12px;opacity:.8">Sentimiento medio: <b>${VPID.fmt.score(s)}</b></div>
         </div>`
      );
      m.on('mouseover', function () { this.openPopup(); });
    });

    // Legend
    const legend = L.control({ position: 'bottomright' });
    legend.onAdd = function () {
      const div = L.DomUtil.create('div');
      div.style.cssText = 'background:var(--elev);color:var(--text);padding:8px 10px;border-radius:8px;border:1px solid var(--border);font-size:11px;line-height:1.6';
      div.innerHTML = `<b>Sentimiento</b><br>
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#34d399"></span> Positivo
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#fbbf24;margin-left:6px"></span> Neutral
        <span style="display:inline-block;width:10px;height:10px;border-radius:50%;background:#fb7185;margin-left:6px"></span> Negativo
        <br><span style="opacity:.7">Tamaño ∝ volumen de cobertura</span>`;
      return div;
    };
    legend.addTo(map);

    setTimeout(() => map && map.invalidateSize(), 200);
    return map;
  }

  function dispose() { if (map) { try { map.remove(); } catch (e) {} map = null; } }

  return { render, dispose };
})();
