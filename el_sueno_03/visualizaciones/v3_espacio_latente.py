# Visualización 3: el espacio latente z animado (proyección PCA 3D de miles de cuadros reales codificados). CC0.
import sys, math, numpy as np, torch
from s2_comun import *
from estilo import *
from PIL import ImageDraw
d0 = np.load(C.ruta("series.npz"), allow_pickle=True); MU = d0["mu"]
rng = np.random.default_rng(0)
todos = np.concatenate([m.astype(np.float32) for m in MU[: min(len(MU), 400)]])
nube = todos[rng.choice(len(todos), min(25000, len(todos)), replace=False)]
media = nube.mean(0); U, Sv, Vt = np.linalg.svd(nube - media, full_matrices=False); P = Vt[:3]
var = (Sv[:3] ** 2).sum() / (Sv ** 2).sum()
proy = (nube - media) @ P.T; esc = np.percentile(np.abs(proy), 98, axis=0)
vae, rnn, Wc = carga()
ep = max(range(min(len(MU), 400)), key=lambda i: len(MU[i]))       # episodio más largo de los datos
traj_mu = MU[ep].astype(np.float32); traj = (traj_mu - media) @ P.T
for k in range(1, len(traj)): traj[k] = 0.7 * traj[k - 1] + 0.3 * traj[k]     # suavizado solo para dibujar el trazo
obs = np.load(sorted(glob.glob(C.ruta("rollouts", "*.npz")))[ep])["obs"]
CX, CY, R = 640, 560, 420
def proyecta(p, ang, elev=0.35):
    q = p / esc; x, y, zz = q[:, 0], q[:, 1], q[:, 2]
    xr = x * math.cos(ang) - y * math.sin(ang); yr = x * math.sin(ang) + y * math.cos(ang)
    yy = zz * math.cos(elev) - yr * math.sin(elev); prof = zz * math.sin(elev) + yr * math.cos(elev)
    return CX + xr * R * 0.7, CY - yy * R * 0.7, prof
vid = Video(os.path.join(SALIDA, "v3_espacio_latente.mp4")); png = None
N = len(traj); FR = 2       # 2 cuadros de video por paso del juego (~30 pasos/s, casi tiempo real)
T1 = min(N, 600)
for f in range(T1 * FR + 240):
    t = min(T1 - 1, f // FR); ang = f * 0.004
    im, d = lienzo(); rejilla_fondo(d)
    arr = np.asarray(im).copy()
    x, y, p = proyecta(proy, ang); b = np.clip((p + 2.5) / 5, 0.15, 1)
    xi, yi = x.astype(int), y.astype(int); ok = (xi > 0) & (xi < W - 1) & (yi > 0) & (yi < H - 1)
    col = (np.array(GRIS)[None] * b[:, None] * 0.85 + np.array(NAVY)[None] * (1 - b[:, None] * 0.85)).astype(np.uint8)
    arr[yi[ok], xi[ok]] = col[ok]; arr[yi[ok] + 1, xi[ok]] = col[ok]; arr[yi[ok], xi[ok] + 1] = col[ok]; arr[yi[ok] + 1, xi[ok] + 1] = col[ok]
    im = Image.fromarray(arr); d = ImageDraw.Draw(im)
    tx, ty, _ = proyecta(traj[: t + 1], ang); pts = list(zip(tx, ty))[-120:]
    for k in range(1, len(pts)):
        d.line([pts[k - 1], pts[k]], fill=mezcla(NAVY, CIAN, k / len(pts)), width=3)
    d.ellipse([tx[-1] - 10, ty[-1] - 10, tx[-1] + 10, ty[-1] + 10], fill=CIAN)
    texto(d, (70, 60), "El mapa interno: 64 números por imagen", "titulo", 58)
    texto(d, (70, 140), f"cada punto gris = un cuadro del juego codificado por el VAE (vista 3D de 64 dimensiones)", "texto", 28, GRIS)
    im.paste(Image.fromarray(obs[t]).resize((360, 360), Image.NEAREST), (1440, 230)); marco(d, [1438, 228, 1801, 591], PAPEL)
    im.paste(a_img(vae.decodifica(torch.as_tensor(traj_mu[t])[None])[0], (360, 360)), (1440, 650)); marco(d, [1438, 648, 1801, 1011], CIAN, 3)
    texto(d, (1420, 245), "lo que ve", "dato_b", 26, PAPEL, "ra"); texto(d, (1420, 665), "lo que reconstruye", "dato_b", 26, CIAN, "ra"); texto(d, (1420, 700), "desde z", "dato", 22, GRIS, "ra")
    # z como rejilla 8x8
    zc = traj_mu[t]
    for k in range(64):
        v = float(np.clip((zc[k] + 2.5) / 5, 0, 1)); gx, gy = 1160 + (k % 8) * 30, 800 + (k // 8) * 26
        d.rectangle([gx, gy, gx + 26, gy + 22], fill=mezcla(NAVY, CIAN, v))
    texto(d, (1160, 770), "z (8×8)", "dato", 22, GRIS)
    texto(d, (70, 1010), f"paso {t}", "dato", 24, GRIS)
    pie(d, ("PRELIMINAR · " if PRELIM else "") + f"en nuestra simulación · PCA: 3 ejes = {var:.0%} de la varianza")
    vid.cuadro(im)
    if f == T1 * FR // 2: png = im
# Paseo por el espacio latente: moverse por los ejes principales y decodificar
for f in range(8 * 60):
    t = f / 60; s1, s2 = 2.2 * math.sin(t * 0.9), 2.2 * math.sin(t * 1.3 + 1)
    zc = media + s1 * Sv[0] / math.sqrt(len(nube)) * Vt[0] + s2 * Sv[1] / math.sqrt(len(nube)) * Vt[1]
    im, d = lienzo(); rejilla_fondo(d)
    texto(d, (70, 60), "Caminar por el mapa interno", "titulo", 58)
    texto(d, (70, 140), "moverse en z y decodificar: imágenes que no son ningún cuadro real: las inventa el decodificador", "texto", 28, GRIS)
    im.paste(a_img(vae.decodifica(torch.as_tensor(zc, dtype=torch.float32)[None])[0], (640, 640)), (640, 250)); marco(d, [638, 248, 1281, 891], CIAN, 3)
    texto(d, (960, 930), f"eje 1: {s1:+.1f} σ    eje 2: {s2:+.1f} σ", "dato", 28, GRIS, "ma")
    pie(d, ("PRELIMINAR · " if PRELIM else "") + "en nuestra simulación"); vid.cuadro(im)
vid.cierra(); png.save(os.path.join(SALIDA, "v3_espacio_latente.png")); im.save(os.path.join(SALIDA, "v3_espacio_latente_paseo.png")); print("listo", vid.n)
