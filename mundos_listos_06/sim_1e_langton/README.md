# Autómata celular de Langton (1984)

**Referencia:** Langton, C. G. (1984). *Self-reproduction in cellular automata*. Physica D **10**, 135–144.

## Regla

Vecinos von Neumann `(c, N, E, S, W)` → estado siguiente según la **tabla de transición** completa de Langton (reproducida en `comun/langton-rules.js`, fuente Golly/diga.me.uk).

## Condición inicial

Configuración estándar (`14×10`) en rejilla abierta `180×120`. Seis generaciones por fotograma para que la colonia de copias sea visible.