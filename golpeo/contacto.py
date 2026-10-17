"""Instante de contacto real a partir de la trayectoria del balón."""
import numpy as np

MOVE_M = 0.03          # desplazamiento a partir del cual el balón "se ha movido"
FIT_WINDOW_S = 0.05    # tramo tras la salida usado para estimar la velocidad


def ball_contact(ball: np.ndarray, fps: float) -> tuple[float | None, float | None]:
    """Devuelve (fotograma de contacto, velocidad de salida en m/s), o (None, None) si el balón no sale.
    El contacto se extrapola hacia atrás desde la salida: el instante en que la recta de salida pasa
    por la posición de reposo. Así funciona aunque el pie tape el balón justo en el impacto."""
    valid = np.flatnonzero(np.isfinite(ball).all(axis=1))
    if len(valid) < 5:
        return None, None
    rest = np.median(ball[valid[:10]], axis=0)
    moved = valid[np.linalg.norm(ball[valid] - rest, axis=1) > MOVE_M]
    if len(moved) == 0:
        return None, None
    k = moved[0]
    window = moved[moved <= k + max(2, int(round(FIT_WINDOW_S * fps)))]
    if len(window) < 2:
        return None, None
    coef = np.polyfit(window, ball[window], 1)        # (2, 3): pendiente por fotograma y ordenada
    vel, origin = coef[0], coef[1]
    t_contact = -np.dot(origin - rest, vel) / np.dot(vel, vel)
    return float(t_contact), float(np.linalg.norm(vel) * fps)
