/* SIM 1B — Lenia (Chan 2019), Orbium. CC0 */
(function () {
  const { parseQuery, SimClock, Camera2D, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const { makeKernel, step, seedOrbium, centroid, renderField, ORBIUM } = CNLenia;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const GW = 176, GH = 176;
  const kernel = makeKernel(ORBIUM.R);
  let field = new Float32Array(GW * GH);
  seedOrbium(field, GW, GH, GW * 0.45, GH * 0.5, 14);
  for (let i = 0; i < 400; i++) {
    field = step(field, GW, GH, kernel, ORBIUM.mu, ORBIUM.sigma, 1 / ORBIUM.T);
  }
  const clock = new SimClock(opts.fps);
  const cam = new Camera2D();
  const off = document.createElement("canvas");
  off.width = GW;
  off.height = GH;
  const octx = off.getContext("2d", { willReadFrequently: true });
  const bl = document.createElement("canvas");
  bl.width = GW;
  bl.height = GH;

  function renderBloom() {
    const { w, h } = opts;
    renderField(octx, field, GW, GH, GW, GH);
    const c = centroid(field, GW, GH, 0.05);
    cam.setTarget((c.x / GW) * w, (c.y / GH) * h, opts.formato === "9x16" ? 2.15 : 1.75);
    cam.update(clock.dt);
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const pw = w * 0.88, ph = h * 0.8;
    const cx = w / 2 + (cam.x - w / 2) * 0.12;
    const cy = h / 2 + (cam.y - h / 2) * 0.12;
    const bctx = bl.getContext("2d");
    bctx.clearRect(0, 0, GW, GH);
    bctx.drawImage(off, 0, 0);
    bctx.globalAlpha = 0.45;
    bctx.drawImage(off, -2, -2);
    bctx.drawImage(off, 2, 2);
    bctx.globalAlpha = 1;
    ctx.drawImage(off, cx - pw / 2, cy - ph / 2, pw, ph);
    ctx.globalAlpha = 0.35;
    ctx.drawImage(bl, cx - pw / 2 - 4, cy - ph / 2 - 4, pw + 8, ph + 8);
    ctx.globalAlpha = 1;
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Lenia · Chan (2019). Estos patrones no están vivos." }],
      counters: [{ text: `μ=${ORBIUM.mu} σ=${ORBIUM.sigma} R=${ORBIUM.R}`, color: CN.gris }],
      cite: "Chan (2019), Complex Systems 28(3); Orbium vía Chakazul/Lenia",
    });
  }

  function stepOnce() {
    for (let i = 0; i < 3; i++) {
      field = step(field, GW, GH, kernel, ORBIUM.mu, ORBIUM.sigma, 1 / ORBIUM.T);
    }
    clock.tick();
    renderBloom();
  }

  function verifyPattern() {
    let mass = 0;
    for (let i = 0; i < field.length; i++) mass += field[i];
    return mass > 50;
  }

  CNCapture.boot({
    warmup: async () => { for (let i = 0; i < 30; i++) stepOnce(); },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();