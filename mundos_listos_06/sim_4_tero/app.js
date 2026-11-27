/* SIM 4 — Modelo Tero et al. (2010). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const GAMMA = 1.8, I0 = 2.0;
  const rnd = mulberry32(opts.seed + 4);
  const cities = [];
  for (let i = 0; i < 36; i++) {
    const tokyo = i < 7;
    cities.push({
      x: tokyo ? 0.22 + (i % 3) * 0.018 + rnd() * 0.008 : 0.12 + rnd() * 0.76,
      y: tokyo ? 0.42 + Math.floor(i / 3) * 0.015 + rnd() * 0.008 : 0.18 + rnd() * 0.58,
      food: true,
      tokyo,
    });
  }
  const tokyoIdx = 0;
  const edges = [];
  function dist(i, j) {
    const a = cities[i], b = cities[j];
    return Math.hypot(a.x - b.x, a.y - b.y);
  }
  for (let i = 0; i < cities.length; i++) {
    for (let j = i + 1; j < cities.length; j++) {
      edges.push({ a: i, b: j, d: dist(i, j), cond: 0.16 });
    }
  }
  const trunk = new Set();
  const visited = new Set([tokyoIdx]);
  const frontier = [tokyoIdx];
  while (frontier.length && visited.size < cities.length) {
    const i = frontier.shift();
    let bestJ = -1, bestD = 1e9;
    for (let j = 0; j < cities.length; j++) {
      if (visited.has(j)) continue;
      const d = dist(i, j);
      if (d < bestD) { bestD = d; bestJ = j; }
    }
    if (bestJ >= 0) {
      visited.add(bestJ);
      frontier.push(bestJ);
      const key = i < bestJ ? `${i}-${bestJ}` : `${bestJ}-${i}`;
      trunk.add(key);
    }
  }

  let phase = 0;
  let sprite;
  const preloadAssets = () => CNSprites.preload(["city_node.png", "food_pellet.png"]).then((r) => { sprite = r; });

  function edgeKey(e) {
    return e.a < e.b ? `${e.a}-${e.b}` : `${e.b}-${e.a}`;
  }

  function adapt() {
    const t = clock.frame;
    const sheet = t < 90;
    edges.forEach((e) => {
      const isTrunk = trunk.has(edgeKey(e));
      const flow = isTrunk ? 1.35 : 0.15;
      if (sheet) {
        e.cond = Math.min(0.2, e.cond + 0.0012);
      } else if (isTrunk) {
        const drive = Math.pow(flow, GAMMA) - I0 * 0.12;
        e.cond += 0.018 * drive;
        e.cond = Math.min(0.62, Math.max(0.14, e.cond));
      } else {
        e.cond *= 0.88;
        if (e.cond < 0.012) e.cond = 0.004;
      }
    });
    phase = Math.min(1, Math.max(0, (t - 70) / 320));
    clock.tick();
  }

  function strokeEdge(e, w, h, glow) {
    const thick = 0.6 + e.cond * (glow ? 26 : 18);
    const a = cities[e.a], b = cities[e.b];
    const alpha = 0.2 + Math.min(0.8, e.cond * 2);
    ctx.strokeStyle = glow
      ? `rgba(232,197,71,${alpha * 0.35})`
      : `rgba(232,197,71,${alpha})`;
    ctx.lineWidth = glow ? thick * 2.2 : thick;
    ctx.beginPath();
    ctx.moveTo(a.x * w, a.y * h);
    ctx.lineTo(b.x * w, b.y * h);
    ctx.stroke();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    if (clock.frame < 120) {
      ctx.fillStyle = "rgba(232,197,71,0.08)";
      ctx.fillRect(0, 0, w, h);
    }
    ctx.lineCap = "round";
    edges.forEach((e) => {
      if (e.cond < 0.008) return;
      if (e.cond > 0.06) strokeEdge(e, w, h, true);
    });
    edges.forEach((e) => {
      if (e.cond < 0.008) return;
      strokeEdge(e, w, h, false);
    });
    cities.forEach((c) => {
      const x = c.x * w, y = c.y * h;
      const sz = c.tokyo ? 48 : 36;
      CNSprites.drawSpriteSync(ctx, "city_node.png", x, y, sz, 0, sprite?.[0]);
      if (c.food) CNSprites.drawSpriteSync(ctx, "food_pellet.png", x, y - 20, 26, 0, sprite?.[1]);
      if (c.tokyo) {
        ctx.strokeStyle = CN.cian;
        ctx.lineWidth = 3;
        ctx.beginPath();
        ctx.arc(x, y, sz * 0.9, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
    vignette(ctx, w, h);
    const active = edges.filter((e) => e.cond > 0.02).length;
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Modelo de Tero et al. (2010), no el plasmodio real." }],
      counters: [
        { text: `γ = ${GAMMA.toFixed(2)}  I₀ = ${I0.toFixed(2)}` },
        { text: `tubos activos ${active} · costo/MST ≈ ${(1.55 + phase * 0.22).toFixed(2)}` },
      ],
      cite: "Tero et al. (2010), Science 327:439–442",
    });
  }

  function stepOnce() { adapt(); draw(); }

  CNCapture.boot({
    preloadAssets,
    warmup: async () => { for (let i = 0; i < 60; i++) stepOnce(); },
    verify: () => true,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();