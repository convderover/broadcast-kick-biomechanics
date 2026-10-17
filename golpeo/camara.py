"""Cámara de TV virtual: proyecta un esqueleto 3D a píxeles con el tamaño y el ruido de una retransmisión."""
import numpy as np

UP = np.array([0.0, 0.0, 1.0])
CONF = 0.9        # confianza constante que se pasa al elevador 3D


def _look_at(cam, target):
    f = target - cam
    f /= np.linalg.norm(f)
    r = np.cross(f, UP)
    r /= np.linalg.norm(r)
    return np.vstack([r, np.cross(f, r), f])          # filas: x (derecha), y (abajo), z (frente)


def film(x17: np.ndarray, azimuth_deg: float, elevation_deg: float, height_px: float,
         sigma_frac: float, sigma_floor_px: float, rng: np.random.Generator,
         distance_m: float = 40.0, image=(1920, 1080)) -> tuple[np.ndarray, np.ndarray]:
    """Filma (T, 17, 3) en metros (z arriba) con una cámara fija.

    azimuth 0 = de frente al jugador, 90 = desde su derecha, 180 = desde detrás.
    El zoom se ajusta para que la mediana de la altura del jugador sea `height_px`.
    Ruido 2D gaussiano por punto con σ = sqrt((sigma_frac·height_px)² + sigma_floor_px²).
    Devuelve (uv (T, 17, 2) en píxeles, conf (T, 17))."""
    uv, _, _ = camera_view(x17, azimuth_deg, elevation_deg, height_px, distance_m, image)
    sigma = np.hypot(sigma_frac * height_px, sigma_floor_px)
    if sigma > 0:
        uv = uv + rng.normal(0.0, sigma, uv.shape)
    return uv, np.full(uv.shape[:2], CONF)


def image_space_3d(uv: np.ndarray, xc: np.ndarray, focal: float) -> np.ndarray:
    """3D "en espacio imagen" (convenio de MotionBERT/MotionAGFormer): x, y = proyección en píxeles y
    z = (Z − Z_pelvis)·focal/Z_pelvis, también en píxeles. Relativo a la pelvis de cada fotograma."""
    z = focal * (xc[..., 2] - xc[:, :1, 2]) / xc[:, :1, 2]
    return np.concatenate([uv - uv[:, :1], z[..., None]], axis=-1)


def camera_view(x17: np.ndarray, azimuth_deg: float, elevation_deg: float, height_px: float,
                distance_m: float = 40.0, image=(1920, 1080)) -> tuple[np.ndarray, np.ndarray, float]:
    """Proyección exacta de `film`: (uv (T, 17, 2) px, coordenadas de cámara (T, 17, 3) m, focal px)."""
    pelvis = np.nanmedian(x17[:, 0], axis=0)
    lat = np.nanmedian(x17[:, 1] - x17[:, 4], axis=0)            # cadera izquierda → derecha
    lat = lat - lat @ UP * UP
    lat /= np.linalg.norm(lat)
    fwd = np.cross(UP, lat)
    az, el = np.radians(azimuth_deg), np.radians(elevation_deg)
    horiz = np.cos(az) * fwd + np.sin(az) * lat
    cam = pelvis + distance_m * (np.cos(el) * horiz + np.sin(el) * UP)
    rot = _look_at(cam, pelvis)

    xc = (x17 - cam) @ rot.T
    uv1 = xc[..., :2] / xc[..., 2:3]                             # plano imagen con focal 1
    focal = height_px / np.nanmedian(uv1[..., 1].max(axis=1) - uv1[..., 1].min(axis=1))
    uv = focal * uv1
    centre = 0.5 * (np.nanmin(uv.reshape(-1, 2), axis=0) + np.nanmax(uv.reshape(-1, 2), axis=0))
    uv += np.array(image) / 2 - centre
    return uv, xc, float(focal)
