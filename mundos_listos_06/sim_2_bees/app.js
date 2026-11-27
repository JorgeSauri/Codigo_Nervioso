/* SIM 2 — Ilustración Seeley/Visscher (no réplica). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed);
  const sprites = ["bee_scout_top.png", "bee_hang.png", "nest_box.png", "branch_cluster.png"];
  let loaded = [];
  CNSprites.preload(sprites).then((r) => { loaded = r; });

  const boxes = [
    { x: 0.25, y: 0.72, q: 0, qual: 0.85, label: "A" },
    { x: 0.72, y: 0.68, q: 0, qual: 0.35, label: "B" },
  ];
  const scouts = Array.from({ length: 18 }, (_, i) => ({
    x: 0.5 + (rnd() - 0.5) * 0.15,
    y: 0.22 + rnd() * 0.08,
    target: boxes[rnd() > 0.6 ? 0 : 1],
    wing: i % 3,
    t: rnd() * 10,
  }));
  const historyA = [], historyB = [];

  function drawChart(w, h) {
    const chartW = opts.formato === "9x16" ? w * 0.9 : w * 0.32;
    const chartH = opts.formato === "9x16" ? h * 0.22 : h * 0.28;
    const x0 = opts.formato === "9x16" ? w * 0.05 : w * 0.62;
    const y0 = opts.formato === "9x16" ? h * 0.62 : h * 0.58;
    ctx.save();
    ctx.translate(x0, y0);
    ctx.strokeStyle = CN.cian;
    ctx.beginPath();
    historyA.forEach((a, i) => {
      const px = 40 + (i / Math.max(1, historyA.length)) * (chartW - 50);
      const py = chartH - 20 - (a / 18) * (chartH - 30);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.stroke();
    ctx.strokeStyle = CN.gris;
    ctx.beginPath();
    historyB.forEach((b, i) => {
      const px = 40 + (i / Math.max(1, historyB.length)) * (chartW - 50);
      const py = chartH - 20 - (b / 18) * (chartH - 30);
      i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
    });
    ctx.stroke();
    const band = chartH - 20 - (12 / 18) * (chartH - 30);
    ctx.setLineDash([6, 4]);
    ctx.strokeStyle = CN.gris;
    ctx.beginPath();
    ctx.moveTo(40, band);
    ctx.lineTo(chartW - 10, band);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.fillStyle = CN.gris;
    ctx.font = '10px "CN Inter"';
    ctx.fillText("unas 10–15 o más (observado)", 44, band - 6);
    ctx.restore();
  }

  function stepLogic() {
    scouts.forEach((s) => {
      s.t += clock.dt;
      const bx = s.target.x, by = s.target.y;
      s.x += (bx - s.x) * 0.02;
      s.y += (by - s.y) * 0.02;
      if (Math.hypot(s.x - bx, s.y - by) < 0.03) {
        s.target.q++;
        s.target = boxes[0];
      }
    });
    historyA.push(boxes[0].q);
    historyB.push(boxes[1].q);
    if (historyA.length > 120) historyA.shift(), historyB.shift();
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    CNSprites.drawSpriteSync(ctx, "branch_cluster.png", w * 0.5, h * 0.14, 180, 0, loaded[3]);
    for (let i = 0; i < 40; i++) {
      CNSprites.drawSpriteSync(ctx, "bee_hang.png", w * (0.35 + (i % 10) * 0.03), h * (0.12 + Math.floor(i / 10) * 0.04), 22, 0, loaded[1]);
    }
    boxes.forEach((b) => {
      CNSprites.drawSpriteSync(ctx, "nest_box.png", w * b.x, h * b.y, 90, 0, loaded[2]);
      ctx.font = `14px "CN Mono"`;
      ctx.fillStyle = CN.papel;
      ctx.fillText(`sitio ${b.label} ${Math.round(b.q)}`, w * b.x - 30, h * b.y + 55);
    });
    scouts.forEach((s) => {
      CNSprites.drawSpriteSync(ctx, "bee_scout_top.png", w * s.x, h * s.y, 28, 0, loaded[0]);
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

  CNCapture.boot({ runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();