# Primordial Particle System (Schmickl, Stefanec & Crailsheim 2016)

**Referencia:** Schmickl, T., Stefanec, M. & Crailsheim, K. (2016). *How a life-like system emerges from a simplistic particle motion law*. Sci. Rep. **6**, 37969.

## Ley de movimiento

Cada partícula cuenta vecinos a distancia \(\le r\): \(L\) a la izquierda y \(R\) a la derecha de su rumbo. \(N = L + R\).

\[
\Delta\phi = \alpha + \beta \, N \, \mathrm{sign}(R - L)
\]

Un \(\Delta\phi\) positivo es un giro a la derecha. Después avanza \(v\) con el rumbo nuevo. La actualización es **asíncrona** (cada partícula gira y se mueve antes de que la siguiente mida) en un toro.

Con \(\alpha = 180°\), una partícula aislada (\(N = 0\)) invierte el rumbo cada paso y queda oscilando en el sitio.

## Parámetros canónicos

- \(\alpha = 180°\), \(\beta = 17°\), \(r = 5\), \(v = 0.67\)
- Densidad \(\rho = 0.08\) partículas por unidad de área (umbral en el que el paper ve células) en un dominio `180×100` → \(N = 1440\)
- 6500 pasos de calentamiento y 5 subpasos por fotograma

## Color por número de vecinos (figuras del paper)

| \(N\) | Color | Papel |
|------:|-------|-------|
| \(> 35\) | amarillo | núcleo |
| \(15 < N \le 35\) | azul | cuerpo de la célula |
| \(13 \le N \le 15\) | marrón | membrana / espora |
| resto | verde | nutriente libre |
