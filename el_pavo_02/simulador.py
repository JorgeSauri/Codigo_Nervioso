"""Simulador de «Código Nervioso» · EP02 La trampa de las criptomonedas.

    .venv/bin/python simulador.py            # ventana escalada a tu pantalla
    .venv/bin/python simulador.py --full     # pantalla completa 1920x1080
    .venv/bin/python simulador.py --escena s4

Teclas: 1..9 cambian de escena · Espacio = Pausa · R = Reiniciar · F = pantalla completa · Esc = salir
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
    ap.add_argument("--escena", default=scenes.SCENE_KEYS[0], choices=scenes.SCENE_KEYS)
    ap.add_argument("--escala", type=float, default=None, help="p. ej. 0.66 para una ventana de 1267x713")
    a = ap.parse_args()
    pygame.init()
    pygame.display.set_caption("Código Nervioso · La trampa de las criptomonedas")
    info = pygame.display.Info()
    full = a.full
    scale = a.escala or min(1.0, (info.current_w * 0.92) / W, (info.current_h * 0.88) / H)

    def open_window():
        if full:
            return pygame.display.set_mode((W, H), pygame.FULLSCREEN | pygame.SCALED)
        return pygame.display.set_mode((int(W * scale), int(H * scale)))

    screen = open_window()
    canvas = pygame.Surface((W, H))
    scene = scenes.make_scene(a.escena)
    clock = pygame.time.Clock()
    while True:
        dt = min(clock.tick(60) / 1000.0, 1 / 20)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                return
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    return
                if ev.key == pygame.K_f:
                    full = not full
                    screen = open_window()
                elif ev.key == pygame.K_SPACE:
                    scene.toggle_pause()
                elif ev.key == pygame.K_r:
                    scene.reset()
                elif pygame.K_1 <= ev.key <= pygame.K_9:
                    i = ev.key - pygame.K_1
                    if i < len(scenes.SCENE_KEYS):
                        scene = scenes.make_scene(scenes.SCENE_KEYS[i])
        scene.update(dt)
        scene.draw(canvas)
        if full:
            screen.blit(canvas, (0, 0))
        else:
            pygame.transform.smoothscale(canvas, screen.get_size(), screen)
        pygame.display.flip()


if __name__ == "__main__":
    main()
