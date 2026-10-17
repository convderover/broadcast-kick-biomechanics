"""Golpeos con verdad terreno 3D de todos los conjuntos, en un formato común."""
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .h36m import to_canonical

ROOT = Path(__file__).parents[1]
CMU_KICKS = ("10_01", "10_02", "10_03", "10_04", "10_05", "10_06", "11_01")   # "soccer - kick ball"
CMU_MASS_KG = 75.0     # CMU no da la masa; las cargas se normalizan por ella, así que no cambia los resultados


@dataclass
class Ensayo:
    id: str
    dataset: str            # "cmu" (golpeo de balón real) o "movi" (golpeo al aire)
    subject: str
    x17: np.ndarray         # (T, 17, 3) metros, z arriba
    fps: float
    contact: float | None   # fotograma de contacto real con el balón, si se conoce
    mass_kg: float
    sex: str
    ball_speed: float | None

    @property
    def seq(self) -> np.ndarray:
        return to_canonical(self.x17)


MAX_GAP_S = 0.25        # huecos de la captura que se rellenan por interpolación lineal (práctica habitual)


def fill_gaps(x: np.ndarray, fps: float, max_gap_s: float = MAX_GAP_S) -> tuple[np.ndarray, bool]:
    """Rellena por interpolación lineal los huecos (NaN) de hasta `max_gap_s` en cada articulación.
    Devuelve (copia rellena, True si no queda ningún hueco)."""
    out = x.copy()
    t = np.arange(len(x))
    max_len = int(round(max_gap_s * fps))
    for j in range(x.shape[1]):
        bad = ~np.isfinite(x[:, j]).all(axis=-1)
        if not bad.any() or bad.all():
            continue
        edges = np.diff(np.r_[0, bad.astype(int), 0])
        for a, b in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
            if b - a <= max_len:                    # en los extremos, np.interp mantiene el último valor válido
                for d in range(x.shape[2]):
                    good = ~bad
                    out[a:b, j, d] = np.interp(t[a:b], t[good], x[good, j, d])
    return out, bool(np.isfinite(out).all())


def cmu_trials(root: Path = ROOT / "datos" / "cmu") -> list[Ensayo]:
    from .contacto import ball_contact
    from .datos_cmu import load_cmu, load_cmu_h36m
    out = []
    for name in CMU_KICKS:
        path = root / f"{name}.c3d"
        if not path.exists():
            continue
        x17, fps = load_cmu_h36m(path)
        x17, ok = fill_gaps(x17, fps)
        if not ok:
            continue
        tr = load_cmu(path)
        c, v = ball_contact(tr.ball, fps) if tr.ball is not None else (None, None)
        out.append(Ensayo(f"cmu_{name}", "cmu", name.split("_")[0], x17, fps, c, CMU_MASS_KG, "male", v))
    return out


def movi_trials(root: Path = ROOT / "datos" / "movi" / "3d", subjects=None) -> list[Ensayo]:
    from .datos_movi import load_movi
    paths = sorted(root.glob("F_Subjects_*/F_v3d_Subject_*.mat"), key=lambda p: int(re.findall(r"(\d+)\.mat", p.name)[0]))
    out = []
    for path in paths:
        n = int(re.findall(r"(\d+)\.mat", path.name)[0])
        if subjects is not None and n not in subjects:
            continue
        try:
            tr = load_movi(path)
        except (ValueError, KeyError, IndexError):        # sujeto sin el movimiento "kicking"
            continue
        x17, ok = fill_gaps(tr.x17, tr.fps)
        if not ok:                                   # hueco de más de 0,25 s en alguna articulación: se excluye
            continue
        out.append(Ensayo(f"movi_{n:02d}", "movi", str(n), x17, tr.fps, None, tr.mass_kg, tr.sex, None))
    return out
