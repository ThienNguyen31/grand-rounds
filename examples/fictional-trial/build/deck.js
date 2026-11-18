/* Deck-specific figures for the NOVA-1 demo. Runs before the engine. */
(() => {
  const NS = 'http://www.w3.org/2000/svg';
  const el = (t, a, p) => { const e = document.createElementNS(NS, t); for (const k in a) e.setAttribute(k, a[k]); p && p.appendChild(e); return e; };
  const INT = '#C8372D', CTL = '#56677F', INK = '#1B2430', MUTED = '#66707C';
  // Adverse events, % of patients (claims.json c11; source p. 6, Table 3)
  const rows = [['Grade 3 or higher', 21.4, 19.5], ['Injection-site pain', 48.9, 9.1], ['Fever', 30.1, 6.3],
                ['Fatigue', 41.2, 33.8], ['Diarrhoea', 20.2, 18.8], ['Pruritus', 18.4, 16.0]];
  const svg = document.getElementById('dumb'); if (!svg) return;
  const X0 = 300, X1 = 960, MAX = 60, x = v => X0 + (X1 - X0) * v / MAX;
  [0, 20, 40, 60].forEach(v => { el('line', {x1: x(v), x2: x(v), y1: 40, y2: 540, stroke: '#E6E8EB', 'stroke-width': 2}, svg);
    el('text', {x: x(v), y: 26, 'font-size': 22, fill: MUTED, 'text-anchor': 'middle'}, svg).textContent = v + '%'; });
  rows.forEach(([name, a, b], i) => {
    const y = 90 + i * 84, d = (0.6 + i * 0.1).toFixed(2) + 's', d2 = (1.5 + i * 0.1).toFixed(2) + 's';
    el('text', {x: 0, y: y + 8, 'font-size': 26, fill: INK}, svg).textContent = name;
    const ln = el('line', {x1: x(Math.min(a, b)), x2: x(Math.max(a, b)), y1: y, y2: y, stroke: '#C4C8CD', 'stroke-width': 5, 'stroke-linecap': 'round', class: 'dfade'}, svg);
    ln.style.setProperty('--d', d2);
    [[b, CTL], [a, INT]].forEach(([v, c]) => { const ci = el('circle', {cx: x(v), cy: y, r: 13, fill: c, stroke: '#fff', 'stroke-width': 3, class: 'dmov'}, svg);
      ci.style.setProperty('--dx', (x(0) - x(v)) + 'px'); ci.style.setProperty('--d', d); });
    const ta = el('text', {x: x(Math.max(a, b)) + 22, y: y + 8, 'font-size': 24, 'font-weight': 700, fill: INT, class: 'dfade'}, svg);
    ta.textContent = a.toFixed(1); ta.style.setProperty('--d', d2);
    const tb = el('text', {x: x(Math.min(a, b)) - 22, y: y + 8, 'font-size': 22, fill: CTL, 'text-anchor': 'end', class: 'dfade'}, svg);
    tb.textContent = b.toFixed(1); tb.style.setProperty('--d', d2);
    if (Math.abs(a - b) < 4) { tb.setAttribute('x', x(Math.max(a, b)) + 90); tb.setAttribute('text-anchor', 'start'); }
  });
})();
