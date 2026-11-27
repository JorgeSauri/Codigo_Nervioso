# Red Physarum — Tero et al. (2010)

**Referencia:** Tero, A. et al. (2010). *Rules for Biologically Inspired Adaptive Network Design*. *Science* **327**, 439–442.

## Dinámica de conductancia

\[
\frac{dD_e}{dt} = |Q_e|^{\mu} + I_0 - D_e
\]

Flujo Poiseuille en arista \(e=(a,b)\):

\[
Q_e = \frac{D_e}{L_e}(p_a - p_b)
\]

Malla 14×9 (126 nodos, 8-vecinos) sobre el área de Kanto. Corriente fija \(I=5\) entre pares de ciudades (nodo de comida más cercano). Presión por Jacobi.

## Parámetros

| Símbolo | Valor |
|---------|-------|
| μ | 1.5 |
| I₀ | 0.012 |
| Δt | 0.2 |
| I (corriente) | 5 |
| \(D_e(0)\) | 0.45 (malla densa) |

Al final del clip se superpone un esquema punteado de la red ferroviaria con la leyenda «esquema aproximado». Ese trazo no modifica \(D\).