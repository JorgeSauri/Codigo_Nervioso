#!/usr/bin/env python3
"""Cuadrícula Fig. 2 · Izhikevich (2003). CC0."""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from comun_render import CIAN, GRIS, Lienzo, NAVY2, PAPEL, texto
from neuronas import IZHI, corriente_pulso, sim_izhi

SEMILLA = 20031120
DT = 0.25
T_STIM = 1000.0


def panel(lienzo: Lienzo, x0: int, y0: int, pw: int, ph: int, key: str, V, sp) -> None:
    lienzo.d.rectangle([x0, y0, x0 + pw, y0 + ph], outline=GRIS, width=1)
    p = IZHI[key]
    texto(lienzo.d, (x0 + 8, y0 + 8), p["label"], tipo="texto_b", tam=20, color=CIAN)
    pts = []
    for i, v in enumerate(V):
        px = x0 + 8 + (pw - 16) * (i / len(V))
        py = y0 + ph - 12 - (ph - 24) * np.clip((v + 80) / 110, 0, 1)
        pts.append((px, py))
    if len(pts) > 1:
        lienzo.d.line(pts, fill=PAPEL, width=2)
    for i in np.where(sp)[0]:
        x = x0 + 8 + (pw - 16) * (i / len(V))
        lienzo.d.line([(x, y0 + 12), (x, y0 + ph - 12)], fill=CIAN, width=1)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formato", choices=["16x9", "9x16"], default="16x9")
    ap.add_argument("--duracion", type=float, default=5.0, help="segundos de video (recorre la simulación)")
    ap.add_argument("--salida", default="salida/02_izhikevich.mp4")
    args = ap.parse_args()

    np.random.seed(SEMILLA)
    n_steps = int(T_STIM / DT)
    I = corriente_pulso(n_steps, DT, 10.0, 0.0, T_STIM * 0.6)
    traces = {}
    for key, par in IZHI.items():
        traces[key] = sim_izhi(DT, n_steps, I, **{k: par[k] for k in "abcd"})

    from comun_render import EscritorVideo, marco_titulo

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    lienzo = Lienzo.crear(args.formato)
    out = EscritorVideo(args.salida, lienzo.w, lienzo.h, 30)
    orden = ["RS", "IB", "CH", "FS", "LTS", "TC", "RZ"]
    cols = 4 if lienzo.w > lienzo.h else 2
    rows = (len(orden) + cols - 1) // cols
    top = 150
    gap = 12
    pw = (lienzo.w - 96 - gap * (cols - 1)) // cols
    ph = (lienzo.h - top - 80 - gap * (rows - 1)) // rows
    n_frames = max(1, int(args.duracion * 30))

    for f in range(n_frames):
        frac = (f + 1) / n_frames
        idx_end = int(frac * n_steps)
        lienzo = Lienzo.crear(args.formato)
        marco_titulo(lienzo, "Izhikevich (2003), Fig. 2", "Siete tipos de disparo con I = 10 pA")
        for k, key in enumerate(orden):
            c = k % cols
            r = k // cols
            x0 = 48 + c * (pw + gap)
            y0 = top + r * (ph + gap)
            V, sp = traces[key]
            panel(lienzo, x0, y0, pw, ph, key, V[:idx_end], sp[:idx_end])
        out.cuadro(lienzo.im)
    out.cierra()
    print(f"Guardado: {args.salida}", flush=True)


if __name__ == "__main__":
    main()