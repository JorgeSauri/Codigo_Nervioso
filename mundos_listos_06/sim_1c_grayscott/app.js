/* SIM 1C — Gray-Scott (Pearson 1993), CPU 2D. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const PARAMS = { Du: 0.16, Dv: 0.08, f: 0.018, k: 0.055 };
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 192, H = 192;
  const dt = 1.0;
  let u = new Float32Array(W * H).fill(1);
  let v = new Float32Array(W * H);
  let uN = new Float32Array(W * H);
  let vN = new Float32Array(W * H);
  const rnd = mulberry32(opts.seed + 12);
  const cx = W / 2, cy = H / 2;
  for (let y = 0; y < H; y++) {
    for (let x = 0; x < W; x++) {
      const d = Math.hypot(x - cx, y - cy);
      if (d < 18) v[y * W + x] = 0.92 * (1 - d / 18);
    }
  }
  for (let i = 0; i < 500; i++) {
    const x = (rnd() * W) | 0, y = (rnd() * H) | 0;
    v[y * W + x] = Math.max(v[y * W + x], 0.85);
  }

  function laplace(arr, x, y) {
    const i = y * W + x;
    const l = arr[((y - 1 + H) % H) * W + x] + arr[((y + 1) % H) * W + x]
      + arr[y * W + ((x - 1 + W) % W)] + arr[y * W + ((x + 1) % W)];
    return l - 4 * arr[i];
  }

  function stepCore() {
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        const uv = u[i] * v[i] * v[i];
        uN[i] = u[i] + (PARAMS.Du * laplace(u, x, y) - uv + PARAMS.f * (1 - u[i])) * dt;
        vN[i] = v[i] + (PARAMS.Dv * laplace(v, x, y) + uv - (PARAMS.f + PARAMS.k) * v[i]) * dt;
      }
    }
    [u, uN] = [uN, u];
    [v, vN] = [vN, v];
    for (let i = 0; i < v.length; i++) {
      u[i] = Math.min(1, Math.max(0, u[i]));
      v[i] = Math.min(1, Math.max(0, v[i]));
    }
  }

  for (let k = 0; k < 100; k++) stepCore();

  const clock = new SimClock(opts.fps);
  const off = document.createElement("canvas");
  off.width = W;
  off.height = H;
  const octx = off.getContext("2d");

  function paintField() {
    const img = octx.createImageData(W, H);
    for (let i = 0; i < v.length; i++) {
      const t = Math.min(1, v[i] * 1.4);
      const i4 = i * 4;
      img.data[i4] = Math.round(8 + t * 0);
      img.data[i4 + 1] = Math.round(20 + t * 220);
      img.data[i4 + 2] = Math.round(40 + t * 175);
      img.data[i4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const pw = w * 0.9, ph = h * 0.82;
    const x0 = (w - pw) / 2, y0 = (h - ph) / 2;
    ctx.drawImage(off, x0, y0, pw, ph);
    ctx.globalAlpha = 0.28;
    ctx.drawImage(off, x0 - 3, y0 - 3, pw + 6, ph + 6);
    ctx.globalAlpha = 1;
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Analogía, no está viva", color: CN.coral }],
      counters: [{ text: `F=${PARAMS.f} k=${PARAMS.k}` }],
      cite: "Pearson (1993), Science 261:189–192",
    });
  }

  function stepOnce() {
    for (let i = 0; i < 6; i++) stepCore();
    paintField();
    clock.tick();
    draw();
  }

  function verifyPattern() {
    let vmax = 0, active = 0;
    for (let i = 0; i < v.length; i++) {
      if (v[i] > 0.15) active++;
      vmax = Math.max(vmax, v[i]);
    }
    return vmax > 0.3 && active > 200;
  }

  paintField();

  CNCapture.boot({
    warmup: async () => {
      for (let k = 0; k < 500; k++) {
        stepCore();
        if ((k & 31) === 31) await new Promise((r) => setTimeout(r, 0));
      }
      paintField();
      draw();
      for (let i = 0; i < 15; i++) stepOnce();
    },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();