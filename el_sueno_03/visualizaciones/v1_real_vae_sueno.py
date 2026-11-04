# Visualización 1: pantalla dividida — Doom real | reconstrucción del VAE | sueño del MDN-RNN. CC0.
import sys, numpy as np, torch
from s2_comun import *
from rollout_real import juega
from estilo import *
SEM = int(sys.argv[1]) if len(sys.argv) > 1 else 900_007
SYNC = 3 * 35        # cada 3 s el sueño se re-ancla al z real
vae, rnn, Wc = carga()
# probamos hasta 8 semillas y nos quedamos con el episodio más largo (máx. 25 s de video); se reporta la semilla
mejor = None
for k in range(8):
    pasos, rec = juega(vae, rnn, Wc, SEM + k, guarda=True, resolucion="RES_640X480", aleatorio=Wc is None)
    print("semilla", SEM + k, "pasos reales", pasos)
    if mejor is None or pasos > mejor[0]: mejor = (pasos, rec, SEM + k)
    if pasos >= 25 * 35: break
pasos, rec, SEM = mejor; rec = rec[:25 * 35]
print("usada semilla", SEM, "pasos", pasos)
gen = torch.Generator().manual_seed(SEM)
sueno = []
for t0 in range(0, len(rec), SYNC):
    acc = [r["a"] for r in rec[t0:t0 + SYNC]]
    s = suena(rnn, vae, None, torch.as_tensor(rec[t0]["z"]), C.TEMPERATURA, len(acc), gen, acciones=acc)
    s += [s[-1]] * (len(acc) - len(s))          # si el sueño «muere» antes, se congela
    sueno += [(x, i) for i, x in enumerate(s)]
recon = [vae.decodifica(torch.as_tensor(r["mu"])[None])[0] for r in rec]
Y = 250; S = 480; XR, XV, XS = 70, 70 + 640 + 70, 70 + 640 + 70 + S + 70
vid = Video(os.path.join(SALIDA, "v1_real_vae_sueno.mp4")); png = None
for t in range(len(rec)):
    im, d = lienzo(); rejilla_fondo(d)
    texto(d, (70, 60), "Lo que ve, lo que entiende, lo que imagina", "titulo", 58)
    texto(d, (70, 140), "Take Cover (ViZDoom + Freedoom) · un agente de world models", "texto", 30, GRIS)
    im.paste(Image.fromarray(rec[t]["cuadro"]).resize((640, 480), Image.NEAREST), (XR, Y))
    im.paste(a_img(recon[t], (S, S)), (XV, Y))
    sx, k = sueno[t]; im.paste(a_img(sx["img"], (S, S)), (XS, Y))
    marco(d, [XR - 2, Y - 2, XR + 641, Y + 481], PAPEL); marco(d, [XV - 2, Y - 2, XV + S + 1, Y + S + 1], GRIS); marco(d, [XS - 2, Y - 2, XS + S + 1, Y + S + 1], CIAN, 3)
    texto(d, (XR, Y + 500), "1 · EL JUEGO REAL", "dato_b", 28, PAPEL); texto(d, (XR, Y + 540), "640×480 píxeles", "texto", 24, GRIS)
    texto(d, (XV, Y + 500), "2 · LO QUE ENTIENDE (VAE)", "dato_b", 28, PAPEL); texto(d, (XV, Y + 540), "reconstruido desde 64 números (z)", "texto", 24, GRIS)
    texto(d, (XS, Y + 500), "3 · LO QUE IMAGINA (MDN-RNN)", "dato_b", 28, CIAN); texto(d, (XS, Y + 540), f"sueña {k / 35:.1f} s hacia adelante", "texto", 24, GRIS)
    # z como 64 barras
    z = rec[t]["mu"]; bx = XV; by = Y + 610
    for j, v in enumerate(z):
        hgt = int(np.clip(v, -3, 3) * 14); x = bx + j * 7
        d.rectangle([x, by - max(hgt, 0), x + 4, by - min(hgt, 0)], fill=GRIS)
    texto(d, (bx + 64 * 7 + 16, by), "z", "dato_b", 28, GRIS, "lm")
    a = rec[t]["a"]; flecha = "◀ izquierda" if a < -C.UMBRAL else ("derecha ▶" if a > C.UMBRAL else "quieto")
    texto(d, (XR, Y + 600), f"paso {t:4d}   acción: {flecha}", "dato", 26, PAPEL)
    if k < 12: texto(d, (XS + S // 2, Y + S // 2), "se re-sincroniza", "dato_b", 30, CIAN, "mm")
    pie(d, ("PRELIMINAR · " if PRELIM else "") + "en nuestra simulación · réplica de Ha & Schmidhuber (2018), World Models")
    fr = 60 / 35; n = int((t + 1) * fr) - int(t * fr); vid.cuadro(im, n)
    if t == min(len(rec) - 1, 2 * SYNC + 60): png = im
vid.cuadro(im, 60); vid.cierra(); png.save(os.path.join(SALIDA, "v1_real_vae_sueno.png")); print("listo", vid.n)
