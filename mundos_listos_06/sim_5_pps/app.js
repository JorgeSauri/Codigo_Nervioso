/* SIM 5 — PPS Schmickl et al. 2016, α=180° β=17°. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const P = { r: 5, alpha: Math.PI, beta: (17 * Math.PI) / 180, v: 0.67 };
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const W = 360;
  const H = 200;
  const rnd = mulberry32(opts.seed + 5);
  const N = 7000;
  const parts = Array.from({ length: N }, () => ({
    x: rnd() * W,
    y: rnd() * H,
    a: rnd() * Math.PI * 2,
  }));
  for (let k = 0; k < 900; k++) {
    const a = rnd() * Math.PI * 2;
    const rad = rnd() * 18;
    parts[k].x = W * 0.35 + Math.cos(a) * rad;
    parts[k].y = H * 0.5 + Math.sin(a) * rad;
  }

  function step() {
    const cols = Math.ceil(W / P.r);
    const rows = Math.ceil(H / P.r);
    const buckets = Array.from({ length: cols * rows }, () => []);
    parts.forEach((p, i) => {
      const cx = Math.min(cols - 1, (p.x / P.r) | 0);
      const cy = Math.min(rows - 1, (p.y / P.r) | 0);
      buckets[cy * cols + cx].push(i);
    });
    const nextA = new Float32Array(N);
    parts.forEach((p, i) => {
      let l = 0;
      let r = 0;
      const cx = Math.min(cols - 1, (p.x / P.r) | 0);
      const cy = Math.min(rows - 1, (p.y / P.r) | 0);
      for (let oy = -1; oy <= 1; oy++) {
        for (let ox = -1; ox <= 1; ox++) {
          const nx = cx + ox;
          const ny = cy + oy;
          if (nx < 0 || ny < 0 || nx >= cols || ny >= rows) continue;
          const list = buckets[ny * cols + nx];
          for (let k = 0; k < list.length; k++) {
            const q = parts[list[k]];
            if (q === p) continue;
            const dx = q.x - p.x;
            const dy = q.y - p.y;
            const d = Math.hypot(dx, dy);
            if (d > P.r || d < 0.01) continue;
            const ang = Math.atan2(dy, dx) - p.a;
            const na = ((ang + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
            if (na > 0) r++;
            else l++;
          }
        }
      }
      let dA = 0;
      if (l === 0 && r > 0) dA = -P.alpha;
      else if (r === 0 && l > 0) dA = P.alpha;
      else if (l > 0 && r > 0) dA = (r - l) * P.beta;
      nextA[i] = p.a + dA;
    });
    parts.forEach((p, i) => {
      p.a = nextA[i];
      p.x = (p.x + Math.cos(p.a) * P.v + W) % W;
      p.y = (p.y + Math.sin(p.a) * P.v + H) % H;
    });
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    const scale = Math.min((w * 0.92) / W, (h * 0.82) / H);
    const ox = (w - W * scale) / 2;
    const oy = (h - H * scale) / 2;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    parts.forEach((p) => {
      ctx.fillStyle = "rgba(0,229,199,0.85)";
      ctx.fillRect(ox + p.x * scale, oy + p.y * scale, 2.2, 2.2);
    });
    ctx.globalCompositeOperation = "source-over";
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "PPS: si un lado vacío gira α; si ambos, (nR−nL)·β. Células emergen y se parten." }],
      counters: [{ text: `N=${N} r=${P.r} α=180° β=17° v=${P.v}` }],
      cite: "Schmickl et al. (2016) Sci. Rep. 6:37969",
    });
  }

  function stepOnce() {
    step();
    step();
    draw();
  }
  draw();
  CNCapture.boot({
    verify: () => parts.length > 5000,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
