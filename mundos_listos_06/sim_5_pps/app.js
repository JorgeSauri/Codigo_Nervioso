/* SIM 5 — Primordial Particle Systems (Schmickl et al. 2016). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const P = { r: 5, alpha: Math.PI, beta: (17 * Math.PI) / 180, v: 0.67 };
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const W = 280;
  const H = 280;
  const scale = Math.min(opts.w, opts.h) / (W * 1.05);
  const ox = (opts.w - W * scale) / 2;
  const oy = (opts.h - H * scale) / 2;
  const rnd = mulberry32(opts.seed + 5);
  const N = Math.floor(0.09 * W * H);

  const parts = Array.from({ length: N }, () => ({
    x: rnd() * W,
    y: rnd() * H,
    a: rnd() * Math.PI * 2,
  }));

  function neighbors(p) {
    let l = 0;
    let r = 0;
    parts.forEach((q) => {
      if (q === p) return;
      const dx = q.x - p.x;
      const dy = q.y - p.y;
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
    ctx.globalCompositeOperation = "lighter";
    parts.forEach((p) => {
      const px = ox + p.x * scale;
      const py = oy + p.y * scale;
      const g = ctx.createRadialGradient(px, py, 0, px, py, 6);
      g.addColorStop(0, "rgba(0,229,199,0.9)");
      g.addColorStop(1, "rgba(0,229,199,0)");
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(px, py, 4.5, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "rgba(220,255,250,0.75)";
      ctx.beginPath();
      ctx.arc(px, py, 1.4, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalCompositeOperation = "source-over";
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Schmickl PPS: reglas locales α, β en vecindad r" }],
      counters: [
        { text: `N=${N} r=${P.r} α=180° β=17° v=${P.v}` },
      ],
      cite: "Schmickl et al. (2016) Sci. Rep. 6:37969",
    });
  }

  function stepOnce() { step(); draw(); }
  draw();
  CNCapture.boot({
    verify: () => parts.length > 500,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();