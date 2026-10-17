"""Golpeo sintético con cinemática conocida, para tests."""
import numpy as np

from golpeo.esqueleto import JOINTS, idx

THIGH, SHANK = 0.45, 0.45


def _leg(hip, theta_deg, knee_deg):
    """Rodilla y tobillo para una flexión de cadera theta (+ = adelante, hacia +y) y de rodilla."""
    th, sh = np.radians(theta_deg), np.radians(theta_deg - knee_deg)
    knee = hip + THIGH * np.stack([np.zeros_like(th), np.sin(th), -np.cos(th)], axis=-1)
    ankle = knee + SHANK * np.stack([np.zeros_like(sh), np.sin(sh), -np.cos(sh)], axis=-1)
    return knee, ankle


def kick_sequence(fps: int = 100, side: str = "r", contact_s: float = 0.5, T_s: float = 1.0,
                  support_knee: float = 20.0, lateral_lean: float = 8.0) -> np.ndarray:
    """Pierna `side` en péndulo con pico de velocidad del tobillo cerca de `contact_s`.
    Mira a +y y la cadera derecha está en +x. Tronco inclinado `lateral_lean` grados hacia la pierna de apoyo."""
    t = np.arange(int(round(T_s * fps))) / fps
    T = len(t)
    seq = np.zeros((T, len(JOINTS), 3))
    sign = {"r": 1.0, "l": -1.0}
    support = "l" if side == "r" else "r"
    for s in ("l", "r"):
        seq[:, idx(f"{s}_hip")] = [0.1 * sign[s], 0.0, 1.0]
    hip_angle = 10 + 50 * np.tanh((t - contact_s) / 0.08)               # de −40° a +60°
    knee_angle = 90 * np.exp(-(((t - (contact_s - 0.12)) / 0.07) ** 2))  # carga y extensión
    k, a = _leg(seq[:, idx(f"{side}_hip")], hip_angle, knee_angle)
    seq[:, idx(f"{side}_knee")], seq[:, idx(f"{side}_ankle")] = k, a
    k, a = _leg(seq[:, idx(f"{support}_hip")], np.full(T, 10.0), np.full(T, support_knee))
    seq[:, idx(f"{support}_knee")], seq[:, idx(f"{support}_ankle")] = k, a
    lean = np.radians(lateral_lean) * -sign[side]      # hacia la pierna de apoyo
    mid_sh = np.array([0.5 * np.sin(lean), 0.0, 1.0 + 0.5 * np.cos(lean)])
    for s in ("l", "r"):
        seq[:, idx(f"{s}_shoulder")] = mid_sh + [0.2 * sign[s], 0.0, 0.0]
    return seq


def mirror(seq: np.ndarray) -> np.ndarray:
    """Espejo x → −x intercambiando izquierda y derecha."""
    out = seq.copy()
    out[..., 0] *= -1
    for j in ("shoulder", "hip", "knee", "ankle"):
        out[:, [idx(f"l_{j}"), idx(f"r_{j}")]] = out[:, [idx(f"r_{j}"), idx(f"l_{j}")]]
    return out
