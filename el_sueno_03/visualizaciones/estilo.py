# Estilo «laboratorio oscuro» de Código Nervioso + escritor de video 1080p60 con ffmpeg. CC0.
import subprocess, numpy as np
from PIL import Image, ImageDraw, ImageFont
NAVY = (11, 16, 32); CIAN = (0, 229, 199); CORAL = (255, 107, 74); PAPEL = (244, 241, 234); GRIS = (138, 147, 166)
W, H, FPS = 1920, 1080, 60
import os
G = os.environ.get("EP03_FUENTES", os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "fuentes") + "/")
_cache = {}
def fuente(tipo, tam):
    k = (tipo, tam)
    if k not in _cache:
        ruta, var = {"titulo": ("Space Grotesk/SpaceGrotesk-VariableFont_wght.ttf", "Bold"),
                     "texto": ("Inter/Inter-VariableFont_opsz,wght.ttf", "Regular"),
                     "texto_b": ("Inter/Inter-VariableFont_opsz,wght.ttf", "SemiBold"),
                     "dato": ("JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf", "Regular"),
                     "dato_b": ("JetBrains Mono/JetBrainsMono-VariableFont_wght.ttf", "Bold")}[tipo]
        f = ImageFont.truetype(G + ruta, tam)
        try: f.set_variation_by_name(var)
        except Exception: pass
        _cache[k] = f
    return _cache[k]
def mezcla(c1, c2, t): return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))
def lienzo():
    im = Image.new("RGB", (W, H), NAVY); return im, ImageDraw.Draw(im)
def rejilla_fondo(d, paso=60, color=(18, 25, 46)):
    for x in range(0, W, paso): d.line([(x, 0), (x, H)], fill=color)
    for y in range(0, H, paso): d.line([(0, y), (W, y)], fill=color)
def texto(d, xy, s, tipo="texto", tam=32, color=PAPEL, ancla="la"):
    d.text(xy, s, font=fuente(tipo, tam), fill=color, anchor=ancla)
def pie(d, s, color=GRIS):
    texto(d, (W - 40, H - 30), s, "dato", 20, color, "rd")
def marco(d, caja, color=GRIS, ancho=2): d.rectangle(caja, outline=color, width=ancho)
class Video:
    def __init__(self, ruta, fps=FPS):
        self.p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}",
                                   "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "medium", "-crf", "17",
                                   "-pix_fmt", "yuv420p", "-movflags", "+faststart", ruta], stdin=subprocess.PIPE)
        self.n = 0
    def cuadro(self, im, veces=1):
        b = (im if isinstance(im, np.ndarray) else np.asarray(im.convert("RGB"))).tobytes()
        for _ in range(veces): self.p.stdin.write(b); self.n += 1
    def cierra(self): self.p.stdin.close(); self.p.wait()
