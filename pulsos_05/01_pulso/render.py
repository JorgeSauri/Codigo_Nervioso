#!/usr/bin/env python3
"""Render animado: LIF frente a Hodgkin-Huxley. CC0."""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from comun_render import CIAN, CORAL, GRIS, MAGENTA, PAPEL, VERDE, EscritorVideo, Lienzo, marco_titulo, texto
from neuronas import I_LIF_JUSTO_DEBAJO, I_LIF_JUSTO_ENCIMA, corriente_pulso, sim_hh, sim_lif

SEMILLA = 20261105
DT = 0.05
FPS = 30


def dibujar_panel(
    lienzo: Lienzo,
    y_top: int,
    alto: int,
    nombre: str,
    color: tuple[int, ...],
    V,
    sp,
    t_ms: float,
    tmax: float,
    idx: int,
) -> None:
    cx = 48
    ancho = lienzo.w - 96
    texto(lienzo.d, (cx, y_top), nombre, tipo="texto_b", tam=24, color=color)
    y0 = y_top + 32
    alt_plot = alto - 40
    pts = []
    for i in range(idx + 1):
        x = cx + ancho * (i * DT / tmax)
        norm = (V[i] + 90.0) / 110.0
        y = y0 + alt_plot * (1.0 - np.clip(norm, 0, 1))
        pts.append((x, y))
    if len(pts) > 1:
        lienzo.d.line(pts, fill=color, width=3)
    for i in range(idx + 1):
        if sp[i]:
            x = cx + ancho * (i * DT / tmax)
            lienzo.d.line([(x, y0), (x, y0 + alt_plot - 4)], fill=VERDE, width=2)


def dibujar_trazas(lienzo: Lienzo, t_ms: float, V_lif, V_hh, sp_lif, sp_hh, iNa, iK, iL, show_ion) -> None:
    w, h = lienzo.w, lienzo.h
    tmax = len(V_lif) * DT
    idx = min(int(t_ms / DT), len(V_lif) - 1)

    marco_titulo(
        lienzo,
        "Un pulso: LIF frente a Hodgkin–Huxley",
        "HH: parámetros del axón gigante del calamar (Hodgkin & Huxley, 1952)",
    )

    # Dejar hueco bajo el subtítulo (~y=122) para que «LIF» no se encime.
    top = 178
    bottom = 56
    n_bands = 3 if show_ion else 2
    band_h = (h - top - bottom) // n_bands

    dibujar_panel(lienzo, top, band_h, "LIF", CIAN, V_lif, sp_lif, t_ms, tmax, idx)
    dibujar_panel(
        lienzo,
        top + band_h,
        band_h,
        "Hodgkin–Huxley",
        MAGENTA,
        V_hh,
        sp_hh,
        t_ms,
        tmax,
        idx,
    )

    if show_ion:
        cx = 48
        ancho = w - 96
        y_ion = top + 2 * band_h + 8
        texto(lienzo.d, (cx, y_ion), "Corrientes iónicas (HH)", tipo="dato", tam=20, color=GRIS)
        y_base = y_ion + 28
        for nombre, serie, color in [("Na⁺", iNa, CORAL), ("K⁺", iK, CIAN), ("fuga", iL, GRIS)]:
            pts = []
            mx = np.max(np.abs(serie[: idx + 1])) + 1e-6
            row_h = (band_h - 50) // 3
            for i in range(idx + 1):
                x = cx + ancho * (i * DT / tmax)
                y = y_base + row_h * 0.7 - row_h * 0.35 * (serie[i] / mx)
                pts.append((x, y))
            if len(pts) > 1:
                lienzo.d.line(pts, fill=color, width=2)
            texto(lienzo.d, (cx + ancho - 160, y_base), nombre, tipo="dato", tam=18, color=color)
            y_base += row_h

    texto(lienzo.d, (48, h - 40), f"t = {t_ms:.0f} ms", tipo="dato", tam=22, color=GRIS)


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
    I_amp = args.corriente
    if args.modo == "justo_debajo":
        I_amp = I_LIF_JUSTO_DEBAJO
    elif args.modo == "justo_encima":
        I_amp = I_LIF_JUSTO_ENCIMA
    I = corriente_pulso(n_steps, DT, I_amp, 20.0, 70.0)

    theta = -50.0
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
    print(
        f"Guardado: {args.salida} (LIF disparos: {int(sp_lif.sum())}, I={I_amp})",
        flush=True,
    )


if __name__ == "__main__":
    main()