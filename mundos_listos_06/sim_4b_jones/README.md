# Physarum por agentes — Jones (2010)

**Referencia:** Jones, J. (2010). *Characteristics of pattern formation and evolution in approximations of Physarum transport networks*. Artificial Life **16**(2), 127–153.

## Agente

Dos sensores laterales a distancia **SO=9** y ángulo **SA=45°**. Rotación **RA=45°** hacia el lado cuya muestra supera a la frontal.

- **N = 80000** agentes en `Float32Array` (posiciones continuas, sin retícula RGBA8).
- Depósito **bilineal** (suma real de 4 taps) sobre un trail `Float32` de `480×270`, luego difusión a 4 vecinos y decaimiento.
- Decaimiento `0.94`, difusión `0.2`, depósito `0.26`, velocidad `1.05`.
- Tres fuentes de feromona. 90 pasos de calentamiento.