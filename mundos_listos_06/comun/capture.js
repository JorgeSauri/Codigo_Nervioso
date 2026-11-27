/* Modo captura determinista (?capture=1). CC0 */
(function (global) {
  "use strict";
  const { parseQuery } = global.CNCore;

  function boot(simFactory) {
    const opts = parseQuery();
    const sim = typeof simFactory === "function" ? simFactory(opts) : simFactory;
    const startRealtime = () => sim.runRealtime();

    if (!opts.capture) {
      if (sim.preloadAssets) sim.preloadAssets().then(startRealtime);
      else startRealtime();
      return;
    }

    global.__cnCapture = {
      opts,
      frame: 0,
      ready: false,
      verify() {
        if (sim.verify) return sim.verify();
        const c = document.getElementById("cn-canvas");
        const ctx = c.getContext("2d");
        const w = c.width, h = c.height;
        const d = ctx.getImageData((w / 2) | 0, (h / 2) | 0, 32, 32).data;
        let s = 0;
        for (let i = 0; i < d.length; i += 4) s += d[i] + d[i + 1] + d[i + 2];
        return s / (32 * 32 * 3) > 18;
      },
      async pullFrame() {
        sim.stepOnce(opts.dt || 1 / 60);
        const canvas = document.getElementById("cn-canvas");
        this.frame++;
        return canvas.toDataURL("image/png");
      },
    };

    (async () => {
      if (sim.preloadAssets) await sim.preloadAssets();
      if (sim.warmup) await sim.warmup();
      global.__cnCapture.ready = true;
    })();
  }

  global.CNCapture = { boot };
})(window);