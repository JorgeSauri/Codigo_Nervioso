/* SIM 1C — Gray-Scott (Pearson 1993), CPU determinista. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const PARAMS = {
    Du: 2e-5,
    Dv: 1e-5,
    f: 0.018,
    k: 0.055,
    source: "Pearson (1993) régimen de manchas que crecen y se parten (σ, Munafo 2022 / Hundsdorfer & Verwer 2003 citan F=0.018, k=0.055 con estas difusividades)",
  };
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 128, H = 128;
  let u = new Float32Array(W * H).fill(1);
  let v = new Float32Array(W * H);
  const rnd = mulberry32(opts.seed + 12);
  for (let i = 0; i < W * H * 0.01; i++) {
    const x = (rnd() * W) | 0, y = (rnd() * H) | 0;
    v[y * W + x] = 0.9;
  }
  const clock = new SimClock(opts.fps);
  const dt = 1.0;

  function laplace(arr, x, y) {
    const i = y * W + x;
    const l = arr[((y - 1 + H) % H) * W + x] + arr[((y + 1) % H) * W + x]
      + arr[y * W + ((x - 1 + W) % W)] + arr[y * W + ((x + 1) % W)];
    return l - 4 * arr[i];
  }

  function step() {
    const nu = new Float32Array(W * H);
    const nv = new Float32Array(W * H);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        const uv = u[i] * v[i] * v[i];
        nu[i] = u[i] + (PARAMS.Du * laplace(u, x, y) - uv + PARAMS.f * (1 - u[i])) * dt;
        nv[i] = v[i] + (PARAMS.Dv * laplace(v, x, y) + uv - (PARAMS.f + PARAMS.k) * v[i]) * dt;
      }
    }
    u = nu; v = nv;
    for (let i = 0; i < v.length; i++) {
      u[i] = Math.min(1, Math.max(0, u[i]));
      v[i] = Math.min(1, Math.max(0, v[i]));
    }
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const pw = w * 0.92, ph = h * 0.82;
    const img = ctx.createImageData(W, H);
    for (let i = 0; i < v.length; i++) {
      const t = Math.min(1, v[i] * 2);
      img.data[i * 4] = Math.round(11 + 200 * t);
      img.data[i * 4 + 1] = Math.round(16 + 220 * t);
      img.data[i * 4 + 2] = Math.round(32 + 150 * t);
      img.data[i * 4 + 3] = 255;
    }
    const off = document.createElement("canvas");
    off.width = W; off.height = H;
    off.getContext("2d").putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(off, (w - pw) / 2, (h - ph) / 2, pw, ph);
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Analogía, no está viva", color: CN.coral }],
      counters: [{ text: `F=${PARAMS.f} k=${PARAMS.k}` }],
      cite: "Pearson (1993), Science 261:189–192",
    });
  }

  function stepOnce() {
    for (let i = 0; i < 8; i++) step();
    draw();
  }

  CNCapture.boot({ runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();