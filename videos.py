"""Vídeos de cada análisis (H.264, en español, para presentación y CV). Salida en resultados/videos/.

  01_contacto_balon.mp4          pico de velocidad del tobillo frente al contacto real con el balón (CMU)
  02_camara_tv_virtual.mp4       lo que "ve" el sistema: 5 ángulos × 3 tamaños, con ruido real de RTMW
  03_error_2d_emision_USO_INTERNO.mp4   RTMW frente a anotación manual en disparos de la Premier (3DSP). Con derechos
  04_reconstruccion_3d.mp4       entrada de TV (80 px, 25 fps) → 3D reconstruido frente a la captura óptica
  05_video_real_movi.mp4         validación con imagen real (MoVi): imagen nativa y reducida a 50 px. Solo uso académico
  06_carga_articular.mp4         momentos de cadera y rodilla de la pierna de golpeo: laboratorio frente a TV
  00_resumen.mp4                 montaje de todo con cartelas, para CV y redes (sin material con derechos)

Uso:  python videos.py [01 02 ...]   (sin argumentos: todos)
"""
import json
import sys
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from experimento_sensibilidad import ELEVACION, noise_models, resample, thigh
from figuras_visuales import BG, FG, KICK, SUPPORT, TRUNK, draw_body, interp_nan, sagittal
from golpeo.camara import film
from golpeo.carga import kick_loads, swing_leg_moments
from golpeo.cinematica import contact_frame, hip_flexion, kicking_side, knee_flexion, rigid_align
from golpeo.contacto import ball_contact
from golpeo.datos_cmu import load_cmu, load_cmu_h36m
from golpeo.h36m import to_canonical
from golpeo.ruido import ResidualBank
from golpeo.video import Mp4, figure_to_rgb, put_text, title_card

ROOT = Path(__file__).parent
OUT = ROOT / "resultados" / "videos"
BONES = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (0, 7), (7, 8), (8, 9), (9, 10),
         (8, 11), (11, 12), (12, 13), (8, 14), (14, 15), (15, 16)]
RIGHT = {(0, 1), (1, 2), (2, 3), (8, 14), (14, 15), (15, 16)}
GRID = "#3b4a5e"
BALL = "#ffd166"
EST = "#4cc9f0"
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.facecolor": BG, "figure.facecolor": BG,
                     "axes.edgecolor": GRID, "axes.labelcolor": FG, "xtick.color": FG, "ytick.color": FG,
                     "text.color": FG, "axes.titlecolor": FG})


def cmu_scene(name="10_01"):
    path = ROOT / "datos" / "cmu" / f"{name}.c3d"
    x17, fps = load_cmu_h36m(path)
    tr = load_cmu(path)
    c_float, v_ball = ball_contact(tr.ball, fps)
    c = int(round(c_float))
    ball = interp_nan(tr.ball)
    launch = ball[min(c + 6, len(ball) - 1)] - ball[c]
    e1 = launch.copy()
    e1[2] = 0
    e1 /= np.linalg.norm(e1)
    origin = ball[c - 30].copy()
    origin[2] = 0
    return dict(x17=x17, fps=fps, c=c, c_float=c_float, ball=ball, raw_ball=tr.ball, e1=e1, origin=origin,
                v_ball=v_ball, seq=tr.seq)


def body_axes(ax, s, t, px, trail=True, alpha=1.0, color_override=None, x17=None):
    x17 = s["x17"] if x17 is None else x17
    ax.set_facecolor(BG)
    ax.axhline(0, color=GRID, lw=2, zorder=1)
    ax.fill_between([-3, 6], -0.3, 0, color="#163020", zorder=0)
    if trail:
        for k, tt in enumerate(range(max(t - 36, 0), t, 6)):
            draw_body(ax, sagittal(x17[tt], s["origin"], s["e1"]), alpha=0.08 + 0.04 * k, skeleton=False, scale_px=px)
    p2 = sagittal(x17[t], s["origin"], s["e1"])
    draw_body(ax, p2, scale_px=px, alpha=alpha)
    b2 = sagittal(s["ball"], s["origin"], s["e1"])
    ax.add_patch(plt.Circle(b2[t], 0.11, fc=BALL, ec="white", lw=1.5, zorder=6))
    ax.set_xlim(-1.6, 3.0)
    ax.set_ylim(-0.3, 2.2)
    ax.set_aspect("equal")
    ax.axis("off")
    return p2, b2


# ---------------------------------------------------------------------------------------------- 01
def video_contacto():
    s = cmu_scene()
    x17, fps, c, cf = s["x17"], s["fps"], s["c"], s["c_float"]
    side = kicking_side(s["seq"], fps)
    v_ank = np.linalg.norm(np.gradient(s["seq"][:, 7], axis=0), axis=1) * fps
    c_ank = contact_frame(s["seq"], fps, side)
    rest = np.nanmedian(s["raw_ball"][:10], axis=0)
    disp = np.linalg.norm(s["raw_ball"] - rest, axis=1) * 100
    lo, hi = c - 60, min(c + 30, len(x17) - 1)
    tt = (np.arange(lo, hi) - cf) / fps * 1000
    with Mp4(OUT / "01_contacto_balon.mp4", 30) as vid:
        for f in title_card("¿Cuándo toca el balón?", "Pico de velocidad del tobillo frente al contacto real\n"
                            "Captura óptica CMU, 120 fps  ·  cámara lenta ×4"):
            vid.write(f)
        for t in range(lo, hi):
            fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
            ax = fig.add_axes([0.0, 0.05, 0.55, 0.85])
            body_axes(ax, s, t, px=fig.dpi * 12.8 * 0.55 / 4.6 * 0.72)
            a1 = fig.add_axes([0.62, 0.55, 0.35, 0.33])
            a2 = fig.add_axes([0.62, 0.12, 0.35, 0.33], sharex=a1)
            a1.plot(tt, v_ank[lo:hi], color=KICK, lw=2.5)
            a2.plot(tt, disp[lo:hi], color=BALL, lw=2.5)
            for a in (a1, a2):
                a.axvline((c_ank - cf) / fps * 1000, color=KICK, ls="--", lw=1.5)
                a.axvline(0, color=BALL, ls="--", lw=1.5)
                a.axvline((t - cf) / fps * 1000, color="white", lw=1)
                a.grid(color=GRID, alpha=0.5)
            a1.set_ylabel("Velocidad tobillo (m/s)")
            a2.set_ylabel("Desplazamiento balón (cm)")
            a2.set_xlabel("ms respecto al contacto real")
            a2.set_ylim(-5, 60)
            a1.text((c_ank - cf) / fps * 1000 - 3, a1.get_ylim()[1] * 0.92, "pico tobillo", color=KICK, ha="right")
            a2.text(3, 50, "contacto real", color=BALL)
            fig.text(0.02, 0.95, f"t = {(t - cf) / fps * 1000:+.0f} ms", fontsize=18, weight="bold")
            fig.text(0.02, 0.91, f"El pico del tobillo llega {(cf - c_ank) / fps * 1000:.0f} ms antes del contacto "
                     f"(media en 5 golpeos: 20 ms; < 1 fotograma a 25 fps)", fontsize=12, color="#c7d0db")
            vid.write(figure_to_rgb(fig))
            plt.close(fig)


# ---------------------------------------------------------------------------------------------- 02
def video_camara_tv():
    s = cmu_scene()
    x17r = resample(s["x17"], s["fps"], 25)
    gt8 = to_canonical(x17r)
    c = contact_frame(gt8, 25, kicking_side(gt8, 25))
    bank = ResidualBank.from_frame(pd.read_csv(ROOT / "resultados" / "error2d_3dsp.csv"))
    views = [(0, "frontal"), (45, "45°"), (90, "lateral"), (135, "135°"), (180, "espalda")]
    sizes = (200, 80, 50)
    cell = 196
    seqs = {}
    for az, _ in views:
        for h in sizes:
            rng = np.random.default_rng(az * 1000 + h)
            uv, _ = film(x17r, az, ELEVACION, h, 0, 0, rng)
            seqs[az, h] = uv + bank.sample(len(uv), 25, h, rng)
    lo, hi = max(c - 20, 0), min(c + 10, len(x17r))
    W, H = 1280, 720
    x_left, y_top = 90, 110
    with Mp4(OUT / "02_camara_tv_virtual.mp4", 8) as vid:
        for f in title_card("Lo que ve una cámara de TV", "El mismo golpeo desde 5 ángulos y 3 tamaños de jugador\n"
                            "25 fps, con el error real del detector en retransmisiones", fps=8, seconds=2.5):
            vid.write(f)
        for t in range(lo, hi):
            frame = np.full((H, W, 3), BG_RGB, np.uint8)
            for j, (az, name) in enumerate(views):
                x0 = x_left + j * (cell + 40)
                put_text(frame, name, (x0 + cell / 2, y_top - 32), 22, FG_RGB, bold=True, anchor="ma")
                for i, h in enumerate(sizes):
                    uv = seqs[az, h]
                    win = uv[lo:hi].reshape(-1, 2)
                    lo_xy, hi_xy = np.percentile(win, 1, axis=0), np.percentile(win, 99, axis=0)
                    n = int(np.ceil(max(hi_xy - lo_xy) * 1.1)) + 2
                    small = np.full((n, n, 3), (34, 48, 66), np.uint8)
                    q = uv[t] - (lo_xy + hi_xy) / 2 + n / 2
                    for a, b in BONES:
                        col = KICK_RGB if (a, b) in RIGHT else (230, 230, 230)
                        cv2.line(small, tuple(np.round(q[a]).astype(int)), tuple(np.round(q[b]).astype(int)), col, 1,
                                 cv2.LINE_AA)
                    big = cv2.resize(small, (cell, cell), interpolation=cv2.INTER_NEAREST)
                    y0 = y_top + i * (cell + 10)
                    frame[y0:y0 + cell, x0:x0 + cell] = big
            for i, h in enumerate(sizes):
                put_text(frame, f"{h} px", (x_left - 12, y_top + i * (cell + 10) + cell / 2), 20, FG_RGB, anchor="rm")
            put_text(frame, f"t = {(t - c) * 40:+d} ms respecto al contacto  ·  pierna de golpeo en naranja  ·  "
                     "cada cuadro, a su resolución real", (x_left, 28), 22, FG_RGB)
            vid.write(frame)


BG_RGB, FG_RGB, KICK_RGB = (15, 23, 36), (232, 237, 243), (255, 138, 61)


# ---------------------------------------------------------------------------------------------- 03
def video_3dsp():
    from golpeo.detector import rtmw
    from golpeo.error2d import coco_to_3dsp
    from medir_error_2d import box, load_gt
    pose = rtmw()
    shots = ["00003", "00021", "00057", "00104"]
    up = 3
    seqs = []
    for shot in shots:
        d = ROOT / "datos" / "3dsp" / "3dsp" / "train" / shot
        frames = []
        for jf in sorted((d / "posture").glob("*.json")):
            img = cv2.imread(str(d / "img" / f"{jf.stem}.jpg"))
            gt = load_gt(jf)
            k, _ = pose(img, bboxes=[box(gt, img.shape)])
            est = coco_to_3dsp(k[0])
            scale = np.array([100 * up / img.shape[1], 100 * up / img.shape[0]])
            big = cv2.resize(img, (100 * up, 100 * up), interpolation=cv2.INTER_CUBIC)
            for P, col in ((gt, (182, 196, 46)), (est, (61, 138, 255))):
                for a, b in BONES:
                    cv2.line(big, tuple(np.round(P[a] * scale).astype(int)), tuple(np.round(P[b] * scale).astype(int)),
                             col, 2, cv2.LINE_AA)
            frames.append(big)
        seqs.append(frames)
    with Mp4(OUT / "03_error_2d_emision_USO_INTERNO.mp4", 5) as vid:
        for t in range(min(len(s) for s in seqs)):
            row = np.concatenate([s[t] for s in seqs], axis=1)
            head = np.full((60, row.shape[1], 3), BG_RGB, np.uint8)
            put_text(head, "3DSP (Premier League vía SoccerNet) · verde: anotación manual · naranja: RTMW · "
                     "USO INTERNO (imágenes con derechos)", (10, 18), 20, FG_RGB)
            vid.write(np.concatenate([head, row[..., ::-1]]))


# ---------------------------------------------------------------------------------------------- 04 y 06
def tv_reconstruction(s, h=80, fps_v=25, az=90, seed=0):
    from golpeo.elevador import Lifter
    xr = resample(s["x17"], s["fps"], fps_v)
    bank = ResidualBank.from_frame(pd.read_csv(ROOT / "resultados" / "error2d_3dsp.csv"))
    rng = np.random.default_rng(seed)
    uv, conf = film(xr, az, ELEVACION, h, 0, 0, rng)
    uv = uv + bank.sample(len(uv), fps_v, h, rng)
    est17 = Lifter().lift_person(uv, conf)
    gt8 = to_canonical(xr)
    est17 = est17 * thigh(gt8) / thigh(to_canonical(est17))
    al = rigid_align(np.concatenate([to_canonical(est17), est17], 1), np.concatenate([gt8, xr], 1))
    return xr, uv, al[:, 8:]


def video_reconstruccion():
    s = cmu_scene()
    h, fps_v = 80, 25
    xr, uv, est17 = tv_reconstruction(s, h, fps_v)
    gt8, est8 = to_canonical(xr), to_canonical(est17)
    side = kicking_side(gt8, fps_v)
    c = int(round(s["c_float"] / s["fps"] * fps_v))
    curves = {"Flexión rodilla de golpeo": (knee_flexion(gt8, side), knee_flexion(est8, side)),
              "Flexión cadera de golpeo": (hip_flexion(gt8, side), hip_flexion(est8, side))}
    lo, hi = max(c - 25, 0), min(c + 12, len(xr))
    vis = est17 - est17[:, :1] + xr[:, :1]
    with Mp4(OUT / "04_reconstruccion_3d.mp4", 6) as vid:
        for f in title_card("De la tele al esqueleto 3D", f"Jugador de {h} px a {fps_v} fps  ->  RTMW + MotionAGFormer\n"
                            "comparado con la captura óptica de laboratorio", fps=6, seconds=2.5):
            vid.write(f)
        for t in range(lo, hi):
            fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
            a1 = fig.add_axes([0.02, 0.12, 0.25, 0.7])
            n = int(h * 1.4)
            canvas = np.full((n, n), 40, np.uint8)
            q = uv[t] - (uv[lo:hi].reshape(-1, 2).mean(0) - n / 2)
            for a, b in BONES:
                cv2.line(canvas, tuple(np.round(q[a]).astype(int)), tuple(np.round(q[b]).astype(int)), 255, 1)
            a1.imshow(canvas, cmap="gray", interpolation="nearest")
            a1.set_title(f"Entrada: {h} px, {fps_v} fps\ncon el error real del detector", fontsize=11)
            a1.axis("off")
            a2 = fig.add_axes([0.28, 0.08, 0.36, 0.8], projection="3d")
            a2.set_facecolor(BG)
            for X, col, lab in ((xr[t], "white", "captura óptica (verdad)"), (vis[t], EST, "reconstruido desde TV")):
                for i, (a, b) in enumerate(BONES):
                    a2.plot(*X[[a, b]].T, color=col, lw=2.5, label=lab if i == 0 else None)
            ctr = xr[t, 0]
            a2.set_xlim(ctr[0] - 0.9, ctr[0] + 0.9)
            a2.set_ylim(ctr[1] - 0.9, ctr[1] + 0.9)
            a2.set_zlim(0, 1.9)
            a2.view_init(elev=8, azim=-60 + 1.5 * (t - lo))
            a2.set_xticks([]), a2.set_yticks([]), a2.set_zticks([])
            a2.xaxis.pane.fill = a2.yaxis.pane.fill = a2.zaxis.pane.fill = False
            a2.legend(loc="upper left", fontsize=10, facecolor=BG, edgecolor=GRID, labelcolor=FG)
            tt = (np.arange(lo, hi) - c) / fps_v * 1000
            for k, (name, (g, e)) in enumerate(curves.items()):
                a = fig.add_axes([0.70, 0.56 - 0.44 * k, 0.28, 0.33])
                a.plot(tt, g[lo:hi], color="white", lw=2.5, label="laboratorio")
                a.plot(tt, e[lo:hi], color=EST, lw=2.5, label="desde TV")
                a.axvline((t - c) / fps_v * 1000, color=KICK, lw=1.5)
                a.set_title(f"{name} (°)", fontsize=11)
                a.grid(color=GRID, alpha=0.5)
                if k == 1:
                    a.set_xlabel("ms respecto al contacto")
                else:
                    a.legend(fontsize=9, facecolor=BG, edgecolor=GRID, labelcolor=FG)
            fig.text(0.02, 0.93, f"t = {(t - c) * 1000 / fps_v:+.0f} ms", fontsize=16, weight="bold")
            vid.write(figure_to_rgb(fig))
            plt.close(fig)


def moment_arc(ax, centre, value, color, scale=0.17, max_value=1.2):
    """Arco cuyo grosor y extensión crecen con el momento (N·m/kg); flecha según el sentido."""
    from matplotlib.patches import Arc
    if not np.isfinite(value) or abs(value) < 0.05:
        return
    span = min(abs(value) / max_value, 1.0) * 300
    lw = 2 + 8 * min(abs(value) / max_value, 1.0)
    theta1, theta2 = (90, 90 + span) if value > 0 else (90 - span, 90)
    ax.add_patch(Arc(centre, 2 * scale, 2 * scale, theta1=theta1, theta2=theta2, color=color, lw=lw, zorder=9,
                     alpha=0.9))


def video_carga():
    s = cmu_scene()
    fps = s["fps"]
    gt = s["seq"]
    side = kicking_side(gt, fps)
    m_gt = swing_leg_moments(gt, fps, side, 75.0, "male", cutoff_hz=12)
    h, fps_v = 80, 25
    xr, _, est17 = tv_reconstruction(s, h, fps_v)
    est8 = to_canonical(est17)
    m_tv = swing_leg_moments(est8, fps_v, side, 75.0, "male", cutoff_hz=0.35 * fps_v)
    cf = s["c_float"]
    t_gt = (np.arange(len(gt)) - cf) / fps * 1000
    t_tv = (np.arange(len(est8)) - cf / fps * fps_v) / fps_v * 1000
    loads_gt = kick_loads(gt, fps, 75.0, contact=s["c"], side=side)
    loads_tv = kick_loads(est8, fps_v, 75.0, contact=int(round(cf / fps * fps_v)), side=side, cutoff_hz=0.35 * fps_v)
    lo, hi = s["c"] - 48, s["c"] + 4
    with Mp4(OUT / "06_carga_articular.mp4", 24) as vid:
        for f in title_card("Momentos articulares del modelo", "Dinámica inversa simplificada de la pierna de golpeo\n"
                            "acuerdo laboratorio–TV; sin validación de carga tisular ni riesgo", fps=24, seconds=3):
            vid.write(f)
        for t in range(lo, hi):
            fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
            ax = fig.add_axes([0.0, 0.08, 0.52, 0.8])
            p2, _ = body_axes(ax, s, t, px=fig.dpi * 12.8 * 0.52 / 4.6 * 0.72, trail=False)
            hip_i, knee_i = (1, 2) if side == "r" else (4, 5)
            moment_arc(ax, p2[hip_i], m_gt["cadera_momento"][t] / 75, "#ef476f")
            moment_arc(ax, p2[knee_i], m_gt["rodilla_momento"][t] / 75, "#06d6a0")
            ax.text(0.02, 0.02, "rojo: momento de cadera   verde: momento de rodilla (grosor = magnitud)",
                    transform=ax.transAxes, fontsize=10, color="#c7d0db")
            for k, (key, name, col) in enumerate((("cadera_momento", "Momento cadera (+ flexor)", "#ef476f"),
                                                  ("rodilla_momento", "Momento rodilla (+ extensor)", "#06d6a0"))):
                a = fig.add_axes([0.58, 0.56 - 0.44 * k, 0.39, 0.33])
                sel = (t_gt >= t_gt[lo]) & (t_gt <= t_gt[hi])
                a.plot(t_gt[sel], m_gt[key][sel] / 75, color=col, lw=2.5, label="laboratorio (120 fps)")
                selv = (t_tv >= t_gt[lo]) & (t_tv <= t_gt[hi])
                a.plot(t_tv[selv], m_tv[key][selv] / 75, color=EST, lw=2, ls="--", marker="o", ms=4,
                       label=f"desde TV ({h} px, {fps_v} fps)")
                a.axvline(t_gt[t], color="white", lw=1)
                a.axhline(0, color=GRID)
                a.set_title(f"{name}, N·m/kg", fontsize=11)
                a.grid(color=GRID, alpha=0.5)
                a.legend(fontsize=9, facecolor=BG, edgecolor=GRID, labelcolor=FG, loc="upper left")
                if k == 1:
                    a.set_xlabel("ms respecto al contacto")
            fig.text(0.02, 0.94, f"t = {t_gt[t]:+.0f} ms", fontsize=16, weight="bold")
            fig.text(0.02, 0.90, f"Pico flexor de cadera: laboratorio {loads_gt['momento_cadera_flexor_max']:.2f}  ·  "
                     f"TV {loads_tv['momento_cadera_flexor_max']:.2f} N·m/kg", fontsize=12, color="#c7d0db")
            vid.write(figure_to_rgb(fig))
            plt.close(fig)


# ---------------------------------------------------------------------------------------------- 05
def video_movi(subject=3, cam="PG2"):
    from golpeo.datos_movi import MoviCamera, load_movi
    from golpeo.detector import rtmw, yolox
    from golpeo.elevador import Lifter
    from golpeo.h36m import coco_to_h36m
    from validar_video_movi import pick_box, player_height_px
    movi = ROOT / "datos" / "movi"
    path = next((movi / "3d").glob(f"F_Subjects_*/F_v3d_Subject_{subject}.mat"))
    tr = load_movi(path)
    gt8 = to_canonical(tr.x17)
    side = kicking_side(gt8, tr.fps)
    c120 = contact_frame(gt8, tr.fps, side)
    f0 = int(np.ceil(tr.frame0 / 4))
    frames = np.arange(f0, int(np.floor((tr.frame0 + len(tr.x17) - 1) / 4)) + 1)
    idx = 4 * frames - tr.frame0
    gt17v = tr.x17[idx]
    camera = MoviCamera.load(movi / "3d" / "Calib", cam)
    gt_uv = camera.project(gt17v)
    hn = player_height_px(gt_uv)
    det, pose = yolox(), rtmw()
    cap = cv2.VideoCapture(str(movi / "video" / f"F_{cam}_Subject_{subject}_L.avi"))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frames[0]))
    imgs, small_imgs, k_nat, k_50, s_50 = [], [], [], [], []
    for i in range(len(frames)):
        ok, img = cap.read()
        box = pick_box(det(img), gt_uv[i, 0])
        k, _ = pose(img, bboxes=[box])
        s = 50 / hn
        im = cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
        im = cv2.imdecode(cv2.imencode(".jpg", im, [cv2.IMWRITE_JPEG_QUALITY, 70])[1], cv2.IMREAD_COLOR)
        k2, sc2 = pose(im, bboxes=[np.asarray(box) * s])
        imgs.append(img), small_imgs.append(im), k_nat.append(k[0][:17]), k_50.append(k2[0][:17] / s), s_50.append(sc2[0][:17])
    uv, _ = coco_to_h36m(np.array(k_50), np.array(s_50))
    conf = np.full(uv.shape[:2], 0.9)              # las puntuaciones de RTMW no están en [0, 1] (ver validar_video_movi)
    est = Lifter().lift_person(uv, conf)
    gt8v = to_canonical(gt17v)
    est = est * thigh(gt8v) / thigh(to_canonical(est))
    est17 = rigid_align(np.concatenate([to_canonical(est), est], 1), np.concatenate([gt8v, gt17v], 1))[:, 8:]
    est8 = to_canonical(est17)
    kg, ke = knee_flexion(gt8v, side), knee_flexion(est8, side)
    cv_ = int(np.argmin(np.abs(idx - c120)))
    lo, hi = max(cv_ - 30, 0), min(cv_ + 15, len(frames))
    vis = est17 - est17[:, :1] + gt17v[:, :1]
    with Mp4(OUT / "05_video_real_movi.mp4", 10) as vid:
        for f in title_card("Validación con imagen real", "Vídeo real con 3D de laboratorio sincronizada (MoVi)\n"
                            "imagen nativa y reducida a 50 px como en una retransmisión", fps=10, seconds=2.5):
            vid.write(f)
        for t in range(lo, hi):
            fig = plt.figure(figsize=(12.8, 7.2), dpi=100)
            a0 = fig.add_axes([0.0, 0.3, 0.3, 0.6])
            im = cv2.cvtColor(imgs[t], cv2.COLOR_BGR2RGB)
            a0.imshow(im)
            P = coco_to_h36m(np.array(k_nat)[t:t + 1], np.ones((1, 17)))[0][0]
            for a, b in BONES:
                a0.plot(*P[[a, b]].T, color=KICK if (a, b) in RIGHT else "white", lw=2)
            ctr = gt_uv[lo:hi, 0].mean(0)
            a0.set_xlim(ctr[0] - hn * 0.8, ctr[0] + hn * 0.8)
            a0.set_ylim(ctr[1] + hn * 0.75, ctr[1] - hn * 0.85)
            a0.set_title(f"Imagen original (~{hn:.0f} px)", fontsize=11)
            a0.axis("off")
            a1 = fig.add_axes([0.31, 0.3, 0.25, 0.6])
            sm = cv2.cvtColor(small_imgs[t], cv2.COLOR_BGR2RGB)
            a1.imshow(sm, interpolation="nearest")
            Q = uv[t] * (50 / hn)
            for a, b in BONES:
                a1.plot(*Q[[a, b]].T, color=KICK if (a, b) in RIGHT else "white", lw=1.5)
            c2 = ctr * 50 / hn
            a1.set_xlim(c2[0] - 40, c2[0] + 40)
            a1.set_ylim(c2[1] + 38, c2[1] - 42)
            a1.set_title("Reducida a 50 px + JPEG (como en TV)", fontsize=11)
            a1.axis("off")
            a2 = fig.add_axes([0.57, 0.3, 0.42, 0.62], projection="3d")
            a2.set_facecolor(BG)
            for X, col, lab in ((gt17v[t], "white", "laboratorio"), (vis[t], EST, "desde 50 px")):
                for i, (a, b) in enumerate(BONES):
                    a2.plot(*X[[a, b]].T, color=col, lw=2.5, label=lab if i == 0 else None)
            ct = gt17v[t, 0]
            a2.set_xlim(ct[0] - 0.9, ct[0] + 0.9), a2.set_ylim(ct[1] - 0.9, ct[1] + 0.9), a2.set_zlim(0, 1.9)
            a2.view_init(elev=8, azim=-70)
            a2.set_xticks([]), a2.set_yticks([]), a2.set_zticks([])
            a2.xaxis.pane.fill = a2.yaxis.pane.fill = a2.zaxis.pane.fill = False
            a2.legend(loc="upper left", fontsize=10, facecolor=BG, edgecolor=GRID, labelcolor=FG)
            a3 = fig.add_axes([0.07, 0.07, 0.88, 0.17])
            tt = (np.arange(lo, hi) - cv_) / 30 * 1000
            a3.plot(tt, kg[lo:hi], color="white", lw=2.5, label="laboratorio")
            a3.plot(tt, ke[lo:hi], color=EST, lw=2.5, label="desde 50 px")
            a3.axvline((t - cv_) / 30 * 1000, color=KICK)
            a3.set_ylabel("Rodilla (°)")
            a3.set_xlabel("ms respecto al golpeo")
            a3.grid(color=GRID, alpha=0.5)
            a3.legend(fontsize=9, facecolor=BG, edgecolor=GRID, labelcolor=FG, loc="upper left")
            fig.text(0.01, 0.95, "MoVi (BioMotion Lab) · solo uso académico", fontsize=10, color="#8a97a8")
            vid.write(figure_to_rgb(fig))
            plt.close(fig)


# ---------------------------------------------------------------------------------------------- 00
def video_resumen():
    """Montaje para CV: cartelas con resultados + los vídeos sin material con derechos (01, 02, 04, 06)."""
    path = ROOT / "resultados" / "cartelas.json"                 # [texto, subtítulo] con los resultados clave
    cartelas = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
    size, fps = (1280, 720), 25
    with Mp4(OUT / "00_resumen.mp4", fps) as vid:
        def cards(text, sub="", seconds=3.0):
            for f in title_card(text, sub, size=size, seconds=seconds, fps=fps):
                vid.write(f)

        def clip(name, max_s=14.0):
            cap = cv2.VideoCapture(str(OUT / name))
            src_fps = cap.get(cv2.CAP_PROP_FPS) or fps
            frames = []
            while True:
                ok, img = cap.read()
                if not ok:
                    break
                frames.append(img)
            # se re-muestrea a 25 fps conservando la cámara lenta original
            n_out = min(int(len(frames) / src_fps * fps), int(max_s * fps))
            for i in range(n_out):
                img = frames[min(int(i * src_fps / fps), len(frames) - 1)]
                vid.write(cv2.resize(img, size)[..., ::-1])   # BGR (OpenCV) → RGB

        cards("Biomecánica del disparo\ndesde la retransmisión", "¿Qué se puede medir de verdad desde la tele?", 3.5)
        cards("Comparación con captura óptica", "escala y alineamiento de referencia · contacto y pierna conocidos", 3.5)
        for name in ("01_contacto_balon.mp4", "02_camara_tv_virtual.mp4", "04_reconstruccion_3d.mp4",
                     "06_carga_articular.mp4"):
            if (OUT / name).exists():
                clip(name)
        for text, sub in cartelas:
            cards(text, sub, 4.5)
        cards("Preprint SportRxiv · sin revisión por pares", "DOI 10.51224/SportRxiv.1131\nCMU · MoVi · 3DSP · RTMW · MotionAGFormer", 3.0)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    jobs = {"01": video_contacto, "02": video_camara_tv, "03": video_3dsp, "04": video_reconstruccion,
            "05": video_movi, "06": video_carga, "00": video_resumen}
    for key in (sys.argv[1:] or ["01", "02", "03", "04", "05", "06", "00"]):
        print("vídeo", key, flush=True)
        jobs[key]()


if __name__ == "__main__":
    main()
