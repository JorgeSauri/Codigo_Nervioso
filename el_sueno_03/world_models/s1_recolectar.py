# Paso 1 [paper]: 10,000 rollouts con política aleatoria en VizDoom «Take Cover». CC0.
import os, sys, shutil, numpy as np
import multiprocessing as mp   # 'spawn': con fork, varias instancias de ViZDoom se bloquean
import config as C
from entorno import TakeCover, PoliticaAleatoria

def trabajador(args):
    wid, semillas = args
    env = TakeCover(semilla=10_000 + wid); hechos = 0
    for s in semillas:
        if shutil.disk_usage(C.ruta()).free < 6e9:          # protección: no llenar el disco
            print("disco casi lleno; se detiene la recolección", flush=True); break
        f = C.ruta("rollouts", f"{s:05d}.npz")
        if os.path.exists(f): hechos += 1; continue
        env.g.set_seed(int(s)); rng = np.random.default_rng(s); pol = PoliticaAleatoria(rng)
        obs = [env.reset()]; acc = []; murio = False
        while True:
            a = pol(); acc.append(a)
            o, murio, fin = env.step(a)
            if fin: break
            obs.append(o)
        if len(obs) > C.MIN_LARGO:
            np.savez_compressed(f, obs=np.array(obs, np.uint8), accion=np.array(acc, np.float16), murio=murio)
            hechos += 1
    env.close(); return hechos

if __name__ == "__main__":
    os.makedirs(C.ruta("rollouts"), exist_ok=True)
    nproc = int(sys.argv[1]) if len(sys.argv) > 1 else os.cpu_count()
    # se piden semillas de más porque se descartan los rollouts cortos
    semillas = list(range(int(C.N_ROLLOUTS * 1.15)))
    partes = [(i, semillas[i::nproc]) for i in range(nproc)]
    with mp.get_context("spawn").Pool(nproc) as p: p.map(trabajador, partes)
    fs = sorted(os.listdir(C.ruta("rollouts")))
    for f in fs[C.N_ROLLOUTS:]: os.remove(C.ruta("rollouts", f))   # nos quedamos con exactamente N_ROLLOUTS
    print("rollouts guardados:", min(len(fs), C.N_ROLLOUTS))
