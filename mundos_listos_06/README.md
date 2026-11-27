# Mundos listos · episodio 6

Simuladores del episodio **«Reglas tontas, mundos listos»** (Código Nervioso). Código bajo [CC0 1.0](../LICENSE). Las fuentes en `fonts/` (Inter, Space Grotesk, JetBrains Mono) conservan la **SIL Open Font License** (`OFL-*.txt`).

## Cómo abrir

```bash
cd mundos_listos_06
python3 -m http.server 8766
```

Entra a http://127.0.0.1:8766/ — cada simulador es una carpeta con `index.html` (sin build).

## Captura determinista

Añade `?capture=1&formato=16x9|9x16&fps=60&w=1920&h=1080&seed=6006`. El reloj avanza con `dt = 1/60` s, no con el reloj de pared.

```bash
pip install -r grabar/requirements.txt
python3 -m playwright install chromium
python3 grabar/grabar_previews.py
```

Los MP4 de preview se escriben en `/opt/cursor/artifacts/` como `ep06_<sim>_16x9_1080p60.mp4` (y verticales `9x16` para Gray-Scott y boids).

## Piezas y parámetros

| Sim | Réplica / ilustración | Parámetros (fuente) |
|-----|------------------------|----------------------|
| **1A** `sim_1a_life/` | Gardner/Conway, reglas B3/S23 (notación posterior) | Semilla planeador + revoltijo; cita Gardner (1970) |
| **1B** `sim_1b_lenia/` | Lenia, lifeform Orbium | `R=13, T=10, μ=0.15, σ=0.015` — Chakazul/Lenia `animals.json`; Chan (2019) |
| **1C** `sim_1c_grayscott/` | Gray-Scott | `Du=2e-5, Dv=1e-5, F=0.018, k=0.055` — régimen σ (Pearson 1993; mapa de fases citado en Hundsdorfer & Verwer 2003) |
| **1D** `sim_1d_lenia_exp/` | Chan (2020) ampliada | **Sin parámetros de autorréplica confirmados** en paper/suplemento/repo contrastado → toma ilustrativa con aviso en pantalla |
| **1E** `sim_1e_langton/` | Langton (1984), tabla von Neumann | Tabla de transición (diga.me.uk / referencia Golly); **sin cifras** en pantalla |
| **2** `sim_2_bees/` | **Ilustración** Seeley/Visscher | Sin umbral rígido; banda 10–15 observada (2003) |
| **3** `sim_3_boids/` | Reynolds (1987) | Separación, alineación, cohesión; 320 agentes |
| **4** `sim_4_tero/` | Modelo Tero et al. (2010) | `γ=1.80`, `I₀=2.00` (Fig. 4); 36 nodos; Tokio = 7 comidas juntas — disposición espacial **ilustrativa**, no calca Fig. 1 |
| **4B** `sim_4b_jones/` | Jones (2010), agentes | Tablero distinto de Tero; quimiotaxis + rastro, sin cifras del paper (texto no contrastado completo) |
| **5** `sim_5_pps/` | Schmickl et al. (2016) | `r=5, α=180°, β=17°, v=0.67`; densidad ≈ `0.08` en dominio 250×250 |

## Figuritas PNG

Rutas: `assets/png/<nombre>.png` (lista en la especificación del episodio). Si falta un archivo, `comun/sprites.js` dibuja un **fallback vectorial** con la paleta del canal.

## No verificado / pendiente

- Parámetros exactos de **autorréplicadores Lenia 2020** (SIM 1D): no localizados en Chan (2020) + `Chakazul/Lenia` con cruce suficiente.
- Posiciones ciudad-a-ciudad del mapa del Pacífico de Tero Fig. 1 (se usa layout ilustrativo).
- Parámetros operativos internos del modelo de Jones más allá del abstract (repositorio UWE 403).

## Licencias

- Código JavaScript/Python/HTML/CSS: CC0.
- Fuentes: OFL 1.1 (ver `fonts/`).