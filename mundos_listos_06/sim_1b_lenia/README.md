# Lenia (Chan 2019)

**Referencia:** Chan, L. (2019). *Lenia: Biology of Artificial Life*. Complex Systems 28(3), 251–286.

## Ecuación

\[
\frac{\partial u}{\partial t} = G_\sigma(K * u) \cdot u
\]

- \(K\): núcleo en anillo de Chan, bump \(e^{4 - 1/(x(1-x))}\) sobre cada capa de \(\beta\). Orbium usa \(\beta=[1]\) (pico en \(r=1/2\)).
- \(G_\sigma\): crecimiento gaussiano \(2\exp(-(u-\mu)^2/(2\sigma^2)) - 1\).

## Especies (Chakazul / Lenia animals)

| Especie | R | T | μ | σ | β |
|---------|---|---|---|---|---|
| Orbium unicaudatus | 13 | 10 | 0.15 | 0.015 | [1] |
| Aerogeminium vagus | 18 | 10 | 0.195 | 0.0198 | [0.75, 1, 0.5] |

Semillas: RLE de `animals.json` (Chakazul), decodificadas en `comun/lenia-seeds.js`.

`dt = 1/T`. Convención **stepSpecies**: convolución y crecimiento por canal (sin mezcla cruzada).