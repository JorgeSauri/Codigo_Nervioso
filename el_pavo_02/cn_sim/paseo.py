"""S3 · ¿Camina como borracho? Paseo aleatorio con volatilidad que recuerda.

Serie sintética GARCH(1,1) con innovaciones t (semilla fija). Por construcción
la dirección de cada día no depende de los anteriores, pero el tamaño sí.

Pruebas que se aplican a la serie, igual que a un precio real:
- Ratio de varianza de Lo y MacKinlay (1988), con el paquete `arch`
  (versión robusta a heterocedasticidad).
- Exponente de Hurst por DFA (Peng et al. 1994) en ventanas móviles de 500 días,
  con m = 4, 8, 16, 32, 64, 128, como en Bariviera (2017).
"""
import numpy as np
from arch.unitroot import VarianceRatio

from .datos import garch_t

N_DIAS = 2000
VENTANA = 500
ESCALAS = (4, 8, 16, 32, 64, 128)
LAGS = (2, 5, 10, 20)


def hurst_dfa(y, escalas=ESCALAS):
    """Exponente de Hurst por DFA-1 (tendencia lineal en cada bloque)."""
    y = np.asarray(y, float)
    x = np.cumsum(y - y.mean())
    M = len(x)
    F = []
    for m in escalas:
        k = M // m
        seg = x[:k * m].reshape(k, m)
        i = np.arange(m)
        ic = i - i.mean()
        b = (seg - seg.mean(1, keepdims=True)) @ ic / (ic @ ic)
        res = seg - seg.mean(1, keepdims=True) - b[:, None] * ic
        F.append(np.sqrt((res ** 2).mean()))
    return float(np.polyfit(np.log(escalas), np.log(F), 1)[0])


def hurst_movil(y, ventana=VENTANA, paso=1):
    ini = np.arange(0, len(y) - ventana + 1, paso)
    return ini + ventana - 1, np.array([hurst_dfa(y[i:i + ventana]) for i in ini])


def razon_varianza(nivel, q):
    vr = VarianceRatio(nivel, lags=q, robust=True)
    return float(vr.vr), float(vr.pvalue)


def autocorr(y, k=1):
    y = y - y.mean()
    return float((y[k:] * y[:-k]).sum() / (y * y).sum())


class Paseo:
    def __init__(self, semilla=2028, n=N_DIAS):
        self.semilla = semilla
        self.r = r = garch_t(n, semilla=semilla)
        self.a = a = np.abs(r)
        self.logp = np.concatenate([[0.0], np.cumsum(r)])
        self.nivel_a = np.concatenate([[0.0], np.cumsum(a - a.mean())])
        self.vr_r = {q: razon_varianza(self.logp, q) for q in LAGS}
        self.vr_a = {q: razon_varianza(self.nivel_a, q) for q in LAGS}
        self.dias_h, self.h_r = hurst_movil(r)
        _, self.h_a = hurst_movil(a)
        self.H_r = hurst_dfa(r)
        self.H_a = hurst_dfa(a)
        self.ac_r = autocorr(r)
        self.ac_a = autocorr(a)
        self.frac_inercia_r = float((self.h_r > 0.6).mean())
        self.frac_inercia_a = float((self.h_a > 0.6).mean())


def muchas_series(n=100, semilla0=3000, q=10):
    hr, ha, rej_r, rej_a, acr, aca, fr = [], [], 0, 0, [], [], []
    for s in range(semilla0, semilla0 + n):
        r = garch_t(N_DIAS, semilla=s)
        a = np.abs(r)
        hr.append(hurst_dfa(r)); ha.append(hurst_dfa(a))
        acr.append(autocorr(r)); aca.append(autocorr(a))
        fr.append(float((hurst_movil(r, paso=10)[1] > 0.6).mean()))
        _, p1 = razon_varianza(np.concatenate([[0.0], np.cumsum(r)]), q)
        _, p2 = razon_varianza(np.concatenate([[0.0], np.cumsum(a - a.mean())]), q)
        rej_r += p1 < 0.05
        rej_a += p2 < 0.05
    return dict(n=n, q=q, h_r=float(np.mean(hr)), h_a=float(np.mean(ha)),
                rej_r=rej_r / n, rej_a=rej_a / n,
                ac_r=float(np.mean(acr)), ac_a=float(np.mean(aca)),
                frac_inercia_r=float(np.mean(fr)),
                con_inercia=float(np.mean(np.array(fr) > 0)))


if __name__ == "__main__":
    import sys
    s = int(sys.argv[1]) if len(sys.argv) > 1 else 2028
    p = Paseo(s)
    print("semilla", s)
    print("VR rendimientos", {q: (round(v, 3), round(pv, 3)) for q, (v, pv) in p.vr_r.items()})
    print("VR tamaño", {q: (round(v, 3), round(pv, 4)) for q, (v, pv) in p.vr_a.items()})
    print("Hurst r", round(p.H_r, 3), "rango móvil", round(p.h_r.min(), 3), round(p.h_r.max(), 3))
    print("Hurst |r|", round(p.H_a, 3), "rango móvil", round(p.h_a.min(), 3), round(p.h_a.max(), 3))
    print("ac1", round(p.ac_r, 3), round(p.ac_a, 3))
    print(muchas_series(100))
