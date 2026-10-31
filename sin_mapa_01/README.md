# Estigmergia · simulador del episodio 1

Simulador del episodio **«Estigmergia: la inteligencia que no vive en ninguna cabeza»** del canal [Código Nervioso](https://www.youtube.com/@CodigoNervioso):

https://youtu.be/GXSB_aicVWg

Muestra, en una ventana de 1920×1080, cómo un rastro de olor puede coordinar a muchas hormigas sin que el plan viva en ninguna de ellas. Sirve para usarlo en vivo o para volver a grabar las tomas del video.

El modelo del puente está en `cn_sim/bridge.py`, las colonias del agente viajero en `cn_sim/tsp.py`, la interfaz en `cn_sim/ui.py` y las escenas en `cn_sim/scenes.py`.

## Qué muestra cada escena

Las teclas `1` a `9` cambian de escena. Con `--escena` se usa la clave de la derecha.

| Tecla | Clave | Qué se ve |
| --- | --- | --- |
| 1 | `sim1` | Puente doble con dos ramas iguales. El nido está a la izquierda y al otro lado hay una zona nueva, sin comida. |
| 2 | `sim2` | La misma idea, con comida al otro lado y una rama más larga que la otra. |
| 3 | `sim3` | La trampa: primero solo existe la rama larga; a los 30 minutos se abre la corta. |
| 4 | `sim4` | El agente viajero. 30 ciudades. Se puede seguir a una sola hormiga y después a la colonia. |
| 5 | `sim5a` | La trampa otra vez, ahora con evaporación. La pantalla la marca como versión de computadora. |
| 6 | `sim5b` | Cinco colonias iguales en el mapa. Solo cambia cuánto olor se borra; a mitad del camino el mapa cambia. |
| 7 | `sim6` | Ant System, Ant Colony System y MAX–MIN, las tres sobre el mismo mapa. |
| 8 | `sim6b` | Una ruta con cruces. Cada clic reacomoda un cruce y el recorrido se acorta. |
| 9 | `juguemos` | Todas las perillas del agente viajero a la vez, y un botón para cambiar el mapa. |

## Qué modela cada escena

* **Puente (1–3, 5):** 20 colonias a la vez (la grande es la nº 1). Cada hormiga elige rama con la regla de Deneubourg (k = 20, «Fuerza del olor» = exponente h: suave 1, normal 2). El olor se deja por tramo al ir y al volver, así que en la rama corta se refuerza antes. Los datos reales de Goss et al. (1989) se muestran aparte y rotulados.
* **Escena 5 (trampa con evaporación):** versión de computadora: cada viaje deja la misma cantidad total de olor repartida en toda la rama (la larga queda más diluida). Con el modelo de hormiga real la colonia no cambia de rama ni con evaporación, por eso esta escena dice «versión de computadora».
* **Agente viajero (4, 6, 9):** Ant System con α = 1, β = 5, evaporación 50 %, m = n hormigas (Dorigo, Maniezzo & Colorni 1996). 30 ciudades.
* **Escena 7:** Ant System, ACS (β = 2, ρ = 0.1, m = 10, q0 = 0.9, φ = 0.1) y MAX–MIN (β = 2, ρ = 0.02, m = n), valores de Stützle et al. (2011), tabla 8.2.
* **Escena 8:** 2-opt simple (quitar un cruce). ACS usó una variante restringida de 3-opt.
* Todos los números en pantalla salen de la simulación, no de experimentos.

## Instalación

Desde la raíz del repositorio:

```bash
cd sin_mapa_01
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

`requirements.txt` pide pygame-ce y numpy. Las fuentes (licencia OFL) están en `fonts/` y el logo en `assets/logo_marca.png`.

## Uso en vivo

```bash
.venv/bin/python simulador.py               # ventana ajustada a la pantalla
.venv/bin/python simulador.py --full        # pantalla completa 1920×1080
.venv/bin/python simulador.py --escena sim4 # empezar en una escena
```

| Tecla | Acción |
| --- | --- |
| 1 … 9 | Cambiar de escena (ver la tabla de arriba) |
| Ratón | Mover perillas y pulsar botones |
| Espacio | Pausa |
| R | Reiniciar |
| O | En la escena 4, una sola hormiga paso a paso |
| F | Pantalla completa o ventana |
| Esc | Salir |

Para grabar en vivo la pantalla, usa OBS sobre la ventana en modo `--full`.

## Grabar las tomas

Hace falta [ffmpeg](https://ffmpeg.org/) en el PATH. `grabar.py` no abre una ventana: manda los cuadros directo a ffmpeg (H.264, 1920×1080, yuv420p, CRF 18). Los MP4 quedan en `salida/`, dentro de esta carpeta.

```bash
.venv/bin/python grabar.py                  # todas las tomas → salida/
.venv/bin/python grabar.py sim02 juguemos   # solo algunas
.venv/bin/python grabar.py --fps 30 sim01
```

| Argumento | Archivo en `salida/` |
| --- | --- |
| `sim01` | `sim01_puente_iguales.mp4` |
| `sim02` | `sim02_puente_desigual.mp4` |
| `sim03` | `sim03_trampa.mp4` |
| `sim04` | `sim04_ant_system.mp4` |
| `sim05a` | `sim05a_evaporacion_puente.mp4` |
| `sim05b` | `sim05b_evaporacion_mapa_cambia.mp4` |
| `sim06` | `sim06_as_acs_mmas.mp4` |
| `sim06b` | `sim06b_destorcer.mp4` |
| `juguemos` | `sim07_juguemos.mp4` |

Cada toma está escrita en `grabar.py` (`take_sim01`, …). El cursor se ve, se mueve y arrastra las perillas poco a poco. Para cambiar la coreografía, edita esas funciones (`r.drag("evap", 0.4, 2.5)`, `r.click("reiniciar")`, `r.wait(10)`).

## Licencia

Código bajo CC0 1.0 (dominio público). El texto legal completo está en [LICENSE](../LICENSE), en la raíz del repositorio.

Las fuentes tipográficas en `fonts/` (Inter, Space Grotesk y JetBrains Mono) siguen con la licencia SIL Open Font License 1.1 y no son CC0. Sus textos son `fonts/OFL-Inter.txt`, `fonts/OFL-SpaceGrotesk.txt` y `fonts/OFL-JetBrainsMono.txt`.
