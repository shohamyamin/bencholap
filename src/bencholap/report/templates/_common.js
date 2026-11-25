// Shared helpers: formatting, colors and sortable / filterable tables.
const BL = (() => {
  const COLORS = ['#4c6ef5', '#f59f00', '#12b886', '#e64980', '#7950f2', '#15aabf', '#fa5252', '#82c91e'];
  const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[c]));
  function fmt(v, kind) {
    if (v === null || v === undefined || Number.isNaN(v)) return '–';
    if (kind === 'time') {
      if (v >= 60000) return (v / 60000).toFixed(1) + ' min';
      if (v >= 1000) return (v / 1000).toFixed(v >= 10000 ? 1 : 2) + ' s';
      return v.toFixed(v < 10 ? 1 : 0) + ' ms';
    }
    if (kind === 'bytes') {
      for (const [u, s] of [['TB', 1e12], ['GB', 1e9], ['MB', 1e6], ['kB', 1e3]]) if (v >= s) return (v / s).toFixed(1) + ' ' + u;
      return v.toFixed(0) + ' B';
    }
    if (kind === 'count') {
      for (const [u, s] of [['B', 1e9], ['M', 1e6], ['k', 1e3]]) if (v >= s) return (v / s).toFixed(1) + u;
      return Math.round(v).toString();
    }
    return String(v);
  }
  function pct(r) { return r === null || r === undefined ? null : (r - 1) * 100; }
  function delta(ratio, significant, threshold = 0.02) {
    if (!ratio && ratio !== 0) return '<span class="delta same">–</span>';
    const p = pct(ratio);
    const cls = Math.abs(ratio - 1) < threshold ? 'same' : (ratio < 1 ? 'down' : 'up');
    const strong = significant ? '' : ' style="opacity:.55"';
    return `<span class="delta ${cls}"${strong}>${p > 0 ? '+' : ''}${p.toFixed(1)}%</span>`;
  }
  // Click-to-sort tables: <th class="sortable" data-key="..." data-type="num|text">
  function sortable(table, rows, render, initial) {
    let key = initial?.key, asc = initial?.asc ?? true;
    const ths = table.querySelectorAll('th.sortable');
    function draw() {
      const data = rows();
      if (key) {
        const th = table.querySelector(`th[data-key="${key}"]`);
        const num = th?.dataset.type === 'num';
        data.sort((a, b) => {
          let x = a._sort?.[key] ?? a[key], y = b._sort?.[key] ?? b[key];
          if (num) { x = x ?? (asc ? Infinity : -Infinity); y = y ?? (asc ? Infinity : -Infinity); return asc ? x - y : y - x; }
          return asc ? String(x ?? '').localeCompare(String(y ?? ''), undefined, {numeric: true}) : String(y ?? '').localeCompare(String(x ?? ''), undefined, {numeric: true});
        });
      }
      ths.forEach(t => { t.classList.toggle('sorted', t.dataset.key === key); t.classList.toggle('asc', t.dataset.key === key && asc); });
      table.querySelector('tbody').innerHTML = data.length ? data.map(render).join('') : `<tr><td colspan="99" class="empty">Nothing matches the filters.</td></tr>`;
    }
    ths.forEach(t => t.addEventListener('click', () => { if (key === t.dataset.key) asc = !asc; else { key = t.dataset.key; asc = t.dataset.type !== 'num' || t.dataset.asc === '1'; } draw(); }));
    return draw;
  }
  function chart(el, cfg) {
    if (typeof Chart === 'undefined') { el.innerHTML = '<div class="empty small">Charts need network access to load Chart.js.</div>'; return null; }
    if (el._chart) el._chart.destroy();
    const canvas = document.createElement('canvas'); el.innerHTML = ''; el.appendChild(canvas);
    el._chart = new Chart(canvas, cfg); return el._chart;
  }
  if (typeof Chart !== 'undefined') {
    Chart.defaults.font.family = 'Inter, -apple-system, Segoe UI, Roboto, sans-serif';
    Chart.defaults.color = '#495065';
    Chart.defaults.plugins.legend.labels.boxWidth = 12;
  }
  return {COLORS, esc, fmt, pct, delta, sortable, chart};
})();
