/* SIM 3 — Reynolds (1987) boids, miles de agentes. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 3);
  const N = 4000;
  const weights = { sep: 1.5, align: 1.0, coh: 1.0 };
  const neighborDist = 36;
  const protectedRange = 12;
  const maxSpeed = 3.4;
  const maxForce = 0.09;
  const CELL = neighborDist;

  const boids = Array.from({ length: N }, () => ({
    x: rnd() * opts.w,
    y: rnd() * opts.h,
    vx: (rnd() - 0.5) * 2,
    vy: (rnd() - 0.5) * 2,
  }));

  function limit(vx, vy, max) {
    const s = Math.hypot(vx, vy) || 1;
    if (s <= max) return [vx, vy];
    return [(vx / s) * max, (vy / s) * max];
  }

  function step() {
    const cols = Math.ceil(opts.w / CELL);
    const rows = Math.ceil(opts.h / CELL);
    const buckets = new Map();
    boids.forEach((b, i) => {
      const key = ((b.x / CELL) | 0) + ((b.y / CELL) | 0) * cols;
      const list = buckets.get(key);
      if (list) list.push(i);
      else buckets.set(key, [i]);
    });
    const next = boids.map((b) => ({ x: b.x, y: b.y, vx: b.vx, vy: b.vy }));
    boids.forEach((b, bi) => {
      const cx = (b.x / CELL) | 0;
      const cy = (b.y / CELL) | 0;
      let sx = 0, sy = 0, ax = 0, ay = 0, cX = 0, cY = 0, nn = 0;
      for (let oy = -1; oy <= 1; oy++) {
        for (let ox = -1; ox <= 1; ox++) {
          const list = buckets.get((cx + ox) + (cy + oy) * cols);
          if (!list) continue;
          for (let k = 0; k < list.length; k++) {
            const oi = list[k];
            if (oi === bi) continue;
            const o = boids[oi];
            const dx = o.x - b.x;
            const dy = o.y - b.y;
            const d = Math.hypot(dx, dy);
            if (d > neighborDist || d < 1e-4) continue;
            nn++;
            if (d < protectedRange) { sx -= dx / d; sy -= dy / d; }
            ax += o.vx; ay += o.vy;
            cX += o.x; cY += o.y;
          }
        }
      }
      let vx = b.vx;
      let vy = b.vy;
      if (nn > 0) {
        ax = ax / nn - b.vx;
        ay = ay / nn - b.vy;
        cX = cX / nn - b.x;
        cY = cY / nn - b.y;
        const la = limit(ax, ay, maxForce);
        const lc = limit(cX, cY, maxForce);
        const ls = limit(sx, sy, maxForce);
        vx += ls[0] * weights.sep + la[0] * weights.align + lc[0] * weights.coh;
        vy += ls[1] * weights.sep + la[1] * weights.align + lc[1] * weights.coh;
      }
      const lim = limit(vx, vy, maxSpeed);
      next[bi].vx = lim[0];
      next[bi].vy = lim[1];
      next[bi].x = (b.x + lim[0] + opts.w) % opts.w;
      next[bi].y = (b.y + lim[1] + opts.h) % opts.h;
    });
    for (let i = 0; i < N; i++) {
      boids[i].x = next[i].x;
      boids[i].y = next[i].y;
      boids[i].vx = next[i].vx;
      boids[i].vy = next[i].vy;
    }
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = "rgba(7,11,22,0.22)";
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    boids.forEach((b) => {
      const ang = Math.atan2(b.vy, b.vx);
      const spd = Math.hypot(b.vx, b.vy);
      ctx.strokeStyle = `rgba(0,229,199,${0.35 + (spd / maxSpeed) * 0.45})`;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(b.x, b.y);
      ctx.lineTo(b.x + Math.cos(ang) * (5 + spd), b.y + Math.sin(ang) * (5 + spd));
      ctx.stroke();
    });
    ctx.globalCompositeOperation = "source-over";
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Reynolds (1987): separation · alignment · cohesion" }],
      counters: [
        { text: `N=${N} d=${neighborDist} d₀=${protectedRange}` },
        { text: `w=(${weights.sep}, ${weights.align}, ${weights.coh})` },
      ],
      cite: "Reynolds (1987) SIGGRAPH; Computer Graphics 21(4)",
    });
  }

  function stepOnce() { step(); draw(); }
  ctx.fillStyle = CN.navy;
  ctx.fillRect(0, 0, opts.w, opts.h);
  draw();
  CNCapture.boot({
    verify: () => boids.length >= 3000,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
