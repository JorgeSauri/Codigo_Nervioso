"""Colonias de hormigas para el agente viajero: Ant System, ACS y MAX–MIN.

Valores por defecto:
  * Ant System (Dorigo, Maniezzo y Colorni 1996, pp. 32–35): α=1, β=5,
    persistencia 0.5 (evaporación 0.5), Q=100, m = número de ciudades.
  * ACS y MAX–MIN (Stützle et al. 2011, Tabla 8.2, p. 204, sin búsqueda
    local): ACS β=2, ρ=0.1, m=10, q0=0.9; MMAS β=2, ρ=0.02, m=n.
  * Lo que no viene en esa tabla (τ0, ξ/φ=0.1, límites de MMAS) sigue los
    valores usuales de ACOTSP / Dorigo y Stützle.
Aquí «evap» siempre es la fracción de olor que se borra en cada ronda.
"""
import numpy as np


def make_cities(n=30, seed=7, w=100.0, h=62.0, min_sep=7.0):
    rng = np.random.default_rng(seed)
    pts = []
    while len(pts) < n:
        p = rng.uniform([4, 4], [w - 4, h - 4])
        if all(np.hypot(*(p - q)) >= min_sep for q in pts):
            pts.append(p)
    return np.array(pts)


def tour_length(tour, D):
    return float(D[tour, np.roll(tour, -1)].sum())


def nearest_neighbor(D, start=0):
    n = len(D)
    tour = [start]
    left = set(range(n)) - {start}
    while left:
        c = tour[-1]
        nxt = min(left, key=lambda j: D[c, j])
        tour.append(nxt); left.remove(nxt)
    return np.array(tour)


def two_opt(tour, D, max_pass=50):
    tour = tour.copy(); n = len(tour)
    for _ in range(max_pass):
        improved = False
        for i in range(n - 1):
            for j in range(i + 2, n if i > 0 else n - 1):
                a, b = tour[i], tour[i + 1]
                c, d = tour[j], tour[(j + 1) % n]
                if D[a, c] + D[b, d] < D[a, b] + D[c, d] - 1e-9:
                    tour[i + 1:j + 1] = tour[i + 1:j + 1][::-1]
                    improved = True
        if not improved:
            break
    return tour


def best_known(D, tries=60, seed=0):
    rng = np.random.default_rng(seed)
    n = len(D); best = None
    for _ in range(tries):
        t = two_opt(rng.permutation(n), D)
        # perturbación doble-puente + 2-opt
        for _ in range(30):
            i, j, k = sorted(rng.choice(np.arange(1, n), 3, replace=False))
            t2 = np.concatenate([t[:i], t[j:k], t[i:j], t[k:]])
            t2 = two_opt(t2, D)
            if tour_length(t2, D) < tour_length(t, D):
                t = t2
        if best is None or tour_length(t, D) < tour_length(best, D):
            best = t
    return best


class Colony:
    ALGOS = ("AS", "ACS", "MMAS")

    def __init__(self, cities, algo="AS", seed=0, **kw):
        self.xy = np.asarray(cities, float)
        self.n = len(self.xy)
        d = self.xy[:, None, :] - self.xy[None, :, :]
        self.D = np.hypot(d[..., 0], d[..., 1])
        np.fill_diagonal(self.D, 1e-9)
        self.eta = 1.0 / self.D
        np.fill_diagonal(self.eta, 0)
        self.Lnn = tour_length(nearest_neighbor(self.D), self.D)
        self.rng = np.random.default_rng(seed)
        self.algo = algo
        self.set_defaults(algo)
        for k, v in kw.items():
            setattr(self, k, v)
        self.reset()

    def set_defaults(self, algo):
        n = self.n
        self.alpha = 1.0
        self.Q = 100.0
        if algo == "AS":
            self.beta, self.evap, self.m, self.q0, self.phi = 5.0, 0.5, n, 0.0, 0.0
        elif algo == "ACS":
            self.beta, self.evap, self.m, self.q0, self.phi = 2.0, 0.1, 10, 0.9, 0.1
        elif algo == "MMAS":
            self.beta, self.evap, self.m, self.q0, self.phi = 2.0, 0.02, n, 0.0, 0.0

    def set_cities(self, cities):
        """Cambia el mapa conservando el olor (para ver si la colonia se adapta)."""
        self.xy = np.asarray(cities, float)
        d = self.xy[:, None, :] - self.xy[None, :, :]
        self.D = np.hypot(d[..., 0], d[..., 1])
        np.fill_diagonal(self.D, 1e-9)
        self.eta = 1.0 / self.D
        np.fill_diagonal(self.eta, 0)
        self.Lnn = tour_length(nearest_neighbor(self.D), self.D)
        self.best_tour = None
        self.best_len = np.inf

    def reset(self):
        n = self.n
        if self.algo == "AS":
            self.tau0 = self.m / self.Lnn
        elif self.algo == "ACS":
            self.tau0 = 1.0 / (n * self.Lnn)
        else:
            self.tau0 = 1.0 / (max(self.evap, 1e-3) * self.Lnn)
        self.tau = np.full((n, n), self.tau0)
        np.fill_diagonal(self.tau, 0)
        self.it = 0
        self.best_tour = None
        self.best_len = np.inf
        self.hist_best = []      # mejor hasta ahora
        self.hist_iter = []      # mejor de la ronda
        self.last_tours = None
        self.last_lens = None

    # ------------------------------------------------------------
    def weights(self):
        return (self.tau ** self.alpha) * (self.eta ** self.beta)

    def probs_from(self, city, visited):
        w = self.weights()[city].copy()
        w[list(visited)] = 0
        s = w.sum()
        return w / s if s > 0 else w

    def construct(self):
        n, m = self.n, int(max(1, round(self.m)))
        tours = np.zeros((m, n), dtype=int)
        tours[:, 0] = self.rng.integers(0, n, m)
        visited = np.zeros((m, n), bool)
        visited[np.arange(m), tours[:, 0]] = True
        W = self.weights()
        for s in range(1, n):
            cur = tours[:, s - 1]
            w = W[cur] * (~visited)
            w = np.maximum(w, 0)
            tot = w.sum(1, keepdims=True)
            # si todo es cero (olor nulo) elegir al azar entre no visitadas
            zero = tot[:, 0] <= 0
            if zero.any():
                w[zero] = (~visited[zero]).astype(float)
                tot = w.sum(1, keepdims=True)
            p = w / tot
            r = self.rng.random((m, 1))
            nxt = (p.cumsum(1) < r).sum(1)
            nxt = np.minimum(nxt, n - 1)
            # corrige si cayó en visitada por redondeo
            bad = visited[np.arange(m), nxt]
            if bad.any():
                nxt[bad] = np.argmax(p[bad], 1)
            if self.q0 > 0:
                greedy = self.rng.random(m) < self.q0
                if greedy.any():
                    nxt[greedy] = np.argmax(w[greedy], 1)
            tours[:, s] = nxt
            visited[np.arange(m), nxt] = True
            if self.algo == "ACS" and self.phi > 0:
                a, b = cur, nxt
                self.tau[a, b] = (1 - self.phi) * self.tau[a, b] + self.phi * self.tau0
                self.tau[b, a] = self.tau[a, b]
                W[a, :] = (self.tau[a, :] ** self.alpha) * (self.eta[a, :] ** self.beta)
                W[b, :] = (self.tau[b, :] ** self.alpha) * (self.eta[b, :] ** self.beta)
        if self.algo == "ACS" and self.phi > 0:
            a, b = tours[:, -1], tours[:, 0]
            self.tau[a, b] = (1 - self.phi) * self.tau[a, b] + self.phi * self.tau0
            self.tau[b, a] = self.tau[a, b]
        return tours

    def _deposit(self, tour, amount):
        a, b = tour, np.roll(tour, -1)
        np.add.at(self.tau, (a, b), amount)
        np.add.at(self.tau, (b, a), amount)

    def iterate(self):
        tours = self.construct()
        lens = self.D[tours, np.roll(tours, -1, 1)].sum(1)
        ib = int(np.argmin(lens))
        if lens[ib] < self.best_len:
            self.best_len = float(lens[ib]); self.best_tour = tours[ib].copy()
        ev = self.evap
        if self.algo == "AS":
            self.tau *= (1 - ev)
            for t, L in zip(tours, lens):
                self._deposit(t, self.Q / L)
        elif self.algo == "ACS":
            t = self.best_tour; a, b = t, np.roll(t, -1)
            self.tau[a, b] = (1 - ev) * self.tau[a, b] + ev / self.best_len
            self.tau[b, a] = self.tau[a, b]
        else:  # MMAS
            self.tau *= (1 - ev)
            use_best = (self.it % 10 == 9)
            t, L = (self.best_tour, self.best_len) if use_best else (tours[ib], lens[ib])
            self._deposit(t, 1.0 / L)
            tmax = 1.0 / (max(ev, 1e-3) * self.best_len)
            pdec = 0.05 ** (1.0 / self.n)
            tmin = tmax * (1 - pdec) / ((self.n / 2 - 1) * pdec)
            np.clip(self.tau, tmin, tmax, out=self.tau)
            np.fill_diagonal(self.tau, 0)
        self.it += 1
        self.hist_best.append(self.best_len)
        self.hist_iter.append(float(lens[ib]))
        self.last_tours, self.last_lens = tours, lens
        return tours, lens
