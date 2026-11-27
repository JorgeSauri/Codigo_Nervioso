/* SIM 2 — Quórum y danza (Seeley/Visscher, ilustración). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed);
  const sprites = [
    "bee_scout_top.png", "bee_scout_wings_up.png", "bee_scout_wings_down.png",
    "bee_hang.png", "nest_box.png", "branch_cluster.png",
    "bee_waggle_01.png", "bee_waggle_02.png", "bee_waggle_03.png", "bee_scout_side.png",
  ];
  let loaded = [];
  const preloadAssets = () => CNSprites.preload(sprites).then((r) => { loaded = r; });

  const siteColors = [CN.cian, CN.coral, "#b48cff", "#7dffb2", "#ffb347"];
  const sites = [
    { x: 0.16, y: 0.74, q: 0, label: "A" },
    { x: 0.32, y: 0.8, q: 0, label: "B" },
    { x: 0.52, y: 0.72, q: 0, label: "C" },
    { x: 0.7, y: 0.78, q: 0, label: "D" },
    { x: 0.86, y: 0.7, q: 0, label: "E" },
  ].map((s, i) => ({ ...s, color: siteColors[i] }));

  const hang = Array.from({ length: 140 }, (_, i) => {
    const a = (i / 140) * Math.PI * 2.4 - 1.1;
    const r = 0.018 + (i % 7) * 0.0045;
    return {
      ox: 0.46 + Math.cos(a) * r + (rnd() - 0.5) * 0.012,
      oy: 0.07 + Math.sin(a) * r * 0.7 + (i % 5) * 0.005,
      x: 0, y: 0,
      phase: rnd() * 10,
      onBranch: true,
    };
  });

  const scouts = Array.from({ length: 36 }, (_, i) => ({
    x: 0.48 + (rnd() - 0.5) * 0.1,
    y: 0.22 + rnd() * 0.08,
    site: i % sites.length,
    t: rnd() * 6,
    trail: [],
    waggle: 0,
  }));

  let winner = -1;
  let migrate = false;
  const quorumMax = 48;

  function pickWinner() {
    let idx = 0;
    for (let i = 1; i < sites.length; i++) if (sites[i].q > sites[idx].q) idx = i;
    return idx;
  }

  function stepLogic() {
    const t = clock.frame;
    if (t > 420 && winner < 0) winner = pickWinner();
    if (t > 520 && winner >= 0) migrate = true;

    scouts.forEach((s) => {
      const site = sites[s.site];
      const tx = site.x;
      const ty = site.y - 0.06;
      if (!migrate) {
        s.waggle = (Math.floor(t / 8) + s.site) % 3;
        const wob = Math.sin(s.t * 5) * 0.012;
        s.x += (tx - s.x) * 0.035 + wob;
        s.y += (ty - s.y) * 0.035 + Math.cos(s.t * 4) * 0.01;
        if (Math.hypot(s.x - tx, s.y - ty) < 0.05) {
          site.q += 0.22 + (s.site === 0 ? 0.08 : 0.04);
          s.site = (s.site + 1 + Math.floor(rnd() * 2)) % sites.length;
        }
        s.trail.push({ x: s.x, y: s.y, c: site.color });
        if (s.trail.length > 28) s.trail.shift();
      } else {
        const w = sites[winner];
        s.x += (w.x - s.x) * 0.055;
        s.y += (w.y - s.y) * 0.055;
      }
      s.t += clock.dt;
    });

    if (!migrate) {
      sites[0].q = Math.min(quorumMax, sites[0].q + 0.05);
      sites.forEach((s, i) => {
        if (i > 0) s.q = Math.min(quorumMax * 0.65, s.q + 0.012 + (i === 1 ? 0.01 : 0));
      });
    }

    hang.forEach((b) => {
      if (migrate && winner >= 0) {
        const w = sites[winner];
        b.x += ((w.x + (rnd() - 0.5) * 0.04) - b.x) * 0.04;
        b.y += ((w.y - 0.12 + (rnd() - 0.5) * 0.03) - b.y) * 0.04;
        b.onBranch = false;
      } else {
        b.x = b.ox;
        b.y = b.oy;
      }
    });

    clock.tick();
  }

  function drawQuorumBars(w, h) {
    const pad = 24;
    const barW = opts.formato === "9x16" ? w * 0.88 : w * 0.38;
    const barH = opts.formato === "9x16" ? h * 0.22 : h * 0.32;
    const x0 = opts.formato === "9x16" ? w * 0.06 : w * 0.56;
    const y0 = opts.formato === "9x16" ? h * 0.58 : h * 0.52;
    const colW = (barW - pad * 2) / sites.length;
    ctx.save();
    ctx.translate(x0, y0);
    ctx.fillStyle = "rgba(8,12,26,0.85)";
    ctx.strokeStyle = CN.gris;
    ctx.fillRect(0, 0, barW, barH);
    ctx.strokeRect(0.5, 0.5, barW - 1, barH - 1);
    const threshY = barH - pad - (14 / quorumMax) * (barH - pad * 2);
    ctx.setLineDash([6, 5]);
    ctx.strokeStyle = CN.gris;
    ctx.beginPath();
    ctx.moveTo(pad, threshY);
    ctx.lineTo(barW - pad, threshY);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.font = '12px "CN Inter"';
    ctx.fillStyle = CN.gris;
    ctx.fillText("quórum ~10–15 (ilustrado)", pad, threshY - 8);
    sites.forEach((s, i) => {
      const cx = pad + colW * i + colW * 0.5;
      const hFill = ((barH - pad * 2) * Math.min(1, s.q / quorumMax));
      ctx.fillStyle = "rgba(255,255,255,0.08)";
      ctx.fillRect(cx - colW * 0.28, pad, colW * 0.56, barH - pad * 2);
      ctx.fillStyle = s.color;
      ctx.fillRect(cx - colW * 0.28, barH - pad - hFill, colW * 0.56, hFill);
      if (winner === i && migrate) {
        ctx.strokeStyle = CN.papel;
        ctx.lineWidth = 3;
        ctx.strokeRect(cx - colW * 0.28 - 2, pad - 4, colW * 0.56 + 4, barH - pad * 2 + 8);
      }
      ctx.font = 'bold 14px "CN Mono"';
      ctx.fillStyle = CN.papel;
      ctx.fillText(s.label, cx - 5, barH - 6);
      ctx.font = '13px "CN Mono"';
      ctx.fillStyle = s.color;
      ctx.fillText(String(Math.floor(s.q)), cx - 8, pad + 16);
    });
    ctx.restore();
  }

  function drawTrails(w, h) {
    scouts.forEach((s) => {
      if (s.trail.length < 2) return;
      const col = sites[s.site]?.color || CN.cian;
      ctx.strokeStyle = col;
      ctx.lineWidth = 3;
      ctx.globalAlpha = 0.45;
      ctx.beginPath();
      s.trail.forEach((p, i) => {
        const px = p.x * w, py = p.y * h;
        i ? ctx.lineTo(px, py) : ctx.moveTo(px, py);
      });
      ctx.stroke();
      ctx.globalAlpha = 1;
    });
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
  CNSprites.drawSpriteSync(ctx, "branch_cluster.png", w * 0.48, h * 0.1, Math.min(420, w * 0.36), 0, loaded[5]);
    hang.forEach((b) => {
      const hx = (migrate ? b.x : b.ox) * w;
      const hy = (migrate ? b.y : b.oy) * h;
      const sz = migrate ? 52 : 46;
      CNSprites.drawSpriteSync(ctx, "bee_hang.png", hx, hy, sz, Math.sin(b.phase + clock.t) * 0.08, loaded[3]);
    });
    sites.forEach((s, si) => {
      const scale = winner === si && migrate ? 210 : 188;
      CNSprites.drawSpriteSync(ctx, "nest_box.png", w * s.x, h * s.y, scale, 0, loaded[4]);
      ctx.font = 'bold 20px "CN Mono"';
      ctx.fillStyle = s.color;
      ctx.fillText(`sitio ${s.label}`, w * s.x - 42, h * s.y - scale * 0.55);
    });
    drawTrails(w, h);
    scouts.forEach((s) => {
      const names = ["bee_waggle_01.png", "bee_waggle_02.png", "bee_waggle_03.png"];
      const name = migrate ? "bee_scout_side.png" : names[s.waggle];
      const idx = sprites.indexOf(name);
      const sp = loaded[idx];
      const tgt = migrate && winner >= 0 ? sites[winner] : sites[s.site];
      const ang = Math.atan2(tgt.y - s.y, tgt.x - s.x);
      CNSprites.drawSpriteSync(ctx, name, w * s.x, h * s.y, migrate ? 88 : 96, ang, sp);
    });
    drawQuorumBars(w, h);
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

  function verifyPattern() {
    return sites.some((s) => s.q >= 0) && hang.length > 80;
  }

  draw();

  CNCapture.boot({
    preloadAssets,
    warmup: async () => { for (let i = 0; i < 5; i++) stepOnce(); },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();