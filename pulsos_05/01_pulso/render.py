#!/usr/bin/env python3
"""Render animado: LIF frente a Hodgkin-Huxley. CC0."""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from comun_render import CIAN, CORAL, GRIS, MAGENTA, NAVY2, PAPEL, VERDE, EscritorVideo, Lienzo, marco_titulo, texto
from neuronas import corriente_pulso, sim_hh, sim_lif

SEMILLA = 20261105
DT = 0.05
FPS = 30


def corriente_umbral_lif(theta: float, R: float, E_L: float, tau_m: float) -> float:
    """Corriente DC en régimen subumbral que lleva V cerca de theta-ε."""
    return (theta - 0.3 - E_L) / R + 0.01


def dibujar_trazas(lienzo: Lienzo, t_ms: float, V_lif, V_hh, sp_lif, sp_hh, iNa, iK, iL, show_ion) -> None:
    w, h = lienzo.w, lienzo.h
    cx = 48
    vy = 180 if h > 1200 else 160
    alto = h - vy - 120
    ancho = w - 96
    tmax = len(V_lif) * DT
    idx = min(int(t_ms / DT), len(V_lif) - 1)

    marco_titulo(
        lienzo,
        "Un pulso: LIF frente a Hodgkin–Huxley",
        "HH: parámetros del axón gigante del calamar (Hodgkin & Huxley, 1952)",
    )

    for nombre, color, V, sp, y0 in [
        ("LIF", CIAN, V_lif, sp_lif, vy),
        ("Hodgkin–Huxley", MAGENTA, V_hh, sp_hh, vy + alto // 2 + 20),
    ]:
        texto(lienzo.d, (cx, y0 - 28), nombre, tipo="texto_b", tam=24, color=color)
        pts = []
        for i in range(idx + 1):
            x = cx + ancho * (i * DT / tmax)
            norm = (V[i] + 90.0) / 110.0
            y = y0 + alto // 2 * (1.0 - np.clip(norm, 0, 1))
            pts.append((x, y))
        if len(pts) > 1:
            lienzo.d.line(pts, fill=color, width=3)
        for i in range(idx + 1):
            if sp[i]:
                x = cx + ancho * (i * DT / tmax)
                lienzo.d.line([(x, y0), (x, y0 + alto // 2 - 4)], fill=VERDE, width=2)

    if show_ion:
        y0 = vy + alto // 2 + 20 + alto // 2 + 30
        texto(lienzo.d, (cx, y0 - 24), "Corrientes iónicas (HH)", tipo="dato", tam=20, color=GRIS)
        for nombre, serie, color in [
            ("Na⁺", iNa, CORAL),
            ("K⁺", iK, CIAN),
            ("fuga", iL, GRIS),
        ]:
            pts = []
            mx = np.max(np.abs(serie[: idx + 1])) + 1e-6
            for i in range(idx + 1):
                x = cx + ancho * (i * DT / tmax)
                y = y0 + 50 - 40 * (serie[i] / mx)
                pts.append((x, y))
            if len(pts) > 1:
                lienzo.d.line(pts, fill=color, width=2)
            texto(lienzo.d, (cx + ancho - 200, y0 + 10), nombre, tipo="dato", tam=18, color=color)
            y0 += 28

    texto(lienzo.d, (cx, h - 48), f"t = {t_ms:.0f} ms", tipo="dato", tam=22, color=GRIS)


def main() -> None:
    ap = argparse.ArgumentParser(description="Render LIF vs HH")
    ap.add_argument("--formato", choices=["16x9", "9x16"], default="16x9")
    ap.add_argument("--duracion", type=float, default=5.0)
    ap.add_argument("--salida", default="salida/01_pulso.mp4")
    ap.add_argument("--corriente", type=float, default=12.0)
    ap.add_argument("--modo", choices=["manual", "justo_debajo", "justo_encima"], default="manual")
    args = ap.parse_args()

    np.random.seed(SEMILLA)
    n_steps = int(args.duracion / DT) + int(80 / DT)
    I = corriente_pulso(n_steps, DT, args.corriente, 20.0, 70.0)

    theta = -50.0
    if args.modo == "justo_debajo":
        I = corriente_pulso(n_steps, DT, corriente_umbral_lif(theta, 1.0, -70.0, 20.0), 20.0, 70.0)
    elif args.modo == "justo_encima":
        I = corriente_pulso(n_steps, DT, corriente_umbral_lif(theta, 1.0, -70.0, 20.0) + 0.15, 20.0, 70.0)

    V_lif, sp_lif = sim_lif(DT, n_steps, I, theta=theta, tau_m=20.0)
    V_hh, iNa, iK, iL, sp_hh = sim_hh(DT, n_steps, I * 0.5)

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    lienzo = Lienzo.crear(args.formato)
    out = EscritorVideo(args.salida, lienzo.w, lienzo.h, FPS)
    n_frames = int(args.duracion * FPS)
    for f in range(n_frames):
        t_ms = f * (n_steps * DT) / n_frames
        lienzo = Lienzo.crear(args.formato)
        dibujar_trazas(lienzo, t_ms, V_lif, V_hh, sp_lif, sp_hh, iNa, iK, iL, True)
        out.cuadro(lienzo.im)
    out.cierra()
    print(f"Guardado: {args.salida}", flush=True)


if __name__ == "__main__":
    main()