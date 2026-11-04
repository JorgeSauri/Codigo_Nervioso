# Paso 3 [paper]: entrena M (MDN-RNN) para predecir P(z_{t+1}, muere_{t+1} | a_t, z_t, h_t). CC0.
# Cada muestra es un tramo de un solo rollout (estado LSTM en cero al inicio, bandera de reinicio=1 en el primer cuadro).
import time, numpy as np, torch
import config as C
from modelos import MDNRNN
dev = "cuda" if torch.cuda.is_available() else "cpu"
torch.manual_seed(0); rng = np.random.default_rng(0)
d = np.load(C.ruta("series.npz"), allow_pickle=True)
MU, LV, A, M = d["mu"], d["logvar"], d["accion"], d["murio"]
N = len(MU); L = C.RNN_SEQ
rnn = MDNRNN().to(dev); opt = torch.optim.Adam(rnn.parameters(), lr=C.RNN_LR)
print("parámetros MDN-RNN:", sum(p.numel() for p in rnn.parameters()), "(paper: 1,678,785; PyTorch suma un segundo sesgo en la LSTM)", flush=True)
lotes_por_epoca = max(1, N // C.RNN_LOTE)      # una época ≈ cada rollout visto una vez (como en el código de Ha)
sched = torch.optim.lr_scheduler.LambdaLR(opt, lambda s: max(0.99999 ** s, 1e-5 / C.RNN_LR))   # decay [código Ha]
def lote():
    B = C.RNN_LOTE; Z = np.zeros((B, L + 1, C.Z), np.float32); Av = np.zeros((B, L + 1), np.float32)
    R = np.zeros((B, L + 1), np.float32); D = np.zeros((B, L + 1), np.float32); Mk = np.zeros((B, L + 1), np.float32)
    for b in range(B):
        i = rng.integers(N); n = len(MU[i])
        ini = 0 if n <= L + 1 or rng.random() < 0.3 else int(rng.integers(0, n - L))   # 30% desde el inicio (aprende el arranque)
        fin = min(n, ini + L + 1)
        if fin == n: ini = max(0, n - L)            # si el tramo llega al final, que el último cuadro sea entrada
        k = fin - ini
        mu = MU[i][ini:fin].astype(np.float32); lv = LV[i][ini:fin].astype(np.float32)
        Z[b, :k] = mu + np.exp(lv / 2) * rng.standard_normal(mu.shape)        # z ~ N(mu, sigma) en cada lote [paper A.2]
        Av[b, :k] = A[i][ini:fin]; Mk[b, :k] = 1
        if ini == 0: R[b, 0] = 1
        if fin == n and M[i]: D[b, k - 1] = 1          # tras la última acción, el agente muere
    t = lambda x: torch.as_tensor(x, device=dev)
    return t(Z), t(Av), t(R), t(D), t(Mk)
log = open(C.ruta("rnn_log.csv"), "w"); log.write("paso,perdida_z,perdida_muerte\n"); t0 = time.time(); paso = 0
for ep in range(C.RNN_EPOCAS):
    for _ in range(lotes_por_epoca):
        Z, Av, R, D, Mk = lote()
        logpi, mu, logs, muerte, _ = rnn(Z[:, :-1], Av[:, :-1], R[:, :-1])
        m_in = Mk[:, 1:]                                   # predicción del siguiente z válida si existe
        lz = (MDNRNN.nll(logpi, mu, logs, Z[:, 1:]).mean(-1) * m_in).sum() / m_in.sum()
        m_d = Mk[:, :-1]; peso = 1 + D[:, :-1] * (C.FACTOR_MUERTE - 1)
        ld = (torch.nn.functional.binary_cross_entropy_with_logits(muerte, D[:, :-1], reduction="none") * peso * m_d).sum() / m_d.sum()
        loss = lz + ld; opt.zero_grad(); loss.backward()
        torch.nn.utils.clip_grad_value_(rnn.parameters(), C.RNN_CLIP); opt.step(); sched.step(); paso += 1
        if paso % 20 == 0:
            log.write(f"{paso},{lz.item():.4f},{ld.item():.4f}\n"); log.flush()
            print(f"época {ep+1}/{C.RNN_EPOCAS} paso {paso} nll_z {lz.item():.3f} muerte {ld.item():.4f} {time.time()-t0:.0f}s", flush=True)
    if (ep + 1) % 10 == 0: torch.save(rnn.state_dict(), C.ruta("mdnrnn_parcial.pt"))
    if ep + 1 == 20: torch.save(rnn.state_dict(), C.ruta("mdnrnn_ep020.pt"))   # el paper dice 20 épocas; el código de Ha usa 400
torch.save(rnn.state_dict(), C.ruta("mdnrnn.pt")); print("MDN-RNN listo", paso, "pasos")
