# Código Nervioso

Simuladores del canal de YouTube de divulgación científica [Código Nervioso](https://www.youtube.com/@CodigoNervioso), de Jorge Sauri.

El canal explica ciencia de datos, inteligencia artificial, bioinspiración y cognición artificial con simulaciones hechas para cada episodio. Este repositorio guarda esas simulaciones: se pueden abrir en vivo o volver a grabar las tomas del video.

- Canal: https://www.youtube.com/@CodigoNervioso

## Episodios

| Carpeta | Episodio | Video |
| --- | --- | --- |
| [sin_mapa_01](sin_mapa_01/) | Estigmergia: la inteligencia que no vive en ninguna cabeza | https://youtu.be/GXSB_aicVWg |
| [el_pavo_02](el_pavo_02/) | La trampa de las criptomonedas: el dilema del pavo | Se estrena el 5 de noviembre de 2026 |
| [el_sueno_03](el_sueno_03/) | Una IA que aprendió a jugar Doom soñando | Se estrena el 12 de noviembre de 2026 |

## Convención de carpetas

Cada episodio tiene su propia carpeta. El nombre es corto, describe el tema y termina con el número del episodio en dos dígitos (`sin_mapa_01`, `el_pavo_02`). No se usa el prefijo `ep01`.

## Requisitos generales

- Python 3
- Un entorno virtual (`python3 -m venv .venv`) dentro de la carpeta de cada episodio
- Las bibliotecas de cada simulador, en su `requirements.txt` (episodio 1: pygame-ce y numpy; episodio 2: además scipy, powerlaw, arch, pandas y xlrd)
- [ffmpeg](https://ffmpeg.org/) solamente para grabar las tomas a MP4

Entra a la carpeta del episodio y sigue el README de ahí.

## Licencia

Código bajo CC0 1.0 (dominio público). El texto legal completo está en [LICENSE](LICENSE).

Las fuentes tipográficas en `sin_mapa_01/fonts/`, `el_pavo_02/fonts/` y `el_sueno_03/fuentes/` (Inter, Space Grotesk y JetBrains Mono) siguen con la licencia SIL Open Font License 1.1 y no son CC0. El texto de cada una está junto a los archivos: `OFL-Inter.txt`, `OFL-SpaceGrotesk.txt` y `OFL-JetBrainsMono.txt`.

Los datos de Shiller que usa la escena S6c de `el_pavo_02` no están en el repositorio: el programa los descarga de shillerdata.com la primera vez.
