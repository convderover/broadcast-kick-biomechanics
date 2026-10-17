"""Ángulos articulares y rasgos del golpeo a partir de secuencias (T, 8, 3)."""
import numpy as np

from .esqueleto import idx

UP = np.array([0.0, 0.0, 1.0])


def _unit(v):
    return v / np.linalg.norm(v, axis=-1, keepdims=True)


def _joint(seq, name):
    return seq[:, idx(name)]


def _mid(seq, a, b):
    return 0.5 * (_joint(seq, a) + _joint(seq, b))


def _dot(a, b):
    return np.sum(a * b, axis=-1)


def knee_flexion(seq: np.ndarray, side: str) -> np.ndarray:
    """180° menos el ángulo cadera–rodilla–tobillo (0 = pierna recta)."""
    hip, knee, ankle = (_joint(seq, f"{side}_{j}") for j in ("hip", "knee", "ankle"))
    cos = _dot(_unit(hip - knee), _unit(ankle - knee))
    return 180.0 - np.degrees(np.arccos(np.clip(cos, -1.0, 1.0)))


def _body_frame(seq):
    """Ejes del cuerpo: arriba (tronco), lateral (hacia la derecha) y frente."""
    up = _unit(_mid(seq, "l_shoulder", "r_shoulder") - _mid(seq, "l_hip", "r_hip"))
    lat = _joint(seq, "r_hip") - _joint(seq, "l_hip")
    lat = _unit(lat - _dot(lat, up)[:, None] * up)
    return up, lat, _unit(np.cross(up, lat))


def hip_flexion(seq: np.ndarray, side: str) -> np.ndarray:
    """Flexión de cadera con signo en el plano sagital del cuerpo (+ = muslo adelante)."""
    up, _, fwd = _body_frame(seq)
    thigh = _joint(seq, f"{side}_knee") - _joint(seq, f"{side}_hip")
    return np.degrees(np.arctan2(_dot(thigh, fwd), -_dot(thigh, up)))


def trunk_lean(seq: np.ndarray) -> np.ndarray:
    """Inclinación del tronco respecto a la vertical del mundo: columnas [sagital, lateral].
    Sagital + = hacia delante; lateral + = hacia la cadera derecha."""
    trunk = _mid(seq, "l_shoulder", "r_shoulder") - _mid(seq, "l_hip", "r_hip")
    lat = _joint(seq, "r_hip") - _joint(seq, "l_hip")
    lat_h = _unit(lat - _dot(lat, UP)[:, None] * UP)
    fwd_h = _unit(np.cross(UP, lat_h))
    vertical = _dot(trunk, UP)
    sagittal = np.degrees(np.arctan2(_dot(trunk, fwd_h), vertical))
    lateral = np.degrees(np.arctan2(_dot(trunk, lat_h), vertical))
    return np.column_stack([sagittal, lateral])


FEATURE_NAMES = (
    "rodilla_apoyo_flexion_contacto",
    "rodilla_golpeo_flexion_max",
    "cadera_golpeo_extension_max",
    "cadera_golpeo_rango",
    "tronco_inclinacion_sagital_contacto",
    "tronco_inclinacion_lateral_contacto",
)


def _ankle_speed(seq, fps, side):
    return np.linalg.norm(np.gradient(_joint(seq, f"{side}_ankle"), axis=0), axis=1) * fps


def kicking_side(seq: np.ndarray, fps: float) -> str:
    """La pierna cuyo tobillo alcanza mayor velocidad."""
    return "r" if np.nanmax(_ankle_speed(seq, fps, "r")) >= np.nanmax(_ankle_speed(seq, fps, "l")) else "l"


def contact_frame(seq: np.ndarray, fps: float, side: str) -> int:
    """Aproximación al contacto: pico de velocidad del tobillo de golpeo."""
    return int(np.nanargmax(_ankle_speed(seq, fps, side)))


def kick_features(seq: np.ndarray, fps: float, contact: int | None = None, side: str | None = None) -> dict:
    """Rasgos del golpeo. `contact` permite pasar el contacto real (p. ej. del balón) y `side` la pierna de
    golpeo; si faltan, se estiman por el pico de velocidad del tobillo."""
    side = kicking_side(seq, fps) if side is None else side
    support = "l" if side == "r" else "r"
    c = contact_frame(seq, fps, side) if contact is None else int(contact)
    w0 = max(c - int(round(0.3 * fps)), 0)
    w1 = min(c + int(round(0.2 * fps)), len(seq) - 1)
    knee_kick = knee_flexion(seq, side)
    hip_kick = hip_flexion(seq, side)
    lean = trunk_lean(seq)[c]
    return {
        "rodilla_apoyo_flexion_contacto": float(knee_flexion(seq, support)[c]),
        "rodilla_golpeo_flexion_max": float(np.nanmax(knee_kick[w0:c + 1])),
        "cadera_golpeo_extension_max": float(-np.nanmin(hip_kick[w0:c + 1])),
        "cadera_golpeo_rango": float(np.nanmax(hip_kick[w0:w1 + 1]) - np.nanmin(hip_kick[w0:w1 + 1])),
        "tronco_inclinacion_sagital_contacto": float(lean[0]),
        # positivo = hacia la pierna de apoyo
        "tronco_inclinacion_lateral_contacto": float(lean[1] if support == "r" else -lean[1]),
    }


def rigid_align(est: np.ndarray, gt: np.ndarray) -> np.ndarray:
    """Alinea est con gt (Kabsch, rotación + traslación, sin escala) usando los puntos válidos de ambos."""
    X, Y = est.reshape(-1, 3), gt.reshape(-1, 3)
    ok = np.isfinite(X).all(axis=1) & np.isfinite(Y).all(axis=1)
    mx, my = X[ok].mean(axis=0), Y[ok].mean(axis=0)
    U, _, Vt = np.linalg.svd((X[ok] - mx).T @ (Y[ok] - my))
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    rot = Vt.T @ np.diag([1.0, 1.0, d]) @ U.T
    return ((X - mx) @ rot.T + my).reshape(est.shape)
