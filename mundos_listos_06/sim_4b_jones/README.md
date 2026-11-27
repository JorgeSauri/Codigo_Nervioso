# Physarum por agentes — Jones (2010)

**Referencia:** Jones, J. (2010). *Characteristics of pattern formation and evolution in approximations of Physarum transport networks*. Artificial Life **16**(2), 127–153.

## Agente

Dos sensores laterales a distancia **SO=9** y ángulo **SA=45°**. Rotación **RA=0.3** rad hacia el lado con mayor quimio.

- Depósito en feromona/trail: incremento `1/Dt` con **Dt=20**.
- Decaimiento global: multiplicador `1 - 1/Dt` por paso.
- Velocidad **2.2** px/step, **N=420** agentes, rejilla `280×200`.
- Tres fuentes de feromona fijas (comida).