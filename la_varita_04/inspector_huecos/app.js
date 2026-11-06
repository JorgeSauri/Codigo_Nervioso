/* Inspector de un solo ejemplo. Reglas manuales. CC0. */
(function () {
  "use strict";

  var EJEMPLO = "Plan para el puesto de tamales de doña Lupe. Abre de 7 a 11 en la esquina. Mañana ofrece tamal de rajas, tamal de mole y atole de guayaba, a 20 pesos. Lleva 80 tamales porque el sábado siempre se acaba antes de las 10. La colonia huele a pan recién hecho y eso atrae clientes. El señor del coche gris pasa a las 8:15 y compra seis. Pon una lona verde porque combina con el puesto de jugos de enfrente.";

  var REGLAS = [
    {
      frase: "Lleva 80 tamales porque el sábado siempre se acaba antes de las 10.",
      clase: "b",
      titulo: "Cantidad y sábado inventados",
      detalle: "En tu mensaje no hay un número de tamales ni la palabra sábado. El texto supone un ritmo de venta y lo escribe como si fuera un dato."
    },
    {
      frase: "Pon una lona verde porque combina con el puesto de jugos de enfrente.",
      clase: "b",
      titulo: "Lona y vecino que nadie mencionó",
      detalle: "No pediste lona, ni color, ni hablaste de un puesto de jugos. La libreta de la esquina, en esta recreación, anota que ese puesto no está."
    },
    {
      frase: "La colonia huele a pan recién hecho",
      clase: "c",
      titulo: "El olor solo se siente ahí",
      detalle: "La colonia, el olor, no viaja en el chat. Quien no está en la banqueta no puede saberlo. La libreta de la recreación anota aceite de taquería, no pan."
    },
    {
      frase: "eso atrae clientes",
      clase: "b",
      titulo: "Del olor a una causa",
      detalle: "Aunque el olor fuera real, «atrae clientes» ya es una explicación. El texto la afirma sin una cuenta."
    },
    {
      frase: "El señor del coche gris pasa a las 8:15 y compra seis.",
      clase: "c",
      titulo: "Quién pasa en coche",
      detalle: "La hora, el coche y los seis tamales son una escena. Solo quien está en la esquina puede verla. En la libreta de la recreación, antes de las 9 no pasó un coche gris."
    },
    {
      frase: "doña Lupe",
      clase: "a",
      titulo: "El nombre lo diste tú",
      detalle: "«Doña Lupe» está en tu mensaje. El plan solo lo repite."
    },
    {
      frase: "Abre de 7 a 11",
      clase: "a",
      titulo: "El horario lo diste tú",
      detalle: "El horario sale de tu texto, no de una suposición."
    },
    {
      frase: "en la esquina",
      clase: "a",
      titulo: "El lugar, en corto",
      detalle: "Dijiste «en la esquina». El plan no inventa aquí el cruce: se queda con lo que escribiste."
    },
    {
      frase: "tamal de rajas",
      clase: "a",
      titulo: "Un sabor que sí diste",
      detalle: "Rajas está en tu mensaje."
    },
    {
      frase: "tamal de mole",
      clase: "a",
      titulo: "Otro sabor que sí diste",
      detalle: "Mole está en tu mensaje."
    },
    {
      frase: "atole de guayaba",
      clase: "a",
      titulo: "La bebida que sí diste",
      detalle: "Atole de guayaba está en tu mensaje."
    },
    {
      frase: "20 pesos",
      clase: "a",
      titulo: "El precio lo diste tú",
      detalle: "El precio sale de tu mensaje. El plan no lo calculó."
    }
  ];

  var plan = document.getElementById("plan");
  var marcado = document.getElementById("marcado");
  var aviso = document.getElementById("aviso");
  var reglaCaja = document.getElementById("regla");
  var activas = { a: true, b: true, c: true };
  var gen = 0;

  function escapar(s) {
    return s.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  function buscar(texto) {
    var ocupado = new Array(texto.length);
    var hits = [];
    var ordenadas = REGLAS.slice().sort(function (a, b) { return b.frase.length - a.frase.length; });
    var bajo = texto.toLowerCase();
    ordenadas.forEach(function (regla) {
      var aguja = regla.frase.toLowerCase();
      var desde = 0;
      while (desde < bajo.length) {
        var i = bajo.indexOf(aguja, desde);
        if (i < 0) break;
        var libre = true;
        for (var k = i; k < i + aguja.length; k++) if (ocupado[k]) libre = false;
        if (libre) {
          for (var j = i; j < i + aguja.length; j++) ocupado[j] = true;
          hits.push({ i: i, j: i + aguja.length, regla: regla });
        }
        desde = i + aguja.length;
      }
    });
    hits.sort(function (a, b) { return a.i - b.i; });
    return hits;
  }

  function pintarRegla(regla) {
    reglaCaja.innerHTML =
      '<p class="kicker">Regla ' + regla.clase.toUpperCase() + '</p>' +
      '<h3>' + escapar(regla.titulo) + '</h3>' +
      '<p>' + escapar(regla.detalle) + '</p>' +
      '<p class="nota">Frase que la dispara: «' + escapar(regla.frase) + '». Está escrita en el código de esta demo, no la encontró un modelo.</p>';
  }

  function htmlDe(texto, hits) {
    var out = "";
    var cursor = 0;
    hits.forEach(function (hit, n) {
      out += escapar(texto.slice(cursor, hit.i));
      var apagada = activas[hit.regla.clase] ? "" : " apagada";
      out += '<button type="button" class="trozo marca-' + hit.regla.clase + apagada + '" data-n="' + n + '">' +
        escapar(texto.slice(hit.i, hit.j)) + "</button>";
      cursor = hit.j;
    });
    out += escapar(texto.slice(cursor));
    return out;
  }

  function inspeccionar() {
    var mi = ++gen;
    var texto = plan.value;
    var hits = buscar(texto);
    var esEjemplo = texto === EJEMPLO;
    aviso.textContent = esEjemplo
      ? "Estás viendo el ejemplo de doña Lupe. Cada color es una regla de este archivo."
      : "El texto ya no es el ejemplo. Solo se pinta la frase que coincide letra por letra con una regla. Lo demás se queda en blanco a propósito.";
    if (!hits.length) {
      marcado.textContent = texto || "No hay texto. Restaura el ejemplo o pega el plan de doña Lupe.";
      return;
    }
    marcado.innerHTML = htmlDe(texto, hits);
    var botones = marcado.querySelectorAll("button.trozo");
    function mostrar(n) {
      botones.forEach(function (b) { b.classList.remove("activo"); });
      botones[n].classList.add("activo");
      pintarRegla(hits[n].regla);
    }
    botones.forEach(function (b) {
      b.addEventListener("click", function () { mostrar(Number(b.getAttribute("data-n"))); });
    });
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
      mostrar(0);
      return;
    }
    botones.forEach(function (b) { b.style.opacity = "0"; });
    var paso = 0;
    function revelar() {
      if (mi !== gen) return;
      if (paso > 0) botones[paso - 1].style.opacity = "";
      if (paso < botones.length) {
        botones[paso].style.opacity = "1";
        paso += 1;
        setTimeout(revelar, 70);
      } else {
        botones.forEach(function (b) { b.style.opacity = ""; });
        mostrar(0);
      }
    }
    revelar();
  }

  document.getElementById("btn-inspeccionar").addEventListener("click", inspeccionar);
  document.getElementById("btn-restaurar").addEventListener("click", function () {
    plan.value = EJEMPLO;
    inspeccionar();
  });
  document.getElementById("filtros").addEventListener("click", function (ev) {
    var b = ev.target.closest("button");
    if (!b) return;
    var clase = b.getAttribute("data-clase");
    activas[clase] = !activas[clase];
    b.setAttribute("aria-pressed", activas[clase] ? "true" : "false");
    inspeccionar();
  });

  plan.value = EJEMPLO;
  inspeccionar();
})();
