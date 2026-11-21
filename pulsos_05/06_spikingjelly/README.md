# 06 · SpikingJelly en MNIST

Red convolucional pequeña con neuronas LIF y **gradiente sustituto** (SpikingJelly + PyTorch, solo CPU).

```bash
cd pulsos_05
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python 06_spikingjelly/train.py --epocas 2
python 06_spikingjelly/inferencia_raster.py --formato 16x9 --salida salida/raster.png
```

El entrenamiento escribe `salida/metricas.json` y `salida/modelo_mnist.pt`. No convierte el conteo de pulsos en energía ni en julios: solo reporta exactitud y pulsos promedio por neurona de salida.