# Graba clips propios de Doom con ViZDoom (MIT) + Freedoom (BSD). CC0 (este script).
# Doom corre a 35 tics/s; cada tic es un cuadro. Se escala x3 con vecino más cercano
# (640x360 -> 1920x1080, pixelado nítido) y ffmpeg lo pasa a 60 fps (duplicando cuadros).
import vizdoom as vzd, numpy as np, os, subprocess, sys, json
OUT=os.path.abspath(os.path.join(os.path.dirname(__file__),"..","salida","broll")); os.makedirs(OUT,exist_ok=True)
def writer(path):
    return subprocess.Popen(["ffmpeg","-y","-loglevel","error","-f","rawvideo","-pix_fmt","rgb24","-s","640x360","-r","35","-i","-",
        "-vf","scale=1920:1080:flags=neighbor,fps=60","-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p",path],stdin=subprocess.PIPE)
def base(cfg,hud=False):
    g=vzd.DoomGame(); g.load_config(os.path.join(vzd.scenarios_path,cfg))
    g.set_window_visible(False); g.set_screen_resolution(vzd.ScreenResolution.RES_640X360)
    g.set_screen_format(vzd.ScreenFormat.RGB24); g.set_render_hud(hud); g.set_labels_buffer_enabled(True)
    g.set_depth_buffer_enabled(True); g.set_sound_enabled(False); g.set_render_messages(False)
    return g
# ---------- take_cover ----------
def esquivador(s):
    """Agente simple: mira las bolas de fuego (etiquetas de ViZDoom) y se aparta de la más grande/cercana al centro."""
    balls=[l for l in s.labels if l.object_name=="DoomImpBall"]
    if not balls: return [0,0]
    b=max(balls,key=lambda l:l.width*l.height)
    cx=b.x+b.width/2
    if abs(cx-320)>160: return [0,0]
    return [1,0] if cx>=320 else [0,1]   # [MOVE_LEFT, MOVE_RIGHT]
def take_cover(nombre,politica,seed,max_tics=2100,min_tics=0,intentos=40):
    g=base("take_cover.cfg"); g.set_episode_timeout(max_tics); g.set_seed(seed); g.init()
    rng=np.random.default_rng(seed)
    for k in range(intentos):
        frames=[]; g.new_episode(); a=[0,0]
        while not g.is_episode_finished():
            s=g.get_state(); frames.append(s.screen_buffer.copy())
            if politica=="aleatorio":
                a=[[1,0],[0,0],[0,1]][rng.integers(3)]
            else: a=esquivador(s)
            g.make_action(a)
        if len(frames)>=min_tics: break
    for _ in range(35): frames.append(frames[-1])  # medio segundo congelado al morir
    w=writer(os.path.join(OUT,nombre))
    for f in frames: w.stdin.write(f.tobytes())
    w.stdin.close(); w.wait(); g.close()
    return len(frames)-35
# ---------- Freedoom ----------
def explorador(path,mapa,seed,tics,skill=3):
    g=base("freedoom2.cfg",hud=True); g.set_doom_map(mapa); g.set_doom_skill(skill); g.set_seed(seed)
    g.set_episode_timeout(tics+10); g.init(); g.new_episode(); g.send_game_command("iddqd")
    btn=[str(b).split(".")[1].split(":")[0] for b in g.get_available_buttons()]; I={b:i for i,b in enumerate(btn)}
    rng=np.random.default_rng(seed); turn=0; w=writer(path); n=0; giro_dir=1; caza=0; ignora=0
    ENEM={"Zombieman","ShotgunGuy","DoomImp","Demon","Spectre","ChaingunGuy","LostSoul","Cacodemon","HellKnight","BaronOfHell","Revenant","Arachnotron","Fatso","PainElemental","WolfensteinSS","Archvile"}
    while not g.is_episode_finished() and n<tics:
        s=g.get_state(); w.stdin.write(s.screen_buffer.tobytes()); n+=1
        a=[0]*len(btn); d=s.depth_buffer
        ene=[l for l in s.labels if l.object_name in ENEM and l.width*l.height>150]
        if ene and ignora==0: caza+=1
        else: caza=0
        if ignora>0: ignora-=1
        if caza>70: caza=0; ignora=105; turn=int(rng.integers(15,30))
        if ene and ignora==0:
            e=max(ene,key=lambda l:l.width*l.height); cx=e.x+e.width/2
            if cx<300: a[I["TURN_LEFT"]]=1
            elif cx>340: a[I["TURN_RIGHT"]]=1
            if abs(cx-320)<60: a[I["ATTACK"]]=1
        else:
            frente=np.median(d[150:210,280:360])
            if turn>0:
                a[I["TURN_LEFT" if giro_dir>0 else "TURN_RIGHT"]]=1; turn-=1
            elif frente<18:
                turn=int(rng.integers(8,20)); giro_dir=1 if np.median(d[150:210,:200])>np.median(d[150:210,440:]) else -1
                a[I["USE"]]=1
            else:
                a[I["MOVE_FORWARD"]]=1; a[I["SPEED"]]=1
                izq,der=np.median(d[150:210,60:200]),np.median(d[150:210,440:580])
                if izq<10: a[I["TURN_RIGHT"]]=1
                elif der<10: a[I["TURN_LEFT"]]=1
                if n%140<4: a[I["USE"]]=1
        g.make_action(a)
    w.stdin.close(); w.wait(); g.close(); return n
if __name__=="__main__":
    info={}
    if len(sys.argv)>1 and sys.argv[1]=="freedoom":
        for m,sd in [(x,int(x[-2:])) for x in sys.argv[2:]]:
            nm=f"freedoom2_{m.lower()}_recorrido.mp4"; info[nm]=explorador(os.path.join(OUT,nm),m,sd,35*25)
        print(info); sys.exit()
    info["takecover_aleatorio_01.mp4"]=take_cover("takecover_aleatorio_01.mp4","aleatorio",1)
    info["takecover_aleatorio_02.mp4"]=take_cover("takecover_aleatorio_02.mp4","aleatorio",7)
    info["takecover_esquivador_01.mp4"]=take_cover("takecover_esquivador_01.mp4","esquivador",3,min_tics=500)
    info["takecover_esquivador_02.mp4"]=take_cover("takecover_esquivador_02.mp4","esquivador",11,min_tics=500)
    for i,(m,sd) in enumerate([("MAP01",1),("MAP02",2),("MAP03",3),("MAP07",4)]):
        nm=f"freedoom2_{m.lower()}_recorrido.mp4"; info[nm]=explorador(os.path.join(OUT,nm),m,sd,35*25)
    json.dump(info,open(os.path.join(OUT,"tics_por_clip.json"),"w"),indent=1)
    print(info)
