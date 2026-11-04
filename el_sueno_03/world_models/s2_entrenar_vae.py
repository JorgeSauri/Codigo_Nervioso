# Paso 2 [paper]: entrena V (VAE) 1 época sobre todos los cuadros. CC0.
import os, glob, json, time, numpy as np, torch
import config as C
from modelos import VAE
dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(0); rng = np.random.default_rng(0)
fs = sorted(glob.glob(C.ruta("rollouts", "*.npz")))
vae = VAE().to(dev); opt = torch.optim.Adam(vae.parameters(), lr=C.VAE_LR)
print("parámetros VAE:", sum(p.numel() for p in vae.parameters()), "(paper: 4,446,915)", flush=True)
log = open(C.ruta("vae_log.csv"), "w"); log.write("paso,perdida,recon,kl\n"); paso = 0; t0 = time.time()
BLOQUE = 400 if C.MODO == "completo" else 8    # rollouts que se cargan a la vez en RAM
for ep in range(C.VAE_EPOCAS):
    orden = rng.permutation(len(fs))
    for b in range(0, len(fs), BLOQUE):
        X = np.concatenate([np.load(fs[i])["obs"] for i in orden[b:b + BLOQUE]]); rng.shuffle(X)
        for i in range(0, len(X) - C.VAE_LOTE + 1, C.VAE_LOTE):
            x = torch.as_tensor(X[i:i + C.VAE_LOTE], device=dev).permute(0, 3, 1, 2).float() / 255
            y, mu, lv = vae(x); L, r, kl = VAE.perdida(x, y, mu, lv)
            opt.zero_grad(); L.backward(); opt.step(); paso += 1
            if paso % 100 == 0:
                log.write(f"{paso},{L.item():.2f},{r.item():.2f},{kl.item():.2f}\n"); log.flush()
                print(f"época {ep} bloque {b}/{len(fs)} paso {paso} pérdida {L.item():.1f} (recon {r.item():.1f}, kl {kl.item():.1f}) {time.time()-t0:.0f}s", flush=True)
        if C.MODO == "completo" and (b // BLOQUE) % 5 == 0:
            torch.save(vae.state_dict(), C.ruta("vae_parcial.pt"))
torch.save(vae.state_dict(), C.ruta("vae.pt")); print("VAE listo", paso, "pasos")
