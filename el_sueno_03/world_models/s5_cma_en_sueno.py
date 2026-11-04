# Pasos 4-5 [paper]: C = tanh(W[z c h]); CMA-ES (población 64, 16 rollouts c/u) maximiza la supervivencia
# DENTRO DEL SUEÑO generado por M (nunca ve el juego real). Todos los sueños de una generación corren en paralelo. CC0.
import os, sys, time, json, numpy as np, torch, cma
import config as C
from modelos import MDNRNN, accion, N_PARAM_C
dev = "cuda" if torch.cuda.is_available() else "cpu"
TAU = C.TEMPERATURA; etiqueta = f"tau{TAU:.2f}"
rnn = MDNRNN().to(dev); rnn.load_state_dict(torch.load(C.ruta("mdnrnn.pt"), map_location=dev)); rnn.eval()
zi = np.load(C.ruta("z_iniciales.npz")); ZI_MU = torch.as_tensor(zi["mu"], device=dev); ZI_LV = torch.as_tensor(zi["logvar"], device=dev)

@torch.no_grad()
def suena(W, tau, gen, max_pasos=C.MAX_PASOS, registra=False):
    """W: (B,1088). Corre B sueños en paralelo; devuelve pasos sobrevividos (B,). Si registra, guarda la trayectoria z del sueño 0."""
    B = W.shape[0]
    idx = torch.randint(len(ZI_MU), (B,), generator=gen, device=dev)
    z = ZI_MU[idx] + torch.exp(ZI_LV[idx] / 2) * torch.randn(B, C.Z, generator=gen, device=dev)
    h = torch.zeros(B, C.RNN_H, device=dev); c = torch.zeros_like(h); estado = None
    reinicio = torch.ones(B, 1, device=dev); vivo = torch.ones(B, dtype=torch.bool, device=dev)
    pasos = torch.zeros(B, device=dev); tray = []
    for t in range(max_pasos):
        a = accion(W, z, c, h)
        if registra: tray.append((z[0].cpu().numpy(), float(a[0])))
        logpi, mu, logs, muerte, estado = rnn(z[:, None], a[:, None], reinicio, estado)
        h, c = estado[0][0], estado[1][0]; reinicio = torch.zeros(B, 1, device=dev)
        z = MDNRNN.muestrea(logpi[:, 0], mu[:, 0], logs[:, 0], tau, gen)
        pasos += vivo.float()
        vivo &= ~(muerte[:, 0] > 0)                     # muere si p(muerte) > 0.5 [paper A.2]
        if not vivo.any(): break
    return (pasos, tray) if registra else pasos

if __name__ == "__main__":
    gen = torch.Generator(device=dev).manual_seed(1234)
    es = cma.CMAEvolutionStrategy(np.zeros(N_PARAM_C), C.CMA_SIGMA0, {"popsize": C.CMA_POB, "seed": 1234, "verbose": -9})
    out = C.ruta(f"controlador_{etiqueta}"); os.makedirs(out, exist_ok=True)
    log = open(os.path.join(out, "cma_log.csv"), "w"); log.write("generacion,mejor,media,peor,eval_mejor_sueno_media,eval_mejor_sueno_de\n")
    mejor_eval = -1; t0 = time.time()
    print(f"CMA-ES en el sueño, τ={TAU}, población {C.CMA_POB} x {C.CMA_REPS} rollouts, {C.CMA_GENS} generaciones, {dev}", flush=True)
    for g in range(1, C.CMA_GENS + 1):
        sol = es.ask()
        W = torch.as_tensor(np.array(sol), dtype=torch.float32, device=dev).repeat_interleave(C.CMA_REPS, 0)
        s = suena(W, TAU, gen).view(C.CMA_POB, C.CMA_REPS).mean(1).cpu().numpy()
        es.tell(sol, (-s).tolist())
        fila = [g, s.max(), s.mean(), s.min(), "", ""]
        if g % C.EVAL_CADA == 0 or g == C.CMA_GENS:
            wb = torch.as_tensor(sol[int(s.argmax())], dtype=torch.float32, device=dev)
            e = suena(wb[None].repeat(C.EVAL_N_SUENO, 1), TAU, gen).cpu().numpy()
            fila[4], fila[5] = f"{e.mean():.1f}", f"{e.std():.1f}"
            np.save(os.path.join(out, f"W_gen{g:04d}.npy"), wb.cpu().numpy())
            if e.mean() > mejor_eval:
                mejor_eval = e.mean(); np.save(os.path.join(out, "W_mejor.npy"), wb.cpu().numpy())
                json.dump({"generacion": g, "tau": TAU, "sueno_media": float(e.mean()), "sueno_de": float(e.std()), "n": C.EVAL_N_SUENO},
                          open(os.path.join(out, "mejor.json"), "w"), indent=1)
        log.write(",".join(str(round(x, 1)) if isinstance(x, (float, np.floating)) else str(x) for x in fila) + "\n"); log.flush()
        print(f"gen {g} mejor {s.max():.0f} media {s.mean():.0f} peor {s.min():.0f} {('eval '+fila[4]+' ± '+fila[5]) if fila[4] else ''} {time.time()-t0:.0f}s", flush=True)
    print("listo; mejor evaluación en sueño:", mejor_eval)
