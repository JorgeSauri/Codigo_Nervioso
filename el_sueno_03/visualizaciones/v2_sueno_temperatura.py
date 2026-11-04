# Visualización 2: el agente juega DENTRO del sueño; perilla de temperatura τ. CC0.
# Los pasos que se muestran son de sueños reales de nuestro modelo (no se eligen a mano: primera semilla de cada τ).
import sys, math, json, numpy as np, torch
from s2_comun import *
from estilo import *
TAUS = [float(x) for x in (sys.argv[1].split(",") if len(sys.argv) > 1 else ["0.1", "1.15", "1.3"])]
SEG = 9 * 35          # hasta 9 s de sueño por valor de τ
vae, rnn, Wc = carga()
zi = np.load(C.ruta("z_iniciales.npz"))
vid = Video(os.path.join(SALIDA, "v2_sueno_temperatura.mp4")); pngs = []; tau_prev = TAUS[0]
CX, CY, S = 160, 230, 720
def perilla(d, tau, x0=1180, y0=330):
    r = 150; cx, cy = x0 + r, y0 + r
    d.ellipse([cx - r, cy - r, cx + r, cy + r], outline=GRIS, width=4)
    for v in [0, 0.5, 1.0, 1.5, 2.0]:
        ang = math.radians(225 - v / 2.0 * 270)
        d.line([(cx + (r + 8) * math.cos(ang), cy - (r + 8) * math.sin(ang)), (cx + (r + 26) * math.cos(ang), cy - (r + 26) * math.sin(ang))], fill=GRIS, width=3)
        texto(d, (cx + (r + 56) * math.cos(ang), cy - (r + 56) * math.sin(ang)), f"{v:g}", "dato", 22, GRIS, "mm")
    ang = math.radians(225 - min(tau, 2) / 2.0 * 270)
    d.line([(cx, cy), (cx + (r - 22) * math.cos(ang), cy - (r - 22) * math.sin(ang))], fill=CIAN, width=10)
    d.ellipse([cx - 16, cy - 16, cx + 16, cy + 16], fill=CIAN)
    texto(d, (cx, cy + r + 70), f"τ = {tau:.2f}", "dato_b", 54, CIAN, "mm")
    texto(d, (cx, cy + r + 125), "temperatura del sueño", "texto", 26, GRIS, "mm")
for i, tau in enumerate(TAUS):
    gen = torch.Generator().manual_seed(1000 + i)
    j = int(torch.randint(len(zi["mu"]), (1,), generator=gen))
    z0 = torch.as_tensor(zi["mu"][j]) + torch.randn(C.Z, generator=gen) * torch.exp(torch.as_tensor(zi["logvar"][j]) / 2)
    s = suena(rnn, vae, Wc, z0, tau, SEG, gen)
    # transición de la perilla
    for f in range(45):
        t = f / 44; tt = tau_prev + (tau - tau_prev) * (1 - (1 - t) ** 3)
        im, d = lienzo(); rejilla_fondo(d)
        texto(d, (CX, 60), "Jugar dentro del sueño", "titulo", 58); texto(d, (CX, 140), "el controlador nunca ve el juego real: entrena aquí", "texto", 30, GRIS)
        im.paste(a_img(s[0]["img"], (S, S)), (CX, CY)); marco(d, [CX - 2, CY - 2, CX + S + 1, CY + S + 1], CIAN, 3)
        perilla(d, tt); pie(d, ("PRELIMINAR · " if PRELIM else "") + "en nuestra simulación · réplica de Ha & Schmidhuber (2018)"); vid.cuadro(im)
    tau_prev = tau
    for t, x in enumerate(s):
        im, d = lienzo(); rejilla_fondo(d)
        texto(d, (CX, 60), "Jugar dentro del sueño", "titulo", 58); texto(d, (CX, 140), "el controlador nunca ve el juego real: entrena aquí", "texto", 30, GRIS)
        im.paste(a_img(x["img"], (S, S)), (CX, CY)); marco(d, [CX - 2, CY - 2, CX + S + 1, CY + S + 1], CIAN, 3)
        perilla(d, tau)
        texto(d, (1180, 820), f"pasos sobrevividos en el sueño: {t + 1}", "dato_b", 30, PAPEL)
        pm = x["p_muerte"]; d.rectangle([1180, 880, 1180 + 500, 900], outline=GRIS, width=2); d.rectangle([1180, 880, 1180 + int(500 * pm), 900], fill=CIAN)
        texto(d, (1180, 915), f"probabilidad de morir que predice el sueño: {pm:.0%}", "dato", 22, GRIS)
        if x["murio"]: texto(d, (CX + S // 2, CY + S // 2), "MUERE EN EL SUEÑO", "titulo", 64, PAPEL, "mm")
        pie(d, ("PRELIMINAR · " if PRELIM else "") + "en nuestra simulación · réplica de Ha & Schmidhuber (2018)")
        fr = 60 / 35; vid.cuadro(im, int((t + 1) * fr) - int(t * fr))
        if t == min(len(s) - 1, 140): pngs.append(im)
    vid.cuadro(im, 45 if not s[-1]["murio"] else 75)
    print(f"τ={tau}: {len(s)} pasos, murió={s[-1]['murio']}")
vid.cierra(); pngs[len(pngs) // 2].save(os.path.join(SALIDA, "v2_sueno_temperatura.png")); print("listo", vid.n)
