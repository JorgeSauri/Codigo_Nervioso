# Paso 6 [paper]: el controlador entrenado en el sueño juega el VizDoom real, 100 rollouts. También la política aleatoria. CC0.
import os, sys, json, numpy as np, torch
import multiprocessing as mp   # 'spawn': con fork, varias instancias de ViZDoom se bloquean
import config as C
torch.set_num_threads(1)
def _carga():
    from modelos import VAE, MDNRNN
    v = VAE(); v.load_state_dict(torch.load(C.ruta("vae.pt"), map_location="cpu")); v.eval()
    r = MDNRNN(); r.load_state_dict(torch.load(C.ruta("mdnrnn.pt"), map_location="cpu")); r.eval()
    return v, r
def _juega(args):
    wpath, semilla, aleatorio = args
    from rollout_real import juega
    v, r = _carga(); W = None if aleatorio else np.load(wpath)
    return juega(v, r, W, semilla, aleatorio=aleatorio)
if __name__ == "__main__":
    tau = sys.argv[1] if len(sys.argv) > 1 else f"{C.TEMPERATURA:.2f}"
    wpath = C.ruta(f"controlador_tau{tau}", sys.argv[2] if len(sys.argv) > 2 else "W_mejor.npy")
    semillas = [900_000 + i for i in range(C.EVAL_N_REAL)]     # semillas que no se usaron para recolectar datos
    nproc = min(os.cpu_count(), 24)
    with mp.get_context("spawn").Pool(nproc) as p:
        real = np.array(p.map(_juega, [(wpath, s, False) for s in semillas]))
        azar = np.array(p.map(_juega, [(wpath, s, True) for s in semillas])) if not os.path.exists(C.ruta("aleatorio_real.json")) else None
    if azar is not None:
        json.dump({"n": len(azar), "media": float(azar.mean()), "de": float(azar.std()), "pasos": azar.tolist()}, open(C.ruta("aleatorio_real.json"), "w"), indent=1)
    res = {"tau": float(tau), "controlador": os.path.basename(wpath), "n": len(real), "media": float(real.mean()), "de": float(real.std()), "pasos": real.tolist()}
    json.dump(res, open(C.ruta(f"controlador_tau{tau}", "real_" + os.path.basename(wpath).replace(".npy", ".json")), "w"), indent=1)
    print(f"τ={tau}: juego real {real.mean():.0f} ± {real.std():.0f} pasos en {len(real)} rollouts")
    a = json.load(open(C.ruta("aleatorio_real.json"))); print(f"aleatorio: {a['media']:.0f} ± {a['de']:.0f}")
