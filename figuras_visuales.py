"""Figuras y vídeo "de presentación": jugador en volumen con esqueleto superpuesto, balón,
trayectoria, vectores de velocidad y fuerza media estimada sobre el balón.

  fig6_golpeo_vectores.png   golpeo real de CMU (10_01), vista lateral con estela
  video_golpeo_vectores.mp4  la misma escena animada
  fig7_3dsp_real_vs_rtmw.png disparos reales de la Premier League (3DSP) con esqueleto manual frente a RTMW.
                             USO INTERNO: imágenes de retransmisión con derechos; no publicar.

La fuerza NO se mide (no hay plataformas de fuerza): F ≈ m·v_salida / t_contacto, con t_contacto supuesto.
Uso:  python figuras_visuales.py
"""
import json
from pathlib import Path

import cv2
import matplotlib
import numpy as np

matplotlib.use("Agg")
import matplotlib.patheffects as pe
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, Polygon

from golpeo.cinematica import knee_flexion
from golpeo.contacto import ball_contact
from golpeo.datos_cmu import load_cmu, load_cmu_h36m
from golpeo.error2d import coco_to_3dsp
from golpeo.h36m import to_canonical

ROOT = Path(__file__).parent
OUT = ROOT / "resultados"
M_BALL = 0.43            # kg
T_CONTACT = 0.010        # s, valor supuesto (orden de magnitud de un golpeo con empeine)
BG, FG = "#0f1724", "#e8edf3"
KICK, SUPPORT, TRUNK = "#ff8a3d", "#2ec4b6", "#9aa5b1"
LIMBS = [((1, 2), 0.075, "kick"), ((2, 3), 0.060, "kick"), ((4, 5), 0.075, "sup"), ((5, 6), 0.060, "sup"),
         ((11, 12), 0.045, "arm"), ((12, 13), 0.038, "arm"), ((14, 15), 0.045, "arm"), ((15, 16), 0.038, "arm")]
BONES = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (0, 7), (7, 8), (8, 9), (9, 10),
         (8, 11), (11, 12), (12, 13), (8, 14), (14, 15), (15, 16)]


def interp_nan(x):
    """Rellena huecos (balón tapado) por interpolación lineal en el tiempo, solo para dibujar."""
    out = x.copy()
    t = np.arange(len(x))
    ok = np.isfinite(x).all(axis=1)
    for d in range(x.shape[1]):
        out[:, d] = np.interp(t, t[ok], x[ok, d])
    return out


def sagittal(points, origin, e1):
    """Proyección al plano del golpeo: (avance horizontal en la dirección del balón, altura)."""
    rel = points - origin
    return np.stack([rel @ e1, rel[..., 2]], axis=-1)


def draw_body(ax, p2, alpha=1.0, skeleton=True, scale_px=None):
    """Cuerpo en volumen (miembros gruesos, tronco relleno, cabeza) + esqueleto fino encima."""
    lw = lambda w: w * scale_px
    trunk = Polygon(p2[[11, 14, 1, 4]][[0, 1, 2, 3]], closed=True, fc=TRUNK, ec="none", alpha=0.85 * alpha, zorder=2)
    ax.add_patch(trunk)
    for (a, b), w, kind in LIMBS:
        col = {"kick": KICK, "sup": SUPPORT, "arm": TRUNK}[kind]
        ax.plot(*p2[[a, b]].T, color=col, lw=lw(w), solid_capstyle="round", alpha=alpha, zorder=3)
    ax.add_patch(Circle(p2[10] - [0, 0.05], 0.11, fc=TRUNK, ec="none", alpha=alpha, zorder=3))
    if skeleton:
        for a, b in BONES:
            ax.plot(*p2[[a, b]].T, color="white", lw=1.2, alpha=0.9 * alpha, zorder=4)
        ax.scatter(*p2.T, s=10, color="white", zorder=5, alpha=alpha)


def arrow(ax, start, vec, color, label, scale):
    ax.annotate("", xy=start + vec * scale, xytext=start, zorder=7,
                arrowprops=dict(arrowstyle="-|>,head_width=0.35,head_length=0.7", lw=3, color=color))
    ax.text(*(start + vec * scale + [0.03, 0.04]), label, color=color, fontsize=11, weight="bold", zorder=8,
            path_effects=[pe.withStroke(linewidth=3, foreground=BG)])


def knee_arc(ax, p2, hip, knee, ankle, value, color):
    v1, v2 = p2[hip] - p2[knee], p2[ankle] - p2[knee]
    a1, a2 = np.degrees(np.arctan2(v1[1], v1[0])), np.degrees(np.arctan2(v2[1], v2[0]))
    lo, hi = sorted([a1, a2]) if abs(a1 - a2) <= 180 else sorted([a1, a2])[::-1]
    ax.add_patch(Arc(p2[knee], 0.22, 0.22, theta1=lo, theta2=hi, color=color, lw=2, zorder=6))
    ax.text(*(p2[knee] + [0.13, -0.02]), f"{value:.0f}°", color=color, fontsize=10, weight="bold", zorder=8,
            path_effects=[pe.withStroke(linewidth=3, foreground=BG)])


def scene():
    path = ROOT / "datos" / "cmu" / "10_01.c3d"
    x17, fps = load_cmu_h36m(path)
    trial = load_cmu(path)
    c_float, v_ball = ball_contact(trial.ball, fps)
    c = int(round(c_float))
    ball = interp_nan(trial.ball)
    launch = ball[min(c + 6, len(ball) - 1)] - ball[c]
    e1 = launch.copy()
    e1[2] = 0
    e1 /= np.linalg.norm(e1)
    origin = ball[c - 30].copy()
    origin[2] = 0
    foot_v = (x17[c, 3] - x17[c - 2, 3]) / (2 / fps)                  # tobillo derecho justo antes
    ball_v = launch / (6 / fps)
    return dict(x17=x17, fps=fps, c=c, ball=ball, e1=e1, origin=origin, foot_v=foot_v, ball_v=ball_v,
                v_ball=v_ball, knee=knee_flexion(to_canonical(x17), "r"), knee_sup=knee_flexion(to_canonical(x17), "l"))


def frame_plot(ax, s, t, trail=True):
    x17, e1, o, c = s["x17"], s["e1"], s["origin"], s["c"]
    ax.set_facecolor(BG)
    ax.axhline(0, color="#3b4a5e", lw=2, zorder=1)
    ax.fill_between([-3, 6], -0.3, 0, color="#163020", zorder=0)               # césped
    if trail:
        for k, tt in enumerate(range(max(t - 36, 0), t, 6)):
            draw_body(ax, sagittal(x17[tt], o, e1), alpha=0.10 + 0.04 * k, skeleton=False, scale_px=s["px"])
    p2 = sagittal(x17[t], o, e1)
    draw_body(ax, p2, scale_px=s["px"])
    b2 = sagittal(s["ball"], o, e1)
    ax.plot(*b2[c:].T, ls="--", color="#ffd166", lw=1.5, alpha=0.8, zorder=5)
    ax.add_patch(Circle(b2[t], 0.11, fc="#ffd166", ec="white", lw=1.5, zorder=6))
    return p2, b2


def fig_vectores(s):
    fig, ax = plt.subplots(figsize=(13, 7), facecolor=BG)
    s["px"] = fig.dpi * 13 / 4.2 / 1.0 * 0.72                                 # metros → puntos de línea
    c = s["c"]
    p2, b2 = frame_plot(ax, s, c)
    fv = sagittal(s["foot_v"][None] + s["origin"], s["origin"], s["e1"])[0]
    bv = sagittal(s["ball_v"][None] + s["origin"], s["origin"], s["e1"])[0]
    force = M_BALL * s["v_ball"] / T_CONTACT
    arrow(ax, p2[3], fv, KICK, f"tobillo {np.linalg.norm(s['foot_v']):.1f} m/s", 0.06)
    arrow(ax, b2[c], bv, "#ffd166", f"balón {s['v_ball']:.1f} m/s", 0.06)
    arrow(ax, b2[c] + [0, 0.25], bv / np.linalg.norm(bv), "#ef476f", f"F media ≈ {force:.0f} N*", 0.6)
    tmax = int(np.argmax(s["knee"][c - 40:c])) + c - 40
    knee_arc(ax, p2, 4, 5, 6, s["knee_sup"][c], SUPPORT)
    ax.text(0.01, 0.97, "Golpeo real capturado en laboratorio (CMU, sujeto 10, 120 fps)", transform=ax.transAxes,
            color=FG, fontsize=14, weight="bold", va="top")
    ax.text(0.01, 0.91, f"Instante de contacto · flexión máx. rodilla de golpeo {s['knee'][tmax]:.0f}° · "
            f"rodilla de apoyo {s['knee_sup'][c]:.0f}°", transform=ax.transAxes, color=FG, fontsize=11, va="top")
    ax.text(0.01, 0.03, f"* Estimación: F = m·v / t, con m = {M_BALL} kg y un contacto supuesto de "
            f"{T_CONTACT * 1000:.0f} ms (no medido). Estela: 300 ms previos.", transform=ax.transAxes,
            color="#8a97a8", fontsize=9)
    ax.set_xlim(-1.6, 3.2)
    ax.set_ylim(-0.3, 2.2)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    fig.savefig(OUT / "fig6_golpeo_vectores.png", dpi=150, facecolor=BG)
    plt.close(fig)


def video_vectores(s):
    c, fps = s["c"], s["fps"]
    writer = None
    for t in range(c - 60, min(c + 36, len(s["x17"])), 2):
        fig, ax = plt.subplots(figsize=(12, 6.5), dpi=100, facecolor=BG)
        s["px"] = fig.dpi * 12 / 4.2 * 0.72
        p2, b2 = frame_plot(ax, s, t)
        if t >= c:
            bv = sagittal(s["ball_v"][None] + s["origin"], s["origin"], s["e1"])[0]
            arrow(ax, b2[t], bv, "#ffd166", f"balón {s['v_ball']:.1f} m/s", 0.05)
        else:
            v = (s["x17"][t, 3] - s["x17"][t - 2, 3]) * fps / 2
            fv = sagittal(v[None] + s["origin"], s["origin"], s["e1"])[0]
            arrow(ax, p2[3], fv, KICK, f"tobillo {np.linalg.norm(v):.1f} m/s", 0.06)
        ax.text(0.01, 0.96, f"t = {(t - c) / fps * 1000:+.0f} ms respecto al contacto   ·   "
                f"rodilla de golpeo {s['knee'][t]:.0f}°", transform=ax.transAxes, color=FG, fontsize=13, va="top")
        ax.set_xlim(-1.6, 3.2)
        ax.set_ylim(-0.3, 2.2)
        ax.set_aspect("equal")
        ax.axis("off")
        fig.tight_layout()
        fig.canvas.draw()
        img = cv2.cvtColor(np.asarray(fig.canvas.buffer_rgba()), cv2.COLOR_RGBA2BGR)
        plt.close(fig)
        if writer is None:
            writer = cv2.VideoWriter(str(OUT / "video_golpeo_vectores.mp4"), cv2.VideoWriter_fourcc(*"mp4v"),
                                     15, (img.shape[1], img.shape[0]))
        writer.write(img)
    writer.release()


def fig_3dsp():
    from rtmlib import RTMPose
    from medir_error_2d import box, load_gt
    pose = RTMPose(str(ROOT / "modelos" / "rtmw" / "end2end.onnx"), model_input_size=(288, 384),
                   backend="onnxruntime", device="cpu")
    shots = ["00003", "00021", "00057", "00104", "00142", "00188"]
    fig, axes = plt.subplots(1, len(shots), figsize=(18, 3.9), facecolor=BG)
    for ax, shot in zip(axes, shots):
        d = ROOT / "datos" / "3dsp" / "3dsp" / "train" / shot
        frame = "011"
        img = cv2.imread(str(d / "img" / f"{frame}.jpg"))
        gt = load_gt(d / "posture" / f"{frame}.json")
        k, _ = pose(img, bboxes=[box(gt, img.shape)])
        est = coco_to_3dsp(k[0])
        up = 4
        big = cv2.resize(img, None, fx=up, fy=up, interpolation=cv2.INTER_CUBIC)
        ax.imshow(cv2.cvtColor(big, cv2.COLOR_BGR2RGB))
        for P, col, lab in ((gt, "#2ec4b6", "anotación manual"), (est, "#ff8a3d", "RTMW")):
            for i, (a, b) in enumerate(BONES):
                ax.plot(*(P[[a, b]] * up).T, color=col, lw=2, label=lab if i == 0 else None)
        h = gt[[3, 6], 1].max() - gt[10, 1]
        ax.set_title(f"disparo {shot} · jugador de {h:.0f} px", color=FG, fontsize=10)
        ax.axis("off")
    axes[0].legend(loc="lower left", fontsize=8)
    fig.suptitle("Disparos reales de retransmisión (3DSP, Premier League vía SoccerNet): anotación manual frente a "
                 "RTMW  —  USO INTERNO, imágenes con derechos", color=FG, fontsize=12)
    fig.tight_layout()
    fig.savefig(OUT / "fig7_3dsp_real_vs_rtmw.png", dpi=140, facecolor=BG)
    plt.close(fig)


def main():
    s = scene()
    print(f"contacto f={s['c']}, tobillo {np.linalg.norm(s['foot_v']):.1f} m/s, balón {s['v_ball']:.1f} m/s, "
          f"F≈{M_BALL * s['v_ball'] / T_CONTACT:.0f} N")
    fig_vectores(s)
    video_vectores(s)
    fig_3dsp()


if __name__ == "__main__":
    main()
