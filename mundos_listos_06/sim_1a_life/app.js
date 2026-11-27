/* SIM 1A — Conway Life B3/S23 · patrones clásicos. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 240;
  const H = 180;
  const cell = 5;
  let grid = new Uint8Array(W * H);
  let trail = new Float32Array(W * H);
  const clock = new SimClock(opts.fps);

  function idx(x, y) {
    return (((y % H) + H) % H) * W + (((x % W) + W) % W);
  }

  function set(x, y, v = 1) {
    grid[idx(x, y)] = v;
  }

  function stamp(cells, ox, oy) {
    cells.forEach(([dx, dy]) => set(ox + dx, oy + dy));
  }

  stamp([[0, 1], [1, 2], [2, 0], [2, 1], [2, 2]], 24, 40);
  stamp([[1, 0], [1, 1], [1, 2]], 120, 32);
  stamp([[0, 0], [1, 0], [2, 0], [0, 1], [1, 1]], 90, 85);
  stamp([[1, 0], [2, 1], [0, 2], [1, 2], [2, 2]], 180, 95);

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

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const gridW = W * cell;
    const gridH = H * cell;
    const ox = (w - gridW * 1.05) / 2;
    const oy = (h - gridH * 1.05) / 2;
  ctx.save();
  ctx.translate(ox, oy);
  ctx.scale(1.05, 1.05);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        const t = trail[i];
        if (!t) continue;
        const px = x * cell;
        const py = y * cell;
        if (grid[i]) {
          ctx.shadowColor = CN.cian;
          ctx.shadowBlur = 6;
          ctx.fillStyle = CN.cian;
          ctx.fillRect(px, py, cell - 1, cell - 1);
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = `rgba(0,229,199,${t * 0.15})`;
          ctx.fillRect(px, py, cell - 1, cell - 1);
        }
      }
    }
    ctx.restore();
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w,
      h,
      formato: opts.formato,
      lines: [{ text: "B3/S23: nacen con 3 vecinos; sobreviven con 2–3" }],
      counters: [
        { text: `rejilla ${W}×${H}` },
        { text: `t = ${clock.frame}` },
      ],
      cite: "Conway (1970); Gardner (1970) Sci. Am.",
    });
  }

  function stepOnce() {
    step();
    draw();
  }

  draw();
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