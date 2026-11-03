"""Graba las tomas sin pantalla (cuadros -> ffmpeg -> MP4 H.264, 1920x1080).

Uso:
    .venv/bin/python grabar.py              # todas las tomas
    .venv/bin/python grabar.py s4 s2        # solo algunas
    .venv/bin/python grabar.py --fps 60 s4
    .venv/bin/python grabar.py --foto 30 s4 # un PNG del segundo 30 (para revisar)
"""
import os
import sys
import argparse
import subprocess

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT_DIR = os.path.join(HERE, "salida")

from cn_sim import scenes          # noqa: E402
from cn_sim.ui import W, H         # noqa: E402

ARCHIVOS = {
    "s2": "s2_peor_dia_colas_gordas.mp4",
    "s3": "s3_paseo_aleatorio.mp4",
    "s4": "s4_fabrica_de_estrategias.mp4",
    "s5a": "s5a_cascada.mp4",
    "s5b": "s5b_lux_marchesi.mp4",
    "s6b": "s6b_concurso_de_belleza.mp4",
    "s6c": "s6c_shiller.mp4",
}
FUNDIDO = 0.5   # segundos de fundido desde y hacia negro


def grabar(key, fps):
    sc = scenes.make_scene(key)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, ARCHIVOS.get(key, f"{key}.mp4"))
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
           "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", path]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    surf = pygame.Surface((W, H))
    negro = pygame.Surface((W, H)); negro.fill((0, 0, 0))
    n = int(round(sc.duracion * fps))
    nf = int(FUNDIDO * fps)
    for i in range(n):
        if i:
            sc.update(1.0 / fps)
        sc.draw(surf)
        a = 0.0
        if i < nf:
            a = 1 - i / nf
        elif i >= n - nf:
            a = (i - (n - nf) + 1) / nf
        if a > 0:
            negro.set_alpha(int(255 * a))
            surf.blit(negro, (0, 0))
        proc.stdin.write(pygame.image.tobytes(surf, "RGB"))
    proc.stdin.close()
    proc.wait()
    print(f"{os.path.basename(path)}: {n / fps:.1f} s", flush=True)


def foto(key, segundos):
    sc = scenes.make_scene(key)
    surf = pygame.Surface((W, H))
    paso = 1.0 / 30
    t = 0.0
    out = []
    for s in sorted(segundos):
        while t < s - 1e-9:
            sc.update(paso); t += paso
        sc.draw(surf)
        p = os.path.join(OUT_DIR, f"{key}_t{s:05.1f}.png")
        os.makedirs(OUT_DIR, exist_ok=True)
        pygame.image.save(surf, p)
        out.append(p)
    print("\n".join(out))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("tomas", nargs="*", default=scenes.SCENE_KEYS)
    ap.add_argument("--fps", type=int, default=30)
    ap.add_argument("--foto", type=float, nargs="*", default=None)
    a = ap.parse_args()
    pygame.init()
    pygame.display.set_mode((W, H))
    for k in a.tomas:
        if a.foto:
            foto(k, a.foto)
        else:
            grabar(k, a.fps)


if __name__ == "__main__":
    main()
