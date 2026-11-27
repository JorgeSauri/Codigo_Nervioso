/* SIM 2 — Ilustración Seeley/Visscher (no réplica). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed);
  const sprites = ["bee_scout_top.png", "bee_scout_wings_up.png", "bee_hang.png", "nest_box.png", "branch_cluster.png"];
  let loaded = [];
  const preloadAssets = () => CNSprites.preload(sprites).then((r) => { loaded = r; });

  const boxes = [
    { x: 0.22, y: 0.7, q: 0, label: "A" },
    { x: 0.74, y: 0.66, q: 0, label: "B" },
  ];
  const scouts = Array.from({ length: 58 }, (_, i) => ({
    x: 0.2 + rnd() * 0.62,
    y: 0.26 + rnd() * 0.44,
    home: rnd() > 0.38 ? 0 : 1,
    vx: (rnd() - 0.5) * 0.008,
    vy: (rnd() - 0.5) * 0.008,
    phase: i % 3,
    t: rnd() * 10,
  }));
  boxes[0].q = 11;
  boxes[1].q = 5;
  const historyA = [];
  const historyB = [];
  for (let i = 0; i < 48; i++) {
    historyA.push(Math.min(20, 2 + i * 0.22));
    historyB.push(Math.min(12, 1 + i * 0.1));
  }

  function drawChart(w, h) {
    const chartW = opts.formato === "9x16" ? w * 0.92 : w * 0.34;
    const chartH = opts.formato === "9x16" ? h * 0.24 : h * 0.3;
    const x0 = opts.formato === "9x16" ? w * 0.04 : w * 0.6;
    const y0 = opts.formato === "9x16" ? h * 0.58 : h * 0.54;
    ctx.save();
    ctx.translate(x0, y0);
    ctx.fillStyle = "rgba(11,16,32,0.72)";
    ctx.strokeStyle = CN.gris;
    ctx.lineWidth = 1;
    ctx.fillRect(0, 0, chartW, chartH);
    ctx.strokeRect(0.5, 0.5, chartW - 1, chartH - 1);
    ctx.strokeStyle = CN.cian;
    ctx.lineWidth = 3;
    ctx.beginPath();
    historyA.forEach((a, i) => {
      const px = 48 + (i / Math.max(1, historyA.length - 1)) * (chartW - 58);
      const py = chartH - 28 - (a / 22) * (chartH - 40);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.stroke();
    ctx.strokeStyle = CN.coral;
    ctx.lineWidth = 2;
    ctx.beginPath();
    historyB.forEach((b, i) => {
      const px = 48 + (i / Math.max(1, historyB.length - 1)) * (chartW - 58);
      const py = chartH - 28 - (b / 22) * (chartH - 40);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.stroke();
    const band = chartH - 28 - (12 / 22) * (chartH - 40);
    ctx.setLineDash([8, 5]);
    ctx.strokeStyle = CN.gris;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(48, band);
    ctx.lineTo(chartW - 12, band);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.font = '13px "CN Mono"';
    ctx.fillStyle = CN.papel;
    ctx.fillText("sitio A", 48, 20);
    ctx.fillStyle = CN.cian;
    ctx.fillText(String(Math.floor(boxes[0].q)), 108, 20);
    ctx.fillStyle = CN.papel;
    ctx.fillText("sitio B", 168, 20);
    ctx.fillStyle = CN.coral;
    ctx.fillText(String(Math.floor(boxes[1].q)), 228, 20);
    ctx.fillStyle = CN.gris;
    ctx.font = '11px "CN Inter"';
    ctx.fillText("unas 10–15 o más (observado)", 48, band - 8);
    ctx.restore();
  }

  function stepLogic() {
    scouts.forEach((s) => {
      const box = boxes[s.home];
      const tx = box.x, ty = box.y - 0.05;
      s.vx += (tx - s.x) * 0.04;
      s.vy += (ty - s.y) * 0.04;
      s.vx *= 0.88;
      s.vy *= 0.88;
      s.x += s.vx;
      s.y += s.vy;
      if (Math.hypot(s.x - tx, s.y - ty) < 0.04) {
        box.q += 0.28;
        s.home = boxes[0].q < boxes[1].q ? 0 : 1;
      }
      s.t += clock.dt;
    });
    boxes[0].q = Math.min(22, boxes[0].q);
    boxes[1].q = Math.min(22, boxes[1].q);
    historyA.push(boxes[0].q);
    historyB.push(boxes[1].q);
    if (historyA.length > 180) historyA.shift(), historyB.shift();
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    CNSprites.drawSpriteSync(ctx, "branch_cluster.png", w * 0.5, h * 0.11, Math.min(320, w * 0.28), 0, loaded[4]);
    for (let i = 0; i < 55; i++) {
      const jx = (i % 11) * 0.028 - 0.14;
      const jy = Math.floor(i / 11) * 0.032;
      CNSprites.drawSpriteSync(ctx, "bee_hang.png", w * (0.38 + jx), h * (0.08 + jy), 40, (i % 7) * 0.1, loaded[2]);
    }
    boxes.forEach((b) => {
      CNSprites.drawSpriteSync(ctx, "nest_box.png", w * b.x, h * b.y, 172, 0, loaded[3]);
    });
    scouts.forEach((s) => {
      const name = s.phase === 1 && loaded[1]?.ok ? "bee_scout_wings_up.png" : "bee_scout_top.png";
      const sp = name === "bee_scout_wings_up.png" ? loaded[1] : loaded[0];
      if (Math.floor(s.t * 4) % 3 === 1) s.phase = 1; else s.phase = 0;
      const ang = Math.atan2(s.vy, s.vx);
      CNSprites.drawSpriteSync(ctx, name, w * s.x, h * s.y, 78, ang, sp);
    });
    drawChart(w, h);
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Ilustración inspirada en Seeley y Visscher, no una réplica." }],
      cite: "Seeley & Visscher (2003); (2004); (2012) Science 335:108–111",
    });
  }

  function stepOnce() {
    stepLogic();
    draw();
  }

  CNCapture.boot({
    preloadAssets,
    warmup: async () => { for (let i = 0; i < 45; i++) stepOnce(); },
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();