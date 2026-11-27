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
      async pullFrame() {
        sim.stepOnce(opts.dt || 1 / 60);
        const canvas = document.getElementById("cn-canvas");
        this.frame++;
        return canvas.toDataURL("image/png");
      },
    };

    (async () => {
      if (sim.preloadAssets) await sim.preloadAssets();
      global.__cnCapture.ready = true;
    })();
  }

  global.CNCapture = { boot };
})(window);