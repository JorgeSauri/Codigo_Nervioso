/* SIM 1D — Lenia ampliada (Chan 2020). Sin replicador confirmado en esta toma. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const NOTE =
    "Parámetros de autorréplica no confirmados (Chan 2020 / Chakazul/Lenia). Esta toma muestra Lenia multicanal ilustrativo, no un patrón del paper.";

  function draw() {
    const { w, h } = opts;
    const t = clock.t;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const cx = w * (0.4 + 0.05 * Math.sin(t * 0.4));
    const cy = h * 0.48;
    const g = ctx.createRadialGradient(cx, cy, 10, cx, cy, w * 0.22);
    g.addColorStop(0, "rgba(0,229,199,0.85)");
    g.addColorStop(0.5, "rgba(0,120,105,0.35)");
    g.addColorStop(1, "rgba(11,16,32,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.arc(cx, cy, w * 0.18, 0, Math.PI * 2);
    ctx.fill();
  if (t > 4) {
      const cx2 = cx + 120 + t * 18;
      const g2 = ctx.createRadialGradient(cx2, cy, 8, cx2, cy, 70);
      g2.addColorStop(0, "rgba(244,241,234,0.5)");
      g2.addColorStop(1, "rgba(11,16,32,0)");
      ctx.fillStyle = g2;
      ctx.beginPath();
      ctx.arc(cx2, cy, 60, 0, Math.PI * 2);
      ctx.fill();
    }
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [
        { text: "Lenia ampliada · Chan (2020)" },
        { text: NOTE, color: CN.coral },
      ],
      cite: "Chan (2020), ALIFE 2020 — sin parámetros de replicador verificados",
    });
  }

  function stepOnce() {
    clock.tick();
    draw();
  }

  CNCapture.boot({ runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();