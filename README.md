# Código Nervioso

Simuladores del canal de YouTube de divulgación científica [Código Nervioso](https://www.youtube.com/@CodigoNervioso), de Jorge Sauri.

El canal explica ciencia de datos, inteligencia artificial, bioinspiración y cognición artificial con simulaciones hechas para cada episodio. Este repositorio guarda esas simulaciones: se pueden abrir en vivo o volver a grabar las tomas del video.

- Canal: https://www.youtube.com/@CodigoNervioso

## Episodios

| Carpeta | Episodio | Video |
| --- | --- | --- |
| [sin_mapa_01](sin_mapa_01/) | Estigmergia: la inteligencia que no vive en ninguna cabeza | https://youtu.be/GXSB_aicVWg |

## Convención de carpetas

Cada episodio tiene su propia carpeta. El nombre es corto, describe el tema y termina con el número del episodio en dos dígitos (`sin_mapa_01`). No se usa el prefijo `ep01`.

## Requisitos generales

- Python 3
- Un entorno virtual (`python3 -m venv .venv`)
- Las bibliotecas de cada simulador, en su `requirements.txt` (en este episodio: pygame-ce y numpy)
- [ffmpeg](https://ffmpeg.org/) solamente para grabar las tomas a MP4

Entra a la carpeta del episodio y sigue el README de ahí.

## Licencia

Código bajo CC0 1.0 (dominio público). El texto legal completo está en [LICENSE](LICENSE).

Las fuentes tipográficas en `sin_mapa_01/fonts/` (Inter, Space Grotesk y JetBrains Mono) siguen con la licencia SIL Open Font License 1.1 y no son CC0. El texto de cada una está junto a los archivos: `OFL-Inter.txt`, `OFL-SpaceGrotesk.txt` y `OFL-JetBrainsMono.txt`.
