"""Figuras "visuales" del artículo (esqueletos y biomecánica), en inglés y en español.

  fig1_design.png   diseño del estudio
  fig2_model.png    rasgos del golpeo sobre el esqueleto, diagrama de cuerpo libre y momentos articulares
  fig3_recon.png    lo que ve la cámara de TV y lo que se reconstruye; curvas medias de 83 participantes
  figS3_bland.png   Bland–Altman de los seis rasgos en la condición típica de retransmisión

Uso:  python figuras_articulo.py   (después de experimento_sensibilidad.py y ondas_movi.py)
"""
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Arc, Circle, FancyArrowPatch, FancyBboxPatch, Polygon, Rectangle

import informe_sensibilidad as rep                       # estilo, paleta y NAMES comunes
from experimento_sensibilidad import ELEVACION, resample, thigh
from golpeo.camara import film
from golpeo.carga import swing_leg_moments
from golpeo.cinematica import FEATURE_NAMES, contact_frame, hip_flexion, kicking_side, knee_flexion, rigid_align, \
    trunk_lean
from golpeo.contacto import ball_contact
from golpeo.datos_cmu import load_cmu, load_cmu_h36m
from golpeo.ensayos import fill_gaps
from golpeo.figuras_es import save_fig
from golpeo.h36m import to_canonical
from golpeo.metricas import agreement
from golpeo.ruido import ResidualBank
from golpeo.spm import paired_snpm

ROOT = Path(__file__).parent
RES = ROOT / "resultados"
INK, MUTED, GRID = "#1f2937", "#9ca3af", "#e5e7eb"
KICK, SUPPORT, EST, GT = "#eb6834", "#1baf7a", "#2a78d6", "#6b7280"
PANEL = "#f3f6fa"
BONES = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (0, 7), (7, 8), (8, 9), (9, 10),
         (8, 11), (11, 12), (12, 13), (8, 14), (14, 15), (15, 16)]
LEG = {"r": [(0, 1), (1, 2), (2, 3)], "l": [(0, 4), (4, 5), (5, 6)]}
J = {"r": (1, 2, 3), "l": (4, 5, 6)}                     # cadera, rodilla, tobillo (H36M)


# ------------------------------------------------------------------------------------------------ datos
def scene(name="10_01"):
    path = ROOT / "datos" / "cmu" / f"{name}.c3d"
    x17, fps = load_cmu_h36m(path)
    x17, _ = fill_gaps(x17, fps)
    seq = to_canonical(x17)
    side = kicking_side(seq, fps)
    tr = load_cmu(path)
    cb = ball_contact(tr.ball, fps)[0] if tr.ball is not None else None
    c = int(round(cb)) if cb is not None else contact_frame(seq, fps, side)
    peak = contact_frame(seq, fps, side)
    v = np.gradient(seq[:, 7 if side == "r" else 6], axis=0)[peak]
    v[2] = 0
    e1 = v / np.linalg.norm(v)                           # dirección horizontal del golpeo
    e_lat = np.cross([0, 0, 1.0], e1)
    origin = x17[c, 0].copy()
    origin[2] = 0
    ball = None
    if tr.ball is not None:
        b = tr.ball.copy()
        ok = np.isfinite(b).all(axis=1)
        t = np.arange(len(b))
        for d in range(3):
            b[:, d] = np.interp(t, t[ok], b[ok, d])
        ball = b
    w0 = max(c - int(round(0.3 * fps)), 0)
    hip = hip_flexion(seq, side)
    knee = knee_flexion(seq, side)
    k = w0 + int(np.nanargmax(knee[w0:c + 1]))           # flexión máxima de rodilla (armado)
    b_end = w0 + int(np.nanargmin(hip[w0:c + 1]))        # final del armado
    return dict(x17=x17, seq=seq, fps=fps, side=side, c=c, k=k, b=b_end, e1=e1, e_lat=e_lat, origin=origin, ball=ball)


def sag(s, P):
    rel = P - s["origin"]
    return np.stack([rel @ s["e1"], rel[..., 2]], -1)


def front(s, P):
    rel = P - s["origin"]
    return np.stack([rel @ s["e_lat"], rel[..., 2]], -1)


def oblique(s, P, yaw=35.0, pitch=18.0):
    """Vista en perspectiva paralela desde arriba y de lado (para sugerir 3D)."""
    a, b = np.radians(yaw), np.radians(pitch)
    ex = np.cos(a) * s["e1"] + np.sin(a) * s["e_lat"]
    ed = -np.sin(a) * s["e1"] + np.cos(a) * s["e_lat"]
    rel = P - s["origin"]
    return np.stack([rel @ ex, rel[..., 2] * np.cos(b) + (rel @ ed) * np.sin(b)], -1)


# ------------------------------------------------------------------------------------------------ dibujo
def draw_skel(ax, p, side, color=INK, kick=KICK, support=None, lw=2.2, alpha=1.0, z=3, head=True, dots=True):
    sup = LEG["l" if side == "r" else "r"]
    for a, b in BONES:
        col = kick if (a, b) in LEG[side] else (support if support and (a, b) in sup else color)
        ax.plot(*p[[a, b]].T, color=col, lw=lw, alpha=alpha, solid_capstyle="round", zorder=z)
    if head:
        centre = p[10] + 0.35 * (p[9] - p[10])
        ax.add_patch(Circle(centre, 0.085, fc="white", ec=color, lw=lw * 0.7, alpha=alpha, zorder=z))
    if dots:
        ax.scatter(*p[[1, 2, 3, 4, 5, 6, 11, 14]].T, s=lw * 4, color=color, zorder=z + 1, alpha=alpha, lw=0)


def mark_angle(ax, centre, v1, v2, r, color, text, xytext):
    """Arco entre dos direcciones y etiqueta fuera del cuerpo (posición en fracción de los ejes) con guía."""
    a1, a2 = np.degrees(np.arctan2(v1[1], v1[0])), np.degrees(np.arctan2(v2[1], v2[0]))
    d = (a2 - a1) % 360
    if d > 180:
        a1, d = a2, 360 - d
    ax.add_patch(Arc(centre, 2 * r, 2 * r, theta1=a1, theta2=a1 + d, color=color, lw=2.0, zorder=6))
    mid = np.radians(a1 + d / 2)
    tip = centre + r * np.array([np.cos(mid), np.sin(mid)])
    ax.annotate(text, xy=tip, xytext=xytext, textcoords="axes fraction", fontsize=7, color=color, weight="bold",
                ha="left", va="center", zorder=7,
                arrowprops=dict(arrowstyle="-", color=color, lw=0.8, shrinkA=2, shrinkB=1))


def dashed(ax, p, q, color=MUTED):
    ax.plot(*np.stack([p, q]).T, color=color, ls=(0, (3, 2)), lw=1, zorder=2)


def ground(ax, x0=-3.0, x1=3.0):
    ax.plot([x0, x1], [0, 0], color="#b7c4b0", lw=1.2, zorder=0)
    ax.fill_between([x0, x1], -0.25, 0, color="#eef4ea", zorder=-1, lw=0)


def ground_grid(ax, s, half=1.0, step=0.5):
    for v in np.arange(-half, half + 1e-9, step):
        for line in ((np.array([v, -half]), np.array([v, half])), (np.array([-half, v]), np.array([half, v]))):
            P = np.array([s["origin"] + a * s["e1"] + b * s["e_lat"] for a, b in line])
            q = oblique(s, P)
            ax.plot(*q.T, color="#cbd5c4", lw=0.7, zorder=0)


def clean(ax):
    ax.set_aspect("equal")
    ax.axis("off")


def pixel_canvas(uv, h=80, pad=1.35, lw=1):
    n = int(h * pad)
    img = np.full((n, n), 247, np.uint8)
    q = uv - uv.reshape(-1, 2).mean(0) + n / 2
    for a, b in BONES:
        cv2.line(img, tuple(np.round(q[a]).astype(int)), tuple(np.round(q[b]).astype(int)), 40, lw, cv2.LINE_AA)
    return img


def thumb(ax, img, edge=MUTED):
    ax.imshow(img, cmap="gray", vmin=0, vmax=255, interpolation="nearest")
    ax.set_xticks([]), ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(True)
        sp.set_color(edge)
        sp.set_linewidth(0.8)


def moment_arrow(ax, centre, r, a_from, a_to, color, lw=1.8):
    """Flecha curva (momento) de a_from a a_to grados alrededor de centre."""
    th = np.radians(np.linspace(a_from, a_to, 40))
    pts = centre + r * np.stack([np.cos(th), np.sin(th)], -1)
    ax.plot(*pts[:-3].T, color=color, lw=lw, zorder=6, solid_capstyle="round")
    ax.annotate("", xy=pts[-1], xytext=pts[-4], arrowprops=dict(arrowstyle="-|>", color=color, lw=lw,
                                                               mutation_scale=10), zorder=6)


# ------------------------------------------------------------------------------------------------ figura 1
FIG1_W, FIG1_GAP = 0.232, 0.016


def fig_design(s, bank):
    fig = plt.figure(figsize=(7.4, 3.0))
    S = rep.SERIES
    xs = [0.008 + i * (FIG1_W + FIG1_GAP) for i in range(4)]
    heads = [("Laboratory\nground truth", S[0]), ("Broadcast\nvideo", S[1]), ("2D → 3D\nreconstruction", S[2]),
             ("Agreement\nwith the lab", S[4])]
    captions = [("optical motion capture", "CMU · 7 ball kicks", "MoVi · 83 participants"),
                ("5 views × 5 sizes × 25/50 fps", "real 2D-detector residuals", "+ real video (digital twin)"),
                ("RTMW-x 2D detector", "MotionAGFormer lifter", "official vs fine-tuned"),
                ("6 joint angles · 3 moments", "bias · MAE · LoA · ICC", "→ injury-study sample size")]
    for i, (x0, (title, col), cap) in enumerate(zip(xs, heads, captions)):
        fig.patches.append(FancyBboxPatch((x0, 0.03), FIG1_W, 0.94, boxstyle="round,pad=0,rounding_size=0.015",
                                          transform=fig.transFigure, fc=PANEL, ec="none", zorder=-5))
        fig.text(x0 + 0.02, 0.885, str(i + 1), ha="center", va="center", color="white", fontsize=7.5, weight="bold",
                 bbox=dict(boxstyle="circle,pad=0.28", fc=col, ec="none"))
        fig.text(x0 + 0.042, 0.885, title, ha="left", va="center", color=INK, fontsize=7.8, weight="bold",
                 linespacing=1.1)
        for j, line in enumerate(cap):
            fig.text(x0 + FIG1_W / 2, 0.215 - j * 0.07, line, ha="center", va="center", fontsize=6.4,
                     color=INK if j == 0 else rep.INK2)
        if i < 3:
            fig.patches.append(FancyArrowPatch((x0 + FIG1_W - 0.006, 0.56), (x0 + FIG1_W + FIG1_GAP + 0.008, 0.56),
                                               transform=fig.transFigure, arrowstyle="-|>", mutation_scale=12,
                                               lw=1.6, color=MUTED, zorder=5))
    x17, side = s["x17"], s["side"]
    # 1 · golpeo de laboratorio con estela
    ax = fig.add_axes([xs[0] + 0.01, 0.29, FIG1_W - 0.02, 0.52])
    frames = list(range(s["k"] - 30, s["c"], 10))
    for i, t in enumerate(frames):
        draw_skel(ax, sag(s, x17[t]), side, color="#9aa5b4", kick="#f4a37f", lw=1.2,
                  alpha=0.2 + 0.45 * i / len(frames), head=False, dots=False)
    draw_skel(ax, sag(s, x17[s["c"]]), side, lw=2.0)
    if s["ball"] is not None:
        ax.add_patch(Circle(sag(s, s["ball"][s["c"]]), 0.11, fc="#ffd166", ec=INK, lw=0.8, zorder=5))
    ground(ax)
    ax.set_xlim(-1.3, 1.0), ax.set_ylim(-0.1, 1.95)
    clean(ax)
    # 2 · cámara virtual (anillo de vistas) y miniaturas a 200/80/50 px
    x0 = xs[1]
    ax = fig.add_axes([x0 + 0.004, 0.33, 0.125, 0.47])
    ax.add_patch(Circle((0, 0), 1.0, fc="#e2eedc", ec="none"))
    ax.add_patch(Circle((0, 0), 0.12, fc=INK, ec="none", zorder=3))
    ax.annotate("", xy=(0, 0.55), xytext=(0, 0.12), arrowprops=dict(arrowstyle="-|>", color=KICK, lw=1.4), zorder=5)
    for az in (0, 45, 90, 135, 180):
        a = np.radians(90 - az)                            # 90° = lateral, cámara arriba del dibujo
        u = np.array([np.cos(a), np.sin(a)])
        ax.plot(*np.stack([0.2 * u, 1.1 * u]).T, color=S[1], lw=0.7, alpha=0.55)
        ax.add_patch(Rectangle(1.2 * u - 0.1, 0.2, 0.2, fc=S[1], ec="none", zorder=4))
        ha = "left" if u[0] > 0.3 else "right" if u[0] < -0.3 else "center"
        va = "bottom" if u[1] > 0.3 else "top" if u[1] < -0.3 else "center"
        ax.text(*(1.36 * u), f"{az}°", fontsize=5.6, ha=ha, va=va, color=rep.INK2)
    ax.set_xlim(-1.75, 1.95), ax.set_ylim(-1.85, 1.85)
    clean(ax)
    xr = resample(x17, s["fps"], 25)
    cr = int(round(s["c"] / s["fps"] * 25))
    for i, h in enumerate((200, 80, 50)):
        rng = np.random.default_rng(h)
        uv, _ = film(xr, 90, ELEVACION, h, 0, 0, rng)
        uv = uv + bank.sample(len(uv), 25, h, rng)
        a2 = fig.add_axes([x0 + 0.14, 0.675 - i * 0.15, 0.05, 0.123])
        thumb(a2, pixel_canvas(uv[cr - 3], h, lw=2 if h >= 200 else 1))
        fig.text(x0 + 0.195, 0.736 - i * 0.15, f"{h} px", fontsize=5.8, color=rep.INK2, va="center")
    # 3 · 2D → 3D
    x0 = xs[2]
    rng = np.random.default_rng(80)
    uv, _ = film(xr, 90, ELEVACION, 80, 0, 0, rng)
    uv = uv + bank.sample(len(uv), 25, 80, rng)
    ax = fig.add_axes([x0 + 0.008, 0.44, 0.085, 0.21])
    img = pixel_canvas(uv[cr], 80)
    thumb(ax, np.full_like(img, 247), edge=GRID)
    q = uv[cr] - uv[cr].mean(0) + img.shape[0] / 2
    for a, b in BONES:
        ax.plot(*q[[a, b]].T, color=KICK if (a, b) in LEG[side] else GT, lw=0.9)
    ax.scatter(*q.T, s=5, color=INK, zorder=3, lw=0)
    ax.set_title("2D", fontsize=7, color=rep.INK2, pad=2)
    fig.patches.append(FancyArrowPatch((x0 + 0.097, 0.545), (x0 + 0.122, 0.545), transform=fig.transFigure,
                                       arrowstyle="-|>", mutation_scale=10, lw=1.3, color=S[2], zorder=5))
    ax = fig.add_axes([x0 + 0.118, 0.29, 0.11, 0.52])
    ground_grid(ax, s)
    draw_skel(ax, oblique(s, x17[s["c"]]), side, lw=1.9)
    ax.set_xlim(-1.0, 1.0), ax.set_ylim(-0.45, 1.95)
    clean(ax)
    ax.set_title("3D", fontsize=7, color=rep.INK2, pad=2)
    # 4 · rasgos y clases de acuerdo
    x0 = xs[3]
    ax = fig.add_axes([x0 + 0.004, 0.29, 0.12, 0.52])
    t = s["k"]
    p = sag(s, x17[t])
    draw_skel(ax, p, side, lw=1.8, support=SUPPORT)
    hi, kn, an = J[side]
    ext = p[kn] + 0.3 * (p[kn] - p[hi]) / np.linalg.norm(p[kn] - p[hi])
    dashed(ax, p[kn], ext)
    a1 = np.degrees(np.arctan2(*(ext - p[kn])[::-1]))
    a2 = np.degrees(np.arctan2(*(p[an] - p[kn])[::-1]))
    lo, hi_ = sorted((a1, a2))
    ax.add_patch(Arc(p[kn], 0.3, 0.3, theta1=lo if hi_ - lo < 180 else hi_, theta2=hi_ if hi_ - lo < 180 else lo + 360,
                     color=KICK, lw=2, zorder=6))
    moment_arrow(ax, p[hi], 0.2, 130, 230, "#d03b3b", lw=1.5)
    ground(ax)
    ax.set_xlim(-1.05, 0.6), ax.set_ylim(-0.1, 1.95)
    clean(ax)
    fig.text(x0 + 0.135, 0.79, "ICC", fontsize=6.6, color=INK, weight="bold")
    for i, cls in enumerate(("good", "moderate", "poor")):
        y = 0.71 - i * 0.085
        fig.patches.append(FancyBboxPatch((x0 + 0.135, y - 0.022), 0.016, 0.044, boxstyle="round,pad=0,rounding_size=0.004",
                                          transform=fig.transFigure, fc=rep.STATUS[cls], ec="none"))
        fig.text(x0 + 0.157, y, cls, fontsize=6.3, va="center", color=INK)
    save_fig(fig, "fig1_design.png")
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ figura 2
def fig_model(s, slow):
    fig = plt.figure(figsize=(7.4, 5.9))
    gs = fig.add_gridspec(2, 1, height_ratios=[1, 1.08], hspace=0.14)
    top = gs[0].subgridspec(1, 4, wspace=0.04)
    bottom = gs[1].subgridspec(1, 2, width_ratios=[0.92, 1.08], wspace=0.22)
    x17, seq, side = s["x17"], s["seq"], s["side"]
    sup = "l" if side == "r" else "r"
    hi, kn, an = J[side]
    shi, skn, san = J[sup]
    purple = rep.SERIES[6]

    def skeleton_panel(k, t, title, view=sag, xlim=(-1.15, 0.95)):
        ax = fig.add_subplot(top[0, k])
        p = view(s, x17[t])
        draw_skel(ax, p, side, support=SUPPORT, lw=2.0)
        if view is sag and s["ball"] is not None and t == s["c"]:
            ax.add_patch(Circle(sag(s, s["ball"][t]), 0.11, fc="#ffd166", ec=INK, lw=0.8, zorder=5))
        ground(ax)
        ax.set_xlim(*xlim), ax.set_ylim(-0.1, 2.0)
        clean(ax)
        ax.set_title(title, loc="left", fontsize=8.3)
        return ax, p

    # a · final del armado: extensión máxima de cadera
    t = s["b"]
    ax, p = skeleton_panel(0, t, "a  End of backswing")
    down = p[hi] + 0.5 * (p[0] - p[8]) / np.linalg.norm(p[0] - p[8])
    dashed(ax, p[hi], down)
    mark_angle(ax, p[hi], down - p[hi], p[kn] - p[hi], 0.22, "#d03b3b",
               f"kicking-hip\nextension\n{-hip_flexion(seq, side)[t]:.0f}°", (0.0, 0.66))
    # b · flexión máxima de rodilla
    t = s["k"]
    ax, p = skeleton_panel(1, t, "b  Peak knee flexion")
    ext = p[kn] + 0.4 * (p[kn] - p[hi]) / np.linalg.norm(p[kn] - p[hi])
    dashed(ax, p[kn], ext)
    mark_angle(ax, p[kn], ext - p[kn], p[an] - p[kn], 0.15, KICK,
               f"kicking-knee\nflexion\n{knee_flexion(seq, side)[t]:.0f}°", (0.69, 0.2))
    # c · contacto, plano sagital
    t = s["c"]
    ax, p = skeleton_panel(2, t, "c  Ball contact")
    ext = p[skn] + 0.4 * (p[skn] - p[shi]) / np.linalg.norm(p[skn] - p[shi])
    dashed(ax, p[skn], ext)
    mark_angle(ax, p[skn], ext - p[skn], p[san] - p[skn], 0.14, SUPPORT,
               f"support-knee\nflexion\n{knee_flexion(seq, sup)[t]:.0f}°", (0.0, 0.2))
    up = p[0] + np.array([0, 0.75])
    dashed(ax, p[0], up)
    mark_angle(ax, p[0], up - p[0], p[8] - p[0], 0.45, purple,
               f"trunk\nsagittal lean\n{trunk_lean(seq)[t, 0]:+.0f}°".replace("-", "−"), (0.0, 0.86))
    # d · contacto, plano frontal
    ax, p = skeleton_panel(3, t, "d  Contact, frontal view", view=front, xlim=(-1.0, 1.1))
    up = p[0] + np.array([0, 0.75])
    dashed(ax, p[0], up)
    lat = trunk_lean(seq)[t, 1] * (1 if sup == "r" else -1)
    mark_angle(ax, p[0], up - p[0], p[8] - p[0], 0.45, purple,
               f"trunk lateral\nlean\n{lat:+.0f}°".replace("-", "−"), (0.58, 0.86))
    # e · diagrama de cuerpo libre de la pierna de golpeo, 50 ms antes del contacto
    ax = fig.add_subplot(bottom[0, 0])
    mm = swing_leg_moments(seq, s["fps"], side, 75.0, "male", cutoff_hz=12)
    t = s["c"] - int(round(0.05 * s["fps"]))
    p = sag(s, x17[t])
    for a, b in BONES:
        if (a, b) not in LEG[side]:
            ax.plot(*p[[a, b]].T, color="#cbd5e1", lw=1.5, solid_capstyle="round", zorder=1)
    ax.add_patch(Circle(p[10] + 0.35 * (p[9] - p[10]), 0.085, fc="white", ec="#cbd5e1", lw=1.2, zorder=1))
    for a, b, w in ((hi, kn, 11), (kn, an, 8)):
        ax.plot(*p[[a, b]].T, color=KICK, lw=w, alpha=0.3, solid_capstyle="round", zorder=2)
        ax.plot(*p[[a, b]].T, color=KICK, lw=1.6, zorder=3)
    coms = (p[hi] + 0.4095 * (p[kn] - p[hi]), p[kn] + 0.4459 * (p[an] - p[kn]), p[an])
    for cpt in coms:
        ax.scatter(*cpt, s=26, color=INK, zorder=6, lw=0)
        ax.annotate("", xy=cpt + [0, -0.15], xytext=cpt, arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.1,
                                                                          mutation_scale=8), zorder=6)
    F = mm["F_hip"][t]
    f2 = np.array([F @ s["e1"], F[2]])
    f2 = 0.3 * f2 / (np.linalg.norm(f2) + 1e-9)
    ax.annotate("", xy=p[hi] + f2, xytext=p[hi], arrowprops=dict(arrowstyle="-|>", color=EST, lw=1.8), zorder=7)
    ax.text(*(p[hi] + 1.12 * f2 + [0.02, 0]), r"$\mathbf{F}_{hip}$", fontsize=8, color=EST, va="center")
    sh, sk = np.sign(mm["cadera_momento"][t]), np.sign(mm["rodilla_momento"][t])
    moment_arrow(ax, p[hi], 0.17, 135 - 45 * sh, 135 + 45 * sh, "#d03b3b")
    ax.text(*(p[hi] + [-0.28, 0.17]), r"$M_{hip}$", fontsize=8, color="#d03b3b", ha="right", va="center")
    moment_arrow(ax, p[kn], 0.14, -45 * sk, 45 * sk, "#d03b3b")
    ax.text(*(p[kn] + [0.2, 0.0]), r"$M_{knee}$", fontsize=8, color="#d03b3b", ha="left", va="center")
    keys = [("●", INK, "segment centre of mass (de Leva 1996)"), ("↓", INK, "segment weight, m·g"),
            ("→", EST, "joint reaction force"), ("↺", "#d03b3b", "net joint moment")]
    for i, (sym, col, lab) in enumerate(keys):
        ax.text(0.0, 0.2 - i * 0.065, sym, transform=ax.transAxes, fontsize=7, color=col, ha="center", va="center")
        ax.text(0.04, 0.2 - i * 0.065, lab, transform=ax.transAxes, fontsize=6.3, color=rep.INK2, va="center")
    ax.text(1.0, 0.98, "Newton–Euler, open chain:\nno force plate needed", transform=ax.transAxes, ha="right",
            va="top", fontsize=6.3, color=rep.INK2)
    ax.set_xlim(p[hi][0] - 0.85, p[hi][0] + 0.75), ax.set_ylim(-0.5, 1.75)
    clean(ax)
    ax.set_title("e  Swing-leg free-body diagram (−50 ms)".replace("-50", "−50"), loc="left", fontsize=8.3)
    # f · momentos netos: golpeo fuerte frente a lento
    right = bottom[0, 1].subgridspec(2, 1, hspace=0.12)
    axh = fig.add_subplot(right[0])
    axk = fig.add_subplot(right[1], sharex=axh)
    for sc, ls, lab in ((s, "-", "full kick (10_01)"), (slow, "--", "slow kick (10_04)")):
        m_ = swing_leg_moments(sc["seq"], sc["fps"], sc["side"], 75.0, "male", cutoff_hz=12)
        tt = (np.arange(len(sc["seq"])) - sc["c"]) / sc["fps"] * 1000
        sel = (tt >= -350) & (tt <= 20)
        hip_m, knee_m = m_["cadera_momento"] / 75, m_["rodilla_momento"] / 75
        axh.plot(tt[sel], hip_m[sel], ls=ls, color="#d03b3b", lw=1.6, label=lab)
        axk.plot(tt[sel], knee_m[sel], ls=ls, color=SUPPORT, lw=1.6, label=lab)
        if sc is s:
            b, c = sc["b"], sc["c"]
            f0 = c - int(round(0.1 * sc["fps"]))
            ih = b + int(np.nanargmax(hip_m[b:c + 1]))
            ike = b + int(np.nanargmax(knee_m[b:c + 1]))
            ikf = f0 + int(np.nanargmin(knee_m[f0:c + 1]))
            for a_, i, y, lab_, off, ha, va in ((axh, ih, hip_m, "peak hip flexor", (6, 3), "left", "bottom"),
                                                (axk, ike, knee_m, "peak knee extensor", (-6, 3), "right", "bottom"),
                                                (axk, ikf, knee_m, "peak knee flexor", (-7, 0), "right", "center")):
                a_.scatter(tt[i], y[i], s=22, color=INK, zorder=5)
                a_.annotate(lab_, (tt[i], y[i]), xytext=off, textcoords="offset points", fontsize=6.3, color=INK,
                            ha=ha, va=va)
    tb = (s["b"] - s["c"]) / s["fps"] * 1000
    for a_ in (axh, axk):
        a_.axvspan(tb, 0, color=GRID, alpha=0.6, zorder=0, lw=0)
        a_.axhline(0, color=MUTED, lw=0.8)
        a_.tick_params(labelsize=7)
    axk.axvspan(-100, 0, color="#fde2d6", alpha=0.8, zorder=0, lw=0)
    axh.text(tb + 4, 0.04, "backswing → contact", transform=axh.get_xaxis_transform(), fontsize=6.3,
             color=rep.INK2)
    axk.set_ylim(top=0.62)
    axh.set_ylim(top=1.3)
    axk.text(-97, 0.4, "last\n100 ms", transform=axk.get_xaxis_transform(), fontsize=6.3, color=rep.INK2)
    axh.set_ylabel("Hip (N·m/kg)\n+ flexor / − extensor", fontsize=7)
    axk.set_ylabel("Knee (N·m/kg)\n+ extensor / − flexor", fontsize=7)
    plt.setp(axh.get_xticklabels(), visible=False)
    axk.set_xlabel("Time relative to contact (ms)", fontsize=7.5)
    axk.legend(fontsize=6.3, loc="lower left", frameon=False)
    axh.set_title("f  Net joint moments, kicking leg", loc="left", fontsize=8.3)
    fig.subplots_adjust(left=0.03, right=0.985, top=0.95, bottom=0.07)
    save_fig(fig, "fig2_model.png")
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ figura 3
def fig_recon(s, bank):
    from golpeo.elevador import Lifter
    lifter = Lifter()
    fps = 25
    xr = resample(s["x17"], s["fps"], fps)
    gt8 = to_canonical(xr)
    c = int(round(s["c"] / s["fps"] * fps))
    est, inputs = {}, {}
    for cam, az in (("lateral", 90), ("frontal", 0)):
        rng = np.random.default_rng(7 + az)
        uv, conf = film(xr, az, ELEVACION, 80, 0, 0, rng)
        uv = uv + bank.sample(len(uv), fps, 80, rng)
        inputs[cam] = uv
        e17 = lifter.lift_person(uv, conf)
        e17 = e17 * thigh(gt8) / thigh(to_canonical(e17))
        al = rigid_align(np.concatenate([to_canonical(e17), e17], 1), np.concatenate([gt8, xr], 1))[:, 8:]
        est[cam] = al - al[:, :1] + xr[:, :1]                  # pelvis superpuesta para comparar la postura
    cols = [c - 8, c - 5, c - 3, c, c + 3]
    fig = plt.figure(figsize=(7.4, 7.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.6, 1], hspace=0.2)
    top = gs[0].subgridspec(4, 5, hspace=0.04, wspace=0.03)
    rows = ["Motion\ncapture\n(truth)", "TV input\nlateral\n80 px", "3D from\nlateral\ncamera",
            "3D from\nfrontal\ncamera"]
    for j, t in enumerate(cols):
        for i in range(4):
            ax = fig.add_subplot(top[i, j])
            if i == 1:
                thumb(ax, pixel_canvas(inputs["lateral"][t], 80), edge=GRID)
            else:
                p_gt = sag(s, xr[t])
                if i == 0:
                    draw_skel(ax, p_gt, s["side"], lw=1.8)
                else:
                    draw_skel(ax, p_gt, s["side"], color="#c4ccd6", kick="#f8c9b3", lw=3.2, head=False, dots=False)
                    draw_skel(ax, sag(s, est["lateral" if i == 2 else "frontal"][t]), s["side"], color=EST,
                              kick="#123f7a", lw=1.4)
                ground(ax)
                ax.set_xlim(-1.2, 1.0), ax.set_ylim(-0.1, 1.95)
                clean(ax)
            if i == 0:
                ax.set_title(f"{(t - c) * 1000 / fps:+.0f} ms".replace("-", "−"), fontsize=7.5)
            if j == 0:
                ax.text(-0.06, 0.5, rows[i], transform=ax.transAxes, ha="right", va="center", fontsize=7,
                        color=INK, linespacing=1.15)
    fig.text(0.13, 0.432, "grey/orange: motion capture   ·   blue: 3D reconstructed from one TV camera "
             "(80 px, 25 fps, broadcast 2D noise)", fontsize=6.5, color=rep.INK2)
    fig.text(0.012, 0.975, "a", fontsize=10, weight="bold")
    ond = np.load(RES / "ondas_movi.npz")
    tms = ond["t"] * 1000
    bottom = gs[1].subgridspec(2, 2, hspace=0.5, wspace=0.2)
    specs = [("lateral", "knee", "Lateral camera · kicking-knee flexion (°)"),
             ("lateral", "hip", "Lateral camera · kicking-hip flexion (°)"),
             ("frontal", "knee", "Frontal camera · kicking-knee flexion (°)"),
             ("frontal", "hip", "Frontal camera · kicking-hip flexion (°)")]
    n = len(ond["lab_lateral_knee"])
    spm_rows = []
    for k, (cam, ang, title) in enumerate(specs):
        ax = fig.add_subplot(bottom[k // 2, k % 2])
        r = paired_snpm(ond[f"lab_{cam}_{ang}"], ond[f"est_{cam}_{ang}"])
        step = tms[1] - tms[0]
        for i, j, p in r["clusters"]:
            ax.axvspan(tms[i] - step / 2, tms[j] + step / 2, color="#d03b3b", alpha=0.1, lw=0)
            spm_rows.append(dict(curve=f"{cam}_{ang}", start_ms=tms[i], end_ms=tms[j], p=p, t_star=r["t_star"]))
        for who, col, lab in (("lab", INK, f"lab (mean ± SD, n = {n})"), ("est", EST, "from TV (mean ± SD)")):
            y = ond[f"{who}_{cam}_{ang}"]
            m, sd = np.nanmean(y, 0), np.nanstd(y, 0)
            ax.fill_between(tms, m - sd, m + sd, color=col, alpha=0.13, lw=0)
            ax.plot(tms, m, color=col, lw=1.8, label=lab)
        ax.axvline(0, color=MUTED, lw=0.8)
        ax.set_title(title, loc="left", fontsize=7.5)
        ax.tick_params(labelsize=7)
        if k >= 2:
            ax.set_xlabel("Time relative to contact (ms)", fontsize=7)
    handles = [plt.Line2D([], [], color=INK, lw=1.8, label=f"lab (mean ± SD, n = {n})"),
               plt.Line2D([], [], color=EST, lw=1.8, label="from TV (mean ± SD)"),
               Rectangle((0, 0), 1, 1, color="#d03b3b", alpha=0.15, lw=0, label="SPM difference, p < 0.05")]
    fig.legend(handles=handles, loc="lower center", ncol=3, fontsize=6.8, frameon=False, bbox_to_anchor=(0.55, 0.0))
    pd.DataFrame(spm_rows).round(4).to_csv(RES / "paper" / "table10_spm.csv", index=False)
    fig.text(0.012, 0.365, "b", fontsize=10, weight="bold")
    fig.subplots_adjust(left=0.13, right=0.98, top=0.965, bottom=0.085)
    save_fig(fig, "fig3_recon.png")
    plt.close(fig)


# ------------------------------------------------------------------------------------------------ figura S3
def fig_bland():
    df = pd.read_csv(RES / "sensibilidad.csv")
    sub = rep.subject_level(df[(df.dataset == "movi") & (df.tipo == "postura") & df.vista.isin((45, 90, 135))
                               & np.logical_and.reduce([df[k] == v for k, v in rep.TYPICAL.items()])])
    fig, axes = plt.subplots(2, 3, figsize=(7.4, 4.8))
    for ax, k in zip(axes.flat, FEATURE_NAMES):
        g = sub[sub.rasgo == k]
        for i, (v, gg) in enumerate(g.groupby("vista")):
            mean = (gg.referencia + gg.estimado) / 2
            ax.scatter(mean, gg.estimado - gg.referencia, s=8, alpha=0.55, color=rep.SERIES[i + 1],
                       marker=rep.MARKERS[i], label=rep.VIEWS[v], lw=0)
        a = agreement(g.referencia.to_numpy(), g.estimado.to_numpy())
        for y, ls in ((a["bias"], "-"), (a["loa_low"], "--"), (a["loa_high"], "--")):
            ax.axhline(y, color=INK, lw=1, ls=ls)
        txt = f"bias {a['bias']:+.1f}°\n95% LoA [{a['loa_low']:.0f}, {a['loa_high']:.0f}]°".replace("-", "−")
        ax.text(0.98, 0.97, txt, transform=ax.transAxes, ha="right", va="top", fontsize=6.3, color=INK,
                bbox=dict(fc="white", ec="none", alpha=0.85, pad=1.5))
        ax.set_title(rep.NAMES[k].replace("\n", " "), loc="left", fontsize=7.8)
        ax.tick_params(labelsize=7)
    for ax in axes[1]:
        ax.set_xlabel("Mean of lab and video (°)", fontsize=7)
    for ax in axes[:, 0]:
        ax.set_ylabel("Video − lab (°)", fontsize=7)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, title="camera view", loc="lower center", ncol=3, fontsize=7, title_fontsize=7,
               frameon=False, bbox_to_anchor=(0.5, 0.0))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    save_fig(fig, "figS3_bland.png")
    plt.close(fig)


def main():
    bank = ResidualBank.from_frame(pd.read_csv(RES / "error2d_3dsp.csv"))
    s = scene("10_01")
    fig_design(s, bank)
    fig_model(s, scene("10_04"))
    fig_recon(s, bank)
    fig_bland()


if __name__ == "__main__":
    main()
