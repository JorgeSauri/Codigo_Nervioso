/* SIM 4B — Jones (2010) Physarum, CPU Float32 + depósito bilineal. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const SA = (45 * Math.PI) / 180;
  const RA = (45 * Math.PI) / 180;
  const SO = 9;
  const SPEED = 1.05;
  const DECAY = 0.94;
  const DIFFUSE = 0.2;
  const DEPOSIT = 0.26;
  const TW = 480;
  const TH = 270;
  const N = 80000;

  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 42);

  const ax = new Float32Array(N);
  const ay = new Float32Array(N);
  const aa = new Float32Array(N);
  for (let i = 0; i < N; i++) {
    ax[i] = rnd() * TW;
    ay[i] = rnd() * TH;
    aa[i] = rnd() * Math.PI * 2;
  }

  let trail = new Float32Array(TW * TH);
  let trailN = new Float32Array(TW * TH);
  const foods = [
    { x: TW * 0.22, y: TH * 0.48 },
    { x: TW * 0.78, y: TH * 0.40 },
    { x: TW * 0.52, y: TH * 0.78 },
  ];

  function sample(x, y) {
    x = ((x % TW) + TW) % TW;
    y = ((y % TH) + TH) % TH;
    const x0 = x | 0;
    const y0 = y | 0;
    const x1 = (x0 + 1) % TW;
    const y1 = (y0 + 1) % TH;
    const tx = x - x0;
    const ty = y - y0;
    const i00 = trail[y0 * TW + x0];
    const i10 = trail[y0 * TW + x1];
    const i01 = trail[y1 * TW + x0];
    const i11 = trail[y1 * TW + x1];
    return (i00 * (1 - tx) + i10 * tx) * (1 - ty) + (i01 * (1 - tx) + i11 * tx) * ty;
  }

  function splat(x, y, amount) {
    x = ((x % TW) + TW) % TW;
    y = ((y % TH) + TH) % TH;
    const x0 = x | 0;
    const y0 = y | 0;
    const tx = x - x0;
    const ty = y - y0;
    const x1 = (x0 + 1) % TW;
    const y1 = (y0 + 1) % TH;
    trail[y0 * TW + x0] += amount * (1 - tx) * (1 - ty);
    trail[y0 * TW + x1] += amount * tx * (1 - ty);
    trail[y1 * TW + x0] += amount * (1 - tx) * ty;
    trail[y1 * TW + x1] += amount * tx * ty;
  }

  function stepAgents() {
    for (let i = 0; i < N; i++) {
      const a = aa[i];
      const x = ax[i];
      const y = ay[i];
      const cL = Math.cos(a - SA);
      const sL = Math.sin(a - SA);
      const cR = Math.cos(a + SA);
      const sR = Math.sin(a + SA);
      const vL = sample(x + cL * SO, y + sL * SO);
      const vR = sample(x + cR * SO, y + sR * SO);
      const vF = sample(x + Math.cos(a) * SO, y + Math.sin(a) * SO);
      let na = a;
      if (vL > vR && vL >= vF) na -= RA;
      else if (vR > vL && vR >= vF) na += RA;
      ax[i] = (x + Math.cos(na) * SPEED + TW) % TW;
      ay[i] = (y + Math.sin(na) * SPEED + TH) % TH;
      aa[i] = na;
      splat(ax[i], ay[i], DEPOSIT);
    }
    foods.forEach((f) => {
      for (let dy = -2; dy <= 2; dy++) {
        for (let dx = -2; dx <= 2; dx++) {
          const xx = (f.x + dx + TW) % TW;
          const yy = (f.y + dy + TH) % TH;
          trail[(yy | 0) * TW + (xx | 0)] += 0.55;
        }
      }
    });
    for (let y = 0; y < TH; y++) {
      const ym = (y - 1 + TH) % TH;
      const yp = (y + 1) % TH;
      for (let x = 0; x < TW; x++) {
        const xm = (x - 1 + TW) % TW;
        const xp = (x + 1) % TW;
        const c = trail[y * TW + x];
        const avg = (trail[ym * TW + x] + trail[yp * TW + x] + trail[y * TW + xm] + trail[y * TW + xp]) * 0.25;
        trailN[y * TW + x] = (c * (1 - DIFFUSE) + avg * DIFFUSE) * DECAY;
      }
    }
    const swap = trail;
    trail = trailN;
    trailN = swap;
  }

  const off = document.createElement("canvas");
  off.width = TW;
  off.height = TH;
  const octx = off.getContext("2d");

  function paint() {
    const img = octx.createImageData(TW, TH);
    for (let i = 0; i < trail.length; i++) {
      const v = trail[i];
      const i4 = i * 4;
      if (v < 0.035) {
        img.data[i4] = 7;
        img.data[i4 + 1] = 11;
        img.data[i4 + 2] = 22;
      } else {
        const t = Math.min(1, (v - 0.035) / 1.1);
        img.data[i4] = Math.round(30 + t * 225);
        img.data[i4 + 1] = Math.round(18 + t * 175);
        img.data[i4 + 2] = Math.round(8 + t * 70 + (t > 0.72 ? (t - 0.72) * 400 : 0));
      }
      img.data[i4 + 3] = 255;
    }
    octx.putImageData(img, 0, 0);
  }

  function draw() {
    const { w, h } = opts;
    paint();
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    const pw = w * 0.92;
    const ph = h * 0.82;
    ctx.imageSmoothingEnabled = true;
    ctx.imageSmoothingQuality = "high";
    ctx.drawImage(off, (w - pw) / 2, h * 0.06, pw, ph);
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Jones (2010): sensores ±SA, giro RA, SO, depósito bilineal + difusión + decaimiento" }],
      counters: [
        { text: `SA=45° RA=45° SO=${SO} N=${N}` },
        { text: `Float32 · trail ${TW}×${TH}` },
      ],
      cite: "Jones (2010) Artificial Life 16(2):127–153",
    });
  }

  for (let i = 0; i < 90; i++) stepAgents();

  function stepOnce() {
    stepAgents();
    clock.tick();
    draw();
  }

  draw();
  CNCapture.boot({
    verify: () => N >= 50000 && trail.some((v) => v > 0.2),
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
