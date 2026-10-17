"""Esqueleto Human3.6M de 17 puntos (el que usa MotionAGFormer) y su paso al canónico."""
import numpy as np

H36M_JOINTS = ("pelvis", "r_hip", "r_knee", "r_ankle", "l_hip", "l_knee", "l_ankle", "spine",
               "thorax", "neck_nose", "head", "l_shoulder", "l_elbow", "l_wrist",
               "r_shoulder", "r_elbow", "r_wrist")

# índice H36M de cada articulación del esqueleto canónico (orden de esqueleto.JOINTS)
_TO_CANONICAL = [11, 14, 4, 1, 5, 2, 6, 3]


def to_canonical(x17: np.ndarray) -> np.ndarray:
    """(T, 17, 3) → (T, 8, 3)."""
    return x17[:, _TO_CANONICAL]


_H36M_FROM_COCO = [9, 11, 14, 12, 15, 13, 16, 4, 1, 5, 2, 6, 3]     # destino H36M …
_COCO_ORDER = [0, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]       # … ← origen COCO


def coco_to_h36m(k: np.ndarray, scores: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(T, ≥17, 2) en orden COCO y sus confianzas (T, ≥17) → H36M-17 (T, 17, 2) y (T, 17), con las mismas reglas
    que la demo oficial de MotionAGFormer (demo/lib/preprocess.py): cabeza, tórax, pelvis y columna derivados."""
    k, scores = np.asarray(k, float)[:, :17], np.asarray(scores, float)[:, :17]
    out = np.zeros((len(k), 17, 2))
    head = np.stack([k[:, 1:5, 0].mean(1), k[:, 1:3, 1].sum(1) - k[:, 0, 1]], -1)
    thorax = k[:, 5:7].mean(1)
    thorax = thorax + (k[:, 0] - thorax) / 3
    out[:, [10, 8, 0, 7]] = np.stack([head, thorax, k[:, 11:13].mean(1), k[:, [5, 6, 11, 12]].mean(1)], 1)
    out[:, _H36M_FROM_COCO] = k[:, _COCO_ORDER]
    out[:, 9] -= (out[:, 9] - k[:, 5:7].mean(1)) / 4
    out[:, 7, 0] += 2 * (out[:, 7, 0] - out[:, [0, 8], 0].mean(1))
    out[:, 8, 1] -= (k[:, 1:3, 1].mean(1) - k[:, 0, 1]) * 2 / 3
    conf = np.zeros((len(k), 17))
    conf[:, _H36M_FROM_COCO] = scores[:, _COCO_ORDER]
    conf[:, 0] = scores[:, [11, 12]].mean(1)
    conf[:, 8] = scores[:, [5, 6]].mean(1)
    conf[:, 7] = conf[:, [0, 8]].mean(1)
    conf[:, 10] = scores[:, 1:5].mean(1)
    return out, conf
