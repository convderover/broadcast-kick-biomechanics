"""Ejemplo de campo: golpeos reales de balón del autor grabados con un móvil (videos/, 1080p a 60 fps).

Nombre de cada vídeo: <orden>_<toma>_<intensidad>.MOV, con toma ∈ {lateral, diagonalatras, diagonaldelante,
frente|delante} e intensidad ∈ {fuerte, suave}. Sin captura óptica: el ejemplo pone a prueba la verosimilitud
(golpeo fuerte frente a suave) y la consistencia entre resoluciones (nativa frente a 80 px), no la validez.

Por vídeo:
  1. YOLOX detecta al jugador (la caja más grande) y RTMW-x estima la 2D en la imagen nativa y en la reducida a
     80 px de jugador con JPEG 70, como en la validación con MoVi. Caché en datos/campo/ (vídeo personal).
  2. MotionAGFormer-B (pesos oficiales) eleva a 3D. La cámara del móvil está nivelada: el eje vertical de la
     imagen se toma como la vertical del mundo. Escala: longitud del muslo = 0,245 × estatura (Winter 2009).
  3. Se corrigen los cruces de etiqueta izquierda/derecha de las piernas (Viterbi, fix_swaps). La pierna de
     golpeo es la derecha (dato del autor): así el contacto no cae en una zancada de la carrera previa.
  4. Contacto automático (pico de velocidad del tobillo), rasgos de postura, momentos de la pierna de golpeo
     (masa del autor) e índice de carga KLI en puntuaciones z respecto a la referencia de laboratorio (MoVi).
Salidas: resultados/campo/campo_rasgos.csv y datos/campo/<vídeo>.npz (series para las figuras).

Uso:  python campo_videos.py
"""
import json
import re
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from golpeo.camara import CONF
from golpeo.carga import LOAD_NAMES, kick_loads, swing_leg_moments
from golpeo.cinematica import FEATURE_NAMES, contact_frame, kick_features, kicking_side
from golpeo.h36m import coco_to_h36m, to_canonical
from validar_video_movi import JPEG, player_height_px

ROOT = Path(__file__).parent
VIDEOS = ROOT / "videos"
CACHE = ROOT / "datos" / "campo"
OUT = ROOT / "resultados" / "campo"
STATURE_M, MASS_KG, SEX = 1.77, 78.0, "male"
KICKING_SIDE = "r"                        # el autor golpea siempre con la derecha
THIGH_RATIO = 0.245                       # longitud del muslo / estatura (Winter 2009)
CUTOFF_HZ = 12.0
H_BROADCAST = 80
VIEWS = {"lateral": ("lateral", 90), "diagonalatras": ("diagonal behind", 135),
         "diagonaldelante": ("diagonal front", 45), "frente": ("front", 0), "delante": ("front", 0)}
NAME = re.compile(r"(\d+)_([a-z]+)_(fuerte|suave)", re.I)


def parse(path: Path) -> dict:
    m = NAME.match(path.stem)
    view, az = VIEWS[m.group(2).lower()]
    return dict(video=path.stem, order=int(m.group(1)), view=view, azimuth=az,
                intensity="strong" if m.group(3).lower() == "fuerte" else "soft")


def detect(path: Path, det, pose) -> dict:
    """2D nativa y a 80 px de jugador (con JPEG), en caché."""
    cache = CACHE / f"{path.stem}_2d.npz"
    if cache.exists():
        z = np.load(cache)
        return {k: z[k] for k in z.files}
    cap = cv2.VideoCapture(str(path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frames = []
    while True:
        ok, img = cap.read()
        if not ok:
            break
        frames.append(img)
    cap.release()
    n = len(frames)
    k_nat, s_nat = np.full((n, 133, 2), np.nan), np.zeros((n, 133))
    boxes = np.full((n, 4), np.nan)
    for i, img in enumerate(frames):
        b = det(img)
        if len(b) == 0:
            continue
        box = b[int(np.argmax([(x[2] - x[0]) * (x[3] - x[1]) for x in b]))]
        boxes[i] = box
        k, s = pose(img, bboxes=[box])
        k_nat[i], s_nat[i] = k[0], s[0]
    uv_nat, _ = coco_to_h36m(k_nat[:, :17], s_nat[:, :17])
    h_native = float(player_height_px(uv_nat))
    scale = H_BROADCAST / h_native
    k_low, s_low = np.full((n, 133, 2), np.nan), np.zeros((n, 133))
    for i, img in enumerate(frames):
        if not np.isfinite(boxes[i]).all():
            continue
        im = cv2.resize(img, None, fx=scale, fy=scale, interpolation=cv2.INTER_AREA)
        im = cv2.imdecode(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, JPEG])[1], cv2.IMREAD_COLOR)
        k, s = pose(im, bboxes=[boxes[i] * scale])
        k_low[i], s_low[i] = k[0] / scale, s[0]
    out = dict(fps=np.array(fps), h_native=np.array(h_native), boxes=boxes,
               k_native=k_nat[:, :17], s_native=s_nat[:, :17], k_low=k_low[:, :17], s_low=s_low[:, :17],
               frame_size=np.array(frames[0].shape[:2]))
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **out)
    return out


MIRROR = [0, 4, 5, 6, 1, 2, 3, 7, 8, 9, 10, 14, 15, 16, 11, 12, 13]     # intercambio izquierda/derecha (H36M)


def fix_swaps(uv: np.ndarray, prior: float = 0.03) -> tuple[np.ndarray, int]:
    """Corrige los cruces de etiqueta izquierda/derecha de rodillas y tobillos (típicos cuando las piernas se
    cruzan en vista lateral) eligiendo, para todo el vídeo a la vez, la secuencia de etiquetas más continua
    (Viterbi con dos estados: normal o cruzado). Cada fotograma cruzado cuesta `prior` alturas de jugador, para
    no cruzar sin pruebas; una inversión de todo el cuerpo se trata aparte (ver `analyse`)."""
    legs = [2, 3, 5, 6]
    alt = [5, 6, 2, 3]
    valid = np.flatnonzero(np.isfinite(uv[:, legs]).all(axis=(1, 2)))
    if len(valid) < 2:
        return uv.copy(), 0
    h = np.nanmedian(np.nanmax(uv[..., 1], axis=1) - np.nanmin(uv[..., 1], axis=1))
    cand = np.stack([uv[valid][:, legs], uv[valid][:, alt]], axis=1)          # (n, 2 estados, 4, 2)
    n = len(valid)
    cost = np.zeros((n, 2))
    back = np.zeros((n, 2), int)
    cost[0] = [0.0, prior]
    for t in range(1, n):
        step = np.linalg.norm(cand[t][None, :] - cand[t - 1][:, None], axis=-1).sum(-1) / h   # (previo, actual)
        tot = cost[t - 1][:, None] + step
        back[t] = np.argmin(tot, axis=0)
        cost[t] = tot.min(axis=0) + [0.0, prior]
    state = np.zeros(n, int)
    state[-1] = int(np.argmin(cost[-1]))
    for t in range(n - 1, 0, -1):
        state[t - 1] = back[t, state[t]]
    out = uv.copy()
    sw = valid[state == 1]
    out[np.ix_(sw, legs)] = uv[np.ix_(sw, alt)]
    return out, int(len(sw))


def fill(uv: np.ndarray) -> np.ndarray:
    ok = np.isfinite(uv).all(axis=(1, 2))
    t = np.arange(len(uv))
    out = uv.copy()
    for j in range(17):
        for d in range(2):
            out[~ok, j, d] = np.interp(t[~ok], t[ok], uv[ok, j, d])
    return out


def to_world(x17_cam: np.ndarray) -> np.ndarray:
    """Coordenadas del elevador (x derecha, y abajo, z profundidad) → mundo con z hacia arriba, en metros."""
    w = np.stack([x17_cam[..., 0], x17_cam[..., 2], -x17_cam[..., 1]], axis=-1)
    seq = to_canonical(w)
    thigh = np.nanmedian(np.linalg.norm(seq[:, 4:6] - seq[:, 2:4], axis=-1))
    return w * (THIGH_RATIO * STATURE_M / thigh)


def analyse(uv: np.ndarray, fps: float, lifter, side=None) -> dict:
    uv, n_swaps = fix_swaps(uv)
    x17 = to_world(lifter.lift_person(fill(uv), np.full(uv.shape[:2], CONF)))
    seq = to_canonical(x17)
    side = KICKING_SIDE
    c = contact_frame(seq, fps, side)
    f = kick_features(seq, fps, contact=c, side=side)
    f.update(kick_loads(seq, fps, MASS_KG, SEX, contact=c, cutoff_hz=CUTOFF_HZ, side=side))
    ank = x17[:, 3 if side == "r" else 6]
    f["peak_ankle_speed"] = float(np.nanmax(np.linalg.norm(np.gradient(ank, axis=0), axis=1) * fps))
    m = swing_leg_moments(seq, fps, side, MASS_KG, SEX, cutoff_hz=CUTOFF_HZ)
    return dict(features=f, x17=x17, side=side, contact=c, swaps=n_swaps, uv=uv,
                hip_moment=m["cadera_momento"] / MASS_KG, knee_moment=m["rodilla_momento"] / MASS_KG)


def kli_z(f: dict, ref: dict) -> float:
    return float(np.mean([(f[k] - ref[k][0]) / ref[k][1] for k in LOAD_NAMES]))          # ref: [media, DE]


def main():
    from golpeo.detector import rtmw, yolox
    from golpeo.elevador import Lifter
    det, pose, lifter = yolox(), rtmw(), Lifter()
    ref = json.loads((ROOT / "resultados" / "resumen_carga.json").read_text(encoding="utf-8"))["ref_mean_sd"]
    rows, t0 = [], time.time()
    for path in sorted(VIDEOS.glob("*.MOV"), key=lambda p: parse(p)["order"]):
        meta = parse(path)
        d = detect(path, det, pose)
        fps = float(d["fps"])
        nat = analyse(coco_to_h36m(d["k_native"], d["s_native"])[0], fps, lifter)
        low = analyse(coco_to_h36m(d["k_low"], d["s_low"])[0], fps, lifter, side=nat["side"])
        np.savez_compressed(CACHE / f"{path.stem}_3d.npz", fps=fps, side=nat["side"], contact=nat["contact"],
                            uv=nat["uv"], uv_low=low["uv"],
                            contact_low=low["contact"], x17=nat["x17"], x17_low=low["x17"],
                            hip_moment=nat["hip_moment"], knee_moment=nat["knee_moment"],
                            hip_moment_low=low["hip_moment"], knee_moment_low=low["knee_moment"])
        for res, a in (("native", nat), ("80 px", low)):
            rows.append(dict(**meta, resolution=res, h_native_px=float(d["h_native"]), fps=fps, side=a["side"],
                             swapped_frames=a["swaps"],
                             contact_frame=a["contact"], kli_z=kli_z(a["features"], ref), **a["features"]))
        print(f"{meta['video']}: jugador {float(d['h_native']):.0f} px, pierna {nat['side']}, "
              f"tobillo {nat['features']['peak_ankle_speed']:.1f} m/s ({time.time() - t0:.0f} s)", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(OUT / "campo_rasgos.csv", index=False)


if __name__ == "__main__":
    main()
