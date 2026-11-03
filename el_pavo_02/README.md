# El pavo · simulador del episodio 2

Simulador del episodio **«La trampa de las criptomonedas: el dilema del pavo»** del canal [Código Nervioso](https://www.youtube.com/@CodigoNervioso).

Cada escena replica, en una ventana de 1920×1080, el método de un artículo citado en el episodio. Sirve para usarla en vivo o para volver a grabar las tomas del video. Todas las cifras que salen en pantalla las calcula el programa al momento. Las únicas excepciones son los valores citados de los artículos, que aparecen con el nombre de su autor: el 79 % de Taleb para el S&P 500, las 45 configuraciones de Bailey et al., la media de 36.73 y la mediana de 33 de Nagel, y el «5 a 13 veces» de Shiller.

## Sobre los datos

Las escenas S2, S3, S4, S5a, S5b y S6b usan **solo datos simulados**, generados con semilla fija. No hay datos de ningún proveedor de precios ni de ninguna criptomoneda real. En pantalla lo dice la etiqueta «Datos simulados». La calibración es cualitativa: la volatilidad se parece a la de una criptomoneda, pero no pretende reproducir ninguna serie real.

* S2 y S4: rendimientos diarios independientes con t de Student de 3 grados de libertad y media cero.
* S3: GARCH(1,1) con innovaciones t de 4 grados de libertad. La dirección no tiene memoria, pero el tamaño de los saltos sí.
* S5a, S5b y S6b: modelos de agentes (ver cada escena).

Con la misma semilla, el resultado es el mismo en cualquier computadora.

**S6c es la única escena con datos reales**: el precio, los dividendos y el índice de precios del S&P desde 1871 que publica Robert J. Shiller en [shillerdata.com](https://shillerdata.com/). El programa descarga el archivo `ie_data.xls` la primera vez que se usa la escena y lo guarda en `datos/`. Esa carpeta está excluida del repositorio: los datos no se redistribuyen y la página no declara una licencia. Si la descarga falla, la escena se detiene con un mensaje de error; no hay datos de reemplazo. En pantalla aparece el crédito «Datos: Robert J. Shiller, shillerdata.com». Como Shiller actualiza el archivo cada mes, las cifras pueden moverse un poco entre una descarga y otra.

### Semillas

| Escena | Semilla | Por qué |
| --- | --- | --- |
| S2 | 2026 | La de omisión del código |
| S3 | 2028 | La de omisión del código; no se buscó |
| S4 | 28 | Elegida porque ilustra: su campeona pasa t > 2. Al final sale el promedio de 100 semillas |
| S5a | 7 | Elegida porque ilustra: la primera semilla con una cascada equivocada temprana que la señal pública rompe. Al final sale el promedio de 10 000 filas |
| S5b | 5014 | La de curtosis mediana entre los 30 mundos que se promedian (semillas 5000 a 5029). Se cambió de la 2029 inicial, cuya curtosis (3.84) quedaba abajo del rango de los 30 mundos y subestimaba el efecto. Al final sale el promedio de los 30 |
| S6b | 1995 | La de omisión; con 1 000 jugadores casi no cambia. Además se promedian 1 000 grupos chicos |

## Qué muestra cada escena

Las teclas `1` a `7` cambian de escena. Con `--escena` se usa la clave.

| Tecla | Clave | Escena |
| --- | --- | --- |
| 1 | `s2` | ¿Cuánto pesa el peor día? |
| 2 | `s3` | ¿Camina como borracho? |
| 3 | `s4` | La fábrica de estrategias ganadoras |
| 4 | `s5a` | Todos copian y nadie usa lo que sabe |
| 5 | `s5b` | El mercado que se inventa sus tormentas |
| 6 | `s6b` | El concurso de belleza |
| 7 | `s6c` | El precio que debió ser |

### S2 · ¿Cuánto pesa el peor día?

Réplica del método de la Tabla 3.3 de Taleb (2020) sobre 10 años (3 650 días) de rendimientos simulados con colas gordas.

* Un histograma de los días se llena poco a poco, con la campana de Gauss encima: misma media y misma desviación que la serie. Las colas (más de 3 desviaciones) van en coral. Luego el eje vertical pasa a escala logarítmica para que se vean los extremos.
* Un contador compara cuántos días de −20 % o peor esperaría la campana con los que salen en la serie.
* «Max Quartic» de Taleb: la parte de la suma de las cuartas potencias, max(X⁴) / Σ X⁴, que aporta un solo día. Se compara con una serie gaussiana del mismo tamaño y con el valor que Taleb reporta para el S&P 500 (0.79 en 56 años).
* El mismo cálculo repetido en 100 series simuladas, para ver cuánto cambia según qué días caen en la muestra.
* El exponente de cola de las pérdidas, estimado con el paquete [`powerlaw`](https://github.com/jeffalstott/powerlaw) (Alstott et al. 2014). `powerlaw` da el exponente α de la densidad. En pantalla sale el de la cola acumulada, α − 1, que es el que usa Mandelbrot. La serie se simuló con un exponente real de 3. Con la semilla de la escena el estimado sale en 2.4: con 10 años de datos, la cola se estima con mucho error. Cualquier valor menor que 4 implica que la curtosis no existe. Por defecto `powerlaw` 2.x limita α a [0, 3], así que el código amplía ese rango.

### S3 · ¿Camina como borracho?

Pruebas de eficiencia débil como las que usan Urquhart (2016) y Bariviera (2017) para bitcoin, aplicadas a una serie simulada de 2 000 días en la que, por construcción, la dirección del día siguiente no se puede predecir, pero el tamaño de los saltos sí tiene memoria (GARCH).

* Arriba, los rendimientos. En medio, su tamaño sin signo, |r|. Abajo, el exponente de Hurst en ventanas móviles de 500 días, por DFA de orden 1 (escalas de 4 a 128 días), como Bariviera (2017).
* Ratio de varianza de Lo y MacKinlay (1988) a 2, 5, 10 y 20 días, con el estadístico robusto a heterocedasticidad del paquete [`arch`](https://github.com/bashtage/arch).
* Con la semilla 2028: ratio a 10 días de 1.11 para la dirección (p = 0.27, no se rechaza el paseo aleatorio) y de 2.35 para el tamaño (p < 0.001). Hurst de toda la serie: 0.53 para la dirección y 0.70 para el tamaño.
* El sombreado dorado marca las ventanas en las que la dirección «parece» tener inercia (Hurst > 0.6) aunque no la tiene: 19 % de las ventanas con esta semilla.
* El mismo cálculo en 100 series (semillas 3000 a 3099): la prueba a 10 días rechaza el paseo en 6 % de las series para la dirección y en 100 % para el tamaño.
* Nota: el Hurst por DFA tiene un sesgo hacia arriba en muestras de 500 días; por eso la dirección promedia 0.54 y no 0.50 en las 100 series.

### S4 · La fábrica de estrategias ganadoras

Réplica del método de Bailey et al. (2014, 2017) sobre un precio simulado de 5 años en el que, por construcción, nadie puede predecir el siguiente día.

* Se prueban 326 reglas de cruce de promedios móviles: simples y exponenciales, rápido de 1 a 40 días y lento de 10 a 300 días, con el lento al menos el doble del rápido. Cada regla va larga o corta y opera al día siguiente de la señal.
* La primera mitad (2.5 años) sirve para elegir la campeona por razón de Sharpe. La segunda mitad son datos que la regla nunca vio. Después se descuenta una comisión de 0.1 % por cada cambio de posición.
* Un contador indica cuántas reglas pasan la prueba t > 2 y cuántas el umbral t > 3 que proponen Harvey, Liu y Zhu (2016). La escena también muestra la cota de Bailey et al. (2014): con 5 años de datos, no más de unas 45 configuraciones.
* Probabilidad de sobreajuste (PBO) por validación cruzada combinatoriamente simétrica (CSCV, Bailey et al. 2017): 16 bloques, 12 870 combinaciones. PBO es la proporción de combinaciones en las que la campeona queda abajo de la mediana fuera de muestra.
* El ejercicio completo repetido en 100 precios simulados (semillas 1 a 100).
* La escena usa la semilla 28. Se eligió porque su campeona pasa la prueba clásica t > 2, que es lo que haría ver una regla como «descubrimiento». Al final aparece el promedio de las 100 semillas para que no dependa de un solo caso.

La CSCV está escrita a mano en `cn_sim/fabrica.py`, vectorizada con numpy. No usa [`pypbo`](https://github.com/esvhd/pypbo), porque ese paquete tiene licencia AGPL-3.0 y no se instala con pip. El cálculo sigue la misma convención: descarta los primeros días que sobran al partir en bloques, usa rango promedio en empates y cuenta logit ≤ 0. Con los rendimientos de la semilla 28 da el mismo PBO que `pypbo` con 8 y con 10 bloques.

### S5a · Todos copian y nadie usa lo que sabe

Cascada informativa de Bikhchandani, Hirshleifer y Welch (1992). Cincuenta personas eligen entre dos restaurantes, una tras otra. El bueno es A. Cada quien recibe una corazonada privada que acierta 60 % de las veces y ve lo que eligieron los anteriores.

* Regla de Bayes del artículo: cada quien cuenta las corazonadas que puede deducir de lo anterior. En empate sigue la suya. Cuando la ventaja de un lado pasa de 1, la cascada empieza: la corazonada propia ya no cambia nada y todos copian.
* Antes de la persona 26 aparece una señal pública (una reseña confiable) que acierta 69 % de las veces, lo que vale dos corazonadas.
* Con la semilla 7: la cascada hacia B (el equivocado) empieza en la persona 3; las primeras 25 eligen B aunque 14 de sus 25 corazonadas decían A. Después de la señal, 25 de 25 eligen A. 23 de las 50 ignoran su corazonada.
* En 10 000 filas (semillas 100000 a 109999): sin señal, 31 % terminan en B; con señal, 22 %. La señal rompe 48 % de las cascadas equivocadas.

### S5b · El mercado que se inventa sus tormentas

**Versión simplificada**, escrita por el canal, del modelo de Lux y Marchesi (1999). Quinientos agentes cambian entre tres grupos: optimistas y pesimistas que siguen la tendencia (chartistas), y fundamentalistas. El valor fundamental se mueve solo con noticias gaussianas. En pantalla lo dice la etiqueta «Versión simplificada».

* Izquierda: las noticias. Derecha: el rendimiento del precio que sale del modelo. Debajo, histogramas en escala logarítmica contra la campana, y la parte del mercado que sigue la tendencia.
* Diferencias con el artículo: tiempo discreto (200 pasos por día), β = 20 en lugar de 6 (con el β del artículo y esta discretización el precio quedaba con autocorrelación alta), cambios de grupo con sorteos binomiales y precio con saltos de Poisson de ±0.01. Los demás parámetros son los del artículo.
* Con la semilla 5014: curtosis de 3.0 en las noticias y de 5.6 en el precio; 0 días de más de 4 desviaciones en las noticias contra 6 en el precio (la campana espera 0.13); autocorrelación del tamaño |r| a un día de 0.01 contra 0.18; la dirección casi no tiene memoria (−0.02).
* En 30 mundos (semillas 5000 a 5029): curtosis del precio de 5.7 en promedio, de 4.5 a 7.7.

### S6b · El concurso de belleza

El juego de Keynes (1936) tal como lo llevó al laboratorio Nagel (1995): cada quien elige de 0 a 100 y gana quien quede más cerca de 2/3 del promedio.

* 1 000 jugadores simulados con pasos de razonamiento (nivel k, Nagel p. 1315): el nivel 0 elige al azar, el nivel 1 elige 2/3 de 50 (33), el nivel 2 elige 2/3 de 33 (22), y así.
* **Las proporciones de niveles (35 % · 35 % · 20 % · 10 % para los niveles 0 a 3) son un supuesto del canal, no un dato.** En pantalla lo dice.
* Cuatro rondas. En cada una, los jugadores parten del promedio de la anterior. El histograma se desliza hacia 0, que es lo que elegiría todo el mundo si todos razonaran hasta el final.
* Con la semilla 1995: promedios de 34.4, 24.4, 17.1 y 12.1.
* En 1 000 grupos de 16 personas, como los de Nagel: la media de la primera ronda queda entre 27 y 45 en el 90 % de los grupos.
* Cifra citada, con su autor: en el laboratorio de Nagel, con p = 2/3, la primera ronda tuvo media 36.73 y mediana 33, y nadie eligió 0 (Figura 1, p. 1316).

### S6c · El precio que debió ser

Réplica del método de Shiller (1981) con sus datos actualizados.

* Precio real del S&P en enero de cada año y dividendo real promedio del año, de 1871 al último año con dividendos completos (2025 en la descarga usada para grabar).
* Como en el artículo: se quita la tendencia exponencial (regresión de ln P contra el tiempo), la tasa de descuento real fija es el promedio del dividendo entre el promedio del precio (sin tendencia), y p* es el valor presente de los dividendos reales que vinieron después: p*ₜ = (p*ₜ₊₁ + dₜ) / (1 + r). El valor final de p* es el precio promedio sin tendencia, como hace Shiller.
* En pantalla, la línea nerviosa del precio contra la línea suave de p*, en dólares de hoy y en escala logarítmica.
* **El año final de la muestra cambia el cálculo**: cambian la tendencia, la tasa y el valor final. Por eso p* también se calcula con la muestra de Shiller (1871–1979). En dólares las dos curvas casi coinciden; la tasa pasa de 4.6 % a 3.8 % y la razón de desviaciones típicas del nivel, σ(p)/σ(p*), de 3.9 a 1.8.
* Los cambios anuales del precio (sin tendencia) tienen una desviación típica 17 veces la de los cambios de p* (20 veces con la muestra a 1979). Esta medida es del canal y no es la prueba de Shiller.
* Cifra citada, con su autor: Shiller encuentra que la volatilidad es de 5 a 13 veces mayor de lo que justifican los dividendos, con sus pruebas formales sobre 1871–1979 (pp. 432–434).

Para ver las cifras de una semilla en la terminal:

```bash
.venv/bin/python -m cn_sim.fabrica 28
.venv/bin/python -m cn_sim.colas 2026
.venv/bin/python -m cn_sim.paseo
.venv/bin/python -m cn_sim.cascada
.venv/bin/python -m cn_sim.lux
.venv/bin/python -m cn_sim.belleza
.venv/bin/python -m cn_sim.shiller      # descarga los datos de Shiller si no están en datos/
```

## Fuentes

* Taleb, N. N. (2020). *Statistical Consequences of Fat Tails*. STEM Academic Press. Tabla 3.3.
* Alstott, J., Bullmore, E. y Plenz, D. (2014). powerlaw: a Python package for analysis of heavy-tailed distributions. *PLoS ONE* 9(1): e85777.
* Bailey, D. H., Borwein, J. M., López de Prado, M. y Zhu, Q. J. (2014). Pseudo-mathematics and financial charlatanism: the effects of backtest overfitting on out-of-sample performance. *Notices of the AMS* 61(5).
* Bailey, D. H., Borwein, J. M., López de Prado, M. y Zhu, Q. J. (2017). The probability of backtest overfitting. *Journal of Computational Finance* 20(4).
* Harvey, C. R., Liu, Y. y Zhu, H. (2016). … and the cross-section of expected returns. *Review of Financial Studies* 29(1).
* Lo, A. W. y MacKinlay, A. C. (1988). Stock market prices do not follow random walks: evidence from a simple specification test. *Review of Financial Studies* 1(1), 41–66.
* Urquhart, A. (2016). The inefficiency of Bitcoin. *Economics Letters* 148, 80–82.
* Bariviera, A. F. (2017). The inefficiency of Bitcoin revisited: a dynamic approach. *Economics Letters* 161, 1–4.
* Sheppard, K. y colaboradores. `arch`: ARCH models and other tools for financial econometrics in Python. https://github.com/bashtage/arch
* Bikhchandani, S., Hirshleifer, D. y Welch, I. (1992). A theory of fads, fashion, custom, and cultural change as informational cascades. *Journal of Political Economy* 100(5), 992–1026.
* Lux, T. y Marchesi, M. (1999). Scaling and criticality in a stochastic multi-agent model of a financial market. *Nature* 397, 498–500.
* Keynes, J. M. (1936). *The General Theory of Employment, Interest and Money*, cap. 12.
* Nagel, R. (1995). Unraveling in guessing games: an experimental study. *American Economic Review* 85(5), 1313–1326.
* Shiller, R. J. (1981). Do stock prices move too much to be justified by subsequent changes in dividends? *American Economic Review* 71(3), 421–436.
* Datos: Robert J. Shiller, *U.S. Stock Markets 1871–Present and CAPE Ratio*, https://shillerdata.com/

## Todas las fuentes del episodio

La descripción del video lleva solo las fuentes principales. Esta es la lista completa que se usó para el guion:

* Russell, B. (1912). The problems of philosophy, cap. VI. https://www.gutenberg.org/ebooks/5827
* Taleb, N. N. (2007). The black swan. Random House, cap. 4. ISBN 978-1-4000-6351-2
* Taleb, N. N. (2020). Statistical consequences of fat tails. https://arxiv.org/abs/2001.10488
* Mandelbrot, B. (1963). The variation of certain speculative prices. https://doi.org/10.1086/294632
* Urquhart, A. (2016). The inefficiency of Bitcoin. https://doi.org/10.1016/j.econlet.2016.09.019
* Nadarajah, S. y Chu, J. (2017). On the inefficiency of Bitcoin. https://doi.org/10.1016/j.econlet.2016.10.033
* Bariviera, A. F. (2017). The inefficiency of Bitcoin revisited. https://doi.org/10.1016/j.econlet.2017.09.013
* Bariviera, A. F. et al. (2017). Some stylized facts of the Bitcoin market. https://doi.org/10.1016/j.physa.2017.04.159
* Liu, Y. y Tsyvinski, A. (2018). Risks and returns of cryptocurrency (NBER Working Paper No. 24877). https://www.nber.org/papers/w24877
* Detzel, A. et al. (2021). Learning and predictability via technical analysis. https://doi.org/10.1111/fima.12310
* Jaquart, P., Dann, D. y Weinhardt, C. (2021). Short-term bitcoin market prediction via machine learning. https://doi.org/10.1016/j.jfds.2021.03.001
* Bailey, D. H. et al. (2014). Pseudo-mathematics and financial charlatanism. https://doi.org/10.1090/noti1105
* Bailey, D. H. et al. (2017). The probability of backtest overfitting. https://doi.org/10.21314/JCF.2016.322
* Harvey, C. R., Liu, Y. y Zhu, H. (2016). … and the cross-section of expected returns. https://doi.org/10.1093/rfs/hhv059
* Shiller, R. J. (1981). Do stock prices move too much…? https://ideas.repec.org/a/aea/aecrev/v71y1981i3p421-36.html
* Keynes, J. M. (1936). The General Theory of Employment, Interest and Money, cap. 12.
* Nagel, R. (1995). Unraveling in guessing games. https://ideas.repec.org/a/aea/aecrev/v85y1995i5p1313-26.html
* Auer, R. y Claessens, S. (2018). Regulating cryptocurrencies: assessing market reactions. https://www.bis.org/publ/qtrpdf/r_qt1809f.htm
* Biais, B. et al. (2023). Equilibrium Bitcoin pricing. https://doi.org/10.1111/jofi.13206
* Cheah, E.-T. y Fry, J. (2015). Speculative bubbles in Bitcoin markets? https://doi.org/10.1016/j.econlet.2015.02.029
* Bikhchandani, S., Hirshleifer, D. y Welch, I. (1992). Informational cascades. https://doi.org/10.1086/261849
* Bouri, E., Gupta, R. y Roubaud, D. (2019). Herding behaviour in cryptocurrencies. https://doi.org/10.1016/j.frl.2018.07.008
* Lux, T. y Marchesi, M. (1999). Scaling and criticality in a stochastic multi-agent model of a financial market. https://doi.org/10.1038/17290
* Arthur, W. B. et al. (1997). Asset pricing under endogenous expectations in an artificial stock market. https://doi.org/10.1201/9780429496639-2
* Cornelli, G. et al. (2023). Crypto shocks and retail losses (BIS Bulletin 69). https://www.bis.org/publications/bulletin-69-crypto-shocks-and-retail-losses.pdf
* Gandal, N. et al. (2018). Price manipulation in the Bitcoin ecosystem. https://doi.org/10.1016/j.jmoneco.2017.12.004
* Cong, L. W. et al. (2023). Crypto wash trading. https://doi.org/10.1287/mnsc.2021.02709
* Xu, J. y Livshits, B. (2019). The anatomy of a cryptocurrency pump-and-dump scheme. https://www.usenix.org/conference/usenixsecurity19/presentation/xu-jiahua
* Hamrick, J. T. et al. (2021). An examination of the cryptocurrency pump-and-dump ecosystem. https://doi.org/10.1016/j.ipm.2021.102506
* SEC (2024). Terraform and Kwon to pay $4.5 billion following fraud verdict. https://www.sec.gov/newsroom/press-releases/2024-73
* Fiscalía SDNY (2024). Samuel Bankman-Fried sentenced to 25 years in prison. https://www.justice.gov/usao-sdny/pr/samuel-bankman-fried-sentenced-25-years-prison
* FBI IC3 (2026). 2025 IC3 annual report. https://www.ic3.gov/AnnualReport/Reports/2025_IC3Report.pdf
* Chague, F., De-Losso, R. y Giovannetti, B. (2020). Day trading for a living? https://doi.org/10.2139/ssrn.3423101
* Barber, B. M. et al. (2014). The cross-section of speculator skill. https://doi.org/10.1016/j.finmar.2013.05.006

## Instalación

Desde la raíz del repositorio:

```bash
cd el_pavo_02
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Solo usa bibliotecas libres (pygame-ce, numpy, scipy, powerlaw, arch, pandas y xlrd). Las fuentes, con licencia OFL, están en `fonts/`, y el logo está en `assets/logo_marca.png`.

## Uso en vivo

```bash
.venv/bin/python simulador.py              # ventana ajustada a la pantalla
.venv/bin/python simulador.py --full       # pantalla completa 1920×1080
.venv/bin/python simulador.py --escena s4  # empezar en una escena
```

| Tecla | Acción |
| --- | --- |
| 1 … 9 | Cambiar de escena |
| Espacio | Pausa |
| R | Reiniciar |
| F | Pantalla completa o ventana |
| Esc | Salir |

## Grabar las tomas

Hace falta [ffmpeg](https://ffmpeg.org/) en el PATH. `grabar.py` no abre ninguna ventana. Manda los cuadros directo a ffmpeg (H.264, 1920×1080, 30 cuadros por segundo, yuv420p, CRF 18) y deja los MP4 en `salida/`.

```bash
.venv/bin/python grabar.py               # todas las tomas → salida/
.venv/bin/python grabar.py s4            # solo una
.venv/bin/python grabar.py --foto 30 s4  # un PNG del segundo 30, para revisar
```

| Clave | Archivo en `salida/` | Duración |
| --- | --- | --- |
| `s2` | `s2_peor_dia_colas_gordas.mp4` | 58 s |
| `s3` | `s3_paseo_aleatorio.mp4` | 56 s |
| `s4` | `s4_fabrica_de_estrategias.mp4` | 58 s |
| `s5a` | `s5a_cascada.mp4` | 56 s |
| `s5b` | `s5b_lux_marchesi.mp4` | 56 s |
| `s6b` | `s6b_concurso_de_belleza.mp4` | 52 s |
| `s6c` | `s6c_shiller.mp4` | 56 s |

La escena S5b promedia 30 mundos la primera vez (tarda un par de minutos) y guarda el resultado en `salida/.cache/`. La S6c necesita internet la primera vez para bajar los datos de Shiller.

## Licencia

El código es de dominio público ([CC0 1.0](LICENSE)). Las fuentes Inter, Space Grotesk y JetBrains Mono tienen licencia SIL Open Font License; los textos de licencia están en `fonts/`.
