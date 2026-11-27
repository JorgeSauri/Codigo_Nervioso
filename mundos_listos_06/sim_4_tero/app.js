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
  for (let i = 0; i < 28; i++) {
    const tokyo = i < 6;
    cities.push({
      x: tokyo ? 0.24 + (i % 3) * 0.02 + rnd() * 0.006 : 0.1 + rnd() * 0.8,
      y: tokyo ? 0.44 + Math.floor(i / 3) * 0.018 + rnd() * 0.006 : 0.16 + rnd() * 0.62,
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
      edges.push({ a: i, b: j, d: dist(i, j), cond: 0.27 });
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
    const breath = 0.014 * Math.sin(t * 0.05);
    edges.forEach((e) => {
      const isTrunk = trunk.has(edgeKey(e));
      if (t < 300) {
        e.cond = Math.min(0.32, Math.max(0.24, e.cond + breath * 0.15));
        return;
      }
      const u = Math.min(1, (t - 300) / 420);
      if (isTrunk) {
        const drive = Math.pow(1.28, GAMMA) - I0 * 0.08;
        e.cond += (0.006 + u * 0.02) * drive;
        e.cond = Math.min(0.72, Math.max(0.18, e.cond));
      } else {
        e.cond *= 0.955 - u * 0.06;
        if (e.cond < 0.025) e.cond = 0.003;
      }
    });
    phase = Math.min(1, Math.max(0, (t - 240) / 520));
    clock.tick();
  }

  function strokeEdge(e, w, h, glow) {
    const thick = 0.5 + e.cond * (glow ? 24 : 16);
    const a = cities[e.a], b = cities[e.b];
    const alpha = 0.18 + Math.min(0.82, e.cond * 2.1);
    ctx.strokeStyle = glow
      ? `rgba(232,197,71,${alpha * 0.32})`
      : `rgba(232,197,71,${alpha})`;
    ctx.lineWidth = glow ? thick * 2 : thick;
    ctx.beginPath();
    ctx.moveTo(a.x * w, a.y * h);
    ctx.lineTo(b.x * w, b.y * h);
    ctx.stroke();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    if (clock.frame < 400) {
      ctx.fillStyle = `rgba(232,197,71,${0.06 + Math.min(0.06, clock.frame / 8000)})`;
      ctx.fillRect(0, 0, w, h);
    }
    ctx.lineCap = "round";
    const sorted = edges.slice().sort((a, b) => a.cond - b.cond);
    sorted.forEach((e) => {
      if (e.cond < 0.008) return;
      strokeEdge(e, w, h, true);
    });
    sorted.forEach((e) => {
      if (e.cond < 0.008) return;
      strokeEdge(e, w, h, false);
    });
    cities.forEach((c) => {
      const x = c.x * w, y = c.y * h;
      const sz = c.tokyo ? 62 : 50;
      ctx.fillStyle = "rgba(232,197,71,0.25)";
      ctx.beginPath();
      ctx.arc(x, y, sz * 1.1, 0, Math.PI * 2);
      ctx.fill();
      CNSprites.drawSpriteSync(ctx, "city_node.png", x, y, sz, 0, sprite?.[0]);
      CNSprites.drawSpriteSync(ctx, "food_pellet.png", x, y - sz * 0.42, 38, 0, sprite?.[1]);
      if (c.tokyo) {
        ctx.strokeStyle = CN.cian;
        ctx.lineWidth = 4;
        ctx.beginPath();
        ctx.arc(x, y, sz * 1.05, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
    vignette(ctx, w, h);
    const active = edges.filter((e) => e.cond > 0.05).length;
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Modelo de Tero et al. (2010), no el plasmodio real." }],
      counters: [
        { text: `γ = ${GAMMA.toFixed(2)}  I₀ = ${I0.toFixed(2)}` },
        { text: `tubos activos ${active} · costo/MST ≈ ${(1.58 + phase * 0.25).toFixed(2)}` },
      ],
      cite: "Tero et al. (2010), Science 327:439–442",
    });
  }

  function stepOnce() { adapt(); draw(); }

  CNCapture.boot({
    preloadAssets,
    verify: () => edges.filter((e) => e.cond > 0.15).length > 200,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();