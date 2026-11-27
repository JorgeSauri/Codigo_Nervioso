/* SIM 4B — Jones (2010) Physarum por agentes. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const SA = (45 * Math.PI) / 180;
  const RA = 0.3;
  const SO = 9;
  const DT_DEP = 20;
  const SPEED = 2.2;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const GW = 280;
  const GH = 200;
  const trail = new Float32Array(GW * GH);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 42);
  const N = 420;
  const agents = Array.from({ length: N }, () => ({
    x: rnd() * GW,
    y: rnd() * GH,
    a: rnd() * Math.PI * 2,
  }));

  const food = [
    { x: 0.22, y: 0.45 },
    { x: 0.78, y: 0.55 },
    { x: 0.5, y: 0.82 },
  ];

  function sense(ag, offAng) {
    const sx = ag.x + Math.cos(ag.a + offAng) * SO;
    const sy = ag.y + Math.sin(ag.a + offAng) * SO;
    const ix = ((sx | 0) + GW) % GW;
    const iy = ((sy | 0) + GH) % GH;
    return trail[iy * GW + ix] || 0;
  }

  function step() {
    agents.forEach((ag) => {
      const vL = sense(ag, -SA);
      const vR = sense(ag, SA);
      if (vL > vR) ag.a -= RA;
      else if (vR > vL) ag.a += RA;
      else ag.a += (rnd() - 0.5) * 0.08;
      ag.x = (ag.x + Math.cos(ag.a) * SPEED + GW) % GW;
      ag.y = (ag.y + Math.sin(ag.a) * SPEED + GH) % GH;
      const i = (ag.y | 0) * GW + (ag.x | 0);
      trail[i] = Math.min(1, trail[i] + 1 / DT_DEP);
    });
    for (let i = 0; i < trail.length; i++) trail[i] *= 1 - 1 / DT_DEP;
    food.forEach((f) => {
      const cx = (f.x * GW) | 0;
      const cy = (f.y * GH) | 0;
      for (let dy = -3; dy <= 3; dy++) {
        for (let dx = -3; dx <= 3; dx++) {
          const j = ((cy + dy + GH) % GH) * GW + ((cx + dx + GW) % GW);
          trail[j] = Math.min(1, trail[j] + 0.08);
        }
      }
    });
    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const sc = Math.min(w / GW, h / GH) * 0.94;
    const ox = (w - GW * sc) / 2;
    const oy = (h - GH * sc) / 2;

    const img = ctx.createImageData(GW, GH);
    for (let i = 0; i < trail.length; i++) {
      const v = trail[i];
      const i4 = i * 4;
      if (v < 0.02) {
        img.data[i4] = 7;
        img.data[i4 + 1] = 11;
        img.data[i4 + 2] = 22;
      } else {
        const t = Math.min(1, v * 1.1);
        img.data[i4] = Math.round(20 + t * 220);
        img.data[i4 + 1] = Math.round(30 + t * 180);
        img.data[i4 + 2] = Math.round(40 + t * 80);
      }
      img.data[i4 + 3] = 255;
    }
    const off = document.createElement("canvas");
    off.width = GW;
    off.height = GH;
    off.getContext("2d").putImageData(img, 0, 0);
    ctx.imageSmoothingEnabled = true;
    ctx.drawImage(off, ox, oy, GW * sc, GH * sc);

    ctx.globalCompositeOperation = "lighter";
    agents.forEach((ag) => {
      const px = ox + ag.x * sc;
      const py = oy + ag.y * sc;
      ctx.fillStyle = "rgba(255,240,180,0.85)";
      ctx.beginPath();
      ctx.arc(px, py, 1.8, 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalCompositeOperation = "source-over";

    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Jones (2010): quimiotaxis con depósito SA, RA, SO" }],
      counters: [
        { text: `SA=45° RA=${RA} SO=${SO} Dt=${DT_DEP}` },
        { text: `agentes N=${N}` },
      ],
      cite: "Jones (2010) Artificial Life 16(2):127–153",
    });
  }

  function stepOnce() { step(); draw(); }
  draw();
  CNCapture.boot({
    verify: () => agents.length > 200,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();