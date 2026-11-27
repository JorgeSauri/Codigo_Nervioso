/* SIM 1C — Gray-Scott (Pearson 1993), cuatro regímenes. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const DU = 0.16;
  const DV = 0.08;
  const REGIMES = [
    { name: "mitosis", f: 0.030, k: 0.062 },
    { name: "gusanos", f: 0.054, k: 0.063 },
    { name: "laberinto", f: 0.029, k: 0.057 },
    { name: "manchas", f: 0.018, k: 0.051 },
  ];
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 256;
  const H = 144;
  const dt = 1.0;
  let u = new Float32Array(W * H).fill(1);
  let v = new Float32Array(W * H);
  let uN = new Float32Array(W * H);
  let vN = new Float32Array(W * H);
  const rnd = mulberry32(opts.seed + 12);

  function regimeAt(x, y) {
    const col = x < W / 2 ? 0 : 1;
    const row = y < H / 2 ? 0 : 1;
    return REGIMES[row * 2 + col];
  }

  function seedBlob(cx, cy, rad) {
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const d = Math.hypot(x - cx, y - cy);
        if (d < rad) v[y * W + x] = 0.9 * (1 - d / rad);
      }
    }
  }
  seedBlob(W * 0.25, H * 0.25, 8);
  seedBlob(W * 0.75, H * 0.25, 7);
  seedBlob(W * 0.25, H * 0.75, 10);
  seedBlob(W * 0.75, H * 0.75, 6);
  for (let i = 0; i < 80; i++) {
    const x = (rnd() * W) | 0;
    const y = (rnd() * H) | 0;
    v[y * W + x] = Math.max(v[y * W + x], 0.8);
  }

  function lap(arr, x, y) {
    const xm = x === 0 || x === (W / 2) | 0 ? x : x - 1;
    const xp = x === W - 1 || x === ((W / 2) | 0) - 1 ? x : x + 1;
    const ym = y === 0 || y === (H / 2) | 0 ? y : y - 1;
    const yp = y === H - 1 || y === ((H / 2) | 0) - 1 ? y : y + 1;
    return arr[ym * W + x] + arr[yp * W + x] + arr[y * W + xm] + arr[y * W + xp] - 4 * arr[y * W + x];
  }

  function stepCore() {
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        const p = regimeAt(x, y);
        const uvv = u[i] * v[i] * v[i];
        uN[i] = u[i] + (DU * lap(u, x, y) - uvv + p.f * (1 - u[i])) * dt;
        vN[i] = v[i] + (DV * lap(v, x, y) + uvv - (p.f + p.k) * v[i]) * dt;
      }
    }
    [u, uN] = [uN, u];
    [v, vN] = [vN, v];
    for (let i = 0; i < v.length; i++) {
      u[i] = Math.min(1, Math.max(0, u[i]));
      v[i] = Math.min(1, Math.max(0, v[i]));
    }
  }

  for (let k = 0; k < 40; k++) stepCore();

  const clock = new SimClock(opts.fps);
  const off = document.createElement("canvas");
  off.width = W;
  off.height = H;
  const octx = off.getContext("2d");

  function paintField() {
    const img = octx.createImageData(W, H);
    for (let i = 0; i < v.length; i++) {
      const t = Math.min(1, v[i] * 1.35);
      const i4 = i * 4;
      img.data[i4] = Math.round(8 + t * 40);
      img.data[i4 + 1] = Math.round(18 + t * 210);
      img.data[i4 + 2] = Math.round(36 + t * 160);
      img.data[i4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const pw = w * 0.92;
    const ph = h * 0.78;
    const x0 = (w - pw) / 2;
    const y0 = h * 0.08;
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(off, x0, y0, pw, ph);
    ctx.globalAlpha = 0.22;
    ctx.drawImage(off, x0 - 2, y0 - 2, pw + 4, ph + 4);
    ctx.globalAlpha = 1;
    ctx.font = '18px "CN Inter"';
    REGIMES.forEach((r, i) => {
      const col = i % 2;
      const row = (i / 2) | 0;
      const x = x0 + col * pw * 0.5 + 16;
      const y = y0 + row * ph * 0.5 + 28;
      ctx.fillStyle = CN.papel;
      ctx.fillText(`${r.name}  F=${r.f.toFixed(3)}  k=${r.k.toFixed(3)}`, x, y);
    });
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "∂u/∂t = Du∇²u − uv² + F(1−u)    ∂v/∂t = Dv∇²v + uv² − (F+k)v" }],
      counters: [{ text: `Du=${DU} Dv=${DV} · 4 regímenes Pearson` }],
      cite: "Pearson (1993) Science 261:189–192",
    });
  }

  function stepOnce() {
    for (let i = 0; i < 4; i++) stepCore();
    paintField();
    clock.tick();
    draw();
  }

  function verifyPattern() {
    let vmax = 0;
    for (let i = 0; i < v.length; i++) if (v[i] > vmax) vmax = v[i];
    return vmax > 0.2;
  }

  paintField();
  draw();
  CNCapture.boot({
    warmup: async () => { for (let i = 0; i < 8; i++) stepOnce(); },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
