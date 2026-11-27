# Gray–Scott (Pearson 1993)

**Referencia:** Pearson, J. E. (1993). *Science* **261**, 189–192.

## Ecuaciones

\[
\frac{\partial u}{\partial t} = D_u \nabla^2 u - uv^2 + f(1-u)
\]
\[
\frac{\partial v}{\partial t} = D_v \nabla^2 v + uv^2 - (f+k)v
\]

## Parámetros (régimen «spots»)

| Parámetro | Valor |
|-----------|-------|
| \(D_u\) | 0.16 |
| \(D_v\) | 0.08 |
| \(f\) | 0.018 |
| \(k\) | 0.055 |

Rejilla `320×320`, Laplaciano 5-puntos, `Δt = 1`, 6 sub-pasos por fotograma.