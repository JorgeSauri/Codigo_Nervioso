# Conway — Juego de la vida (B3/S23)

**Referencia:** Conway (1970); Gardner (1970) *Scientific American* 223(4), 120–123.

## Reglas

Para cada celda con 8 vecinos de Moore:

- **Nacimiento:** celda muerta → viva si exactamente **3** vecinos vivos.
- **Supervivencia:** celda viva permanece si tiene **2 o 3** vecinos vivos; en caso contrario muere.

## Implementación

- Rejilla toroidal `240×180`, un paso de tiempo = una generación sincrónica.
- Semillas: pistola de Gosper, LWSS, planeador y bellota (matusalén). Bordes abiertos. Rejilla `220×130`.