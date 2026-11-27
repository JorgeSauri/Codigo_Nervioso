/* SIM 4 — Tero et al. (2010): Poiseuille + adaptación de conductancia. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const MU = 1.5;
  const I0 = 0.012;
  const DT = 0.2;
  const IFLOW = 5;

  const cities = [
    { name: "Tokio", x: 0.54, y: 0.46 },
    { name: "Ueno", x: 0.58, y: 0.40 },
    { name: "Shinagawa", x: 0.50, y: 0.52 },
    { name: "Yokohama", x: 0.38, y: 0.56 },
    { name: "Kawasaki", x: 0.45, y: 0.54 },
    { name: "Chiba", x: 0.66, y: 0.50 },
    { name: "Ōmiya", x: 0.52, y: 0.26 },
    { name: "Tachikawa", x: 0.42, y: 0.38 },
    { name: "Funabashi", x: 0.62, y: 0.54 },
    { name: "Yokosuka", x: 0.34, y: 0.64 },
    { name: "Kashiwa", x: 0.68, y: 0.38 },
    { name: "Kawaguchi", x: 0.56, y: 0.30 },
    { name: "Hachiōji", x: 0.36, y: 0.42 },
    { name: "Kisarazu", x: 0.72, y: 0.56 },
    { name: "Ōfuna", x: 0.40, y: 0.62 },
    { name: "Maebashi", x: 0.48, y: 0.20 },
  ];

  const bay = [
    [0.30, 0.58], [0.38, 0.66], [0.50, 0.70], [0.62, 0.68], [0.74, 0.60], [0.78, 0.52],
  ];

  const RAIL_REF = [
    [0, 1], [0, 2], [1, 6], [6, 11], [11, 15], [1, 7], [7, 12],
    [0, 5], [5, 8], [5, 13], [2, 4], [4, 3], [3, 14], [3, 9],
    [2, 0], [6, 10], [10, 11],
  ];
  const railKeys = new Set(RAIL_REF.map(([a, b]) => (a < b ? `${a}-${b}` : `${b}-${a}`)));

  const COLS = 14;
  const ROWS = 9;
  const nodes = [];
  for (let y = 0; y < ROWS; y++) {
    for (let x = 0; x < COLS; x++) {
      nodes.push({
        x: 0.28 + x * (0.52 / (COLS - 1)),
        y: 0.16 + y * (0.56 / (ROWS - 1)),
      });
    }
  }
  const n = nodes.length;
  const edges = [];
  for (let i = 0; i < n; i++) {
    const x = i % COLS;
    const y = (i / COLS) | 0;
    for (let dy = -1; dy <= 1; dy++) {
      for (let dx = -1; dx <= 1; dx++) {
        if (!dx && !dy) continue;
        const xx = x + dx;
        const yy = y + dy;
        if (xx < 0 || yy < 0 || xx >= COLS || yy >= ROWS) continue;
        const j = yy * COLS + xx;
        if (i >= j) continue;
        const L = Math.max(0.02, Math.hypot(nodes[i].x - nodes[j].x, nodes[i].y - nodes[j].y));
        edges.push({ a: i, b: j, L, D: 0.45, Q: 0, phase: (i * 3 + j) * 0.01 });
      }
    }
  }
  const food = [];
  cities.forEach((c) => {
    let best = 0;
    let bd = 1e9;
    nodes.forEach((nd, i) => {
      const d = (nd.x - c.x) ** 2 + (nd.y - c.y) ** 2;
      if (d < bd) { bd = d; best = i; }
    });
    if (!food.includes(best)) food.push(best);
  });

  let pairIdx = 0;

  function edgeIndex(i, j) {
    if (i > j) [i, j] = [j, i];
    return edges.findIndex((e) => e.a === i && e.b === j);
  }

  function pressure(src, sink) {
    const p = new Float64Array(n);
    const adj = Array.from({ length: n }, () => []);
    edges.forEach((e) => {
      const k = e.D / e.L;
      adj[e.a].push({ j: e.b, k });
      adj[e.b].push({ j: e.a, k });
    });
    for (let it = 0; it < 70; it++) {
      const np = new Float64Array(n);
      for (let i = 0; i < n; i++) {
        if (i === sink) continue;
        let num = i === src ? IFLOW : 0;
        let den = 0;
        adj[i].forEach(({ j, k }) => { num += k * p[j]; den += k; });
        np[i] = den > 1e-12 ? num / den : 0;
      }
      p.set(np);
    }
    return p;
  }

  function physicsStep() {
    const src = food[pairIdx % food.length];
    const sink = food[(pairIdx + 6) % food.length];
    pairIdx++;
    if (src === sink) return;
    const p = pressure(src, sink);
    edges.forEach((e) => {
      const Q = (e.D / e.L) * (p[e.a] - p[e.b]);
      e.Q = Q;
      const drive = Math.pow(Math.abs(Q), MU) + I0 - e.D;
      e.D += DT * drive;
      e.D = Math.max(0.0001, Math.min(2, e.D));
    });
  }

  function curvePath(e, w, h) {
    const a = nodes[e.a];
    const b = nodes[e.b];
    const x1 = a.x * w;
    const y1 = a.y * h;
    const x2 = b.x * w;
    const y2 = b.y * h;
    const mx = (x1 + x2) * 0.5;
    const my = (y1 + y2) * 0.5;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const bulge = 0;
    const nx = -dy / len;
    const ny = dx / len;
    const cx = mx + nx * bulge;
    const cy = my + ny * bulge;
    return { x1, y1, cx, cy, x2, y2 };
  }

  function strokeTube(e, w, h, glow) {
    if (e.D < 0.06) return;
    const path = curvePath(e, w, h);
    const thick = 1.1 + Math.min(16, e.D * 9);
    const pulse = 0.85 + 0.15 * Math.sin(clock.frame * 0.12 + e.phase + Math.abs(e.Q) * 8);
    const alpha = (0.12 + Math.min(0.85, e.D * 1.8)) * pulse;
    ctx.beginPath();
    ctx.moveTo(path.x1, path.y1);
    ctx.quadraticCurveTo(path.cx, path.cy, path.x2, path.y2);
    ctx.strokeStyle = glow
      ? `rgba(255,220,90,${alpha * 0.25})`
      : `rgba(255,215,80,${alpha})`;
    ctx.lineWidth = glow ? thick * 2.3 : thick;
    ctx.lineCap = "round";
    ctx.stroke();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);

    ctx.strokeStyle = "rgba(100,140,170,0.22)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    bay.forEach((pt, i) => {
      const x = pt[0] * w;
      const y = pt[1] * h;
      i ? ctx.lineTo(x, y) : ctx.moveTo(x, y);
    });
    ctx.stroke();

    const sorted = edges.slice().sort((a, b) => a.D - b.D);
    sorted.forEach((e) => strokeTube(e, w, h, true));
    sorted.forEach((e) => strokeTube(e, w, h, false));

    cities.forEach((c) => {
      const x = c.x * w;
      const y = c.y * h;
      const r = c.name === "Tokio" ? 11 : 8;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r * 4.5);
      g.addColorStop(0, "rgba(255,230,120,0.45)");
      g.addColorStop(1, "rgba(255,230,120,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, r * 4, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(255,248,220,0.95)";
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "rgba(255,200,80,0.7)";
      ctx.lineWidth = 1.5;
      ctx.stroke();
      ctx.font = '11px "CN Inter"';
      ctx.fillStyle = CN.papel;
      ctx.fillText(c.name, x - 28, y - r - 6);
    });

    if (clock.frame > 640) {
      const fade = Math.min(1, (clock.frame - 640) / 160);
      ctx.setLineDash([9, 7]);
      ctx.lineWidth = 2.5;
      ctx.strokeStyle = `rgba(120,230,255,${0.75 * fade})`;
      RAIL_REF.forEach(([ia, ib]) => {
        const a = cities[ia];
        const b = cities[ib];
        ctx.beginPath();
        ctx.moveTo(a.x * w, a.y * h);
        ctx.lineTo(b.x * w, b.y * h);
        ctx.stroke();
      });
      ctx.setLineDash([]);
      ctx.font = '16px "CN Inter"';
      ctx.fillStyle = `rgba(180,230,255,${0.9 * fade})`;
      ctx.fillText("esquema aproximado · ferrocarril JR (referencia visual)", w * 0.04, h * 0.93);
    }

    vignette(ctx, w, h);

    const active = edges.filter((e) => e.D > 0.04).length;
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "dD/dt = |Q|ᵘ + I₀ − D  ·  flujo Poiseuille" }],
      counters: [
        { text: `μ=${MU} I₀=${I0} Δt=${DT} · nodos Kanto n=${n}` },
        { text: `tubos D>0.04: ${active} / ${edges.length}` },
      ],
      cite: "Tero, Takagi et al. (2010) Science 327:439–442",
    });
  }

  function stepOnce() {
    physicsStep();
    clock.tick();
    draw();
  }

  function verify() {
    const dense = edges.filter((e) => e.D > 0.08).length;
    return edges.length > 200 && dense > 15;
  }

  draw();

  CNCapture.boot({
    verify,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();