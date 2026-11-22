/* LIF vs Hodgkin-Huxley · EP05 · CC0 */
(function () {
  const DT = 0.2;
  const TMAX = 120;

  const HH = {
    Cm: 1, gNa: 120, gK: 36, gL: 0.3, ENa: 50, EK: -77, EL: -54.387,
  };

  function am(v) {
    const x = v + 40;
    return Math.abs(x) < 1e-6 ? 1 : 0.1 * x / (1 - Math.exp(-x / 10));
  }
  const bm = (v) => 4 * Math.exp(-(v + 65) / 18);
  const ah = (v) => 0.07 * Math.exp(-(v + 65) / 20);
  const bh = (v) => 1 / (1 + Math.exp(-(v + 35) / 10));
  function an(v) {
    const x = v + 55;
    return Math.abs(x) < 1e-6 ? 0.1 : 0.01 * x / (1 - Math.exp(-x / 10));
  }
  const bn = (v) => 0.125 * Math.exp(-(v + 65) / 80);

  function simLif(I, tau, theta, E_L, R) {
    const n = Math.floor(TMAX / DT);
    const V = new Float64Array(n);
    const sp = [];
    let v = E_L;
    for (let t = 0; t < n; t++) {
      V[t] = v;
      v += (DT / tau) * (-(v - E_L) + R * I[t]);
      if (v >= theta) {
        sp.push(t);
        v = E_L;
      }
    }
    return { V, sp };
  }

  function simHh(I) {
    const n = Math.floor(TMAX / DT);
    const V = new Float64Array(n);
    const iNa = new Float64Array(n);
    const iK = new Float64Array(n);
    const iL = new Float64Array(n);
    const sp = [];
    let v = -65;
    let m = am(v) / (am(v) + bm(v));
    let h = ah(v) / (ah(v) + bh(v));
    let n_ = an(v) / (an(v) + bn(v));
    for (let t = 0; t < n; t++) {
      V[t] = v;
      iNa[t] = HH.gNa * m ** 3 * h * (v - HH.ENa);
      iK[t] = HH.gK * n_ ** 4 * (v - HH.EK);
      iL[t] = HH.gL * (v - HH.EL);
      const dv = (I[t] - iNa[t] - iK[t] - iL[t]) / HH.Cm;
      const v0 = v;
      v += DT * dv;
      m += DT * (am(v) * (1 - m) - bm(v) * m);
      h += DT * (ah(v) * (1 - h) - bh(v) * h);
      n_ += DT * (an(v) * (1 - n_) - bn(v) * n_);
      if (v0 < 0 && v >= 0) sp.push(t);
    }
    return { V, iNa, iK, iL, sp };
  }

  function corriente(Iamp, tOff) {
    const n = Math.floor(TMAX / DT);
    const I = new Float64Array(n);
    const i0 = Math.floor(20 / DT);
    const i1 = Math.floor(tOff / DT);
    for (let i = i0; i < i1; i++) I[i] = Iamp;
    return I;
  }

  function dibujar(cv, V, sp, color, label) {
    const ctx = cv.getContext("2d");
    const w = cv.width = cv.clientWidth * devicePixelRatio;
    const h = cv.height = (cv.clientHeight || 200) * devicePixelRatio;
    ctx.setTransform(1, 0, 0, 1, 0, 0);
    ctx.clearRect(0, 0, w, h);
    const pad = 16 * devicePixelRatio;
    ctx.strokeStyle = color;
    ctx.lineWidth = 2 * devicePixelRatio;
    ctx.beginPath();
    for (let i = 0; i < V.length; i++) {
      const x = pad + (w - 2 * pad) * (i / V.length);
      const y = pad + (h - 2 * pad) * (1 - (V[i] + 90) / 110);
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.stroke();
    ctx.fillStyle = "#c6f59a";
    for (const i of sp) {
      const x = pad + (w - 2 * pad) * (i / V.length);
      ctx.fillRect(x - 1, pad, 2, h - 2 * pad);
    }
    ctx.fillStyle = "#9aa3b8";
    ctx.font = `${14 * devicePixelRatio}px monospace`;
    ctx.fillText(label, pad, pad - 4);
  }

  function dibujarIon(cv, iNa, iK, iL) {
    const ctx = cv.getContext("2d");
    const w = cv.width = cv.clientWidth * devicePixelRatio;
    const h = cv.height = (cv.clientHeight || 120) * devicePixelRatio;
    ctx.clearRect(0, 0, w, h);
    const pad = 16 * devicePixelRatio;
    const series = [
      { data: iNa, c: "#ff7a59", n: "Na" },
      { data: iK, c: "#3ee0d0", n: "K" },
      { data: iL, c: "#9aa3b8", n: "fuga" },
    ];
    for (const s of series) {
      const mx = Math.max(...s.data.map(Math.abs)) + 1e-6;
      ctx.strokeStyle = s.c;
      ctx.lineWidth = 1.5 * devicePixelRatio;
      ctx.beginPath();
      for (let i = 0; i < s.data.length; i++) {
        const x = pad + (w - 2 * pad) * (i / s.data.length);
        const y = h / 2 - (s.data[i] / mx) * (h / 2 - pad);
        if (i === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }
  }

  const els = {
    corr: document.getElementById("corr"),
    dur: document.getElementById("dur"),
    tau: document.getElementById("tau"),
    umbral: document.getElementById("umbral"),
    btnIon: document.getElementById("btn-ion"),
    cvLif: document.getElementById("cv-lif"),
    cvHh: document.getElementById("cv-hh"),
    cvIon: document.getElementById("cv-ion"),
    estado: document.getElementById("estado"),
  };

  // Misma calibración pedagógica que render.py (aquí DT=0.2): 20 sin pulso, ~28 con 1–2.
  const I_JUSTO_DEBAJO = 20;
  const I_JUSTO_ENCIMA = 28;

  function actualizar(Iextra) {
    const Iamp = Iextra ?? +els.corr.value;
    ["corr-v", "dur-v", "tau-v", "umbral-v"].forEach((id) => {
      const k = id.replace("-v", "");
      document.getElementById(id).textContent = document.getElementById(k).value;
    });
    const I = corriente(Iamp, +els.dur.value);
    const lif = simLif(I, +els.tau.value, +els.umbral.value, -70, 1);
    const Ihh = I.map((x) => x * 0.5);
    const hh = simHh(Ihh);
    dibujar(els.cvLif, lif.V, lif.sp, "#3ee0d0", "LIF");
    dibujar(els.cvHh, hh.V, hh.sp, "#f06bff", "Hodgkin–Huxley");
    const mostrar = els.btnIon.getAttribute("aria-pressed") === "true";
    els.cvIon.style.display = mostrar ? "" : "none";
    if (mostrar) dibujarIon(els.cvIon, hh.iNa, hh.iK, hh.iL);
    els.estado.textContent =
      `Disparos LIF: ${lif.sp.length} · HH: ${hh.sp.length}. Corriente ${Iamp.toFixed(2)}.`;
  }

  ["corr", "dur", "tau", "umbral"].forEach((id) =>
    document.getElementById(id).addEventListener("input", () => actualizar())
  );
  els.btnIon.addEventListener("click", () => {
    const on = els.btnIon.getAttribute("aria-pressed") === "true";
    els.btnIon.setAttribute("aria-pressed", on ? "false" : "true");
    actualizar();
  });
  document.getElementById("btn-debajo").addEventListener("click", () => {
    els.corr.value = String(I_JUSTO_DEBAJO);
    actualizar(I_JUSTO_DEBAJO);
  });
  document.getElementById("btn-encima").addEventListener("click", () => {
    els.corr.value = String(I_JUSTO_ENCIMA);
    actualizar(I_JUSTO_ENCIMA);
  });
  document.getElementById("btn-reinicio").addEventListener("click", () => {
    els.corr.value = 12;
    els.dur.value = 70;
    actualizar();
  });
  window.addEventListener("resize", () => actualizar());
  actualizar();
})();