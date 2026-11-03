"""S6b · El concurso de belleza de Keynes, en la versión de Nagel (1995).

Cada jugador elige un número de 0 a 100; gana quien quede más cerca de 2/3 del
promedio. Modelo de pasos de razonamiento (nivel k), como en Nagel (p. 1315):
nivel 0 elige al azar alrededor de un ancla, nivel k elige ancla · (2/3)^k.
En la ronda 1 el ancla es 50 (nivel 0 elige uniforme entre 0 y 100); en las
siguientes, el ancla es el promedio de la ronda anterior (aprendizaje simple).

Las proporciones de niveles son un SUPUESTO del canal, no un dato.
"""
import numpy as np

P = 2 / 3
NIVELES = np.array([0, 1, 2, 3])
PROPORCIONES = np.array([0.35, 0.35, 0.20, 0.10])     # supuesto declarado
RONDAS = 4
N_JUG = 1000
RUIDO = 0.12            # desviación relativa de cada elección alrededor de su objetivo


def jugar(semilla=1995, n=N_JUG, rondas=RONDAS, prop=PROPORCIONES):
    rng = np.random.default_rng(semilla)
    nivel = rng.choice(NIVELES, size=n, p=prop)
    elecciones = []
    ancla = 50.0
    for r in range(rondas):
        objetivo = ancla * P ** nivel
        x = objetivo * (1 + RUIDO * rng.standard_normal(n)) + rng.normal(0, 1.0, n)
        if r == 0:
            l0 = nivel == 0
            x[l0] = rng.uniform(0, 100, l0.sum())
        else:
            l0 = nivel == 0
            x[l0] = ancla * (1 + 0.35 * rng.standard_normal(l0.sum()))
        x = np.clip(x, 0, 100)
        elecciones.append(x)
        ancla = float(x.mean())
    E = np.array(elecciones)
    medias = E.mean(1)
    return dict(nivel=nivel, E=E, medias=medias, medianas=np.median(E, 1), ganador=P * medias,
                ceros=(E < 0.5).mean(1))


def grupos(n_grupos=1000, tam=16, semilla0=20000):
    """Media de la ronda 1 en grupos chicos como los de Nagel (15 a 18 personas)."""
    m = np.array([jugar(s, n=tam, rondas=1)["medias"][0] for s in range(semilla0, semilla0 + n_grupos)])
    return dict(n=n_grupos, tam=tam, p5=float(np.percentile(m, 5)), p50=float(np.median(m)),
                p95=float(np.percentile(m, 95)), media=float(m.mean()))


if __name__ == "__main__":
    j = jugar()
    print("medias", j["medias"].round(2), "medianas", j["medianas"].round(1), "ceros", j["ceros"])
    print(grupos())
