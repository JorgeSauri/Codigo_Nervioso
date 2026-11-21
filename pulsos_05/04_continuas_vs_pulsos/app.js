(function () {
  const N = 5;
  const seed = 4404;
  let s = seed;

  function randn() {
    s ^= s << 13;
    s ^= s >> 17;
    s ^= s << 5;
    const u = (s >>> 0) / 4294967296;
    return (u * 2 - 1) * 0.35;
  }

  const Wann = Array.from({ length: N }, () => Array.from({ length: N }, () => randn()));
  const Wsnn = Array.from({ length: N }, () => Array.from({ length: N }, () => randn() * 0.9));
  let x = Array(N).fill(0).map(() => randn());
  let v = Array(N).fill(-0.2);
  const raster = Array.from({ length: N }, () => []);
  let conteo = 0;
  let t = 0;
  let timer = null;

  function tanhNet(W, h, b = 0) {
    return W.map((row, i) => {
      const s = row.reduce((a, w, j) => a + w * h[j], b);
      return Math.tanh(s);
    });
  }

  function pasoSnn(hin) {
    const out = [];
    for (let i = 0; i < N; i++) {
      let I = hin[i];
      for (let j = 0; j < N; j++) I += Wsnn[j][i] * (hin[j] > 0.5 ? 1 : 0);
      v[i] += (-v[i] + I) / 15;
      if (v[i] >= -0.2) {
        out.push(1);
        v[i] = 0;
        raster[i].push(t);
        conteo++;
      } else out.push(0);
    }
    t++;
    return out;
  }

  function dibujarRed(cv, activ, W, pulses) {
    const ctx = cv.getContext("2d");
    const rect = cv.parentElement.getBoundingClientRect();
    const w = (cv.width = rect.width * devicePixelRatio);
    const h = (cv.height = rect.height * devicePixelRatio);
    ctx.clearRect(0, 0, w, h);
    const pos = [];
    for (let i = 0; i < N; i++) {
      const px = w * (0.15 + 0.7 * (i / (N - 1)));
      const py = h * 0.45;
      pos.push([px, py]);
    }
    for (let j = 0; j < N; j++) {
      for (let i = 0; i < N; i++) {
        if (i === j) continue;
        const ww = Math.abs(W[i][j]);
        if (ww < 0.05) continue;
        ctx.strokeStyle = W[i][j] > 0 ? "#f06bff" : "#ffc14d";
        ctx.lineWidth = Math.max(1, ww * 8 * devicePixelRatio);
        ctx.beginPath();
        ctx.moveTo(pos[j][0], pos[j][1]);
        ctx.lineTo(pos[i][0], pos[i][1]);
        ctx.stroke();
        if (pulses && activ[j]) {
          const pulse = 0.2 + 0.8 * Math.abs(Math.sin(performance.now() / 200 + i));
          const mx = pos[j][0] + (pos[i][0] - pos[j][0]) * pulse;
          const my = pos[j][1] + (pos[i][1] - pos[j][1]) * pulse;
          ctx.fillStyle = "#c6f59a";
          ctx.beginPath();
          ctx.arc(mx, my, 5 * devicePixelRatio, 0, Math.PI * 2);
          ctx.fill();
        }
      }
    }
    for (let i = 0; i < N; i++) {
      const [px, py] = pos[i];
      const r = (14 + (activ[i] ? 8 : 0)) * devicePixelRatio;
      ctx.fillStyle = activ[i] > 0.3 ? "#3ee0d0" : "#5a6278";
      ctx.beginPath();
      ctx.arc(px, py, r, 0, Math.PI * 2);
      ctx.fill();
      ctx.strokeStyle = "#f4f1ea";
      ctx.stroke();
    }
  }

  function dibujarRaster(cv) {
    const ctx = cv.getContext("2d");
    const w = (cv.width = cv.clientWidth * devicePixelRatio);
    const h = (cv.height = (cv.clientHeight || 100) * devicePixelRatio);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = "#3ee0d0";
    const tmax = Math.max(t, 1);
    for (let ni = 0; ni < N; ni++) {
      for (const tt of raster[ni]) {
        const xx = 8 + (w - 16) * (tt / tmax);
        const yy = 8 + (h - 16) * (ni / (N - 1));
        ctx.fillRect(xx, yy - 2, 3, 4);
      }
    }
  }

  const cvAnn = document.getElementById("cv-ann");
  const cvSnn = document.getElementById("cv-snn");
  const cvRaster = document.getElementById("cv-raster");

  function unPaso() {
    const ruido = +document.getElementById("ruido").value;
    x = x.map((xi, i) => 0.85 * xi + 0.15 * randn() * ruido);
    const h = tanhNet(Wann, x);
    const snn = pasoSnn(h.map((v) => (v + 1) / 2));
    dibujarRed(cvAnn, h.map((v) => (v + 1) / 2), Wann, false);
    dibujarRed(cvSnn, snn, Wsnn, true);
    dibujarRaster(cvRaster);
    document.getElementById("vals-ann").textContent = h.map((v, i) => `h${i}: ${v.toFixed(3)}`).join("  ");
    document.getElementById("conteo").textContent = String(conteo);
  }

  document.getElementById("btn-paso").addEventListener("click", unPaso);
  document.getElementById("btn-play").addEventListener("click", () => {
    if (timer) {
      clearInterval(timer);
      timer = null;
      return;
    }
    timer = setInterval(unPaso, 120);
  });

  unPaso();
})();