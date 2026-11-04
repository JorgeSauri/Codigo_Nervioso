# Juega «Take Cover» real con el agente V+M+C (o al azar). Lo usan la evaluación y las visualizaciones. CC0.
import numpy as np, torch
import config as C
from entorno import TakeCover, PoliticaAleatoria
from modelos import accion

@torch.no_grad()
def juega(vae, rnn, W, semilla, guarda=False, resolucion="RES_160X120", aleatorio=False):
    env = TakeCover(semilla, resolucion); rng = np.random.default_rng(semilla)
    gen = torch.Generator().manual_seed(int(semilla))
    obs = env.reset(); estado = None; reinicio = 1.0; pasos = 0; rec = []
    pol = PoliticaAleatoria(rng); h = c = torch.zeros(1, C.RNN_H); Wt = None if W is None else torch.as_tensor(W, dtype=torch.float32)[None]
    while True:
        x = torch.as_tensor(obs, dtype=torch.float32).permute(2, 0, 1)[None] / 255
        mu, lv = vae.codifica(x)
        z = mu + torch.randn(mu.shape, generator=gen) * torch.exp(lv / 2)
        a = pol() if aleatorio else float(accion(Wt, z, c, h)[0])
        if guarda: rec.append(dict(cuadro=env.cuadro, obs=obs, mu=mu[0].numpy(), z=z[0].numpy(), a=a, h=h[0].numpy().copy(), c=c[0].numpy().copy()))
        _, _, _, _, estado = rnn(z[:, None], torch.tensor([[a]], dtype=torch.float32), torch.tensor([[reinicio]]), estado)
        h, c = estado[0][0], estado[1][0]; reinicio = 0.0
        obs, murio, fin = env.step(a); pasos += 1
        if fin: break
    env.close()
    return (pasos, rec) if guarda else pasos
