"""Error 2D de un detector de pose frente a anotaciones manuales de 3DSP, y modelo de ruido ajustado."""
import numpy as np
from scipy.optimize import nnls

# Índices 3DSP (por nombre) ← COCO-17 (cuerpo de COCO-WholeBody). Los puntos centrales son medias.
_FROM_COCO = {1: 11, 2: 13, 3: 15, 4: 12, 5: 14, 6: 16, 9: 0, 11: 6, 12: 8, 13: 10, 14: 5, 15: 7, 16: 9}
LIMB_JOINTS = (1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16)     # caderas, rodillas, tobillos, brazos


def coco_to_3dsp(k: np.ndarray) -> np.ndarray:
    """(≥17, 2) en orden COCO → (17, 2) en el orden y con los nombres de 3DSP."""
    out = np.zeros((17, 2))
    for i, c in _FROM_COCO.items():
        out[i] = k[c]
    out[0] = 0.5 * (k[11] + k[12])                 # Center of Hips
    out[8] = 0.5 * (k[5] + k[6])                   # Center of Shoulder
    out[7] = 0.5 * (out[0] + out[8])               # Center of Body
    out[10] = 0.5 * (k[1] + k[2])                  # Head ≈ media de los ojos (como la demo)
    return out


def player_height(kp17: np.ndarray) -> float:
    """Altura aparente del jugador: de la cabeza al tobillo más bajo, en píxeles."""
    return float(max(kp17[3, 1], kp17[6, 1]) - kp17[10, 1])


def fit_noise_model(height_px: np.ndarray, sigma_px: np.ndarray) -> tuple[float, float]:
    """Ajusta σ² = (a·H)² + b² por mínimos cuadrados no negativos. Devuelve (a, b)."""
    A = np.column_stack([np.asarray(height_px, float) ** 2, np.ones(len(height_px))])
    coef, _ = nnls(A, np.asarray(sigma_px, float) ** 2)
    return float(np.sqrt(coef[0])), float(np.sqrt(coef[1]))
