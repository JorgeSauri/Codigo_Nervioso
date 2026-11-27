/* SIM 1A — Conway Life B3/S23, planeador. CC0 */
(function () {
  const { parseQuery, SimClock, Camera2D, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 220, H = 160;
  const cell = 6;
  let grid = new Uint8Array(W * H);
  let trail = new Float32Array(W * H);
  const clock = new SimClock(opts.fps);
  const cam = new Camera2D();

  function idx(x, y) {
    return (((y % H) + H) % H) * W + (((x % W) + W) % W);
  }

  function set(x, y, v = 1) {
    grid[idx(x, y)] = v;
  }

  function placeGlider(x, y) {
    const g = [[0, 1, 0], [0, 0, 1], [1, 1, 1]];
    g.forEach((row, dy) => row.forEach((v, dx) => v && set(x + dx, y + dy)));
  }

  function step() {
    const next = new Uint8Array(W * H);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        let n = 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (!dx && !dy) continue;
            n += grid[idx(x + dx, y + dy)];
          }
        }
        const alive = grid[idx(x, y)];
        next[idx(x, y)] = alive ? (n === 2 || n === 3 ? 1 : 0) : n === 3 ? 1 : 0;
      }
    }
    grid = next;
    for (let i = 0; i < trail.length; i++) {
      trail[i] *= 0.82;
      if (grid[i]) trail[i] = 1;
    }
    clock.tick();
  }

  let phase = "glider";
  let gx = 40, gy = 70;
  placeGlider(gx, gy);
  cam.setTarget(gx * cell, gy * cell, 2.4);

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    ctx.save();
    const focusX = phase === "glider" ? gx * cell : W * cell * 0.5;
    const focusY = phase === "glider" ? gy * cell : H * cell * 0.5;
    cam.setTarget(focusX, focusY, phase === "glider" ? 2.8 : 1.2);
    cam.update(clock.dt);
    const ox = w / 2 - cam.x * cam.zoom;
    const oy = h / 2 - cam.y * cam.zoom;
    ctx.translate(ox, oy);
    ctx.scale(cam.zoom, cam.zoom);
    if (phase !== "glider") {
      ctx.strokeStyle = "rgba(138,147,166,0.08)";
      for (let x = 0; x <= W; x++) {
        ctx.beginPath();
        ctx.moveTo(x * cell, 0);
        ctx.lineTo(x * cell, H * cell);
        ctx.stroke();
      }
    }
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        const t = trail[i];
        if (!t) continue;
        const px = x * cell, py = y * cell;
        ctx.fillStyle = grid[i]
          ? `rgba(0,229,199,${0.55 + t * 0.45})`
          : `rgba(0,229,199,${t * 0.18})`;
        const r = 2;
        ctx.fillRect(px + 1, py + 1, cell - 2, cell - 2);
        if (grid[i]) {
          ctx.shadowColor = CN.cian;
          ctx.shadowBlur = 8;
          ctx.fillStyle = CN.cian;
          ctx.fill();
          ctx.shadowBlur = 0;
        }
      }
    }
    ctx.restore();
    vignette(ctx, w, h);
    const t = clock.frame;
    if (t > 180) phase = "random";
    if (t === 300) {
      grid.fill(0);
      trail.fill(0);
      const rnd = mulberry32(opts.seed + 1);
      for (let i = 0; i < W * H * 0.28; i++) grid[(rnd() * W * H) | 0] = 1;
    }
    drawOverlay(ctx, {
      w,
      h,
      formato: opts.formato,
      lines: [{ text: "Juego de la Vida · reglas B3/S23 (notación posterior)" }],
      counters: [{ text: `t = ${String(clock.frame).padStart(6, "0")}` }],
      cite: "Gardner (1970), Sci. Am. 223(4), 120–123",
    });
  }

  function stepOnce() {
    step();
    if (clock.frame % 4 === 0 && phase === "glider") {
      gx += 1;
      gy += 1;
    }
    draw();
  }

  CNCapture.boot({
    runRealtime() {
      const loop = () => {
        stepOnce();
        requestAnimationFrame(loop);
      };
      loop();
    },
    stepOnce,
  });
})();