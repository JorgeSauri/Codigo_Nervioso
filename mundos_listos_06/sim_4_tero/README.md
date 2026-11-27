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

Presiones por iteración de Jacobi con fuentes/sumideros alternados en nodos del área metropolitana de Tokio/Kanto (`n=16`).

## Parámetros

| Símbolo | Valor |
|---------|-------|
| μ | 1.8 |
| I₀ | 0.14 |
| Δt | 0.22 |
| QSCALE | 180 (escala numérica del flujo) |
| \(D_e(0)\) | 0.38 (lámina inicial uniforme) |