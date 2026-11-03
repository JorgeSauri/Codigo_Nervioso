"""S4 · La fábrica de estrategias ganadoras.

Réplica del experimento de sobreajuste de Bailey et al. (2014, 2017):
cientos de reglas de cruce de promedios móviles sobre un precio sintético
impredecible; se elige la mejor en la primera mitad y se aplica en la segunda.
La probabilidad de sobreajuste (PBO) se calcula con CSCV, siguiendo los pasos
de Bailey, Borwein, López de Prado y Zhu (2017), sección 2.
"""
import itertools
import math
import numpy as np

from .datos import rendimientos_t, DIAS_ANIO

ANIOS = 5
N_DIAS = ANIOS * DIAS_ANIO
COMISION = 0.001          # 0.1 % por cada cambio de posición (cada lado)


def media_movil(p, k):
    c = np.cumsum(np.insert(p, 0, 0.0))
    m = np.full(len(p), np.nan)
    m[k - 1:] = (c[k:] - c[:-k]) / k
    return m


CALENTAR = 300            # días previos para que la regla más lenta ya tenga promedio


def media_exp(p, k):
    a = 2.0 / (k + 1)
    m = np.empty(len(p))
    m[0] = p[0]
    for t in range(1, len(p)):
        m[t] = a * p[t] + (1 - a) * m[t - 1]
    return m


def reglas():
    """Cruces de promedio rápido contra lento, simple (S) o exponencial (E)."""
    rapidas = [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20, 25, 30, 40]
    lentas = [10, 15, 20, 30, 40, 50, 60, 80, 100, 120, 150, 200, 250, 300]
    return [(t, f, s) for t in ("S", "E") for f in rapidas for s in lentas if s >= 2 * f]


def sharpe(r, axis=0):
    sd = r.std(axis=axis, ddof=1)
    return np.where(sd > 0, r.mean(axis=axis) / np.where(sd > 0, sd, 1), 0.0) * math.sqrt(DIAS_ANIO)


def cscv_pbo(M, S=16):
    """PBO por validación cruzada combinatoriamente simétrica (Bailey et al. 2017).

    M: matriz T x N de rendimientos (filas = días, columnas = estrategias).
    Se parte en S bloques; para cada una de las C(S, S/2) combinaciones, la mitad
    de los bloques es «dentro de muestra» y el resto «fuera». Se elige la mejor
    estrategia dentro (Sharpe) y se mide su rango relativo fuera, w; el logit es
    ln(w / (1 - w)). PBO = proporción de logits <= 0.
    Devuelve (pbo, logits).
    """
    T, N = M.shape
    resto = T % S                                     # como pypbo: se descartan los primeros días
    T = T - resto
    B = M[resto:].reshape(S, T // S, N)
    s1, s2, n = B.sum(1), (B ** 2).sum(1), T // S         # S x N
    combs = np.array(list(itertools.combinations(range(S), S // 2)))
    C = np.zeros((len(combs), S))
    C[np.arange(len(combs))[:, None], combs] = 1.0
    D = 1.0 - C

    def sr(mask):
        k = mask.sum(1, keepdims=True) * n
        m = (mask @ s1) / k
        v = ((mask @ s2) - k * m ** 2) / (k - 1)
        return m / np.sqrt(np.maximum(v, 1e-300))
    sr_in, sr_out = sr(C), sr(D)
    best = sr_in.argmax(1)
    sr_best = sr_out[np.arange(len(combs)), best]
    # rango de 1 (peor) a N (mejor); los empates reciben el rango promedio
    rango = (sr_out < sr_best[:, None]).sum(1) + 0.5 * ((sr_out == sr_best[:, None]).sum(1) + 1)
    w = rango / (N + 1)
    logits = np.log(w / (1 - w))
    return float((logits <= 0).mean()), logits


class Fabrica:
    def __init__(self, semilla=2026, pbo=True):
        self.semilla = semilla
        total = CALENTAR + N_DIAS
        self.r_todo = rendimientos_t(total, sd=0.035, gl=3, semilla=semilla)
        self.p_todo = 100 * np.exp(np.cumsum(self.r_todo))
        self.reglas = reglas()
        N = len(self.reglas)
        pos = np.zeros((total, N))
        cache = {}
        for j, (tipo, f, s) in enumerate(self.reglas):
            fn = media_movil if tipo == "S" else media_exp
            for k in (f, s):
                if (tipo, k) not in cache:
                    cache[(tipo, k)] = self.p_todo if k == 1 else fn(self.p_todo, k)
            sig = np.sign(cache[(tipo, f)] - cache[(tipo, s)])
            sig = np.nan_to_num(sig)
            pos[1:, j] = sig[:-1]                         # se opera al día siguiente
        cambios = np.abs(np.diff(pos, axis=0, prepend=pos[:1]))
        ret = pos * self.r_todo[:, None]                  # largo / corto
        ret_com = ret - cambios * COMISION
        a = CALENTAR
        self.r, self.p = self.r_todo[a:], self.p_todo[a:]
        self.pos, self.ret, self.ret_com = pos[a:], ret[a:], ret_com[a:]
        self.mitad = m = N_DIAS // 2
        ins, oos = self.ret[:m], self.ret[m:]
        self.sr_in = sharpe(ins)
        self.sr_out = sharpe(oos)
        self.sr_out_com = sharpe(self.ret_com[m:])
        self.t_in = self.sr_in / math.sqrt(DIAS_ANIO) * math.sqrt(len(ins))
        self.campeona = c = int(np.argmax(self.sr_in))
        self.eq_in = np.exp(np.cumsum(ins[:, c])) - 1     # rendimiento acumulado
        self.eq_out = np.exp(np.cumsum(oos[:, c])) - 1
        self.eq_out_com = np.exp(np.cumsum(self.ret_com[m:, c])) - 1
        self.eq_todas_in = np.exp(np.cumsum(ins, axis=0)) - 1
        self.ganancia_in = float(self.eq_in[-1])
        self.ganancia_out = float(self.eq_out[-1])
        self.ganancia_out_com = float(self.eq_out_com[-1])
        self.n_cambios_out = int((np.abs(np.diff(self.pos[m:, c])) > 0).sum())
        self.signif_2 = int((self.t_in > 2).sum())
        self.signif_3 = int((self.t_in > 3).sum())
        self.rango_out = int((self.sr_out < self.sr_out[c]).sum() + 1)
        if pbo:
            self.pbo, self.logits = cscv_pbo(self.ret, S=16)

    def resumen(self):
        t, f, s = self.reglas[self.campeona]
        return {
            "semilla": self.semilla,
            "reglas": len(self.reglas),
            "campeona": f"{t}{f}/{s}",
            "sharpe_fuera_com": round(float(self.sr_out_com[self.campeona]), 2),
            "sharpe_dentro": round(float(self.sr_in[self.campeona]), 2),
            "sharpe_fuera": round(float(self.sr_out[self.campeona]), 2),
            "ganancia_dentro": round(self.ganancia_in * 100, 1),
            "ganancia_fuera": round(self.ganancia_out * 100, 1),
            "ganancia_fuera_comisiones": round(self.ganancia_out_com * 100, 1),
            "cambios_fuera": self.n_cambios_out,
            "t>2": self.signif_2,
            "t>3": self.signif_3,
            "rango_fuera": f"{self.rango_out}/{len(self.reglas)}",
            "pbo": round(self.pbo * 100, 1),
        }


if __name__ == "__main__":
    import sys
    semillas = [int(x) for x in sys.argv[1:]] or [2026]
    for s in semillas:
        print(Fabrica(s).resumen(), flush=True)


def muchos_mundos(n=100, primera=1):
    """Repite el experimento con n precios simulados distintos (semillas primera..)."""
    sin, sout, sout_c = [], [], []
    for s in range(primera, primera + n):
        f = Fabrica(s, pbo=False)
        c = f.campeona
        sin.append(f.sr_in[c]); sout.append(f.sr_out[c]); sout_c.append(f.sr_out_com[c])
    sin, sout, sout_c = map(np.array, (sin, sout, sout_c))
    return {"n": n, "sharpe_dentro": float(sin.mean()), "sharpe_fuera": float(sout.mean()),
            "sharpe_fuera_com": float(sout_c.mean()), "fuera_peor": float((sout < sin).mean()),
            "fuera_neg_com": float((sout_c <= 0).mean())}
