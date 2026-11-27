/* SIM 2 — Seeley/Visscher/Passino: reclutamiento, quórum, stop signals. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 7);

  /* Passino et al. / Seeley: calidad relativa de sitios, quórum ~20–30 defensores */
  const QUORUM = 26;
  const SITES = [
    { x: 0.58, y: 0.38, quality: 0.92, color: CN.cian, A: 2 },
    { x: 0.74, y: 0.48, quality: 0.58, color: CN.coral, A: 0.5 },
    { x: 0.82, y: 0.62, quality: 0.48, color: "#9B8CFF", A: 0.5 },
    { x: 0.66, y: 0.70, quality: 0.40, color: CN.ocre, A: 0.5 },
  ];
  const SW = { x: 0.28, y: 0.48 };
  const K_R = 0.016;
  const K_DEC = 0.012;
  const K_STOP = 0.034;
  const N_SWARM = 1400;
  const N_SCOUT = 56;

  const swarm = Array.from({ length: N_SWARM }, () => {
    const a = rnd() * Math.PI * 2;
    const r = Math.pow(rnd(), 0.48) * 0.09;
    return {
      bx: Math.cos(a) * r,
      by: Math.sin(a) * r * 0.82,
      site: -1,
    };
  });

  const scouts = Array.from({ length: N_SCOUT }, (_, i) => ({
    site: i % SITES.length,
    x: SW.x,
    y: SW.y,
    phase: "search",
    t: rnd() * 2,
  }));

  const dances = SITES.map((s, i) => ({
    site: i,
    active: 0,
    angle: (i / SITES.length) * Math.PI * 2,
  }));

  let migrated = false;
  let winner = 0;
  const stopFlash = [];

  function clusterCenter() {
    if (!migrated) return SW;
    const s = SITES[winner];
    const t = Math.min(1, (clock.frame - migrateT) / 360);
    const ease = t * t * (3 - 2 * t);
    return {
      x: SW.x + (s.x - SW.x) * ease,
      y: SW.y + (s.y - SW.y) * ease,
    };
  }
  let migrateT = 99999;

  function stepDynamics() {
    const t = clock.frame;

    scouts.forEach((sc) => {
      const tgt = sc.phase === "search" ? SITES[sc.site] : SW;
      const dx = tgt.x - sc.x;
      const dy = tgt.y - sc.y;
      const d = Math.hypot(dx, dy) || 1e-6;
      const sp = sc.phase === "search" ? 0.022 : 0.026;
      sc.x += (dx / d) * sp;
      sc.y += (dy / d) * sp;
      if (sc.phase === "search" && d < 0.03) {
        sc.phase = "return";
        const q = SITES[sc.site].quality * (0.85 + rnd() * 0.15);
        dances[sc.site].active += q * 0.45;
        SITES[sc.site].A += q * 0.1;
      } else if (sc.phase === "return" && Math.hypot(sc.x - SW.x, sc.y - SW.y) < 0.035) {
        sc.phase = "search";
        sc.site = (sc.site + 1 + (rnd() < SITES[0].quality ? 0 : 1)) % SITES.length;
      }
    });

    SITES.forEach((s, i) => {
      let inh = 0;
      SITES.forEach((o, j) => {
        if (j === i) return;
        inh += K_STOP * o.A * dances[j].active * 0.02;
      });
      const rec = K_R * dances[i].active * s.quality;
      s.A += rec - K_DEC * s.A - inh;
      if (s.A < 0) s.A = 0;
      dances[i].active *= 0.992;
      if ((t & 31) === 0 && inh > 0.05) stopFlash.push({ x: SW.x, y: SW.y, site: i, age: 0 });
    });

    if (!migrated && SITES[0].A >= QUORUM) {
      migrated = true;
      migrateT = t;
      winner = 0;
    }

    const c = clusterCenter();
    const scale = migrated ? 1 - 0.18 * Math.min(1, (t - migrateT) / 360) : 1;
    swarm.forEach((b) => {
      if (migrated) {
        const pull = SITES[winner];
        const bias = b.site < 0 ? 0 : (b.site === winner ? 0.012 : -0.006);
        b.site = winner;
        const ox = b.bx * scale;
        const oy = b.by * scale;
        const tx = pull.x + ox * 0.65 + bias;
        const ty = pull.y + oy * 0.65;
        const cx = c.x + b.bx * scale;
        const cy = c.y + b.by * scale;
        const blend = Math.min(1, (t - migrateT) / 280);
        b.x = cx * (1 - blend) + tx * blend;
        b.y = cy * (1 - blend) + ty * blend;
      } else {
        const commit = rnd();
        if (commit < SITES[0].A * 0.0008) b.site = 0;
        else if (commit < (SITES[0].A + SITES[3].A) * 0.0006) b.site = 3;
        b.x = c.x + b.bx;
        b.y = c.y + b.by;
      }
    });

    for (let i = stopFlash.length - 1; i >= 0; i--) {
      stopFlash[i].age++;
      if (stopFlash[i].age > 28) stopFlash.splice(i, 1);
    }

    clock.tick();
  }

  function drawSite(s, w, h) {
    const u = w / 960;
    const x = s.x * w;
    const y = s.y * h;
    const base = (46 + s.quality * 28) * u;
    const ang = Math.min(1, s.A / QUORUM) * Math.PI * 2;
    ctx.strokeStyle = "rgba(138,147,166,0.4)";
    ctx.lineWidth = 2 * u;
    ctx.beginPath();
    ctx.arc(x, y, base * 0.92, 0, Math.PI * 2);
    ctx.stroke();
    ctx.strokeStyle = s.color;
    ctx.lineWidth = 4 * u;
    ctx.beginPath();
    ctx.arc(x, y, base * 0.92, -Math.PI / 2, -Math.PI / 2 + ang);
    ctx.stroke();
    const g = ctx.createRadialGradient(x, y, 0, x, y, base);
    g.addColorStop(0, `rgba(0,0,0,0.92)`);
    g.addColorStop(0.7, `rgba(20,14,8,0.85)`);
    g.addColorStop(1, `rgba(232,197,71,${0.12 + s.quality * 0.2})`);
    ctx.fillStyle = g;
    ctx.beginPath();
    ctx.ellipse(x, y + base * 0.05, base * 0.55, base * 0.42, 0, 0, Math.PI);
    ctx.fill();
    ctx.font = `bold ${Math.round(16 * u)}px "CN Mono"`;
    ctx.fillStyle = CN.papel;
    ctx.fillText(`${s.A.toFixed(0)}`, x - 10 * u, y + base + 18 * u);
  }

  function drawWaggle(d, w, h) {
    if (d.active < 0.4) return;
    const s = SITES[d.site];
    const c = clusterCenter();
    const cx = c.x * w;
    const cy = c.y * h;
    const u = w / 960;
    const fade = migrated ? Math.max(0, 1 - (clock.frame - migrateT) / 160) : 1;
    if (fade < 0.04) return;
    const amp = (12 + d.site * 2) * u;
    const ph = clock.t * 4 + d.angle;
    const jx = (d.site - 1.5) * 14 * u;
    const jy = (d.site % 2 === 0 ? -8 : 8) * u;
    ctx.strokeStyle = s.color;
    ctx.globalAlpha = 0.5 * fade;
    ctx.lineWidth = 1.5 * u;
    ctx.beginPath();
    for (let a = 0; a <= Math.PI * 2; a += 0.08) {
      const px = cx + jx + amp * Math.sin(a + ph);
      const py = cy + jy + amp * Math.sin(a + ph) * Math.cos(a + ph);
      a < 0.01 ? ctx.moveTo(px, py) : ctx.lineTo(px, py);
    }
    ctx.stroke();
    ctx.globalAlpha = 1;
  }

  function draw() {
    const { w, h } = opts;
    ctx.fillStyle = CN.navy;
    ctx.fillRect(0, 0, w, h);

    const c = clusterCenter();
    const sx = c.x * w;
    const sy = c.y * h;

    ctx.strokeStyle = "rgba(139,110,75,0.55)";
    ctx.lineWidth = 10;
    ctx.lineCap = "round";
    ctx.beginPath();
    ctx.moveTo(w * 0.12, h * 0.22);
    ctx.quadraticCurveTo(w * 0.24, h * 0.26, w * 0.34, h * 0.32);
    ctx.stroke();

    SITES.forEach((s) => drawSite(s, w, h));

    ctx.globalCompositeOperation = "lighter";
    swarm.forEach((b) => {
      const px = (b.x ?? c.x + b.bx) * w;
      const py = (b.y ?? c.y + b.by) * h;
      const col = b.site >= 0 ? SITES[b.site].color : "rgba(255,220,120,0.75)";
      ctx.fillStyle = col;
      ctx.beginPath();
      ctx.arc(px, py, 2.5 * (w / 960), 0, Math.PI * 2);
      ctx.fill();
    });
    ctx.globalCompositeOperation = "source-over";

    scouts.forEach((sc) => {
      ctx.fillStyle = CN.ocre;
      ctx.beginPath();
      ctx.arc(sc.x * w, sc.y * h, 3 * (w / 960), 0, Math.PI * 2);
      ctx.fill();
    });

    dances.forEach((d) => drawWaggle(d, w, h));

    stopFlash.forEach((p) => {
      const life = 1 - p.age / 28;
      ctx.strokeStyle = `rgba(255,107,74,${0.5 * life})`;
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.arc(sx, sy, 18 + p.age * 2.5, 0, Math.PI * 2);
      ctx.stroke();
    });

    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [
        { text: "∂Aᵢ/∂t = kᵣ·dᵢ·Qᵢ − δAᵢ − Σⱼ kₛ·stopⱼ" },
      ],
      counters: [
        { text: `agentes ${N_SWARM + N_SCOUT} · quórum ${QUORUM}` },
        { text: `A₀=${SITES[0].A.toFixed(1)} migrated=${migrated ? 1 : 0}` },
      ],
      cite: "Seeley & Visscher (2003, 2012); Passino et al. (2003)",
    });
  }

  function stepOnce() {
    stepDynamics();
    draw();
  }

  swarm.forEach((b) => {
    b.x = SW.x + b.bx;
    b.y = SW.y + b.by;
  });

  CNCapture.boot({
    verify: () => N_SWARM > 500 && SITES.length === 4,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();