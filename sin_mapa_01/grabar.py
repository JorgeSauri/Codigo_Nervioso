"""Graba las tomas del simulador sin pantalla (frames -> ffmpeg -> MP4 H.264).

Uso:
    .venv/bin/python grabar.py              # todas las tomas, en salida/
    .venv/bin/python grabar.py sim02 sim04  # solo algunas
    .venv/bin/python grabar.py --fps 30 sim01

Hace falta ffmpeg en el PATH. Los MP4 quedan en la carpeta salida/.
"""
import os
import sys
import random
import argparse
import subprocess

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
for _v in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS"):
    os.environ.setdefault(_v, "1")
import numpy as np
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
OUT_DIR = os.path.join(HERE, "salida")

from cn_sim import ui, scenes          # noqa: E402
from cn_sim.ui import W, H             # noqa: E402


class Recorder:
    """Avanza la escena cuadro por cuadro y mueve un cursor visible."""

    def __init__(self, scene, path, fps=60):
        self.scene = scene
        self.fps = fps
        self.dt = 1.0 / fps
        self.surf = pygame.Surface((W, H))
        self.cur = [1640.0, 1060.0]
        self.down = 0.0
        self.frames = 0
        cmd = ["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
               "-s", f"{W}x{H}", "-r", str(fps), "-i", "-",
               "-c:v", "libx264", "-threads", "3", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
               "-movflags", "+faststart", path]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)

    # -- básicos ---------------------------------------------------------
    def frame(self, hl=None):
        sc = self.scene
        for c in sc.all_controls():
            if isinstance(c, ui.Slider):
                target = 1.0 if c is hl else 0.0
                c.hl += (target - c.hl) * 0.25
            if isinstance(c, ui.Button) and c.pressed > 0:
                c.pressed = max(0.0, c.pressed - self.dt * 4)
        sc.update(self.dt)
        sc.draw(self.surf)
        ui.draw_cursor(self.surf, (int(self.cur[0]), int(self.cur[1])), self.down)
        self.proc.stdin.write(pygame.image.tobytes(self.surf, "RGB"))
        self.frames += 1

    def wait(self, s, hl=None):
        for _ in range(int(round(s * self.fps))):
            self.down = max(0.0, self.down - 0.15)
            self.frame(hl)

    def move(self, to, dur=0.7, hl=None):
        x0, y0 = self.cur
        n = max(1, int(dur * self.fps))
        for i in range(1, n + 1):
            f = ui.ease(i / n)
            self.cur = [x0 + (to[0] - x0) * f, y0 + (to[1] - y0) * f]
            self.down = max(0.0, self.down - 0.15)
            self.frame(hl)

    # -- controles -------------------------------------------------------
    def drag(self, name, value, dur=2.0, after=0.4):
        sl = self.scene.control(name)
        self.move(sl.knob_pos(), 0.6, hl=sl)
        v0 = sl.value
        n = max(1, int(dur * self.fps))
        for i in range(1, n + 1):
            self.down = min(1.0, self.down + 0.2)
            v = v0 + (value - v0) * ui.ease(i / n)
            sl.set(v)
            kx, ky = sl.knob_pos(v)
            self.cur = [kx, ky]
            self.frame(hl=sl)
        sl.set(value)
        self.wait(after, hl=sl)

    def click(self, name, after=0.5):
        b = self.scene.control(name)
        self.move(b.rect.center, 0.6)
        for _ in range(6):
            self.down = min(1.0, self.down + 0.35)
            self.frame()
        b.click()
        self.wait(after)

    def park(self, dur=0.6):
        """Aparta el cursor a una esquina del panel."""
        self.move((1840, 1050), dur)

    def close(self):
        self.proc.stdin.close()
        self.proc.wait()
        return self.frames / self.fps


# ======================================================================
#  Tomas (una por bloque del guion)
# ======================================================================
def take_sim01(r):
    """Puente con ramas iguales: con olor 'normal' gana una rama al azar; con 'suave' no."""
    s = r.scene
    s.time_scale = 60.0
    r.wait(3)
    r.drag("hormigas", 50, 0.1, after=0.2)
    r.park()
    r.wait(19)                       # se decide (20 min simulados)
    r.drag("fuerza", 1.0, 2.5)       # suave
    r.click("reiniciar")
    r.park()
    r.wait(20)                       # no se decide
    r.drag("fuerza", 2.0, 2.0)       # normal otra vez
    r.drag("hormigas", 500, 2.0)
    r.click("reiniciar")
    r.park()
    r.wait(23)


def take_sim02(r):
    """Rama corta vs larga: ×1.4 y ×2 (los mismos casos que Goss et al.)."""
    s = r.scene
    s.time_scale = 60.0
    r.wait(1.5)
    r.drag("largo", 1.4, 2.5)
    r.click("reiniciar")
    r.park()
    r.wait(25)
    r.drag("largo", 2.0, 2.5)
    r.click("reiniciar")
    r.park()
    r.wait(25)


def take_sim03(r):
    """La trampa: 30 min solo con la rama larga; se abre el atajo y casi nadie cambia."""
    s = r.scene
    s.time_scale = 60.0
    r.wait(2)
    r.move(s.control("evap").knob_pos(), 1.0, hl=s.control("evap"))
    r.wait(1.5, hl=s.control("evap"))
    r.park()
    r.wait(30)
    r.drag("hormigas", 200, 2.0)
    r.click("reiniciar")
    r.park()
    r.wait(30)


def take_sim04(r):
    """Agente viajero con Ant System: una hormiga, luego la colonia."""
    s = r.scene
    r.wait(1.5)
    s.start_oneant(slow_steps=6, step_time=1.5)
    r.wait(19)
    r.click("reiniciar")             # arranca la colonia
    r.park()
    r.wait(18)
    r.drag("distancia", 0.0, 2.5)    # sin mirar la distancia
    r.click("reiniciar")
    r.park()
    r.wait(10)
    r.drag("distancia", 5.0, 2.0)
    r.drag("hormigas", 30, 0.1, after=0.1)
    r.click("reiniciar")
    r.park()
    r.wait(12)


def take_sim05a(r):
    """La trampa con evaporación (versión de computadora): 0 → moderada → muchísima."""
    s = r.scene
    s.time_scale = 60.0
    r.wait(1.5)
    r.park()
    r.wait(20.5)                     # sin evaporación: no cambian
    r.drag("evap", 0.40, 2.5)
    r.click("reiniciar")
    r.park()
    r.wait(21)                       # moderada: cambian
    r.drag("evap", 0.97, 2.5)
    r.click("reiniciar")
    r.park()
    r.wait(22)                       # muchísima: a medias


def take_sim05b(r):
    r.park(0.2)
    r.wait(60)


def take_sim06(r):
    """AS vs ACS vs MAX–MIN con valores publicados."""
    s = r.scene
    r.park(0.2)
    r.wait(36)                       # 180 rondas
    r.wait(24)                       # hasta 300
    r.drag("q0", 0.0, 2.5)
    r.click("reiniciar")
    r.park()
    r.wait(14)


def take_sim06b(r):
    s = r.scene
    r.wait(2.5)
    for _ in range(6):
        r.click("destorcer", after=2.2)
    r.park()
    r.wait(2)
    r.click("reiniciar", after=1.5)
    for _ in range(3):
        r.click("destorcer", after=2.2)
    r.park()
    r.wait(2)


def take_juguemos(r):
    s = r.scene
    r.wait(1)
    r.park()
    r.wait(8)
    r.drag("hormigas", 8, 2.0)
    r.click("reiniciar")
    r.wait(6)
    r.drag("hormigas", 40, 2.0)
    r.drag("fuerza", 3.0, 2.0)
    r.drag("evap", 0.05, 2.0)
    r.click("reiniciar")
    r.park()
    r.wait(8)
    r.drag("fuerza", 1.0, 1.5)
    r.drag("evap", 0.5, 1.5)
    r.drag("distancia", 2.0, 1.5)
    r.click("mapa")
    r.park()
    r.wait(8)
    r.click("pausa", after=2.0)
    r.click("pausa", after=0.3)
    r.drag("distancia", 5.0, 1.5)
    r.click("mapa")
    r.park()
    r.wait(6)


TAKES = {
    "sim01": ("sim1", "sim01_puente_iguales.mp4", take_sim01),
    "sim02": ("sim2", "sim02_puente_desigual.mp4", take_sim02),
    "sim03": ("sim3", "sim03_trampa.mp4", take_sim03),
    "sim04": ("sim4", "sim04_ant_system.mp4", take_sim04),
    "sim05a": ("sim5a", "sim05a_evaporacion_puente.mp4", take_sim05a),
    "sim05b": ("sim5b", "sim05b_evaporacion_mapa_cambia.mp4", take_sim05b),
    "sim06": ("sim6", "sim06_as_acs_mmas.mp4", take_sim06),
    "sim06b": ("sim6b", "sim06b_destorcer.mp4", take_sim06b),
    "juguemos": ("juguemos", "sim07_juguemos.mp4", take_juguemos),
}


def record(key, fps):
    scene_key, fname, fn = TAKES[key]
    random.seed(1); np.random.seed(1)
    sc = scenes.make_scene(scene_key)
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, fname)
    r = Recorder(sc, path, fps)
    fn(r)
    secs = r.close()
    print(f"{fname}: {secs:.1f} s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("takes", nargs="*", default=list(TAKES))
    ap.add_argument("--fps", type=int, default=60)
    a = ap.parse_args()
    pygame.init()
    pygame.display.set_mode((W, H))
    for k in a.takes:
        record(k, a.fps)


if __name__ == "__main__":
    main()
