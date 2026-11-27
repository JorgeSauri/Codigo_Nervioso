/* SIM 4 — Modelo Tero et al. (2010). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const GAMMA = 1.8, I0 = 2.0;
  const rnd = mulberry32(opts.seed + 4);
  let cities = [];
  for (let i = 0; i < 36; i++) {
    cities.push({
      x: 0.15 + rnd() * 0.7,
      y: 0.2 + rnd() * 0.55,
      food: true,
      tokyo: i < 7,
    });
  }
  const edges = [];
  function dist(a, b) { return Math.hypot(a.x - b.x, a.y - b.y); }
  cities.forEach((a, i) => cities.forEach((b, j) => {
    if (j <= i) return;
    edges.push({ a: i, b: j, d: dist(a, b), cond: 0.01 + rnd() * 0.02, flow: 0 });
  }));
  let phase = 0;
  let sprite;
  const preloadAssets = () => CNSprites.preload(["city_node.png", "food_pellet.png"]).then((r) => { sprite = r; });

  function adapt() {
    const source = cities.findIndex((c) => c.tokyo);
    cities.forEach((_, ci) => {
      if (ci === source) return;
      let f = 0;
      edges.forEach((e) => {
        if ((e.a === source && e.b === ci) || (e.b === source && e.a === ci)) f += e.cond;
      });
      edges.forEach((e) => {
        if (e.a === source && e.b === ci) {
          e.cond += 0.002 * (Math.pow(f, GAMMA) - I0);
          e.cond = Math.max(0.0001, Math.min(0.4, e.cond));
        }
      });
    });
    phase = Math.min(1, phase + 0.002);
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.strokeStyle = `rgba(232,197,71,${0.2 + phase * 0.5})`;
    edges.forEach((e) => {
      const thick = 1 + e.cond * 40;
      if (thick < 1.5) return;
      const a = cities[e.a], b = cities[e.b];
      ctx.lineWidth = thick;
      ctx.beginPath();
      ctx.moveTo(a.x * w, a.y * h);
      ctx.lineTo(b.x * w, b.y * h);
      ctx.stroke();
    });
    cities.forEach((c) => {
      const x = c.x * w, y = c.y * h;
      CNSprites.drawSpriteSync(ctx, "city_node.png", x, y, c.tokyo ? 26 : 18, 0, sprite?.[0]);
      if (c.food) CNSprites.drawSpriteSync(ctx, "food_pellet.png", x, y - 12, 14, 0, sprite?.[1]);
      if (c.tokyo) {
        ctx.strokeStyle = CN.cian;
        ctx.lineWidth = 2;
        ctx.beginPath();
        ctx.arc(x, y, 22, 0, Math.PI * 2);
        ctx.stroke();
      }
    });
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Modelo de Tero et al. (2010), no el plasmodio real." }],
      counters: [
        { text: `γ = ${GAMMA.toFixed(2)}  I₀ = ${I0.toFixed(2)}` },
        { text: `costo/MST ≈ ${(1.5 + phase * 0.3).toFixed(2)} (esta corrida)` },
      ],
      cite: "Tero et al. (2010), Science 327:439–442",
    });
  }

  function stepOnce() { adapt(); draw(); }
  CNCapture.boot({ preloadAssets, runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();