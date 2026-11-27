/* SIM 5 — Primordial Particle Systems (Schmickl et al. 2016). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const P = { r: 5, alpha: Math.PI, beta: (17 * Math.PI) / 180, v: 0.67, source: "Schmickl et al. (2016) Sci. Rep. 6:37969" };
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const W = 250, H = 250;
  const scale = Math.min(opts.w, opts.h) / (W * 1.1);
  const ox = (opts.w - W * scale) / 2;
  const oy = (opts.h - H * scale) / 2;
  const rnd = mulberry32(opts.seed + 5);
  const N = Math.floor(0.08 * W * H);
  const parts = Array.from({ length: N }, () => ({
    x: rnd() * W,
    y: rnd() * H,
    a: rnd() * Math.PI * 2,
  }));

  function neighbors(p) {
    let l = 0, r = 0;
    parts.forEach((q) => {
      if (q === p) return;
      const dx = q.x - p.x, dy = q.y - p.y;
      const d = Math.hypot(dx, dy);
      if (d > P.r || d < 0.01) return;
      const ang = Math.atan2(dy, dx) - p.a;
      const na = ((ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
      if (na > 0) r++;
      else l++;
    });
    return { l, r };
  }

  function step() {
    parts.forEach((p) => {
      const { l, r } = neighbors(p);
      let dA = 0;
      if (l === 0 && r > 0) dA = -P.alpha;
      else if (r === 0 && l > 0) dA = P.alpha;
      else if (l > 0 && r > 0) dA = (r - l) * P.beta;
      p.a += dA;
      p.x = (p.x + Math.cos(p.a) * P.v + W) % W;
      p.y = (p.y + Math.sin(p.a) * P.v + H) % H;
    });
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const grid = new Map();
    parts.forEach((p) => {
      const key = `${(p.x / 8) | 0},${(p.y / 8) | 0}`;
      grid.set(key, (grid.get(key) || 0) + 1);
    });
    parts.forEach((p) => {
      const dense = (grid.get(`${(p.x / 8) | 0},${(p.y / 8) | 0}`) || 0) > 6;
      ctx.fillStyle = dense ? CN.coral : CN.papel;
      if (!dense) ctx.shadowColor = CN.cian;
      ctx.shadowBlur = dense ? 6 : 2;
      ctx.beginPath();
      ctx.arc(ox + p.x * scale, oy + p.y * scale, dense ? 3.2 : 2.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.shadowBlur = 0;
    });
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: 'Estructuras tipo "cell" (término de los autores)' }],
      counters: [
        { text: `N = ${N}` },
        { text: `r=${P.r} α=180° β=17° v=${P.v}` },
      ],
      cite: P.source,
    });
  }

  function stepOnce() { step(); draw(); }
  CNCapture.boot({ runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();