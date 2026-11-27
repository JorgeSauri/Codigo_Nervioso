/* SIM 1B — Lenia continua (Chan 2019), rejilla única. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const {
    makeKernel, convolve, step, stampSeed,
    renderFieldSmooth, renderFieldFast, ORBIUM, GEMINIUM,
  } = CNLenia;

  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const GW = opts.formato === "9x16" ? 200 : 296;
  const GH = opts.formato === "9x16" ? 356 : 167;
  const kOrb = makeKernel(ORBIUM.R, ORBIUM.beta);
  const kGem = makeKernel(GEMINIUM.R, GEMINIUM.beta);
  const seeds = window.CNLeniaSeeds;

  let ch0 = new Float32Array(GW * GH);
  let ch1 = new Float32Array(GW * GH);
  stampSeed(ch0, GW, GH, GW * 0.28, GH * 0.48, seeds.orbium);
  stampSeed(ch0, GW, GH, GW * 0.72, GH * 0.55, seeds.orbium);
  stampSeed(ch1, GW, GH, GW * 0.5, GH * 0.32, seeds.geminium);

  const warmN = opts.capture ? 8 : 6;
  for (let i = 0; i < warmN; i++) {
    ch0 = step(ch0, GW, GH, kOrb, ORBIUM.mu, ORBIUM.sigma, 1 / ORBIUM.T);
    ch1 = step(ch1, GW, GH, kGem, GEMINIUM.mu, GEMINIUM.sigma, 1 / GEMINIUM.T);
  }

  const clock = new SimClock(opts.fps);
  const offW = opts.formato === "9x16" ? GW : Math.min(624, GW * 2);
  const offH = opts.formato === "9x16" ? GH : Math.min(352, Math.round(offW * (GH / GW)));
  const off = document.createElement("canvas");
  off.width = offW;
  off.height = offH;
  const octx = off.getContext("2d", { willReadFrequently: true });
  let trail;
  let trailCtx;
  let lastPot = null;

  function combined() {
    const c = new Float32Array(GW * GH);
    for (let i = 0; i < c.length; i++) c[i] = Math.min(1, ch0[i] + ch1[i]);
    return c;
  }

  function renderScene() {
    const { w, h } = opts;
    if (!trail) {
      trail = document.createElement("canvas");
      trail.width = w;
      trail.height = h;
      trailCtx = trail.getContext("2d");
    }
    const comb = combined();
    lastPot = convolve(comb, GW, GH, kOrb);
    if (opts.capture && opts.formato === "9x16") {
      renderFieldFast(octx, comb, lastPot, GW, GH);
    } else {
      renderFieldSmooth(octx, comb, lastPot, GW, GH, offW, offH);
    }

    const pw = w * 0.96;
    const ph = h * 0.9;
    const x0 = (w - pw) / 2;
    const y0 = (h - ph) / 2;

    trailCtx.fillStyle = "rgba(7,11,22,0.45)";
    trailCtx.fillRect(0, 0, w, h);
    trailCtx.imageSmoothingEnabled = true;
    trailCtx.imageSmoothingQuality = "high";
    trailCtx.globalAlpha = 0.22;
    trailCtx.drawImage(off, x0, y0, pw, ph);
    trailCtx.globalAlpha = 1;

    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(trail, 0, 0);
    ctx.drawImage(off, x0, y0, pw, ph);
    ctx.globalAlpha = 0.35;
    ctx.drawImage(off, x0 - 2, y0 - 2, pw + 4, ph + 4);
    ctx.globalAlpha = 1;
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "∂u/∂t = G_σ(K∗u)   kernel de anillo Chan 2019" }],
      counters: [{
        text: `Orbium R=${ORBIUM.R} μ=${ORBIUM.mu} σ=${ORBIUM.sigma} · Geminium R=${GEMINIUM.R} μ=${GEMINIUM.mu}`,
        color: CN.gris,
      }],
      cite: "Chan (2019); Chakazul/Lenia animals.json",
    });
  }

  function stepOnce() {
    const substeps = opts.capture ? 1 : 2;
    for (let k = 0; k < substeps; k++) {
      ch0 = step(ch0, GW, GH, kOrb, ORBIUM.mu, ORBIUM.sigma, 1 / ORBIUM.T);
    ch1 = step(ch1, GW, GH, kGem, GEMINIUM.mu, GEMINIUM.sigma, 1 / GEMINIUM.T);
    }
    clock.tick();
    renderScene();
  }

  function verifyPattern() {
    const comb = combined();
    let mass = 0;
    let hi = 0;
    for (let i = 0; i < comb.length; i++) {
      mass += comb[i];
      if (comb[i] > 0.25) hi++;
    }
    const cover = hi / comb.length;
    return mass > 25 && mass < GW * GH * 0.55 && cover < 0.32;
  }

  renderScene();

  CNCapture.boot({
    warmup: async () => {
      for (let i = 0; i < 6; i++) {
        stepOnce();
        if ((i & 7) === 7) await new Promise((r) => setTimeout(r, 0));
      }
    },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();