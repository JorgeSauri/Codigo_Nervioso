/* Sprites PNG con fallback vectorial. CC0 */
(function (global) {
  "use strict";

  function assetUrl(name) {
    return `../assets/png/${name}`;
  }

  const fallbacks = {
    bee_scout_top(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#E8C547";
      ctx.beginPath();
      ctx.ellipse(0, 2, s * 0.22, s * 0.28, 0, 0, Math.PI * 2);
      ctx.fill();
      ctx.fillStyle = "#0B1020";
      for (let i = -1; i <= 1; i++) ctx.fillRect(-s * 0.18, -4 + i * 10, s * 0.36, 5);
      ctx.strokeStyle = "rgba(0,229,199,0.45)";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.ellipse(-8, -8, 10, 16, -0.4, 0, Math.PI * 2);
      ctx.ellipse(8, -8, 10, 16, 0.4, 0, Math.PI * 2);
      ctx.stroke();
      ctx.restore();
    },
    fish_boid_cyan(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#00E5C7";
      ctx.beginPath();
      ctx.moveTo(s * 0.3, 0);
      ctx.quadraticCurveTo(0, -s * 0.18, -s * 0.32, 0);
      ctx.quadraticCurveTo(0, s * 0.18, s * 0.3, 0);
      ctx.fill();
      ctx.beginPath();
      ctx.moveTo(-s * 0.32, 0);
      ctx.lineTo(-s * 0.42, -s * 0.12);
      ctx.lineTo(-s * 0.42, s * 0.12);
      ctx.closePath();
      ctx.fill();
      ctx.fillStyle = "#0B1020";
      ctx.beginPath();
      ctx.arc(s * 0.12, -3, 3, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    },
    ant_top(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.strokeStyle = "#FF6B4A";
      ctx.lineWidth = 2;
      ctx.fillStyle = "#0B1020";
      [-14, 0, 12].forEach((dx, i) => {
        const w = 10 - i * 2;
        ctx.beginPath();
        ctx.ellipse(dx, 0, w, w * 0.7, 0, 0, Math.PI * 2);
        ctx.fill();
      });
      ctx.restore();
    },
    physarum_agent(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#E8C547";
      ctx.beginPath();
      ctx.moveTo(0, -s * 0.2);
      ctx.bezierCurveTo(s * 0.2, -s * 0.2, s * 0.18, s * 0.15, 0, s * 0.22);
      ctx.bezierCurveTo(-s * 0.18, s * 0.15, -s * 0.2, -s * 0.2, 0, -s * 0.2);
      ctx.fill();
      ctx.restore();
    },
    pps_particle(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#F4F1EA";
      ctx.beginPath();
      ctx.arc(0, 0, s * 0.14, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#00E5C7";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    },
    city_node(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#F4F1EA";
      ctx.beginPath();
      ctx.arc(0, 0, s * 0.2, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#00E5C7";
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.restore();
    },
    food_pellet(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#F4F1EA";
      ctx.beginPath();
      ctx.arc(0, 0, s * 0.16, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    },
    nest_box(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.fillStyle = "#F4F1EA";
      ctx.fillRect(-s * 0.22, -s * 0.15, s * 0.44, s * 0.3);
      ctx.fillStyle = "#0B1020";
      ctx.beginPath();
      ctx.arc(s * 0.15, 0, s * 0.08, 0, Math.PI * 2);
      ctx.fill();
      ctx.restore();
    },
    branch_cluster(ctx, s) {
      ctx.save();
      ctx.translate(s / 2, s / 2);
      ctx.strokeStyle = "#8A93A6";
      ctx.lineWidth = 6;
      ctx.lineCap = "round";
      ctx.beginPath();
      ctx.moveTo(-s * 0.35, s * 0.2);
      ctx.quadraticCurveTo(0, -s * 0.25, s * 0.35, -s * 0.05);
      ctx.stroke();
      ctx.restore();
    },
    bee_hang(ctx, s) {
      fallbacks.bee_scout_top(ctx, s);
    },
    default(ctx, s) {
      ctx.fillStyle = "rgba(0,229,199,0.25)";
      ctx.fillRect(0, 0, s, s);
    },
  };

  const cache = new Map();

  function loadSprite(name) {
    if (cache.has(name)) return cache.get(name);
    const img = new Image();
    const p = new Promise((resolve) => {
      img.onload = () => resolve({ img, ok: true, name });
      img.onerror = () => resolve({ img: null, ok: false, name });
      img.src = assetUrl(name);
    });
    cache.set(name, p);
    return p;
  }

  function drawSprite(ctx, name, x, y, size, angle = 0) {
    const drawFb = () => {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      (fallbacks[name] || fallbacks.default)(ctx, size);
      ctx.restore();
    };
    const hit = cache.get(name);
    if (!hit) {
      loadSprite(name).then((sp) => {
        if (!sp.ok) return;
      });
      drawFb();
      return;
    }
    hit.then((sp) => {
      ctx.save();
      ctx.translate(x, y);
      ctx.rotate(angle);
      if (sp.ok && sp.img.complete) {
        ctx.drawImage(sp.img, -size / 2, -size / 2, size, size);
      } else {
        (fallbacks[name] || fallbacks.default)(ctx, size);
      }
      ctx.restore();
    });
  }

  function drawSpriteSync(ctx, name, x, y, size, angle, sp) {
    ctx.save();
    ctx.translate(x, y);
    ctx.rotate(angle);
    if (sp?.ok && sp.img?.complete && sp.img.naturalWidth) {
      ctx.drawImage(sp.img, -size / 2, -size / 2, size, size);
    } else {
      (fallbacks[name] || fallbacks.default)(ctx, size);
    }
    ctx.restore();
  }

  async function preload(names) {
    return Promise.all(names.map(loadSprite));
  }

  global.CNSprites = { loadSprite, drawSprite, drawSpriteSync, preload, fallbacks, assetUrl };
})(window);