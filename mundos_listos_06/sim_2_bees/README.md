# Selección de nido — abejas (Seeley / Passino)

**Referencias:**

- Seeley, T. D. & Visscher, P. K. (2003, 2004, 2012).
- Passino, K. M., Seeley, T. D. & Visscher, P. K. (2003). *Swarm Cognition in Honey Bees*.

## Modelo (ilustrativo continuo)

Defensores/apoyadores por sitio \(A_i\) con calidad \(Q_i\):

\[
\frac{dA_i}{dt} = k_r \cdot d_i \cdot Q_i - \delta A_i - \sum_{j\neq i} k_s \cdot \mathrm{stop}_{j\to i}
\]

- **Exploradoras** (`N_SCOUT=56`): ida a sitio, retorno activa danza `d_i`.
- **Enjambre** (`N_SWARM=1400`): partículas reclutadas según \(A_i\).
- **Quórum** `QUORUM=28` en sitio 0 → migración colectiva.
- Parámetros: `k_r=0.085`, `δ=0.012`, `k_s=0.034`; calidades \(Q \in \{0.92,0.58,0.48,0.40\}\).