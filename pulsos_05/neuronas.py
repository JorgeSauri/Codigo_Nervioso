"""Modelos LIF, Hodgkin-Huxley e Izhikevich en NumPy (CPU). CC0."""
from __future__ import annotations

import numpy as np

# Hodgkin-Huxley: parámetros del axón gigante del calamar (Hodgkin & Huxley, 1952)
HH = dict(
    Cm=1.0,
    gNa=120.0,
    gK=36.0,
    gL=0.3,
    ENa=50.0,
    EK=-77.0,
    EL=-54.387,
)


def alpha_m(v: float) -> float:
    x = v + 40.0
    return 0.1 * x / (1.0 - np.exp(-x / 10.0)) if abs(x) > 1e-6 else 1.0


def beta_m(v: float) -> float:
    return 4.0 * np.exp(-(v + 65.0) / 18.0)


def alpha_h(v: float) -> float:
    return 0.07 * np.exp(-(v + 65.0) / 20.0)


def beta_h(v: float) -> float:
    return 1.0 / (1.0 + np.exp(-(v + 35.0) / 10.0))


def alpha_n(v: float) -> float:
    x = v + 55.0
    return 0.01 * x / (1.0 - np.exp(-x / 10.0)) if abs(x) > 1e-6 else 0.1


def beta_n(v: float) -> float:
    return 0.125 * np.exp(-(v + 65.0) / 80.0)


def sim_lif(
    dt: float,
    n_steps: int,
    I_ext: np.ndarray,
    *,
    tau_m: float = 20.0,
    R: float = 1.0,
    E_L: float = -70.0,
    V_reset: float = -70.0,
    theta: float = -50.0,
    V0: float = -70.0,
) -> tuple[np.ndarray, np.ndarray]:
    """Integración Euler de LIF (Gerstner & Kistler, caps. 1–2)."""
    V = np.zeros(n_steps)
    spikes = np.zeros(n_steps, dtype=bool)
    v = V0
    for t in range(n_steps):
        V[t] = v
        dv = (-(v - E_L) + R * I_ext[t]) / tau_m
        v = v + dt * dv
        if v >= theta:
            spikes[t] = True
            v = V_reset
    return V, spikes


def sim_hh(
    dt: float,
    n_steps: int,
    I_ext: np.ndarray,
    *,
    V0: float = -65.0,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    v = V0
    m = alpha_m(v) / (alpha_m(v) + beta_m(v))
    n = alpha_n(v) / (alpha_n(v) + beta_n(v))
    h = alpha_h(v) / (alpha_h(v) + beta_h(v))
    V = np.zeros(n_steps)
    iNa = np.zeros(n_steps)
    iK = np.zeros(n_steps)
    iL = np.zeros(n_steps)
    spikes = np.zeros(n_steps, dtype=bool)
    p = HH
    for t in range(n_steps):
        V[t] = v
        iNa[t] = p["gNa"] * (m**3) * h * (v - p["ENa"])
        iK[t] = p["gK"] * (n**4) * (v - p["EK"])
        iL[t] = p["gL"] * (v - p["EL"])
        dv = (I_ext[t] - iNa[t] - iK[t] - iL[t]) / p["Cm"]
        dm = alpha_m(v) * (1 - m) - beta_m(v) * m
        dn = alpha_n(v) * (1 - n) - beta_n(v) * n
        dh = alpha_h(v) * (1 - h) - beta_h(v) * h
        v_old = v
        v += dt * dv
        m += dt * dm
        n += dt * dn
        h += dt * dh
        if v_old < 0.0 <= v:
            spikes[t] = True
    return V, iNa, iK, iL, spikes


def corriente_pulso(n_steps: int, dt: float, I_amp: float, t_on: float, t_off: float) -> np.ndarray:
    I = np.zeros(n_steps)
    i0 = int(t_on / dt)
    i1 = int(t_off / dt)
    I[i0:i1] = I_amp
    return I


IZHI = {
    "RS": dict(a=0.02, b=0.2, c=-65.0, d=8.0, label="RS"),
    "IB": dict(a=0.02, b=0.2, c=-55.0, d=4.0, label="IB"),
    "CH": dict(a=0.02, b=0.2, c=-50.0, d=2.0, label="CH"),
    "FS": dict(a=0.1, b=0.2, c=-65.0, d=2.0, label="FS"),
    "LTS": dict(a=0.02, b=0.25, c=-65.0, d=2.0, label="LTS"),
    "TC": dict(a=0.02, b=0.2, c=-65.0, d=20.0, label="TC"),
    "RZ": dict(a=0.1, b=0.26, c=-65.0, d=2.0, label="RZ"),
}


def sim_izhi(
    dt: float,
    n_steps: int,
    I_ext: np.ndarray,
    *,
    a: float,
    b: float,
    c: float,
    d: float,
    v0: float = -65.0,
    u0: float | None = None,
) -> tuple[np.ndarray, np.ndarray]:
    if u0 is None:
        u0 = b * v0
    v = v0
    u = u0
    V = np.zeros(n_steps)
    spikes = np.zeros(n_steps, dtype=bool)
    for t in range(n_steps):
        V[t] = v
        dv = (0.04 * v * v + 5.0 * v + 140.0 - u + I_ext[t]) * dt
        du = (a * (b * v - u)) * dt
        v += dv
        u += du
        if v >= 30.0:
            spikes[t] = True
            v = c
            u += d
    return V, spikes