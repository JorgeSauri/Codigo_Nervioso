"""Simulador interactivo de «Código Nervioso» · EP01 Hormigas.

    .venv/bin/python simulador.py            # ventana escalada a tu pantalla
    .venv/bin/python simulador.py --full     # pantalla completa 1920x1080
    .venv/bin/python simulador.py --escena sim4

Teclas: 1..9 cambian de escena · Espacio = Pausa · R = Reiniciar · F = pantalla completa
        O = una sola hormiga (escena 4) · Esc = salir
"""
import os
import sys
import argparse
import pygame

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from cn_sim import scenes          # noqa: E402
from cn_sim.ui import W, H         # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true")
    ap.add_argument("--escena", default="sim1", choices=scenes.SCENE_KEYS)
    ap.add_argument("--escala", type=float, default=None, help="p. ej. 0.66 para una ventana de 1267x713")
    a = ap.parse_args()
    pygame.init()
    pygame.display.set_caption("Código Nervioso · Simulador de hormigas")
    info = pygame.display.Info()
    full = a.full
    scale = a.escala or min(1.0, (info.current_w * 0.92) / W, (info.current_h * 0.88) / H)

    def open_window():
        if full:
            return pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
        return pygame.display.set_mode((int(W * scale), int(H * scale)))

    screen = open_window()
    canvas = pygame.Surface((W, H))
    key = a.escena
    scene = scenes.make_scene(key)
    clock = pygame.time.Clock()
    while True:
        dt = min(clock.tick(60) / 1000.0, 1 / 20)
        sx = W / screen.get_width(); sy = H / screen.get_height()
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return
                if ev.key == pygame.K_f:
                    full = not full
                    screen = open_window()
                    continue
                if ev.key == pygame.K_SPACE:
                    scene.toggle_pause()
                if ev.key == pygame.K_r and hasattr(scene, "reset"):
                    scene.reset()
                if ev.key == pygame.K_o and hasattr(scene, "start_oneant"):
                    scene.start_oneant()
                if pygame.K_1 <= ev.key <= pygame.K_9:
                    i = ev.key - pygame.K_1
                    if i < len(scenes.SCENE_KEYS):
                        key = scenes.SCENE_KEYS[i]
                        scene = scenes.make_scene(key)
                continue
            if ev.type in (pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP, pygame.MOUSEMOTION):
                if not full:
                    d = dict(ev.dict)
                    d["pos"] = (int(ev.pos[0] * sx), int(ev.pos[1] * sy))
                    ev = pygame.event.Event(ev.type, d)
                scene.handle(ev)
        scene.update(dt)
        scene.draw(canvas)
        if full:
            screen.blit(canvas, (0, 0))
        else:
            pygame.transform.smoothscale(canvas, screen.get_size(), screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
