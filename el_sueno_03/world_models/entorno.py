# Envoltura mínima de VizDoom «Take Cover» (ViZDoom, MIT; texturas Freedoom, BSD). CC0.
import os, numpy as np, cv2, vizdoom as vzd
import config as C

def preprocesa(rgb):
    """Cuadro RGB (alto, ancho, 3) -> 64x64x3 uint8, recortando abajo como Ha."""
    h = int(round(rgb.shape[0] * C.RECORTE_Y))
    return cv2.resize(rgb[:h], (64, 64), interpolation=cv2.INTER_AREA)

def accion_a_botones(a):
    if a < -C.UMBRAL: return [1, 0]   # MOVE_LEFT
    if a >  C.UMBRAL: return [0, 1]   # MOVE_RIGHT
    return [0, 0]

class TakeCover:
    def __init__(self, semilla=0, resolucion="RES_160X120", max_pasos=None):
        g = vzd.DoomGame()
        g.load_config(os.path.join(vzd.scenarios_path, "take_cover.cfg"))
        g.set_window_visible(False); g.set_sound_enabled(False)
        g.set_screen_resolution(getattr(vzd.ScreenResolution, resolucion))
        g.set_screen_format(vzd.ScreenFormat.RGB24)
        g.set_seed(int(semilla) % (2**31))
        g.init(); self.g = g
        self.max_pasos = max_pasos or C.MAX_PASOS
    def reset(self):
        self.g.new_episode(); self.t = 0
        self.cuadro = self.g.get_state().screen_buffer.copy()
        return preprocesa(self.cuadro)
    def step(self, a):
        """Devuelve (obs64, murio, terminado). Recompensa = 1 por paso vivo."""
        self.g.make_action(accion_a_botones(a)); self.t += 1
        murio = self.g.is_episode_finished()
        if not murio: self.cuadro = self.g.get_state().screen_buffer.copy()
        fin = murio or self.t >= self.max_pasos
        return preprocesa(self.cuadro), murio, fin
    def close(self): self.g.close()

class PoliticaAleatoria:
    """[código Ha, extract.py] acción uniforme en [-1,1] que se mantiene 1-10 cuadros."""
    def __init__(self, rng): self.rng = rng; self.rep = 1; self.a = 0.0; self.k = 0
    def __call__(self):
        if self.k % self.rep == 0:
            self.a = self.rng.random() * 2 - 1; self.rep = int(self.rng.integers(1, 11)); self.k = 0
        self.k += 1; return self.a
