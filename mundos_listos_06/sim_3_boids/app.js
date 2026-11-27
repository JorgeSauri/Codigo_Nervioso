/* SIM 3 — Reynolds (1987) boids. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 3);
  const N = 320;
  const weights = { sep: 1.5, align: 1, coh: 1 };
  const fishNames = ["fish_boid_cyan.png", "fish_boid_tail_a.png", "fish_boid_tail_b.png"];
  let fishSp = [];
  const preloadAssets = () => CNSprites.preload(fishNames).then((r) => { fishSp = r; });

  const boids = Array.from({ length: N }, () => ({
    x: rnd() * opts.w,
    y: rnd() * opts.h,
    vx: (rnd() - 0.5) * 2,
    vy: (rnd() - 0.5) * 2,
    trail: [],
  }));

  function step() {
    const vision = 48;
    const maxV = 3.2;
    boids.forEach((b) => {
      let sx = 0, sy = 0, ax = 0, ay = 0, cx = 0, cy = 0, nn = 0;
      boids.forEach((o) => {
        if (o === b) return;
        const dx = o.x - b.x, dy = o.y - b.y;
        const d = Math.hypot(dx, dy);
        if (d > vision) return;
        nn++;
        if (d < 20) { sx -= dx / d; sy -= dy / d; }
        ax += o.vx; ay += o.vy;
        cx += o.x; cy += o.y;
      });
      if (nn) {
        ax /= nn; ay /= nn;
        cx = cx / nn - b.x; cy = cy / nn - b.y;
      }
      b.vx += (sx * weights.sep + ax * weights.align + cx * weights.coh) * 0.04;
      b.vy += (sy * weights.sep + ay * weights.align + cy * weights.coh) * 0.04;
      const sp = Math.hypot(b.vx, b.vy) || 1;
      if (sp > maxV) { b.vx = (b.vx / sp) * maxV; b.vy = (b.vy / sp) * maxV; }
      b.x = (b.x + b.vx + opts.w) % opts.w;
      b.y = (b.y + b.vy + opts.h) % opts.h;
      b.trail.push({ x: b.x, y: b.y });
      if (b.trail.length > 24) b.trail.shift();
    });
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    boids.forEach((b) => {
      for (let i = 1; i < b.trail.length; i++) {
        ctx.strokeStyle = `rgba(0,229,199,${0.08 + i / b.trail.length * 0.2})`;
        ctx.beginPath();
        ctx.moveTo(b.trail[i - 1].x, b.trail[i - 1].y);
        ctx.lineTo(b.trail[i].x, b.trail[i].y);
        ctx.stroke();
      }
      const ang = Math.atan2(b.vy, b.vx);
      const spIdx = Math.floor(clock.frame / 5 + b.trail.length) % 3;
      const sp = fishSp[spIdx] || fishSp[0];
      const size = 22 + Math.min(12, Math.hypot(b.vx, b.vy) * 3);
      CNSprites.drawSpriteSync(ctx, fishNames[spIdx] || fishNames[0], b.x, b.y, size, ang, sp);
    });
    ctx.globalCompositeOperation = "source-over";
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Reynolds (1987): collision · align · cohesion" }],
      counters: [{ text: `boids = ${N}` }],
      cite: "Reynolds (1987), SIGGRAPH",
    });
  }

  function stepOnce() { step(); draw(); }
  CNCapture.boot({ preloadAssets, runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();