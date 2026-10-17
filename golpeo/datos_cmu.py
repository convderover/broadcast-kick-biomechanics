"""Lector de los golpeos de la base CMU (sujeto 10) al esqueleto canónico."""
import warnings
from dataclasses import dataclass
from pathlib import Path

import ezc3d
import numpy as np

from .esqueleto import JOINTS

# Centros articulares virtuales del C3D (comprobados por longitudes de segmento:
# HJ0–FE0 ≈ 403 mm de muslo, FE0–TI0 ≈ 459 mm de pierna, TI0 a 48 mm del marcador de tobillo).
CMU_MAP = {
    "l_shoulder": "LCL0", "r_shoulder": "RCL0",
    "l_hip": "LHJ0", "r_hip": "RHJ0",
    "l_knee": "LFE0", "r_knee": "RFE0",
    "l_ankle": "LTI0", "r_ankle": "RTI0",
}
BALL_MARKERS = ("WEP1", "WEP2", "WEP3")


def _read(path):
    c = ezc3d.c3d(str(path))
    labels = [l.split(":")[-1] for l in c["parameters"]["POINT"]["LABELS"]["value"]]
    points = c["data"]["points"][:3, : len(labels)].transpose(2, 1, 0) / 1000.0   # (T, N, 3) m
    return labels, points, float(c["parameters"]["POINT"]["RATE"]["value"][0])


def load_cmu_h36m(path: str | Path) -> tuple[np.ndarray, float]:
    """El golpeo de CMU en el esqueleto H36M de 17 puntos que espera MotionAGFormer (metros, z arriba).
    Codo = HU0 y muñeca = WR0 (brazo de 293 mm y antebrazo de 281 mm). La cabeza se aproxima con
    HED0 (nariz) y con la media de los cuatro marcadores de la cabeza (coronilla)."""
    labels, p, fps = _read(path)
    g = lambda name: p[:, labels.index(name)]
    x = np.zeros((len(p), 17, 3))
    x[:, 1], x[:, 2], x[:, 3] = g("RHJ0"), g("RFE0"), g("RTI0")
    x[:, 4], x[:, 5], x[:, 6] = g("LHJ0"), g("LFE0"), g("LTI0")
    x[:, 0] = 0.5 * (x[:, 1] + x[:, 4])
    x[:, 11], x[:, 12], x[:, 13] = g("LCL0"), g("LHU0"), g("LWR0")
    x[:, 14], x[:, 15], x[:, 16] = g("RCL0"), g("RHU0"), g("RWR0")
    x[:, 8] = 0.5 * (x[:, 11] + x[:, 14])
    x[:, 7] = 0.5 * (x[:, 0] + x[:, 8])
    x[:, 9] = g("HED0")
    x[:, 10] = np.mean([g(m) for m in ("LFHD", "RFHD", "LBHD", "RBHD")], axis=0)
    return x, fps


@dataclass
class CmuTrial:
    seq: np.ndarray            # (T, 8, 3) en metros, z arriba
    fps: float
    ball: np.ndarray | None    # (T, 3) en metros: media de los marcadores del balón, o None


def load_cmu(path: str | Path) -> CmuTrial:
    c = ezc3d.c3d(str(path))
    labels = [l.split(":")[-1] for l in c["parameters"]["POINT"]["LABELS"]["value"]]
    points = c["data"]["points"][:3, : len(labels)].transpose(2, 1, 0) / 1000.0   # (T, N, 3) m
    seq = np.stack([points[:, labels.index(CMU_MAP[j])] for j in JOINTS], axis=1)
    ball = None
    if all(m in labels for m in BALL_MARKERS):
        markers = np.stack([points[:, labels.index(m)] for m in BALL_MARKERS])
        with warnings.catch_warnings():          # fotogramas con el balón tapado → NaN, sin aviso
            warnings.simplefilter("ignore", RuntimeWarning)
            ball = np.nanmean(markers, axis=0) if np.isfinite(markers).any() else None
    return CmuTrial(seq=seq, fps=float(c["parameters"]["POINT"]["RATE"]["value"][0]), ball=ball)
