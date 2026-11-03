"""Piezas de interfaz con la estética de Código Nervioso."""
import os
import math
import pygame

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
W, H = 1920, 1080

BG = (11, 16, 32)          # Navy Sináptico #0B1020
BG2 = (17, 24, 46)
PANEL = (20, 28, 54)
CYAN = (0, 229, 199)       # Cian Impulso #00E5C7
CORAL = (255, 107, 74)     # Coral Potencial #FF6B4A
PAPER = (244, 241, 234)    # Papel Cajal #F4F1EA
GREY = (138, 147, 166)     # Gris Axón #8A93A6
DIM = (60, 70, 98)
GOLD = (255, 200, 87)

_fonts = {}
FONT_FILES = {
    "title": "SpaceGrotesk-Bold.ttf",
    "bold": "Inter-Bold.ttf",
    "text": "Inter-Medium.ttf",
    "mono": "JetBrainsMono-SemiBold.ttf",
}


def font(kind, size):
    key = (kind, size)
    if key not in _fonts:
        _fonts[key] = pygame.font.Font(os.path.join(HERE, "fonts", FONT_FILES[kind]), size)
    return _fonts[key]


def text(surf, s, pos, kind="text", size=28, color=PAPER, anchor="topleft", alpha=255):
    img = font(kind, size).render(s, True, color)
    if alpha < 255:
        img.set_alpha(alpha)
    r = img.get_rect(**{anchor: pos})
    surf.blit(img, r)
    return r


def lerp(a, b, t):
    return a + (b - a) * t


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(lerp(a, b, t)) for a, b in zip(c1, c2))


def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def rrect(surf, color, rect, radius=14, width=0):
    pygame.draw.rect(surf, color, rect, width=width, border_radius=radius)


_logo = None


def watermark(surf):
    global _logo
    if _logo is None:
        img = pygame.image.load(os.path.join(HERE, "assets", "logo_marca.png")).convert_alpha()
        h = 46
        w = int(img.get_width() * h / img.get_height())
        _logo = pygame.transform.smoothscale(img, (w, h))
        _logo.set_alpha(200)
    surf.blit(_logo, (36, H - 36 - _logo.get_height()))
    text(surf, "Código Nervioso", (36 + _logo.get_width() + 14, H - 36 - _logo.get_height() // 2),
         "title", 26, GREY, "midleft", alpha=210)


def background(surf):
    surf.fill(BG)


def header(surf, title, subtitle=None):
    text(surf, title, (60, 38), "title", 54, PAPER)
    if subtitle:
        text(surf, subtitle, (62, 104), "text", 28, GREY)


# ------------------------------------------------------------------
class Control:
    visible = True
    enabled = True

    def center(self):
        return self.rect.center


class Slider(Control):
    """Deslizador grande con etiqueta en palabras y valor legible."""

    def __init__(self, name, label, vmin, vmax, value, fmt=None, step=None,
                 on_change=None, color=CYAN, live=True):
        self.name, self.label = name, label
        self.vmin, self.vmax = vmin, vmax
        self.value = value
        self.fmt = fmt or (lambda v: f"{v:.2f}")
        self.step = step
        self.on_change = on_change
        self.color = color
        self.rect = pygame.Rect(0, 0, 400, 96)
        self.dragging = False
        self.live = live
        self.hl = 0.0   # resaltado (0..1)

    def layout(self, x, y, w):
        self.rect = pygame.Rect(x, y, w, 96)

    @property
    def track(self):
        return pygame.Rect(self.rect.x + 4, self.rect.y + 64, self.rect.w - 8, 8)

    def frac(self):
        return (self.value - self.vmin) / (self.vmax - self.vmin)

    def knob_pos(self, value=None):
        v = self.value if value is None else value
        f = (v - self.vmin) / (self.vmax - self.vmin)
        tr = self.track
        return (int(tr.x + f * tr.w), tr.centery)

    def set(self, v, notify=True):
        v = max(self.vmin, min(self.vmax, v))
        if self.step:
            v = round((v - self.vmin) / self.step) * self.step + self.vmin
            v = max(self.vmin, min(self.vmax, v))
        changed = abs(v - self.value) > 1e-12
        self.value = v
        if changed and notify and self.on_change:
            self.on_change(v)

    def value_at(self, x):
        tr = self.track
        f = (x - tr.x) / tr.w
        return self.vmin + max(0, min(1, f)) * (self.vmax - self.vmin)

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1:
            hit = self.rect.inflate(0, 10)
            if hit.collidepoint(ev.pos) and ev.pos[1] > self.rect.y + 44:
                self.dragging = True
                self.set(self.value_at(ev.pos[0]))
                return True
        elif ev.type == pygame.MOUSEBUTTONUP and ev.button == 1:
            self.dragging = False
        elif ev.type == pygame.MOUSEMOTION and self.dragging:
            self.set(self.value_at(ev.pos[0]))
            return True
        return False

    def draw(self, surf):
        r = self.rect
        col = self.color if self.enabled else DIM
        text(surf, self.label, (r.x, r.y + 4), "bold", 30, PAPER if self.enabled else GREY)
        text(surf, self.fmt(self.value), (r.right, r.y + 6), "mono", 30, col, "topright")
        tr = self.track
        rrect(surf, DIM, tr, 4)
        filled = tr.copy(); filled.w = max(0, int(self.frac() * tr.w))
        rrect(surf, col, filled, 4)
        kx, ky = self.knob_pos()
        rad = 17 + int(4 * self.hl)
        if self.hl > 0.01:
            g = pygame.Surface((80, 80), pygame.SRCALPHA)
            pygame.draw.circle(g, (*col, int(70 * self.hl)), (40, 40), 34)
            surf.blit(g, (kx - 40, ky - 40))
        pygame.draw.circle(surf, PAPER, (kx, ky), rad)
        pygame.draw.circle(surf, col, (kx, ky), rad - 5)


class Button(Control):
    def __init__(self, name, label, on_click=None, color=CYAN, w=None):
        self.name, self.label = name, label
        self.on_click = on_click
        self.color = color
        self.rect = pygame.Rect(0, 0, w or 200, 64)
        self.pressed = 0.0
        self.active = False
        self.fixed_w = w

    def layout(self, x, y, w):
        self.rect = pygame.Rect(x, y, self.fixed_w or w, 64)

    def click(self):
        self.pressed = 1.0
        if self.on_click:
            self.on_click()

    def handle(self, ev):
        if ev.type == pygame.MOUSEBUTTONDOWN and ev.button == 1 and self.rect.collidepoint(ev.pos):
            self.click()
            return True
        return False

    def draw(self, surf):
        r = self.rect
        p = self.pressed
        col = self.color
        if self.active:
            rrect(surf, col, r, 16)
            text(surf, self.label, r.center, "bold", 28, BG, "center")
        else:
            rrect(surf, mix(PANEL, col, 0.18 + 0.5 * p), r, 16)
            rrect(surf, col, r, 16, 3)
            text(surf, self.label, r.center, "bold", 28, PAPER, "center")
        self.pressed = max(0.0, p - 0.06)


def layout_panel(controls, x=1410, y=170, w=450, gap=22):
    """Acomoda los controles en columna; los botones de una misma fila van en tuplas."""
    for c in controls:
        if isinstance(c, tuple):
            n = len(c)
            bw = (w - (n - 1) * 16) // n
            for i, b in enumerate(c):
                b.layout(x + i * (bw + 16), y, bw)
            y += 64 + gap
        else:
            c.layout(x, y, w)
            y += c.rect.h + gap
    return y


def flatten(controls):
    out = []
    for c in controls:
        out.extend(c if isinstance(c, tuple) else [c])
    return out


# ------------------------------------------------------------------
def draw_cursor(surf, pos, down=0.0):
    x, y = pos
    pts = [(0, 0), (0, 34), (9, 26), (15, 40), (21, 37), (15, 24), (27, 24)]
    poly = [(x + px, y + py) for px, py in pts]
    sh = [(px + 3, py + 4) for px, py in poly]
    s = pygame.Surface((W, H), pygame.SRCALPHA) if False else None
    pygame.draw.polygon(surf, (0, 0, 0), sh)
    pygame.draw.polygon(surf, PAPER, poly)
    pygame.draw.polygon(surf, (10, 10, 20), poly, 2)
    if down > 0.01:
        rad = int(18 + 26 * (1 - down))
        g = pygame.Surface((120, 120), pygame.SRCALPHA)
        pygame.draw.circle(g, (*CYAN, int(200 * down)), (60, 60), rad, 4)
        surf.blit(g, (x - 60, y - 60))


def glow_line(surf, color, a, b, width, intensity=1.0):
    """Línea con halo suave (se dibuja sobre una superficie SRCALPHA)."""
    if intensity <= 0.01:
        return
    al = int(255 * min(1, intensity))
    pygame.draw.line(surf, (*color, int(al * 0.18)), a, b, int(width * 3) + 2)
    pygame.draw.line(surf, (*color, int(al * 0.35)), a, b, int(width * 1.8) + 1)
    pygame.draw.line(surf, (*color, al), a, b, max(1, int(width)))


def chart(surf, rect, series, colors, labels=None, title=None, ymin=None, ymax=None,
          ref=None, ref_label=None, xmax=None):
    """Gráfica de líneas simple. series: listas de valores por ronda."""
    rrect(surf, BG2, rect, 14)
    pad_l, pad_b, pad_t = 70, 40, 46
    x0, y0 = rect.x + pad_l, rect.y + pad_t
    w, h = rect.w - pad_l - 24, rect.h - pad_t - pad_b
    if title:
        text(surf, title, (rect.x + 20, rect.y + 10), "bold", 24, PAPER)
    allv = [v for s in series for v in s if v == v and v < 1e9]
    if ref is not None:
        allv.append(ref)
    if not allv:
        return
    lo = ymin if ymin is not None else min(allv)
    hi = ymax if ymax is not None else max(allv)
    if hi - lo < 1e-6:
        hi = lo + 1
    span = hi - lo
    if ymin is None:
        lo -= span * 0.05
    hi += span * 0.05
    n = xmax or max(2, max(len(s) for s in series))
    for i in range(5):
        yy = y0 + h * i / 4
        pygame.draw.line(surf, (35, 45, 72), (x0, yy), (x0 + w, yy), 1)
        val = hi - (hi - lo) * i / 4
        text(surf, f"{val:.0f}", (x0 - 10, yy), "mono", 18, GREY, "midright")
    text(surf, "ronda", (x0 + w, y0 + h + 8), "text", 18, GREY, "topright")
    text(surf, "0", (x0, y0 + h + 8), "mono", 18, GREY, "topleft")
    if ref is not None:
        yy = y0 + h * (hi - ref) / (hi - lo)
        for xx in range(int(x0), int(x0 + w), 16):
            pygame.draw.line(surf, GREY, (xx, yy), (xx + 8, yy), 2)
        if ref_label:
            if ymin is None:
                text(surf, ref_label, (x0 + w - 4, yy + 6), "text", 18, GREY, "topright")
            else:
                text(surf, ref_label, (x0 + 8, yy - 4), "text", 18, GREY, "bottomleft")
    for s, col in zip(series, colors):
        if len(s) < 2:
            continue
        pts = []
        for i, v in enumerate(s[:n]):
            px = x0 + w * i / (n - 1)
            py = y0 + h * (hi - min(max(v, lo), hi)) / (hi - lo)
            pts.append((px, py))
        pygame.draw.aalines(surf, col, False, pts)
        pygame.draw.lines(surf, col, False, pts, 3)
    if labels:
        lx = rect.x + rect.w - 20
        for lab, col in reversed(list(zip(labels, colors))):
            r = text(surf, lab, (lx, rect.y + 14), "text", 20, col, "topright")
            lx = r.x - 24


# ------------------------------------------------------------------
#  Piezas añadidas para EP02 (gráficas por tiempo, etiquetas fijas)
# ------------------------------------------------------------------
def pill(surf, s, pos, color=CORAL, size=26, anchor="topright", fill=False):
    """Etiqueta en cápsula (p. ej. «Datos simulados»)."""
    img = font("bold", size).render(s, True, BG if fill else color)
    box = img.get_rect()
    box.inflate_ip(36, 16)
    setattr(box, anchor, pos)
    if fill:
        rrect(surf, color, box, box.h // 2)
    else:
        rrect(surf, mix(BG, color, 0.12), box, box.h // 2)
        rrect(surf, color, box, box.h // 2, 3)
    surf.blit(img, img.get_rect(center=box.center))
    return box


def fade(t, t0, dur=0.6):
    """0 → 1 entre t0 y t0 + dur."""
    return ease((t - t0) / dur) if dur > 0 else float(t >= t0)


def prog(t, t0, t1):
    """Avance lineal 0 → 1 entre t0 y t1."""
    if t1 <= t0:
        return float(t >= t1)
    return max(0.0, min(1.0, (t - t0) / (t1 - t0)))


def blit_alpha(surf, img, pos, alpha):
    if alpha <= 0:
        return
    if alpha < 255:
        img = img.copy()
        img.set_alpha(int(alpha))
    surf.blit(img, pos)


def text_a(surf, s, pos, kind="text", size=28, color=PAPER, anchor="topleft", a=1.0):
    """Texto con opacidad 0..1."""
    if a <= 0.01:
        return None
    return text(surf, s, pos, kind, size, color, anchor, alpha=int(255 * min(1, a)))


class Axes:
    """Ejes con escala lineal o logarítmica en y."""

    def __init__(self, rect, x0, x1, y0, y1, logy=False):
        self.rect = pygame.Rect(rect)
        self.x0, self.x1, self.y0, self.y1 = x0, x1, y0, y1
        self.logy = logy

    def _fy(self, y):
        if self.logy:
            return math.log10(max(y, 1e-12))
        return y

    def px(self, x, y):
        r = self.rect
        fx = (x - self.x0) / (self.x1 - self.x0)
        a, b = self._fy(self.y0), self._fy(self.y1)
        fy = (self._fy(y) - a) / (b - a)
        return (r.x + fx * r.w, r.bottom - fy * r.h)

    def pxs(self, xs, ys):
        import numpy as _np
        xs = _np.asarray(xs, float); ys = _np.asarray(ys, float)
        r = self.rect
        fx = (xs - self.x0) / (self.x1 - self.x0)
        if self.logy:
            ys = _np.log10(_np.maximum(ys, 1e-12))
            a, b = math.log10(self.y0), math.log10(self.y1)
        else:
            a, b = self.y0, self.y1
        fy = (ys - a) / (b - a)
        return _np.stack([r.x + fx * r.w, r.bottom - fy * r.h], 1)

    def frame(self, surf, yticks=(), fmt=lambda v: f"{v:g}", xticks=(), xfmt=lambda v: f"{v:g}",
              xlabel=None, ylabel=None, a=1.0, grid=True):
        r = self.rect
        gc = mix(BG2, (45, 58, 92), a)
        for v in yticks:
            _, y = self.px(self.x0, v)
            if grid:
                pygame.draw.line(surf, gc, (r.x, y), (r.right, y), 1)
            text_a(surf, fmt(v), (r.x - 12, y), "mono", 20, GREY, "midright", a)
        for v in xticks:
            x, _ = self.px(v, self.y0)
            pygame.draw.line(surf, mix(BG2, DIM, a), (x, r.bottom), (x, r.bottom + 8), 2)
            text_a(surf, xfmt(v), (x, r.bottom + 12), "mono", 20, GREY, "midtop", a)
        pygame.draw.line(surf, mix(BG2, DIM, a), (r.x, r.bottom), (r.right, r.bottom), 2)
        if xlabel:
            text_a(surf, xlabel, (r.right, r.bottom + 40), "text", 21, GREY, "topright", a)
        if ylabel:
            text_a(surf, ylabel, (r.x, r.y - 14), "text", 21, GREY, "bottomleft", a)

    def line(self, surf, xs, ys, color, width=3, upto=None):
        pts = self.pxs(xs, ys)
        if upto is not None:
            pts = pts[:max(0, int(upto))]
        if len(pts) >= 2:
            pygame.draw.lines(surf, color, False, pts.tolist(), width)
        return pts


def card(surf, rect, title, value, color=CYAN, sub=None, a=1.0):
    """Tarjeta de cifra: título chico, número grande y una línea opcional."""
    if a <= 0.01:
        return
    rect = pygame.Rect(rect)
    s = pygame.Surface(rect.size, pygame.SRCALPHA)
    pygame.draw.rect(s, (*BG2, 255), s.get_rect(), border_radius=16)
    pygame.draw.rect(s, (*color, 255), pygame.Rect(0, 0, 8, rect.h), border_top_left_radius=16,
                     border_bottom_left_radius=16)
    text(s, title, (26, 14), "text", 23, GREY)
    text(s, value, (26, 44), "title", 46, color)
    if sub:
        text(s, sub, (26, rect.h - 14), "text", 21, PAPER, "bottomleft")
    s.set_alpha(int(255 * a))
    surf.blit(s, rect)


def fmt_pct(v, dec=1, signo=True):
    s = f"{v * 100:+.{dec}f} %" if signo else f"{v * 100:.{dec}f} %"
    return s.replace("-", "−")


def fmt_num(v, dec=2, signo=False):
    s = f"{v:+.{dec}f}" if signo else f"{v:.{dec}f}"
    return s.replace("-", "−")


def fmt_int(v):
    return f"{int(round(v)):,}".replace(",", " ")
