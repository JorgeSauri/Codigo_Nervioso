# Réplica: Dyna-Q en el Dyna Maze de Sutton & Barto (2018), cap. 8, Ejemplo 8.1 / Fig. 8.2 (pp. 164-165)
# Parámetros del libro: alpha=0.1, epsilon=0.1, gamma=0.95, Q inicial 0, empates al azar, 50 episodios; n = 0, 5, 50. CC0.
# v2 (3 nov 2026): generador de acciones y generador de planeación separados -> con la misma semilla,
# el episodio 1 es idéntico para todo n (como en el libro). Contador de "primer episodio <= 16" corregido.
# Solo CPU.
import numpy as np, json, sys
from multiprocessing import Pool
H,W=6,9; START=(2,0); GOAL=(0,8)
WALLS={(1,2),(2,2),(3,2),(4,5),(0,7),(1,7),(2,7)}   # 54 casillas, 47 libres
ACTS=[(-1,0),(1,0),(0,-1),(0,1)]
ALPHA,EPS,GAMMA,EPISODES=0.1,0.1,0.95,50
def step(s,a):
    r,c=s[0]+ACTS[a][0],s[1]+ACTS[a][1]
    if r<0 or r>=H or c<0 or c>=W or (r,c) in WALLS: r,c=s
    return (r,c),(1.0 if (r,c)==GOAL else 0.0)
def run(args):
    n,seed=args
    rng_act=np.random.default_rng([seed,0]); rng_plan=np.random.default_rng([seed,1])
    Q=np.zeros((H,W,4)); model={}; keys=[]; steps=[]
    for ep in range(EPISODES):
        s=START; k=0
        while s!=GOAL:
            if rng_act.random()<EPS: a=int(rng_act.integers(4))
            else:
                q=Q[s]; a=int(rng_act.choice(np.flatnonzero(q==q.max())))
            s2,r=step(s,a)
            Q[s][a]+=ALPHA*(r+GAMMA*Q[s2].max()*(s2!=GOAL)-Q[s][a])
            if (s,a) not in model: keys.append((s,a))
            model[(s,a)]=(s2,r)
            for _ in range(n):
                ps,pa=keys[rng_plan.integers(len(keys))]; ps2,pr=model[(ps,pa)]
                Q[ps][pa]+=ALPHA*(pr+GAMMA*Q[ps2].max()*(ps2!=GOAL)-Q[ps][pa])
            s=s2; k+=1
        steps.append(k)
    return steps
def first_ep_leq(m,thr=16):
    ok=m<=thr
    return int(np.argmax(ok))+1 if ok.any() else None
if __name__=="__main__":
    SEEDS=int(sys.argv[1]) if len(sys.argv)>1 else 1000
    free=H*W-len(WALLS); assert free==47
    out={"semillas":SEEDS,"casillas":H*W,"casillas_libres":free,"optimo":14}
    with Pool() as p:
        for n in (0,5,50):
            S=np.array(p.map(run,[(n,sd) for sd in range(SEEDS)]))
            m=S.mean(0); sd=S.std(0,ddof=1); se=sd/np.sqrt(SEEDS)
            d={}
            for e in (1,2,3,5,10,25,50):
                d[f"ep{e}"]={"media":round(float(m[e-1]),1),"error_estandar":round(float(se[e-1]),1),"desv_est":round(float(sd[e-1]),1),"mediana":float(np.median(S[:,e-1]))}
            d["primer_ep_promedio_<=16"]=first_ep_leq(m,16)
            d["primer_ep_promedio_<=18"]=first_ep_leq(m,18)  # piso con epsilon=0.1 ~16.6
            out[f"n={n}"]=d
            out.setdefault("_ep1_por_semilla_primeras5",{})[f"n={n}"]=S[:5,0].tolist()
    print(json.dumps(out,indent=1,ensure_ascii=False))
    json.dump(out,open(__import__("os").path.join(__import__("os").path.dirname(__import__("os").path.abspath(__file__)),"..","resultados","dyna_maze_resultados.json"),"w"),indent=1,ensure_ascii=False)
