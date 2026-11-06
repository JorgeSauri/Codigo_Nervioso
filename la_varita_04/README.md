# La varita · episodio 4

Demos del episodio **«¿Por qué es tan fácil usarla mal?»** del canal Código Nervioso.

Este episodio es la excepción del repo: no hay Python de entrenamiento, ni PyTorch, ni GPU, ni un modelo que descargar. Son cuatro páginas HTML, CSS y JavaScript. Corren en el navegador, sin paso de build.

El video se estrena el **19 de noviembre de 2026**. El enlace del video se agrega cuando exista. Canal: https://www.youtube.com/@CodigoNervioso

| Carpeta | Qué muestra |
| --- | --- |
| [`palanquitas/`](palanquitas/) | Una frase fija, siete palancas y un diccionario chiquito. El primer intento, sesgado a la playa, escribe **sandalia**. El entrenador destapa **taza** y las palancas se mueven un poco con un gradiente de juguete. |
| [`nube_embeddings/`](nube_embeddings/) | Maqueta 3D de dos vecindarios (desayuno y playa). La línea sandalia→taza es la distancia del error **en este dibujo**. |
| [`linea_tiempo/`](linea_tiempo/) | De 1811 al chatbot. En cada parada: qué se perdió, qué se ganó y la fuente. No anuncia extinción de oficios, lenguajes ni interfaces. |
| [`inspector_huecos/`](inspector_huecos/) | El plan de doña Lupe, pintado con reglas escritas a mano: lo que tú diste, lo que el texto supone y lo que solo tú puedes observar. |

En todas las pantallas hay un rótulo visible: «Ilustración del mecanismo, no un LLM real» o «Demo ilustrativa». El inspector, además, dice que no es un detector automático.

## Cómo abrirla

Hace falta un navegador moderno. No hace falta `npm`, ni un entorno virtual, ni red (salvo que el navegador tenga que leer las fuentes locales, que ya vienen en la carpeta).

Desde el administrador de archivos, abre `la_varita_04/index.html`. Eso es un `file://`.

O, si prefieres un servidor mínimo:

```bash
cd la_varita_04
python3 -m http.server 8765
```

Luego entra a http://127.0.0.1:8765/

La nube **no** usa three.js ni Plotly. Un CDN se cae sin internet y el criterio de esta carpeta es que abra también en `file://`. El giro 3D es un proyector chico en un `<canvas>` (`nube_embeddings/app.js`). No hay que instalar nada.

## Qué no hace

- No entrena un modelo ni baja pesos.
- No trae un vocabulario de ~200&nbsp;000 palabras. Ese número, en palanquitas, está rotulado como **ilustrativo**. El archivo tiene unas decenas de palabras curadas.
- No calcula embeddings. Los puntos de la nube son coordenadas escritas a mano. El rótulo dice «proyección simplificada».
- No detecta errores en un plan cualquiera. El inspector solo pinta las frases de **este** ejemplo.
- No dice que una tecnología vuelva inevitable el fin de un oficio, de un lenguaje o de una interfaz.

## Controles

### Palanquitas

- **Palancas.** Siete sliders. El puntaje de cada palabra es el producto punto con su vector. Las barras son un softmax con temperatura 1.35, para que se vean.
- **Primer intento.** Unos números al azar y luego el sesgo de playa. Tiene que quedar **sandalia**.
- **Entrenador.** Destapa **taza**, dibuja la flecha de error y da **un** paso corto de gradiente (la entropía cruzada respecto a taza). Un paso no alcanza: sandalia sigue arriba.
- **Montaje.** Varios pasos de verdad, y un contador que sube hasta 12&nbsp;000. El contador es teatro: no hay corpus. Los pasos sí mueven las palancas.
- **Reiniciar.** Vuelve al sesgo de playa.
- **Ver pedacitos / ver palabras.** Parte la frase en fichas de colores. No es un tokenizador real.

### Nube

- Arrastra para girar. La rueda del mouse acerca o aleja.
- **Vista general, vecindario desayuno, vecindario playa, línea del error.** Mueven la cámara.
- **Siguiente apuesta.** Un punto sale de sandalia y cae junto a taza.
- **Taller / mostrador.** En el taller la línea es el error y las posiciones no se entrenan. En el mostrador aparece la frase y una raya de «café» al hueco: es un dibujo de la atención, no los pesos de un transformer.

### Línea de tiempo

- Desliza de lado, o usa **Anterior / Siguiente**, los puntos de arriba o las flechas del teclado.
- En pantalla angosta las paradas se apilan.
- 1811 y 1830 llevan ilustración tipo grabado hecha para esta demo, no un grabado de archivo.
- Oficina y render llevan, en la propia ficha, «recuerdo del autor» y «caso personal». No son estudios.

### Inspector de huecos

- El plan de ejemplo ya viene pegado. **Inspeccionar** aplica las reglas.
- Toca un tramo de color para leer la regla que lo pintó.
- Los tres botones de la libreta prenden o apagan un color.
- **Restaurar el ejemplo** devuelve el texto de doña Lupe.
- Si editas el plan, solo se colorea la frase que coincide con una regla. El resto queda en blanco. La libreta (coches, olor, tamales, puesto de jugos) es una recreación del ejemplo, no un censo.

## Referencias

No inventamos DOI. Abajo va el identificador cuando está en el brief del episodio o cuando la página de la revista lo muestra en la URL que consultamos. Si no, la ficha se queda en autor, año y publicación.

### El mecanismo que las demos ilustran, y no reproducen

- Shannon, C. E. (1951). Prediction and entropy of printed English. *Bell System Technical Journal*.
- Bengio, Y., Ducharme, R., Vincent, P. y Jauvin, C. (2003). A neural probabilistic language model. *Journal of Machine Learning Research*.
- Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., Kaiser, Ł. y Polosukhin, I. (2017). Attention is all you need. *Advances in Neural Information Processing Systems*.

Las rayas de la nube no son esa atención. El softmax de palanquitas es el gesto, con siete números, no un modelo de lenguaje.

### Contexto del episodio, no de estas sims

- Jumper, J., Evans, R., Pritzel, A., Green, T., Figurnov, M., Ronneberger, O. y colaboradores (2021). Highly accurate protein structure prediction with AlphaFold. *Nature*. https://doi.org/10.1038/s41586-021-03819-2

Aquí no simulamos plegamiento de proteínas.

### Línea de tiempo

- Mokyr, J., Vickers, C. y Ziebarth, N. L. (2015). The history of technological anxiety and the future of economic growth: Is this time different? *Journal of Economic Perspectives, 29*(3), 31–50. La parada de 1811 y la de 1830 usan su advertencia: se ha exagerado mucho cuánto de los motines luditas (1811–1816) y de Captain Swing (1830–1832) fue miedo a ser reemplazados por la máquina. No pegamos una cita textual larga.
- Orben, A. (2020). The Sisyphean cycle of technology panics. *Perspectives on Psychological Science*. https://doi.org/10.1177/1745691620919372
- Preston, M. I. (1941). Children's reactions to movie horrors and radio crime. *The Journal of Pediatrics*. Llega a la parada de 1941 **vía Orben**, sin cita textual de Preston.
- Weizenbaum, J. (1966). ELIZA—a computer program for the study of natural language communication between man and machine. *Communications of the ACM*. El diálogo de la pantalla es inventado para la demo; no es una transcripción del artículo.
- Cave, S. y Dihal, K. (2019). Hopes and fears for intelligent machines in fiction and reality. *Nature Machine Intelligence*.
- Autor, D. H. (2015). Why are there still so many jobs? The history and future of workplace automation. *Journal of Economic Perspectives, 29*(3).

Las paradas de la oficina y del render **no** citan paper: están rotuladas como recuerdo del autor y caso personal.

### Cómo se usa un generador, y lo fácil que es no atinarle

- Liu, M. X., Sarkar, A., Negreanu, C., Zorn, B., Williams, J., Toronto, N. y Gordon, A. D. (2023). «What it wants me to say»: Bridging the abstraction gap between end-user programmers and code-generating large language models. *CHI 2023*. arXiv:2304.06597. https://arxiv.org/abs/2304.06597
- Ross, S. I., Martinez, F., Houde, S., Muller, M. y Weisz, J. D. (2023). The programmer's assistant: Conversational interaction with a large language model for software development. *Proceedings of the 28th International Conference on Intelligent User Interfaces (IUI '23)*, 491–514.
- Barke, S., James, M. B. y Polikarpova, N. (2023). Grounded Copilot: How programmers interact with code-generating models. *Proceedings of the ACM on Programming Languages, 7*(OOPSLA1), artículo 78. https://cseweb.ucsd.edu/~npolikarpova/publications/oopsla23-copilot.pdf

## Licencia

Código de esta carpeta en [CC0 1.0](LICENSE), igual que el resto del repo.

Inter, Space Grotesk y JetBrains Mono **no** son CC0. Siguen con la SIL Open Font License 1.1. El texto está en `fuentes/OFL-Inter.txt`, `fuentes/OFL-SpaceGrotesk.txt` y `fuentes/OFL-JetBrainsMono.txt`. Los archivos se copiaron de `el_pavo_02/fonts/`.
