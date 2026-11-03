"""S2 · ¿Cuánto pesa el peor día? Réplica del método de la Tabla 3.3 de Taleb (2020)
sobre rendimientos diarios simulados con colas gordas (t de Student, 3 grados de libertad).

- «Max Quartic»: max(X⁴) / Σ X⁴, la parte de la curtosis que aporta una sola observación.
- Exponente de cola de las pérdidas con el paquete `powerlaw` (Alstott et al. 2014).
  `powerlaw` da el exponente α de la densidad; el de la cola acumulada es α − 1.
"""
import math
import warnings
import numpy as np

from .datos import rendimientos_t, rendimientos_normales, DIAS_ANIO

ANIOS = 10
N_DIAS = ANIOS * DIAS_ANIO
SD = 0.045            # volatilidad diaria (calibración cualitativa, no de un proveedor)
GL = 3                # grados de libertad de la t: colas gordas
UMBRAL = -0.20        # «caer 20 % o más en un día»


def max_cuartica(x):
    x4 = np.asarray(x, float) ** 4
    return float(x4.max() / x4.sum())


def normal_cdf(z):
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def exponente_cola(perdidas):
    import powerlaw
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        fit = powerlaw.Fit(perdidas, verbose=False, parameter_ranges={"alpha": [1.01, 8.0]})
    return float(fit.power_law.alpha - 1), float(fit.power_law.xmin), int(fit.n_tail)


class Colas:
    def __init__(self, semilla=2026, sd=SD, gl=GL, n=N_DIAS):
        self.semilla = semilla
        self.sd, self.gl, self.n = sd, gl, n
        self.r = rendimientos_t(n, sd=sd, gl=gl, semilla=semilla)
        self.sd_muestral = float(self.r.std())
        # la campana con la misma media y desviación que la serie
        self.mu = float(self.r.mean())
        self.p_umbral_campana = normal_cdf((UMBRAL - self.mu) / self.sd_muestral)
        self.esperados_campana = n * self.p_umbral_campana
        self.observados = int((self.r <= UMBRAL).sum())
        self.mq = max_cuartica(self.r)
        self.i_peor4 = int(np.argmax(self.r ** 4))
        self.peor = float(self.r.min())
        self.mejor = float(self.r.max())
        g = rendimientos_normales(n, sd=self.sd_muestral, semilla=semilla + 1)
        self.mq_campana = max_cuartica(g)
        perd = -self.r[self.r < 0]
        self.alfa_cola, self.xmin, self.n_cola = exponente_cola(perd)

    def resumen(self):
        return dict(semilla=self.semilla, dias=self.n, sd=self.sd_muestral,
                    esperados=self.esperados_campana, observados=self.observados,
                    mq=self.mq, mq_campana=self.mq_campana, peor=self.peor, mejor=self.mejor,
                    alfa_cola=self.alfa_cola, xmin=self.xmin, n_cola=self.n_cola)


def muchas_series(n=100, sd=SD, gl=GL, dias=N_DIAS, semilla0=1):
    mq, mqg = [], []
    for s in range(semilla0, semilla0 + n):
        r = rendimientos_t(dias, sd=sd, gl=gl, semilla=s)
        mq.append(max_cuartica(r))
        mqg.append(max_cuartica(rendimientos_normales(dias, sd=float(r.std()), semilla=s + 100000)))
    mq, mqg = np.array(mq), np.array(mqg)
    return dict(n=n, p5=float(np.percentile(mq, 5)), p50=float(np.median(mq)),
                p95=float(np.percentile(mq, 95)), min=float(mq.min()), max=float(mq.max()), g_p50=float(np.median(mqg)),
                g_p95=float(np.percentile(mqg, 95)))


if __name__ == "__main__":
    import sys
    for s in (sys.argv[1:] or ["2026"]):
        c = Colas(int(s))
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in c.resumen().items()})
    print(muchas_series())
