# Visualización 4: Dyna-Q en el laberinto (S1). Agente real + rutas imaginadas, n = 0 / 5 / 50. CC0.
# Usa exactamente la lógica y las semillas de ../dyna_laberinto/dyna_maze.py; las cifras de la barra final
# salen de dyna_maze_resultados.json (promedio de 1000 corridas).
import sys, os, json, numpy as np
from multiprocessing import Pool
AQUI = os.path.dirname(os.path.abspath(__file__)); SIM = os.path.join(AQUI, "../dyna_laberinto")
sys.path.insert(0, SIM)
import dyna_maze as D
SAL = os.path.join(AQUI, "..", "salida", "visualizaciones"); os.makedirs(SAL, exist_ok=True)
from estilo import *
from PIL import Image, ImageDraw

def corre_grabando(n, seed, ep_grabar=1):
    """Copia instrumentada de dyna_maze.run: mismo orden de llamadas a los generadores."""
    rng_act = np.random.default_rng([seed, 0]); rng_plan = np.random.default_rng([seed, 1])
    Q = np.zeros((D.H, D.W, 4)); model = {}; keys = []; steps = []; reg = []
    for ep in range(D.EPISODES):
        s = D.START; k = 0
        while s != D.GOAL:
            if rng_act.random() < D.EPS: a = int(rng_act.integers(4))
            else:
                q = Q[s]; a = int(rng_act.choice(np.flatnonzero(q == q.max())))
            s2, r = D.step(s, a)
            Q[s][a] += D.ALPHA * (r + D.GAMMA * Q[s2].max() * (s2 != D.GOAL) - Q[s][a])
            if (s, a) not in model: keys.append((s, a))
            model[(s, a)] = (s2, r); plan = []
            for _ in range(n):
                ps, pa = keys[rng_plan.integers(len(keys))]; ps2, pr = model[(ps, pa)]
                Q[ps][pa] += D.ALPHA * (pr + D.GAMMA * Q[ps2].max() * (ps2 != D.GOAL) - Q[ps][pa]); plan.append((ps, ps2))
            if ep == ep_grabar: reg.append((s, s2, plan, Q.max(-1).copy()))
            s = s2; k += 1
        steps.append(k)
        if ep == ep_grabar: V0 = None
    return steps, reg

def ep2(args): return D.run(args)[:2]
if __name__ == "__main__":
    res = json.load(open(os.path.join(AQUI, "..", "resultados", "dyna_maze_resultados.json")))
    medias = {n: res[f"n={n}"]["ep2"]["media"] for n in (0, 5, 50)}
    with Pool() as p:
        R = {n: np.array(p.map(ep2, [(n, s) for s in range(1000)])) for n in (0, 5, 50)}
    # semilla de ejemplo: episodio 2 lo más cercano al promedio en los tres casos
    err = sum(np.abs(np.log(R[n][:, 1] / medias[n])) for n in (0, 5, 50))
    seed = int(np.argmin(err)); print("semilla de ejemplo", seed, {n: R[n][seed].tolist() for n in (0, 5, 50)}, medias)
    regs = {}; pasos_ep1 = None
    for n in (0, 5, 50):
        st, rg = corre_grabando(n, seed); regs[n] = rg; pasos_ep1 = st[0]
        assert st[:2] == R[n][seed].tolist()
    # ---- dibujo ----
    CEL = 64; MW, MH = D.W * CEL, D.H * CEL
    X0 = [(W - 3 * MW) // 4 * (i + 1) + MW * i for i in range(3)]; Y0 = 310
    ETIQ = {0: "n = 0", 5: "n = 5", 50: "n = 50"}; SUB = {0: "solo experiencia real", 5: "5 pasos imaginados por paso real", 50: "50 pasos imaginados por paso real"}
    def centro(i, rc): return (X0[i] + rc[1] * CEL + CEL // 2, Y0 + rc[0] * CEL + CEL // 2)
    vid = Video(os.path.join(SAL, "v4_dyna_laberinto_n0_5_50.mp4")); fotogramas = {}
    def base(titulo_sub):
        im, d = lienzo(); rejilla_fondo(d)
        texto(d, (80, 70), "Dyna-Q: aprender del mundo y, además, imaginar", "titulo", 58)
        texto(d, (80, 150), titulo_sub, "texto", 30, GRIS)
        pie(d, "en nuestra simulación · laberinto de Sutton & Barto (2018), ej. 8.1 · α=0.1 ε=0.1 γ=0.95")
        return im, d
    def laberinto(d, i, n, V, agente=None, estela=(), plan=(), pasos=None, meta=False):
        texto(d, (X0[i], Y0 - 100), ETIQ[n], "dato_b", 40, PAPEL); texto(d, (X0[i], Y0 - 48), SUB[n], "texto", 24, GRIS)
        vmax = 1.0
        for r in range(D.H):
            for c in range(D.W):
                x, y = X0[i] + c * CEL, Y0 + r * CEL
                if (r, c) in D.WALLS: d.rectangle([x, y, x + CEL - 1, y + CEL - 1], fill=(52, 60, 80)); continue
                v = min(1.0, V[r, c] / vmax) ** 0.5 if V is not None else 0
                d.rectangle([x + 2, y + 2, x + CEL - 3, y + CEL - 3], fill=mezcla((20, 28, 50), (0, 120, 108), v))
        marco(d, [X0[i] - 3, Y0 - 3, X0[i] + MW + 2, Y0 + MH + 2], GRIS, 2)
        gx, gy = centro(i, D.GOAL); texto(d, (gx, gy), "META", "dato_b", 15, PAPEL, "mm")
        sx, sy = centro(i, D.START); texto(d, (sx, sy), "INICIO", "dato", 12, GRIS, "mm")
        for (a, b) in plan:      # transiciones imaginadas (repaso del modelo)
            p1, p2 = centro(i, a), centro(i, b)
            if a == b: d.ellipse([p1[0] - 9, p1[1] - 9, p1[0] + 9, p1[1] + 9], outline=CIAN, width=2)
            else: d.line([p1, p2], fill=CIAN, width=3); d.ellipse([p2[0] - 5, p2[1] - 5, p2[0] + 5, p2[1] + 5], fill=CIAN)
        for j, e in enumerate(estela):
            t = (j + 1) / (len(estela) + 1); p = centro(i, e); rr = 4 + 6 * t
            d.ellipse([p[0] - rr, p[1] - rr, p[0] + rr, p[1] + rr], fill=mezcla((20, 28, 50), PAPEL, t * 0.6))
        if agente is not None:
            p = centro(i, agente); d.ellipse([p[0] - 15, p[1] - 15, p[0] + 15, p[1] + 15], fill=PAPEL)
        if pasos is not None:
            texto(d, (X0[i], Y0 + MH + 30), f"pasos reales: {pasos}", "dato_b", 34, CIAN if meta else PAPEL)
            if meta: texto(d, (X0[i], Y0 + MH + 80), "llegó a la meta", "texto_b", 28, CIAN)
    # Intro
    im, d = base(f"Episodio 1: aún no saben dónde está la meta; los tres deambulan igual ({pasos_ep1} pasos)")
    for i, n in enumerate((0, 5, 50)): laberinto(d, i, n, np.zeros((D.H, D.W)), agente=D.START)
    texto(d, (W // 2, 860), "punto blanco = el agente en el mundo real      líneas cian = experiencias que el modelo «revive» en su imaginación", "texto", 28, GRIS, "ma")
    vid.cuadro(im, 4 * FPS); fotogramas["intro"] = im
    # Episodio 2 animado
    largos = {n: len(regs[n]) for n in (0, 5, 50)}; K = max(largos.values())
    V0 = {n: regs[n][0][3] for n in (0, 5, 50)}
    for k in range(K + 1):
        fr = max(1, int(round(9 * 0.965 ** k)))      # al principio lento, luego acelera
        im, d = base("Episodio 2 · una corrida de ejemplo (misma semilla para los tres)")
        for i, n in enumerate((0, 5, 50)):
            L = largos[n]
            if k < L:
                s, s2, plan, V = regs[n][k]
                est = [regs[n][j][0] for j in range(max(0, k - 12), k)]
                laberinto(d, i, n, V, agente=s, estela=est, plan=plan, pasos=k)
            else:
                s, s2, plan, V = regs[n][L - 1]
                laberinto(d, i, n, V, agente=D.GOAL, pasos=L, meta=True)
        vid.cuadro(im, fr)
        if k == 25: fotogramas["ep2"] = im
    vid.cuadro(im, 2 * FPS)
    # Cierre: promedios de 1000 corridas
    opt = res["optimo"]; maxv = 700
    for f in range(int(5.5 * FPS)):
        t = min(1, f / (1.5 * FPS)); t = 1 - (1 - t) ** 3
        im, d = lienzo(); rejilla_fondo(d)
        texto(d, (80, 70), "¿Cuántos pasos para llegar en el episodio 2?", "titulo", 58)
        texto(d, (80, 150), "promedio de 1000 corridas, en nuestra simulación", "texto", 30, GRIS)
        bx, bw = 400, 1050
        for j, n in enumerate((0, 5, 50)):
            y = 330 + j * 170; v = medias[n]
            texto(d, (bx - 30, y + 40), ETIQ[n], "dato_b", 44, PAPEL, "rm")
            d.rectangle([bx, y, bx + int(bw * v / maxv * t), y + 80], fill=CIAN if n else (70, 80, 104))
            texto(d, (bx + int(bw * v / maxv * t) + 24, y + 40), f"≈{int(round(v, -1))}  ({v:.1f})", "dato_b", 40, PAPEL, "lm")
        xo = bx + int(bw * opt / maxv)
        for yy in range(300, 850, 18): d.line([(xo, yy), (xo, yy + 9)], fill=GRIS, width=3)
        texto(d, (xo + 12, 870), f"ruta óptima: {opt} pasos", "dato", 28, GRIS)
        pie(d, "en nuestra simulación · Dyna-Q, laberinto de Sutton & Barto (2018), ej. 8.1")
        vid.cuadro(im)
    fotogramas["cierre"] = im
    vid.cierra()
    for k, im in fotogramas.items(): im.save(os.path.join(AQUI, "..", f"v4_dyna_laberinto_{k}.png"))
    json.dump({"semilla_ejemplo": seed, "pasos_ep1": pasos_ep1, "pasos_ep2_ejemplo": {n: largos[n] for n in largos}, "promedios_ep2_1000": medias},
              open(os.path.join(SAL, "v4_dyna_laberinto_datos.json"), "w"), indent=1)
    print("listo", vid.n, "cuadros")
