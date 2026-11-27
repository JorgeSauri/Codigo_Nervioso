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
- **Quórum** `QUORUM=26` en el sitio de mayor calidad → la nube densa despega y migra.
- Las danzas en 8 miden unos 14 px y se dibujan sobre el enjambre; el quórum se lee en el arco de cada sitio.
- Parámetros: `k_r=0.016`, `δ=0.012`, `k_s=0.034`; calidades \(Q \in \{0.92,0.58,0.48,0.40\}\).
- Cada retorno de exploradora suma `0.45·Q` a la danza y `0.1·Q` a \(A_i\).