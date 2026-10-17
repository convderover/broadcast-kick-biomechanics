"""Validación con imagen real: RTMW → MotionAGFormer sobre el vídeo de MoVi, frente a la 3D de Visual3D.

Para cada sujeto y cada cámara fija (PG1, PG2; 800×600 a 30 fps, sincronizadas con la captura a 120 fps):
  1. YOLOX detecta al sujeto en la imagen original (se elige la caja que contiene la pelvis proyectada).
  2. La imagen se reduce para que el jugador mida lo que mediría en una retransmisión (nativa ≈ 300 px,
     120, 80 y 50 px) y se comprime en JPEG (calidad 70). RTMW estima la pose 2D dentro de la caja escalada.
     La 2D detectada se guarda en datos/movi/pose2d (caché) para poder evaluar otros elevadores sin repetirla.
  3. Se mide el error 2D frente a la 3D proyectada con la calibración de MoVi.
  4. MotionAGFormer-B (oficial o ajustado) eleva a 3D; escala por el muslo y alineamiento rígido.
  5. Rasgos de postura y cargas articulares (contacto y pierna conocidos, y automáticos).

El golpeo de MoVi es al aire y lo hacen no futbolistas: valida la medida (la cadena de visión), no el gesto.
Uso:  python validar_video_movi.py [sujeto ...] [--elevador ckpt --salida prefijo] [--solo-deteccion]
      → resultados/video_movi.csv y video_movi_2d.csv
"""
import argparse
import re
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd

from experimento_sensibilidad import CUTOFF_GT, thigh
from golpeo.carga import LOAD_NAMES, kick_loads
from golpeo.cinematica import FEATURE_NAMES, _body_frame, contact_frame, kick_features, kicking_side, rigid_align
from golpeo.datos_movi import MoviCamera, load_movi
from golpeo.ensayos import fill_gaps
from golpeo.camara import CONF
from golpeo.h36m import coco_to_h36m, to_canonical

ROOT = Path(__file__).parent
MOVI = ROOT / "datos" / "movi"
POSE2D = MOVI / "pose2d"                 # caché de la 2D detectada (derivado de MoVi: no se publica)
OUT = ROOT / "resultados"
CAMS = ("PG1", "PG2")
ALTURAS = (None, 120, 80, 50)            # None = resolución nativa
JPEG = 70
FPS_VIDEO = 30.0
LIMBS = [1, 2, 3, 4, 5, 6, 11, 12, 13, 14, 15, 16]


def player_height_px(uv17):
    """Altura aparente en píxeles: de la coronilla (H36M 10) al tobillo más bajo."""
    return np.nanmedian(np.maximum(uv17[:, 3, 1], uv17[:, 6, 1]) - uv17[:, 10, 1])


def pick_box(boxes, pelvis_uv):
    inside = [(b[2] - b[0]) * (b[3] - b[1]) if b[0] <= pelvis_uv[0] <= b[2] and b[1] <= pelvis_uv[1] <= b[3] else -1
              for b in boxes]
    return boxes[int(np.argmax(inside))] if len(boxes) and max(inside) > 0 else None


def camera_azimuth(cam: MoviCamera, seq8, c):
    """Ángulo de la cámara respecto al frente del jugador en el contacto (0 = de frente, 90 = lateral)."""
    centre = -cam.t @ cam.R.T / 1000.0
    up, lat, fwd = (v[c] for v in _body_frame(seq8))
    to_cam = centre - 0.5 * (seq8[c, 2] + seq8[c, 3])
    to_cam[2] = 0
    fwd_h = fwd - fwd @ np.array([0, 0, 1.0]) * np.array([0, 0, 1.0])
    ang = np.degrees(np.arctan2(np.cross(fwd_h, to_cam)[2], fwd_h @ to_cam))     # + = cámara a la izquierda
    return abs(ang), -ang                         # (0–180, y con el convenio de golpeo/camara.film: + = derecha)


def camera_elevation_distance(cam: MoviCamera, seq8):
    """Elevación (grados) y distancia (m) de la cámara respecto a la pelvis media del sujeto."""
    centre = -cam.t @ cam.R.T / 1000.0
    v = centre - np.nanmean(0.5 * (seq8[:, 2] + seq8[:, 3]), axis=0)
    return float(np.degrees(np.arcsin(v[2] / np.linalg.norm(v)))), float(np.linalg.norm(v))


def label(h):
    return "native" if h is None else str(h)


def subject_window(path):
    """Ventana del golpeo: referencia, fotogramas de vídeo y su correspondencia con la captura."""
    tr = load_movi(path)
    x17, ok = fill_gaps(tr.x17, tr.fps)                  # mismo criterio que la sensibilidad
    if not ok:
        raise ValueError("hueco de captura de más de 0,25 s")
    tr.x17 = x17
    gt8 = to_canonical(tr.x17)
    side = kicking_side(gt8, tr.fps)
    c120 = contact_frame(gt8, tr.fps, side)
    ref = kick_features(gt8, tr.fps, contact=c120, side=side)
    ref.update(kick_loads(gt8, tr.fps, tr.mass_kg, tr.sex, contact=c120, cutoff_hz=CUTOFF_GT, side=side))
    f0 = int(np.ceil(tr.frame0 / 4))
    f1 = int(np.floor((tr.frame0 + len(tr.x17) - 1) / 4))
    frames = np.arange(f0, f1 + 1)
    idx120 = 4 * frames - tr.frame0                       # fotograma de captura de cada fotograma de vídeo
    return dict(tr=tr, gt8=gt8, side=side, c120=c120, ref=ref, frames=frames, gt17v=tr.x17[idx120],
                gt8v=gt8[idx120], c_video=int(np.argmin(np.abs(idx120 - c120))))


def detect(w, cam_name, det, pose):
    """YOLOX + RTMW en la imagen nativa y reducida; se guarda en caché para no repetirlo."""
    cache = POSE2D / f"S{w['tr'].subject:02d}_{cam_name}.npz"
    if cache.exists():
        z = np.load(cache, allow_pickle=False)
        return {k: z[k] for k in z.files}
    cam = MoviCamera.load(MOVI / "3d" / "Calib", cam_name)
    gt_uv = cam.project(w["gt17v"])
    h_native = player_height_px(gt_uv)
    frames = w["frames"]
    cap = cv2.VideoCapture(str(MOVI / "video" / f"F_{cam_name}_Subject_{w['tr'].subject}_L.avi"))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frames[0]))
    out = {"h_native": np.array(h_native), "gt_uv": gt_uv}
    for h in ALTURAS:
        out[f"k_{label(h)}"] = np.full((len(frames), 17, 2), np.nan)
        out[f"s_{label(h)}"] = np.zeros((len(frames), 17))
    for i in range(len(frames)):
        ok, img = cap.read()
        if not ok:
            break
        box = pick_box(det(img), gt_uv[i, 0])
        if box is None:
            continue
        for h in ALTURAS:
            s = 1.0 if h is None else h / h_native
            im = img if h is None else cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
            if h is not None:
                im = cv2.imdecode(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, JPEG])[1], cv2.IMREAD_COLOR)
            k, sc = pose(im, bboxes=[np.asarray(box) * s])
            out[f"k_{label(h)}"][i], out[f"s_{label(h)}"][i] = k[0][:17] / s, sc[0][:17]
    cap.release()
    POSE2D.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(cache, **out)
    return out


def evaluate(w, cam_name, d, lifter, rows, rows2d):
    tr, gt8, side = w["tr"], w["gt8"], w["side"]
    cam = MoviCamera.load(MOVI / "3d" / "Calib", cam_name)
    gt_uv, h_native = d["gt_uv"], float(d["h_native"])
    az, az_film = camera_azimuth(cam, gt8, w["c120"])
    el, dist = camera_elevation_distance(cam, gt8)
    for h in ALTURAS:
        uv, _ = coco_to_h36m(d[f"k_{label(h)}"], d[f"s_{label(h)}"])
        # Las "confianzas" de RTMW son máximos SimCC sin normalizar (3–7) y el elevador se entrenó con
        # confianzas en [0, 1]: pasarlas tal cual deforma la 3D (rodilla de golpeo −41°). Se usa la misma
        # confianza constante que en la cámara virtual.
        conf = np.full(uv.shape[:2], CONF)
        okf = np.isfinite(uv).all(axis=(1, 2))
        if okf.mean() < 0.8:
            continue
        target = h_native if h is None else h
        err = np.linalg.norm(uv - gt_uv, axis=-1) * (target / h_native)       # en píxeles a esa escala
        if rows2d is not None:
            for i in np.flatnonzero(okf):
                dd = (uv[i] - gt_uv[i]) * (target / h_native)
                rows2d.append(dict(sujeto=tr.subject, camara=cam_name, disparo=f"{tr.subject:02d}_{cam_name}_{round(target)}",
                                   escala=1.0, altura_px=round(target), nativa=h is None, fotograma=int(w["frames"][i]),
                                   sigma_eje_px=float(np.sqrt((err[i, LIMBS] ** 2).mean() / 2)),
                                   **{f"err_j{j}": float(err[i, j]) for j in range(17)},
                                   **{f"{ax}_j{j}": float(dd[j, k]) for j in range(17) for k, ax in enumerate("xy")}))
        # fotogramas perdidos: interpolación lineal (como haría un sistema real antes de elevar)
        t = np.arange(len(uv))
        for j in range(17):
            for k in range(2):
                uv[~okf, j, k] = np.interp(t[~okf], t[okf], uv[okf, j, k])
        est = to_canonical(lifter.lift_person(uv, conf))
        est = rigid_align(est * thigh(w["gt8v"]) / thigh(est), w["gt8v"])
        for modo, kw in (("conocido", dict(contact=w["c_video"], side=side)), ("auto", {})):
            f = kick_features(est, FPS_VIDEO, **kw)
            f.update(kick_loads(est, FPS_VIDEO, tr.mass_kg, tr.sex, cutoff_hz=min(CUTOFF_GT, 0.35 * FPS_VIDEO), **kw))
            for k in FEATURE_NAMES + LOAD_NAMES:
                rows.append(dict(ensayo=f"movi_{tr.subject:02d}", sujeto=tr.subject, camara=cam_name,
                                 vista_real=az, azimut_film=az_film, elevacion=el, distancia_m=dist,
                                 altura_px=round(target), nativa=h is None, altura_nativa_px=h_native,
                                 fps=FPS_VIDEO, contacto=modo, rasgo=k,
                                 tipo="carga" if k in LOAD_NAMES else "postura",
                                 referencia=w["ref"][k], estimado=f[k], error=f[k] - w["ref"][k]))


def subject_number(path):
    return int(re.findall(r"(\d+)\.mat", path.name)[0])


def main():
    from golpeo.elevador import CKPT, Lifter
    ap = argparse.ArgumentParser()
    ap.add_argument("sujetos", nargs="*", type=int)
    ap.add_argument("--elevador", default=None, help="checkpoint alternativo del elevador (p. ej. ajustado)")
    ap.add_argument("--salida", default="video_movi", help="prefijo de los CSV en resultados/")
    ap.add_argument("--solo-deteccion", action="store_true")
    args = ap.parse_args()
    paths = sorted((MOVI / "3d").glob("F_Subjects_*/F_v3d_Subject_*.mat"), key=subject_number)
    det = pose = None
    lifter = None if args.solo_deteccion else Lifter(ckpt=Path(args.elevador) if args.elevador else CKPT)
    rows, rows2d, t0 = [], [], time.time()
    for path in paths:
        n = subject_number(path)
        if args.sujetos and n not in args.sujetos:
            continue
        cams = [c for c in CAMS if (MOVI / "video" / f"F_{c}_Subject_{n}_L.avi").exists()]
        if not cams:
            continue
        try:
            w = subject_window(path)
            for cam_name in cams:
                if det is None and not (POSE2D / f"S{n:02d}_{cam_name}.npz").exists():
                    from golpeo.detector import rtmw, yolox
                    det, pose = yolox(), rtmw()
                d = detect(w, cam_name, det, pose)
                if lifter is not None:
                    evaluate(w, cam_name, d, lifter, rows, rows2d if args.elevador is None else None)
        except (ValueError, KeyError, IndexError) as exc:
            print(f"sujeto {n}: omitido ({exc})", flush=True)
            continue
        print(f"sujeto {n} listo ({time.time() - t0:.0f} s)", flush=True)
        if lifter is not None:
            pd.DataFrame(rows).to_csv(OUT / f"{args.salida}.csv", index=False)
            if args.elevador is None:
                pd.DataFrame(rows2d).to_csv(OUT / f"{args.salida}_2d.csv", index=False)
    print(f"{len(rows)} filas, {len(rows2d)} fotogramas 2D en {time.time() - t0:.0f} s")


if __name__ == "__main__":
    main()
