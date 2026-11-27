/* SIM 4B — Jones (2010) Physarum, agentes en WebGL2. CC0 */
(function () {
  const { parseQuery, SimClock, setupCanvas, drawOverlay, vignette, CN, mulberry32 } = CNCore;
  const SA = (45 * Math.PI) / 180;
  const RA = (45 * Math.PI) / 180;
  const SO = 9;
  const DECAY = 0.90;
  const DIFFUSE = 0.22;
  const DEPOSIT = 0.008;
  const AW = 512;
  const AH = 512;
  const N = AW * AH;
  const TW = 640;
  const TH = 360;

  const opts = parseQuery();
  const canvas = document.getElementById("cn-canvas");
  const ctx = setupCanvas(canvas, opts);
  const clock = new SimClock(opts.fps);
  const rnd = mulberry32(opts.seed + 42);

  const glCanvas = document.createElement("canvas");
  glCanvas.width = opts.w;
  glCanvas.height = opts.h;
  const gl = glCanvas.getContext("webgl2", { antialias: false, premultipliedAlpha: false });
  if (!gl) throw new Error("WebGL2 requerido para Jones");
  gl.enable(gl.VERTEX_PROGRAM_POINT_SIZE);

  function tex(w, h, data, filter) {
    const t = gl.createTexture();
    gl.bindTexture(gl.TEXTURE_2D, t);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, filter);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, data);
    return t;
  }
  function fbo(texture) {
    const f = gl.createFramebuffer();
    gl.bindFramebuffer(gl.FRAMEBUFFER, f);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
    return f;
  }
  function prog(vs, fs) {
    const mk = (type, src) => {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) throw new Error(gl.getShaderInfoLog(s));
      return s;
    };
    const p = gl.createProgram();
    gl.attachShader(p, mk(gl.VERTEX_SHADER, vs));
    gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs));
    gl.linkProgram(p);
    if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error(gl.getProgramInfoLog(p));
    return p;
  }

  const quadVs = `#version 300 es
  out vec2 vUv;
  void main() {
    vec2 p = vec2(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0);
    vUv = p * 0.5 + 0.5;
    gl_Position = vec4(p, 0.0, 1.0);
  }`;

  const agentFs = `#version 300 es
  precision highp float;
  uniform sampler2D uAgents;
  uniform sampler2D uTrail;
  uniform vec2 uTrailSize;
  uniform float uSA, uRA, uSO, uSpeed;
  out vec4 frag;
  void main() {
    ivec2 c = ivec2(gl_FragCoord.xy);
    vec4 a = texelFetch(uAgents, c, 0);
    float ang = a.z * 6.28318530718;
    vec2 pos = a.xy;
    float so = uSO / uTrailSize.x;
    vec2 sL = fract(pos + vec2(cos(ang - uSA), sin(ang - uSA)) * so);
    vec2 sR = fract(pos + vec2(cos(ang + uSA), sin(ang + uSA)) * so);
    vec2 sF = fract(pos + vec2(cos(ang), sin(ang)) * so);
    float vL = texture(uTrail, sL).r;
    float vR = texture(uTrail, sR).r;
    float vF = texture(uTrail, sF).r;
    if (vL > vR && vL > vF) ang -= uRA;
    else if (vR > vL && vR > vF) ang += uRA;
    pos = fract(pos + vec2(cos(ang), sin(ang)) * uSpeed);
    frag = vec4(pos, fract(ang / 6.28318530718), 1.0);
  }`;

  const decayFs = `#version 300 es
  precision highp float;
  uniform sampler2D uTrail;
  uniform vec2 uTrailSize;
  uniform float uDecay, uDiffuse;
  in vec2 vUv;
  out vec4 frag;
  void main() {
    vec2 px = 1.0 / uTrailSize;
    float c = texture(uTrail, vUv).r;
    float n = texture(uTrail, vUv + vec2(px.x, 0.0)).r
            + texture(uTrail, vUv - vec2(px.x, 0.0)).r
            + texture(uTrail, vUv + vec2(0.0, px.y)).r
            + texture(uTrail, vUv - vec2(0.0, px.y)).r;
    float v = mix(c, n * 0.25, uDiffuse) * uDecay;
    vec2 foodA = vec2(0.22, 0.48);
    vec2 foodB = vec2(0.78, 0.42);
    vec2 foodC = vec2(0.50, 0.78);
    v += 0.02 * exp(-dot(vUv - foodA, vUv - foodA) * 2200.0);
    v += 0.02 * exp(-dot(vUv - foodB, vUv - foodB) * 2200.0);
    v += 0.02 * exp(-dot(vUv - foodC, vUv - foodC) * 2200.0);
    frag = vec4(v, 0.0, 0.0, 1.0);
  }`;

  const depositVs = `#version 300 es
  uniform sampler2D uAgents;
  uniform vec2 uAgentSize;
  void main() {
    int id = gl_VertexID;
    int x = id % int(uAgentSize.x);
    int y = id / int(uAgentSize.x);
    vec2 pos = texelFetch(uAgents, ivec2(x, y), 0).xy;
    gl_Position = vec4(pos * 2.0 - 1.0, 0.0, 1.0);
    gl_PointSize = 1.0;
  }`;
  const depositFs = `#version 300 es
  precision highp float;
  uniform float uDeposit;
  out vec4 frag;
  void main() { frag = vec4(uDeposit, 0.0, 0.0, 1.0); }`;

  const showFs = `#version 300 es
  precision highp float;
  uniform sampler2D uTrail;
  in vec2 vUv;
  out vec4 frag;
  void main() {
    float v = texture(uTrail, vUv).r;
    vec3 navy = vec3(0.027, 0.043, 0.086);
    vec3 gold = vec3(1.0, 0.78, 0.22);
    vec3 hot = vec3(0.15, 0.95, 0.82);
    vec3 col = navy;
    col = mix(col, gold, smoothstep(0.04, 0.28, v));
    col += hot * smoothstep(0.22, 0.7, v);
    frag = vec4(col, 1.0);
  }`;

  const agents0 = new Uint8Array(N * 4);
  for (let i = 0; i < N; i++) {
    agents0[i * 4] = (rnd() * 255) | 0;
    agents0[i * 4 + 1] = (rnd() * 255) | 0;
    agents0[i * 4 + 2] = (rnd() * 255) | 0;
    agents0[i * 4 + 3] = 255;
  }
  let agentA = tex(AW, AH, agents0, gl.NEAREST);
  let agentB = tex(AW, AH, null, gl.NEAREST);
  let trailA = tex(TW, TH, null, gl.LINEAR);
  let trailB = tex(TW, TH, null, gl.LINEAR);
  const fAgentA = fbo(agentA);
  const fAgentB = fbo(agentB);
  const fTrailA = fbo(trailA);
  const fTrailB = fbo(trailB);

  const pAgent = prog(quadVs, agentFs);
  const pDecay = prog(quadVs, decayFs);
  const pDeposit = prog(depositVs, depositFs);
  const pShow = prog(quadVs, showFs);
  const vao = gl.createVertexArray();
  gl.bindVertexArray(vao);

  function bindTex(unit, texture) {
    gl.activeTexture(gl.TEXTURE0 + unit);
    gl.bindTexture(gl.TEXTURE_2D, texture);
  }

  function stepGpu() {
    gl.bindFramebuffer(gl.FRAMEBUFFER, fAgentB);
    gl.viewport(0, 0, AW, AH);
    gl.useProgram(pAgent);
    bindTex(0, agentA);
    bindTex(1, trailA);
    gl.uniform1i(gl.getUniformLocation(pAgent, "uAgents"), 0);
    gl.uniform1i(gl.getUniformLocation(pAgent, "uTrail"), 1);
    gl.uniform2f(gl.getUniformLocation(pAgent, "uTrailSize"), TW, TH);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uSA"), SA);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uRA"), RA);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uSO"), SO);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uSpeed"), 1.6 / TW);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    [agentA, agentB] = [agentB, agentA];
    const tmpF = fAgentA;
    /* swap FBO bindings by reassigning textures already swapped via names;
       framebuffers stay attached to original textures, so swap FBO refs too */
    void tmpF;

    gl.bindFramebuffer(gl.FRAMEBUFFER, fTrailB);
    gl.viewport(0, 0, TW, TH);
    gl.disable(gl.BLEND);
    gl.useProgram(pDecay);
    bindTex(0, trailA);
    gl.uniform1i(gl.getUniformLocation(pDecay, "uTrail"), 0);
    gl.uniform2f(gl.getUniformLocation(pDecay, "uTrailSize"), TW, TH);
    gl.uniform1f(gl.getUniformLocation(pDecay, "uDecay"), DECAY);
    gl.uniform1f(gl.getUniformLocation(pDecay, "uDiffuse"), DIFFUSE);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.useProgram(pDeposit);
    bindTex(0, agentA);
    gl.uniform1i(gl.getUniformLocation(pDeposit, "uAgents"), 0);
    gl.uniform2f(gl.getUniformLocation(pDeposit, "uAgentSize"), AW, AH);
    gl.uniform1f(gl.getUniformLocation(pDeposit, "uDeposit"), DEPOSIT);
    gl.drawArrays(gl.POINTS, 0, N);
    gl.disable(gl.BLEND);
    [trailA, trailB] = [trailB, trailA];
  }

  /* Framebuffers are bound to textures created above. After swap, the
     "B" framebuffer still points at the texture now named trailA.
     Rebuild attachment each step to stay correct. */
  function attach(fb, texture) {
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, texture, 0);
  }

  function stepGpuFixed() {
    attach(fAgentB, agentB);
    gl.bindFramebuffer(gl.FRAMEBUFFER, fAgentB);
    gl.viewport(0, 0, AW, AH);
    gl.disable(gl.BLEND);
    gl.useProgram(pAgent);
    bindTex(0, agentA);
    bindTex(1, trailA);
    gl.uniform1i(gl.getUniformLocation(pAgent, "uAgents"), 0);
    gl.uniform1i(gl.getUniformLocation(pAgent, "uTrail"), 1);
    gl.uniform2f(gl.getUniformLocation(pAgent, "uTrailSize"), TW, TH);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uSA"), SA);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uRA"), RA);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uSO"), SO);
    gl.uniform1f(gl.getUniformLocation(pAgent, "uSpeed"), 1.6 / TW);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    const nextAgent = agentB;
    agentB = agentA;
    agentA = nextAgent;

    attach(fTrailB, trailB);
    gl.bindFramebuffer(gl.FRAMEBUFFER, fTrailB);
    gl.viewport(0, 0, TW, TH);
    gl.useProgram(pDecay);
    bindTex(0, trailA);
    gl.uniform1i(gl.getUniformLocation(pDecay, "uTrail"), 0);
    gl.uniform2f(gl.getUniformLocation(pDecay, "uTrailSize"), TW, TH);
    gl.uniform1f(gl.getUniformLocation(pDecay, "uDecay"), DECAY);
    gl.uniform1f(gl.getUniformLocation(pDecay, "uDiffuse"), DIFFUSE);
    gl.drawArrays(gl.TRIANGLES, 0, 3);

    gl.enable(gl.BLEND);
    gl.blendFunc(gl.ONE, gl.ONE);
    gl.useProgram(pDeposit);
    bindTex(0, agentA);
    gl.uniform1i(gl.getUniformLocation(pDeposit, "uAgents"), 0);
    gl.uniform2f(gl.getUniformLocation(pDeposit, "uAgentSize"), AW, AH);
    gl.uniform1f(gl.getUniformLocation(pDeposit, "uDeposit"), DEPOSIT);
    gl.drawArrays(gl.POINTS, 0, N);
    gl.disable(gl.BLEND);
    const nextTrail = trailB;
    trailB = trailA;
    trailA = nextTrail;
  }

  function draw() {
    const { w, h } = opts;
    gl.bindFramebuffer(gl.FRAMEBUFFER, null);
    gl.viewport(0, 0, glCanvas.width, glCanvas.height);
    gl.useProgram(pShow);
    bindTex(0, trailA);
    gl.uniform1i(gl.getUniformLocation(pShow, "uTrail"), 0);
    gl.drawArrays(gl.TRIANGLES, 0, 3);
    ctx.drawImage(glCanvas, 0, 0, w, h);
    vignette(ctx, w, h);
    drawOverlay(ctx, {
      w, h, formato: opts.formato,
      lines: [{ text: "Jones (2010): sensores ±SA, giro RA, offset SO, depósito + difusión + decaimiento" }],
      counters: [
        { text: `SA=45° RA=45° SO=${SO} decay=${DECAY} N=${N}` },
        { text: `WebGL2 · trail ${TW}×${TH}` },
      ],
      cite: "Jones (2010) Artificial Life 16(2):127–153",
    });
  }

  function stepOnce() {
    stepGpuFixed();
    clock.tick();
    draw();
  }

  draw();
  CNCapture.boot({
    verify: () => gl && N > 100000,
    runRealtime() { const go = () => { stepOnce(); requestAnimationFrame(go); }; go(); },
    stepOnce,
  });
})();
