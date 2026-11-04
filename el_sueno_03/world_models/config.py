# S2 «World Models en Doom»: réplica de Ha & Schmidhuber (2018), «World Models», arXiv:1803.10122, sección 4 y apéndice A.
# Código propio en PyTorch, CC0. Los valores marcados [paper] vienen del artículo; [código Ha] del repositorio público
# hardmaru/WorldModelsExperiments (doomrnn/), consultado el 3 nov 2026.
import os
RAIZ = os.environ.get("S2_RAIZ", os.path.join(os.path.dirname(os.path.abspath(__file__)), "datos"))
MODO = os.environ.get("S2_MODO", "completo")    # "prueba" = corrida mínima en CPU para depurar

# Entorno
MAX_PASOS   = 2100      # [paper] cada rollout dura máx. 2100 pasos (~60 s); un paso = un tic de Doom (35/s)
UMBRAL      = 1/3       # [código Ha] acción continua en [-1,1]; < -1/3 izquierda, > 1/3 derecha, en medio quieto
RECORTE_Y   = 400/480   # [código Ha] _process_frame recorta las filas 0:400 de 480 antes de reducir a 64x64
# (Ha además invertía los colores, 1-obs; aquí NO invertimos para que las imágenes se vean naturales)

# Datos
N_ROLLOUTS  = 10_000    # [paper] 10,000 rollouts con política aleatoria
MIN_LARGO   = 100       # [código Ha] se descartan rollouts de <=100 cuadros
# Política aleatoria [código Ha, extract.py]: acción uniforme en [-1,1] que se repite 1-10 cuadros

# V: VAE convolucional [paper, apéndice A.1]
Z = 64                  # [paper] z ∈ R^64 en Doom
KL_TOLERANCIA = 0.5     # [código Ha] kl = max(kl, 0.5*Z)
VAE_EPOCAS  = 1         # [paper] «trained the model for 1 epoch»
VAE_LOTE, VAE_LR = 100, 1e-4   # [código Ha]

# M: MDN-RNN [paper, A.2]
RNN_H       = 512       # [paper] LSTM de 512 unidades en Doom
MEZCLAS     = 5         # [paper] 5 gaussianas
FACTOR_MUERTE = 10.0    # [código Ha] restart_factor=10: peso del caso raro «muere en el siguiente cuadro»
RNN_SEQ, RNN_LOTE, RNN_LR, RNN_CLIP = 500, 100, 1e-3, 1.0   # [código Ha] rnn_train.py
RNN_EPOCAS  = 20        # [paper] «trained for 20 epochs»; ojo: el código público de Ha usa 400. Se puede cambiar con S2_RNN_EPOCAS
RNN_EPOCAS  = int(os.environ.get("S2_RNN_EPOCAS", RNN_EPOCAS))

# C: controlador lineal a = tanh(W [z c h]) sin sesgo -> 64+512+512 = 1,088 parámetros [paper]
TEMPERATURA = float(os.environ.get("S2_TAU", 1.15))   # [paper] τ = 1.15 para el mejor agente
CMA_POB, CMA_REPS, CMA_SIGMA0 = 64, 16, 0.1           # [paper] población 64, 16 rollouts por agente
CMA_GENS    = int(os.environ.get("S2_GENS", 300))
EVAL_CADA, EVAL_N_SUENO = 25, 1024                    # [paper] cada 25 generaciones, el mejor se evalúa 1024 veces
EVAL_N_REAL = 100                                     # [paper] 100 rollouts en el juego real

if MODO == "prueba":
    N_ROLLOUTS, MIN_LARGO = 24, 20
    VAE_LOTE = 32
    RNN_SEQ, RNN_LOTE, RNN_EPOCAS = 120, 8, 3
    CMA_POB, CMA_REPS, CMA_GENS, EVAL_CADA, EVAL_N_SUENO, EVAL_N_REAL = 8, 2, 4, 2, 16, 3
    MAX_PASOS = 400

if MODO == "caja":   # versión reducida en CPU (box) solo para desarrollar las visualizaciones; resultados PRELIMINARES
    N_ROLLOUTS, VAE_EPOCAS = 600, 3
    RNN_SEQ, RNN_LOTE, RNN_EPOCAS = 300, 16, 150
    CMA_POB, CMA_REPS, CMA_GENS, EVAL_CADA, EVAL_N_SUENO, EVAL_N_REAL = 16, 4, 40, 10, 64, 20

def ruta(*p):
    d = os.path.join(RAIZ, MODO)
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, *p)
