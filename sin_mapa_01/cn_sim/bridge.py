"""Modelo del puente doble (Deneubourg 1990 / Goss 1989), versión didáctica.

Cada rama se divide en celdas. Las hormigas caminan por la rama y dejan
olor en las celdas que pisan, de ida y de vuelta. En cada extremo eligen
rama con la regla de Deneubourg:  P = (k+A)^h / ((k+A)^h + (k+B)^h),
donde A y B son el olor junto a la bifurcación. Se simulan R corridas
independientes a la vez (vectorizado); la corrida 0 es la que se dibuja.
"""
import numpy as np

NEST, OUT, FOOD, BACK = 0, 1, 2, 3


class BridgeModel:
    def __init__(self, n_ants=100, ratio=1.0, runs=20, k=20.0, h=2.0,
                 deposit=1.0, evap=0.0, seed=1, cells_short=60,
                 cross_time=30.0, rest_mean=40.0, short_closed=False,
                 per_length=False):
        self.rng = np.random.default_rng(seed)
        self.R = runs
        self.k, self.h, self.deposit, self.evap = k, h, deposit, evap
        self.cross_time = cross_time      # s simulados para cruzar la rama corta
        self.rest_mean = rest_mean
        self.short_closed = short_closed  # rama 0 (arriba) cerrada (la trampa)
        # per_length: versión «de computadora»: cada viaje lleva la misma
        # cantidad de olor, así que en la rama larga queda más diluido.
        self.per_length = per_length
        self.set_ratio(ratio, reset=False)
        self.n_ants = int(n_ants)
        self.cells_short = cells_short
        self.reset()

    # ---------------------------------------------------------------
    def set_ratio(self, ratio, reset=True):
        self.ratio = float(ratio)
        if reset:
            self.reset()

    def reset(self):
        R, N = self.R, self.n_ants
        self.ncell = np.array([self.cells_short,
                               int(round(self.cells_short * self.ratio))])
        self.maxc = int(self.ncell.max())
        # olor: [corrida, rama, celda]
        self.ph = np.zeros((R, 2, self.maxc))
        self.state = np.full((R, N), NEST)
        self.branch = np.zeros((R, N), dtype=int)
        self.pos = np.zeros((R, N))          # en celdas
        self.timer = self.rng.exponential(self.rest_mean, (R, N)) * \
            self.rng.uniform(0.05, 1.0, (R, N))
        self.t = 0.0
        # historial de elecciones en el nido: (t, rama) por corrida
        self.choices = [[] for _ in range(R)]
        self.total_choices = np.zeros((R, 2))
        self.opened_at = None

    def set_n_ants(self, n):
        n = int(n)
        if n == self.n_ants:
            return
        R = self.R
        if n > self.n_ants:
            extra = n - self.n_ants
            self.state = np.concatenate([self.state, np.full((R, extra), NEST)], 1)
            self.branch = np.concatenate([self.branch, np.zeros((R, extra), int)], 1)
            self.pos = np.concatenate([self.pos, np.zeros((R, extra))], 1)
            self.timer = np.concatenate(
                [self.timer, self.rng.uniform(0, self.rest_mean * 2, (R, extra))], 1)
        else:
            self.state = self.state[:, :n]
            self.branch = self.branch[:, :n]
            self.pos = self.pos[:, :n]
            self.timer = self.timer[:, :n]
        self.n_ants = n

    def open_short(self):
        self.short_closed = False
        self.opened_at = self.t

    # ---------------------------------------------------------------
    def _choose(self, A, B, mask):
        """Devuelve rama elegida (0/1) para las hormigas en mask."""
        k, h = self.k, self.h
        a = (k + A) ** h
        b = (k + B) ** h
        p0 = a / (a + b)
        if self.short_closed:
            p0 = np.zeros_like(p0)
        r = self.rng.random(p0.shape)
        return np.where(r < p0, 0, 1)

    def step(self, dt):
        R, N = self.R, self.n_ants
        speed = self.cells_short / self.cross_time   # celdas por segundo
        self.t += dt
        st, br, pos = self.state, self.branch, self.pos
        rr = np.repeat(np.arange(R)[:, None], N, 1)

        # olor junto a cada extremo (promedio de 3 celdas)
        nest_end = self.ph[:, :, :3].mean(-1)                 # (R,2)
        far = np.stack([self.ph[:, 0, self.ncell[0] - 3:self.ncell[0]].mean(-1),
                        self.ph[:, 1, self.ncell[1] - 3:self.ncell[1]].mean(-1)], 1)

        # 1) hormigas en el nido que salen
        self.timer -= dt
        leaving = (st == NEST) & (self.timer <= 0)
        if leaving.any():
            A = np.broadcast_to(nest_end[:, 0:1], (R, N))
            B = np.broadcast_to(nest_end[:, 1:2], (R, N))
            ch = self._choose(A, B, leaving)
            br[leaving] = ch[leaving]
            st[leaving] = OUT
            pos[leaving] = 0.0
            for r_i in np.nonzero(leaving.any(1))[0]:
                c = ch[r_i][leaving[r_i]]
                n1 = int(c.sum()); n0 = len(c) - n1
                self.total_choices[r_i, 0] += n0
                self.total_choices[r_i, 1] += n1
                self.choices[r_i].append((self.t, n0, n1))
        # 2) hormigas en la comida que regresan
        at_food = (st == FOOD) & (self.timer <= 0)
        if at_food.any():
            A = np.broadcast_to(far[:, 0:1], (R, N))
            B = np.broadcast_to(far[:, 1:2], (R, N))
            ch = self._choose(A, B, at_food)
            br[at_food] = ch[at_food]
            st[at_food] = BACK
            pos[at_food] = self.ncell[ch[at_food]] - 1e-3

        # 3) caminar y dejar olor
        moving = (st == OUT) | (st == BACK)
        step = speed * dt
        old = pos.copy()
        pos[st == OUT] += step
        pos[st == BACK] -= step
        if moving.any():
            nc = self.ncell[br]
            cell = np.clip(np.floor(pos), 0, nc - 1).astype(int)
            # deposita proporcional a lo avanzado (celdas cruzadas)
            amt = self.deposit * (np.abs(pos - old))
            if self.per_length:
                amt = amt * (self.cells_short / nc)
            np.add.at(self.ph, (rr[moving], br[moving], cell[moving]), amt[moving])
        arrived = (st == OUT) & (pos >= self.ncell[br])
        st[arrived] = FOOD
        self.timer[arrived] = self.rng.uniform(1.0, 4.0, arrived.sum())
        home = (st == BACK) & (pos <= 0)
        st[home] = NEST
        self.timer[home] = self.rng.exponential(self.rest_mean, home.sum())

        # 4) evaporación (fracción por minuto)
        if self.evap > 0:
            self.ph *= (1.0 - self.evap) ** (dt / 60.0)
        # celdas inexistentes de la rama corta siempre en cero
        if self.ncell[0] < self.maxc:
            self.ph[:, 0, self.ncell[0]:] = 0
        if self.ncell[1] < self.maxc:
            self.ph[:, 1, self.ncell[1]:] = 0

    # ---------------------------------------------------------------
    def share(self, window=300.0):
        """Fracción de salidas por la rama 0 en la ventana reciente, por corrida."""
        out = np.full(self.R, 0.5)
        for r in range(self.R):
            n0 = n1 = 0
            for (t, a, b) in reversed(self.choices[r]):
                if t < self.t - window:
                    break
                n0 += a; n1 += b
            if n0 + n1 > 0:
                out[r] = n0 / (n0 + n1)
        return out

    def trim_history(self, keep=900.0):
        for r in range(self.R):
            c = self.choices[r]
            i = 0
            while i < len(c) and c[i][0] < self.t - keep:
                i += 1
            if i:
                del c[:i]
