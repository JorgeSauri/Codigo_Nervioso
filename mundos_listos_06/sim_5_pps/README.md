# Primordial Particle System (Schmickl 2016)

**Referencia:** Schmickl, T. et al. (2016). *Collective perception and decision-making in a robot swarm*. Sci. Rep. **6**, 37969.

## Reglas en vecindad radio \(r\)

Conteos izquierda/derecha en sector frontal; actualización de rumbo:

| Condición | Δθ |
|-----------|-----|
| solo derecha | \(-\alpha\) |
| solo izquierda | \(+\alpha\) |
| ambos | \((n_R - n_L)\,\beta\) |

## Parámetros canónicos

- \(\alpha = 180°\) (`Math.PI`)
- \(\beta = 17°\)
- \(r = 5\), \(v = 0.67\)
- \(N \approx 0.09 \times W \times H\) en dominio `280×280`