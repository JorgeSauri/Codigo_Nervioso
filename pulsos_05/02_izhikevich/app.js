(function () {
  const DT = 0.25;
  const TMAX = 1000;

  function sim(par, Iamp, tOff) {
    const n = Math.floor(TMAX / DT);
    const V = new Float64Array(n);
    const sp = [];
    let v = -65;
    let u = par.b * v;
    for (let t = 0; t < n; t++) {
      const I = t * DT < tOff ? Iamp : 0;
      V[t] = v;
      v += DT * (0.04 * v * v + 5 * v + 140 - u + I);
      u += DT * (par.a * (par.b * v - u));
      if (v >= 30) {
        sp.push(t);
        v = par.c;
        u += par.d;
      }
    }
    return { V, sp };
  }

  function pintar(cv, res) {
    const ctx = cv.getContext("2d");
    const w = (cv.width = cv.clientWidth * devicePixelRatio);
    const h = (cv.height = 100 * devicePixelRatio);
    ctx.clearRect(0, 0, w, h);
    const pad = 6 * devicePixelRatio;
    ctx.strokeStyle = "#f4f1ea";
    ctx.lineWidth = 1.5 * devicePixelRatio;
    ctx.beginPath();
    for (let i = 0; i < res.V.length; i++) {
      const x = pad + (w - 2 * pad) * (i / res.V.length);
      const y = h - pad - (h - 2 * pad) * ((res.V[i] + 80) / 110);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.strokeStyle = "#3ee0d0";
    for (const i of res.sp) {
      const x = pad + (w - 2 * pad) * (i / res.V.length);
      ctx.beginPath();
      ctx.moveTo(x, pad);
      ctx.lineTo(x, h - pad);
      ctx.stroke();
    }
  }

  const rejilla = document.getElementById("rejilla");
  const cards = {};
  for (const key of Object.keys(window.IZHI_TIPOS)) {
    const div = document.createElement("div");
    div.className = "tipo";
    div.innerHTML = `<h3>${key}</h3><canvas></canvas>`;
    rejilla.appendChild(div);
    cards[key] = div.querySelector("canvas");
  }

  function correr() {
    const Iamp = +document.getElementById("iamp").value;
    const tOff = +document.getElementById("toff").value;
    document.getElementById("iamp-v").textContent = Iamp;
    document.getElementById("toff-v").textContent = tOff;
    for (const [key, par] of Object.entries(window.IZHI_TIPOS)) {
      pintar(cards[key], sim(par, Iamp, tOff));
    }
  }

  document.getElementById("btn-go").addEventListener("click", correr);
  document.getElementById("iamp").addEventListener("input", correr);
  document.getElementById("toff").addEventListener("input", correr);
  correr();
})();