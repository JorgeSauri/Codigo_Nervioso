"""S6c · El precio que debió ser (Shiller 1981, «Do stock prices move too much…»).

Datos reales: precio, dividendos e índice de precios del S&P desde 1871, de
Robert J. Shiller (https://shillerdata.com/). El archivo se DESCARGA al correr
y se guarda en datos/ (excluido del repositorio); no se redistribuye.

Método, como en Shiller (1981, pp. 421, 430-431, apéndice):
  · Precio real de enero (P) y dividendo real del año calendario (D, promedio
    de la tasa anual mensual que publica Shiller).
  · Tendencia exponencial: regresión de ln P contra el tiempo; se dividen P y D
    entre la tendencia (p, d).
  · Tasa de descuento real constante r = promedio de d / promedio de p.
  · p*_t = (p*_{t+1} + d_t) / (1 + r), con valor terminal p*_T = promedio de p.
  · Desigualdad de Shiller: σ(p) ≤ σ(p*). Se reporta σ(p) / σ(p*).
El año final de la muestra cambia la tendencia, r y el valor terminal, y con
ello todo p*; por eso se calcula también con la muestra 1871-1979 de Shiller.
"""
import os
import re
import urllib.request

import numpy as np

CARPETA = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "datos")
ARCHIVO = os.path.join(CARPETA, "ie_data.xls")
PORTADA = "https://shillerdata.com/"
URL_RESPALDO = ("https://img1.wsimg.com/blobby/go/e5e77e0b-59d1-44d9-ab25-4763ac982e53/downloads/"
                "1449043e-a1ed-4e2e-8e9c-7b9a2a064493/ie_data.xls")
UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) codigo-nervioso-simulador"}


class DescargaFallida(RuntimeError):
    pass


def _get(url, timeout=60):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def descargar(forzar=False):
    """Baja ie_data.xls de shillerdata.com a datos/. Devuelve la ruta."""
    if os.path.exists(ARCHIVO) and not forzar:
        return ARCHIVO
    os.makedirs(CARPETA, exist_ok=True)
    errores, urls = [], []
    try:
        html = _get(PORTADA).decode("utf-8", "replace")
        m = re.search(r'(?:https?:)?//[^"\'\s]+?ie_data\.xls[^"\'\s]*', html)
        if m:
            u = m.group(0)
            urls.append("https:" + u if u.startswith("//") else u)
    except Exception as e:                       # noqa: BLE001
        errores.append(f"portada: {e}")
    urls.append(URL_RESPALDO)
    for u in urls:
        try:
            datos = _get(u)
            if datos[:4] != b"\xd0\xcf\x11\xe0":  # firma de un .xls (OLE2)
                raise ValueError("la respuesta no es un archivo .xls")
            with open(ARCHIVO, "wb") as f:
                f.write(datos)
            return ARCHIVO
        except Exception as e:                   # noqa: BLE001
            errores.append(f"{u}: {e}")
    raise DescargaFallida("No se pudieron descargar los datos de Shiller:\n  " + "\n  ".join(errores))


def leer_mensual(ruta=None):
    import pandas as pd
    df = pd.read_excel(ruta or descargar(), sheet_name="Data", header=None, skiprows=8)
    fecha = pd.to_numeric(df[0], errors="coerce")
    ok = fecha.notna()
    fecha = fecha[ok].to_numpy(float)
    precio_real = pd.to_numeric(df[7][ok], errors="coerce").to_numpy(float)
    div_real = pd.to_numeric(df[8][ok], errors="coerce").to_numpy(float)
    anio = np.floor(fecha + 1e-9).astype(int)
    mes = np.rint((fecha - anio) * 100).astype(int)
    return anio, mes, precio_real, div_real


def anual(ruta=None):
    """Años completos: precio real de enero y dividendo real promedio del año."""
    anio, mes, P, D = leer_mensual(ruta)
    anios, Pa, Da = [], [], []
    for y in np.unique(anio):
        sel = anio == y
        if sel.sum() < 12 or np.isnan(D[sel]).any():
            continue
        ene = sel & (mes == 1)
        if not ene.any() or np.isnan(P[ene][0]):
            continue
        anios.append(y); Pa.append(P[ene][0]); Da.append(D[sel].mean())
    return np.array(anios), np.array(Pa), np.array(Da)


def p_estrella(anios, P, D, hasta=None):
    if hasta is not None:
        s = anios <= hasta
        anios, P, D = anios[s], P[s], D[s]
    t = anios - anios[-1]
    b, a = np.polyfit(t, np.log(P), 1)
    tend = np.exp(a + b * t)
    p, d = P / tend, D / tend
    r = d.mean() / p.mean()
    ps = np.empty_like(p)
    ps[-1] = p.mean()
    for i in range(len(p) - 2, -1, -1):
        ps[i] = (ps[i + 1] + d[i]) / (1 + r)
    return dict(anios=anios, P=P, D=D, tend=tend, p=p, d=d, ps=ps, Pstar=ps * tend, r=r,
                crec=np.exp(b) - 1, razon=p.std() / ps.std(),
                razon_cambios=np.std(np.diff(p)) / np.std(np.diff(ps)))


def calcular(ruta=None):
    anios, P, D = anual(ruta)
    total = p_estrella(anios, P, D)
    s79 = p_estrella(anios, P, D, hasta=1979)
    return dict(anios=anios, P=P, D=D, total=total, s79=s79)


if __name__ == "__main__":
    c = calcular()
    for k in ("total", "s79"):
        x = c[k]
        print(k, x["anios"][0], x["anios"][-1], "r=%.4f g=%.4f razon=%.2f razon_cambios=%.2f" %
              (x["r"], x["crec"], x["razon"], x["razon_cambios"]))
    i50 = list(c["anios"]).index(1950)
    print("P* 1950 total", c["total"]["Pstar"][i50], "s79", c["s79"]["Pstar"][i50], "P", c["P"][i50])
