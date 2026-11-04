# El sueño · simuladores del episodio 3

Código del episodio **«Una IA que aprendió a jugar Doom soñando»** del canal Código Nervioso.

Aquí está todo lo que usamos para las simulaciones del video:

| Carpeta | Qué hay |
| --- | --- |
| [`world_models/`](world_models/) | Réplica en PyTorch del experimento de Ha y Schmidhuber (2018) en ViZDoom «Take Cover»: visión (VAE), memoria (MDN-RNN) y controlador entrenado **solo dentro del sueño** con CMA-ES. Pasos s1 a s6. |
| [`dyna_laberinto/`](dyna_laberinto/) | Dyna-Q en el laberinto de Sutton y Barto (2018), cap. 8, Ejemplo 8.1, con n = 0, 5 y 50 pasos de planeación. |
| [`visualizaciones/`](visualizaciones/) | Las visualizaciones del video: Doom real vs. reconstrucción vs. sueño, la perilla de temperatura, el espacio latente y el laberinto Dyna. |
| [`animaciones/`](animaciones/) | Animaciones hechas con los datos de nuestras corridas (Dyna-Q, registro de CMA-ES, tabla de resultados, parámetros de las redes, modelo TD). |
| [`broll/`](broll/) | `grabar_clips.py`: graba nuestros propios clips de Doom con ViZDoom y Freedoom. |
| [`resultados/`](resultados/) | Resúmenes chicos (JSON y CSV) de nuestras corridas: los números que salen en pantalla. |

No hay pesos de redes, datasets ni videos en el repositorio: todo se genera al correr el código (ver `.gitignore`).

## Requisitos

- Python 3.10 o más reciente, en un entorno virtual dentro de esta carpeta: `python3 -m venv .venv && . .venv/bin/activate`
- `pip install -r requirements.txt` (numpy, pillow, torch, vizdoom, cma)
- [ffmpeg](https://ffmpeg.org/) para escribir los MP4 de las visualizaciones, las animaciones y el b-roll
- Para `world_models/` completo: una GPU NVIDIA con CUDA y bastante disco libre (los rollouts se guardan como `.npz`). El modo `prueba` corre en CPU.
- El laberinto Dyna solo necesita numpy y CPU.

ViZDoom trae el escenario «Take Cover» y el WAD libre Freedoom; no hace falta ningún archivo del Doom comercial.

## Cómo correr cada parte

### 1. World Models en Doom (`world_models/`)

```bash
cd world_models
# prueba rápida en CPU (minutos): verifica que todo funcione
S2_MODO=prueba ./correr_todo.sh
# corrida completa (GPU); el paper usa 20 épocas para la MDN-RNN y el código público de Ha, 400
S2_RNN_EPOCAS=400 TAUS="0.10 0.50 1.00 1.15 1.30" nohup ./correr_todo.sh > corrida.log 2>&1 &
```

| Paso | Script | Qué hace |
| --- | --- | --- |
| 1 | `s1_recolectar.py [n_procesos]` | Partidas con política aleatoria (el paper pide 10,000), cuadros de 64×64 |
| 2 | `s2_entrenar_vae.py` | V: VAE convolucional, z de 64 dimensiones |
| 3 | `s3_codificar.py` | Codifica todos los cuadros a (μ, log σ²) |
| 4 | `s4_entrenar_mdnrnn.py` | M: LSTM de 512 + mezcla de 5 gaussianas que predice el siguiente z y si el agente muere |
| 5 | `s5_cma_en_sueno.py` | C: controlador lineal de 1,088 parámetros, CMA-ES (población 64 × 16 partidas) **solo dentro del sueño**, a temperatura τ (`S2_TAU`) |
| 6 | `s6_evaluar_real.py τ` | El controlador soñado juega el juego real: 100 partidas, más una línea base al azar |

Cada constante de `config.py` dice si sale del paper **[paper]** o del código público del autor **[código Ha]** (github.com/hardmaru/WorldModelsExperiments, carpeta `doomrnn/`). Los datos se guardan en `world_models/datos/<modo>/`, que no se sube al repositorio.

Variables útiles: `S2_MODO` (`completo`, `prueba` o `caja`), `S2_RNN_EPOCAS`, `S2_TAU`, `S2_GENS` (generaciones de CMA-ES, 300 por omisión), `TAUS` (lista de temperaturas para `correr_todo.sh`), `NPROC` (procesos para recolectar) y `PODAR=0` para no borrar rollouts tras codificarlos.

**Tiempos aproximados.** Son orientativos, porque no cronometramos cada paso de nuestra corrida y dependen mucho de la máquina. El modo `prueba` tarda minutos en CPU. La corrida completa toma horas en GPU; no medimos el tiempo exacto. La recolección, las 400 épocas de la MDN-RNN y cada temperatura de CMA-ES son lo más lento.

### 2. Laberinto Dyna-Q (`dyna_laberinto/`)

```bash
python dyna_laberinto/dyna_maze.py        # 1000 semillas; segundos a pocos minutos en CPU
python dyna_laberinto/dyna_maze.py 50     # menos semillas, más rápido
```

Parámetros del libro: α = 0.1, ε = 0.1, γ = 0.95, 50 episodios, n = 0, 5 y 50. Escribe `resultados/dyna_maze_resultados.json`.

### 3. Visualizaciones (`visualizaciones/`)

`v1` a `v3` necesitan los modelos entrenados de `world_models/` (`vae.pt`, `mdnrnn.pt` y el controlador); `v4` solo necesita el laberinto Dyna. Escriben MP4 y PNG en `salida/visualizaciones/`.

```bash
cd visualizaciones
python v1_real_vae_sueno.py            # Doom real | reconstrucción del VAE | sueño de la MDN-RNN
python v2_sueno_temperatura.py 0.1,1.15,1.3   # el agente juega dentro del sueño a varias temperaturas
python v3_espacio_latente.py           # el espacio latente z en 3D (PCA)
python v4_dyna_laberinto.py            # Dyna-Q con n = 0, 5 y 50
```

Con `S2_MODO=prueba` o `caja` las visualizaciones se rotulan como PRELIMINAR. Las fuentes tipográficas están en `fuentes/` (ver Licencia).

### 4. Animaciones con datos (`animaciones/`)

```bash
cd animaciones
python anim_datos.py            # todas: a08 a21 a12 a13 a11 a16
python anim_datos.py a13        # solo una
```

Leen los resúmenes de `resultados/` y el laberinto de `dyna_laberinto/`. Escriben en `salida/animaciones/`.

### 5. B-roll de Doom (`broll/`)

```bash
python broll/grabar_clips.py                       # clips de «Take Cover» (al azar y esquivando) y recorridos de Freedoom
python broll/grabar_clips.py freedoom MAP01 MAP02  # solo recorridos de esos mapas
```

Graba a 640×360 y 35 cuadros por segundo, y escala a 1920×1080 a 60 fps. Los clips quedan en `salida/broll/`.

## Resultados

### Nuestra simulación (juego real, n = 100 partidas por fila)

Pasos que sobrevive el agente en «Take Cover» (máximo 2100). «Sueño» es la mejor evaluación dentro del sueño (1024 partidas soñadas); «real» es el mismo controlador jugando el juego real con semillas que no vio al entrenar. Media ± desviación estándar.

| τ | Sueño | Juego real |
| --- | --- | --- |
| 0.10 | 2100 ± 0 | 637 ± 400 |
| 0.50 | 2075 ± 172 | 903 ± 530 |
| 1.00 | 1708 ± 592 | 771 ± 436 |
| 1.15 | 1578 ± 655 | 988 ± 538 |
| 1.30 | 1316 ± 675 | 872 ± 518 |
| al azar | — | 335 ± 176 |

Los archivos están en `resultados/` (`real_tau*.json`, `mejor_tau*.json`, `cma_tau*.csv`, `aleatorio_real.json`).

### Paper: Ha y Schmidhuber (2018), Tabla 2

Estos números son del artículo, no de nuestra corrida.

| τ | Sueño | Juego real |
| --- | --- | --- |
| 0.10 | 2086 ± 140 | 193 ± 58 |
| 0.50 | 2060 ± 277 | 196 ± 50 |
| 1.00 | 1145 ± 690 | 868 ± 511 |
| 1.15 | 918 ± 546 | 1092 ± 556 |
| 1.30 | 732 ± 269 | 753 ± 139 |
| al azar | — | 210 ± 108 |

### Qué sí y qué no reprodujimos

- **Sí** se repite el patrón grande: con τ = 0.1 el sueño da la calificación perfecta (2100) y en el juego real cae a 637; con τ = 1.15 el agente saca menos dentro del sueño, pero es nuestro mejor resultado en el juego real (988).
- **No** reprodujimos el colapso a temperatura baja. En el paper, con τ = 0.1 y 0.5 el agente queda por debajo del azar en el juego real (193 y 196 contra 210). En nuestra corrida queda muy por encima (637 y 903 contra 335).
- **La recolección se detuvo en 7,583 de los 10,000 rollouts** que pide el paper, y entrenamos con esos 7,583.
- Otras diferencias de método: la MDN-RNN se entrenó 400 épocas (como el código público de Ha; el paper dice 20); no invertimos los colores de los cuadros; PyTorch usa dos sesgos por compuerta en la LSTM, así que la MDN-RNN tiene 1,680,833 parámetros contra 1,678,785 del paper. Nuestra línea base al azar da 335 (el paper reporta 210).

## Créditos

- [ViZDoom](https://github.com/Farama-Foundation/ViZDoom), licencia MIT.
- [Freedoom](https://freedoom.github.io/), licencia BSD-3-Clause, © Freedoom project.
- Experimento original: Ha, D. y Schmidhuber, J. (2018), y su código público [hardmaru/WorldModelsExperiments](https://github.com/hardmaru/WorldModelsExperiments). Nuestra réplica es código propio.
- Laberinto Dyna: Sutton, R. S. y Barto, A. G. (2018), cap. 8.

## Licencia

Código bajo **CC0 1.0** (dominio público); el texto legal está en [LICENSE](LICENSE).

Las fuentes tipográficas de `fuentes/` (Inter, Space Grotesk y JetBrains Mono) siguen con la licencia SIL Open Font License 1.1 y no son CC0. Sus textos están en `fuentes/`.

## Fuentes

Lista completa de las fuentes citadas en el episodio.

### Modelos del mundo en IA

- Craik, K. J. W. (1943). *The nature of explanation*. Cambridge University Press. https://archive.org/details/natureofexplanat0000crai
- Ha, D., & Schmidhuber, J. (2018). World models. *arXiv:1803.10122*. https://arxiv.org/abs/1803.10122
- Ha, D., & Schmidhuber, J. (2018). Recurrent world models facilitate policy evolution. *Advances in Neural Information Processing Systems 31 (NeurIPS 2018)*. arXiv:1809.01999. https://arxiv.org/abs/1809.01999
- Hafner, D., Lillicrap, T., Ba, J., & Norouzi, M. (2020). Dream to control: Learning behaviors by latent imagination. *ICLR 2020*. arXiv:1912.01603. https://arxiv.org/abs/1912.01603
- Hafner, D., Lillicrap, T., Norouzi, M., & Ba, J. (2021). Mastering Atari with discrete world models. *ICLR 2021*. arXiv:2010.02193. https://arxiv.org/abs/2010.02193
- Hafner, D., Pasukonis, J., Ba, J., & Lillicrap, T. (2025). Mastering diverse control tasks through world models. *Nature, 640*, 647–653. https://doi.org/10.1038/s41586-025-08744-2
- Schrittwieser, J., Antonoglou, I., Hubert, T., Simonyan, K., Sifre, L., Schmitt, S., et al. (2020). Mastering Atari, Go, chess and shogi by planning with a learned model. *Nature, 588*(7839), 604–609. https://doi.org/10.1038/s41586-020-03051-4
- Ding, J., Zhang, Y., Shang, Y., et al. (2025). Understanding world or predicting future? A comprehensive survey of world models. *ACM Computing Surveys, 58*(3). https://doi.org/10.1145/3746449
- LeCun, Y. (2022). A path towards autonomous machine intelligence (versión 0.9.2). *OpenReview*. https://openreview.net/forum?id=BZ5a1r-kVsf
- Assran, M., Duval, Q., Misra, I., Bojanowski, P., Vincent, P., Rabbat, M., LeCun, Y., & Ballas, N. (2023). Self-supervised learning from images with a joint-embedding predictive architecture. *CVPR 2023*, 15619–15629. https://doi.org/10.1109/CVPR52729.2023.01499
- Bardes, A., Garrido, Q., Ponce, J., Chen, X., Rabbat, M., LeCun, Y., Assran, M., & Ballas, N. (2024). Revisiting feature prediction for learning visual representations from video. *Transactions on Machine Learning Research (TMLR)*. arXiv:2404.08471. https://arxiv.org/abs/2404.08471
- Assran, M., Bardes, A., Fan, D., Garrido, Q., Howes, R., Komeili, M., et al. (2025). V-JEPA 2: Self-supervised video models enable understanding, prediction and planning. *arXiv:2506.09985*. https://arxiv.org/abs/2506.09985

### Aprendizaje por refuerzo con modelo (Dyna)

- Sutton, R. S. (1990). Integrated architectures for learning, planning, and reacting based on approximating dynamic programming. En *Machine Learning Proceedings 1990* (pp. 216–224). Morgan Kaufmann. https://doi.org/10.1016/B978-1-55860-141-3.50030-4
- Sutton, R. S. (1991). Dyna, an integrated architecture for learning, planning, and reacting. *ACM SIGART Bulletin, 2*(4), 160–163. https://doi.org/10.1145/122344.122377
- Sutton, R. S., & Barto, A. G. (2018). *Reinforcement learning: An introduction* (2.ª ed.), cap. 8, Ejemplo 8.1. MIT Press. http://incompleteideas.net/book/RLbook2020.pdf

### Cerebro predictivo

- Rao, R. P. N., & Ballard, D. H. (1999). Predictive coding in the visual cortex: A functional interpretation of some extra-classical receptive-field effects. *Nature Neuroscience, 2*(1), 79–87. https://doi.org/10.1038/4580
- Friston, K. (2010). The free-energy principle: A unified brain theory? *Nature Reviews Neuroscience, 11*(2), 127–138. https://doi.org/10.1038/nrn2787
- Clark, A. (2013). Whatever next? Predictive brains, situated agents, and the future of cognitive science. *Behavioral and Brain Sciences, 36*(3), 181–204. https://doi.org/10.1017/S0140525X12000477
- Wolpert, D. M., Miall, R. C., & Kawato, M. (1998). Internal models in the cerebellum. *Trends in Cognitive Sciences, 2*(9), 338–347. https://doi.org/10.1016/S1364-6613(98)01221-2
- Schultz, W., Dayan, P., & Montague, P. R. (1997). A neural substrate of prediction and reward. *Science, 275*(5306), 1593–1599. https://doi.org/10.1126/science.275.5306.1593
- Hobson, J. A., & Friston, K. J. (2012). Waking and dreaming consciousness: Neurobiological and functional considerations. *Progress in Neurobiology, 98*(1), 82–98. https://doi.org/10.1016/j.pneurobio.2012.05.003
- Hobson, J. A., Hong, C. C.-H., & Friston, K. J. (2014). Virtual reality and consciousness inference in dreaming. *Frontiers in Psychology, 5*, 1133. https://doi.org/10.3389/fpsyg.2014.01133

### Mapas, replay y planeación en el cerebro

- Tolman, E. C. (1948). Cognitive maps in rats and men. *Psychological Review, 55*(4), 189–208. https://doi.org/10.1037/h0061626
- O'Keefe, J., & Dostrovsky, J. (1971). The hippocampus as a spatial map. Preliminary evidence from unit activity in the freely-moving rat. *Brain Research, 34*(1), 171–175. https://doi.org/10.1016/0006-8993(71)90358-1
- Hafting, T., Fyhn, M., Molden, S., Moser, M.-B., & Moser, E. I. (2005). Microstructure of a spatial map in the entorhinal cortex. *Nature, 436*(7052), 801–806. https://doi.org/10.1038/nature03721
- Wilson, M. A., & McNaughton, B. L. (1994). Reactivation of hippocampal ensemble memories during sleep. *Science, 265*(5172), 676–679. https://doi.org/10.1126/science.8036517
- Foster, D. J., & Wilson, M. A. (2006). Reverse replay of behavioural sequences in hippocampal place cells during the awake state. *Nature, 440*(7084), 680–683. https://doi.org/10.1038/nature04587
- Johnson, A., & Redish, A. D. (2007). Neural ensembles in CA3 transiently encode paths forward of the animal at a decision point. *Journal of Neuroscience, 27*(45), 12176–12189. https://doi.org/10.1523/JNEUROSCI.3761-07.2007
- Pfeiffer, B. E., & Foster, D. J. (2013). Hippocampal place-cell sequences depict future paths to remembered goals. *Nature, 497*, 74–79. https://doi.org/10.1038/nature12112
- Girardeau, G., Benchenane, K., Wiener, S. I., Buzsáki, G., & Zugaro, M. B. (2009). Selective suppression of hippocampal ripples impairs spatial memory. *Nature Neuroscience, 12*(10), 1222–1223. https://doi.org/10.1038/nn.2384
- Jadhav, S. P., Kemere, C., German, P. W., & Frank, L. M. (2012). Awake hippocampal sharp-wave ripples support spatial memory. *Science, 336*(6087), 1454–1458. https://doi.org/10.1126/science.1217230
- Mattar, M. G., & Daw, N. D. (2018). Prioritized memory access explains planning and hippocampal replay. *Nature Neuroscience, 21*, 1609–1617. https://doi.org/10.1038/s41593-018-0232-z
- Wilson, R. C., Takahashi, Y. K., Schoenbaum, G., & Niv, Y. (2014). Orbitofrontal cortex as a cognitive map of task space. *Neuron, 81*(2), 267–279. https://doi.org/10.1016/j.neuron.2013.11.005
- Daw, N. D., Niv, Y., & Dayan, P. (2005). Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control. *Nature Neuroscience, 8*(12), 1704–1711. https://doi.org/10.1038/nn1560
- Daw, N. D., Gershman, S. J., Seymour, B., Dayan, P., & Dolan, R. J. (2011). Model-based influences on humans' choices and striatal prediction errors. *Neuron, 69*(6), 1204–1215. https://doi.org/10.1016/j.neuron.2011.02.027
- Feher da Silva, C., & Hare, T. A. (2020). Humans primarily use model-based inference in the two-stage task. *Nature Human Behaviour, 4*(10), 1053–1066. https://doi.org/10.1038/s41562-020-0905-y
- Stachenfeld, K. L., Botvinick, M. M., & Gershman, S. J. (2017). The hippocampus as a predictive map. *Nature Neuroscience, 20*(11), 1643–1653. https://doi.org/10.1038/nn.4650

### Red neuronal por defecto

- Raichle, M. E., MacLeod, A. M., Snyder, A. Z., Powers, W. J., Gusnard, D. A., & Shulman, G. L. (2001). A default mode of brain function. *PNAS, 98*(2), 676–682. https://doi.org/10.1073/pnas.98.2.676
- Buckner, R. L., Andrews-Hanna, J. R., & Schacter, D. L. (2008). The brain's default network: Anatomy, function, and relevance to disease. *Annals of the New York Academy of Sciences, 1124*, 1–38. https://doi.org/10.1196/annals.1440.011
- Schacter, D. L., & Addis, D. R. (2007). The cognitive neuroscience of constructive memory: Remembering the past and imagining the future. *Philosophical Transactions of the Royal Society B, 362*(1481), 773–786. https://doi.org/10.1098/rstb.2007.2087
- Schacter, D. L., Addis, D. R., & Buckner, R. L. (2007). Remembering the past to imagine the future: The prospective brain. *Nature Reviews Neuroscience, 8*(9), 657–661. https://doi.org/10.1038/nrn2213
- Hassabis, D., & Maguire, E. A. (2007). Deconstructing episodic memory with construction. *Trends in Cognitive Sciences, 11*(7), 299–306. https://doi.org/10.1016/j.tics.2007.05.001
- Hassabis, D., Kumaran, D., Vann, S. D., & Maguire, E. A. (2007). Patients with hippocampal amnesia cannot imagine new experiences. *PNAS, 104*(5), 1726–1731. https://doi.org/10.1073/pnas.0610561104
- Buckner, R. L., & Carroll, D. C. (2007). Self-projection and the brain. *Trends in Cognitive Sciences, 11*(2), 49–57. https://doi.org/10.1016/j.tics.2006.11.004
- Spreng, R. N., Mar, R. A., & Kim, A. S. N. (2009). The common neural basis of autobiographical memory, prospection, navigation, theory of mind, and the default mode: A quantitative meta-analysis. *Journal of Cognitive Neuroscience, 21*(3), 489–510. https://doi.org/10.1162/jocn.2008.21029
- Carhart-Harris, R. L., & Friston, K. J. (2010). The default-mode, ego-functions and free-energy: A neurobiological account of Freudian ideas. *Brain, 133*(4), 1265–1283. https://doi.org/10.1093/brain/awq010
- Andrews-Hanna, J. R., Reidler, J. S., Sepulcre, J., Poulin, R., & Buckner, R. L. (2010). Functional-anatomic fractionation of the brain's default network. *Neuron, 65*(4), 550–562. https://doi.org/10.1016/j.neuron.2010.02.005
- Andrews-Hanna, J. R., Smallwood, J., & Spreng, R. N. (2014). The default network and self-generated thought: Component processes, dynamic control, and clinical relevance. *Annals of the New York Academy of Sciences, 1316*(1), 29–52. https://doi.org/10.1111/nyas.12360
- Spreng, R. N. (2012). The fallacy of a "task-negative" network. *Frontiers in Psychology, 3*, 145. https://doi.org/10.3389/fpsyg.2012.00145
- Callard, F., & Margulies, D. S. (2014). What we talk about when we talk about the default mode network. *Frontiers in Human Neuroscience, 8*, 619. https://doi.org/10.3389/fnhum.2014.00619
- Poldrack, R. A. (2006). Can cognitive processes be inferred from neuroimaging data? *Trends in Cognitive Sciences, 10*(2), 59–63. https://doi.org/10.1016/j.tics.2005.12.004
- Vincent, J. L., Patel, G. H., Fox, M. D., Snyder, A. Z., Baker, J. T., Van Essen, D. C., Zempel, J. M., Snyder, L. H., Corbetta, M., & Raichle, M. E. (2007). Intrinsic functional architecture in the anaesthetized monkey brain. *Nature, 447*(7140), 83–86. https://doi.org/10.1038/nature05758
- Lu, H., Zou, Q., Gu, H., Raichle, M. E., Stein, E. A., & Yang, Y. (2012). Rat brains also have a default mode network. *PNAS, 109*(10), 3979–3984. https://doi.org/10.1073/pnas.1200506109
- Menon, V., & Uddin, L. Q. (2010). Saliency, switching, attention and control: A network model of insula function. *Brain Structure and Function, 214*(5–6), 655–667. https://doi.org/10.1007/s00429-010-0262-0
- Yuan, Y., Pan, X., & Wang, R. (2021). Biophysical mechanism of the interaction between default mode network and working memory network. *Cognitive Neurodynamics, 15*(6), 1101–1124. https://doi.org/10.1007/s11571-021-09674-1
