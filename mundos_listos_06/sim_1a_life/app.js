/* SIM 1A — Conway Life B3/S23: Gosper, naves, matusalén. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 220;
  const H = 130;
  let grid = new Uint8Array(W * H);
  let trail = new Float32Array(W * H);
  const clock = new SimClock(opts.fps);

  function idx(x, y) {
    if (x < 0 || y < 0 || x >= W || y >= H) return -1;
    return y * W + x;
  }
  function set(x, y) {
    const i = idx(x, y);
    if (i >= 0) grid[i] = 1;
  }
  function stamp(cells, ox, oy) {
    cells.forEach(([x, y]) => set(ox + x, oy + y));
  }

  const GOSPER = [
    [24, 0], [22, 1], [24, 1], [12, 2], [13, 2], [20, 2], [21, 2], [34, 2], [35, 2],
    [11, 3], [15, 3], [20, 3], [21, 3], [34, 3], [35, 3],
    [0, 4], [1, 4], [10, 4], [16, 4], [20, 4], [21, 4],
    [0, 5], [1, 5], [10, 5], [14, 5], [16, 5], [17, 5], [22, 5], [24, 5],
    [10, 6], [16, 6], [24, 6], [11, 7], [15, 7], [12, 8], [13, 8],
  ];
  const LWSS = [[1, 0], [4, 0], [0, 1], [0, 2], [4, 2], [0, 3], [1, 3], [2, 3], [3, 3]];
  const ACORN = [[1, 0], [3, 1], [0, 2], [1, 2], [4, 2], [5, 2], [6, 2]];
  const GLIDER = [[1, 0], [2, 1], [0, 2], [1, 2], [2, 2]];

  stamp(GOSPER, 2, 4);
  stamp(LWSS, 150, 18);
  stamp(ACORN, 150, 70);
  stamp(GLIDER, 90, 100);

  function step() {
    const next = new Uint8Array(W * H);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        let n = 0;
        for (let dy = -1; dy <= 1; dy++) {
          for (let dx = -1; dx <= 1; dx++) {
            if (!dx && !dy) continue;
            const j = idx(x + dx, y + dy);
            if (j >= 0) n += grid[j];
          }
        }
        const alive = grid[idx(x, y)];
        next[idx(x, y)] = alive ? (n === 2 || n === 3 ? 1 : 0) : n === 3 ? 1 : 0;
      }
    }
    grid = next;
    for (let i = 0; i < trail.length; i++) {
      trail[i] *= 0.86;
      if (grid[i]) trail[i] = 1;
    }
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const cell = Math.min((w * 0.94) / W, (h * 0.82) / H);
    const ox = (w - W * cell) / 2;
    const oy = h * 0.08;
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        if (trail[i] < 0.04 && !grid[i]) continue;
        const px = ox + x * cell;
        const py = oy + y * cell;
        if (grid[i]) {
          ctx.shadowColor = CN.cian;
          ctx.shadowBlur = 8;
          ctx.fillStyle = CN.cian;
          ctx.fillRect(px, py, cell - 0.6, cell - 0.6);
          ctx.shadowBlur = 0;
        } else {
          ctx.fillStyle = `rgba(0,229,199,${trail[i] * 0.22})`;
          ctx.fillRect(px, py, cell - 0.6, cell - 0.6);
        }
      }
    }
    vignette(ctx, w, h);
    let pop = 0;
    for (let i = 0; i < grid.length; i++) pop += grid[i];
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "B3/S23 · pistola de Gosper, LWSS, planeador, bellota (matusalén)" }],
      counters: [{ text: `vivas ${pop} · t=${clock.frame} · ${W}×${H}` }],
      cite: "Conway (1970); Gardner (1970) Sci. Am. 223(4)",
    });
  }

  function stepOnce() { step(); draw(); }
  draw();
  CNCapture.boot({
    verify: () => grid.reduce((s, v) => s + v, 0) > 30,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
