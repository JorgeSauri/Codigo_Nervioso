# Boids (Reynolds 1987)

**Referencia:** Reynolds, C. W. (1987). *Flocks, herds and schools: A distributed behavioral model*. SIGGRAPH / *Computer Graphics* 21(4).

## Fuerzas locales

1. **Separación** — alejarse de vecinos a distancia \(< d_0 = 20\).
2. **Alineación** — igualar velocidad media en radio \(d = 48\).
3. **Cohesión** — acercarse al centroide local.

Pesos: \(w_{\mathrm{sep}}=1.5\), \(w_{\mathrm{ali}}=1.0\), \(w_{\mathrm{coh}}=1.0\).  
\(N=4000\), vecindad \(d=36\), \(d_0=12\), \(v_{\max}=3.4\), fuerza limitada a `0.09`. Hash espacial.