"""Curvas de ángulos de la pierna de golpeo (laboratorio frente a reconstrucción desde una cámara de TV virtual)
para los participantes de MoVi, alineadas con el contacto. Alimenta la figura de reconstrucción del artículo.

Condición: 25 fps, jugador de 80 px, residuos reales de retransmisión, cámara lateral (90°) y frontal (0°),
elevador oficial. Salida: resultados/ondas_movi.npz con t (s), y por cámara y ángulo (participantes × tiempo).
Uso:  python ondas_movi.py
"""
from pathlib import Path

import numpy as np
import pandas as pd

from experimento_sensibilidad import ELEVACION, resample, thigh
from golpeo.camara import film
from golpeo.cinematica import contact_frame, hip_flexion, kicking_side, knee_flexion, rigid_align
from golpeo.ensayos import movi_trials
from golpeo.h36m import to_canonical
from golpeo.ruido import ResidualBank

ROOT = Path(__file__).parent
RES = ROOT / "resultados"
FPS, H = 25, 80
T_GRID = np.arange(-0.4, 0.2001, 1 / FPS)


def aligned(series, fps, c):
    t = (np.arange(len(series)) - c) / fps
    return np.interp(T_GRID, t, series, left=np.nan, right=np.nan)


def main():
    from golpeo.elevador import Lifter
    lifter = Lifter()
    bank = ResidualBank.from_frame(pd.read_csv(RES / "error2d_3dsp.csv"))
    out = {f"{who}_{cam}_{ang}": [] for who in ("lab", "est") for cam in ("lateral", "frontal") for ang in ("knee", "hip")}
    for n, e in enumerate(movi_trials()):
        side = kicking_side(e.seq, e.fps)
        t_c = contact_frame(e.seq, e.fps, side) / e.fps
        x17r = resample(e.x17, e.fps, FPS)
        gt8 = to_canonical(x17r)
        c = int(round(t_c * FPS))
        for cam, az in (("lateral", 90), ("frontal", 0)):
            rng = np.random.default_rng([n, az])
            uv, conf = film(x17r, az, ELEVACION, H, 0, 0, rng)
            uv = uv + bank.sample(len(uv), FPS, H, rng)
            est = to_canonical(lifter.lift_person(uv, conf))
            est = rigid_align(est * thigh(gt8) / thigh(est), gt8)
            for who, seq in (("lab", gt8), ("est", est)):
                out[f"{who}_{cam}_knee"].append(aligned(knee_flexion(seq, side), FPS, c))
                out[f"{who}_{cam}_hip"].append(aligned(hip_flexion(seq, side), FPS, c))
    np.savez_compressed(RES / "ondas_movi.npz", t=T_GRID, **{k: np.array(v) for k, v in out.items()})
    print("participantes:", len(out["lab_lateral_knee"]))


if __name__ == "__main__":
    main()
