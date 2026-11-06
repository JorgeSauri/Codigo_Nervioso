/* Juguete de siguiente palabra. CC0. No es un modelo de lenguaje. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.VaritaModelo = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  /* Siete palanquitas. El orden es el de los sliders. */
  var NOMBRES = [
    "calor de taza",
    "arena",
    "mañana",
    "pie",
    "líquido",
    "mesa",
    "suela"
  ];

  var AYUDAS = [
    "qué tanto el juguete premia lo que se agarra caliente",
    "qué tanto empuja hacia la playa",
    "qué tanto huele a desayuno temprano",
    "qué tanto piensa en el pie",
    "qué tanto quiere un líquido",
    "qué tanto se queda en la mesa",
    "qué tanto busca una suela"
  ];

  /*
   * Vectores curados a mano, en el mismo orden que NOMBRES.
   * No salen de un embedding entrenado.
   */
  var PALABRAS = [
    { id: "taza", nombre: "taza", v: [1.20, -0.90, 0.72, -0.80, 0.42, 1.00, -0.95] },
    { id: "cafe", nombre: "café", v: [0.98, -0.55, 0.95, -0.35, 1.00, 0.58, -0.48] },
    { id: "plato", nombre: "plato", v: [0.40, -0.48, 0.55, -0.30, -0.10, 1.10, -0.42] },
    { id: "jarra", nombre: "jarra", v: [0.72, -0.38, 0.42, -0.42, 0.88, 0.62, -0.50] },
    { id: "cuchara", nombre: "cuchara", v: [0.22, -0.42, 0.48, -0.18, 0.05, 0.92, -0.36] },
    { id: "desayuno", nombre: "desayuno", v: [0.78, -0.72, 1.15, -0.28, 0.30, 0.80, -0.52] },
    { id: "vaso", nombre: "vaso", v: [0.35, -0.20, 0.40, -0.25, 0.70, 0.55, -0.30] },
    { id: "leche", nombre: "leche", v: [0.30, -0.35, 0.70, -0.20, 0.85, 0.40, -0.25] },
    { id: "pan", nombre: "pan", v: [0.45, -0.30, 0.80, -0.15, -0.20, 0.70, -0.20] },
    { id: "azucar", nombre: "azúcar", v: [0.15, -0.10, 0.40, -0.10, 0.20, 0.45, -0.10] },
    { id: "cuchillo", nombre: "cuchillo", v: [0.05, -0.20, 0.25, -0.05, -0.15, 0.55, -0.10] },
    { id: "servilleta", nombre: "servilleta", v: [0.10, 0.05, 0.30, -0.05, -0.10, 0.60, -0.05] },
    { id: "mesa", nombre: "mesa", v: [0.20, -0.25, 0.35, -0.20, 0.00, 1.05, -0.15] },
    { id: "silla", nombre: "silla", v: [0.05, -0.15, 0.20, -0.10, -0.05, 0.70, -0.05] },
    { id: "olla", nombre: "olla", v: [0.55, -0.30, 0.25, -0.20, 0.35, 0.40, -0.25] },
    { id: "estufa", nombre: "estufa", v: [0.60, -0.40, 0.20, -0.25, 0.05, 0.15, -0.20] },
    { id: "huevo", nombre: "huevo", v: [0.25, -0.25, 0.75, -0.10, -0.05, 0.45, -0.15] },
    { id: "tortilla", nombre: "tortilla", v: [0.35, -0.20, 0.65, -0.10, -0.10, 0.50, -0.10] },
    { id: "mantequilla", nombre: "mantequilla", v: [0.20, -0.15, 0.55, -0.08, 0.05, 0.48, -0.08] },
    { id: "mermelada", nombre: "mermelada", v: [0.12, -0.05, 0.40, -0.05, 0.10, 0.42, -0.05] },
    { id: "galleta", nombre: "galleta", v: [0.10, 0.00, 0.35, -0.05, -0.10, 0.40, -0.05] },
    { id: "miel", nombre: "miel", v: [0.18, -0.08, 0.30, -0.05, 0.25, 0.28, -0.05] },
    { id: "te", nombre: "té", v: [0.55, -0.20, 0.50, -0.15, 0.80, 0.35, -0.20] },
    { id: "jugo", nombre: "jugo", v: [0.15, 0.10, 0.45, -0.10, 0.75, 0.30, -0.10] },
    { id: "agua", nombre: "agua", v: [0.05, 0.15, 0.20, 0.00, 0.90, 0.15, -0.05] },
    { id: "sal", nombre: "sal", v: [0.05, 0.05, 0.15, -0.05, 0.05, 0.25, -0.05] },
    { id: "pimienta", nombre: "pimienta", v: [0.08, -0.05, 0.10, -0.05, 0.00, 0.22, -0.05] },
    { id: "tenedor", nombre: "tenedor", v: [0.08, -0.20, 0.30, -0.08, -0.05, 0.62, -0.10] },
    { id: "crema", nombre: "crema", v: [0.22, -0.10, 0.35, -0.08, 0.30, 0.38, -0.08] },
    { id: "refrigerador", nombre: "refrigerador", v: [0.15, -0.30, 0.20, -0.15, 0.20, 0.10, -0.10] },

    { id: "sandalia", nombre: "sandalia", v: [-0.45, 1.15, 0.15, 1.05, -0.70, -0.55, 1.15] },
    { id: "playa", nombre: "playa", v: [-0.20, 1.20, 0.25, 0.35, 0.05, -0.40, 0.25] },
    { id: "chancla", nombre: "chancla", v: [-0.40, 1.00, 0.10, 0.95, -0.60, -0.48, 1.10] },
    { id: "arena", nombre: "arena", v: [-0.15, 1.15, 0.20, 0.25, -0.20, -0.30, 0.20] },
    { id: "zapato", nombre: "zapato", v: [-0.10, 0.45, 0.05, 0.90, -0.55, -0.15, 0.95] },
    { id: "toalla", nombre: "toalla", v: [0.05, 0.70, 0.10, 0.15, 0.10, -0.10, 0.05] },
    { id: "sombrilla", nombre: "sombrilla", v: [-0.10, 0.85, 0.20, 0.05, 0.00, -0.20, 0.00] },
    { id: "ola", nombre: "ola", v: [-0.20, 0.90, 0.10, 0.00, 0.40, -0.35, -0.05] },
    { id: "mar", nombre: "mar", v: [-0.15, 0.95, 0.15, 0.00, 0.45, -0.30, 0.00] },
    { id: "sol", nombre: "sol", v: [0.30, 0.70, 0.40, 0.05, 0.00, -0.10, 0.00] },
    { id: "concha", nombre: "concha", v: [-0.10, 0.75, 0.05, 0.10, 0.05, -0.15, 0.05] },
    { id: "palmera", nombre: "palmera", v: [-0.05, 0.80, 0.15, 0.00, 0.00, -0.20, 0.00] },
    { id: "traje", nombre: "traje", v: [0.00, 0.40, 0.05, 0.15, -0.10, -0.05, 0.10] },
    { id: "sombrero", nombre: "sombrero", v: [0.05, 0.55, 0.10, 0.00, -0.05, -0.05, 0.00] },
    { id: "gorra", nombre: "gorra", v: [0.00, 0.40, 0.10, 0.00, -0.05, 0.00, 0.00] },
    { id: "calcetin", nombre: "calcetín", v: [0.00, 0.15, 0.05, 0.70, -0.10, 0.05, 0.35] },
    { id: "bota", nombre: "bota", v: [0.00, 0.10, 0.00, 0.75, -0.20, 0.00, 0.80] },

    { id: "ventana", nombre: "ventana", v: [0.05, 0.10, 0.15, -0.05, 0.00, 0.10, -0.05] },
    { id: "calle", nombre: "calle", v: [-0.05, 0.20, 0.10, 0.15, 0.00, -0.10, 0.15] },
    { id: "coche", nombre: "coche", v: [0.00, 0.05, 0.05, 0.00, 0.00, -0.05, 0.10] },
    { id: "arbol", nombre: "árbol", v: [0.00, 0.25, 0.15, 0.00, 0.05, -0.10, 0.00] },
    { id: "nube", nombre: "nube", v: [0.00, 0.20, 0.10, 0.00, 0.10, -0.05, 0.00] },
    { id: "libro", nombre: "libro", v: [0.05, -0.10, 0.10, -0.05, 0.00, 0.25, -0.05] },
    { id: "lapiz", nombre: "lápiz", v: [0.00, -0.05, 0.05, -0.05, 0.00, 0.20, 0.00] },
    { id: "mano", nombre: "mano", v: [0.15, 0.05, 0.10, 0.05, 0.00, 0.10, 0.00] },
    { id: "boca", nombre: "boca", v: [0.10, 0.00, 0.15, 0.00, 0.15, 0.10, 0.00] },
    { id: "hambre", nombre: "hambre", v: [0.20, -0.05, 0.35, 0.00, 0.00, 0.15, 0.00] },
    { id: "sed", nombre: "sed", v: [0.10, 0.15, 0.20, 0.05, 0.40, 0.05, 0.00] },
    { id: "tarde", nombre: "tarde", v: [0.05, 0.15, -0.10, 0.00, 0.05, 0.05, 0.00] },
    { id: "manana", nombre: "mañana", v: [0.15, 0.00, 0.50, 0.00, 0.10, 0.10, 0.00] },
    { id: "camisa", nombre: "camisa", v: [0.00, 0.15, 0.05, 0.00, 0.00, 0.00, 0.05] },
    { id: "helado", nombre: "helado", v: [0.05, 0.35, 0.10, 0.00, 0.20, 0.10, 0.00] },
    { id: "puerta", nombre: "puerta", v: [0.00, 0.00, 0.05, 0.00, 0.00, 0.05, 0.05] },
    { id: "llave", nombre: "llave", v: [0.00, -0.05, 0.05, 0.00, 0.00, 0.08, 0.00] },
    { id: "bolsa", nombre: "bolsa", v: [0.00, 0.20, 0.10, 0.05, 0.00, 0.05, 0.05] },
    { id: "reloj", nombre: "reloj", v: [0.05, 0.00, 0.20, 0.00, 0.00, 0.10, 0.00] }
  ];

  /* Sesgo inicial: el vecindario de la playa gana. Sandalia queda arriba. */
  var INICIO = [-0.20, 1.35, 0.08, 0.95, -0.70, -0.45, 1.20];

  var TEMPERATURA = 1.35;
  var PASO = 0.45;
  var META = "taza";

  function clon(w) {
    return w.slice();
  }

  function dot(a, b) {
    var s = 0;
    for (var i = 0; i < a.length; i++) s += a[i] * b[i];
    return s;
  }

  function logits(w) {
    var out = new Array(PALABRAS.length);
    for (var i = 0; i < PALABRAS.length; i++) out[i] = dot(w, PALABRAS[i].v) / TEMPERATURA;
    return out;
  }

  function softmax(xs) {
    var m = xs[0];
    for (var i = 1; i < xs.length; i++) if (xs[i] > m) m = xs[i];
    var ex = new Array(xs.length);
    var s = 0;
    for (var j = 0; j < xs.length; j++) {
      ex[j] = Math.exp(xs[j] - m);
      s += ex[j];
    }
    for (var k = 0; k < ex.length; k++) ex[k] /= s;
    return ex;
  }

  function distribucion(w) {
    return softmax(logits(w));
  }

  function indiceMeta() {
    for (var i = 0; i < PALABRAS.length; i++) if (PALABRAS[i].id === META) return i;
    return 0;
  }

  /* Gradiente de la entropía cruzada respecto a las palanquitas. */
  function gradiente(w) {
    var p = distribucion(w);
    var meta = indiceMeta();
    var g = [0, 0, 0, 0, 0, 0, 0];
    for (var i = 0; i < PALABRAS.length; i++) {
      var coef = (p[i] - (i === meta ? 1 : 0)) / TEMPERATURA;
      var v = PALABRAS[i].v;
      for (var k = 0; k < 7; k++) g[k] += coef * v[k];
    }
    return g;
  }

  function paso(w, lr) {
    var g = gradiente(w);
    var tasa = lr == null ? PASO : lr;
    var siguiente = clon(w);
    for (var k = 0; k < 7; k++) {
      siguiente[k] = Math.max(-1.6, Math.min(1.6, siguiente[k] - tasa * g[k]));
    }
    return siguiente;
  }

  function orden(w) {
    var p = distribucion(w);
    var filas = [];
    for (var i = 0; i < PALABRAS.length; i++) {
      filas.push({
        id: PALABRAS[i].id,
        nombre: PALABRAS[i].nombre,
        prob: p[i],
        puntaje: dot(w, PALABRAS[i].v)
      });
    }
    filas.sort(function (a, b) { return b.prob - a.prob; });
    return filas;
  }

  function perdida(w) {
    var p = distribucion(w);
    var q = Math.max(p[indiceMeta()], 1e-12);
    return -Math.log(q);
  }

  return {
    NOMBRES: NOMBRES,
    AYUDAS: AYUDAS,
    PALABRAS: PALABRAS,
    INICIO: INICIO,
    TEMPERATURA: TEMPERATURA,
    PASO: PASO,
    META: META,
    clon: clon,
    distribucion: distribucion,
    gradiente: gradiente,
    paso: paso,
    orden: orden,
    perdida: perdida,
    ENTRADAS_ILUSTRATIVAS: 200000
  };
});
