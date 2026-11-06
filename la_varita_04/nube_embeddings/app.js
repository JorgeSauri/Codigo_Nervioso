/* Nube 3D en canvas, sin three.js, para que abra en file:// sin red. CC0. */
(function () {
  "use strict";
  var N = window.VaritaNube;
  var lienzo = document.getElementById("cielo");
  var ctx = lienzo.getContext("2d");
  if (!N || !ctx) {
    document.getElementById("escena-texto").textContent = "No se pudo armar la nube.";
    return;
  }

  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var sandalia = N.buscar("sandalia");
  var taza = N.buscar("taza");
  var cafe = N.buscar("cafe");
  var dist = N.distancia(sandalia, taza);
  document.getElementById("distancia").textContent = dist.toFixed(2);

  function lista(grupo, id) {
    var ul = document.getElementById(id);
    N.PUNTOS.filter(function (p) { return p.grupo === grupo; }).forEach(function (p) {
      var li = document.createElement("li");
      li.textContent = p.nombre;
      ul.appendChild(li);
    });
  }
  lista("desayuno", "lista-desayuno");
  lista("playa", "lista-playa");

  function centro(grupo) {
    var pts = N.PUNTOS.filter(function (p) { return p.grupo === grupo; });
    var s = [0, 0, 0];
    pts.forEach(function (p) {
      s[0] += p.p[0]; s[1] += p.p[1]; s[2] += p.p[2];
    });
    return s.map(function (v) { return v / pts.length; });
  }
  function ryDe(c) { return Math.atan2(c[0], c[2]); }
  function rxDe(c) { return Math.atan2(c[1], Math.hypot(c[0], c[2])); }

  var des = centro("desayuno");
  var pla = centro("playa");
  var cam = { ry: 0.4, rx: 0.18, dist: 8.2 };
  var meta = { ry: 0.4, rx: 0.18, dist: 8.2 };
  var modo = "general";
  var escena = "taller";
  var arrastrando = false;
  var ultimo = null;
  var inercia = 0;
  var pulso = 0;
  var apuestaT = 0;
  var apuestaVa = false;
  var polvo = [];
  var semilla = 20261119;
  function aleatorio() {
    semilla = (semilla + 0x6d2b79f5) | 0;
    var t = Math.imul(semilla ^ (semilla >>> 15), 1 | semilla);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  }
  for (var i = 0; i < 70; i++) {
    var u = aleatorio() * Math.PI * 2;
    var v = Math.acos(2 * aleatorio() - 1);
    var r = 6.5 + aleatorio() * 2.2;
    polvo.push([
      r * Math.sin(v) * Math.cos(u),
      (aleatorio() - 0.5) * 5,
      r * Math.sin(v) * Math.sin(u)
    ]);
  }

  function tamano() {
    var caja = lienzo.parentNode.getBoundingClientRect();
    var dpr = Math.min(2, window.devicePixelRatio || 1);
    lienzo.width = Math.max(2, Math.floor(caja.width * dpr));
    lienzo.height = Math.max(2, Math.floor(caja.height * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    return { w: caja.width, h: caja.height };
  }
  var vista = tamano();
  window.addEventListener("resize", function () { vista = tamano(); });
  if (window.ResizeObserver) {
    new ResizeObserver(function () { vista = tamano(); }).observe(lienzo.parentNode);
  }

  function proyectar(p) {
    var x = p[0], y = p[1], z = p[2];
    var cosy = Math.cos(cam.ry), siny = Math.sin(cam.ry);
    var x1 = x * cosy - z * siny;
    var z1 = x * siny + z * cosy;
    var cosx = Math.cos(cam.rx), sinx = Math.sin(cam.rx);
    var y2 = y * cosx - z1 * sinx;
    var z2 = y * sinx + z1 * cosx;
    var profundidad = cam.dist - z2;
    var f = (Math.min(vista.w, vista.h) * 0.86) / Math.max(0.35, profundidad);
    return {
      x: vista.w / 2 + x1 * f,
      y: vista.h / 2 - y2 * f,
      f: f,
      z: z2
    };
  }

  function enFrente(q) {
    var profundidad = cam.dist - q.z;
    if (profundidad < 0.5) return false;
    if (modo === "error") return true;
    return q.z > 0.2;
  }

  function colorGrupo(g) {
    if (g === "desayuno") return "#3ee0d0";
    if (g === "playa") return "#f06bff";
    if (g === "hueco") return "#ffc14d";
    if (g === "apuesta") return "#ff7a59";
    return "rgba(154,163,184,0.85)";
  }

  function linea(a, b, estilo, ancho) {
    ctx.beginPath();
    ctx.moveTo(a.x, a.y);
    ctx.lineTo(b.x, b.y);
    ctx.strokeStyle = estilo;
    ctx.lineWidth = ancho;
    ctx.stroke();
  }

  function apuestaPos() {
    var t = apuestaT;
    var suave = t * t * (3 - 2 * t);
    return [
      sandalia.p[0] + (taza.p[0] - sandalia.p[0]) * suave,
      sandalia.p[1] + (taza.p[1] - sandalia.p[1]) * suave + Math.sin(t * Math.PI) * 0.25,
      sandalia.p[2] + (taza.p[2] - sandalia.p[2]) * suave
    ];
  }

  var ocupadas = [];
  function cabeEtiqueta(x, y, texto) {
    var ancho = ctx.measureText(texto).width + 8;
    var alto = 16;
    for (var i = 0; i < ocupadas.length; i++) {
      var o = ocupadas[i];
      if (x < o.x + o.w && x + ancho > o.x && y < o.y + o.h && y + alto > o.y) return false;
    }
    ocupadas.push({ x: x, y: y, w: ancho, h: alto });
    return true;
  }

  function dibujar() {
    var w = vista.w, h = vista.h;
    ctx.clearRect(0, 0, w, h);
    ocupadas = [];
    ctx.font = "600 13px 'CN Mono', ui-monospace, monospace";

    polvo.forEach(function (p) {
      var q = proyectar(p);
      if (!enFrente(q)) return;
      ctx.fillStyle = "rgba(244,241,234,0.25)";
      ctx.fillRect(q.x, q.y, 1.4, 1.4);
    });

    var umbral = 1.7;
    ctx.lineWidth = 1;
    for (var i = 0; i < N.PUNTOS.length; i++) {
      for (var j = i + 1; j < N.PUNTOS.length; j++) {
        var a = N.PUNTOS[i], b = N.PUNTOS[j];
        if (a.grupo !== b.grupo || a.grupo === "otro") continue;
        if (N.distancia(a, b) > umbral) continue;
        var pa = proyectar(a.p), pb = proyectar(b.p);
        if (!enFrente(pa) || !enFrente(pb)) continue;
        linea(pa, pb, a.grupo === "desayuno" ? "rgba(62,224,208,0.35)" : "rgba(240,107,255,0.35)", 1.2);
      }
    }

    var pulsoLinea = 0.55 + 0.45 * (0.5 + 0.5 * Math.sin(pulso));
    var ps = proyectar(sandalia.p);
    var pt = proyectar(taza.p);
    if (enFrente(ps) && enFrente(pt)) {
      ctx.save();
      ctx.shadowColor = "#ff7a59";
      ctx.shadowBlur = 16 * pulsoLinea;
      linea(ps, pt, "rgba(255,122,89," + (0.35 + 0.55 * pulsoLinea) + ")", 2.2);
      ctx.restore();
      ctx.fillStyle = "#ff7a59";
      var mx = (ps.x + pt.x) / 2;
      var my = (ps.y + pt.y) / 2 - 12;
      if (cabeEtiqueta(mx - 40, my, "error")) {
        ctx.fillText("error  " + dist.toFixed(2), mx - 40, my);
      }
    }

    if (escena === "mostrador") {
      var pc = proyectar(cafe.p);
      var ph = proyectar(N.HUECO.p);
      if (enFrente(pc) && enFrente(ph)) {
      ctx.setLineDash([4, 6]);
      linea(pc, ph, "rgba(255,193,77,0.9)", 1.6);
      ctx.setLineDash([]);
      var em = (pc.x + ph.x) / 2;
      var en = (pc.y + ph.y) / 2 - 10;
      ctx.fillStyle = "#ffc14d";
      if (cabeEtiqueta(em - 54, en, "café → hueco")) ctx.fillText("café → hueco", em - 54, en);
      }
    } else {
      ctx.save();
      ctx.setLineDash([2, 8]);
      ctx.globalAlpha = 0.45 + 0.25 * Math.sin(pulso * 1.5);
      if (enFrente(ps) && enFrente(pt)) linea(ps, pt, "rgba(244,241,234,0.8)", 1);
      ctx.restore();
    }

    var dibujables = N.PUNTOS.map(function (p) {
      return { p: p, q: proyectar(p.p), prioridad: p.grupo === "otro" ? 0 : 1 };
    });
    dibujables.push({ p: N.HUECO, q: proyectar(N.HUECO.p), prioridad: 2 });
    if (apuestaVa || apuestaT > 0) {
      dibujables.push({
        p: { nombre: "apuesta", grupo: "apuesta", id: "apuesta" },
        q: proyectar(apuestaPos()),
        prioridad: 3
      });
    }
    dibujables.sort(function (a, b) { return a.q.z - b.q.z; });

    dibujables.forEach(function (item) {
      var q = item.q;
      if (!enFrente(q)) return;
      var radio = Math.max(2.2, q.f * (item.p.grupo === "otro" ? 0.045 : 0.07));
      var color = colorGrupo(item.p.grupo);
      var glow = ctx.createRadialGradient(q.x, q.y, 0, q.x, q.y, radio * 6);
      glow.addColorStop(0, color);
      glow.addColorStop(1, "rgba(0,0,0,0)");
      ctx.globalAlpha = item.p.grupo === "otro" ? 0.28 : 0.55;
      ctx.fillStyle = glow;
      ctx.beginPath();
      ctx.arc(q.x, q.y, radio * 6, 0, Math.PI * 2);
      ctx.fill();
      ctx.globalAlpha = 1;
      ctx.fillStyle = color;
      ctx.beginPath();
      ctx.arc(q.x, q.y, radio, 0, Math.PI * 2);
      ctx.fill();
      var siempre = item.p.grupo !== "otro";
      if (siempre && cabeEtiqueta(q.x + radio + 4, q.y - 4, item.p.nombre)) {
        ctx.fillStyle = color;
        ctx.fillText(item.p.nombre, q.x + radio + 4, q.y + 4);
      }
    });

    ctx.globalAlpha = 0.85;
    ctx.fillStyle = "rgba(244,241,234,0.72)";
    ctx.font = "600 12px 'CN Inter', sans-serif";
    var pie = escena === "taller"
      ? "Taller · las posiciones están fijas · la línea es el error"
      : "Mostrador · Me serví café en una ___  ·  se consulta, no se entrena";
    ctx.fillText(pie, 16, 28);
    ctx.fillText("proyección simplificada", 16, 48);
    ctx.globalAlpha = 1;
  }

  function acercar(actual, destino, factor) {
    return actual + (destino - actual) * factor;
  }

  function cuadro() {
    if (modo === "general" && !arrastrando && !reducido) meta.ry += 0.0024;
    var f = reducido ? 1 : 0.08;
    cam.ry = acercar(cam.ry, meta.ry, arrastrando ? 1 : f);
    cam.rx = acercar(cam.rx, meta.rx, arrastrando ? 1 : f);
    cam.dist = acercar(cam.dist, meta.dist, arrastrando ? 1 : f);
    if (!arrastrando && Math.abs(inercia) > 0.00005 && modo === "general") {
      meta.ry += inercia;
      inercia *= 0.96;
    }
    if (!reducido) pulso += 0.04;
    if (apuestaVa && !reducido) {
      apuestaT = Math.min(1, apuestaT + 0.008);
      if (apuestaT >= 1) apuestaVa = false;
    }
    dibujar();
    requestAnimationFrame(cuadro);
  }

  function fijarModo(siguiente, boton) {
    modo = siguiente;
    ["btn-general", "btn-desayuno", "btn-playa", "btn-error"].forEach(function (id) {
      document.getElementById(id).setAttribute("aria-pressed", id === boton ? "true" : "false");
    });
    inercia = 0;
  }

  document.getElementById("btn-general").addEventListener("click", function () {
    fijarModo("general", "btn-general");
    meta.rx = 0.18;
    meta.dist = 8.2;
  });
  document.getElementById("btn-desayuno").addEventListener("click", function () {
    fijarModo("foco", "btn-desayuno");
    meta.ry = ryDe(des);
    meta.rx = rxDe(des);
    meta.dist = 5.4;
  });
  document.getElementById("btn-playa").addEventListener("click", function () {
    fijarModo("foco", "btn-playa");
    meta.ry = ryDe(pla);
    meta.rx = rxDe(pla);
    meta.dist = 5.4;
  });
  document.getElementById("btn-error").addEventListener("click", function () {
    fijarModo("error", "btn-error");
    var medio = [
      (sandalia.p[0] + taza.p[0]) / 2,
      (sandalia.p[1] + taza.p[1]) / 2,
      (sandalia.p[2] + taza.p[2]) / 2
    ];
    meta.ry = ryDe([taza.p[0] - sandalia.p[0], 0, taza.p[2] - sandalia.p[2]]) + Math.PI / 2;
    meta.rx = rxDe(medio);
    meta.dist = 9.4;
    pulso = Math.PI / 2;
  });
  document.getElementById("btn-apuesta").addEventListener("click", function () {
    apuestaVa = true;
    if (reducido) apuestaT = 1;
    else if (apuestaT >= 1) apuestaT = 0;
  });

  var textoEscena = document.getElementById("escena-texto");
  document.getElementById("btn-taller").addEventListener("click", function () {
    escena = "taller";
    this.setAttribute("aria-pressed", "true");
    document.getElementById("btn-mostrador").setAttribute("aria-pressed", "false");
    textoEscena.textContent = "Taller: las posiciones no se entrenan aquí. La línea recuerda el empujón que, en un modelo de verdad, acercaría piezas que salen juntas. En esta página nadie las mueve solas.";
  });
  document.getElementById("btn-mostrador").addEventListener("click", function () {
    escena = "mostrador";
    this.setAttribute("aria-pressed", "true");
    document.getElementById("btn-taller").setAttribute("aria-pressed", "false");
    textoEscena.textContent = "Mostrador: la nube se consulta. La frase es «Me serví café en una ___». La raya café → hueco es un dibujo de la atención, no el cálculo de un transformer.";
  });

  lienzo.addEventListener("pointerdown", function (ev) {
    arrastrando = true;
    ultimo = { x: ev.clientX, y: ev.clientY };
    lienzo.setPointerCapture(ev.pointerId);
    lienzo.style.cursor = "grabbing";
  });
  lienzo.addEventListener("pointermove", function (ev) {
    if (!arrastrando || !ultimo) return;
    var dx = ev.clientX - ultimo.x;
    var dy = ev.clientY - ultimo.y;
    meta.ry += dx * 0.008;
    cam.ry = meta.ry;
    meta.rx = Math.max(-1.1, Math.min(1.1, meta.rx + dy * 0.006));
    cam.rx = meta.rx;
    inercia = dx * 0.0004;
    ultimo = { x: ev.clientX, y: ev.clientY };
    modo = "general";
    ["btn-general", "btn-desayuno", "btn-playa", "btn-error"].forEach(function (id) {
      document.getElementById(id).setAttribute("aria-pressed", id === "btn-general" ? "true" : "false");
    });
  });
  function soltar() {
    arrastrando = false;
    ultimo = null;
    lienzo.style.cursor = "grab";
  }
  lienzo.addEventListener("pointerup", soltar);
  lienzo.addEventListener("pointercancel", soltar);
  lienzo.addEventListener("wheel", function (ev) {
    ev.preventDefault();
    meta.dist = Math.max(3.6, Math.min(14, meta.dist + ev.deltaY * 0.01));
  }, { passive: false });

  requestAnimationFrame(cuadro);
})();
