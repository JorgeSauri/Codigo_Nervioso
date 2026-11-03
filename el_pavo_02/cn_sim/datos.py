"""Series sintéticas con semilla fija. Ningún dato de proveedores de precios."""
import numpy as np

DIAS_ANIO = 365          # cripto cotiza todos los días


def rendimientos_t(n, sd=0.035, gl=3, semilla=2026):
    """Rendimientos diarios independientes con colas gordas (t de Student).

    La media es cero y cada día es independiente del anterior: por construcción
    nadie puede predecir el siguiente paso.
    """
    rng = np.random.default_rng(semilla)
    x = rng.standard_t(gl, size=n)
    x = x / np.sqrt(gl / (gl - 2))          # varianza 1
    return sd * x


def rendimientos_normales(n, sd=0.035, semilla=2027):
    rng = np.random.default_rng(semilla)
    return sd * rng.standard_normal(n)


def garch_t(n, omega=2e-5, alfa=0.10, beta=0.88, gl=4, semilla=2028, quemar=500):
    """GARCH(1,1) con innovaciones t: la dirección no tiene memoria, el tamaño sí."""
    rng = np.random.default_rng(semilla)
    z = rng.standard_t(gl, size=n + quemar) / np.sqrt(gl / (gl - 2))
    r = np.empty(n + quemar)
    s2 = omega / (1 - alfa - beta)
    for t in range(n + quemar):
        r[t] = np.sqrt(s2) * z[t]
        s2 = omega + alfa * r[t] ** 2 + beta * s2
    return r[quemar:]


def precio(rend, p0=100.0):
    return p0 * np.exp(np.cumsum(rend))
