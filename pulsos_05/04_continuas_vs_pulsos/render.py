#!/usr/bin/env python3
"""Red continua vs red de impulsos · lado a lado. CC0."""
from __future__ import annotations

import argparse
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from comun_render import AMBAR, CIAN, GRIS, Lienzo, MAGENTA, PAPEL, VERDE, texto
from comun_render import EscritorVideo, marco_titulo, rejilla

SEMILLA = 4404


class RedContinua:
    def __init__(self, rng: np.random.Generator) -> None:
        self.W = rng.normal(0, 0.4, (5, 5))
        self.b = rng.normal(0, 0.1, 5)

    def paso(self, x: np.ndarray) -> np.ndarray:
        return np.tanh(self.W @ x + self.b)


class RedImpulsos:
    def __init__(self, rng: np.random.Generator) -> None:
        self.W = rng.normal(0, 0.35, (5, 5))
        self.umbral = -0.2
        self.v = rng.uniform(-0.5, 0.1, 5)
        self.tau = 15.0
        self.spikes_hist: list[list[int]] = [[] for _ in range(5)]

    def paso(self, x_in: np.ndarray, dt: float = 1.0) -> np.ndarray:
        I = self.W @ (x_in > 0.5).astype(float) + x_in
        self.v += dt * (-self.v + I) / self.tau
        sp = self.v >= self.umbral
        out = sp.astype(float)
        self.v = np.where(sp, 0.0, self.v)
        return out


def dibujar_red(d, x0, y0, bw, bh, activ, W, es_impulso, t_local) -> None:
    pos = []
    n = 5
    for i in range(n):
        px = x0 + bw * (0.2 + 0.6 * (i / max(1, n - 1)))
        py = y0 + bh * 0.35
        pos.append((px, py))
        r = 14 + (10 if activ[i] > 0.5 and es_impulso else 0)
        color = CIAN if activ[i] > 0.3 else GRIS
        d.ellipse([px - r, py - r, px + r, py + r], fill=color, outline=PAPEL)
        d.text((px, py + r + 8), f"n{i}", anchor="mm", fill=GRIS)
    for j in range(n):
        for i in range(n):
            if i == j:
                continue
            w = abs(W[i, j])
            if w < 0.05:
                continue
            width = max(1, int(6 * w))
            c = MAGENTA if W[i, j] > 0 else AMBAR
            d.line([pos[j][0], pos[j][1], pos[i][0], pos[i][1]], fill=c, width=width)
    if es_impulso:
        for j, (px, py) in enumerate(pos):
            if activ[j] > 0.5:
                for i in range(n):
                    if i == j or abs(W[i, j]) < 0.05:
                        continue
                    tx = pos[i][0]
                    ty = pos[i][1]
                    pulse = 0.3 + 0.7 * abs(np.sin(t_local * 0.2 + i))
                    mx = px + (tx - px) * pulse
                    my = py + (ty - py) * pulse
                    d.ellipse([mx - 4, my - 4, mx + 4, my + 4], fill=VERDE)


def raster(d, x0, y0, w, h, hist, t_now, color=CIAN) -> None:
    d.rectangle([x0, y0, x0 + w, y0 + h], outline=GRIS)
    for ni, times in enumerate(hist):
        for t in times:
            if t > t_now:
                break
            yy = y0 + 8 + (h - 16) * (ni / max(1, len(hist) - 1))
            xx = x0 + 8 + (w - 16) * min(1.0, t / max(t_now, 1))
            d.rectangle([xx, yy - 3, xx + 3, yy + 3], fill=color)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--formato", choices=["16x9", "9x16"], default="16x9")
    ap.add_argument("--duracion", type=float, default=5.0)
    ap.add_argument("--salida", default="salida/04_continuas_vs_pulsos.mp4")
    args = ap.parse_args()

    rng = np.random.default_rng(SEMILLA)
    cont = RedContinua(rng)
    imp = RedImpulsos(np.random.default_rng(SEMILLA + 1))
    T = int(args.duracion * 30)
    x = rng.uniform(-0.5, 0.5, 5)
    traj_c = []
    counts = []
    spikes_frame: list[np.ndarray] = []
    t_global = 0
    for _ in range(T):
        x = 0.85 * x + 0.15 * rng.normal(0, 0.3, 5)
        x = cont.paso(x)
        traj_c.append(x.copy())
        sp = imp.paso(x, dt=2.0)
        t_global += 1
        for ni in np.where(sp)[0]:
            imp.spikes_hist[ni].append(t_global)
        spikes_frame.append(sp.copy())
        counts.append(sum(len(h) for h in imp.spikes_hist))

    os.makedirs(os.path.dirname(args.salida) or ".", exist_ok=True)
    lienzo = Lienzo.crear(args.formato)
    out = EscritorVideo(args.salida, lienzo.w, lienzo.h, 30)
    mitad = lienzo.w // 2

    for f in range(T):
        lienzo = Lienzo.crear(args.formato)
        rejilla(lienzo.d, lienzo.w, lienzo.h)
        marco_titulo(lienzo, "Continuas frente a impulsos", "Misma topología · distinta representación temporal")
        texto(lienzo.d, (48, 155), "Activaciones continuas", tipo="texto_b", tam=26, color=MAGENTA)
        texto(lienzo.d, (mitad + 24, 155), "Red de impulsos (SNN)", tipo="texto_b", tam=26, color=CIAN)
        act_c = np.clip((traj_c[f] + 1) / 2, 0, 1)
        act_i = spikes_frame[f]

        bw = mitad - 72
        bh = min(340, lienzo.h // 3)
        dibujar_red(lienzo.d, 48, 190, bw, bh, act_c, cont.W, False, f)
        dibujar_red(lienzo.d, mitad + 24, 190, bw, bh, act_i, imp.W, True, f)
        ry = 190 + bh + 36
        rh = 120
        texto(lienzo.d, (mitad + 24, ry - 20), "Raster de disparos", tipo="dato", tam=20, color=GRIS)
        raster(lienzo.d, mitad + 24, ry, bw, rh, imp.spikes_hist, f + 1)
        texto(
            lienzo.d,
            (mitad + 24, ry + rh + 28),
            f"Pulsos contados (sin convertir a energía): {counts[f]}",
            tipo="dato",
            tam=22,
            color=PAPEL,
        )
        texto(
            lienzo.d,
            (48, ry),
            "Valores reales fluyendo cada paso",
            tipo="texto",
            tam=22,
            color=GRIS,
        )
        for i in range(5):
            texto(
                lienzo.d,
                (48, ry + 30 + i * 22),
                f"h{i}: {traj_c[f][i]:+.3f}",
                tipo="dato",
                tam=18,
                color=PAPEL,
            )
        out.cuadro(lienzo.im)
    out.cierra()
    print(f"Guardado: {args.salida}", flush=True)


if __name__ == "__main__":
    main()