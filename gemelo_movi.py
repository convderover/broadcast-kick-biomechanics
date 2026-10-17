"""Gemelo digital de cada grabación de MoVi: ¿predice la simulación el error que se mide con imagen real?

Para cada sujeto y cámara de validar_video_movi.py se simula la misma toma con la cámara virtual
(golpeo/camara.film) usando su geometría real (azimut, elevación y distancia de la cámara calibrada) y los
mismos fotogramas de la captura (30 fps). La 2D simulada recibe tres ruidos:
  - ninguno: proyección exacta.
  - movi: residuos reales de RTMW en el vídeo de MoVi (del resto de sujetos, sin el propio).
  - 3dsp: residuos reales de RTMW en retransmisiones de la Premier League.
Si "movi" reproduce el error medido sobre la imagen real, la simulación es válida, y la variante "3dsp"
estima el error esperable en una retransmisión.

Uso:  python gemelo_movi.py   (después de validar_video_movi.py)   → resultados/gemelo_movi.csv
"""
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd

from experimento_sensibilidad import CUTOFF_GT, thigh
from golpeo.camara import film
from golpeo.carga import LOAD_NAMES, kick_loads
from golpeo.cinematica import FEATURE_NAMES, contact_frame, kick_features, kicking_side, rigid_align
from golpeo.datos_movi import load_movi
from golpeo.ensayos import fill_gaps
from golpeo.h36m import to_canonical
from golpeo.ruido import ResidualBank

ROOT = Path(__file__).parent
RES = ROOT / "resultados"
FPS_VIDEO = 30.0


def main():
    from golpeo.elevador import Lifter
    lifter = Lifter()
    real = pd.read_csv(RES / "video_movi.csv")
    geo = real.groupby(["sujeto", "camara", "altura_px"]).agg(
        az=("azimut_film", "first"), el=("elevacion", "first"), dist=("distancia_m", "first"),
        nativa=("nativa", "first")).reset_index()
    res2d = pd.read_csv(RES / "video_movi_2d.csv")
    bank_3dsp = ResidualBank.from_frame(pd.read_csv(RES / "error2d_3dsp.csv"))
    paths = {int(re.findall(r"(\d+)\.mat", p.name)[0]): p for p in (ROOT / "datos" / "movi" / "3d").glob("F_Subjects_*/*.mat")}
    rows, t0 = [], time.time()
    for n, subject in enumerate(sorted(geo.sujeto.unique())):
        tr = load_movi(paths[subject])
        tr.x17, _ = fill_gaps(tr.x17, tr.fps)            # mismo relleno que la validación (los sujetos ya filtrados)
        gt8 = to_canonical(tr.x17)
        side = kicking_side(gt8, tr.fps)
        c120 = contact_frame(gt8, tr.fps, side)
        ref = kick_features(gt8, tr.fps, contact=c120, side=side)
        ref.update(kick_loads(gt8, tr.fps, tr.mass_kg, tr.sex, contact=c120, cutoff_hz=CUTOFF_GT, side=side))
        f0 = int(np.ceil(tr.frame0 / 4))
        frames = np.arange(f0, int(np.floor((tr.frame0 + len(tr.x17) - 1) / 4)) + 1)
        idx120 = 4 * frames - tr.frame0
        x17v, gt8v = tr.x17[idx120], gt8[idx120]
        c_video = int(np.argmin(np.abs(idx120 - c120)))
        others = res2d[res2d.sujeto != subject]
        for g in geo[geo.sujeto == subject].itertuples():
            label = "native" if g.nativa else str(g.altura_px)
            bank_movi = ResidualBank.from_frame(others[others.nativa == g.nativa] if g.nativa else
                                                others[others.altura_px == g.altura_px], order="h36m", fps=FPS_VIDEO)
            for ruido in ("ninguno", "movi", "3dsp"):
                rng = np.random.default_rng([subject, int(g.altura_px), len(ruido), 0 if g.camara == "PG1" else 1])
                uv, conf = film(x17v, g.az, g.el, g.altura_px, 0.0, 0.0, rng, distance_m=g.dist)
                if ruido == "movi":
                    uv = uv + bank_movi.sample(len(uv), FPS_VIDEO, g.altura_px, rng)
                elif ruido == "3dsp":
                    uv = uv + bank_3dsp.sample(len(uv), FPS_VIDEO, g.altura_px, rng)
                est = to_canonical(lifter.lift_person(uv, conf))
                est = rigid_align(est * thigh(gt8v) / thigh(est), gt8v)
                for modo, kw in (("conocido", dict(contact=c_video, side=side)), ("auto", {})):
                    f = kick_features(est, FPS_VIDEO, **kw)
                    f.update(kick_loads(est, FPS_VIDEO, tr.mass_kg, tr.sex, cutoff_hz=min(CUTOFF_GT, 0.35 * FPS_VIDEO), **kw))
                    for k in FEATURE_NAMES + LOAD_NAMES:
                        rows.append(dict(sujeto=subject, camara=g.camara, altura_label=label, altura_px=g.altura_px,
                                         ruido=ruido, contacto=modo, rasgo=k,
                                         tipo="carga" if k in LOAD_NAMES else "postura",
                                         referencia=ref[k], estimado=f[k], error=f[k] - ref[k]))
        print(f"{n + 1} sujetos ({time.time() - t0:.0f} s)", flush=True)
        if (n + 1) % 10 == 0:                            # guardado parcial por si se interrumpe
            pd.DataFrame(rows).to_csv(RES / "gemelo_movi.csv", index=False)
    pd.DataFrame(rows).to_csv(RES / "gemelo_movi.csv", index=False)


if __name__ == "__main__":
    main()
