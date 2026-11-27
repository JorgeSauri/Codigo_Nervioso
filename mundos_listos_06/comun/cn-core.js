/* Código Nervioso EP06 — utilidades compartidas. CC0 */
(function (global) {
  "use strict";

  const CN = {
    navy: "#0B1020",
    cian: "#00E5C7",
    coral: "#FF6B4A",
    papel: "#F4F1EA",
    gris: "#8A93A6",
    ocre: "#E8C547",
    dt: 1 / 60,
    easeOut: (t) => {
      const u = 1 - t;
      return 1 - u * u * u;
    },
    easeStd: (t) => t * t * (3 - 2 * t),
    bezierOut: (t) => {
      const p0 = 0, p1 = 0.22, p2 = 1, p3 = 0.36, p4 = 1;
      const u = 1 - t;
      return 3 * u * u * t * p1 + 3 * u * t * t * p3 + t * t * t;
    },
  };

  function parseQuery() {
    const q = new URLSearchParams(location.search);
    return {
      capture: q.get("capture") === "1",
      formato: q.get("formato") === "9x16" ? "9x16" : "16x9",
      fps: Math.min(60, Math.max(1, parseInt(q.get("fps") || "60", 10))),
      seed: parseInt(q.get("seed") || "6006", 10),
      w: parseInt(q.get("w") || "1920", 10),
      h: parseInt(q.get("h") || "1080", 10),
    };
  }

  function mulberry32(a) {
    return function () {
      let t = (a += 0x6d2b79f5);
      t = Math.imul(t ^ (t >>> 15), t | 1);
      t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  class SimClock {
    constructor(fps = 60) {
      this.fps = fps;
      this.dt = 1 / fps;
      this.frame = 0;
      this.t = 0;
    }
    tick() {
      this.frame++;
      this.t = this.frame * this.dt;
      return this.dt;
    }
  }

  class Camera2D {
    constructor() {
      this.x = 0;
      this.y = 0;
      this.zoom = 1;
      this.tx = 0;
      this.ty = 0;
      this.tz = 1;
      this.lag = 0.35;
    }
    setTarget(x, y, z) {
      this.tx = x;
      this.ty = y;
      if (z != null) this.tz = z;
    }
    update(dt) {
      const k = 1 - Math.exp(-dt / this.lag);
      this.x += (this.tx - this.x) * k;
      this.y += (this.ty - this.y) * k;
      this.zoom += (this.tz - this.zoom) * k;
    }
    worldToScreen(wx, wy, w, h) {
      return [
        w / 2 + (wx - this.x) * this.zoom,
        h / 2 + (wy - this.y) * this.zoom,
      ];
    }
  }

  function vignette(ctx, w, h, strength = 0.05) {
    const g = ctx.createRadialGradient(w * 0.5, h * 0.48, w * 0.15, w * 0.5, h * 0.5, w * 0.72);
    g.addColorStop(0, `rgba(255,255,255,${strength})`);
    g.addColorStop(1, "rgba(0,0,0,0.35)");
    ctx.fillStyle = g;
    ctx.fillRect(0, 0, w, h);
  }

  function drawOverlay(ctx, cfg) {
    const { w, h, formato, lines = [], counters = [], cite = "" } = cfg;
    const pad = formato === "9x16" ? h * 0.06 : w * 0.025;
    const bottomSafe = formato === "9x16" ? h * 0.12 : h * 0.04;
    ctx.save();
    ctx.textBaseline = "top";
    lines.forEach((line, i) => {
      ctx.font = `${Math.round(16 + w * 0.008)}px "CN Grotesk", sans-serif`;
      ctx.fillStyle = line.color || CN.papel;
      ctx.fillText(line.text, pad, pad + i * (22 + w * 0.006));
    });
    counters.forEach((c, i) => {
      ctx.font = `${Math.round(14 + w * 0.005)}px "CN Mono", monospace`;
      ctx.fillStyle = c.color || CN.cian;
      const y = h - bottomSafe - (counters.length - i) * 22;
      ctx.fillText(c.text, w - pad - ctx.measureText(c.text).width, y);
    });
    if (cite) {
      ctx.font = `${Math.round(11 + w * 0.003)}px "CN Inter", sans-serif`;
      ctx.fillStyle = CN.gris;
      const tw = ctx.measureText(cite).width;
      ctx.fillText(cite, w - pad - tw, h - pad * 0.35);
    }
    ctx.restore();
  }

  function setupCanvas(canvas, opts) {
    const dpr = opts.capture ? 1 : Math.min(2, window.devicePixelRatio || 1);
    canvas.width = opts.w * dpr;
    canvas.height = opts.h * dpr;
    canvas.style.width = opts.w + "px";
    canvas.style.height = opts.h + "px";
    const ctx = canvas.getContext("2d", { alpha: false });
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return ctx;
  }

  function initCaptureBridge(sim) {
    const q = parseQuery();
    if (!q.capture) return q;
    document.body.classList.add("cn-capture");
    global.__cnCapture = {
      opts: q,
      ready: false,
      frame: 0,
      async pullFrame() {
        await sim.stepSim();
        const canvas = document.getElementById("cn-canvas");
        return canvas.toDataURL("image/png");
      },
    };
    return q;
  }

  global.CN = CN;
  global.CNCore = {
    CN,
    parseQuery,
    mulberry32,
    SimClock,
    Camera2D,
    vignette,
    drawOverlay,
    setupCanvas,
    initCaptureBridge,
  };
})(typeof window !== "undefined" ? window : globalThis);