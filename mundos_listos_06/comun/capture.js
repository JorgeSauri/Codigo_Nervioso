/* Modo captura determinista (?capture=1). CC0 */
(function (global) {
  "use strict";
  const { parseQuery } = global.CNCore;

  function boot(simFactory) {
    const opts = parseQuery();
    const sim = typeof simFactory === "function" ? simFactory(opts) : simFactory;
    if (!opts.capture) {
      sim.runRealtime();
      return;
    }
    global.__cnCapture = {
      opts,
      frame: 0,
      ready: true,
      async pullFrame() {
        sim.stepOnce(opts.dt || 1 / 60);
        const canvas = document.getElementById("cn-canvas");
        this.frame++;
        return canvas.toDataURL("image/png");
      },
    };
  }

  global.CNCapture = { boot };
})(window);