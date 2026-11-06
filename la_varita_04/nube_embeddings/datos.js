/* Coordenadas curadas a mano. Maqueta 3D, no un embedding entrenado. CC0. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.VaritaNube = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function punto(id, nombre, grupo, x, y, z) {
    return { id: id, nombre: nombre, grupo: grupo, p: [x, y, z] };
  }

  var PUNTOS = [
    punto("taza", "taza", "desayuno", 2.35, 0.95, 1.15),
    punto("cafe", "café", "desayuno", 1.85, 0.45, 1.55),
    punto("plato", "plato", "desayuno", 2.70, 0.20, 0.75),
    punto("jarra", "jarra", "desayuno", 1.55, 1.15, 0.85),
    punto("cuchara", "cuchara", "desayuno", 2.85, 0.85, 1.45),
    punto("desayuno", "desayuno", "desayuno", 2.05, 1.35, 1.70),

    punto("sandalia", "sandalia", "playa", -2.55, -0.35, -1.25),
    punto("playa", "playa", "playa", -2.05, -0.95, -1.75),
    punto("chancla", "chancla", "playa", -2.95, -0.15, -1.65),
    punto("arena", "arena", "playa", -1.75, -0.65, -1.05),
    punto("zapato", "zapato", "playa", -3.15, -0.85, -0.95),

    punto("pan", "pan", "otro", 0.00, 1.70, 0.00),
    punto("leche", "leche", "otro", -1.43, 1.52, 1.31),
    punto("libro", "libro", "otro", 0.23, 1.34, -2.66),
    punto("calle", "calle", "otro", 4.60, 2.40, -1.20),
    punto("agua", "agua", "otro", -4.40, 1.80, 2.20),
    punto("ventana", "ventana", "otro", 3.23, 0.81, -2.06),
    punto("reloj", "reloj", "otro", -1.05, 0.63, 3.91),
    punto("bolsa", "bolsa", "otro", -1.93, 0.45, -3.72),
    punto("nube", "nube", "otro", 0.20, 2.80, -3.80),
    punto("mano", "mano", "otro", -4.02, 0.09, 1.66),
    punto("hambre", "hambre", "otro", 1.84, -0.09, -3.93),
    punto("camisa", "camisa", "otro", 1.29, -0.27, 4.10),
    punto("llave", "llave", "otro", 2.80, -2.40, 3.20),
    punto("puerta", "puerta", "otro", 3.95, -0.63, -0.87),
    punto("helado", "helado", "otro", -2.20, -0.81, 3.13),
    punto("arbol", "árbol", "otro", -0.46, -0.98, -3.52),
    punto("coche", "coche", "otro", 2.43, -1.16, 2.04),
    punto("sal", "sal", "otro", 1.20, 2.90, 2.40),
    punto("miel", "miel", "otro", 1.38, -1.52, -1.37),
    punto("lampara", "lámpara", "otro", 0.00, -1.70, 0.00)
  ];

  var HUECO = punto("hueco", "hueco", "hueco", 3.15, 1.55, 0.35);

  function buscar(id) {
    for (var i = 0; i < PUNTOS.length; i++) if (PUNTOS[i].id === id) return PUNTOS[i];
    return null;
  }

  function distancia(a, b) {
    var dx = a.p[0] - b.p[0];
    var dy = a.p[1] - b.p[1];
    var dz = a.p[2] - b.p[2];
    return Math.sqrt(dx * dx + dy * dy + dz * dz);
  }

  return {
    PUNTOS: PUNTOS,
    HUECO: HUECO,
    buscar: buscar,
    distancia: distancia
  };
});
