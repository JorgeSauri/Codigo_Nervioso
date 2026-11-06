/* Demo palanquitas. CC0. Ilustración, no un LLM. */
(function () {
  "use strict";
  var M = window.VaritaModelo;
  if (!M) {
    document.getElementById("estado").textContent = "No cargó el juguete (modelo.js).";
    return;
  }

  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var estado = {
    w: M.clon(M.INICIO),
    gen: 0,
    montando: false,
    metaVisible: false,
    pedacitos: true,
    ultimoPaso: 0
  };

  var hueco = document.getElementById("hueco");
  var palabraEl = document.getElementById("palabra");
  var barras = document.getElementById("barras");
  var perdida = document.getElementById("perdida");
  var estadoEl = document.getElementById("estado");
  var fichas = document.getElementById("fichas");
  var sliders = document.getElementById("sliders");
  var diccionario = document.getElementById("diccionario");
  var puente = document.getElementById("puente");
  var meta = document.getElementById("meta");
  var montajeCaja = document.getElementById("montaje");
  var contador = document.getElementById("contador");
  var mano = document.getElementById("mano");
  var btnMontaje = document.getElementById("btn-montaje");
  var entradas = [];

  document.getElementById("n-pal").textContent = String(M.PALABRAS.length);

  var PLAYA = { sandalia: 1, chancla: 1, playa: 1, arena: 1, zapato: 1, toalla: 1, sombrilla: 1, ola: 1, mar: 1, concha: 1, palmera: 1 };
  var DESAYUNO = { taza: 1, cafe: 1, plato: 1, jarra: 1, cuchara: 1, desayuno: 1, vaso: 1, leche: 1, pan: 1, te: 1 };

  function lado(id) {
    if (DESAYUNO[id]) return "lado-desayuno";
    if (PLAYA[id]) return "lado-playa";
    return "";
  }

  M.NOMBRES.forEach(function (nombre, i) {
    var bloque = document.createElement("label");
    bloque.className = "palanca";
    bloque.innerHTML =
      '<div class="cabecera-palanca"><span>' + nombre + '</span><span class="dato" data-valor>' + estado.w[i].toFixed(2) + '</span></div>' +
      '<div class="ayuda-palanca">' + M.AYUDAS[i] + '</div>';
    var input = document.createElement("input");
    input.type = "range";
    input.min = "-1.6";
    input.max = "1.6";
    input.step = "0.01";
    input.value = String(estado.w[i]);
    input.setAttribute("aria-label", nombre);
    input.addEventListener("input", function () {
      estado.gen += 1;
      pararMontaje();
      leer();
      pintar("Moviste una palanquita. El puntaje se recalcula al momento.");
    });
    bloque.appendChild(input);
    sliders.appendChild(bloque);
    entradas.push(input);
  });

  M.PALABRAS.forEach(function (p) {
    var chip = document.createElement("span");
    chip.className = "mini";
    chip.textContent = p.nombre;
    chip.dataset.id = p.id;
    diccionario.appendChild(chip);
  });

  function leer() {
    entradas.forEach(function (input, i) { estado.w[i] = Number(input.value); });
  }

  function escribirSliders() {
    entradas.forEach(function (input, i) {
      input.value = String(estado.w[i]);
      input.parentNode.querySelector("[data-valor]").textContent = estado.w[i].toFixed(2);
    });
  }

  function pintarFichas() {
    var partes = estado.pedacitos
      ? ["Me", "ser", "ví", "ca", "fé", "en", "u", "na", "___"]
      : ["Me", "serví", "café", "en", "una", "___"];
    fichas.innerHTML = "";
    partes.forEach(function (texto, i) {
      var f = document.createElement("span");
      f.className = "ficha";
      f.style.animationDelay = (i * 0.04) + "s";
      f.textContent = texto;
      fichas.appendChild(f);
    });
  }

  function pintar(mensaje) {
    var orden = M.orden(estado.w);
    var ganadora = orden[0];
    hueco.textContent = ganadora.nombre;
    hueco.className = "hueco " + lado(ganadora.id);
    palabraEl.textContent = ganadora.nombre;
    palabraEl.className = "palabra-grande " + lado(ganadora.id);
    barras.innerHTML = "";
    orden.slice(0, 5).forEach(function (fila) {
      var li = document.createElement("li");
      var nombre = document.createElement("span");
      nombre.textContent = fila.nombre;
      nombre.className = lado(fila.id);
      var pista = document.createElement("div");
      pista.className = "pista";
      var barra = document.createElement("span");
      barra.style.width = Math.max(1.5, fila.prob * 100) + "%";
      pista.appendChild(barra);
      var pct = document.createElement("span");
      pct.className = "dato";
      pct.textContent = (fila.prob * 100).toFixed(1) + "%";
      li.appendChild(nombre);
      li.appendChild(pista);
      li.appendChild(pct);
      barras.appendChild(li);
    });
    var sorpresa = M.perdida(estado.w);
    perdida.textContent = "Sorpresa de juguete, −log p(taza): " + sorpresa.toFixed(2) + ". Más grande, más lejos está taza de ganar.";
    escribirSliders();
    var chips = diccionario.querySelectorAll(".mini");
    chips.forEach(function (chip) {
      chip.classList.toggle("gana", chip.dataset.id === ganadora.id);
    });
    puente.classList.toggle("oculto", !estado.metaVisible);
    meta.classList.toggle("oculto", !estado.metaVisible);
    if (mensaje) estadoEl.textContent = mensaje;
  }

  function pararMontaje() {
    estado.montando = false;
    btnMontaje.textContent = "Montaje";
    btnMontaje.setAttribute("aria-pressed", "false");
  }

  function espera(ms) {
    return new Promise(function (resolver) { setTimeout(resolver, ms); });
  }

  function animarHacia(destino, ms, gen) {
    var inicio = M.clon(estado.w);
    var t0 = performance.now();
    return new Promise(function (resolver) {
      function frame(ahora) {
        if (gen !== estado.gen) { resolver(false); return; }
        var t = reducido ? 1 : Math.min(1, (ahora - t0) / ms);
        var suave = 1 - Math.pow(1 - t, 3);
        for (var k = 0; k < 7; k++) estado.w[k] = inicio[k] + (destino[k] - inicio[k]) * suave;
        pintar();
        if (t < 1) requestAnimationFrame(frame);
        else resolver(true);
      }
      requestAnimationFrame(frame);
    });
  }

  async function moverMano(selector) {
    if (reducido) return;
    var el = document.querySelector(selector);
    if (!el) return;
    var r = el.getBoundingClientRect();
    mano.style.left = (r.left + Math.min(36, r.width * 0.2)) + "px";
    mano.style.top = Math.max(8, r.top - 28) + "px";
    mano.classList.remove("oculto");
    await espera(620);
  }

  async function primerIntento() {
    var gen = ++estado.gen;
    pararMontaje();
    estado.metaVisible = false;
    pintar("Tirando palanquitas al azar…");
    if (!reducido) {
      for (var n = 0; n < 7; n++) {
        if (gen !== estado.gen) return;
        for (var k = 0; k < 7; k++) estado.w[k] = (Math.random() * 2 - 1) * 1.1;
        pintar();
        await espera(90);
      }
    }
    var ok = await animarHacia(M.INICIO, 800, gen);
    if (!ok) return;
    pintar("Primer intento, sesgado al vecindario de la playa. Sale sandalia. El diccionario de doscientas mil es número ilustrativo: aquí hay " + M.PALABRAS.length + " palabras.");
  }

  async function entrenador() {
    var gen = ++estado.gen;
    pararMontaje();
    estado.metaVisible = true;
    pintar("El entrenador señala la palabra que queríamos: taza.");
    await moverMano("#btn-entrenador");
    if (gen !== estado.gen) return;
    await moverMano("#meta-palabra");
    if (gen !== estado.gen) return;
    mano.classList.add("oculto");
    var destino = M.paso(estado.w, 0.35);
    var ok = await animarHacia(destino, 900, gen);
    if (!ok) return;
    var top = M.orden(estado.w)[0];
    pintar("Un paso de gradiente de juguete. Las palanquitas se movieron un poco hacia taza. Arriba sigue «" + top.nombre + "»: un empujón no alcanza.");
  }

  function montaje() {
    if (estado.montando) {
      pararMontaje();
      pintar("Montaje en pausa. Las palanquitas se quedan donde iban.");
      return;
    }
    var gen = ++estado.gen;
    estado.montando = true;
    estado.metaVisible = true;
    btnMontaje.textContent = "Pausar montaje";
    btnMontaje.setAttribute("aria-pressed", "true");
    montajeCaja.classList.remove("oculto");
    if (reducido) {
      var guard = 0;
      while (guard < 24) {
        var ordenYa = M.orden(estado.w);
        if (ordenYa[0].id === "taza" && ordenYa[0].prob >= 0.45) break;
        estado.w = M.paso(estado.w, M.PASO);
        guard += 1;
      }
      contador.textContent = (12000).toLocaleString("es-MX");
      pararMontaje();
      pintar("Sin animación: las palanquitas avanzaron de golpe. El contador en " + (12000).toLocaleString("es-MX") + " sigue siendo montaje, no un corpus.");
      return;
    }
    var t0 = performance.now();
    var duracion = reducido ? 1 : 7600;
    var mostrado = 0;
    estado.ultimoPaso = t0;
    function frame(ahora) {
      if (!estado.montando || gen !== estado.gen) return;
      var t = Math.min(1, (ahora - t0) / duracion);
      var suave = 1 - Math.pow(1 - t, 3);
      mostrado = Math.round(12000 * suave);
      contador.textContent = mostrado.toLocaleString("es-MX");
      if (ahora - estado.ultimoPaso > (reducido ? 0 : 460)) {
        estado.ultimoPaso = ahora;
        var orden = M.orden(estado.w);
        if (orden[0].id !== "taza" || orden[0].prob < 0.45) estado.w = M.paso(estado.w, M.PASO);
      }
      var ya = M.orden(estado.w)[0].id === "taza";
      pintar(ya
        ? "El hueco ya cayó en taza. El contador sigue porque es montaje, no un corpus de " + mostrado.toLocaleString("es-MX") + " frases."
        : "Montaje acelerado. El contador es teatro. Los pasos sí ajustan el softmax de juguete.");
      if (t < 1) requestAnimationFrame(frame);
      else pararMontaje();
    }
    requestAnimationFrame(frame);
  }

  document.getElementById("btn-intento").addEventListener("click", primerIntento);
  document.getElementById("btn-entrenador").addEventListener("click", entrenador);
  btnMontaje.addEventListener("click", montaje);
  document.getElementById("btn-reinicio").addEventListener("click", function () {
    estado.gen += 1;
    pararMontaje();
    mano.classList.add("oculto");
    estado.metaVisible = false;
    estado.w = M.clon(M.INICIO);
    contador.textContent = "0";
    montajeCaja.classList.add("oculto");
    pintar("De vuelta al sesgo de playa. Sandalia otra vez, sin haber entrenado nada de verdad.");
  });
  document.getElementById("btn-pedacitos").addEventListener("click", function () {
    estado.pedacitos = true;
    this.setAttribute("aria-pressed", "true");
    document.getElementById("btn-palabras").setAttribute("aria-pressed", "false");
    pintarFichas();
  });
  document.getElementById("btn-palabras").addEventListener("click", function () {
    estado.pedacitos = false;
    this.setAttribute("aria-pressed", "true");
    document.getElementById("btn-pedacitos").setAttribute("aria-pressed", "false");
    pintarFichas();
  });

  pintarFichas();
  montajeCaja.classList.add("oculto");
  primerIntento();
})();
