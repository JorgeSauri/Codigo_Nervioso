/* SIM 1E — Langton (1984). CC0 */
(function () {
  const { parseQuery, SimClock, Camera2D, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const { rules, initial } = CNLangton;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const W = 96, H = 96;
  const grid = new Uint8Array(W * H);
  const clock = new SimClock(opts.fps);
  const cam = new Camera2D();
  const colors = [CN.navy, CN.cian, CN.coral, CN.papel, CN.gris, CN.ocre, "#5a9e8a", "#9e5a7a"];

  const ox = Math.floor((W - initial.w) / 2);
  const oy = Math.floor((H - initial.h) / 2);
  initial.grid.forEach((row, y) => row.forEach((v, x) => { if (v) grid[(oy + y) * W + ox + x] = v; }));

  function neigh(c, n, e, s, w) {
    const perms = [
      `${c}${n}${e}${s}${w}`,
      `${c}${e}${s}${w}${n}`,
      `${c}${s}${w}${n}${e}`,
      `${c}${w}${n}${e}${s}`,
    ];
    for (const key of perms) if (rules[key] != null) return rules[key];
    return c;
  }

  function step() {
    const next = new Uint8Array(W * H);
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const i = y * W + x;
        const c = grid[i];
        const n = grid[((y - 1 + H) % H) * W + x];
        const e = grid[y * W + ((x + 1) % W)];
        const s = grid[((y + 1) % H) * W + x];
        const w = grid[y * W + ((x - 1 + W) % W)];
        next[i] = neigh(c, n, e, s, w);
      }
    }
    grid.set(next);
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    const cell = Math.min(w / W, h / H) * 0.85 * cam.zoom;
    cam.setTarget(W * cell * 0.5, H * cell * 0.5, clock.frame > 200 ? 0.65 : 1.1);
    cam.update(clock.dt);
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const offX = (w - W * cell) / 2;
    const offY = (h - H * cell) / 2;
    for (let y = 0; y < H; y++) {
      for (let x = 0; x < W; x++) {
        const s = grid[y * W + x];
        ctx.fillStyle = colors[s] || CN.navy;
        ctx.globalAlpha = s ? 0.95 : 1;
        ctx.fillRect(offX + x * cell, offY + y * cell, cell - 0.5, cell - 0.5);
      }
    }
    ctx.globalAlpha = 1;
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Langton (1984): tabla de transición (c,N,E,S,W)" }],
      cite: "Langton (1984), Physica D 10:135–144",
    });
  }

  function stepOnce() {
    step();
    draw();
  }

  CNCapture.boot({ runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();