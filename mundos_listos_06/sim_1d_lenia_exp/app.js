/* SIM 1D — mismo modelo Chan 2019 que sim_1b (Orbium). El clip del episodio es sim_1b. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const { makeKernel, step, seedOrbium, renderFieldFast, ORBIUM } = CNLenia;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const GW = 160;
  const GH = 90;
  const kernel = makeKernel(ORBIUM.R);
  const dt = 1 / ORBIUM.T;
  let field = new Float32Array(GW * GH);
  seedOrbium(field, GW, GH, GW * 0.5, GH * 0.5, 13, 0.8);
  const clock = new SimClock(opts.fps);
  const off = document.createElement("canvas");
  off.width = GW;
  off.height = GH;
  const octx = off.getContext("2d");

  function draw() {
    const { w, h } = opts;
    renderFieldFast(octx, field, field, GW, GH);
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.drawImage(off, (w - w * 0.8) / 2, (h - h * 0.7) / 2, w * 0.8, h * 0.7);
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Lenia Orbium · misma ecuación que el clip principal (sim_1b)" }],
      counters: [{ text: `R=${ORBIUM.R} μ=${ORBIUM.mu} σ=${ORBIUM.sigma}` }],
      cite: "Chan (2019) Complex Systems 28(3)",
    });
  }
  function stepOnce() {
    field = step(field, GW, GH, kernel, ORBIUM.mu, ORBIUM.sigma, dt);
    clock.tick();
    draw();
  }
  draw();
  CNCapture.boot({
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
