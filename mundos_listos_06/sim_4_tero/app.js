/* SIM 4 — Tero et al. (2010): Poiseuille + adaptación de conductancia. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const MU = 1.8;
  const I0 = 0.14;
  const DT = 0.22;
  const QSCALE = 180;

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

  const n = cities.length;
  const dist = (i, j) => Math.hypot(cities[i].x - cities[j].x, cities[i].y - cities[j].y);
  const edges = [];
  const bend = new Float32Array(6000);
  let ei = 0;
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      const key = `${i}-${j}`;
      const onRail = railKeys.has(key);
      edges.push({
        a: i, b: j, L: dist(i, j),
        D: 0.38,
        Q: 0,
        phase: (ei % 17) * 0.37,
        rail: onRail,
      });
      bend[ei++] = ((i * 17 + j * 7) % 100) / 100 - 0.5;
    }
  }

  let pairIdx = 0;
  const food = cities.map((_, i) => i);

  function edgeIndex(i, j) {
    if (i > j) [i, j] = [j, i];
    return edges.findIndex((e) => e.a === i && e.b === j);
  }

  function pressure(src, sink) {
    const p = new Float64Array(n).fill(0.5);
    p[src] = 1;
    p[sink] = 0;
    const fixed = new Set([src, sink]);
    const adj = Array.from({ length: n }, () => []);
    edges.forEach((e) => {
      const k = e.D / (e.L + 1e-6);
      adj[e.a].push({ j: e.b, k });
      adj[e.b].push({ j: e.a, k });
    });
    for (let it = 0; it < 100; it++) {
      for (let i = 0; i < n; i++) {
        if (fixed.has(i)) continue;
        let num = 0;
        let den = 0;
        adj[i].forEach(({ j, k }) => {
          num += k * p[j];
          den += k;
        });
        if (den > 1e-12) p[i] = num / den;
      }
      p[src] = 1;
      p[sink] = 0;
    }
    return p;
  }

  function physicsStep() {
    const src = food[pairIdx % food.length];
    const sink = food[(pairIdx + 1) % food.length];
    pairIdx++;
    const p = pressure(src, sink);
    edges.forEach((e) => {
      const Q = (e.D / (e.L + 1e-6)) * (p[e.a] - p[e.b]);
      e.Q = Q;
      const drive = Math.pow(Math.abs(Q) * QSCALE + 1e-8, MU) + I0 - e.D;
      e.D += DT * drive;
      e.D = Math.max(0.001, Math.min(0.95, e.D));
    });
  }

  function curvePath(e, w, h) {
    const a = cities[e.a];
    const b = cities[e.b];
    const x1 = a.x * w;
    const y1 = a.y * h;
    const x2 = b.x * w;
    const y2 = b.y * h;
    const mx = (x1 + x2) * 0.5;
    const my = (y1 + y2) * 0.5;
    const dx = x2 - x1;
    const dy = y2 - y1;
    const len = Math.hypot(dx, dy) || 1;
    const bulge = e.phase * (28 + 40 * e.D);
    const nx = -dy / len;
    const ny = dx / len;
    const cx = mx + nx * bulge;
    const cy = my + ny * bulge;
    return { x1, y1, cx, cy, x2, y2 };
  }

  function strokeTube(e, w, h, glow) {
    if (e.D < 0.015) return;
    const path = curvePath(e, w, h);
    const thick = 1.2 + Math.pow(e.D, 0.55) * 22;
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
    return dense > 80;
  }

  draw();

  CNCapture.boot({
    verify,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();