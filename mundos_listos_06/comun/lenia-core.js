/* Núcleo Lenia discreto (Chan 2019). CC0 */
(function (global) {
  "use strict";

  function growth(u, mu, sigma) {
    return 2 * Math.exp(-((u - mu) ** 2) / (2 * sigma * sigma)) - 1;
  }

  function makeKernel(R, beta = [1]) {
    const size = R * 2 + 1;
    const k = new Float64Array(size * size);
    let sum = 0;
    for (let y = -R; y <= R; y++) {
      for (let x = -R; x <= R; x++) {
        const r = Math.sqrt(x * x + y * y) / R;
        if (r > 1) continue;
        const val = Math.exp(4 - 4 / (r * (1 - r) + 1e-9)) * (beta[0] || 1);
        const idx = (y + R) * size + (x + R);
        k[idx] = val;
        sum += val;
      }
    }
    for (let i = 0; i < k.length; i++) k[i] /= sum || 1;
    return { data: k, size, R };
  }

  function convolve(field, w, h, kernel) {
    const { data, size, R } = kernel;
    const out = new Float32Array(w * h);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        let s = 0;
        for (let ky = -R; ky <= R; ky++) {
          for (let kx = -R; kx <= R; kx++) {
            const xx = (x + kx + w) % w;
            const yy = (y + ky + h) % h;
            s += field[yy * w + xx] * data[(ky + R) * size + (kx + R)];
          }
        }
        out[y * w + x] = s;
      }
    }
    return out;
  }

  function step(field, w, h, kernel, mu, sigma, dt) {
    const pot = convolve(field, w, h, kernel);
    const next = new Float32Array(w * h);
    for (let i = 0; i < field.length; i++) {
      const g = growth(pot[i], mu, sigma);
      next[i] = Math.min(1, Math.max(0, field[i] + dt * g));
    }
    return next;
  }

  function seedOrbium(field, w, h, cx, cy, rad, peak = 0.72) {
    const ringW = Math.max(1.2, rad * 0.22);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const d = Math.hypot(x - cx, y - cy);
        const ring = Math.exp(-((d - rad) ** 2) / (2 * ringW * ringW));
        const core = Math.exp(-(d * d) / (2 * (rad * 0.55) ** 2)) * 0.08;
        const v = Math.min(1, ring * peak + core);
        if (v > 0.04) field[y * w + x] = Math.max(field[y * w + x], v);
      }
    }
  }

  function centroid(field, w, h, thresh = 0.1) {
    let mx = 0, my = 0, m = 0;
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const v = field[y * w + x];
        if (v < thresh) continue;
        mx += x * v;
        my += y * v;
        m += v;
      }
    }
    return m > 0 ? { x: mx / m, y: my / m, mass: m } : { x: w / 2, y: h / 2, mass: 0 };
  }

  function renderField(ctx, field, w, h, drawW, drawH, opts = {}) {
    const thresh = opts.thresh ?? 0;
    const bg = opts.bg ?? [7, 11, 22];
    const img = ctx.createImageData(drawW, drawH);
    const sx = w / drawW;
    const sy = h / drawH;
    for (let py = 0; py < drawH; py++) {
      for (let px = 0; px < drawW; px++) {
        const v0 = field[Math.floor(py * sy) * w + Math.floor(px * sx)];
        const i = (py * drawW + px) * 4;
        if (v0 < thresh) {
          img.data[i] = bg[0];
          img.data[i + 1] = bg[1];
          img.data[i + 2] = bg[2];
          img.data[i + 3] = 255;
          continue;
        }
        const t = Math.min(1, Math.pow(v0, 0.72));
        img.data[i] = Math.round(12 + t * 18);
        img.data[i + 1] = Math.round(22 + t * 228);
        img.data[i + 2] = Math.round(38 + t * 175);
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }

  global.CNLenia = {
    growth,
    makeKernel,
    step,
    seedOrbium,
    centroid,
    renderField,
    ORBIUM: {
      R: 13,
      T: 10,
      mu: 0.15,
      sigma: 0.015,
      source: "Chakazul/Lenia animals.json · Orbium unicaudatus; Chan (2019)",
    },
  };
})(window);