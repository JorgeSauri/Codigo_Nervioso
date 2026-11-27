/* SIM 4B — Jones (2010) agentes, no Tero. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const GW = 160, GH = 120;
  const trail = new Float32Array(GW * GH);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 42);
  const agents = Array.from({ length: 120 }, () => ({
    x: rnd() * GW,
    y: rnd() * GH,
    a: rnd() * Math.PI * 2,
  }));
  let sp;
  const preloadAssets = () => CNSprites.preload(["physarum_agent.png"]).then((r) => { sp = r[0]; });

  function step() {
    const sense = 3;
    agents.forEach((ag) => {
      const lx = Math.cos(ag.a - 0.5), ly = Math.sin(ag.a - 0.5);
      const rx = Math.cos(ag.a + 0.5), ry = Math.sin(ag.a + 0.5);
      const fx = Math.cos(ag.a), fy = Math.sin(ag.a);
      const vL = trail[((ag.y + ly * sense) | 0) * GW + ((ag.x + lx * sense) | 0)] || 0;
      const vR = trail[((ag.y + ry * sense) | 0) * GW + ((ag.x + rx * sense) | 0)] || 0;
      const vF = trail[((ag.y + fy * sense) | 0) * GW + ((ag.x + fx * sense) | 0)] || 0;
      if (vL > vR) ag.a -= 0.25;
      else if (vR > vL) ag.a += 0.25;
      if (vF < 0.05) ag.a += (rnd() - 0.5) * 0.5;
      ag.x = (ag.x + Math.cos(ag.a) * 1.2 + GW) % GW;
      ag.y = (ag.y + Math.sin(ag.a) * 1.2 + GH) % GH;
      const i = (ag.y | 0) * GW + (ag.x | 0);
      trail[i] = Math.min(1, trail[i] + 0.35);
    });
    for (let i = 0; i < trail.length; i++) trail[i] *= 0.992;
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const sc = Math.min(w / GW, h / GH);
    for (let y = 0; y < GH; y++) {
      for (let x = 0; x < GW; x++) {
        const v = trail[y * GW + x];
        if (v < 0.03) continue;
        ctx.fillStyle = `rgba(232,197,71,${v * 0.85})`;
        ctx.fillRect(x * sc, y * sc, sc, sc);
      }
    }
    agents.forEach((ag) => {
      CNSprites.drawSpriteSync(ctx, "physarum_agent.png", ag.x * sc, ag.y * sc, 12, ag.a, sp);
    });
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [
        { text: "Modelo de Jones (2010). No es el de Tero, no es Tokio.", color: CN.papel },
      ],
      cite: "Jones (2010), Artificial Life 16(2):127–153",
    });
  }

  function stepOnce() { step(); draw(); }
  CNCapture.boot({ preloadAssets, runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); }, stepOnce });
})();