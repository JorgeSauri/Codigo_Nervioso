# Carga los modelos de S2 para las visualizaciones. CC0.
import os, sys, json, glob, numpy as np, torch
AQUI = os.path.dirname(os.path.abspath(__file__))
S2 = os.environ.get("S2_DIR") or os.path.abspath(os.path.join(AQUI, "../world_models")); sys.path.insert(0, S2)
import config as C
from modelos import VAE, MDNRNN, accion
from PIL import Image
torch.set_grad_enabled(False)
def carga(tau="1.15"):
    vae = VAE(); vae.load_state_dict(torch.load(C.ruta("vae.pt"), map_location="cpu")); vae.eval()
    rnn = MDNRNN(); rnn.load_state_dict(torch.load(C.ruta("mdnrnn.pt"), map_location="cpu")); rnn.eval()
    wf = C.ruta(f"controlador_tau{tau}", "W_mejor.npy"); W = np.load(wf) if os.path.exists(wf) else None
    return vae, rnn, W
PRELIM = C.MODO != "completo" or os.environ.get("S2_PRELIM") == "1"
SALIDA = os.path.join(AQUI, "..", "salida", "preliminar_" + C.MODO if C.MODO != "completo" else ("preliminar" if PRELIM else "visualizaciones")); os.makedirs(SALIDA, exist_ok=True)
ETIQ_PRELIM = "PRELIMINAR · modelo de prueba con datos reducidos" if PRELIM else ""
def a_img(x, tam):
    """x: tensor (3,64,64) en [0,1] o array (64,64,3) uint8 → PIL ampliado con vecino más cercano."""
    if isinstance(x, torch.Tensor): x = (x.clamp(0, 1).permute(1, 2, 0).numpy() * 255).astype(np.uint8)
    return Image.fromarray(x).resize(tam, Image.NEAREST)
def suena(rnn, vae, W, z0, tau, pasos, gen, acciones=None, h0=None):
    """Sueño de un solo agente. Devuelve lista de dicts (z, img, a, p_muerte, murio)."""
    z = z0[None].clone(); estado = h0; h = torch.zeros(1, C.RNN_H) if h0 is None else h0[0][0]; c = torch.zeros(1, C.RNN_H) if h0 is None else h0[1][0]
    reinicio = torch.ones(1, 1) if h0 is None else torch.zeros(1, 1); out = []
    for t in range(pasos):
        if acciones is not None: a = torch.tensor([acciones[t]], dtype=torch.float32)
        elif W is not None: a = accion(torch.as_tensor(W, dtype=torch.float32)[None], z, c, h)
        else: a = torch.zeros(1)
        logpi, mu, logs, muerte, estado = rnn(z[:, None], a[:, None], reinicio, estado)
        h, c = estado[0][0], estado[1][0]; reinicio = torch.zeros(1, 1)
        img = vae.decodifica(z)[0]
        p = float(torch.sigmoid(muerte[0, 0]))
        out.append(dict(z=z[0].numpy().copy(), img=img, a=float(a[0]), p_muerte=p, murio=p > 0.5))
        z = MDNRNN.muestrea(logpi[:, 0], mu[:, 0], logs[:, 0], tau, gen)
        if p > 0.5: break
    return out
