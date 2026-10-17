"""Lector de MoVi (ronda F: captura óptica completa + vídeo) al esqueleto H36M de 17 puntos.

La 3D es la de Visual3D (centros articulares virtuales, mm, z arriba, 120 fps). El vídeo de las cámaras
fijas PG1/PG2 va a 30 fps: el fotograma de vídeo f corresponde al de captura 4·f (comprobado con RTMW:
error de 2–4 px en tobillos y rodillas con desfase 0 ± 2 fotogramas de captura)."""
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import scipy.io as sio

VIRTUAL = ("HEAD", "MHIP", "PELVIS", "THORAX", "LAJC", "LEJC", "LHIP", "LHJC", "LKJC", "LSJC", "LWJC", "LFJC",
           "RAJC", "REJC", "RHIP", "RHJC", "RKJC", "RSJC", "RWJC", "RFJC")   # LHJC/RHJC = mano; LHIP/RHIP = cadera
GAP = 1e6               # Visual3D marca los huecos con −999999000
VIDEO_STEP = 4          # 120 / 30


@dataclass
class MoviTrial:
    subject: int
    sex: str
    height_m: float
    mass_kg: float
    x17: np.ndarray         # (T, 17, 3) en metros, z arriba, ventana del golpeo
    fps: float
    frame0: int             # primer fotograma de captura de la ventana
    video_frame0: int       # primer fotograma de vídeo (30 fps) del movimiento "kicking"
    video_frames: int
    toes: np.ndarray        # (T, 2, 3) punto del pie (FJC) izquierdo y derecho, para la dinámica inversa


def load_movi(path: str | Path, margin_s: float = 0.5) -> MoviTrial:
    """El movimiento 'kicking' de un sujeto, con `margin_s` segundos de margen a cada lado."""
    d = sio.loadmat(str(path), simplify_cells=True)
    rec = next(v for k, v in d.items() if not k.startswith("__"))
    mv, s = rec["move"], rec["subject"]
    k = list(mv["motions_list"]).index("kicking")
    a, b = (int(v) for v in mv["flags120"][k])
    names = list(mv["markerName"])
    vn = [names[int(j) - 1] for j in np.atleast_1d(mv["virtualMarkers"])]
    loc = np.asarray(mv["virtualMarkerLocation"], float)
    m = int(round(margin_s * 120))
    lo, hi = max(a - m, 0), min(b + m, len(loc) - 1)
    V = loc[lo:hi + 1].copy()
    V[np.abs(V) > GAP] = np.nan
    V[(V == 0).all(axis=-1)] = np.nan                         # articulación sin calcular: Visual3D deja (0, 0, 0)
    V /= 1000.0
    g = lambda n: V[:, vn.index(n)]

    phys = [names[int(j) - 1] for j in np.atleast_1d(mv["physicalMarkers"])]
    P = np.asarray(mv["markerLocation"], float)[lo:hi + 1][:, [names.index(n) for n in phys]]
    P[np.abs(P) > GAP] = np.nan
    P[(P == 0).all(axis=-1)] = np.nan
    head_top = np.mean([P[:, phys.index(n)] / 1000.0 for n in ("LFHD", "RFHD", "LBHD", "RBHD")], axis=0)

    x = np.zeros((len(V), 17, 3))
    x[:, 1], x[:, 2], x[:, 3] = g("RHIP"), g("RKJC"), g("RAJC")
    x[:, 4], x[:, 5], x[:, 6] = g("LHIP"), g("LKJC"), g("LAJC")
    x[:, 0] = 0.5 * (x[:, 1] + x[:, 4])
    x[:, 11], x[:, 12], x[:, 13] = g("LSJC"), g("LEJC"), g("LWJC")
    x[:, 14], x[:, 15], x[:, 16] = g("RSJC"), g("REJC"), g("RWJC")
    x[:, 8] = 0.5 * (x[:, 11] + x[:, 14])
    x[:, 7] = 0.5 * (x[:, 0] + x[:, 8])
    x[:, 9] = g("HEAD")
    x[:, 10] = head_top
    a30, b30 = (int(v) for v in mv["flags30"][k])
    return MoviTrial(subject=int(str(s["id"]).split("_")[-1]), sex=str(s["sex"]), height_m=float(s["height"]) / 100,
                     mass_kg=float(s["mass"]), x17=x, fps=120.0, frame0=lo, video_frame0=a30,
                     video_frames=b30 - a30 + 1, toes=np.stack([g("LFJC"), g("RFJC")], axis=1))


class MoviCamera:
    """Cámara calibrada de MoVi con el convenio de MATLAB: K traspuesta, x_cam = X·R + t (mm)
    y distorsión radial de dos términos."""

    def __init__(self, K_matlab, radial, R, t):
        self.K = np.asarray(K_matlab, float).T
        self.radial = np.asarray(radial, float)
        self.R, self.t = np.asarray(R, float), np.asarray(t, float)

    @classmethod
    def load(cls, calib_dir: str | Path, cam: str) -> "MoviCamera":
        calib_dir = Path(calib_dir)
        intr = np.load(calib_dir / f"cameraParams_{cam}.npz", allow_pickle=False)
        extr = np.load(calib_dir / f"Extrinsics_{cam}.npz", allow_pickle=False)
        return cls(intr["IntrinsicMatrix"], intr["RadialDistortion"], extr["rotationMatrix"], extr["translationVector"])

    def to_camera(self, X_m: np.ndarray) -> np.ndarray:
        return (np.asarray(X_m, float) * 1000.0) @ self.R + self.t

    def project(self, X_m: np.ndarray) -> np.ndarray:
        """(..., 3) en metros (mundo) → (..., 2) en píxeles."""
        Xc = self.to_camera(X_m)
        xy = Xc[..., :2] / Xc[..., 2:3]
        r2 = (xy ** 2).sum(-1, keepdims=True)
        xy = xy * (1 + self.radial[0] * r2 + self.radial[1] * r2 ** 2)
        return xy @ self.K[:2, :2].T + self.K[:2, 2]
