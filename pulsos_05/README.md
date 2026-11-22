# Pulsos · episodio 5

Demos del episodio sobre **redes neuronales de impulsos (SNN)** del canal [Código Nervioso](https://www.youtube.com/@CodigoNervioso).

Cuatro piezas: tres con HTML/JavaScript (sin build) y una con Python (SpikingJelly). Todo corre en **CPU**. Textos, comentarios y controles en español.

**Video:** (pendiente)

| Carpeta | Qué muestra |
| --- | --- |
| [`01_pulso/`](01_pulso/) | Integración y disparo: neurona **LIF** (Gerstner & Kistler, caps. 1–2) frente a **Hodgkin–Huxley** (1952). Corriente inyectada, fuga, umbral, pulsos. Nota visible: parámetros HH del **axón gigante del calamar**. |
| [`02_izhikevich/`](02_izhikevich/) | Réplica ilustrativa de la **Fig. 2** de Izhikevich (2003): tipos **RS, IB, CH, FS, LTS, TC, RZ** con *a, b, c, d* del artículo. |
| [`04_continuas_vs_pulsos/`](04_continuas_vs_pulsos/) | Misma red pequeña: a la izquierda activaciones **continuas**, a la derecha **impulsos** con raster y conteo de pulsos (sin pasar a energía ni julios). |
| [`06_spikingjelly/`](06_spikingjelly/) | CNN+LIF y variante **una capa** (784→10, Poisson). Entrenamiento en CPU; `inferencia_raster.py` acepta `--modelo cnn\|una_capa`. |

## Instalación

### Demos web

Navegador moderno. Abre `pulsos_05/index.html` o sirve la carpeta:

```bash
cd pulsos_05
python3 -m http.server 8765
```

### Python (renders y SpikingJelly)

```bash
cd pulsos_05
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

`requirements.txt` fija versiones de NumPy, Matplotlib, Pillow, PyTorch (rueda **cpu**), torchvision y SpikingJelly. Si `pip` no encuentra `torch+cpu`, usa:

```bash
pip install torch==2.5.1+cpu torchvision==0.20.1+cpu -f https://download.pytorch.org/whl/torch_stable.html
pip install -r requirements.txt
```

## Uso de los renders

Cada `render.py` acepta:

| Opción | Valor |
| --- | --- |
| `--formato` | `16x9` (1920×1080) o `9x16` (1080×1920) |
| `--duracion` | segundos de video (por defecto 5) |
| `--salida` | ruta del MP4 |

Ejemplos:

```bash
python 01_pulso/render.py --formato 16x9 --duracion 5 --salida salida/01_16x9.mp4
python 01_pulso/render.py --formato 9x16 --duracion 5 --salida salida/01_9x16.mp4
python 02_izhikevich/render.py --formato 16x9 --salida salida/02_16x9.mp4
python 04_continuas_vs_pulsos/render.py --formato 9x16 --salida salida/04_9x16.mp4
```

Semillas fijas en cada script (`SEMILLA` en el código).

### Entrenamiento SNN

```bash
python 06_spikingjelly/train.py --epocas 2 --reporte salida/metricas.json
python 06_spikingjelly/train_una_capa.py --epocas 2 --reporte salida/metricas_una_capa.json
python 06_spikingjelly/inferencia_raster.py --modelo una_capa --formato 16x9 --salida salida/raster_una_capa_16x9.png
```

MNIST se descarga a `06_spikingjelly/data/` (excluido del repo).

## Fidelidad respecto a los papers

- **Hodgkin–Huxley:** ecuaciones clásicas y conductancias del calamar; la comparación con LIF es pedagógica, no un ajuste experimental.
- **Botones «justo debajo / encima» (01_pulso):** con τ_m=20 ms y θ=−50 mV, I=20 no dispara; I≈28.5 da 1–2 pulsos LIF en el render (Euler, Δt=0.05 ms).
- **Izhikevich:** mismos parámetros de la Tabla 1; la forma de las trazas puede diferir un poco de la Fig. 2 del PDF (escalón de corriente, integrador Euler, sin ruido).
- **Continuas vs impulsos:** red de juguete, no una arquitectura publicada.
- **SpikingJelly:** red pequeña para entrenar en CPU en minutos; la exactitud no compite con CNN convencionales.

## Referencias (citas completas)

- Gerstner, W., Kistler, W. M., Naud, R. y Paninski, L. (2014). *Neuronal Dynamics: From Single Neurons to Networks and Models of Cognition*. Cambridge University Press.
- Hodgkin, A. L. y Huxley, A. F. (1952). A quantitative description of membrane current and its application to conduction and excitation in nerve. *The Journal of Physiology, 117*(4), 500–544.
- Izhikevich, E. M. (2003). Simple model of spiking neurons. *IEEE Transactions on Neural Networks, 14*(6), 1569–1572. https://doi.org/10.1109/TNN.2003.820440
- Fang, W., Yu, Y., Chen, T., Huang, T., Lin, Y. y Masquelier, T. (2023). SpikingJelly: An open-source machine learning infrastructure platform for spike-based intelligence. *Science Advances, 9*(40), eadi1480.

## Licencia

Código en [CC0 1.0](LICENSE). Las fuentes Inter, Space Grotesk y JetBrains Mono siguen la SIL Open Font License 1.1 (`fuentes/OFL-*.txt`).