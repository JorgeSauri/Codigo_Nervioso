# Lenia (Chan 2019)

**Referencia:** Chan, L. (2019). *Lenia: Biology of Artificial Life*. Complex Systems 28(3), 251–286.

## Ecuación

\[
\frac{\partial u}{\partial t} = G_\sigma(K * u) \cdot u
\]

- \(K\): kernel en anillo con parámetro \(R\) (polinomio tipo \(e^{4 - 4/(r(1-r))}\)).
- \(G_\sigma\): crecimiento gaussiano \(2\exp(-(u-\mu)^2/(2\sigma^2)) - 1\).

## Especies (Chakazul / Lenia animals)

| Especie | R | T | μ | σ |
|---------|---|---|---|---|
| Orbium (`unicaudatus`) | 26 | 10 | 0.15 | 0.015 |
| Aerogeminium (`3GA2v`) | 22 | 10 | 0.195 | 0.0198 |

`dt = 1/T`. Convención **stepSpecies**: convolución y crecimiento por canal (sin mezcla cruzada).