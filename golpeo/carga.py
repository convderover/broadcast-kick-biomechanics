"""Carga articular de la pierna de golpeo por dinámica inversa (Newton–Euler) a partir de centros articulares.

Durante el balanceo la pierna de golpeo no toca el suelo (cadena abierta), así que los momentos netos en rodilla
y cadera quedan determinados por la cinemática y los parámetros inerciales de los segmentos, sin plataformas de
fuerza. Modelo:
  - Segmentos muslo (cadera→rodilla) y pierna (rodilla→tobillo) como barras con los parámetros de de Leva (1996).
  - El pie como masa puntual en el tobillo (H36M no tiene puntos del pie; así el mismo modelo vale para la
    verdad terreno y para la pose estimada desde vídeo).
  - Sin rotación axial (solo hay centros articulares): ω = u × u̇ con u la dirección del segmento.
  - Momentos expresados sobre el eje lateral del cuerpo (plano sagital): + = extensor de rodilla y flexor de cadera.
Limitaciones: no incluye la fuerza del balón (las ventanas acaban en el contacto) ni la inercia del pie.
"""
import numpy as np
from scipy.signal import butter, filtfilt

from .cinematica import _body_frame, _joint, contact_frame, hip_flexion, kicking_side

GRAVITY = np.array([0.0, 0.0, -9.81])

# de Leva (1996), J Biomech 29(9):1223–1230, tabla 4. mass = fracción de la masa corporal; com = posición del
# centro de masas desde la articulación proximal (fracción de la longitud); rg = radio de giro transversal (sagital).
DE_LEVA = {
    "male": {"thigh": {"mass": 0.1416, "com": 0.4095, "rg": 0.329},
             "shank": {"mass": 0.0433, "com": 0.4459, "rg": 0.255},
             "foot": {"mass": 0.0137}},
    "female": {"thigh": {"mass": 0.1478, "com": 0.3612, "rg": 0.369},
               "shank": {"mass": 0.0481, "com": 0.4416, "rg": 0.271},
               "foot": {"mass": 0.0129}},
}

LOAD_NAMES = (
    "momento_cadera_flexor_max",       # N·m/kg, desde el final del armado hasta el contacto (psoas, recto femoral)
    "momento_rodilla_extensor_max",    # N·m/kg, ídem (cuádriceps, recto femoral)
    "momento_rodilla_flexor_max",      # N·m/kg, en los 100 ms previos al contacto (frenado: isquiotibiales)
)


def lowpass(x: np.ndarray, fps: float, cutoff_hz: float | None, order: int = 4) -> np.ndarray:
    """Butterworth de fase cero sobre el eje 0. Rellena huecos (NaN) por interpolación lineal antes de filtrar
    y los devuelve como NaN."""
    x = np.asarray(x, float)
    flat = x.reshape(len(x), -1).copy()
    t = np.arange(len(x))
    nan = ~np.isfinite(flat)
    for j in range(flat.shape[1]):
        ok = ~nan[:, j]
        if ok.sum() >= 2 and (~ok).any():
            flat[~ok, j] = np.interp(t[~ok], t[ok], flat[ok, j])
    if cutoff_hz is not None and len(x) > 3 * (order + 1):
        b, a = butter(order, cutoff_hz / (fps / 2))
        good = np.isfinite(flat).all(axis=0)
        flat[:, good] = filtfilt(b, a, flat[:, good], axis=0)
    flat[nan] = np.nan
    return flat.reshape(x.shape)


def _deriv(x, fps):
    return np.gradient(x, axis=0) * fps


def _segment_omega(prox, dist, fps):
    u = dist - prox
    u = u / np.linalg.norm(u, axis=-1, keepdims=True)
    return np.cross(u, _deriv(u, fps))


def swing_leg_moments(seq: np.ndarray, fps: float, side: str, mass_kg: float, sex: str = "male",
                      cutoff_hz: float | None = 12.0) -> dict:
    """Momentos netos (N·m) que la articulación proximal ejerce sobre muslo y pierna, proyectados sobre el eje
    lateral del cuerpo. Devuelve series (T,): 'rodilla_momento', 'cadera_momento' y los vectores 3D."""
    p = DE_LEVA[sex if sex in DE_LEVA else "male"]
    s = lowpass(seq, fps, cutoff_hz)
    hip, knee, ankle = (_joint(s, f"{side}_{j}") for j in ("hip", "knee", "ankle"))
    m_t, m_s, m_f = (mass_kg * p[k]["mass"] for k in ("thigh", "shank", "foot"))
    L_t = np.nanmedian(np.linalg.norm(knee - hip, axis=1))
    L_s = np.nanmedian(np.linalg.norm(ankle - knee, axis=1))
    I_t, I_s = m_t * (p["thigh"]["rg"] * L_t) ** 2, m_s * (p["shank"]["rg"] * L_s) ** 2

    c_t = hip + p["thigh"]["com"] * (knee - hip)
    c_s = knee + p["shank"]["com"] * (ankle - knee)
    acc = lambda x: _deriv(_deriv(x, fps), fps)
    alpha_t = _deriv(_segment_omega(hip, knee, fps), fps)
    alpha_s = _deriv(_segment_omega(knee, ankle, fps), fps)

    F_foot_on_shank = -m_f * (acc(ankle) - GRAVITY)
    F_knee = m_s * (acc(c_s) - GRAVITY) - F_foot_on_shank            # rodilla sobre la pierna
    M_knee = I_s * alpha_s - np.cross(knee - c_s, F_knee) - np.cross(ankle - c_s, F_foot_on_shank)
    F_hip = m_t * (acc(c_t) - GRAVITY) + F_knee                       # cadera sobre el muslo
    M_hip = I_t * alpha_t - np.cross(hip - c_t, F_hip) + np.cross(knee - c_t, F_knee) + M_knee

    _, lat, _ = _body_frame(s)
    return {"rodilla_momento": np.sum(M_knee * lat, axis=-1), "cadera_momento": np.sum(M_hip * lat, axis=-1),
            "M_knee": M_knee, "M_hip": M_hip, "F_knee": F_knee, "F_hip": F_hip}


def kick_loads(seq: np.ndarray, fps: float, mass_kg: float, sex: str = "male", contact: int | None = None,
               cutoff_hz: float | None = 12.0, side: str | None = None) -> dict:
    """Picos de carga de la pierna de golpeo normalizados por la masa (N·m/kg).
    Ventana: desde el máximo armado (mínima flexión de cadera en los 0,3 s previos) hasta el contacto."""
    side = kicking_side(seq, fps) if side is None else side
    c = contact_frame(seq, fps, side) if contact is None else int(contact)
    m = swing_leg_moments(seq, fps, side, mass_kg, sex, cutoff_hz)
    w0 = max(c - int(round(0.3 * fps)), 0)
    hip = hip_flexion(lowpass(seq, fps, cutoff_hz), side)
    b = w0 + int(np.nanargmin(hip[w0:c + 1]))                        # final del armado
    b = min(b, c - 1) if c > w0 else w0
    f0 = max(c - int(round(0.1 * fps)), 0)
    kn, hp = m["rodilla_momento"], m["cadera_momento"]
    return {
        "momento_cadera_flexor_max": float(np.nanmax(hp[b:c + 1]) / mass_kg),
        "momento_rodilla_extensor_max": float(np.nanmax(kn[b:c + 1]) / mass_kg),
        "momento_rodilla_flexor_max": float(np.nanmax(-kn[f0:c + 1]) / mass_kg),
    }
