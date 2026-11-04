# Utilidades comunes para las animaciones del EP03 (estilo laboratorio oscuro). CC0.
import sys, os, math
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '../visualizaciones'))
from estilo import *
from PIL import Image, ImageDraw, ImageFilter
AQUI = os.path.dirname(os.path.abspath(__file__))
SAL = os.path.join(AQUI, '..', 'salida', 'animaciones')
def suave(x):
    x = max(0.0, min(1.0, x)); return x * x * (3 - 2 * x)
def tramo(t, a, b): return suave((t - a) / (b - a)) if b > a else float(t >= a)
def alfa(c, a, fondo=NAVY): return mezcla(fondo, c, max(0, min(1, a)))
def envolver(s, tipo, tam, ancho):
    f = fuente(tipo, tam); lin = []; cur = ''
    for p in s.split(' '):
        x = (cur + ' ' + p).strip()
        if f.getlength(x) > ancho and cur: lin.append(cur); cur = p
        else: cur = x
    lin.append(cur); return lin
def parrafo(d, xy, s, tipo='texto', tam=48, color=PAPEL, ancho=1500, inter=1.3, ancla='la', visibles=None):
    x, y = xy; lin = envolver(s, tipo, tam, ancho); n = 0
    for l in lin:
        if visibles is not None:
            if n >= visibles: break
            l = l[:max(0, visibles - n)]
        n += len(l) + 1
        texto(d, (x, y), l, tipo, tam, color, ancla); y += int(tam * inter)
    return y
def flecha(d, a, b, color=GRIS, ancho=4, punta=18):
    d.line([a, b], fill=color, width=ancho)
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    for s in (-1, 1):
        d.line([b, (b[0] - punta * math.cos(ang + s * 0.45), b[1] - punta * math.sin(ang + s * 0.45))], fill=color, width=ancho)
def render(nombre, dur, dibuja, fondo_rejilla=True, fin_fundido=0.5, ini_fundido=0.4):
    ruta = os.path.join(SAL, nombre + '.mp4'); v = Video(ruta); n = int(round(dur * FPS))
    for i in range(n):
        t = i / FPS; im, d = lienzo()
        if fondo_rejilla: rejilla_fondo(d)
        r = dibuja(t, im, d)
        if r is not None: im = r
        k = min(1, t / ini_fundido if ini_fundido else 1, (dur - t) / fin_fundido if fin_fundido else 1)
        if k < 1: im = Image.blend(Image.new('RGB', (W, H), NAVY), im, max(0, k))
        v.cuadro(im)
        if i == n // 2: im.save(os.path.join(SAL, 'frames', nombre + '.png'))
    v.cierra(); print('OK', nombre, n, 'cuadros')
os.makedirs(os.path.join(SAL, 'frames'), exist_ok=True)
