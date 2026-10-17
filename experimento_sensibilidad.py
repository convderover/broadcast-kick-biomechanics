"""Estudio de sensibilidad: ¿cuánto se equivocan los rasgos y las cargas del golpeo cuando la pose 3D se
reconstruye desde una sola cámara de TV?

Verdad terreno:
  - CMU, sujetos 10 y 11: 7 golpeos de balón reales (captura óptica a 120 fps; contacto real desde el balón).
  - MoVi: 86 sujetos, un golpeo al aire cada uno (Visual3D a 120 fps; sin balón). Aporta la variabilidad
    entre sujetos que hace interpretable el ICC.
Cámara: virtual (5 ángulos × 5 tamaños del jugador × 50/25 fps).
Ruido 2D, tres modelos:
  - sin_ruido: proyección exacta.
  - gauss: gaussiano independiente con el σ(H) medido para RTMW en 3DSP (resultados/modelo_ruido.json).
  - residuos: residuos reales de RTMW en disparos de la Premier League (3DSP), remuestreados con su estructura
    temporal (golpeo/ruido.py).
Reconstrucción 3D: MotionAGFormer-B (pesos oficiales H36M) sobre un recorte centrado en el jugador; escala por
la longitud del muslo (equivale a conocer la estatura del jugador) y alineamiento rígido con la referencia
(equivale a conocer la vertical del campo).
Salidas por condición: los 6 rasgos de postura (golpeo/cinematica.py) y los 3 picos de carga articular de la
pierna de golpeo (golpeo/carga.py), con dos variantes del instante de contacto:
  - conocido: el fotograma del golpeo y la pierna se dan (anotación del analista o seguimiento del balón).
  - auto: se estiman en la pose reconstruida (pico de velocidad del tobillo), sin ninguna ayuda.

Uso:  python experimento_sensibilidad.py [cmu|movi|todo]   → resultados/sensibilidad.csv y resultados/ensayos.csv
      Evaluación del elevador ajustado (misma entrada 2D para todos): ver main().
"""
import json
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from golpeo.camara import film
from golpeo.carga import LOAD_NAMES, kick_loads
from golpeo.cinematica import FEATURE_NAMES, _ankle_speed, contact_frame, kick_features, kicking_side, rigid_align
from golpeo.ensayos import cmu_trials, movi_trials
from golpeo.h36m import to_canonical
from golpeo.ruido import ResidualBank

ROOT = Path(__file__).parent
OUT = ROOT / "resultados"
ALTURAS = (400, 200, 120, 80, 50)          # altura del jugador en píxeles
VISTAS = (0, 45, 90, 135, 180)             # 0 = de frente, 90 = lateral derecho, 180 = de espaldas
FPS = (50, 25)
ELEVACION = 15.0                           # grados, cámara elevada como en una retransmisión
SEMILLAS = {"cmu": 3, "movi": 1}           # por modelo de ruido; en MoVi la réplica la dan los 86 sujetos
CUTOFF_GT = 12.0                           # Hz, filtro de la captura óptica para la dinámica inversa


def cutoff(fps):
    """Frecuencia de corte para la pose reconstruida: 12 Hz, o menos si la Nyquist lo exige."""
    return min(CUTOFF_GT, 0.35 * fps)


def noise_models():
    """Parámetros (a, b) del ruido gaussiano σ = √((a·altura)² + b²) px por eje."""
    m = json.loads((OUT / "modelo_ruido.json").read_text())
    return {"sin_ruido": (0.0, 0.0), "gauss": (m["sigma_frac"], m["sigma_floor_px"]),
            "residuos": (0.0, 0.0)}


def resample(x, fps_in, fps_out):
    """Remuestrea en el tiempo por interpolación lineal (la captura óptica es continua)."""
    t_in = np.arange(len(x)) / fps_in
    t_out = np.arange(0, t_in[-1], 1 / fps_out)
    flat = x.reshape(len(x), -1)
    return np.stack([np.interp(t_out, t_in, flat[:, j]) for j in range(flat.shape[1])], 1).reshape(
        len(t_out), *x.shape[1:])


def thigh(seq):
    return np.nanmedian(np.linalg.norm(seq[:, 2] - seq[:, 4], axis=1))


def reference(e):
    """Rasgos y cargas de referencia de un ensayo (captura óptica a su fps original)."""
    c = None if e.contact is None else round(e.contact)
    f = kick_features(e.seq, e.fps, contact=c)
    f.update(kick_loads(e.seq, e.fps, e.mass_kg, e.sex, contact=c, cutoff_hz=CUTOFF_GT))
    return f


def main():
    """python experimento_sensibilidad.py [cmu|movi|todo] [--elevadores oficial,ruta.pth] [--sujetos 1,3,...]
    [--rapido] [--salida nombre]. Con varios elevadores, todos reciben exactamente la misma entrada 2D."""
    import argparse
    from pathlib import Path as _P
    from golpeo.elevador import Lifter
    ap = argparse.ArgumentParser()
    ap.add_argument("conjunto", nargs="?", default="todo", choices=("cmu", "movi", "todo"))
    ap.add_argument("--elevadores", default="oficial", help="'oficial' o rutas de checkpoint, separados por comas")
    ap.add_argument("--sujetos", default=None, help="sujetos de MoVi, separados por comas")
    ap.add_argument("--rapido", action="store_true", help="25 fps, 200/80/50 px, sin ruido y residuos")
    ap.add_argument("--salida", default="sensibilidad")
    ap.add_argument("--banco", default="completo", choices=("completo", "entrenamiento", "prueba"),
                    help="disparos del banco de residuos: todos o una mitad (ResidualBank.half)")
    args = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    lifters = {name: Lifter() if name == "oficial" else Lifter(ckpt=_P(name)) for name in args.elevadores.split(",")}
    tags = {name: "oficial" if name == "oficial" else _P(name).stem.split(".")[0] for name in lifters}
    ruidos = noise_models()
    fps_list, alturas = ((25,), (200, 80, 50)) if args.rapido else (FPS, ALTURAS)
    if args.rapido:
        ruidos = {k: v for k, v in ruidos.items() if k in ("sin_ruido", "residuos")}
    bank = ResidualBank.from_frame(pd.read_csv(OUT / "error2d_3dsp.csv"))
    if args.banco != "completo":
        bank = bank.half(args.banco)
    subjects = None if args.sujetos is None else {int(s) for s in args.sujetos.split(",")}
    trials = ((cmu_trials() if args.conjunto in ("cmu", "todo") else [])
              + (movi_trials(subjects=subjects) if args.conjunto in ("movi", "todo") else []))
    print(f"{len(trials)} golpeos; banco de residuos: {len(bank)} disparos; elevadores: {list(tags.values())}", flush=True)
    rows, meta, t0 = [], [], time.time()
    for n, e in enumerate(trials):
        gt = reference(e)
        side = kicking_side(e.seq, e.fps)
        t_contact = (e.contact if e.contact is not None else contact_frame(e.seq, e.fps, side)) / e.fps
        meta.append(dict(ensayo=e.id, dataset=e.dataset, sujeto=e.subject, sexo=e.sex, masa_kg=e.mass_kg,
                         lado=side, v_tobillo_max=float(np.nanmax(_ankle_speed(e.seq, e.fps, side))),
                         v_balon=e.ball_speed, contacto_real=e.contact is not None, **gt))
        for fps_out in fps_list:
            x17r = resample(e.x17, e.fps, fps_out)
            gt8r = to_canonical(x17r)
            for az in VISTAS:
                for h in alturas:
                    for ruido, (frac, floor) in ruidos.items():
                        for seed in range(1 if ruido == "sin_ruido" else SEMILLAS[e.dataset]):
                            rng = np.random.default_rng([seed, n, az, h, fps_out])
                            uv, conf = film(x17r, az, ELEVACION, h, frac, floor, rng)
                            if ruido == "residuos":
                                uv = uv + bank.sample(len(uv), fps_out, h, rng)
                            for name, lifter in lifters.items():
                                est = to_canonical(lifter.lift_person(uv, conf))
                                est = rigid_align(est * thigh(gt8r) / thigh(est), gt8r)
                                c = min(int(round(t_contact * fps_out)), len(est) - 1)
                                for modo, kw in (("conocido", dict(contact=c, side=side)), ("auto", {})):
                                    f = kick_features(est, fps_out, **kw)
                                    f.update(kick_loads(est, fps_out, e.mass_kg, e.sex, cutoff_hz=cutoff(fps_out), **kw))
                                    for k in FEATURE_NAMES + LOAD_NAMES:
                                        rows.append(dict(ensayo=e.id, dataset=e.dataset, elevador=tags[name], fps=fps_out,
                                                         vista=az, altura_px=h, ruido=ruido, semilla=seed, contacto=modo,
                                                         rasgo=k, tipo="carga" if k in LOAD_NAMES else "postura",
                                                         referencia=gt[k], estimado=f[k], error=f[k] - gt[k]))
        print(f"{n + 1}/{len(trials)} {e.id} listo ({time.time() - t0:.0f} s)", flush=True)
        if (n + 1) % 10 == 0:
            pd.DataFrame(rows).to_csv(OUT / f"{args.salida}.csv", index=False)
    pd.DataFrame(rows).to_csv(OUT / f"{args.salida}.csv", index=False)
    if args.salida == "sensibilidad":
        pd.DataFrame(meta).to_csv(OUT / "ensayos.csv", index=False)
    print(f"{len(rows)} filas en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
