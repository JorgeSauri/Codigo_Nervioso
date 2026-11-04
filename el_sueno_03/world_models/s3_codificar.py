# Paso 2b [código Ha, series.py]: guarda mu y logvar de cada cuadro para entrenar M. CC0.
import glob, numpy as np, torch
import config as C
from modelos import VAE
dev = "cuda" if torch.cuda.is_available() else "cpu"
vae = VAE().to(dev); vae.load_state_dict(torch.load(C.ruta("vae.pt"), map_location=dev)); vae.eval()
fs = sorted(glob.glob(C.ruta("rollouts", "*.npz"))); MU, LV, A, M = [], [], [], []
with torch.no_grad():
    for k, f in enumerate(fs):
        d = np.load(f); x = torch.as_tensor(d["obs"], device=dev).permute(0, 3, 1, 2).float() / 255
        mu, lv = vae.codifica(x)
        MU.append(mu.cpu().numpy().astype(np.float16)); LV.append(lv.cpu().numpy().astype(np.float16))
        A.append(d["accion"]); M.append(bool(d["murio"]))
        if k % 1000 == 0: print(k, "/", len(fs), flush=True)
np.savez(C.ruta("series.npz"), mu=np.array(MU, dtype=object), logvar=np.array(LV, dtype=object),
         accion=np.array(A, dtype=object), murio=np.array(M))
# 1000 z iniciales para arrancar los sueños [código Ha, rnn_train.py]
np.savez(C.ruta("z_iniciales.npz"), mu=np.array([m[0] for m in MU[:1000]], np.float32), logvar=np.array([l[0] for l in LV[:1000]], np.float32))
print("series listas:", len(fs), "rollouts,", sum(len(m) for m in MU), "cuadros; murieron:", int(np.sum(M)))
