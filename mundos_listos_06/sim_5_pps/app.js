/* SIM 5 — PPS Schmickl, Stefanec & Crailsheim 2016. CC0
   Δφ = α + β·N·sign(R−L), giro a la derecha si Δφ>0, luego avance v.
   Actualización asíncrona en un toro, como en el paper. */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const P = { r: 5, alpha: Math.PI, beta: (17 * Math.PI) / 180, v: 0.67, rho: 0.08 };
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 5);
  const W = 180;
  const H = 100;
  const N = Math.floor(P.rho * W * H);
  const TAU = Math.PI * 2;
  const xs = new Float64Array(N);
  const ys = new Float64Array(N);
  const hs = new Float64Array(N);
  const nb = new Int16Array(N);
  for (let i = 0; i < N; i++) {
    xs[i] = rnd() * W;
    ys[i] = rnd() * H;
    hs[i] = rnd() * TAU;
  }

  function wrapDelta(d, span) {
    if (d > span * 0.5) return d - span;
    if (d < -span * 0.5) return d + span;
    return d;
  }

  function scope(ang) {
    ang %= TAU;
    if (ang < 0) ang += TAU;
    return ang;
  }

  const cols = Math.ceil(W / P.r);
  const rows = Math.ceil(H / P.r);
  const r2 = P.r * P.r;

  function step() {
    const buckets = Array.from({ length: cols * rows }, () => []);
    for (let i = 0; i < N; i++) {
      const cx = Math.min(cols - 1, (xs[i] / P.r) | 0);
      const cy = Math.min(rows - 1, (ys[i] / P.r) | 0);
      buckets[cy * cols + cx].push(i);
    }
    for (let i = 0; i < N; i++) {
      let L = 0;
      let R = 0;
      const cx = Math.min(cols - 1, Math.max(0, (xs[i] / P.r) | 0));
      const cy = Math.min(rows - 1, Math.max(0, (ys[i] / P.r) | 0));
      const heading = hs[i];
      for (let oy = -1; oy <= 1; oy++) {
        for (let ox = -1; ox <= 1; ox++) {
          const list = buckets[((cy + oy + rows) % rows) * cols + ((cx + ox + cols) % cols)];
          for (let k = 0; k < list.length; k++) {
            const j = list[k];
            if (j === i) continue;
            const dx = wrapDelta(xs[j] - xs[i], W);
            const dy = wrapDelta(ys[j] - ys[i], H);
            if (dx * dx + dy * dy > r2) continue;
            if (scope(Math.atan2(dy, dx) - heading) < Math.PI) R++;
            else L++;
          }
        }
      }
      const n = L + R;
      nb[i] = n;
      const s = R > L ? 1 : R < L ? -1 : 0;
      hs[i] = heading + P.alpha + P.beta * n * s;
      xs[i] = (xs[i] + Math.cos(hs[i]) * P.v + W) % W;
      ys[i] = (ys[i] + Math.sin(hs[i]) * P.v + H) % H;
    }
  }

  for (let i = 0; i < 6500; i++) step();

  function colorOf(n) {
    if (n > 35) return "#FFE08A";
    if (n > 15) return "#4AA3FF";
    if (n >= 13) return "#C48A4A";
    return "#1DB88A";
  }

  function draw() {
    const { w, h } = opts;
    const scale = Math.min((w * 0.92) / W, (h * 0.8) / H);
    const ox = (w - W * scale) / 2;
    const oy = (h - H * scale) / 2;
    const rad = Math.max(2.2, scale * 0.34);
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    for (let pass = 0; pass < 4; pass++) {
      for (let i = 0; i < N; i++) {
        const n = nb[i];
        const band = n > 35 ? 3 : n > 15 ? 2 : n >= 13 ? 1 : 0;
        if (band !== pass) continue;
        ctx.fillStyle = colorOf(n);
        ctx.beginPath();
        ctx.arc(ox + xs[i] * scale, oy + ys[i] * scale, rad, 0, TAU);
        ctx.fill();
      }
    }
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Δφ = α + β·N·sign(R−L). Núcleo N>35, membrana 13–15." }],
      counters: [{ text: `N=${N} ρ=${P.rho} r=${P.r} α=180° β=17° dominio ${W}×${H}` }],
      cite: "Schmickl, Stefanec & Crailsheim (2016) Sci. Rep. 6:37969",
    });
  }

  function stepOnce() {
    step();
    step();
    step();
    step();
    step();
    clock.tick();
    draw();
  }
  draw();
  CNCapture.boot({
    verify: () => {
      let cells = 0;
      for (let i = 0; i < N; i++) if (nb[i] > 15) cells++;
      return N > 1000 && cells > 40;
    },
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
