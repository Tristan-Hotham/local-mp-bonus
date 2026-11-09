/* The local MP bonus: every UK constituency 1832 to 2024 on a plain MapLibre base map (OpenFreeMap Positron), coloured by the
 * share of its MPs born within 25 km, with an era switch, search, layers and popups listing each seat's MPs.
 * Dr Tristan Hotham, Independent researcher, 2026. MIT licence. */
(function () {
  'use strict';
  const STYLE = 'https://tiles.openfreemap.org/styles/positron';
  const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  const norm = s => String(s).normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase();
  const small = matchMedia('(max-width:600px)').matches;
  const ERAS = { all: [1832, 2024, 'All years'], e1: [1832, 1917, '1832 to 1917'], e2: [1918, 1944, '1918 to 1944'], e3: [1945, 2009, '1945 to 2009'], e4: [2010, 2024, '2010 to 2024'] };
  const RAMP = [[0, '#F4E9DC'], [0.33, '#E9A66B'], [0.66, '#C2410C'], [1, '#6E2207']];
  let map, D, era = 'e4', feats = [], years = [];
  document.getElementById('theme').addEventListener('click', () => { const r = document.documentElement, d = r.dataset.theme ? r.dataset.theme === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches; r.dataset.theme = d ? 'light' : 'dark'; });
  const T = document.getElementById('title'); const fold = f => T.classList.toggle('folded', f);
  if (small) fold(true);
  document.getElementById('unfold').addEventListener('click', () => fold(false));
  document.getElementById('fold').addEventListener('click', () => fold(true));

  function bonusBox() {
    const b = window.BONUS[era];
    document.getElementById('bonusBox').innerHTML = `Local bonus, ${esc(ERAS[era][2])}: <span class="v">${b.b >= 0 ? '+' : ''}${b.b.toFixed(1)}</span> points<br><span style="color:#6B655B">95% CI ${b.lo.toFixed(1)} to ${b.hi.toFixed(1)}; ${b.local.toFixed(0)}% of MPs local</span>`;
  }

  function stats(si) {          // MPs of seat si within the era
    const [a, z] = ERAS[era]; let n = 0, l = 0, tot = 0;
    for (const r of D.bySeat[si]) { const y = years[r[1]]; if (y < a || y > z) continue; tot++; if (r[4] != null) { n++; if (r[4] <= 25) l++; } }
    return { n, l, tot };
  }

  function refresh() {
    for (const f of feats) { const s = stats(f.properties.i); f.properties.n = s.n; f.properties.tot = s.tot; f.properties.p = s.n ? s.l / s.n : -1; }
    map.getSource('s').setData({ type: 'FeatureCollection', features: feats });
    document.querySelectorAll('#eras .chip[data-era]').forEach(b => b.setAttribute('aria-pressed', b.dataset.era === era));
    bonusBox(); layerVis();
  }

  function layerVis() {
    const on = id => document.getElementById(id).checked;
    const f = ['all', ['>', ['get', 'tot'], 0]];
    const parts = [];
    if (on('lyS')) parts.push(['>=', ['get', 'p'], 0]);
    if (on('lyN')) parts.push(['<', ['get', 'p'], 0]);
    f.push(parts.length ? ['any', ...parts] : ['==', 1, 0]);
    map.setFilter('seats', f); map.setFilter('seats-halo', f); map.setFilter('seat-lbl', f);
    map.setLayoutProperty('seat-lbl', 'visibility', on('lyL') ? 'visible' : 'none');
    for (const l of map.getStyle().layers) if (l.type === 'symbol' && l.id !== 'seat-lbl') map.setLayoutProperty(l.id, 'visibility', on('lyB') ? 'visible' : 'none');
    document.getElementById('key').style.display = on('lyK') ? '' : 'none';
  }

  function popup(si, ll) {
    const s = D.seats[si], [a, z] = ERAS[era], st = stats(si);
    const rows = D.bySeat[si].filter(r => years[r[1]] >= a && years[r[1]] <= z);
    const tr = rows.map(r => { const km = r[4], loc = km != null && km <= 25;
      return `<tr><td>${esc(D.elections[r[1]])}</td><td>${esc(r[2])}<br><span class="nt">${esc(r[3] >= 0 ? D.fams[r[3]][1] : '')}</span></td><td class="r ${loc ? 'lc' : ''}">${km == null ? '<span class="nt">not known</span>' : km.toFixed(0) + ' km'}</td><td class="r">${r[5] == null ? '<span class="nt">unopp.</span>' : r[5].toFixed(1) + '%'}</td></tr>`; }).join('');
    const head = st.n ? `${st.l} of ${st.n} MPs with a known birthplace born within 25 km (${Math.round(100 * st.l / st.n)}%)` : 'No MP here with a known birthplace in this era';
    new maplibregl.Popup({ maxWidth: '350px' }).setLngLat(ll).setHTML(`<b class="t">${esc(s[0])}</b><div class="nt">${esc(s[3])} · ${esc(ERAS[era][2])}</div><div style="margin-top:4px">${head}</div>
      ${rows.length ? `<table><tr class="nt"><td>Election</td><td>MP</td><td class="r">Born</td><td class="r">Vote</td></tr>${tr}</table>` : ''}
      <div class="nt">Distance from birthplace to the seat point. Vote: the MP's share in the seat. Sources: Born and bred? and Who won here? (Wikidata, Wikipedia, UK Parliament and House of Commons Library). <a href="https://www.wikidata.org/wiki/${esc(s[4])}" target="_blank" rel="noopener">Wikidata ${esc(s[4])}</a></div>`).addTo(map);
  }

  function setup() {
    years = D.elections.map(e => +e.replace(/\D/g, '').slice(-4));
    D.bySeat = D.seats.map(() => []); for (const r of D.mps) D.bySeat[r[0]].push(r);
    feats = D.seats.map((s, i) => ({ type: 'Feature', properties: { i, name: s[0], p: -1, n: 0, tot: 0 }, geometry: { type: 'Point', coordinates: [s[1], s[2]] } }));
    const before = (map.getStyle().layers.find(l => l.type === 'symbol') || {}).id;
    map.addSource('s', { type: 'geojson', data: { type: 'FeatureCollection', features: feats }, attribution: 'Seats and MPs: Born and bred?, Who won here? (Wikidata, Wikipedia, UK Parliament)' });
    const col = ['case', ['<', ['get', 'p'], 0], '#BDB7AD', ['interpolate', ['linear'], ['get', 'p'], ...RAMP.flat()]];
    const rad = e => ['interpolate', ['linear'], ['zoom'], 4, ['+', 3 + e, ['*', 0.5, ['sqrt', ['get', 'n']]]], 8, ['+', 5.5 + e, ['*', 0.9, ['sqrt', ['get', 'n']]]], 12, ['+', 9 + e, ['sqrt', ['get', 'n']]]];
    map.addLayer({ id: 'seats-halo', type: 'circle', source: 's', paint: { 'circle-radius': rad(1.5), 'circle-color': '#fff', 'circle-opacity': 0.9 } }, before);
    map.addLayer({ id: 'seats', type: 'circle', source: 's', paint: { 'circle-radius': rad(0), 'circle-color': col, 'circle-stroke-color': '#6B655B', 'circle-stroke-width': 0.5, 'circle-opacity': 0.95 } }, before);
    map.addLayer({ id: 'seat-lbl', type: 'symbol', source: 's', minzoom: 7.5, layout: { 'text-field': ['get', 'name'], 'text-size': 11, 'text-font': ['Noto Sans Regular'], 'text-offset': [0, 1.1], 'text-anchor': 'top', 'text-optional': true }, paint: { 'text-color': '#4A453D', 'text-halo-color': '#fff', 'text-halo-width': 1.3 } });
    map.on('click', 'seats', e => { const f = e.features[0]; popup(f.properties.i, f.geometry.coordinates); });
    map.on('mouseenter', 'seats', () => map.getCanvas().style.cursor = 'pointer'); map.on('mouseleave', 'seats', () => map.getCanvas().style.cursor = '');
    document.querySelectorAll('#eras .chip[data-era]').forEach(b => b.addEventListener('click', () => { era = b.dataset.era; refresh(); }));
    const lp = document.getElementById('lp'), btn = document.getElementById('lyrBtn');
    btn.addEventListener('click', e => { e.stopPropagation(); const o = lp.classList.toggle('open'); btn.setAttribute('aria-expanded', o); });
    document.addEventListener('click', e => { if (!lp.contains(e.target) && e.target !== btn) { lp.classList.remove('open'); btn.setAttribute('aria-expanded', false); } });
    ['lyS', 'lyN', 'lyL', 'lyB', 'lyK'].forEach(id => document.getElementById(id).addEventListener('change', layerVis));
    refresh();
  }

  function setupSearch() {
    const q = document.getElementById('q'), sug = document.getElementById('sug'); let items = [], k = -1;
    const idx = D.seats.map((s, i) => ({ n: s[0], nn: norm(s[0]), i, c: D.bySeat[i].length, y0: years[(D.bySeat[i][0] || [0, 0])[1]], y1: years[(D.bySeat[i][D.bySeat[i].length - 1] || [0, 0])[1]] }));
    const show = () => { const v = norm(q.value.trim()); sug.innerHTML = ''; k = -1; if (v.length < 2) { sug.style.display = 'none'; return; }
      items = idx.filter(x => x.nn.startsWith(v)).concat(idx.filter(x => !x.nn.startsWith(v) && x.nn.includes(v))).slice(0, 12);
      items.forEach((it, j) => { const li = document.createElement('li'); li.setAttribute('role', 'option'); li.innerHTML = `${esc(it.n)} <span>${it.y0} to ${it.y1}</span>`; li.addEventListener('mousedown', e => { e.preventDefault(); pick(j); }); sug.appendChild(li); });
      sug.style.display = items.length ? 'block' : 'none'; };
    const pick = j => { const it = items[j]; if (!it) return; q.value = it.n; sug.style.display = 'none'; fold(true);
      const s = D.seats[it.i]; const ys = D.bySeat[it.i].map(r => years[r[1]]);
      if (!ys.some(y => y >= ERAS[era][0] && y <= ERAS[era][1])) { era = 'all'; refresh(); }
      map.flyTo({ center: [s[1], s[2]], zoom: 9, duration: 1200 }); map.once('moveend', () => popup(it.i, [s[1], s[2]])); };
    q.addEventListener('input', show);
    q.addEventListener('keydown', e => { const lis = [...sug.children];
      if (e.key === 'ArrowDown' || e.key === 'ArrowUp') { e.preventDefault(); k = Math.max(0, Math.min(lis.length - 1, k + (e.key === 'ArrowDown' ? 1 : -1))); lis.forEach((l, i) => l.setAttribute('aria-selected', i === k)); }
      else if (e.key === 'Enter') { e.preventDefault(); if (!items.length) show(); pick(k < 0 ? 0 : k); } else if (e.key === 'Escape') sug.style.display = 'none'; });
    q.addEventListener('blur', () => setTimeout(() => sug.style.display = 'none', 150));
  }

  fetch('data/seats.json').then(r => r.json()).then(d => {
    D = d;
    const m0 = new maplibregl.Map({ container: 'map', style: STYLE, attributionControl: { compact: true }, maxZoom: 14, renderWorldCopies: false,
      center: small ? [-3.2, 54.6] : [-4.2, 54.4], zoom: small ? 4.4 : 5.2 });
    return new Promise((res, rej) => { m0.once('load', () => res(m0)); m0.once('error', e => { if (!m0.loaded()) rej(e.error || e); }); });
  }).then(mm => {
    map = mm; window.__map = mm;
    mm.on('error', e => { const er = e && e.error; if (er && (er.name === 'AbortError' || /abort/i.test(er.message || ''))) return; console.error(er || e); });
    const n = document.getElementById('nojs'); if (n) n.remove();
    mm.addControl(new maplibregl.NavigationControl({ showCompass: false }), 'bottom-right');
    const foldAt = () => document.querySelectorAll('.maplibregl-ctrl-attrib.maplibregl-compact').forEach(at => { at.classList.remove('maplibregl-compact-show'); at.removeAttribute('open'); });
    mm.once('idle', foldAt); setTimeout(foldAt, 1500);
    setup(); setupSearch();
  }).catch(e => { console.error(e); const n = document.getElementById('nojs'); if (n) n.textContent = 'The map could not load: ' + e.message; });
})();
