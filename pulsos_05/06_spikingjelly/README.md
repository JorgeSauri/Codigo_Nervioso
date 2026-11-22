# 06 · SpikingJelly en MNIST

Dos variantes en CPU (SpikingJelly + PyTorch):

| Script | Red |
| --- | --- |
| `train.py` | CNN pequeña + LIF |
| `train_una_capa.py` | **Una sola capa** `Linear(784→10)` + LIF, codificación **Poisson** (como `lif_fc_mnist`) |

```bash
cd pulsos_05
pip install -r requirements.txt
python 06_spikingjelly/train.py --epocas 2
python 06_spikingjelly/train_una_capa.py --epocas 2 --T 32
python 06_spikingjelly/inferencia_raster.py --modelo cnn --formato 16x9
python 06_spikingjelly/inferencia_raster.py --modelo una_capa --formato 16x9
```

Checkpoints: `salida/modelo_mnist.pt` y `salida/modelo_una_capa.pt`. Con `--modelo una_capa`, el raster usa por defecto el **primer dígito 7** del set de prueba (índice 0). No convierte pulsos en julios.