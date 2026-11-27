/* SIM 1B — Lenia (Chan 2019), Orbium. CC0 */
(function () {
  const { parseQuery, SimClock, Camera2D, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const { makeKernel, step, seedOrbium, centroid, ORBIUM } = CNLenia;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const GW = 128, GH = 128;
  const kernel = makeKernel(ORBIUM.R);
  let field = new Float32Array(GW * GH);
  seedOrbium(field, GW, GH, GW * 0.35, GH * 0.55, 16);
  const clock = new SimClock(opts.fps);
  const cam = new Camera2D();
  const off = document.createElement("canvas");
  off.width = GW;
  off.height = GH;
  const octx = off.getContext("2d");

  function renderBloom() {
    const { w, h } = opts;
    octx.clearRect(0, 0, GW, GH);
    for (let i = 0; i < field.length; i++) {
      const v = field[i];
      const x = i % GW, y = (i / GW) | 0;
      const t = Math.min(1, v);
      octx.fillStyle = `rgba(0,${Math.round(80 + 150 * t)},${Math.round(120 + 80 * t)},${t})`;
      octx.fillRect(x, y, 1, 1);
    }
    const c = centroid(field, GW, GH);
    cam.setTarget((c.x / GW) * w, (c.y / GH) * h, opts.formato === "9x16" ? 2.2 : 1.8);
    cam.update(clock.dt);
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const pw = w * 0.92, ph = h * 0.82;
    const px = (w - pw) / 2, py = (h - ph) / 2;
    ctx.save();
    ctx.translate(w / 2 + (cam.x - w / 2) * 0.15, h / 2 + (cam.y - h / 2) * 0.15);
    ctx.drawImage(off, -pw / 2, -ph / 2, pw, ph);
    ctx.globalAlpha = 0.35;
    ctx.filter = "blur(12px)";
    ctx.drawImage(off, -pw / 2, -ph / 2, pw, ph);
    ctx.filter = "none";
    ctx.globalAlpha = 1;
    ctx.restore();
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w,
      h,
      formato: opts.formato,
      lines: [{ text: "Lenia · Chan (2019). Estos patrones no están vivos." }],
      counters: [{ text: `μ=${ORBIUM.mu} σ=${ORBIUM.sigma} R=${ORBIUM.R}`, color: CN.gris }],
      cite: "Chan (2019), Complex Systems 28(3); Orbium vía Chakazul/Lenia",
    });
  }

  function stepOnce() {
    for (let i = 0; i < 2; i++) field = step(field, GW, GH, kernel, ORBIUM.mu, ORBIUM.sigma, 1 / ORBIUM.T);
    clock.tick();
    renderBloom();
  }

  CNCapture.boot({ runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();