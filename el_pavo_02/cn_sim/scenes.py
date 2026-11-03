"""Escenas del EP02. Cada escena avanza sola en el tiempo: update(dt) y draw(surf).

Todas las cifras que se ven salen del cálculo de los módulos de modelo
(fabrica, colas, ...); aquí solo se dibujan.
"""
import math
import numpy as np
import pygame

from . import ui
from .ui import (W, H, BG, BG2, PANEL, CYAN, CORAL, PAPER, GREY, DIM, GOLD,
                 text, text_a, rrect, mix, fade, prog, card, pill, Axes,
                 fmt_pct, fmt_num, fmt_int)

PANEL_RECT = pygame.Rect(1385, 150, 500, 830)


class Scene:
    title = ""
    subtitle = ""
    metodo = ""             # «Método: …» siempre visible
    simulados = False       # muestra la etiqueta «Datos simulados»
    credito = None          # crédito fijo de datos, si aplica
    duracion = 60.0

    def __init__(self):
        self.t = 0.0
        self.paused = False

    def reset(self):
        self.t = 0.0

    def toggle_pause(self):
        self.paused = not self.paused

    def update(self, dt):
        if not self.paused:
            self.t = min(self.t + dt, self.duracion + 5)

    def draw(self, surf):
        ui.background(surf)
        self.draw_scene(surf, self.t)
        self.draw_common(surf)

    def draw_scene(self, surf, t):
        pass

    def draw_common(self, surf):
        ui.header(surf, self.title, self.subtitle)
        if self.simulados:
            pill(surf, "Datos simulados", (W - 36, 40), CORAL, 26, "topright", fill=True)
        ui.watermark(surf)
        y = H - 58
        if self.credito:
            text(surf, self.credito, (W - 36, y - 34), "bold", 22, PAPER, "midright")
        if self.metodo:
            text(surf, self.metodo, (W - 36, y), "text", 22, GREY, "midright")

    def panel(self, surf):
        rrect(surf, PANEL, PANEL_RECT, 22)


def _pct_corto(v):
    """Porcentaje sin decimales, salvo que redondear lo lleve a 100 %."""
    s = f"{v * 100:.0f}"
    if s == "100" and v < 1:
        s = f"{v * 100:.1f}"
    return f"{s} %"


def _bajar(n_pts, maximo=400):
    """Índices para dibujar como mucho `maximo` puntos de una curva."""
    paso = max(1, n_pts // maximo)
    idx = np.arange(0, n_pts, paso)
    if idx[-1] != n_pts - 1:
        idx = np.append(idx, n_pts - 1)
    return idx


# ======================================================================
#  S4 · La fábrica de estrategias ganadoras (Bailey et al. 2014, 2017)
# ======================================================================
class FabricaScene(Scene):
    title = "La fábrica de estrategias ganadoras"
    subtitle = "Cientos de reglas sobre un precio que, por construcción, nadie puede predecir"
    metodo = "Método: Bailey et al. 2014, 2017 · Harvey, Liu y Zhu 2016"
    simulados = True
    duracion = 58.0

    # guion (segundos)
    T_PRECIO = (1.0, 7.0)
    T_FABRICA = (8.0, 20.0)
    T_CAMPEONA = 21.0
    T_FUERA = (26.0, 33.0)
    T_COMIS = (35.0, 39.0)
    T_PBO = (41.0, 48.0)
    T_MUNDOS = 50.0

    def __init__(self, semilla=28):
        super().__init__()
        from .fabrica import Fabrica, muchos_mundos, N_DIAS, COMISION
        self.f = f = Fabrica(semilla)
        self.mundos = muchos_mundos(100)
        self.N = len(f.reglas)
        self.n_dias = N_DIAS
        self.comision = COMISION
        m = f.mitad
        c = f.campeona
        # valor de 100 invertidos
        self.v_in = 100 * (1 + f.eq_in)
        self.v_out = self.v_in[-1] * (1 + f.eq_out)
        self.v_out_c = self.v_in[-1] * (1 + f.eq_out_com)
        self.todas = 100 * (1 + f.eq_todas_in)               # m x N
        top = max(self.v_in.max(), self.v_out.max(), self.v_out_c.max(),
                  np.percentile(self.todas.max(0), 99))
        self.ax = Axes((150, 540, 1180, 400), 0, N_DIAS, 0, math.ceil(top / 200) * 200)
        self.ax_p = Axes((150, 190, 1180, 200), 0, N_DIAS, f.p.min() * 0.9, f.p.max() * 1.05)
        self.idx_in = _bajar(m, 300)
        self.idx_out = _bajar(N_DIAS - m, 300)
        # orden aleatorio fijo para «fabricar» las reglas; la campeona se pinta al final
        rng = np.random.default_rng(5)
        self.orden = [j for j in rng.permutation(self.N) if j != c]
        self.capa = None
        self.pintadas = 0
        self.t_in = f.t_in

    def reset(self):
        super().reset()
        self.capa = None
        self.pintadas = 0

    # -- capas ---------------------------------------------------------
    def _pintar_reglas(self, hasta):
        if self.capa is None:
            self.capa = pygame.Surface((W, H), pygame.SRCALPHA)
            self.pintadas = 0
        m = self.f.mitad
        xs = self.idx_in
        while self.pintadas < hasta and self.pintadas < len(self.orden):
            j = self.orden[self.pintadas]
            pts = self.ax.pxs(xs, self.todas[xs, j])
            col = (*GOLD, 140) if self.t_in[j] > 2 else (*GREY, 60)
            pygame.draw.lines(self.capa, col, False, pts.tolist(), 1)
            self.pintadas += 1

    # -- dibujo --------------------------------------------------------
    def draw_scene(self, surf, t):
        f = self.f
        m = f.mitad
        ap = fade(t, 0.3)
        # precio sintético
        p_ = prog(t, *self.T_PRECIO)
        self.ax_p.frame(surf, yticks=self._ticks(self.ax_p.y0, self.ax_p.y1, 4), fmt=lambda v: f"{v:.0f}",
                        xticks=[0, 365, 730, 1095, 1460, 1825], xfmt=lambda v: f"año {int(v // 365)}",
                        ylabel="Precio simulado", a=ap, grid=True)
        n = int(p_ * self.n_dias)
        idx = _bajar(self.n_dias, 600)
        idx = idx[idx < max(n, 2)]
        if len(idx) >= 2:
            self.ax_p.line(surf, idx, f.p[idx], PAPER, 2)
        # división dentro / fuera
        a_div = fade(t, self.T_PRECIO[1])
        if a_div > 0.01:
            x, _ = self.ax.px(m, 0)
            col = mix(BG, GREY, a_div)
            for yy in range(195, 945, 18):
                pygame.draw.line(surf, col, (x, yy), (x, yy + 9), 2)
            text_a(surf, "← aquí se elige la campeona", (x - 16, 462), "bold", 24, CYAN, "midright", a_div)
            text_a(surf, "datos que nunca vio →", (x + 16, 462), "bold", 24, CORAL, "midleft", a_div)

        # ejes del valor
        a_ax = fade(t, self.T_FABRICA[0] - 0.6)
        self.ax.frame(surf, yticks=self._ticks(0, self.ax.y1, 5), fmt=lambda v: f"{v:.0f}",
                      ylabel="Valor de 100 invertidos con cada regla", a=a_ax)
        # fábrica de reglas
        pf = prog(t, *self.T_FABRICA)
        hechas = int(round(pf * (self.N - 1)))
        if t >= self.T_FABRICA[0]:
            self._pintar_reglas(hechas)
            surf.blit(self.capa, (0, 0))
        # campeona
        a_c = fade(t, self.T_CAMPEONA)
        if a_c > 0.01:
            pts = self.ax.line(surf, self.idx_in, self.v_in[self.idx_in], CYAN, 5)
            ex, ey = pts[-1]
            pygame.draw.circle(surf, CYAN, (int(ex), int(ey)), 9)
        # fuera de muestra
        po = prog(t, *self.T_FUERA)
        xs_out = m + self.idx_out
        if po > 0:
            k = max(2, int(po * len(self.idx_out)))
            self.ax.line(surf, xs_out[:k], self.v_out[self.idx_out[:k]], CORAL, 5)
        pc = prog(t, *self.T_COMIS)
        if pc > 0:
            k = max(2, int(pc * len(self.idx_out)))
            self.ax.line(surf, xs_out[:k], self.v_out_c[self.idx_out[:k]], GOLD, 3)
        self.draw_panel(surf, t, hechas)

    def _ticks(self, lo, hi, n):
        span = hi - lo
        paso = 10 ** math.floor(math.log10(span / n))
        for mult in (1, 2, 2.5, 5, 10):
            if span / (paso * mult) <= n:
                paso *= mult
                break
        v = math.ceil(lo / paso) * paso
        out = []
        while v <= hi + 1e-9:
            out.append(v)
            v += paso
        return out

    def draw_panel(self, surf, t, hechas):
        f = self.f
        c = f.campeona
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, self.T_FABRICA[0] - 0.4)
        if t < self.T_PBO[0] - 0.5:
            # contador de reglas
            hechas_tot = hechas + (1 if t >= self.T_CAMPEONA else 0)
            vistas = self.orden[:hechas] + ([c] if t >= self.T_CAMPEONA else [])
            t2 = int((self.t_in[vistas] > 2).sum()) if vistas else 0
            t3 = int((self.t_in[vistas] > 3).sum()) if vistas else 0
            text_a(surf, "Reglas probadas", (x, 176), "text", 24, GREY, a=a)
            text_a(surf, f"{fmt_int(hechas_tot)} de {self.N}", (x, 204), "title", 52, PAPER, a=a)
            text_a(surf, "Cruces de promedio rápido contra lento", (x, 270), "text", 21, GREY, a=a)
            text_a(surf, "Pasan la prueba t > 2", (x, 318), "text", 24, GREY, a=a)
            text_a(surf, f"{t2}", (x + w, 312), "title", 40, GOLD, "topright", a=a)
            text_a(surf, "Pasan t > 3 (umbral de Harvey)", (x, 368), "text", 24, GREY, a=a)
            text_a(surf, f"{t3}", (x + w, 362), "title", 40, GOLD, "topright", a=a)
            text_a(surf, "Bailey et al.: con 5 años de datos,", (x, 424), "text", 21, GREY, a=a)
            text_a(surf, "no más de unas 45 configuraciones.", (x, 452), "text", 21, GREY, a=a)
            tipo, fr, le = f.reglas[c]
            nombre = ("simple" if tipo == "S" else "exponencial")
            card(surf, (x, 500, w, 140), "Campeona, en los datos donde se eligió",
                 fmt_pct(f.ganancia_in, 0), CYAN,
                 f"Sharpe {fmt_num(f.sr_in[c])} · cruce {fr}/{le} días", a=fade(t, self.T_CAMPEONA + 0.8))
            card(surf, (x, 656, w, 140), "La misma, en los datos que nunca vio",
                 fmt_pct(f.ganancia_out, 1), CORAL, f"Sharpe {fmt_num(f.sr_out[c])}",
                 a=fade(t, self.T_FUERA[1] - 0.4))
            card(surf, (x, 812, w, 140), f"Con comisión de {self.comision * 100:.1f} % por operación",
                 fmt_pct(f.ganancia_out_com, 1), GOLD,
                 f"Sharpe {fmt_num(f.sr_out_com[c])} · {f.n_cambios_out} operaciones",
                 a=fade(t, self.T_COMIS[1] - 0.3))
        else:
            self.draw_pbo(surf, t, x, w)

    def draw_pbo(self, surf, t, x, w):
        f = self.f
        a = fade(t, self.T_PBO[0] - 0.5)
        text_a(surf, "Probabilidad de sobreajuste", (x, 176), "bold", 27, PAPER, a=a)
        text_a(surf, "Se parte la historia en 16 trozos y se", (x, 214), "text", 21, GREY, a=a)
        text_a(surf, f"repite la elección {fmt_int(len(f.logits))} veces.", (x, 240), "text", 21, GREY, a=a)
        # histograma de logits
        lg = f.logits
        bins = np.linspace(-5, 5, 21)          # el 0 cae justo en un borde
        cnt, _ = np.histogram(np.clip(lg, -4.99, 4.99), bins)
        pv = prog(t, self.T_PBO[0], self.T_PBO[1] - 2)
        box = pygame.Rect(x, 290, w, 250)
        rrect(surf, BG2, box.inflate(0, 50).move(0, 10), 14)
        mx = cnt.max()
        bw = box.w / len(cnt)
        for i, cn in enumerate(cnt):
            h = (box.h - 20) * cn / mx * pv
            col = CORAL if bins[i + 1] <= 0 else CYAN
            r = pygame.Rect(box.x + i * bw + 2, box.bottom - h, bw - 4, h)
            pygame.draw.rect(surf, mix(BG2, col, a), r)
        x0 = box.x + box.w / 2
        pygame.draw.line(surf, mix(BG2, PAPER, a), (x0, box.y), (x0, box.bottom), 2)
        text_a(surf, "peor que la mediana", (box.x + 6, box.bottom + 8), "text", 19, CORAL, a=a)
        text_a(surf, "mejor", (box.right - 6, box.bottom + 8), "text", 19, CYAN, "topright", a=a)
        a2 = fade(t, self.T_PBO[1] - 1.5)
        card(surf, (x, 590, w, 150), "La campeona cae abajo de la mediana",
             f"{f.pbo * 100:.0f} % de las veces", CORAL, "PBO, validación cruzada CSCV", a=a2)
        mu = self.mundos
        a3 = fade(t, self.T_MUNDOS)
        card(surf, (x, 756, w, 196), f"Repetido en {mu['n']} precios simulados",
             f"{fmt_num(mu['sharpe_dentro'])} → {fmt_num(mu['sharpe_fuera'])}", GOLD,
             None, a=a3)
        text_a(surf, "Sharpe promedio de la campeona:", (x + 26, 860), "text", 21, PAPER, a=a3)
        text_a(surf, "donde se eligió → donde no", (x + 26, 888), "text", 21, PAPER, a=a3)
        text_a(surf, f"Con comisión: {fmt_num(mu['sharpe_fuera_com'])}", (x + 26, 916), "text", 21, PAPER, a=a3)


# ======================================================================
#  S2 · ¿Cuánto pesa el peor día? (Taleb 2020, Tabla 3.3; Alstott et al. 2014)
# ======================================================================
class ColasScene(Scene):
    title = "¿Cuánto pesa el peor día?"
    subtitle = "Diez años de rendimientos diarios con colas gordas, contra la campana de Gauss"
    metodo = "Método: Taleb 2020 (Tabla 3.3) · Alstott et al. 2014 (powerlaw)"
    simulados = True
    duracion = 58.0

    T_SERIE = (1.0, 19.0)
    T_LOG = (21.0, 23.0)
    T_CONTEO = 25.0
    T_PEOR = 32.0
    T_MUCHAS = 41.0
    T_COLA = 48.0

    def __init__(self, semilla=2026):
        super().__init__()
        from .colas import Colas, muchas_series, UMBRAL
        self.c = c = Colas(semilla)
        self.mu = muchas_series(100)
        self.umbral = UMBRAL
        r = c.r
        self.N = len(r)
        lim = math.ceil(np.abs(r).max() * 10 + 0.5) / 10
        self.lim = lim
        self.ax_s = Axes((150, 190, 1180, 190), 0, self.N, -lim, lim)
        self.bins = np.arange(-lim, lim + 1e-9, 0.01)
        self.bw = 0.01
        cnt_tot, _ = np.histogram(r, self.bins)
        self.ymax_lin = float(cnt_tot.max()) * 1.12
        self.ax_h = Axes((150, 470, 1180, 420), -lim, lim, 0, self.ymax_lin)
        self.ax_hl = Axes((150, 470, 1180, 420), -lim, lim, 0.3, self.ymax_lin * 3, logy=True)
        self.capa = None
        self.pintados = 0
        self.cola = 3 * c.sd_muestral          # colas pintadas en coral: más de 3 desviaciones

    def reset(self):
        super().reset()
        self.capa = None
        self.pintados = 0

    def _pintar_dias(self, hasta):
        if self.capa is None:
            self.capa = pygame.Surface((W, H), pygame.SRCALPHA)
            self.pintados = 0
        r = self.c.r
        _, y0 = self.ax_s.px(0, 0)
        while self.pintados < hasta:
            i = self.pintados
            x, y = self.ax_s.px(i, r[i])
            if r[i] <= self.umbral:
                col = (*CORAL, 255)
            elif abs(r[i]) > self.cola:
                col = (*CORAL, 150)
            else:
                col = (*PAPER, 70)
            pygame.draw.line(self.capa, col, (x, y0), (x, y), 1 if r[i] > self.umbral else 3)
            self.pintados += 1

    def _histo(self, surf, ax, n, a, log):
        r = self.c.r[:n]
        cnt, _ = np.histogram(r, self.bins)
        ticks = ([1, 10, 100, 1000] if log else self._ticks_lin())
        fmt = (lambda v: f"{v:,.0f}".replace(",", " "))
        ax.frame(surf, yticks=[v for v in ticks if v <= ax.y1], fmt=fmt,
                 xticks=[v / 10 for v in range(int(-self.lim * 10), int(self.lim * 10) + 1, 1)],
                 xfmt=lambda v: f"{v * 100:+.0f} %".replace("-", "−").replace("+0 %", "0 %"),
                 ylabel="Días en cada cajón de 1 %", a=a)
        for i, cn in enumerate(cnt):
            if cn <= 0:
                continue
            xa, _ = ax.px(self.bins[i], ax.y0)
            xb, _ = ax.px(self.bins[i + 1], ax.y0)
            _, yt = ax.px(0, max(cn, ax.y0 if log else 0))
            yb = ax.rect.bottom
            centro = (self.bins[i] + self.bins[i + 1]) / 2
            col = CORAL if abs(centro) > self.cola else CYAN
            pygame.draw.rect(surf, mix(BG, col, a * (0.95 if col == CORAL else 0.75)),
                             pygame.Rect(xa + 1, yt, max(1, xb - xa - 2), yb - yt))
        # campana con la misma media y desviación de la serie
        if n > 30:
            sd = float(r.std()) if n > 100 else self.c.sd_muestral
            xs = np.linspace(-self.lim, self.lim, 600)
            ys = n * self.bw * np.exp(-0.5 * (xs / sd) ** 2) / (sd * math.sqrt(2 * math.pi))
            keep = ys >= ax.y0 if log else np.ones_like(ys, bool)
            pts = ax.pxs(xs[keep], ys[keep])
            if len(pts) > 2:
                pygame.draw.lines(surf, mix(BG, PAPER, a), False, pts.tolist(), 3)

    def _ticks_lin(self):
        paso = 100 if self.ymax_lin < 900 else 200
        return list(range(0, int(self.ymax_lin) + 1, paso))

    def draw_scene(self, surf, t):
        c = self.c
        a0 = fade(t, 0.3)
        n = max(2, int(prog(t, *self.T_SERIE) * self.N))
        # serie diaria
        yt = [-0.2, 0, 0.2]
        self.ax_s.frame(surf, yticks=yt, fmt=lambda v: f"{v * 100:+.0f} %".replace("-", "−").replace("+0 %", "0 %"),
                        xticks=[i * 365 for i in range(0, 11, 2)], xfmt=lambda v: f"año {int(v // 365)}",
                        ylabel="Rendimiento de cada día", a=a0)
        _, yu = self.ax_s.px(0, self.umbral)
        for xx in range(self.ax_s.rect.x, self.ax_s.rect.right, 16):
            pygame.draw.line(surf, mix(BG, CORAL, 0.6 * a0), (xx, yu), (xx + 8, yu), 1)
        self._pintar_dias(n)
        surf.blit(self.capa, (0, 0))
        # histograma: lineal y luego logarítmico
        k = prog(t, *self.T_LOG)
        if k < 1:
            self._histo(surf, self.ax_h, n, a0 * (1 - k), False)
        if k > 0:
            capa = pygame.Surface((W, H), pygame.SRCALPHA)
            self._histo(capa, self.ax_hl, n, 1.0, True)
            capa.set_alpha(int(255 * k))
            surf.blit(capa, (0, 0))
            pill(surf, "Escala logarítmica: cada raya, 10 veces más días",
                 (self.ax_h.rect.right, self.ax_h.rect.y - 40), GREY, 21, "topright")
        # leyenda
        lx, ly = self.ax_h.rect.x + 20, self.ax_h.rect.y + 6
        if k < 0.5:
            ly = self.ax_h.rect.y + 6
        pygame.draw.line(surf, mix(BG, PAPER, a0), (lx, ly + 12), (lx + 34, ly + 12), 3)
        text_a(surf, "campana de Gauss", (lx + 44, ly), "text", 21, PAPER, a=a0)
        pygame.draw.rect(surf, mix(BG, CORAL, a0), pygame.Rect(lx, ly + 34, 34, 18))
        text_a(surf, "colas: más de 3 desviaciones", (lx + 44, ly + 30), "text", 21, PAPER, a=a0)
        # el peor día
        ap = fade(t, self.T_PEOR)
        if ap > 0.01:
            i = c.i_peor4
            v = c.r[i]
            x, y = self.ax_s.px(i, v)
            pygame.draw.circle(surf, mix(BG, GOLD, ap), (int(x), int(y)), 12, 3)
            ax = self.ax_hl if k >= 0.5 else self.ax_h
            xh, yh = ax.px(v, ax.y0 if ax.logy else 0)
            pygame.draw.polygon(surf, mix(BG, GOLD, ap),
                                [(xh, yh - 70), (xh - 12, yh - 96), (xh + 12, yh - 96)])
            text_a(surf, f"peor día: {fmt_pct(v, 0)}", (xh, yh - 104), "bold", 22, GOLD, "midbottom", ap)
        self.draw_panel(surf, t, n)

    def draw_panel(self, surf, t, n):
        c, mu = self.c, self.mu
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, 0.5)
        text_a(surf, "Días simulados", (x, 176), "text", 24, GREY, a=a)
        text_a(surf, f"{fmt_int(n)} de {fmt_int(self.N)}", (x, 204), "title", 52, PAPER, a=a)
        text_a(surf, f"Días independientes · volatilidad diaria {c.sd_muestral * 100:.1f} %",
               (x, 270), "text", 19, GREY, a=a)
        # conteo de −20 %
        a1 = fade(t, self.T_CONTEO)
        if a1 > 0.01:
            r = pygame.Rect(x, 310, w, 170)
            s = pygame.Surface(r.size, pygame.SRCALPHA)
            pygame.draw.rect(s, (*BG2, 255), s.get_rect(), border_radius=16)
            pygame.draw.rect(s, (*CORAL, 255), pygame.Rect(0, 0, 8, r.h), border_top_left_radius=16,
                             border_bottom_left_radius=16)
            text(s, "Días de −20 % o peor", (26, 14), "text", 23, GREY)
            text(s, "Según la campana", (26, 56), "text", 24, PAPER)
            text(s, f"{c.esperados_campana:.3f}", (r.w - 24, 50), "title", 36, PAPER, "topright")
            text(s, "En la serie", (26, 104), "text", 24, PAPER)
            text(s, f"{c.observados}", (r.w - 24, 96), "title", 40, CORAL, "topright")
            anios = 1 / (c.p_umbral_campana * 365)
            text(s, f"La campana: uno cada {fmt_int(round(anios, -2))} años", (26, r.h - 12), "text", 19, GREY,
                 "bottomleft")
            s.set_alpha(int(255 * a1))
            surf.blit(s, r)
        card(surf, (x, 496, w, 140), "Parte de la curtosis del peor día",
             f"{c.mq * 100:.0f} %", GOLD,
             f"Campana: {c.mq_campana * 100:.1f} % · Taleb, S&P 500: 79 %",
             a=fade(t, self.T_PEOR + 0.8))
        card(surf, (x, 652, w, 140), f"El peor día, en {mu['n']} series simuladas",
             f"de {_pct_corto(mu['min'])} a {_pct_corto(mu['max'])}", GOLD,
             f"Mediana {mu['p50'] * 100:.0f} % · cambia con la muestra", a=fade(t, self.T_MUCHAS))
        card(surf, (x, 808, w, 150), "Exponente de cola de las pérdidas",
             fmt_num(c.alfa_cola, 1), CYAN,
             f"Real: {c.gl}. Menor que 4: curtosis infinita", a=fade(t, self.T_COLA))




# ======================================================================
#  S3 · ¿Camina como borracho? (Lo y MacKinlay 1988; Bariviera 2017)
# ======================================================================
class PaseoScene(Scene):
    title = "¿Camina como borracho?"
    subtitle = "Una serie al azar: la dirección no tiene memoria, el tamaño de los saltos sí"
    metodo = ("Método: ratio de varianza de Lo y MacKinlay 1988 (paquete arch) · "
              "Hurst por DFA en ventanas de 500 días, como Bariviera 2017")
    simulados = True
    duracion = 56.0

    T_SERIE = (1.0, 10.0)
    T_HURST = (12.0, 26.0)
    T_EXPLICA = 13.0
    T_VR_R = 27.0
    T_VR_A = 32.0
    T_VENT = 37.0
    T_H = 42.0
    T_MUCHAS = 47.0

    def __init__(self, semilla=2028):
        super().__init__()
        from .paseo import Paseo, muchas_series, VENTANA
        self.p = p = Paseo(semilla)
        self.mu = muchas_series(100)
        self.N = len(p.r)
        self.ventana = VENTANA
        lim = float(np.abs(p.r).max()) * 1.05
        self.ax_r = Axes((150, 200, 1180, 150), 0, self.N, -lim, lim)
        self.ax_a = Axes((150, 420, 1180, 110), 0, self.N, 0, lim)
        self.ax_h = Axes((150, 610, 1180, 300), 0, self.N, 0.25, 1.0)
        self.capa = None

    def reset(self):
        super().reset()

    def _capa(self):
        if self.capa is not None:
            return self.capa
        c = pygame.Surface((W, H), pygame.SRCALPHA)
        p = self.p
        _, y0 = self.ax_r.px(0, 0)
        for i, v in enumerate(p.r):
            x, y = self.ax_r.px(i + 0.5, v)
            pygame.draw.line(c, (*CYAN, 170), (x, y0), (x, y), 1)
        _, yb = self.ax_a.px(0, 0)
        for i, v in enumerate(p.a):
            x, y = self.ax_a.px(i + 0.5, v)
            pygame.draw.line(c, (*CORAL, 190), (x, yb), (x, y), 1)
        self.capa = c
        return c

    def draw_scene(self, surf, t):
        p = self.p
        a0 = fade(t, 0.3)
        k = prog(t, *self.T_SERIE)
        n = max(2, int(k * self.N))
        pct = lambda v: f"{v * 100:+.0f} %".replace("-", "−").replace("+0 %", "0 %")
        xt = [i * 365 for i in range(0, 6)]
        xf = lambda v: f"año {int(v // 365)}"
        lim = self.ax_r.y1
        paso = 0.1
        yt = [-paso * j for j in range(int(lim / paso), 0, -1)] + [0] + [paso * j for j in range(1, int(lim / paso) + 1)]
        self.ax_r.frame(surf, yticks=yt, fmt=pct, xticks=xt, xfmt=lambda v: "",
                        ylabel="Rendimiento de cada día: ¿sube o baja?", a=a0)
        self.ax_a.frame(surf, yticks=[0] + [paso * j for j in range(1, int(lim / paso) + 1)], fmt=pct,
                        xticks=xt, xfmt=lambda v: "", ylabel="Su tamaño, sin signo: ¿día tranquilo o de sacudidas?", a=a0)
        capa = self._capa()
        xr = int(self.ax_r.px(n, 0)[0])
        clip = pygame.Rect(0, 0, xr, H)
        surf.blit(capa, (0, 0), clip)
        # Hurst en ventanas móviles
        ah = fade(t, self.T_HURST[0] - 1)
        ax = self.ax_h
        ax.frame(surf, yticks=[0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0], fmt=lambda v: f"{v:.1f}",
                 xticks=xt, xfmt=xf, ylabel="Exponente de Hurst, ventana de los últimos 500 días", a=ah)
        if ah > 0.01:
            _, y5 = ax.px(0, 0.5)
            for xx in range(ax.rect.x, ax.rect.right, 18):
                pygame.draw.line(surf, mix(BG, PAPER, 0.7 * ah), (xx, y5), (xx + 9, y5), 2)
            _, y6 = ax.px(0, 0.6)
            for xx in range(ax.rect.x, ax.rect.right, 18):
                pygame.draw.line(surf, mix(BG, GOLD, 0.35 * ah), (xx, y6), (xx + 5, y6), 1)
            text_a(surf, "0.5 = paseo aleatorio", (ax.rect.x + 14, y5 + 6), "bold", 21, PAPER, a=ah)
            ae = fade(t, self.T_EXPLICA)
            text_a(surf, "Arriba de 0.5: las rachas tienden a seguir", (ax.rect.x + 14, ax.rect.y + 4),
                   "text", 21, GOLD, a=ae)
        kh = prog(t, *self.T_HURST)
        if kh > 0:
            d = p.dias_h
            idx = _bajar(len(d), 600)
            m = int(kh * len(idx))
            if m >= 2:
                av = fade(t, self.T_VENT)
                if av > 0.01:   # ventanas que «parecen» tener inercia
                    sel = p.h_r > 0.6
                    for i in np.nonzero(sel)[0][::3]:
                        x, _ = ax.px(d[i], 0)
                        pygame.draw.line(surf, mix(BG, GOLD, 0.16 * av), (x, ax.rect.y + 30),
                                         (x, ax.rect.bottom), 1)
                ax.line(surf, d[idx], p.h_a[idx], CORAL, 3, upto=m)
                ax.line(surf, d[idx], p.h_r[idx], CYAN, 3, upto=m)
            lx, ly = ax.rect.right - 330, ax.rect.y + 4
            pygame.draw.line(surf, CYAN, (lx, ly + 12), (lx + 30, ly + 12), 4)
            text(surf, "dirección", (lx + 40, ly), "text", 21, PAPER)
            pygame.draw.line(surf, CORAL, (lx + 160, ly + 12), (lx + 190, ly + 12), 4)
            text(surf, "tamaño", (lx + 200, ly), "text", 21, PAPER)
        av = fade(t, self.T_VENT)
        text_a(surf, f"En {_pct_corto(p.frac_inercia_r)} de las ventanas la dirección «parece» tener inercia "
                     f"(Hurst > 0.6), aunque por construcción no la tiene",
               (ax.rect.x, ax.rect.bottom + 44), "bold", 22, GOLD, a=av)
        self.draw_panel(surf, t, n)

    def draw_panel(self, surf, t, n):
        p, mu = self.p, self.mu
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, 0.5)
        text_a(surf, "Días simulados", (x, 176), "text", 24, GREY, a=a)
        text_a(surf, f"{fmt_int(n)} de {fmt_int(self.N)}", (x, 204), "title", 52, PAPER, a=a)
        text_a(surf, "GARCH(1,1) con colas gordas (t, 4 g. l.)", (x, 270), "text", 19, GREY, a=a)
        vr, pv = p.vr_r[10]
        card(surf, (x, 310, w, 140), "Ratio de varianza a 10 días: dirección",
             fmt_num(vr, 2), CYAN, f"p = {pv:.2f}: no se rechaza el paseo", a=fade(t, self.T_VR_R))
        vr, pv = p.vr_a[10]
        pvs = "p < 0.001" if pv < 0.001 else f"p = {pv:.3f}"
        card(surf, (x, 466, w, 140), "Ratio de varianza a 10 días: tamaño",
             fmt_num(vr, 2), CORAL, f"{pvs}: el tamaño tiene memoria", a=fade(t, self.T_VR_A))
        card(surf, (x, 622, w, 140), "Hurst de toda la serie",
             f"{fmt_num(p.H_r, 2)} · {fmt_num(p.H_a, 2)}", GOLD, "dirección · tamaño", a=fade(t, self.T_H))
        card(surf, (x, 778, w, 160), f"En {mu['n']} series: rechazan el paseo",
             f"{_pct_corto(mu['rej_r'])} · {_pct_corto(mu['rej_a'])}", GOLD,
             f"Hurst medio {fmt_num(mu['h_r'], 2)} · {fmt_num(mu['h_a'], 2)}", a=fade(t, self.T_MUCHAS))



# ======================================================================
#  S5a · La cascada (Bikhchandani, Hirshleifer y Welch 1992)
# ======================================================================
class CascadaScene(Scene):
    title = "Todos copian y nadie usa lo que sabe"
    subtitle = "50 personas eligen restaurante una tras otra. El bueno es A; nadie lo sabe"
    metodo = "Método: cascada informativa de Bikhchandani, Hirshleifer y Welch 1992 (regla de Bayes)"
    simulados = True
    duracion = 56.0

    T_A = (2.5, 19.5)       # agentes 1..K_PUB-1
    T_MAYORIA = 20.5
    T_PUB = 23.0
    T_B = (25.5, 39.5)      # agentes K_PUB..N
    T_MUNDOS = 42.0
    T_ROTAS = 47.0

    def __init__(self, semilla=None):
        super().__init__()
        from .cascada import correr, muchas, buscar_semilla, resumen, inicio_cascada, N, P, Q, K_PUB
        self.semilla = buscar_semilla() if semilla is None else semilla
        self.r = correr(self.semilla)
        self.res = resumen(self.r)
        self.i0 = inicio_cascada(self.r)
        self.mu = muchas()
        self.N, self.P, self.Q, self.K = N, P, Q, K_PUB
        self.ax = Axes((150, 745, 1180, 170), 0.5, N + 0.5, -4, 4)

    def _visibles(self, t):
        k1 = self.K - 1
        if t < self.T_A[0]:
            return 0
        if t < self.T_B[0]:
            return min(k1, 1 + int((t - self.T_A[0]) / (self.T_A[1] - self.T_A[0]) * (k1 - 1) + 1e-6))
        return min(self.N, k1 + 1 + int((t - self.T_B[0]) / (self.T_B[1] - self.T_B[0]) * (self.N - k1 - 1)))

    def _pos(self, i):
        return (209 + 118 * (i % 10), 230 + 92 * (i // 10))

    def draw_scene(self, surf, t):
        r = self.r
        a0 = fade(t, 0.3)
        nv = self._visibles(t)
        col = lambda v: CYAN if v == 1 else CORAL
        # leyenda
        lx, ly = 150, 160
        pygame.draw.circle(surf, mix(BG, CYAN, a0), (lx + 12, ly + 13), 11)
        text_a(surf, "eligió A", (lx + 30, ly), "text", 21, PAPER, a=a0)
        pygame.draw.circle(surf, mix(BG, CORAL, a0), (lx + 142, ly + 13), 11)
        text_a(surf, "eligió B", (lx + 160, ly), "text", 21, PAPER, a=a0)
        pygame.draw.circle(surf, mix(BG, PAPER, a0), (lx + 282, ly + 13), 6)
        text_a(surf, "punto: su corazonada", (lx + 296, ly), "text", 21, PAPER, a=a0)
        pygame.draw.circle(surf, mix(BG, GOLD, a0), (lx + 532, ly + 13), 11, 3)
        text_a(surf, "anillo: la ignoró y copió", (lx + 552, ly), "text", 21, PAPER, a=a0)
        # agentes
        for i in range(self.N):
            x, y = self._pos(i)
            if i >= nv:
                pygame.draw.circle(surf, mix(BG, DIM, 0.6 * a0), (x, y), 30, 2)
                continue
            age = 1.0 if i < nv - 1 else min(1.0, 0.35 + 0.65 * fade(t, self._t_de(i), 0.3))
            pygame.draw.circle(surf, mix(BG, col(r["accion"][i]), 0.9 * age), (x, y), 30)
            text(surf, str(i + 1), (x, y), "mono", 19, BG, "center")
            pygame.draw.circle(surf, mix(BG, col(r["senal"][i]), age), (x, y + 42), 7)
            if r["contra"][i]:
                pygame.draw.circle(surf, mix(BG, GOLD, age), (x, y), 35, 3)
        # avisos entre la fila y la franja
        ye = 652
        if self.i0 is not None and nv > self.i0:
            ac = fade(t, self._t_de(self.i0)) * (1 - fade(t, self.T_PUB - 0.6))
            text_a(surf, f"Desde la persona {self.i0 + 1}, la corazonada propia ya no cambia nada: todos copian",
                   (150, ye), "bold", 23, GOLD, "midleft", a=ac)
        ap = fade(t, self.T_PUB)
        if ap > 0.01:
            bueno = r["s_pub"] == 1
            txt = ("Señal pública antes de la persona " f"{self.K}: una reseña confiable dice A" if bueno
                   else f"Señal pública antes de la persona {self.K}: una reseña dice B")
            pill(surf, txt, (150, ye - 18), CYAN if bueno else CORAL, 23, "topleft", fill=True)
            xs, _ = self.ax.px(self.K - 0.5, 0)
            pygame.draw.line(surf, mix(BG, CYAN, ap), (xs, self.ax.rect.y), (xs, self.ax.rect.bottom), 2)
            x, y = self._pos(self.K - 1)
            pygame.draw.line(surf, mix(BG, CYAN, ap), (x - 56, y - 40), (x - 56, y + 50), 3)
        # franja: lo que cada quien deduce
        ax = self.ax
        ax.frame(surf, yticks=[-2, 0, 2], fmt=lambda v: {2: "A +2", -2: "B +2", 0: "0"}[int(v)],
                 xticks=[1, 10, 20, 30, 40, 50], xfmt=lambda v: f"#{int(v)}",
                 ylabel="Ventaja que cada quien deduce de lo anterior (corazonadas por A menos por B)", a=a0)
        for lado, c in ((1, CYAN), (-1, CORAL)):
            _, ya = ax.px(0, 2 * lado)
            _, yb = ax.px(0, 4 * lado)
            rr = pygame.Rect(ax.rect.x, min(ya, yb), ax.rect.w, abs(yb - ya))
            sh = pygame.Surface(rr.size, pygame.SRCALPHA); sh.fill((*c, int(28 * a0)))
            surf.blit(sh, rr)
            text_a(surf, "zona de cascada: todos copian", (ax.rect.right - 10, (ya + yb) / 2),
                   "text", 19, c, "midright", a=a0)
        if nv >= 1:
            v = r["ventaja"][:nv]
            pts = []
            for i in range(nv):
                xa, y = ax.px(i + 0.5, v[i]); xb, _ = ax.px(i + 1.5, v[i])
                pts += [(xa, y), (xb, y)]
            if len(pts) >= 2:
                pygame.draw.lines(surf, PAPER, False, pts, 3)
        self.draw_panel(surf, t, nv)

    def _t_de(self, i):
        k1 = self.K - 1
        if i < k1:
            return self.T_A[0] + i * (self.T_A[1] - self.T_A[0]) / (k1 - 1)
        return self.T_B[0] + (i - k1) * (self.T_B[1] - self.T_B[0]) / (self.N - k1 - 1)

    def draw_panel(self, surf, t, nv):
        r, res, mu = self.r, self.res, self.mu
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, 0.5)
        k1 = self.K - 1
        text_a(surf, "Personas en la fila", (x, 176), "text", 24, GREY, a=a)
        text_a(surf, f"{nv} de {self.N}", (x, 204), "title", 52, PAPER, a=a)
        text_a(surf, f"Cada corazonada acierta {self.P * 100:.0f} % de las veces", (x, 270), "text", 19,
               GREY, a=a)
        n1 = min(nv, k1)
        sA = int((r["senal"][:n1] == 1).sum()); eB = int((r["accion"][:n1] == -1).sum())
        card(surf, (x, 310, w, 140), "Antes de la señal: eligieron B", f"{eB} de {n1}", CORAL,
             f"Corazonadas por A: {sA} de {n1}", a=fade(t, self.T_A[0] + 2))
        card(surf, (x, 466, w, 140), "La señal pública vale", "2 corazonadas", CYAN,
             f"Acierta {self.Q * 100:.0f} % de las veces", a=fade(t, self.T_PUB))
        n2 = max(0, nv - k1)
        eA = int((r["accion"][k1:nv] == 1).sum())
        card(surf, (x, 622, w, 140), "Después de la señal: eligieron A", f"{eA} de {n2}", CYAN,
             f"Ignoraron su corazonada: {int(r['contra'][:nv].sum())} de {nv}", a=fade(t, self.T_B[0]))
        card(surf, (x, 778, w, 160), f"{fmt_int(mu['n'])} filas: terminan en B",
             f"{_pct_corto(mu['sin_mal'])} → {_pct_corto(mu['con_mal'])}", GOLD,
             f"sin señal → con señal · rompe {_pct_corto(mu['rotas'])}", a=fade(t, self.T_MUNDOS))



# ======================================================================
#  S5b · Lux y Marchesi (1999), versión simplificada
# ======================================================================
class LuxScene(Scene):
    title = "El mercado que se inventa sus tormentas"
    subtitle = "500 agentes que se contagian el ánimo. Las noticias que reciben son de campana"
    metodo = "Método: versión simplificada de Lux y Marchesi 1999 (Nature), escrita por el canal"
    simulados = True
    duracion = 56.0

    T_SERIE = (1.5, 16.0)
    T_K = 18.0
    T_D4 = 23.0
    T_MEM = 28.0
    T_TORM = 33.0
    T_MUNDOS = 40.0

    def __init__(self, semilla=5014):
        super().__init__()
        from .lux import Lux, muchas
        self.L = L = Lux(semilla)
        self.mu = muchas()
        self.zr = (L.r - L.r.mean()) / L.r.std()
        self.zn = (L.n - L.n.mean()) / L.n.std()
        self.N = len(L.r)
        lim = 6.5
        self.lim = lim
        self.ax_n = Axes((150, 215, 560, 160), 0, self.N, -lim, lim)
        self.ax_r = Axes((770, 215, 560, 160), 0, self.N, -lim, lim)
        self.ax_hn = Axes((150, 462, 560, 200), -lim, lim, 0.6, 2500, logy=True)
        self.ax_hr = Axes((770, 462, 560, 200), -lim, lim, 0.6, 2500, logy=True)
        self.ax_z = Axes((150, 790, 1180, 110), 0, self.N, 0, max(0.5, math.ceil(L.Z.max() * 10) / 10))
        self.bins = np.arange(-lim, lim + 1e-9, 0.5)
        # la tormenta más grande: 60 días alrededor del máximo de chartistas
        i = int(np.argmax(L.Z[1:]))
        self.torm = (max(0, i - 30), min(self.N, i + 30))
        self.z_pico = float(L.Z[1:][i]); self.z_med = float(np.median(L.Z))
        self.capa = None

    def _capa(self):
        if self.capa is not None:
            return self.capa
        c = pygame.Surface((W, H), pygame.SRCALPHA)
        for ax, z, col in ((self.ax_n, self.zn, CYAN), (self.ax_r, self.zr, CORAL)):
            _, y0 = ax.px(0, 0)
            for i, v in enumerate(z):
                x, y = ax.px(i + 0.5, max(-self.lim, min(self.lim, v)))
                pygame.draw.line(c, (*col, 170), (x, y0), (x, y), 1)
        self.capa = c
        return c

    def _histo(self, surf, ax, z, n, col, a):
        cnt, _ = np.histogram(z[:n], self.bins)
        ax.frame(surf, yticks=[1, 10, 100, 1000], fmt=lambda v: f"{v:,.0f}".replace(",", " "),
                 xticks=[-6, -4, -2, 0, 2, 4, 6], xfmt=lambda v: f"{v:+.0f}".replace("-", "−").replace("+0", "0"),
                 a=a)
        for i, cn in enumerate(cnt):
            if cn <= 0:
                continue
            xa, _ = ax.px(self.bins[i], 1); xb, _ = ax.px(self.bins[i + 1], 1)
            _, yt = ax.px(0, cn)
            c = GOLD if abs((self.bins[i] + self.bins[i + 1]) / 2) > 4 else col
            pygame.draw.rect(surf, mix(BG, c, 0.8 * a), pygame.Rect(xa + 1, yt, max(1, xb - xa - 2),
                                                                      ax.rect.bottom - yt))
        if n > 50:
            xs = np.linspace(-self.lim, self.lim, 400)
            ys = n * 0.5 * np.exp(-0.5 * xs ** 2) / math.sqrt(2 * math.pi)
            keep = ys >= ax.y0
            pts = ax.pxs(xs[keep], ys[keep])
            pygame.draw.lines(surf, mix(BG, PAPER, a), False, pts.tolist(), 3)

    def draw_scene(self, surf, t):
        L = self.L
        a0 = fade(t, 0.3)
        pill(surf, "Versión simplificada", (W - 36, 92), GOLD, 22, "topright")
        n = max(2, int(prog(t, *self.T_SERIE) * self.N))
        fz = lambda v: f"{v:+.0f}".replace("-", "−").replace("+0", "0")
        xt = [0, 500, 1000, 1500, 2000]
        self.ax_n.frame(surf, yticks=[-4, 0, 4], fmt=fz, xticks=xt, xfmt=lambda v: "", a=a0,
                        ylabel="Entrada: noticias de cada día")
        self.ax_r.frame(surf, yticks=[-4, 0, 4], fmt=fz, xticks=xt, xfmt=lambda v: "", a=a0,
                        ylabel="Salida: rendimiento del precio")
        for ax in (self.ax_n, self.ax_r):
            for v in (-4, 4):
                _, y = ax.px(0, v)
                for xx in range(ax.rect.x, ax.rect.right, 14):
                    pygame.draw.line(surf, mix(BG, GOLD, 0.5 * a0), (xx, y), (xx + 6, y), 1)
        capa = self._capa()
        for ax in (self.ax_n, self.ax_r):
            xr = int(ax.px(n, 0)[0])
            area = pygame.Rect(ax.rect.x, ax.rect.y - 5, xr - ax.rect.x, ax.rect.h + 10)
            surf.blit(capa, area.topleft, area)
        text_a(surf, "En desviaciones típicas · raya dorada: ±4", (self.ax_r.rect.right, 440),
               "text", 21, GREY, "bottomright", a=a0)
        # histogramas
        text_a(surf, "Días por tamaño (escala logarítmica) contra la campana", (150, 440), "text", 21, GREY,
               "bottomleft", a=a0)
        self._histo(surf, self.ax_hn, self.zn, n, CYAN, a0)
        self._histo(surf, self.ax_hr, self.zr, n, CORAL, a0)
        # proporción de chartistas
        az = self.ax_z
        az.frame(surf, yticks=[0, 0.25, 0.5] if az.y1 <= 0.6 else [0, 0.5, 1.0],
                 fmt=lambda v: f"{v * 100:.0f} %", xticks=[0, 500, 1000, 1500, 2000],
                 xfmt=lambda v: f"día {int(v)}", ylabel="Qué parte del mercado sigue la tendencia (chartistas)", a=a0)
        idx = _bajar(self.N, 700)
        idx = idx[idx < n]
        if len(idx) > 1:
            az.line(surf, idx, L.Z[1:][idx], GOLD, 2)
        at = fade(t, self.T_TORM)
        if at > 0.01:
            i0, i1 = self.torm
            for ax in (self.ax_r, self.ax_z):
                xa, _ = ax.px(i0, 0); xb, _ = ax.px(i1, 0)
                rr = pygame.Rect(xa, ax.rect.y - 4, xb - xa, ax.rect.h + 8)
                pygame.draw.rect(surf, mix(BG, PAPER, at), rr, 2, border_radius=6)
            text_a(surf, f"Tormenta: los que siguen la tendencia pasan de {self.z_med * 100:.0f} % "
                         f"a {self.z_pico * 100:.0f} % del mercado",
                   (150, az.rect.y - 46), "bold", 22, PAPER, "bottomleft", a=at)
        self.draw_panel(surf, t, n)

    def draw_panel(self, surf, t, n):
        res, mu = self.L.res, self.mu
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, 0.5)
        text_a(surf, "Días simulados", (x, 176), "text", 24, GREY, a=a)
        text_a(surf, f"{fmt_int(n)} de {fmt_int(self.N)}", (x, 204), "title", 52, PAPER, a=a)
        text_a(surf, "Noticias → precio (campana: curtosis 3)", (x, 270), "text", 19, GREY, a=a)
        card(surf, (x, 310, w, 140), "Curtosis: noticias → precio",
             f"{fmt_num(res['k_n'], 1)} → {fmt_num(res['k_r'], 1)}", CORAL, "Más de 3: colas gordas",
             a=fade(t, self.T_K))
        card(surf, (x, 466, w, 140), "Días de más de 4 desviaciones",
             f"{res['d4_n']} → {res['d4_r']}", GOLD, f"La campana espera {2 * self.N * 3.167e-5:.2f}",
             a=fade(t, self.T_D4))
        card(surf, (x, 622, w, 140), "Memoria del tamaño (1 día)",
             f"{fmt_num(res['aca1_n'], 2)} → {fmt_num(res['aca1_r'], 2)}", CYAN,
             f"Dirección: {fmt_num(res['ac1_r'], 2)} (sin memoria)", a=fade(t, self.T_MEM))
        card(surf, (x, 778, w, 160), f"Promedio de {mu['n']} mundos",
             f"{fmt_num(mu['k_n'], 1)} → {fmt_num(mu['k_r'], 1)}", GOLD,
             f"Curtosis de {fmt_num(mu['k_r_min'], 1)} a {fmt_num(mu['k_r_max'], 1)} · memoria {fmt_num(mu['aca1_r'], 2)}",
             a=fade(t, self.T_MUNDOS))



# ======================================================================
#  S6b · El concurso de belleza (Keynes 1936; Nagel 1995)
# ======================================================================
class BellezaScene(Scene):
    title = "El concurso de belleza"
    subtitle = "Elige de 0 a 100. Gana quien quede más cerca de 2/3 del promedio"
    metodo = "Método: pasos de razonamiento (nivel k) de Nagel 1995 · 1 000 jugadores simulados"
    simulados = True
    duracion = 52.0

    T_R1 = (1.5, 9.0)
    T_MEDIA = 9.5
    T_MORPH = [(13.0, 17.0), (21.0, 25.0), (29.0, 33.0)]
    T_NAGEL = 36.0
    T_GRUPOS = 41.0

    def __init__(self, semilla=1995):
        super().__init__()
        from .belleza import jugar, grupos, PROPORCIONES, N_JUG
        self.j = jugar(semilla)
        self.g = grupos()
        self.prop = PROPORCIONES
        self.n = N_JUG
        self.bins = np.arange(0, 100.0001, 2)
        hmax = max(np.histogram(e, self.bins)[0].max() for e in self.j["E"])
        self.ax = Axes((150, 250, 1180, 540), 0, 100, 0, math.ceil(hmax * 1.15 / 20) * 20)
        rng = np.random.default_rng(3)
        self.orden = rng.permutation(self.n)

    def _estado(self, t):
        """(valores actuales, ronda mostrada 0..3, ¿en transición?)"""
        E = self.j["E"]
        if t < self.T_MORPH[0][0]:
            return E[0], 0, False
        for k, (a, b) in enumerate(self.T_MORPH):
            if t < a:
                return E[k], k, False
            if t < b:
                f = ui.ease(prog(t, a, b))
                return E[k] * (1 - f) + E[k + 1] * f, k + 1, True
        return E[-1], len(E) - 1, False

    def draw_scene(self, surf, t):
        j, ax = self.j, self.ax
        a0 = fade(t, 0.3)
        vals, ronda, moviendo = self._estado(t)
        if t < self.T_R1[1] + 0.01:
            m = int(prog(t, *self.T_R1) * self.n)
            vals = vals[self.orden[:m]]
        ax.frame(surf, yticks=list(range(0, int(ax.y1) + 1, 20 if ax.y1 <= 160 else 40)),
                 fmt=lambda v: f"{v:.0f}", xticks=list(range(0, 101, 10)), xfmt=lambda v: f"{v:.0f}",
                 ylabel="Jugadores que eligieron cada número (cajones de 2)", xlabel="Número elegido", a=a0)
        # marcas de niveles
        for v, lab in ((50, "nivel 0: 50"), (100 / 3, "nivel 1: 33"), (200 / 9, "nivel 2: 22")):
            x, _ = ax.px(v, 0)
            for yy in range(ax.rect.y, ax.rect.bottom, 14):
                pygame.draw.line(surf, mix(BG, PAPER, 0.45 * a0), (x, yy), (x, yy + 7), 2)
            text_a(surf, lab, (x + 6, ax.rect.y + 4), "bold", 21, PAPER, a=a0)
        x0, _ = ax.px(0, 0)
        text_a(surf, "Si todos razonaran hasta el final, todos elegirían 0", (ax.rect.right, ax.rect.y + 40),
               "text", 21, GREY, "topright", a=a0)
        # histograma
        if len(vals):
            cnt, _ = np.histogram(vals, self.bins)
            for i, c in enumerate(cnt):
                if c <= 0:
                    continue
                xa, _ = ax.px(self.bins[i], 0); xb, _ = ax.px(self.bins[i + 1], 0)
                _, yt = ax.px(0, c)
                pygame.draw.rect(surf, mix(BG, CYAN, 0.8), pygame.Rect(xa + 1, yt, max(1, xb - xa - 2),
                                                                     ax.rect.bottom - yt))
        # promedio y ganador
        am = fade(t, self.T_MEDIA) * (0.35 if moviendo else 1.0)
        if am > 0.01 and len(vals):
            med = float(np.mean(vals)); gan = med * 2 / 3
            for v, col, lab, dx, anc in ((med, GOLD, f"promedio {med:.1f}", 8, "topleft"),
                                         (gan, CORAL, f"gana {gan:.1f} (2/3)", -8, "topright")):
                x, _ = ax.px(v, 0)
                pygame.draw.line(surf, mix(BG, col, am), (x, ax.rect.y + 70), (x, ax.rect.bottom), 3)
                text_a(surf, lab, (x + dx, ax.rect.y + 74), "bold", 22, col, anc, a=am)
        # promedios por ronda
        hechas = ronda + (0 if moviendo else 1) if t >= self.T_MEDIA else 0
        if hechas:
            s = "   ·   ".join(f"Ronda {k + 1}: {j['medias'][k]:.1f}" for k in range(hechas))
            text_a(surf, "Promedio por ronda", (150, 872), "text", 21, GREY, a=a0)
            text_a(surf, s, (150, 900), "bold", 26, GOLD, a=a0)
        self.draw_panel(surf, t, ronda, moviendo)

    def draw_panel(self, surf, t, ronda, moviendo):
        j, g = self.j, self.g
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, 0.5)
        text_a(surf, "Ronda", (x, 176), "text", 24, GREY, a=a)
        text_a(surf, f"{ronda + 1} de {len(j['medias'])}", (x, 204), "title", 52, PAPER, a=a)
        text_a(surf, "Cada ronda parten del promedio anterior", (x, 270), "text", 19, GREY, a=a)
        pr = " · ".join(f"{p * 100:.0f}" for p in self.prop)
        card(surf, (x, 310, w, 140), "Supuesto del canal, no dato:", f"{pr} %", GOLD,
             "de jugadores en los niveles 0 · 1 · 2 · 3", a=fade(t, 1.0))
        r0 = ronda if not moviendo else ronda - 1
        card(surf, (x, 466, w, 140), "Eligieron 0 en esta ronda",
             f"{int(round(j['ceros'][max(0, r0)] * self.n))} de {fmt_int(self.n)}", CYAN,
             f"Mediana {j['medianas'][max(0, r0)]:.0f}", a=fade(t, self.T_MEDIA))
        card(surf, (x, 622, w, 140), "Nagel 1995, laboratorio, ronda 1", "media 36.73", PAPER,
             "Mediana 33 · nadie eligió 0", a=fade(t, self.T_NAGEL))
        card(surf, (x, 778, w, 160), f"Grupos de {g['tam']}, {fmt_int(g['n'])} sorteos",
             f"{g['p5']:.0f} a {g['p95']:.0f}", GOLD,
             f"Media de la ronda 1 (90 % de los grupos)", a=fade(t, self.T_GRUPOS))



# ======================================================================
#  S6c · El precio que debió ser (Shiller 1981, datos reales)
# ======================================================================
class ShillerScene(Scene):
    title = "El precio que debió ser"
    subtitle = "Bolsa de EE. UU. desde 1871 contra lo que justificaban sus dividendos"
    metodo = ("Método: p* = valor presente de los dividendos reales posteriores con tasa constante, "
              "como Shiller 1981 · precio de enero")
    simulados = False
    credito = "Datos: Robert J. Shiller, shillerdata.com"
    duracion = 56.0

    T_P = (1.5, 16.0)
    T_PS = (17.0, 27.0)
    T_79 = (31.0, 38.0)
    T_SHILLER = 44.0

    def __init__(self):
        super().__init__()
        import warnings
        from .shiller import calcular
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            self.c = calcular()
        c = self.c
        self.anios = c["anios"].astype(float)
        self.ax = Axes((170, 240, 1150, 600), self.anios[0], self.anios[-1] + 1, 80, 9000, logy=True)

    def draw_scene(self, surf, t):
        c, ax, an = self.c, self.ax, self.anios
        tot, s79 = c["total"], c["s79"]
        a0 = fade(t, 0.3)
        ax.frame(surf, yticks=[100, 300, 1000, 3000], fmt=lambda v: f"{v:,.0f}".replace(",", " "),
                 xticks=list(range(1880, 2030, 20)), xfmt=lambda v: f"{v:.0f}",
                 ylabel="Índice S&P real, en dólares de hoy (escala logarítmica)", a=a0)
        n = len(an)
        kP = prog(t, *self.T_P) * n
        ax.line(surf, an, c["P"], mix(BG, CORAL, a0), 3, upto=kP)
        if kP >= 2:
            i = min(n - 1, int(kP) - 1)
            x, y = ax.px(an[i], c["P"][i])
            fin = i > n - 12
            text_a(surf, f"{an[i]:.0f}", (x - 10 if fin else x + 10, y - 10), "bold", 24, CORAL,
                   "bottomright" if fin else "bottomleft", a=a0)
        a1 = fade(t, self.T_PS[0])
        if a1 > 0.01:
            kS = prog(t, *self.T_PS) * n
            # p* se calcula de atrás hacia adelante: se dibuja desde el final
            xs, ys = an[::-1], tot["Pstar"][::-1]
            ax.line(surf, xs, ys, mix(BG, CYAN, a1), 5, upto=kS)
        al = fade(t, 2.0)
        text_a(surf, "Precio real (enero de cada año)", (190, 262), "bold", 24, CORAL, a=al)
        text_a(surf, f"p*: lo que justificaban los dividendos que vinieron después (muestra 1871–{an[-1]:.0f})",
               (190, 294), "bold", 24, CYAN, a=a1)
        a2 = fade(t, self.T_79[0])
        if a2 > 0.01:
            k = prog(t, *self.T_79) * len(s79["anios"])
            pts = ax.pxs(s79["anios"][::-1].astype(float), s79["Pstar"][::-1])[:max(0, int(k))]
            for j in range(0, len(pts) - 1, 2):
                pygame.draw.line(surf, mix(BG, GOLD, a2), pts[j], pts[j + 1], 4)
            text_a(surf, "p* con la muestra de Shiller (1871–1979)", (190, 326), "bold", 24, GOLD, a=a2)
            a3 = fade(t, self.T_79[1] - 1)
            if a3 > 0.5:
                pill(surf, "El año final de la muestra cambia el cálculo de p*", (ax.rect.centerx, 880),
                     GOLD, 26, "center")
            text_a(surf, f"En dólares las dos p* casi coinciden; cambian la tasa ({fmt_pct(s79['r'], 1, False)} contra "
                         f"{fmt_pct(tot['r'], 1, False)}) y la comparación de nivel ({s79['razon']:.1f} contra {tot['razon']:.1f} veces)",
                   (ax.rect.centerx, 912), "text", 21, GREY, "midtop", a=a3)
        self.draw_panel(surf, t)

    def draw_panel(self, surf, t):
        c = self.c
        tot, s79 = c["total"], c["s79"]
        self.panel(surf)
        x, w = PANEL_RECT.x + 24, PANEL_RECT.w - 48
        a = fade(t, 0.5)
        n = len(self.anios)
        k = max(1, min(n, int(prog(t, *self.T_P) * n)))
        text_a(surf, "Años de datos reales", (x, 176), "text", 24, GREY, a=a)
        text_a(surf, f"{fmt_int(k)}", (x, 204), "title", 52, PAPER, a=a)
        text_a(surf, f"De {self.anios[0]:.0f} a {self.anios[-1]:.0f} · dividendos completos", (x, 270), "text", 19, GREY, a=a)
        card(surf, (x, 310, w, 140), "Tasa de descuento real fija", fmt_pct(tot["r"], 1, False), CYAN,
             f"Muestra 1871–1979: {fmt_pct(s79['r'], 1, False)}", a=fade(t, self.T_PS[0]))
        card(surf, (x, 466, w, 140), "El precio se mueve más que p*",
             f"{tot['razon_cambios']:.0f} veces", CORAL,
             f"Cambios anuales · muestra a 1979: {s79['razon_cambios']:.0f}", a=fade(t, self.T_PS[1]))
        card(surf, (x, 622, w, 140), "Variación del nivel, p contra p*",
             f"{tot['razon']:.1f} veces", GOLD, f"Muestra 1871–1979: {s79['razon']:.1f} veces", a=fade(t, self.T_79[1]))
        card(surf, (x, 778, w, 160), "Shiller 1981, pp. 432–434", "5 a 13 veces", PAPER,
             "Sus pruebas formales, 1871–1979", a=fade(t, self.T_SHILLER))


SCENES = {
    "s2": ColasScene,
    "s3": PaseoScene,
    "s4": FabricaScene,
    "s5a": CascadaScene,
    "s5b": LuxScene,
    "s6b": BellezaScene,
    "s6c": ShillerScene,
}
SCENE_KEYS = list(SCENES)


def make_scene(key):
    return SCENES[key]()
