"""Utilidades compartidas para renders en CPU (PIL + ffmpeg). CC0."""
from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass

import numpy as np
from PIL import Image, ImageDraw, ImageFont

NAVY = (7, 11, 20)
NAVY2 = (16, 24, 43)
CIAN = (62, 224, 208)
MAGENTA = (240, 107, 255)
CORAL = (255, 122, 89)
AMBAR = (255, 193, 77)
PAPEL = (244, 241, 234)
GRIS = (154, 163, 184)
VERDE = (198, 245, 154)

FUENTES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fuentes")
_cache: dict[tuple[str, int], ImageFont.FreeTypeFont] = {}


def formato_px(fmt: str) -> tuple[int, int]:
    if fmt == "9x16":
        return 1080, 1920
    return 1920, 1080


@dataclass
class Lienzo:
    w: int
    h: int
    im: Image.Image
    d: ImageDraw.ImageDraw

    @classmethod
    def crear(cls, fmt: str = "16x9") -> Lienzo:
        w, h = formato_px(fmt)
        im = Image.new("RGB", (w, h), NAVY)
        return cls(w, h, im, ImageDraw.Draw(im))


def fuente(tipo: str, tam: int) -> ImageFont.FreeTypeFont:
    k = (tipo, tam)
    if k not in _cache:
        rutas = {
            "titulo": ("SpaceGrotesk-Bold.ttf", 700),
            "texto": ("Inter-Medium.ttf", 500),
            "texto_b": ("Inter-Bold.ttf", 700),
            "dato": ("JetBrainsMono-SemiBold.ttf", 600),
        }
        nombre, _ = rutas[tipo]
        _cache[k] = ImageFont.truetype(os.path.join(FUENTES, nombre), tam)
    return _cache[k]


def rejilla(d: ImageDraw.ImageDraw, w: int, h: int, paso: int = 64) -> None:
    c = (18, 25, 46)
    for x in range(0, w, paso):
        d.line([(x, 0), (x, h)], fill=c)
    for y in range(0, h, paso):
        d.line([(0, y), (w, y)], fill=c)


def texto(
    d: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    s: str,
    *,
    tipo: str = "texto",
    tam: int = 28,
    color: tuple[int, ...] = PAPEL,
    ancla: str = "la",
) -> None:
    d.text(xy, s, font=fuente(tipo, tam), fill=color, anchor=ancla)


def marco_titulo(lienzo: Lienzo, titulo: str, subtitulo: str | None = None) -> None:
    rejilla(lienzo.d, lienzo.w, lienzo.h)
    texto(lienzo.d, (48, 36), "Código Nervioso · EP05", tipo="dato", tam=22, color=GRIS)
    texto(lienzo.d, (48, 68), titulo, tipo="titulo", tam=44, color=PAPEL)
    if subtitulo:
        texto(lienzo.d, (48, 122), subtitulo, tipo="texto", tam=26, color=GRIS)


class EscritorVideo:
    def __init__(self, ruta: str, w: int, h: int, fps: int = 30) -> None:
        self.fps = fps
        self.p = subprocess.Popen(
            [
                "ffmpeg",
                "-y",
                "-loglevel",
                "error",
                "-f",
                "rawvideo",
                "-pix_fmt",
                "rgb24",
                "-s",
                f"{w}x{h}",
                "-r",
                str(fps),
                "-i",
                "-",
                "-c:v",
                "libx264",
                "-preset",
                "medium",
                "-crf",
                "18",
                "-pix_fmt",
                "yuv420p",
                "-movflags",
                "+faststart",
                ruta,
            ],
            stdin=subprocess.PIPE,
        )
        self.n = 0

    def cuadro(self, im: Image.Image, veces: int = 1) -> None:
        b = np.asarray(im.convert("RGB")).tobytes()
        for _ in range(veces):
            self.p.stdin.write(b)
            self.n += 1

    def cierra(self) -> None:
        self.p.stdin.close()
        self.p.wait()