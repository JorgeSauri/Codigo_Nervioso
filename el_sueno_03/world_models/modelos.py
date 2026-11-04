# V (VAE), M (MDN-RNN) y C (controlador) de Ha & Schmidhuber (2018). PyTorch, CC0.
import math, torch, torch.nn as nn, torch.nn.functional as F
import config as C

class VAE(nn.Module):
    """Apéndice A.1: 4 conv 4x4 stride 2 (32,64,128,256) -> z; decodificador con 4 deconv (128,64,32,3)."""
    def __init__(self, z=C.Z):
        super().__init__()
        self.enc = nn.Sequential(nn.Conv2d(3,32,4,2), nn.ReLU(), nn.Conv2d(32,64,4,2), nn.ReLU(),
                                 nn.Conv2d(64,128,4,2), nn.ReLU(), nn.Conv2d(128,256,4,2), nn.ReLU(), nn.Flatten())
        self.mu, self.logvar = nn.Linear(1024, z), nn.Linear(1024, z)
        self.fc = nn.Linear(z, 1024)
        self.dec = nn.Sequential(nn.ConvTranspose2d(1024,128,5,2), nn.ReLU(), nn.ConvTranspose2d(128,64,5,2), nn.ReLU(),
                                 nn.ConvTranspose2d(64,32,6,2), nn.ReLU(), nn.ConvTranspose2d(32,3,6,2), nn.Sigmoid())
    def codifica(self, x):                       # x: (B,3,64,64) en [0,1]
        h = self.enc(x); return self.mu(h), self.logvar(h)
    def decodifica(self, z):
        return self.dec(self.fc(z).view(-1, 1024, 1, 1))
    def forward(self, x):
        mu, lv = self.codifica(x); z = mu + torch.randn_like(mu) * torch.exp(lv / 2)
        return self.decodifica(z), mu, lv
    @staticmethod
    def perdida(x, y, mu, lv):
        r = ((x - y) ** 2).sum((1, 2, 3)).mean()                        # L2 [paper]
        kl = (-0.5 * (1 + lv - mu**2 - lv.exp()).sum(1)).clamp(min=C.KL_TOLERANCIA * C.Z).mean()
        return r + kl, r, kl

class MDNRNN(nn.Module):
    """Apéndice A.2: LSTM + mezcla de 5 gaussianas diagonales para z_{t+1}, y logit de «muere» (done)."""
    def __init__(self, z=C.Z, h=C.RNN_H, k=C.MEZCLAS):
        super().__init__()
        self.z, self.k = z, k
        self.lstm = nn.LSTM(z + 2, h, batch_first=True)      # entrada: z_t, a_t, bandera de reinicio [código Ha]
        self.out = nn.Linear(h, z * k * 3 + 1)
    def forward(self, z, a, reinicio, estado=None):
        x = torch.cat([z, a.unsqueeze(-1), reinicio.unsqueeze(-1)], -1)
        y, estado = self.lstm(x, estado)
        o = self.out(y)
        muerte = o[..., 0]
        o = o[..., 1:].reshape(*o.shape[:-1], self.z, self.k, 3)
        logpi = F.log_softmax(o[..., 0], -1)
        return logpi, o[..., 1], o[..., 2], muerte, estado      # logpi, mu, logsigma: (..., z, k)
    @staticmethod
    def nll(logpi, mu, logs, z1):
        lp = -0.5 * ((z1.unsqueeze(-1) - mu) / logs.exp()) ** 2 - logs - 0.5 * math.log(2 * math.pi)
        return -torch.logsumexp(logpi + lp, -1)                   # (..., z)
    @staticmethod
    def muestrea(logpi, mu, logs, tau, gen=None):
        """Muestreo con temperatura como en DoomCoverRNNEnv de Ha: pesos de mezcla ^(1/τ), ruido * sqrt(τ)."""
        p = F.softmax(logpi / tau, -1)
        idx = torch.multinomial(p.reshape(-1, p.shape[-1]), 1, generator=gen).view(*p.shape[:-1], 1)
        m = mu.gather(-1, idx).squeeze(-1); s = logs.gather(-1, idx).squeeze(-1).exp()
        ruido = torch.randn(m.shape, generator=gen, device=m.device)
        return m + s * ruido * math.sqrt(tau)

N_PARAM_C = C.Z + 2 * C.RNN_H     # 1,088

def accion(W, z, c, h):
    """W: (B, 1088). Devuelve a ∈ [-1,1] (B,)."""
    return torch.tanh((W * torch.cat([z, c, h], -1)).sum(-1))
