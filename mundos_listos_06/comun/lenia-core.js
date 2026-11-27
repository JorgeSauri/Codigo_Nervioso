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

  function stepChannels(channels, w, h, kernel, specs, dt) {
    const comb = new Float32Array(w * h);
    for (let i = 0; i < comb.length; i++) {
      let s = 0;
      for (let c = 0; c < channels.length; c++) s += channels[c][i];
      comb[i] = Math.min(1, s);
    }
    const pot = convolve(comb, w, h, kernel);
    return channels.map((ch, ci) => {
      const { mu, sigma } = specs[ci];
      const next = new Float32Array(w * h);
      for (let i = 0; i < ch.length; i++) {
        const g = growth(pot[i], mu, sigma);
        next[i] = Math.min(1, Math.max(0, ch[i] + dt * g));
      }
      return next;
    });
  }

  function seedOrbium(field, w, h, cx, cy, rad, peak = 0.78) {
    const ringW = Math.max(1.1, rad * 0.2);
    for (let y = 0; y < h; y++) {
      for (let x = 0; x < w; x++) {
        const d = Math.hypot(x - cx, y - cy);
        const ring = Math.exp(-((d - rad) ** 2) / (2 * ringW * ringW));
        const core = Math.exp(-(d * d) / (2 * (rad * 0.5) ** 2)) * 0.06;
        const v = Math.min(1, ring * peak + core);
        if (v > 0.03) field[y * w + x] = Math.max(field[y * w + x], v);
      }
    }
  }

  function seedGeminium(field, w, h, cx, cy, sep, rad, peak = 0.76) {
    seedOrbium(field, w, h, cx - sep, cy, rad, peak);
    seedOrbium(field, w, h, cx + sep, cy, rad, peak * 0.98);
  }

  function sampleBilinear(field, w, h, fx, fy) {
    const x = Math.max(0, Math.min(w - 1.001, fx));
    const y = Math.max(0, Math.min(h - 1.001, fy));
    const x0 = x | 0;
    const y0 = y | 0;
    const tx = x - x0;
    const ty = y - y0;
    const i00 = field[y0 * w + x0];
    const i10 = field[y0 * w + x0 + 1];
    const i01 = field[(y0 + 1) * w + x0];
    const i11 = field[(y0 + 1) * w + x0 + 1];
    return (i00 * (1 - tx) + i10 * tx) * (1 - ty) + (i01 * (1 - tx) + i11 * tx) * ty;
  }

  /** Colormap tipo magma/Chan: interior cálido, borde cian brillante. */
  function colorize(v, p) {
    if (v < 0.035 && p < 0.06) return null;
    const t = Math.min(1, Math.max(0, v * 0.92 + p * 0.08));
    const edge = Math.min(1, Math.max(0, (p - 0.08) * 2.2)) * (1 - t * 0.35);
    const r = Math.round(8 + t * t * 220 + edge * 40);
    const g = Math.round(12 + t * 85 + edge * 200);
    const b = Math.round(28 + (1 - t) * 40 + t * t * 180 + edge * 120);
    return [r, g, b];
  }

  function renderFieldSmooth(ctx, field, pot, w, h, outW, outH) {
    const img = ctx.createImageData(outW, outH);
    const bg = [7, 11, 22];
    for (let py = 0; py < outH; py++) {
      const fy = (py + 0.5) * (h / outH);
      for (let px = 0; px < outW; px++) {
        const fx = (px + 0.5) * (w / outW);
        const v = sampleBilinear(field, w, h, fx, fy);
        const pp = sampleBilinear(pot, w, h, fx, fy);
        const i = (py * outW + px) * 4;
        const c = colorize(v, pp);
        if (!c) {
          img.data[i] = bg[0];
          img.data[i + 1] = bg[1];
          img.data[i + 2] = bg[2];
        } else {
          img.data[i] = c[0];
          img.data[i + 1] = c[1];
          img.data[i + 2] = c[2];
        }
        img.data[i + 3] = 255;
      }
    }
    ctx.putImageData(img, 0, 0);
  }

  const ORBIUM = {
    R: 26,
    T: 10,
    mu: 0.15,
    sigma: 0.015,
    source: "Chakazul animals.json · Orbium unicaudatus",
  };

  const GEMINIUM = {
    R: 22,
    T: 10,
    mu: 0.195,
    sigma: 0.0198,
    source: "Chakazul · Aerogeminium vagus (3GA2v)",
  };

  function renderFieldFast(ctx, field, pot, w, h) {
    const img = ctx.createImageData(w, h);
    const bg = [7, 11, 22];
    for (let i = 0; i < field.length; i++) {
      const v = field[i];
      const pp = pot[i];
      const i4 = i * 4;
      const c = colorize(v, pp);
      if (!c) {
        img.data[i4] = bg[0];
        img.data[i4 + 1] = bg[1];
        img.data[i4 + 2] = bg[2];
      } else {
        img.data[i4] = c[0];
        img.data[i4 + 1] = c[1];
        img.data[i4 + 2] = c[2];
      }
      img.data[i4 + 3] = 255;
    }
    ctx.putImageData(img, 0, 0);
  }

  global.CNLenia = {
    growth,
    makeKernel,
    convolve,
    step,
    stepChannels,
    seedOrbium,
    seedGeminium,
    renderFieldSmooth,
    renderFieldFast,
    colorize,
    ORBIUM,
    GEMINIUM,
  };
})(window);