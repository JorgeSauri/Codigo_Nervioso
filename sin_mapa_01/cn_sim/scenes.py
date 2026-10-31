"""Escenas del simulador. Cada escena tiene controles, update(dt) y draw(surf)."""
import math
import numpy as np
import pygame

from . import ui
from .ui import (W, H, BG, BG2, PANEL, CYAN, CORAL, PAPER, GREY, DIM, GOLD,
                 text, rrect, mix, Slider, Button, layout_panel, flatten, chart)
from .bridge import BridgeModel, NEST, OUT, FOOD, BACK
from .tsp import Colony, make_cities, best_known, tour_length, two_opt


def pct(v):
    return f"{v * 100:.0f} %"


class Scene:
    title = ""
    subtitle = ""
    note = "Simulación didáctica: los números son de esta simulación, no de un experimento."

    def __init__(self):
        self.paused = False
        self.controls = []
        self.flash_msg = None
        self.flash_t = 0.0
        self.flash_pos = (710, 190)

    def all_controls(self):
        return flatten(self.controls)

    def control(self, name):
        for c in self.all_controls():
            if c.name == name:
                return c
        raise KeyError(name)

    def handle(self, ev):
        for c in self.all_controls():
            if c.visible and c.handle(ev):
                return True
        return False

    def toggle_pause(self):
        self.paused = not self.paused
        try:
            b = self.control("pausa")
            b.label = "Seguir" if self.paused else "Pausa"
            b.active = self.paused
        except KeyError:
            pass

    def flash(self, msg, dur=3.0):
        self.flash_msg, self.flash_t = msg, dur

    def draw_common(self, surf):
        ui.header(surf, self.title, self.subtitle)
        rrect(surf, PANEL, pygame.Rect(1385, 150, 500, 870), 22)
        for c in self.all_controls():
            if c.visible:
                c.draw(surf)
        if self.note:
            text(surf, self.note, (1360, H - 58), "text", 21, GREY, "midright")
        ui.watermark(surf)
        self.draw_flash(surf)

    def draw_flash(self, surf):
        if self.flash_msg and self.flash_t > 0:
            a = int(255 * min(1, self.flash_t / 0.4))
            img = ui.font("title", 44).render(self.flash_msg, True, BG)
            r = img.get_rect(center=self.flash_pos)
            box = r.inflate(48, 24)
            s = pygame.Surface(box.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (*CORAL, 255), s.get_rect(), border_radius=18)
            s.blit(img, (24, 12))
            s.set_alpha(a)
            surf.blit(s, box)

    def update_common(self, dt):
        if self.flash_t > 0:
            self.flash_t -= dt


# ======================================================================
#  PUENTE DOBLE
# ======================================================================
def _bezier(p0, p1, p2, p3, n):
    t = np.linspace(0, 1, n)[:, None]
    p0, p1, p2, p3 = map(np.array, (p0, p1, p2, p3))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


def _length(pts):
    return float(np.hypot(*np.diff(pts, axis=0).T).sum())


def branch_paths(ratio, fork=(340, 520), join=(1080, 520), rise=230):
    up = _bezier(fork, (fork[0] + 130, fork[1] - rise * 1.33),
                 (join[0] - 130, join[1] - rise * 1.33), join, 400)
    base = up.copy(); base[:, 1] = 2 * fork[1] - base[:, 1]
    Lu = _length(up)
    if ratio <= 1.001:
        return up, base
    u = np.linspace(0, 1, len(base))
    env = np.clip(np.sin(np.pi * (u - 0.12) / 0.76), 0, None) * ((u > 0.12) & (u < 0.88))

    def make(A):
        p = base.copy()
        p[:, 1] += A * env * np.sin(2 * np.pi * 12 * (u - 0.12) / 0.76)
        return p
    lo, hi = 0.0, 400.0
    for _ in range(40):
        mid = (lo + hi) / 2
        if _length(make(mid)) < ratio * Lu:
            lo = mid
        else:
            hi = mid
    return up, make(lo)


def resample(pts, n):
    seg = np.hypot(*np.diff(pts, axis=0).T)
    s = np.concatenate([[0], np.cumsum(seg)])
    t = np.linspace(0, s[-1], n)
    return np.stack([np.interp(t, s, pts[:, 0]), np.interp(t, s, pts[:, 1])], 1)


class BridgeScene(Scene):
    """mode: 'iguales', 'desigual', 'trampa', 'evaporacion'."""

    def __init__(self, mode="iguales", seed=11):
        super().__init__()
        self.mode = mode
        self.seed = seed
        trap = mode in ("trampa", "evaporacion")
        self.has_food = mode != "iguales"
        ratio = 1.0 if mode == "iguales" else 2.0
        evap = 0.0
        self.time_scale = 45.0            # segundos simulados por segundo real
        self.ff_scale = 240.0             # adelantado (trampa)
        self.open_at = 30 * 60 if trap else None
        self.decide_after = (12 if trap else 20) * 60   # tiempo para declarar resultado
        self.model = BridgeModel(n_ants=60 if trap else 100, ratio=ratio, runs=20,
                                 evap=evap, seed=seed, short_closed=trap,
                                 per_length=(mode == "evaporacion"))
        self.titles()
        self.build_controls()
        self.rebuild_geometry()
        self.ff = trap
        self.opened_flash = False
        self.flash_pos = (710, 520)

    def titles(self):
        m = self.mode
        if m == "iguales":
            self.title = "Puente doble · dos ramas iguales"
            self.subtitle = "Nido a la izquierda, zona nueva a la derecha (sin comida)"
        elif m == "desigual":
            self.title = "Puente doble · una rama corta y una larga"
            self.subtitle = "Ahora sí hay comida al otro lado"
        elif m == "trampa":
            self.title = "La trampa · el atajo llega tarde"
            self.subtitle = "Primero solo existe la rama larga; a los 30 minutos se abre la corta"
        else:
            self.title = "El arte de olvidar · la trampa con evaporación"
            self.subtitle = "Versión de computadora: el olor de cada viaje rinde menos en la rama larga"

    def build_controls(self):
        m = self.model
        c = [Slider("hormigas", "Número de hormigas", 10, 500, m.n_ants,
                    lambda v: f"{v:.0f}", 10, lambda v: m.set_n_ants(v)),
             Slider("deposito", "Olor que deja cada una", 0.2, 3.0, m.deposit,
                    lambda v: f"×{v:.1f}", 0.1, lambda v: setattr(m, "deposit", v)),
             Slider("fuerza", "Fuerza del olor", 1.0, 3.0, m.h,
                    lambda v: {1.0: "suave", 2.0: "normal", 3.0: "fuerte"}.get(round(v, 1), f"{v:.1f}"),
                    0.1, lambda v: setattr(m, "h", v))]
        if self.mode in ("desigual",):
            c.append(Slider("largo", "Largo de la rama larga", 1.0, 2.5, m.ratio,
                            lambda v: f"×{v:.1f}", 0.1, self.set_ratio, color=CORAL))
        if self.mode in ("trampa", "evaporacion"):
            c.append(Slider("evap", "Evaporación", 0.0, 0.98, m.evap,
                            lambda v: "nada" if v < 0.005 else f"{v * 100:.0f} %/min", 0.01,
                            lambda v: setattr(m, "evap", v), color=CORAL))
        c.append((Button("reiniciar", "Reiniciar", self.reset),
                  Button("pausa", "Pausa", self.toggle_pause)))
        self.controls = c
        self.panel_bottom = layout_panel(c)

    def set_ratio(self, v):
        self.model.set_ratio(v)
        self.rebuild_geometry()

    def reset(self):
        m = self.model
        m.short_closed = self.mode in ("trampa", "evaporacion")
        m.rng = np.random.default_rng(self.seed + int(m.t * 7) % 1000)
        m.reset()
        self.ff = m.short_closed
        self.opened_flash = False
        self.rebuild_geometry()

    def rebuild_geometry(self):
        m = self.model
        up, lo = branch_paths(m.ratio)
        self.paths = [resample(up, m.ncell[0] + 1), resample(lo, m.ncell[1] + 1)]
        self.fine = [resample(up, 600), resample(lo, int(600 * m.ratio))]

    # ------------------------------------------------------------------
    def update(self, dt):
        self.update_common(dt)
        if self.paused:
            return
        m = self.model
        scale = self.ff_scale if (self.ff and m.short_closed) else self.time_scale
        sim = dt * scale
        nsub = max(1, int(math.ceil(sim / 0.5)))
        for _ in range(nsub):
            m.step(sim / nsub)
            if self.open_at and m.short_closed and m.t >= self.open_at:
                m.open_short()
                self.flash("¡Se abre el atajo!", 3.0)
        m.trim_history(1200)

    # ------------------------------------------------------------------
    def ant_xy(self, b, pos):
        P = self.paths[b]
        i = np.clip(pos, 0, len(P) - 1.001)
        i0 = np.floor(i).astype(int)
        f = (i - i0)[:, None]
        return P[i0] * (1 - f) + P[i0 + 1] * f

    def draw(self, surf):
        ui.background(surf)
        m = self.model
        cols = [CYAN, CORAL]
        ov = pygame.Surface((1340, 900), pygame.SRCALPHA)
        off = np.array([0, 140])
        # ramas base
        for b in range(2):
            pts = [tuple(p - off) for p in self.fine[b]]
            closed = (b == 0 and m.short_closed)
            base = (40, 50, 80) if not closed else (30, 36, 58)
            pygame.draw.lines(ov, base, False, pts, 22 if not closed else 16)
        # tallos y círculos
        fork, join = (340, 520 - 140), (1080, 520 - 140)
        pygame.draw.line(ov, (40, 50, 80), (210, 380), fork, 22)
        pygame.draw.line(ov, (40, 50, 80), join, (1210, 380), 22)
        # olor por celda (corrida 0)
        for b in range(2):
            if b == 0 and m.short_closed:
                continue
            P = self.paths[b] - off
            ph = m.ph[0, b, :m.ncell[b]]
            inten = 1 - np.exp(-ph / 35.0)
            for i in range(m.ncell[b]):
                if inten[i] > 0.02:
                    ui.glow_line(ov, cols[b], P[i], P[i + 1], 3 + 9 * inten[i], 0.25 + 0.75 * inten[i])
        surf.blit(ov, (0, 140))
        if m.short_closed:
            mid = self.fine[0][300]
            pygame.draw.line(surf, CORAL, (mid[0] - 30, mid[1] - 30), (mid[0] + 30, mid[1] + 30), 8)
            pygame.draw.line(surf, CORAL, (mid[0] - 30, mid[1] + 30), (mid[0] + 30, mid[1] - 30), 8)
            text(surf, "cerrada", (mid[0], mid[1] - 44), "bold", 26, CORAL, "midbottom")
        # nido y destino
        pygame.draw.circle(surf, (30, 40, 70), (210, 520), 78)
        pygame.draw.circle(surf, GREY, (210, 520), 78, 3)
        text(surf, "Nido", (210, 520), "title", 34, PAPER, "center")
        dest = "Comida" if self.has_food else "Zona nueva"
        pygame.draw.circle(surf, (30, 40, 70), (1210, 520), 78)
        pygame.draw.circle(surf, GOLD if self.has_food else GREY, (1210, 520), 78, 3)
        text(surf, dest, (1210, 520), "title", 30 if self.has_food else 26, PAPER, "center")
        # hormigas
        st, br, pos = m.state[0], m.branch[0], m.pos[0]
        for b in range(2):
            for kind, col in ((OUT, PAPER), (BACK, GOLD if self.has_food else PAPER)):
                sel = (st == kind) & (br == b)
                if sel.any():
                    xy = self.ant_xy(b, pos[sel])
                    for x, y in xy:
                        pygame.draw.circle(surf, col, (int(x), int(y)), 5)
        # etiquetas de ramas
        ytop = self.fine[0][:, 1].min()
        ybot = self.fine[1][:, 1].max()
        lab0 = "Arriba" if m.ratio <= 1.001 else "Rama corta"
        lab1 = "Abajo" if m.ratio <= 1.001 else f"Rama larga (×{m.ratio:.1f})"
        text(surf, lab0, (710, ytop - 22), "bold", 28, CYAN, "midbottom")
        if ybot + 60 < 835:
            text(surf, lab1, (710, ybot + 22), "bold", 28, CORAL, "midtop")
        else:   # rama muy ondulada: etiqueta a la izquierda, bajo el nido
            text(surf, lab1, (215, 640), "bold", 28, CORAL, "midtop")
        # reloj y reparto
        mins = m.t / 60
        rrect(surf, BG2, pygame.Rect(60, 160, 330, 120), 16)
        text(surf, "Tiempo simulado", (80, 172), "text", 22, GREY)
        text(surf, f"{int(mins):d} min", (80, 200), "mono", 44, PAPER)
        if self.ff and m.short_closed:
            text(surf, "adelantando »", (370, 172), "bold", 22, GOLD, "topright")
        share = m.share(window=180)
        s0 = share[0]
        rrect(surf, BG2, pygame.Rect(1030, 160, 330, 120), 16)
        text(surf, f"Salen por {'arriba' if m.ratio <= 1.001 else 'la corta'}", (1050, 172), "text", 22, GREY)
        text(surf, pct(s0), (1050, 200), "mono", 44, CYAN)
        self.draw_runs(surf, share)
        self.draw_common(surf)
        self.draw_reference(surf)

    def draw_runs(self, surf, share):
        m = self.model
        x0, y0 = 60, 842
        rrect(surf, BG2, pygame.Rect(x0, y0, 1300, 162), 16)
        text(surf, "20 colonias a la vez", (x0 + 20, y0 + 12), "bold", 26, PAPER)
        text(surf, "(la nº 1 es la grande)", (x0 + 290, y0 + 17), "text", 20, GREY)
        tw, gap = 48, 13
        tx = x0 + 40
        decided = (m.t - (self.open_at or 0)) >= self.decide_after and not m.short_closed
        for r in range(m.R):
            rect = pygame.Rect(tx + r * (tw + gap), y0 + 54, tw, 70)
            rrect(surf, (30, 40, 66), rect, 8)
            h0 = int(rect.h * share[r])
            top = pygame.Rect(rect.x, rect.y, rect.w, h0)
            bot = pygame.Rect(rect.x, rect.y + h0, rect.w, rect.h - h0)
            if h0 > 0:
                pygame.draw.rect(surf, CYAN, top, border_top_left_radius=8, border_top_right_radius=8,
                                 border_bottom_left_radius=0 if bot.h else 8, border_bottom_right_radius=0 if bot.h else 8)
            if bot.h > 0:
                pygame.draw.rect(surf, CORAL, bot, border_bottom_left_radius=8, border_bottom_right_radius=8,
                                 border_top_left_radius=0 if h0 else 8, border_top_right_radius=0 if h0 else 8)
            if r == 0:
                pygame.draw.rect(surf, PAPER, rect.inflate(6, 6), 3, border_radius=10)
            text(surf, str(r + 1), (rect.centerx, rect.bottom + 4), "mono", 16, GREY, "midtop")
        n0 = int((share > 0.5).sum())
        a0 = int((share >= 0.65).sum()); a1 = int((share <= 0.35).sum()); und = m.R - a0 - a1
        if decided:
            if self.mode == "trampa":
                msg = f"Cambiaron al atajo: {n0} de 20"
            elif self.mode == "evaporacion":
                msg = (f"Cambiaron al atajo: {n0} de 20  ·  "
                       f"van por la corta: {100 * float(share.mean()):.0f} %")
            elif m.ratio <= 1.001:
                msg = f"Arriba: {a0}  ·  Abajo: {a1}  ·  Sin decidir: {und}"
            else:
                msg = f"Corta: {a0}  ·  Larga: {a1}  ·  Sin decidir: {und}"
            text(surf, msg, (x0 + 1280, y0 + 12), "bold", 24, GOLD, "topright")
        else:
            left = self.decide_after - (m.t - (self.open_at or 0)) if not m.short_closed else None
            text(surf, "esperando a que se decidan…", (x0 + 1280, y0 + 15), "text", 22, GREY, "topright")

    def draw_reference(self, surf):
        y = self.panel_bottom + 6
        if self.mode == "desigual":
            lines = ["Experimento real (Goss et al. 1989):",
                     "rama ×1.4 → eligió la corta en 15 de 18",
                     "rama ×2 → eligió la corta en 14 de 14"]
        elif self.mode == "trampa":
            lines = ["Experimento real (Goss et al. 1989):",
                     "cambiaron al atajo en 2 de 18 ensayos"]
        elif self.mode == "iguales":
            lines = ["En el experimento real, cada rama",
                     "ganaba más o menos la mitad",
                     "de las veces."]
        else:
            lines = ["Sin evaporación: se queda atorada.",
                     "Evaporación media: cambia al atajo.",
                     "Demasiada: no se decide del todo."]
        rrect(surf, BG2, pygame.Rect(1410, y, 450, 40 + 36 * len(lines)), 14)
        for i, l in enumerate(lines):
            text(surf, l, (1430, y + 18 + 36 * i), "bold" if i == 0 else "text", 23,
                 PAPER if i == 0 else GREY)


# ======================================================================
#  AGENTE VIAJERO
# ======================================================================
MAP = pygame.Rect(60, 165, 1300, 806)


class TSPView:
    """Dibuja una colonia sobre un rectángulo."""

    def __init__(self, colony, rect, pad=30):
        self.c = colony
        self.set_rect(rect, pad)
        self.tau_disp = colony.tau.copy()

    def set_rect(self, rect, pad=30):
        self.rect = pygame.Rect(rect)
        xy = self.c.xy
        sx = (self.rect.w - 2 * pad) / 100.0
        sy = (self.rect.h - 2 * pad) / 62.0
        s = min(sx, sy)
        ox = self.rect.x + (self.rect.w - 100 * s) / 2
        oy = self.rect.y + (self.rect.h - 62 * s) / 2
        self.P = np.stack([ox + xy[:, 0] * s, oy + xy[:, 1] * s], 1)
        self.scale = s

    def draw(self, surf, ants=None, frac=0.0, best=True, edge_w=10, city_r=9, cmap=CYAN):
        r = self.rect
        rrect(surf, BG2, r, 18)
        ov = pygame.Surface(r.size, pygame.SRCALPHA)
        P = self.P - np.array([r.x, r.y])
        tau = self.tau_disp
        n = len(P)
        iu = np.triu_indices(n, 1)
        vals = tau[iu]
        mx = vals.max() if vals.size else 1
        if mx <= 0:
            mx = 1
        f = vals / mx
        order = np.argsort(f)
        for k in order:
            if f[k] < 0.05:
                continue
            i, j = iu[0][k], iu[1][k]
            ui.glow_line(ov, cmap, P[i], P[j], 1 + (edge_w - 1) * f[k], f[k] ** 0.8)
        if best and self.c.best_tour is not None:
            t = self.c.best_tour
            pts = [tuple(P[i]) for i in t] + [tuple(P[t[0]])]
            pygame.draw.lines(ov, (*CORAL, 90), True, pts, int(edge_w * 0.9) + 4)
            pygame.draw.lines(ov, (*CORAL, 255), True, pts, 4)
        surf.blit(ov, r.topleft)
        if ants is not None:
            n_ = ants.shape[1]
            pos = frac * n_
            k = int(pos) % n_
            fr = pos - int(pos)
            a = ants[:, k]; b = ants[:, (k + 1) % n_]
            xy = self.P[a] * (1 - fr) + self.P[b] * fr
            for x, y in xy:
                pygame.draw.circle(surf, PAPER, (int(x), int(y)), max(3, city_r // 2))
        for x, y in self.P:
            pygame.draw.circle(surf, BG, (int(x), int(y)), city_r + 3)
            pygame.draw.circle(surf, CYAN if cmap == CYAN else PAPER, (int(x), int(y)), city_r)


class TSPScene(Scene):
    """mode: 'ant_system', 'evaporacion', 'juguemos'."""

    def __init__(self, mode="ant_system", n=30, seed=7):
        super().__init__()
        self.mode = mode
        self.n = n
        self.map_seed = seed
        self.cities = make_cities(n, seed)
        self.colony = Colony(self.cities, "AS", seed=1)
        self.view = TSPView(self.colony, MAP)
        self.bk = tour_length(best_known(self.colony.D, tries=12), self.colony.D)
        self.rps = 2.0            # rondas por segundo
        self.acc = 0.0
        self.ants = None
        self.oneant = None
        self.sweep = None
        if mode == "ant_system":
            self.title = "Hormigas de mentira · el agente viajero"
            self.subtitle = "30 ciudades. Cada hormiga arma una ruta que pasa por todas."
        elif mode == "evaporacion":
            self.title = "El arte de olvidar · evaporación en el mapa"
            self.subtitle = "Misma colonia, distinto olvido"
        else:
            self.title = "¡Juguemos!"
            self.subtitle = "Todas las perillas a la vez"
        self.build_controls()
        self.started = mode != "ant_system"

    def build_controls(self):
        c = self.colony
        def setter(attr):
            return lambda v: setattr(self.colony, attr, v)
        ctr = [Slider("fuerza", "Fuerza del olor", 0.0, 3.0, c.alpha, lambda v: f"{v:.1f}", 0.1, setter("alpha")),
               Slider("distancia", "Peso de la distancia", 0.0, 6.0, c.beta, lambda v: f"{v:.1f}", 0.1, setter("beta")),
               Slider("evap", "Evaporación", 0.0, 0.95, c.evap,
                      lambda v: "nada" if v < 0.005 else f"{v * 100:.0f} % por ronda", 0.01, setter("evap"), color=CORAL),
               Slider("hormigas", "Número de hormigas", 1, 60, c.m, lambda v: f"{v:.0f}", 1,
                      lambda v: setattr(self.colony, "m", int(round(v))))]
        row = (Button("reiniciar", "Reiniciar", self.reset), Button("pausa", "Pausa", self.toggle_pause))
        ctr.append(row)
        if self.mode == "juguemos":
            ctr.append((Button("mapa", "Nuevo mapa", self.new_map, color=CORAL),))
        self.controls = ctr
        self.panel_bottom = layout_panel(ctr)

    def reset(self):
        c = self.colony
        params = dict(alpha=c.alpha, beta=c.beta, evap=c.evap, m=c.m)
        c.rng = np.random.default_rng(np.random.randint(1 << 30))
        c.reset()
        for k, v in params.items():
            setattr(c, k, v)
        self.view.tau_disp = c.tau.copy()
        self.acc = 0.0
        self.ants = None
        self.started = True
        self.oneant = None

    def new_map(self):
        self.map_seed += 1
        c = self.colony
        params = dict(alpha=c.alpha, beta=c.beta, evap=c.evap, m=c.m)
        self.cities = make_cities(self.n, self.map_seed)
        self.colony = Colony(self.cities, "AS", seed=self.map_seed, **params)
        self.view = TSPView(self.colony, MAP)
        self.bk = tour_length(best_known(self.colony.D, tries=8), self.colony.D)
        self.build_controls_keep()
        self.reset()

    def build_controls_keep(self):
        vals = {s.name: s.value for s in self.all_controls() if isinstance(s, Slider)}
        self.build_controls()
        for s in self.all_controls():
            if isinstance(s, Slider) and s.name in vals:
                s.value = vals[s.name]

    # ---- una sola hormiga paso a paso -----------------------------------
    def start_oneant(self, slow_steps=6, step_time=1.6):
        c = self.colony
        start = int(np.argmin(np.hypot(*(c.xy - c.xy.mean(0)).T)))
        self.oneant = dict(tour=[start], phase="think", t=0.0, slow=slow_steps,
                           step_time=step_time, nxt=None, probs=None, done=False)
        self._oneant_think()

    def _oneant_think(self):
        o = self.oneant
        c = self.colony
        p = c.probs_from(o["tour"][-1], o["tour"])
        o["probs"] = p
        o["nxt"] = int(c.rng.choice(len(p), p=p)) if p.sum() > 0 else None
        o["phase"], o["t"] = "think", 0.0

    def update_oneant(self, dt):
        o = self.oneant
        k = len(o["tour"])
        slow = k <= o["slow"]
        think_t = o["step_time"] if slow else 0.06
        move_t = 0.7 if slow else 0.08
        o["t"] += dt
        if o["phase"] == "think" and o["t"] >= think_t:
            o["phase"], o["t"] = "move", 0.0
        elif o["phase"] == "move" and o["t"] >= move_t:
            o["tour"].append(o["nxt"])
            if len(o["tour"]) >= self.n:
                o["phase"], o["done"] = "finished", True
                o["t"] = 0.0
            else:
                self._oneant_think()
        elif o["phase"] == "finished" and o["t"] > 2.0:
            pass

    def draw_oneant(self, surf):
        o = self.oneant
        v = self.view
        P = v.P
        t = o["tour"]
        for a, b in zip(t[:-1], t[1:]):
            pygame.draw.line(surf, PAPER, P[a], P[b], 4)
        if o["phase"] == "finished":
            pygame.draw.line(surf, PAPER, P[t[-1]], P[t[0]], 4)
        cur = t[-1]
        if o["phase"] in ("think", "move") and o["probs"] is not None:
            p = o["probs"]
            top = np.argsort(p)[::-1][:6]
            ov = pygame.Surface((W, H), pygame.SRCALPHA)
            for j in top:
                if p[j] <= 0.005:
                    continue
                ui.glow_line(ov, CYAN, P[cur], P[j], 2 + 22 * p[j], 0.35 + 0.65 * min(1, p[j] * 2.5))
            surf.blit(ov, (0, 0))
            if len(t) <= o["slow"]:
                for j in top[:4]:
                    if p[j] <= 0.02:
                        continue
                    mx, my = (P[cur] + P[j]) / 2
                    text(surf, f"{p[j] * 100:.0f} %", (mx, my - 16), "mono", 24, PAPER, "center")
        # ciudades
        for i, (x, y) in enumerate(P):
            pygame.draw.circle(surf, BG, (int(x), int(y)), 12)
            pygame.draw.circle(surf, GREY if i in t else CYAN, (int(x), int(y)), 9)
        if o["phase"] == "move":
            k = len(t)
            slow = k <= o["slow"]
            f = ui.ease(o["t"] / (0.7 if slow else 0.08))
            xy = P[cur] * (1 - f) + P[o["nxt"]] * f
        else:
            xy = P[cur]
        pygame.draw.circle(surf, CORAL, (int(xy[0]), int(xy[1])), 14)
        pygame.draw.circle(surf, PAPER, (int(xy[0]), int(xy[1])), 14, 3)

    # ---------------------------------------------------------------------
    def update(self, dt):
        self.update_common(dt)
        if self.paused:
            return
        if self.oneant is not None:
            self.update_oneant(dt)
            return
        if not self.started:
            return
        self.acc += dt * self.rps
        while self.acc >= 1.0 or self.ants is None:
            if self.ants is not None:
                self.acc -= 1.0
            self.view.tau_disp = self.colony.tau.copy()
            tours, _ = self.colony.iterate()
            self.ants = tours
            if self.rps > 6:
                break

    def draw(self, surf):
        ui.background(surf)
        if self.oneant is not None:
            rrect(surf, BG2, MAP, 18)
            self.draw_oneant(surf)
            text(surf, "Una sola hormiga: más grueso = más probable", (MAP.x + 24, MAP.bottom - 20),
                 "bold", 26, PAPER, "bottomleft")
        else:
            ants = self.ants if (self.rps <= 4 and self.ants is not None) else None
            ants = ants[:40] if ants is not None else None
            self.view.draw(surf, ants=ants, frac=min(self.acc, 0.999))
            c = self.colony
            if c.it > 0:
                box = pygame.Rect(MAP.x + 20, MAP.y + 18, 420, 92)
                s = pygame.Surface(box.size, pygame.SRCALPHA)
                pygame.draw.rect(s, (*BG, 215), s.get_rect(), border_radius=14)
                surf.blit(s, box)
                text(surf, f"Ronda {c.it}", (box.x + 18, box.y + 10), "mono", 30, PAPER)
                text(surf, "Mejor ruta:", (box.x + 18, box.y + 52), "text", 26, GREY)
                text(surf, f"{c.best_len:.0f}", (box.x + 170, box.y + 47), "mono", 34, CORAL)
            # leyenda
            text(surf, "líneas cian = olor   ·   línea coral = mejor ruta hasta ahora",
                 (MAP.x + 24, MAP.bottom - 16), "text", 22, GREY, "bottomleft")
        self.draw_common(surf)
        self.draw_chart(surf)

    def draw_chart(self, surf):
        c = self.colony
        rect = pygame.Rect(1410, self.panel_bottom + 4, 450, 1000 - self.panel_bottom - 4)
        if rect.h < 150:
            return
        if self.sweep is not None:
            return
        chart(surf, rect, [c.hist_iter, c.hist_best], [mix(CYAN, BG2, 0.35), CORAL],
              labels=["de la ronda", "mejor"], title="Largo de ruta",
              ref=self.bk, ref_label="mejor conocida", xmax=max(60, len(c.hist_best)))


class EvapSweepScene(Scene):
    """Cinco colonias iguales salvo la evaporación; a mitad del camino cambia el mapa (sim 5b)."""
    VALUES = [0.0, 0.02, 0.1, 0.5, 0.9]

    def __init__(self, n=30, seed=7, change_at=80, rounds=170):
        super().__init__()
        self.title = "El arte de olvidar · ¿y si el mapa cambia?"
        self.subtitle = "Cinco colonias iguales; solo cambia cuánto olor se borra por ronda"
        self.cities = make_cities(n, seed)
        r = np.random.default_rng(0)
        self.cities2 = self.cities.copy()
        self.moved = r.choice(n, 8, replace=False)
        self.cities2[self.moved] = r.uniform([4, 4], [96, 58], (8, 2))
        self.change_at = change_at
        self.rounds = rounds
        self.colors = [CORAL, GOLD, PAPER, CYAN, (150, 120, 255)]
        tmp = Colony(self.cities)
        self.bk1 = tour_length(best_known(tmp.D, tries=12), tmp.D)
        tmp2 = Colony(self.cities2)
        self.bk2 = tour_length(best_known(tmp2.D, tries=12), tmp2.D)
        self.rps = 3.0
        self.controls = [(Button("reiniciar", "Reiniciar", self.reset),
                          Button("pausa", "Pausa", self.toggle_pause))]
        layout_panel(self.controls, x=1410, y=900, w=450)
        self.reset(first=True)

    def reset(self, first=False):
        self.cols, self.views = [], []
        w, h = 352, 232
        for i, ev in enumerate(self.VALUES):
            c = Colony(self.cities, "AS", seed=3 + (0 if first else np.random.randint(1000)),
                       evap=ev, beta=2.0)
            self.cols.append(c)
            self.views.append(TSPView(c, pygame.Rect(60 + i * (w + 18), 170, w, h), pad=14))
        self.gap = [[] for _ in self.VALUES]
        self.acc = 0.0
        self.morph = None

    def draw_common(self, surf):
        ui.header(surf, self.title, self.subtitle)
        for c in self.all_controls():
            c.draw(surf)
        text(surf, self.note, (1860, H - 40), "text", 21, GREY, "bottomright")
        ui.watermark(surf)

    def update(self, dt):
        self.update_common(dt)
        if self.morph is not None:
            self.morph += dt / 1.5
            f = ui.ease(min(1.0, self.morph))
            xy = self.cities * (1 - f) + self.cities2 * f
            for v in self.views:
                v.c.xy = xy
                v.set_rect(v.rect, 14)
            if self.morph >= 1.0:
                for v in self.views:
                    v.c.set_cities(self.cities2)
                    v.set_rect(v.rect, 14)
                self.morph = None
            return
        if self.paused or self.cols[0].it >= self.rounds:
            return
        self.acc += dt * self.rps
        while self.acc >= 1 and self.morph is None:
            self.acc -= 1
            bk = self.bk1 if self.cols[0].it < self.change_at else self.bk2
            for i, (c, v) in enumerate(zip(self.cols, self.views)):
                c.iterate()
                v.tau_disp = c.tau.copy()
                self.gap[i].append((c.hist_iter[-1] / bk - 1) * 100)
            if self.cols[0].it == self.change_at:
                self.morph = 0.0
                self.flash("¡Cambia el mapa! 8 ciudades se mueven", 3.0)

    def smooth(self, s, k=6):
        out = []
        for i in range(len(s)):
            seg = s[max(0, i - k + 1):i + 1]
            out.append(sum(seg) / len(seg))
        return out

    def draw(self, surf):
        ui.background(surf)
        for i, (v, ev) in enumerate(zip(self.views, self.VALUES)):
            v.draw(surf, best=False, edge_w=6, city_r=5)
            if self.cols[0].it >= self.change_at or self.morph is not None:
                for j in self.moved:
                    x, y = v.P[j]
                    pygame.draw.circle(surf, CORAL, (int(x), int(y)), 9, 2)
            lab = "sin evaporación" if ev == 0 else f"evaporación {ev * 100:.0f} %"
            text(surf, lab, (v.rect.centerx, v.rect.bottom + 12), "bold", 26, self.colors[i], "midtop")
        rect = pygame.Rect(60, 470, 1800, 410)
        series = [self.smooth(g) for g in self.gap]
        chart(surf, rect, series, self.colors,
              labels=[("0 %" if ev == 0 else f"{ev * 100:.0f} %") for ev in self.VALUES],
              title="Qué tan lejos está de la mejor ruta conocida, en % (más bajo = mejor)",
              ymin=0, ref=0.0, ref_label="la mejor ruta conocida", xmax=self.rounds)
        # marca del cambio
        x0, w = rect.x + 70, rect.w - 94
        xc = x0 + w * self.change_at / (self.rounds - 1)
        pygame.draw.line(surf, CORAL, (xc, rect.y + 46), (xc, rect.bottom - 40), 2)
        text(surf, "cambia el mapa", (xc + 8, rect.y + 50), "bold", 20, CORAL)
        text(surf, f"Ronda {self.cols[0].it} de {self.rounds}", (60, 910), "mono", 32, PAPER)
        text(surf, "Peso de la distancia: 2 · promedio de 6 rondas", (60, 960), "text", 22, GREY)
        self.draw_common(surf)
        self.draw_flash(surf)


class CompareScene(Scene):
    """Ant System vs Ant Colony System vs MAX–MIN (sim 6)."""

    def __init__(self, n=30, seed=7, rounds=300):
        super().__init__()
        self.title = "Hormigas mejoradas · tres versiones, mismo mapa"
        self.subtitle = "Valores publicados: Ant System (1996) · ACS y MAX–MIN (Stützle et al. 2011)"
        self.cities = make_cities(n, seed)
        self.rounds = rounds
        self.names = ["Ant System", "Ant Colony System", "MAX–MIN"]
        self.algos = ["AS", "ACS", "MMAS"]
        self.colors = [PAPER, CYAN, CORAL]
        self.cols = [Colony(self.cities, a, seed=5) for a in self.algos]
        w, h = 586, 340
        self.views = [TSPView(c, pygame.Rect(60 + i * (w + 21), 170, w, h), pad=18)
                      for i, c in enumerate(self.cols)]
        self.bk = tour_length(best_known(self.cols[0].D, tries=12), self.cols[0].D)
        self.rps = 5.0
        self.acc = 0.0
        acs = self.cols[1]
        self.controls = [
            Slider("q0", "Qué tan seguido va a lo seguro", 0.0, 0.98, acs.q0, pct, 0.01,
                   lambda v: setattr(self.cols[1], "q0", v)),
            Slider("phi", "Olor que borra al pasar", 0.0, 0.5, acs.phi, pct, 0.01,
                   lambda v: setattr(self.cols[1], "phi", v)),
            (Button("reiniciar", "Reiniciar", self.reset), Button("pausa", "Pausa", self.toggle_pause))]
        layout_panel(self.controls, x=1300, y=640, w=560)

    def draw_common(self, surf):
        ui.header(surf, self.title, self.subtitle)
        rrect(surf, PANEL, pygame.Rect(1280, 580, 600, 440), 22)
        text(surf, "Perillas de Ant Colony System", (1300, 596), "bold", 22, CYAN, "topleft")
        for c in self.all_controls():
            c.draw(surf)
        text(surf, self.note, (1860, H - 40), "text", 20, GREY, "bottomright")
        ui.watermark(surf)

    def reset(self):
        for c in self.cols:
            q0, phi = c.q0, c.phi
            c.rng = np.random.default_rng(np.random.randint(1 << 30))
            c.reset()
            c.q0, c.phi = q0, phi
        for v in self.views:
            v.tau_disp = v.c.tau.copy()

    def update(self, dt):
        if self.paused or self.cols[0].it >= self.rounds:
            return
        self.acc += dt * self.rps
        while self.acc >= 1:
            self.acc -= 1
            for c, v in zip(self.cols, self.views):
                c.iterate()
                v.tau_disp = c.tau.copy()

    def draw(self, surf):
        ui.background(surf)
        for i, v in enumerate(self.views):
            v.draw(surf, best=True, edge_w=7, city_r=6)
            c = v.c
            text(surf, self.names[i], (v.rect.x + 4, v.rect.bottom + 10), "bold", 28, self.colors[i])
            if c.it:
                text(surf, f"mejor: {c.best_len:.0f}", (v.rect.right - 4, v.rect.bottom + 12),
                     "mono", 26, PAPER, "topright")
        rect = pygame.Rect(60, 570, 1200, 400)
        chart(surf, rect, [c.hist_best for c in self.cols], self.colors, labels=self.names,
              title="Mejor ruta hasta ahora (más bajo = mejor)", ref=self.bk,
              ref_label="mejor ruta conocida", xmax=self.rounds)
        text(surf, f"Ronda {self.cols[0].it} de {self.rounds}", (1300, 950), "mono", 30, PAPER)
        self.draw_common(surf)


class TwoOptScene(Scene):
    """Búsqueda local: destorcer cruces (sim 6b)."""
    note = "Ejemplo simplificado; ACS usó una versión restringida de 3-opt."

    def __init__(self, n=30, seed=7):
        super().__init__()
        self.title = "La peinada · destorcer cruces"
        self.subtitle = "Búsqueda local: si dos tramos se cruzan, se reacomodan y la ruta se acorta"
        self.cities = make_cities(n, seed)
        self.colony = Colony(self.cities, "AS", seed=0)
        self.view = TSPView(self.colony, MAP)
        self.D = self.colony.D
        self.controls = [(Button("destorcer", "Destorcer un cruce", self.fix_one, color=CORAL),),
                         (Button("reiniciar", "Ruta nueva", self.reset),)]
        self.panel_bottom = layout_panel(self.controls)
        self.anim = None
        self.reset()

    def reset(self):
        rng = np.random.default_rng(np.random.randint(1 << 30))
        # ruta "de hormiga apurada": vecino más cercano con algo de azar
        n = len(self.D)
        while True:
            t = [int(rng.integers(n))]
            left = set(range(n)) - set(t)
            while left:
                c = t[-1]
                cand = sorted(left, key=lambda j: self.D[c, j])[:3]
                nx = cand[0] if rng.random() < 0.6 else cand[int(rng.integers(len(cand)))]
                t.append(nx); left.remove(nx)
            self.tour = np.array(t)
            if len(self.crossings()) >= 4:
                break
        self.start_len = tour_length(self.tour, self.D)
        self.fixed = 0
        self.anim = None

    def crossings(self):
        P = self.view.P
        t = self.tour; n = len(t)
        out = []
        def ccw(a, b, c):
            return (c[1] - a[1]) * (b[0] - a[0]) > (b[1] - a[1]) * (c[0] - a[0])
        for i in range(n):
            for j in range(i + 2, n):
                if i == 0 and j == n - 1:
                    continue
                a, b = P[t[i]], P[t[(i + 1) % n]]
                c, d = P[t[j]], P[t[(j + 1) % n]]
                if ccw(a, c, d) != ccw(b, c, d) and ccw(a, b, c) != ccw(a, b, d):
                    gain = self.D[t[i], t[i + 1]] + self.D[t[j], t[(j + 1) % n]] - \
                        self.D[t[i], t[j]] - self.D[t[i + 1], t[(j + 1) % n]]
                    out.append((gain, i, j))
        out.sort(reverse=True)
        return out

    def fix_one(self):
        if self.anim is not None:
            return
        cr = self.crossings()
        if not cr:
            self.flash("¡Ya no hay cruces!", 2.5)
            return
        _, i, j = cr[0]
        self.anim = dict(i=i, j=j, t=0.0)

    def update(self, dt):
        self.update_common(dt)
        if self.anim is None or self.paused:
            return
        a = self.anim
        a["t"] += dt
        if a["t"] >= 2.0:
            i, j = a["i"], a["j"]
            self.tour[i + 1:j + 1] = self.tour[i + 1:j + 1][::-1].copy()
            self.fixed += 1
            self.anim = None

    def draw(self, surf):
        ui.background(surf)
        rrect(surf, BG2, MAP, 18)
        P = self.view.P
        t = self.tour; n = len(t)
        hi = set()
        if self.anim:
            i, j = self.anim["i"], self.anim["j"]
            hi = {i, j}
        cross_edges = set()
        for _, i, j in self.crossings():
            cross_edges |= {i, j}
        for k in range(n):
            a, b = P[t[k]], P[t[(k + 1) % n]]
            if k in hi:
                ph = self.anim["t"]
                if ph < 1.0:
                    blink = 0.5 + 0.5 * math.sin(ph * 18)
                    pygame.draw.line(surf, mix(CORAL, PAPER, blink * 0.4), a, b, 9)
                continue
            col = CORAL if k in cross_edges else CYAN
            pygame.draw.line(surf, col, a, b, 5 if k in cross_edges else 4)
        if self.anim and self.anim["t"] >= 1.0:
            f = ui.ease((self.anim["t"] - 1.0) / 0.8)
            i, j = self.anim["i"], self.anim["j"]
            A, B, C, D = P[t[i]], P[t[i + 1]], P[t[j]], P[t[(j + 1) % n]]
            # tramos nuevos A–C y B–D aparecen
            pygame.draw.line(surf, mix(BG2, GOLD, f), A, A + (C - A) * f, 8)
            pygame.draw.line(surf, mix(BG2, GOLD, f), D, D + (B - D) * f, 8)
            if f < 1:
                pygame.draw.line(surf, mix(CORAL, BG2, f), A, B, 6)
                pygame.draw.line(surf, mix(CORAL, BG2, f), C, D, 6)
        for x, y in P:
            pygame.draw.circle(surf, BG, (int(x), int(y)), 12)
            pygame.draw.circle(surf, PAPER, (int(x), int(y)), 9)
        self.draw_common(surf)
        L = tour_length(self.tour, self.D)
        y = self.panel_bottom + 10
        rrect(surf, BG2, pygame.Rect(1410, y, 450, 330), 16)
        text(surf, "Largo de la ruta", (1430, y + 20), "text", 26, GREY)
        text(surf, f"{L:.0f}", (1430, y + 56), "mono", 80, GOLD)
        drop = (1 - L / self.start_len) * 100
        text(surf, f"empezó en {self.start_len:.0f}", (1430, y + 160), "text", 26, GREY)
        text(surf, f"{drop:.0f} % más corta", (1430, y + 196), "bold", 30, CYAN)
        ncr = len(self.crossings())
        text(surf, f"Cruces que quedan: {ncr}", (1430, y + 250), "bold", 28, CORAL if ncr else CYAN)
        text(surf, "coral = tramos que se cruzan", (MAP.x + 24, MAP.bottom - 16), "text", 22, GREY, "bottomleft")


def make_scene(key):
    return {
        "sim1": lambda: BridgeScene("iguales"),
        "sim2": lambda: BridgeScene("desigual"),
        "sim3": lambda: BridgeScene("trampa"),
        "sim4": lambda: TSPScene("ant_system"),
        "sim5a": lambda: BridgeScene("evaporacion"),
        "sim5b": lambda: EvapSweepScene(),
        "sim6": lambda: CompareScene(),
        "sim6b": lambda: TwoOptScene(),
        "juguemos": lambda: TSPScene("juguemos"),
    }[key]()


SCENE_KEYS = ["sim1", "sim2", "sim3", "sim4", "sim5a", "sim5b", "sim6", "sim6b", "juguemos"]
