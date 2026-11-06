/* Navegación de la línea. El texto vive en el HTML. CC0. */
(function () {
  "use strict";
  var riel = document.getElementById("riel");
  var paradas = Array.prototype.slice.call(document.querySelectorAll(".parada"));
  var puntos = document.getElementById("puntos");
  var reducido = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  var botones = paradas.map(function (parada, i) {
    var b = document.createElement("button");
    b.type = "button";
    b.textContent = parada.getAttribute("data-etiqueta");
    b.setAttribute("aria-label", "Ir a " + parada.getAttribute("data-etiqueta"));
    b.addEventListener("click", function () { ir(i); });
    puntos.appendChild(b);
    return b;
  });

  function horizontal() {
    return riel.scrollWidth > riel.clientWidth + 24;
  }

  function actual() {
    var caja = riel.getBoundingClientRect();
    var medio = window.innerHeight / 2;
    var mejor = 0;
    var menor = Infinity;
    var deLado = horizontal();
    paradas.forEach(function (parada, i) {
      var r = parada.getBoundingClientRect();
      var d = deLado
        ? Math.abs(r.left - caja.left)
        : Math.abs((r.top + r.bottom) / 2 - medio);
      if (d < menor) { menor = d; mejor = i; }
    });
    return mejor;
  }

  function marcar() {
    var i = actual();
    botones.forEach(function (b, k) {
      b.setAttribute("aria-pressed", k === i ? "true" : "false");
    });
  }

  function ir(i) {
    i = Math.max(0, Math.min(paradas.length - 1, i));
    paradas[i].scrollIntoView({
      behavior: reducido ? "auto" : "smooth",
      inline: "start",
      block: "nearest"
    });
  }

  document.getElementById("siguiente").addEventListener("click", function () { ir(actual() + 1); });
  document.getElementById("anterior").addEventListener("click", function () { ir(actual() - 1); });
  riel.addEventListener("scroll", marcar, { passive: true });
  document.addEventListener("keydown", function (ev) {
    var tag = (ev.target && ev.target.tagName) || "";
    if (tag === "INPUT" || tag === "TEXTAREA") return;
    if (ev.key === "ArrowRight") { ev.preventDefault(); ir(actual() + 1); }
    if (ev.key === "ArrowLeft") { ev.preventDefault(); ir(actual() - 1); }
  });
  marcar();
})();
