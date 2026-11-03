"""S5b · Mercado de agentes de Lux y Marchesi (1999), versión simplificada.

Escrita por el canal a partir de la descripción del artículo (Nature 397,
498–500) y de la formulación de Lux y Marchesi (2000); no hay código de
referencia verificado. Tres tipos de agentes: fundamentalistas (compran si el
precio está por debajo del valor fundamental), chartistas optimistas y
chartistas pesimistas. Los chartistas se contagian el ánimo (opinión mayoritaria
y tendencia del precio) y la gente cambia de estrategia según cuál rinde más.

Simplificaciones declaradas:
- Tiempo discreto: pasos de 0.01 y cambios de grupo con sorteos binomiales.
- Un «día» del video son 200 pasos; β = 20 en vez de 6 (sin esto, con un día
  de 1 unidad, los rendimientos salen con autocorrelación alta).
- El precio sube o baja en saltos de 0.01 con tasas proporcionales al exceso de
  demanda, como en el artículo; mínimo de 4 agentes por grupo.
Las noticias (el valor fundamental) son un paseo aleatorio gaussiano.
"""
import json
import math
import os

import numpy as np

N = 500
PARAM = dict(v1=3.0, v2=2.0, beta=20.0, Tc=10.0, Tf=5.0, a1=0.6, a2=0.2, a3=0.5,
             pf0=10.0, r=0.004, R=0.0004, s=0.75, sig=0.005, nmin=4, dt=0.01, pasos_dia=200)
N_DIAS = 2000
QUEMAR = 200


def correr(semilla=2029, n_dias=N_DIAS, quemar=QUEMAR, **kw):
    q = dict(PARAM, **kw)
    rng = np.random.default_rng(semilla)
    v1, v2, beta, a1, a2, a3 = q["v1"], q["v2"], q["beta"], q["a1"], q["a2"], q["a3"]
    r_, R_, s_, dt, nmin = q["r"], q["R"], q["s"], q["dt"], q["nmin"]
    tc, g = q["Tc"] / N, q["Tf"] / N
    k = q["pasos_dia"]
    sd_paso = q["sig"] * math.sqrt(1.0 / k)
    no, ne, nf = 50, 50, 400
    p = pf = q["pf0"]
    pdot = 0.0
    tot = n_dias + quemar
    P = np.empty(tot); PF = np.empty(tot); Z = np.empty(tot); X = np.empty(tot)
    exp = math.exp
    for dia in range(tot):
        zn = rng.standard_normal(k)
        mu = rng.normal(0, 0.05, k)
        for j in range(k):
            pf *= exp(sd_paso * zn[j])
            nc = no + ne
            x = (no - ne) / nc
            u1 = a1 * x + a2 * pdot / v1
            pe_o = v1 * nc / N * exp(u1)
            po_e = v1 * nc / N * exp(-u1)
            dev = s_ * abs((pf - p) / p)
            u21 = a3 * ((r_ + pdot / v2) / p - R_ - dev)
            u22 = a3 * (R_ - (r_ + pdot / v2) / p - dev)
            u21 = max(-30.0, min(30.0, u21)); u22 = max(-30.0, min(30.0, u22))
            f_o = v2 * no / N * exp(u21); o_f = v2 * nf / N * exp(-u21)
            f_e = v2 * ne / N * exp(u22); e_f = v2 * nf / N * exp(-u22)
            a = rng.binomial(ne, min(1.0, pe_o * dt)); b = rng.binomial(no, min(1.0, po_e * dt))
            c = rng.binomial(nf, min(1.0, f_o * dt)); d = rng.binomial(no, min(1.0, o_f * dt))
            e = rng.binomial(nf, min(1.0, f_e * dt)); f = rng.binomial(ne, min(1.0, e_f * dt))
            no += a - b + c - d; ne += b - a + e - f
            no = max(no, nmin); ne = max(ne, nmin); nf = N - no - ne
            if nf < nmin:
                ex = nmin - nf; nf = nmin
                if no > ne:
                    no -= ex
                else:
                    ne -= ex
            ed = (no - ne) * tc + nf * g * (pf - p)
            lam = beta * (ed + mu[j])
            dp = 0.01 * (rng.poisson(max(lam, 0.0) * dt) - rng.poisson(max(-lam, 0.0) * dt))
            p = max(p + dp, 0.01)
            pdot = dp / dt
        P[dia] = p; PF[dia] = pf; Z[dia] = (no + ne) / N; X[dia] = (no - ne) / (no + ne)
    return P[quemar:], PF[quemar:], Z[quemar:], X[quemar:]


def curtosis(r):
    z = (r - r.mean()) / r.std()
    return float((z ** 4).mean())


def ac(y, k):
    y = y - y.mean()
    return float((y[k:] * y[:-k]).sum() / (y * y).sum())


def resumen(P, PF):
    r = np.diff(np.log(P)); n = np.diff(np.log(PF))
    zr = (r - r.mean()) / r.std(); zn = (n - n.mean()) / n.std()
    return dict(k_r=curtosis(r), k_n=curtosis(n),
                ac1_r=ac(r, 1), ac1_n=ac(n, 1),
                aca1_r=ac(np.abs(r), 1), aca20_r=ac(np.abs(r), 20),
                aca1_n=ac(np.abs(n), 1), aca20_n=ac(np.abs(n), 20),
                max_r=float(np.abs(zr).max()), max_n=float(np.abs(zn).max()),
                d4_r=int((np.abs(zr) > 4).sum()), d4_n=int((np.abs(zn) > 4).sum()))


class Lux:
    def __init__(self, semilla=2029):
        self.semilla = semilla
        self.P, self.PF, self.Z, self.X = correr(semilla)
        self.r = np.diff(np.log(self.P))
        self.n = np.diff(np.log(self.PF))
        self.res = resumen(self.P, self.PF)


def _cache_path():
    return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "salida", ".cache")


def muchas(n=30, semilla0=5000, usar_cache=True):
    """Promedio de n mundos. Se guarda en salida/.cache (no va al repo)."""
    clave = json.dumps(dict(PARAM, n=n, semilla0=semilla0, N=N, d=N_DIAS, q=QUEMAR), sort_keys=True)
    ruta = os.path.join(_cache_path(), "lux_muchas.json")
    if usar_cache and os.path.exists(ruta):
        with open(ruta) as fh:
            dat = json.load(fh)
        if dat.get("clave") == clave:
            return dat["res"]
    from concurrent.futures import ProcessPoolExecutor
    with ProcessPoolExecutor(4) as ex:
        filas = list(ex.map(_uno, range(semilla0, semilla0 + n)))
    res = {k: float(np.mean([f[k] for f in filas])) for k in filas[0]}
    res["n"] = n
    res["k_r_min"] = float(min(f["k_r"] for f in filas))
    res["k_r_max"] = float(max(f["k_r"] for f in filas))
    os.makedirs(_cache_path(), exist_ok=True)
    with open(ruta, "w") as fh:
        json.dump(dict(clave=clave, res=res), fh)
    return res


def _uno(s):
    P, PF, _, _ = correr(s)
    return resumen(P, PF)


if __name__ == "__main__":
    import sys
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 2029
    L = Lux(s)
    print("semilla", s, {k: round(v, 3) for k, v in L.res.items()})
    print("z medio", round(L.Z.mean(), 3), "max", round(L.Z.max(), 3))
    print(muchas())
