# Animaciones con DATOS REALES de nuestras simulaciones (EP03). CC0.
import sys, csv, json, heapq
import numpy as np
from comun import *
sys.path.insert(0, os.path.join(AQUI, '../dyna_laberinto'))
import dyna_maze as DM
DAT = os.path.join(AQUI, '..', 'resultados')
ETQ = 'EN NUESTRA SIMULACIÓN'
def leer_cma(t):
    return list(csv.DictReader(open(os.path.join(DAT, f'cma_tau{t}.csv'))))
# ---------------- laberinto ----------------
def dib_lab(d, x0, y0, c, V=None, vmax=1.0, marca=None, agente=None, brillo=None):
    for r in range(DM.H):
        for k in range(DM.W):
            x, y = x0 + k * c, y0 + r * c; caja = [x + 3, y + 3, x + c - 3, y + c - 3]
            if (r, k) in DM.WALLS: d.rectangle(caja, fill=(88, 96, 118)); d.line([caja[0], caja[3], caja[2], caja[1]], fill=(70, 78, 100), width=3); continue
            v = 0 if V is None else V[r, k]
            col = mezcla((20, 28, 50), CIAN, min(1, (v / vmax) ** 0.6)) if v > 1e-6 else (20, 28, 50)
            if brillo is not None and brillo[r, k] > 0: col = mezcla(col, PAPEL, 0.6 * brillo[r, k])
            d.rectangle(caja, fill=col)
    gx, gy = x0 + DM.GOAL[1] * c, y0 + DM.GOAL[0] * c
    d.rectangle([gx + 3, gy + 3, gx + c - 3, gy + c - 3], outline=CORAL, width=4); texto(d, (gx + c / 2, gy + c / 2), 'M', 'dato_b', int(c * .4), CORAL, 'mm')
    sx, sy = x0 + DM.START[1] * c, y0 + DM.START[0] * c
    texto(d, (sx + c / 2, sy + c / 2), 'S', 'dato_b', int(c * .4), PAPEL, 'mm')
    if agente is not None:
        ax, ay = x0 + agente[1] * c + c / 2, y0 + agente[0] * c + c / 2
        d.ellipse([ax - c * .25, ay - c * .25, ax + c * .25, ay + c * .25], fill=CORAL)
def a08():
    """n=0 vs n=50, misma semilla: valor (max Q) durante el episodio 2, paso real a paso real; con n=50 se ven las 50 actualizaciones imaginadas."""
    def corre(n, seed=3, pasos2=35):
        rng_act = np.random.default_rng([seed, 0]); rng_plan = np.random.default_rng([seed, 1])
        Q = np.zeros((DM.H, DM.W, 4)); model = {}; keys = []; snaps = []
        for ep in range(2):
            s = DM.START; k = 0
            while s != DM.GOAL:
                if rng_act.random() < DM.EPS: a = int(rng_act.integers(4))
                else: q = Q[s]; a = int(rng_act.choice(np.flatnonzero(q == q.max())))
                s2, r = DM.step(s, a)
                Q[s][a] += DM.ALPHA * (r + DM.GAMMA * Q[s2].max() * (s2 != DM.GOAL) - Q[s][a])
                if (s, a) not in model: keys.append((s, a))
                model[(s, a)] = (s2, r); sub = []
                for _ in range(n):
                    ps, pa = keys[rng_plan.integers(len(keys))]; ps2, pr = model[(ps, pa)]
                    Q[ps][pa] += DM.ALPHA * (pr + DM.GAMMA * Q[ps2].max() * (ps2 != DM.GOAL) - Q[ps][pa])
                    if ep == 1: sub.append(Q.max(2).copy())
                if ep == 1: snaps.append((s2, Q.max(2).copy(), sub))
                s = s2; k += 1
                if ep == 1 and k >= pasos2: break
            if ep == 0: ep1 = k; V1 = Q.max(2).copy()
        return ep1, V1, snaps
    e0, V10, S0 = corre(0); e5, V15, S5 = corre(50)
    assert e0 == e5
    vmax = max(V15.max(), max(s[1].max() for s in S5))
    c = 82; X0, X1, Y = 120, 1040, 300; P = 0.32; T0 = 3.0; L0 = DM.run((0, 3))[1]; L5 = DM.run((50, 3))[1]
    def dib(t, im, d):
        texto(d, (120, 70), 'Valor aprendido: qué tan cerca de la meta «se siente» cada casilla', 'titulo', 44, PAPEL)
        texto(d, (120, 130), f'{ETQ} · misma semilla · el 1.er episodio tardó {e0} pasos en ambos', 'dato', 26, CIAN)
        i = int((t - T0) / P) if t >= T0 else -1; i = min(i, len(S0) - 1)
        for (x0, nom, V1, S) in ((X0, 'SIN IMAGINAR (n = 0)', V10, S0), (X1, 'IMAGINANDO 50 PASOS (n = 50)', V15, S5)):
            texto(d, (x0, 230), nom, 'dato_b', 32, PAPEL if x0 == X0 else CIAN)
            if i < 0: V = V1; ag = DM.START; lbl = 'tras el 1.er episodio'
            else:
                ag, V, sub = S[i]
                if sub:
                    fr = (t - T0 - i * P) / P; j = min(len(sub) - 1, int(fr * len(sub))); V = sub[j]
                lbl = f'episodio 2 · paso real {i + 1}'
            dib_lab(d, x0, Y, c, V, vmax, agente=ag)
            texto(d, (x0, Y + DM.H * c + 30), lbl, 'dato', 28, GRIS)
            texto(d, (x0, Y + DM.H * c + 72), f'casillas con valor: {(V > 1e-9).sum()} de 47', 'dato_b', 30, CIAN if x0 == X1 else PAPEL)
            if i == len(S0) - 1: texto(d, (x0, Y + DM.H * c + 120), (f'2.º episodio completo: {L5} pasos (llegó)' if x0 == X1 else f'2.º episodio completo: {L0} pasos (sigue buscando)'), 'dato', 26, CIAN if x0 == X1 else CORAL)
        pie(d, 'Dyna-Q · Sutton & Barto (2018), Ej. 8.1 · α = 0.1, ε = 0.1, γ = 0.95')
    render('a08_propagacion_valor', T0 + len(S0) * P + 2.5, dib)
def a21():
    """Barrido priorizado vs repaso al azar, con el modelo aprendido en el 1.er episodio (misma experiencia)."""
    rng = np.random.default_rng(11); Q = np.zeros((DM.H, DM.W, 4)); model = {}
    s = DM.START
    while s != DM.GOAL:   # 1.er episodio: Q-learning puro, solo se anota el modelo
        q = Q[s]; a = int(rng.integers(4)) if rng.random() < DM.EPS else int(rng.choice(np.flatnonzero(q == q.max())))
        s2, r = DM.step(s, a); Q[s][a] += DM.ALPHA * (r + DM.GAMMA * Q[s2].max() * (s2 != DM.GOAL) - Q[s][a]); model[(s, a)] = (s2, r); s = s2
    pred = {}
    for (ps, pa), (ps2, pr) in model.items(): pred.setdefault(ps2, set()).add((ps, pa))
    N = 60; ALF = 0.5
    def prior(Qp):
        Qp = Qp.copy(); pq = []; orden = []; vs = []
        for (ps, pa), (ps2, pr) in model.items():
            p = abs(pr + DM.GAMMA * Qp[ps2].max() * (ps2 != DM.GOAL) - Qp[ps][pa])
            if p > 1e-4: heapq.heappush(pq, (-p, ps, pa))
        while pq and len(orden) < N:
            _, ps, pa = heapq.heappop(pq); ps2, pr = model[(ps, pa)]
            Qp[ps][pa] += ALF * (pr + DM.GAMMA * Qp[ps2].max() * (ps2 != DM.GOAL) - Qp[ps][pa])
            orden.append(ps); vs.append(Qp.max(2).copy())
            for (qs, qa) in pred.get(ps, ()):
                q2, qr = model[(qs, qa)]; p = abs(qr + DM.GAMMA * Qp[q2].max() * (q2 != DM.GOAL) - Qp[qs][qa])
                if p > 1e-4: heapq.heappush(pq, (-p, qs, qa))
        return orden, vs
    def azar(Qp):
        Qp = Qp.copy(); r2 = np.random.default_rng(5); ks = list(model); orden = []; vs = []
        for _ in range(N):
            ps, pa = ks[r2.integers(len(ks))]; ps2, pr = model[(ps, pa)]
            Qp[ps][pa] += ALF * (pr + DM.GAMMA * Qp[ps2].max() * (ps2 != DM.GOAL) - Qp[ps][pa]); orden.append(ps); vs.append(Qp.max(2).copy())
        return orden, vs
    O1, V1 = prior(Q); O2, V2 = azar(Q); vmax = max(V1[-1].max(), V2[-1].max())
    c = 82; T0 = 2.0; P = 0.2
    def dib(t, im, d):
        texto(d, (120, 70), '¿Qué repasa primero?', 'titulo', 52, PAPEL)
        texto(d, (120, 140), f'{ETQ} · mismo laberinto, mismas notas del 1.er recorrido · {N} repasos', 'dato', 26, CIAN)
        i = int((t - T0) / P) if t >= T0 else -1; i = min(i, N - 1)
        for x0, nom, O, V, col in ((120, 'POR PRIORIDAD (sorpresa más grande primero)', O1, V1, CIAN), (1040, 'AL AZAR', O2, V2, GRIS)):
            texto(d, (x0, 230), nom, 'dato_b', 28, col)
            Vi = V[i] if i >= 0 else Q.max(2)
            br = np.zeros((DM.H, DM.W))
            if i >= 0:
                for k in range(max(0, i - 4), i + 1): br[O[k]] = max(br[O[k]], 1 - (i - k) / 5)
            dib_lab(d, x0, 300, c, Vi, vmax, brillo=br)
            texto(d, (x0, 300 + DM.H * c + 30), f'repaso {max(0, i + 1)} de {N}', 'dato', 28, GRIS)
            texto(d, (x0, 300 + DM.H * c + 72), f'casillas con valor: {(Vi > 1e-9).sum()}', 'dato_b', 30, col)
        pie(d, 'Barrido priorizado · Moore & Atkeson (1993); Sutton & Barto (2018), §8.4')
    render('a21_replay_priorizado', T0 + N * P + 2.5, dib)
def a12():
    F = leer_cma('1.15'); g = np.array([int(r['generacion']) for r in F]); mej = np.array([float(r['mejor']) for r in F]); med = np.array([float(r['media']) for r in F])
    ev = [(int(r['generacion']), float(r['eval_mejor_sueno_media'])) for r in F if r['eval_mejor_sueno_media']]
    x0, y0, x1, y1 = 220, 220, 1760, 900
    X = lambda gg: x0 + (gg - 1) / (len(g) - 1) * (x1 - x0); Y = lambda v: y1 - v / 2100 * (y1 - y0)
    def dib(t, im, d):
        texto(d, (120, 70), 'El controlador entrena SOLO dentro del sueño', 'titulo', 50, PAPEL)
        texto(d, (120, 140), f'{ETQ} · CMA-ES · τ = 1.15 · población de 64 · 16 sueños por candidato', 'dato', 26, CIAN)
        for v in (0, 500, 1000, 1500, 2100):
            d.line([(x0, Y(v)), (x1, Y(v))], fill=(30, 40, 64)); texto(d, (x0 - 16, Y(v)), f'{v:,}', 'dato', 22, GRIS, 'rm')
        texto(d, ((x0 + x1) / 2, y1 + 50), 'generación', 'dato', 24, GRIS, 'mm'); texto(d, (x0, y0 - 30), 'instantes que sobrevive DENTRO DEL SUEÑO (máx. 2,100)', 'dato', 22, GRIS)
        for gg in (1, 100, 200, 300): texto(d, (X(gg), y1 + 18), str(gg), 'dato', 22, GRIS, 'ma')
        k = int(len(g) * tramo(t, 0.8, 9.0))
        if k > 1:
            d.line([(X(a), Y(b)) for a, b in zip(g[:k], med[:k])], fill=CIAN, width=4)
            d.line([(X(a), Y(b)) for a, b in zip(g[:k], mej[:k])], fill=mezcla(NAVY, PAPEL, .45), width=2)
        for gg, v in ev:
            if gg <= (g[k - 1] if k else 0): d.ellipse([X(gg) - 9, Y(v) - 9, X(gg) + 9, Y(v) + 9], fill=CORAL)
        LY = Y(800); texto(d, (x1 - 520, LY), '— promedio de la población', 'dato', 24, CIAN); texto(d, (x1 - 520, LY + 34), '— mejor candidato', 'dato', 24, mezcla(NAVY, PAPEL, .6))
        texto(d, (x1 - 520, LY + 68), '●  el mejor, evaluado en 1,024 sueños', 'dato', 24, CORAL)
        if t > 9.5: texto(d, (x1, Y(330)), 'nunca jugó el juego real', 'titulo', 40, alfa(CORAL, tramo(t, 9.5, 10.2)), 'rd')
    render('a12_curva_cma', 13, dib)
def a13():
    paper = {'0.10': (2086, 140, 193, 58), '0.50': (2060, 277, 196, 50), '1.00': (1145, 690, 868, 511), '1.15': (918, 546, 1092, 556), '1.30': (732, 269, 753, 139)}
    nues = {}
    for t in paper:
        m = json.load(open(os.path.join(DAT, f'mejor_tau{t}.json'))); r = json.load(open(os.path.join(DAT, f'real_tau{t}.json')))
        F = leer_cma(t); ev = [float(x['eval_mejor_sueno_media']) for x in F if x['eval_mejor_sueno_media']]
        nues[t] = (m['sueno_media'], m['sueno_de'], r['media'], r['de'])
    azp, azn = 210, json.load(open(os.path.join(DAT, 'aleatorio_real.json')))['media']
    json.dump({'paper': paper, 'nuestra': nues, 'azar_paper': azp, 'azar_nuestro': azn}, open(os.path.join(SAL, 'frames', 'a13_datos.json'), 'w'), indent=1)
    taus = list(paper)
    def panel(d, x0, x1, tit, dat, az, col_t, a, foco):
        y0, y1 = 300, 880; Y = lambda v: y1 - v / 2100 * (y1 - y0)
        texto(d, (x0, 230), tit, 'dato_b', 30, col_t)
        for v in (0, 750, 2100):
            d.line([(x0, Y(v)), (x1, Y(v))], fill=(30, 40, 64)); texto(d, (x0 - 12, Y(v)), f'{v:,}', 'dato', 20, GRIS, 'rm')
        texto(d, (x0 - 12, Y(750) + 14), 'resuelto', 'dato', 16, GRIS, 'ra')
        gw = (x1 - x0) / len(taus)
        for i, tt in enumerate(taus):
            ms, ss, mr, sr = dat[tt]; cx = x0 + gw * (i + .5); dim = 1 if foco is None or foco == tt else .35
            for j, (m, s, col) in enumerate(((ms, ss, CIAN), (mr, sr, CORAL))):
                bx = cx - 44 + j * 46; h = m * a
                d.rectangle([bx, Y(h), bx + 40, y1], fill=mezcla(NAVY, col, .85 * dim))
                if a >= 1: d.line([(bx + 20, Y(max(0, m - s))), (bx + 20, Y(min(2100, m + s)))], fill=mezcla(NAVY, PAPEL, .5 * dim), width=2)
                if a >= 1: texto(d, (bx + 20, Y(m) - 10), f'{m:,.0f}', 'dato', 17, mezcla(NAVY, PAPEL, dim), 'md')
            texto(d, (cx, y1 + 16), f'τ = {tt}', 'dato', 22, mezcla(NAVY, PAPEL, dim), 'ma')
        yy = Y(az); xx = x0
        while xx < x1: d.line([(xx, yy), (min(x1, xx + 14), yy)], fill=PAPEL, width=2); xx += 24
        texto(d, (x1 + 10, yy), f'azar\n{az:,.0f}', 'dato', 18, PAPEL, 'lm')
    def dib(t, im, d):
        texto(d, (120, 70), 'Puntaje dentro del sueño vs. en el juego real', 'titulo', 48, PAPEL)
        texto(d, (120, 140), 'instantes sobrevividos en Doom (máx. 2,100) · barras: promedio · línea: ± desviación', 'dato', 24, GRIS)
        a = tramo(t, 0.5, 2.5); foco = '0.10' if 4 < t < 9 else None
        panel(d, 200, 900, 'PAPER · Ha & Schmidhuber (2018), Tabla 2', paper, azp, PAPEL, a, foco)
        panel(d, 1100, 1800, ETQ + ' (100 partidas reales)', nues, azn, CIAN, tramo(t, 2.0, 4.0), foco)
        d.rectangle([200, 980, 226, 1000], fill=CIAN); texto(d, (236, 990), 'dentro del sueño', 'dato', 22, PAPEL, 'lm')
        d.rectangle([480, 980, 506, 1000], fill=CORAL); texto(d, (516, 990), 'en el juego real', 'dato', 22, PAPEL, 'lm')
    render('a13_barrido_tau', 16, dib)
def a11():
    P = [('VISIÓN (VAE)', 4446915, PAPEL), ('MEMORIA (MDN-RNN)', 1680833, PAPEL), ('CONTROLADOR', 1088, CORAL)]
    def dib(t, im, d):
        texto(d, (120, 70), '¿Cuántos números ajustables tiene cada pieza?', 'titulo', 50, PAPEL)
        texto(d, (120, 140), ETQ + ' · Doom', 'dato', 26, CIAN)
        x0, x1 = 560, 1480
        for i, (n, v, c) in enumerate(P):
            y = 300 + i * 190; a = tramo(t, 0.5 + i * .8, 1.8 + i * .8)
            texto(d, (x0 - 30, y + 40), n, 'dato_b', 32, c, 'rm')
            w = (x1 - x0) * v / P[0][1] * a
            d.rectangle([x0, y, x0 + max(2, w), y + 80], fill=mezcla(NAVY, CIAN if i < 2 else CORAL, .85))
            if a > 0: texto(d, (x0 + max(2, w) + 20, y + 40), f'{int(v * a):,}', 'dato_b', 34, PAPEL, 'lm')
        if t > 4.5:
            k = tramo(t, 4.5, 5.5); cx, cy = x0 + 1, 300 + 2 * 190 + 40
            d.ellipse([cx - 60 * k, cy - 60 * k, cx + 60 * k, cy + 60 * k], outline=CORAL, width=4)
            texto(d, (x0, 920), 'el que decide: 1,088 números · 0.02 % del total', 'titulo', 44, alfa(CORAL, tramo(t, 5, 6)))
    render('a11_controlador_diminuto', 10, dib)
def a16():
    """Modelo TD(0) con representación de serie completa (Schultz, Dayan & Montague 1997). Luz en t=10, jugo en t=40."""
    T, CS, US, AL = 60, 10, 40, 0.15
    w = np.zeros(T)
    def ensayo(w, jugo=True, luz=True, aprende=True):
        x = lambda t: (luz and CS <= t) ; V = np.array([w[t - CS] if (luz and t >= CS) else 0. for t in range(T + 1)])
        r = np.zeros(T); 
        if jugo: r[US] = 1
        delta = np.array([r[t] + V[t + 1] - V[t] for t in range(T)])
        if aprende:
            for t in range(CS, T): w[t - CS] += AL * delta[t]
        return delta
    d0 = ensayo(np.zeros(T), luz=True)  # 1.er ensayo
    for _ in range(300): ensayo(w)
    d1 = ensayo(w.copy(), aprende=False); d2 = ensayo(w.copy(), jugo=False, aprende=False)
    json.dump({'primer': d0.round(3).tolist(), 'aprendido': d1.round(3).tolist(), 'sin_jugo': d2.round(3).tolist()}, open(os.path.join(SAL, 'frames', 'a16_datos.json'), 'w'))
    fases = [('1 · Jugo que nadie anunció', d0, True), ('2 · Después de aprender que la luz lo anuncia', d1, True), ('3 · La luz se enciende… y el jugo no llega', d2, False)]
    x0, x1, yb = 260, 1760, 640; X = lambda t: x0 + t / (T - 1) * (x1 - x0); Y = lambda v: yb - v * 260
    def dib(t, im, d):
        texto(d, (120, 70), 'Sorpresa = lo que pasó − lo que esperabas', 'titulo', 50, PAPEL)
        texto(d, (120, 140), ETQ + ' · modelo de diferencia temporal (TD)', 'dato', 26, CIAN)
        f = min(2, int(t / 5)); nom, dl, jugo = fases[f]; tl = t - f * 5
        texto(d, (x0, 230), nom, 'titulo', 38, PAPEL)
        d.line([(x0, yb), (x1, yb)], fill=GRIS, width=2); texto(d, (x0 - 20, Y(1)), '+', 'dato_b', 34, CIAN, 'rm'); texto(d, (x0 - 20, Y(-1)), '−', 'dato_b', 34, CORAL, 'rm')
        cx = X(CS); d.ellipse([cx - 26, 880, cx + 26, 932], fill=(255, 214, 102) if f else (60, 66, 90)); texto(d, (cx, 960), 'luz', 'dato', 24, GRIS, 'ma')
        jx = X(US); col = CIAN if jugo else (60, 66, 90)
        d.polygon([(jx, 872), (jx - 24, 914), (jx, 940), (jx + 24, 914)], fill=col); texto(d, (jx, 960), 'jugo' if jugo else 'sin jugo', 'dato', 24, GRIS, 'ma')
        k = int(T * tramo(tl, 0.3, 3.0))
        pts = [(X(i), Y(dl[i])) for i in range(k)]
        if len(pts) > 1: d.line(pts, fill=PAPEL, width=5)
        for i in range(k):
            if abs(dl[i]) > .2: d.ellipse([X(i) - 10, Y(dl[i]) - 10, X(i) + 10, Y(dl[i]) + 10], fill=CIAN if dl[i] > 0 else CORAL)
        texto(d, (x1, yb + 30), 'tiempo →', 'dato', 22, GRIS, 'ra')
        pie(d, 'Ilustración del modelo de Schultz, Dayan & Montague (1997); no son datos de neuronas')
    render('a16_td_dopamina', 15, dib)
if __name__ == '__main__':
    for n in (sys.argv[1:] or ['a08', 'a21', 'a12', 'a13', 'a11', 'a16']): globals()[n]()
