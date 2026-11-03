"""S5a · Cascada informativa (Bikhchandani, Hirshleifer y Welch 1992).

Dos restaurantes, A y B. El bueno es A (los agentes no lo saben). Cada agente
recibe una corazonada privada que acierta con probabilidad P, ve lo que
eligieron todos los anteriores y elige el restaurante más probable según la
regla de Bayes. Con previa 50/50 y corazonadas simétricas, lo que cuenta es la
ventaja d = (corazonadas por A deducidas) − (por B). Si empata, sigue su propia
corazonada. Cuando |d| llega a 2, la corazonada propia ya no puede cambiar la
decisión: todos copian y sus elecciones dejan de revelar información (cascada).

Señal pública: antes del agente K_PUB se anuncia una señal pública que acierta
con probabilidad Q, elegida para que valga exactamente dos corazonadas
(log-verosimilitud doble).
"""
import numpy as np

N = 50
P = 0.6
Q = P ** 2 / (P ** 2 + (1 - P) ** 2)       # vale lo mismo que 2 corazonadas
PESO_PUB = 2.0
K_PUB = 26                                  # la señal pública llega antes de este agente (1..N)


def correr(semilla, publica=True, n=N, p=P, k_pub=K_PUB):
    """Devuelve un dict con señales, elecciones y la ventaja deducida."""
    rng = np.random.default_rng(semilla)
    senal = np.where(rng.random(n) < p, 1, -1)          # +1 = corazonada por A (la buena)
    s_pub = 1 if rng.random() < Q else -1
    d = 0.0                                             # ventaja deducida de elecciones previas
    accion = np.zeros(n, int)
    ventaja = np.zeros(n)                               # lo que ve cada agente antes de elegir
    copia = np.zeros(n, bool)                           # en cascada: su señal no cambia nada
    for i in range(n):
        base = d + (PESO_PUB * s_pub if (publica and i >= k_pub - 1) else 0.0)
        ventaja[i] = base
        tot = base + senal[i]
        accion[i] = senal[i] if tot == 0 else (1 if tot > 0 else -1)
        if abs(base) > 1:
            copia[i] = True                                # elección no informativa
        else:
            d += senal[i]                                  # los demás deducen su señal
    contra = accion != senal
    return dict(senal=senal, accion=accion, ventaja=ventaja, copia=copia,
                contra=contra, s_pub=s_pub, publica=publica)


def inicio_cascada(run, hasta=None):
    c = run["copia"][:hasta] if hasta else run["copia"]
    idx = np.nonzero(c)[0]
    return int(idx[0]) if len(idx) else None


def resumen(run, k_pub=K_PUB):
    a, s = run["accion"], run["senal"]
    antes = slice(0, k_pub - 1)
    return dict(
        cascada_mala_antes=bool(run["copia"][k_pub - 2] and a[k_pub - 2] == -1),
        senales_A_antes=int((s[antes] == 1).sum()),
        eligieron_A_antes=int((a[antes] == 1).sum()),
        final=int(a[-1]),
        contra=int(run["contra"].sum()),
    )


def muchas(n=10000, semilla0=100000):
    """Con y sin señal pública: ¿en cuántos mundos termina la fila eligiendo B?"""
    sin_mal = con_mal = mal_antes = rotas = 0
    contra = 0
    for s in range(semilla0, semilla0 + n):
        r0 = correr(s, publica=False)
        r1 = correr(s, publica=True)
        sin_mal += r0["accion"][-1] == -1
        con_mal += r1["accion"][-1] == -1
        contra += r0["contra"].mean()
        if r0["copia"][K_PUB - 2] and r0["accion"][K_PUB - 2] == -1:
            mal_antes += 1
            rotas += r1["accion"][-1] == 1
    return dict(n=n, sin_mal=sin_mal / n, con_mal=con_mal / n, mal_antes=mal_antes / n,
                rotas=rotas / max(1, mal_antes), contra=contra / n)


def buscar_semilla(desde=0, hasta=2000):
    """Primer mundo que ilustra todo: cascada equivocada temprana, mayoría de
    corazonadas a favor de A antes de la señal, señal pública correcta, y una
    nueva cascada correcta al final."""
    for s in range(desde, hasta):
        r = correr(s)
        i0 = inicio_cascada(r)
        if i0 is None or i0 > 8 or r["accion"][i0] != -1:
            continue
        res = resumen(r)
        if (res["cascada_mala_antes"] and r["s_pub"] == 1 and res["final"] == 1
                and res["senales_A_antes"] > (K_PUB - 1) / 2 and r["copia"][-1]):
            return s
    return None


if __name__ == "__main__":
    s = buscar_semilla()
    r = correr(s)
    print("semilla", s, "Q", round(Q, 3), "inicio cascada", inicio_cascada(r) + 1, resumen(r))
    print("acciones", "".join("A" if x == 1 else "B" for x in r["accion"]))
    print("señales ", "".join("A" if x == 1 else "B" for x in r["senal"]))
    print(muchas())
