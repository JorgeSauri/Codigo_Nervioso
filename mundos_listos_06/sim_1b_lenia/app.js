/* SIM 1B — Lenia, Orbium como anillos luminosos + física local. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const { makeKernel, step, seedOrbium, ORBIUM } = CNLenia;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const PW = 96;
  const PH = 96;
  const kernel = makeKernel(ORBIUM.R);
  const dt = 1 / ORBIUM.T;
  const creatures = [
    { px: 0.2, py: 0.42, rad: 11.8 },
    { px: 0.45, py: 0.3, rad: 12.1 },
    { px: 0.72, py: 0.44, rad: 12.4 },
    { px: 0.35, py: 0.66, rad: 11.6 },
    { px: 0.62, py: 0.7, rad: 12.0 },
  ].map((c) => {
    let field = new Float32Array(PW * PH);
    seedOrbium(field, PW, PH, PW * 0.5, PH * 0.52, c.rad, 0.62);
    for (let i = 0; i < 60; i++) field = step(field, PW, PH, kernel, ORBIUM.mu, ORBIUM.sigma, dt);
    return { ...c, field, t: 0, trail: [] };
  });

  const clock = new SimClock(opts.fps);
  let trail;
  let trailCtx;

  function measure(field, w, h) {
    let mx = 0;
    let my = 0;
    let m = 0;
    let r2 = 0;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const v = field[y * w + x];
        if (v < 0.22) continue;
        mx += x * v;
        my += y * v;
        m += v;
      }
    }
    if (m < 1) return { x: 0.5, y: 0.5, rad: 18, mass: 0 };
    const cx = mx / m;
    const cy = my / m;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const v = field[y * w + x];
        if (v < 0.22) continue;
        r2 += v * ((x - cx) ** 2 + (y - cy) ** 2);
      }
    }
    const rad = Math.sqrt(r2 / m) * 2.4;
    return { x: cx / w, y: cy / h, rad, mass: m };
  }

  function drawRing(sx, sy, rad, t, trailColor) {
    ctx.save();
    ctx.translate(sx, sy);
    ctx.rotate(t * 0.35);
    ctx.strokeStyle = "rgba(118,255,232,0.92)";
    ctx.lineWidth = Math.max(4, rad * 0.18);
    ctx.beginPath();
    for (let a = 0; a <= Math.PI * 2 + 0.01; a += 0.12) {
      const wob = 1 + 0.1 * Math.sin(a * 6 + t * 4);
      const rx = Math.cos(a) * rad * wob;
      const ry = Math.sin(a) * rad * wob * 0.82;
      a < 0.01 ? ctx.moveTo(rx, ry) : ctx.lineTo(rx, ry);
    }
    ctx.closePath();
    ctx.stroke();
    ctx.globalAlpha = 0.4;
    ctx.strokeStyle = "rgba(118,255,232,0.65)";
    ctx.lineWidth = rad * 0.45;
    ctx.stroke();
    ctx.globalAlpha = 1;
    const g = ctx.createRadialGradient(0, 0, 0, 0, 0, rad * 1.4);
    g.addColorStop(0, "rgba(80,220,200,0.25)");
    g.addColorStop(1, "rgba(80,220,200,0)");
    ctx.fillStyle = g;
    ctx.fillRect(-rad * 1.4, -rad * 1.4, rad * 2.8, rad * 2.8);
    if (trailCtx && trailColor) {
      trailCtx.fillStyle = trailColor;
      trailCtx.beginPath();
      trailCtx.arc(sx, sy, rad * 0.55, 0, Math.PI * 2);
      trailCtx.fill();
    }
    ctx.restore();
  }

  function renderScene() {
    const { w, h } = opts;
    if (!trail) {
      trail = document.createElement("canvas");
      trail.width = w;
      trail.height = h;
      trailCtx = trail.getContext("2d");
    }
    trailCtx.fillStyle = "rgba(7,11,22,0.16)";
    trailCtx.fillRect(0, 0, w, h);
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(trail, 0, 0);
    const scale = opts.formato === "9x16" ? 0.9 : 1;
    creatures.forEach((c) => {
      const m = measure(c.field, PW, PH);
      const sx = (c.px + (m.x - 0.5) * 0.22) * w;
      const sy = (c.py + (m.y - 0.5) * 0.22) * h;
      const rad = Math.max(22, Math.min(56, m.rad * scale * (opts.formato === "9x16" ? 3.2 : 3.8)));
      c.trail.push({ x: sx, y: sy });
      if (c.trail.length > 36) c.trail.shift();
      ctx.strokeStyle = "rgba(90,210,190,0.12)";
      ctx.lineWidth = 8;
      ctx.beginPath();
      c.trail.forEach((p, i) => { i ? ctx.lineTo(p.x, p.y) : ctx.moveTo(p.x, p.y); });
      ctx.stroke();
      drawRing(sx, sy, rad, c.t, `rgba(110,240,215,${0.06 + (c.trail.length / 36) * 0.08})`);
    });
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Lenia · Chan (2019). Estos patrones no están vivos." }],
      counters: [{
        text: `μ=${ORBIUM.mu} σ=${ORBIUM.sigma} R=${ORBIUM.R} · ${creatures.length} criaturas`,
        color: CN.gris,
      }],
      cite: "Chan (2019), Complex Systems 28(3); Orbium vía Chakazul/Lenia",
    });
  }

  function stepOnce() {
    creatures.forEach((c) => {
      c.field = step(c.field, PW, PH, kernel, ORBIUM.mu, ORBIUM.sigma, dt);
      c.field = step(c.field, PW, PH, kernel, ORBIUM.mu, ORBIUM.sigma, dt);
      c.t += clock.dt;
      c.px += Math.sin(c.t * 2) * 0.0015 + 0.0011;
      c.py += Math.cos(c.t * 1.6) * 0.0012 - 0.0003;
      c.px = Math.min(0.84, Math.max(0.12, c.px));
      c.py = Math.min(0.8, Math.max(0.16, c.py));
    });
    clock.tick();
    renderScene();
  }

  function verifyPattern() {
    const vis = creatures.filter((c) => measure(c.field, PW, PH).mass > 12);
    return vis.length >= 3;
  }

  renderScene();

  CNCapture.boot({
    warmup: async () => { for (let i = 0; i < 15; i++) stepOnce(); },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();