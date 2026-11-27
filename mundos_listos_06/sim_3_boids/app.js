/* SIM 3 — Reynolds (1987) boids. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 3);
  const N = 720;
  const weights = { sep: 1.5, align: 1.0, coh: 1.0 };
  const neighborDist = 48;
  const protectedRange = 20;
  const maxSpeed = 3.2;
  const maxForce = 0.08;

  const boids = Array.from({ length: N }, () => ({
    x: rnd() * opts.w,
    y: rnd() * opts.h,
    vx: (rnd() - 0.5) * 2,
    vy: (rnd() - 0.5) * 2,
  }));

  function limit(vx, vy, max) {
    const s = Math.hypot(vx, vy) || 1;
    if (s > max) {
      return [(vx / s) * max, (vy / s) * max];
    }
    return [vx, vy];
  }

  function step() {
    boids.forEach((b) => {
      let sx = 0;
      let sy = 0;
      let ax = 0;
      let ay = 0;
      let cx = 0;
      let cy = 0;
      let nn = 0;
      boids.forEach((o) => {
        if (o === b) return;
        const dx = o.x - b.x;
        const dy = o.y - b.y;
        const d = Math.hypot(dx, dy);
        if (d > neighborDist) return;
        nn++;
        if (d < protectedRange && d > 0) {
          sx -= dx / d;
          sy -= dy / d;
        }
        ax += o.vx;
        ay += o.vy;
        cx += o.x;
        cy += o.y;
      });
      if (nn > 0) {
        ax /= nn;
        ay /= nn;
        cx = cx / nn - b.x;
        cy = cy / nn - b.y;
        ax -= b.vx;
        ay -= b.vy;
        const la = limit(ax, ay, maxForce);
        ax = la[0];
        ay = la[1];
        const ls = limit(cx, cy, maxForce);
        cx = ls[0];
        cy = ls[1];
        const ls2 = limit(sx, sy, maxForce);
        sx = ls2[0];
        sy = ls2[1];
      }
      b.vx += sx * weights.sep + ax * weights.align + cx * weights.coh;
      b.vy += sy * weights.sep + ay * weights.align + cy * weights.coh;
      const lim = limit(b.vx, b.vy, maxSpeed);
      b.vx = lim[0];
      b.vy = lim[1];
      b.x = (b.x + b.vx + opts.w) % opts.w;
      b.y = (b.y + b.vy + opts.h) % opts.h;
    });
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = "rgba(7,11,22,0.18)";
    ctx.fillRect(0, 0, w, h);
    ctx.globalCompositeOperation = "lighter";
    boids.forEach((b) => {
      const ang = Math.atan2(b.vy, b.vx);
      const spd = Math.hypot(b.vx, b.vy);
      const len = 7 + spd * 2.2;
      const px = b.x + Math.cos(ang) * len;
      const py = b.y + Math.sin(ang) * len;
      ctx.strokeStyle = `rgba(0,229,199,${0.25 + spd / maxSpeed * 0.45})`;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      ctx.moveTo(b.x, b.y);
      ctx.lineTo(px, py);
      ctx.stroke();
      ctx.fillStyle = `rgba(180,255,240,${0.5 + spd / maxSpeed * 0.4})`;
      ctx.beginPath();
      ctx.arc(b.x, b.y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalCompositeOperation = "source-over";
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Reynolds (1987): separation · alignment · cohesion" }],
      counters: [
        { text: `N=${N} d=${neighborDist} d₀=${protectedRange}` },
        { text: `w_sep=${weights.sep} w_ali=${weights.align} w_coh=${weights.coh}` },
      ],
      cite: "Reynolds (1987) SIGGRAPH; Computer Graphics 21(4)",
    });
  }

  function stepOnce() { step(); draw(); }
  draw();
  CNCapture.boot({
    verify: () => boids.length > 300,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();