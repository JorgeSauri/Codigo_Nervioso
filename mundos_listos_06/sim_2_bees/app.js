/* SIM 2 — Quórum y danza (Seeley/Visscher, ilustración EP06). CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 7);
  const sprites = [
    "bee_hang.png", "bee_scout_top.png", "bee_scout_wings_up.png", "bee_scout_side.png",
    "bee_waggle_01.png", "bee_waggle_02.png", "bee_waggle_03.png",
    "branch_cluster.png", "nest_box.png", "bee_stop_butt.png",
  ];
  let loaded = [];

  const preloadAssets = () => CNSprites.preload(sprites).then((r) => { loaded = r; });

  const SWARM_X = 0.24;
  const SWARM_Y = 0.44;
  const BRANCH_X = 0.22;
  const BRANCH_Y = 0.26;

  const sites = [
    { label: "A", x: 0.56, y: 0.36, color: CN.cian, quality: 0.95, q: 2 },
    { label: "B", x: 0.72, y: 0.50, color: CN.coral, quality: 0.62, q: 1 },
    { label: "C", x: 0.84, y: 0.38, color: "#9B8CFF", quality: 0.52, q: 0.5 },
    { label: "D", x: 0.66, y: 0.68, color: CN.ocre, quality: 0.45, q: 0.5 },
  ];

  const swarm = Array.from({ length: 260 }, () => {
    const a = rnd() * Math.PI * 2;
    const r = Math.pow(rnd(), 0.55) * 0.11;
    return {
      bx: SWARM_X + Math.cos(a) * r,
      by: SWARM_Y + Math.sin(a) * r * 0.75,
      x: SWARM_X,
      y: SWARM_Y,
      ph: rnd() * 10,
    };
  });

  const scouts = Array.from({ length: 18 }, (_, i) => ({
    site: i % sites.length,
    t: rnd() * 4,
    phase: "out",
    x: SWARM_X,
    y: SWARM_Y,
  }));

  const dancers = sites.map((s, i) => ({
    site: i,
    x: SWARM_X + (i - 1.5) * 0.028,
    y: SWARM_Y + 0.02,
    amp: 0.028 + i * 0.004,
  }));

  const stopPulses = [];
  let migrate = false;
  let winner = 0;
  const QMAX = 42;

  function drawBranch(w, h) {
    const bx = BRANCH_X * w;
    const by = BRANCH_Y * h;
    const tilt = -0.12;
    ctx.save();
    ctx.translate(bx, by);
    ctx.rotate(tilt);
    CNSprites.drawSpriteSync(ctx, "branch_cluster.png", 0, 0, Math.min(520, w * 0.32), 0, loaded[7]);
    ctx.restore();
    ctx.strokeStyle = "rgba(139,110,75,0.45)";
    ctx.lineWidth = 14;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(bx - w * 0.08, by + h * 0.01);
    ctx.quadraticCurveTo(bx, by + h * 0.04, bx + w * 0.07, by + h * 0.08);
    ctx.stroke();
  }

  function drawSwarmMass(w, h) {
    const cx = SWARM_X * w;
    const cy = SWARM_Y * h;
    const g = ctx.createRadialGradient(cx, cy, 0, cx, cy, w * 0.14);
    g.addColorStop(0, "rgba(232,197,71,0.10)");
    g.addColorStop(0.55, "rgba(232,197,71,0.04)");
    g.addColorStop(1, "rgba(11,16,32,0)");
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(cx, cy, w * 0.13, h * 0.17, 0, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawSite(s, w, h) {
    const x = s.x * w;
    const y = s.y * h;
    const base = 110 + s.quality * 80 + Math.min(40, s.q * 1.2);
    const glow = 0.25 + s.quality * 0.35 + (s.q / QMAX) * 0.25;
    ctx.fillStyle = `rgba(232,197,71,${glow * 0.35})`;
    ctx.beginPath();
    ctx.ellipse(x, y, base * 0.55, base * 0.42, 0, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "rgba(6,8,18,0.92)";
    ctx.beginPath();
    ctx.ellipse(x, y, base * 0.36, base * 0.28, 0, 0, Math.PI);
    ctx.fill();
    ctx.strokeStyle = "rgba(160,122,72,0.85)";
    ctx.lineWidth = 6;
    ctx.beginPath();
    ctx.ellipse(x, y - base * 0.06, base * 0.4, base * 0.32, 0, 0.2, Math.PI - 0.2);
    ctx.stroke();
    ctx.strokeStyle = `rgba(244,241,234,${0.25 + s.quality * 0.4})`;
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, base * 0.38, Math.PI * 1.05, Math.PI * 1.95);
    ctx.stroke();
    const ringR = base * 0.62;
    const ang = Math.min(1, s.q / QMAX) * Math.PI * 2;
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 5;
    ctx.beginPath();
    ctx.arc(x, y, ringR, -Math.PI / 2, -Math.PI / 2 + ang);
    ctx.stroke();
    ctx.strokeStyle = "rgba(138,147,166,0.35)";
    ctx.lineWidth = 2;
    ctx.beginPath();
    ctx.arc(x, y, ringR, 0, Math.PI * 2);
    ctx.stroke();
    ctx.font = 'bold 18px "CN Mono"';
    ctx.fillStyle = CN.papel;
    ctx.fillText(String(Math.floor(s.q)), x - 8, y + ringR + 22);
    ctx.font = '13px "CN Inter"';
    ctx.fillStyle = s.color;
    ctx.fillText(`sitio ${s.label}`, x - 26, y - base * 0.55);
  }

  function drawFigure8(d, w, h) {
    const site = sites[d.site];
    if (site.q < 4) return;
    const cx = d.x * w;
    const cy = d.y * h;
    const s = d.amp * w * (0.85 + Math.sin(clock.frame * 0.08) * 0.08);
    ctx.strokeStyle = site.color;
    ctx.globalAlpha = 0.28 + Math.min(0.35, site.q / QMAX);
    ctx.lineWidth = 2.5;
    ctx.beginPath();
    for (let a = 0; a <= Math.PI * 2.01; a += 0.07) {
      const px = cx + s * Math.sin(a);
      const py = cy + s * Math.sin(a) * Math.cos(a);
      a < 0.01 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.globalAlpha = 1;
    const wa = clock.frame * 0.35;
    const px = cx + s * Math.sin(wa);
    const py = cy + s * Math.sin(wa) * Math.cos(wa);
    const wig = ["bee_waggle_01.png", "bee_waggle_02.png", "bee_waggle_03.png"][(clock.frame >> 2) % 3];
    const idx = sprites.indexOf(wig);
    CNSprites.drawSpriteSync(ctx, wig, px, py, 44, Math.atan2(Math.cos(wa), Math.sin(wa)), loaded[idx]);
  }

  function drawScout(sc, w, h) {
    const name = sc.phase === "out" ? "bee_scout_side.png" : "bee_scout_wings_up.png";
    const idx = sprites.indexOf(name);
    const ang = Math.atan2(
      (sc.phase === "out" ? sites[sc.site].y : SWARM_Y) - sc.y,
      (sc.phase === "out" ? sites[sc.site].x : SWARM_X) - sc.x,
    );
    CNSprites.drawSpriteSync(ctx, name, sc.x * w, sc.y * h, 52, ang, loaded[idx]);
  }

  function drawStopPulses(w, h) {
    stopPulses.forEach((p) => {
      const life = 1 - p.age / 36;
      if (life <= 0) return;
      ctx.strokeStyle = `rgba(255,107,74,${0.45 * life})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(p.x * w, p.y * h, 12 + p.age * 2.2, 0, Math.PI * 2);
      ctx.stroke();
    });
  }

  function stepLogic() {
    const t = clock.frame;
    if (t > 500 && sites[0].q >= sites[1].q) winner = 0;
    if (t > 580) migrate = true;

    scouts.forEach((sc) => {
      const tgt = sc.phase === "out" ? sites[sc.site] : { x: SWARM_X, y: SWARM_Y };
      const dx = tgt.x - sc.x;
      const dy = tgt.y - sc.y;
      const sp = migrate ? 0.075 : 0.028;
      sc.x += dx * sp;
      sc.y += dy * sp;
      if (sc.phase === "out" && Math.hypot(dx, dy) < 0.035) {
        sites[sc.site].q += 0.35 + sites[sc.site].quality * 0.15;
        sc.phase = "return";
        stopPulses.push({ x: SWARM_X, y: SWARM_Y, age: 0 });
      } else if (sc.phase === "return" && Math.hypot(sc.x - SWARM_X, sc.y - SWARM_Y) < 0.04) {
        sc.phase = "out";
        if (!migrate) sc.site = sites[0].q < sites[1].q ? 0 : (sc.site + 1) % sites.length;
      }
      sc.t += clock.dt;
    });

    if (!migrate) {
      sites[0].q = Math.min(QMAX, sites[0].q + 0.07);
      sites[1].q = Math.min(QMAX * 0.75, sites[1].q + 0.025);
      sites[2].q = Math.min(QMAX * 0.6, sites[2].q + 0.018);
      sites[3].q = Math.min(QMAX * 0.55, sites[3].q + 0.015);
      if (sites[0].q > 10) {
        sites[1].q *= 0.996;
        sites[2].q *= 0.995;
        if ((t & 23) === 0) stopPulses.push({ x: sites[1].x, y: sites[1].y, age: 0 });
      }
    }

    swarm.forEach((b) => {
      if (migrate) {
        const tx = sites[winner].x + (rnd() - 0.5) * 0.04;
        const ty = sites[winner].y + (rnd() - 0.5) * 0.03;
        b.x += (tx - b.x) * (t > 800 ? 0.07 : 0.048);
        b.y += (ty - b.y) * (t > 800 ? 0.07 : 0.048);
      } else {
        b.x = b.bx + Math.sin(b.ph + clock.t * 2) * 0.003;
        b.y = b.by + Math.cos(b.ph * 1.3 + clock.t * 1.6) * 0.0025;
      }
    });

    for (let i = stopPulses.length - 1; i >= 0; i--) {
      stopPulses[i].age++;
      if (stopPulses[i].age > 36) stopPulses.splice(i, 1);
    }

    clock.tick();
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);
    drawBranch(w, h);
    drawSwarmMass(w, h);
    sites.forEach((s) => drawSite(s, w, h));
    swarm.forEach((b) => {
      CNSprites.drawSpriteSync(
        ctx, "bee_hang.png",
        w * b.x, h * b.y,
        migrate ? 34 : 28,
        Math.sin(b.ph + clock.t) * 0.12,
        loaded[0],
      );
    });
    dancers.forEach((d) => drawFigure8(d, w, h));
    scouts.forEach((sc) => drawScout(sc, w, h));
    drawStopPulses(w, h);
    if (migrate && (clock.frame & 7) === 0) {
      CNSprites.drawSpriteSync(ctx, "bee_stop_butt.png", w * SWARM_X, h * SWARM_Y, 32, 0, loaded[9]);
    }
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
    return swarm.length > 200 && sites.length === 4;
  }

  draw();

  CNCapture.boot({
    preloadAssets,
    warmup: async () => { for (let i = 0; i < 20; i++) stepOnce(); },
    verify: verifyPattern,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();