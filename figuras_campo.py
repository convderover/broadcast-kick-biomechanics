"""Figuras del ejemplo de campo (vídeos del autor), en inglés y en español.

  resultados/campo/opciones/*.png       opciones de fotograma con el esqueleto superpuesto y la pierna de golpeo
                                        coloreada por su carga articular instantánea (para elegir la del artículo)
  resultados/paper{,_es}/fig11_field.png       figura del artículo: secuencia, ángulos y momentos fuerte/suave
  resultados/paper{,_es}/figS9_field_views.png fuerte frente a suave por toma y nativa frente a 80 px

La carga se colorea respecto al propio jugador: 1 = el momento máximo de cadera (o de rodilla) en sus golpeos
fuertes. Desde vídeo los momentos absolutos salen inflados (apartado 3.5 del artículo), así que no es un
riesgo de lesión validado: indica dónde y cuándo se concentra la carga y cómo cambia entre golpeos.
Uso:  python figuras_campo.py   (después de campo_videos.py)
"""
import json
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.cm import ScalarMappable
from matplotlib.colors import LinearSegmentedColormap, Normalize

import informe_sensibilidad as rep                       # estilo común
from campo_videos import CACHE, OUT, VIDEOS, parse
from golpeo.cinematica import FEATURE_NAMES, hip_flexion, knee_flexion
from golpeo.figuras_es import localize, save_fig
from golpeo.h36m import coco_to_h36m, to_canonical

ROOT = Path(__file__).parent
OPC = OUT / "opciones"
LOAD_CMAP = LinearSegmentedColormap.from_list("carga", ["#1baf7a", "#f2c12e", "#eb6834", "#c0262d"])
BONES = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (0, 7), (7, 8), (8, 9), (9, 10),
         (8, 11), (11, 12), (12, 13), (8, 14), (14, 15), (15, 16)]
LEG = {"r": (1, 2, 3), "l": (4, 5, 6)}
VIEW_ORDER = ["lateral", "diagonal front", "diagonal behind", "front"]
SCALE = {}                 # carga máxima de cadera y rodilla en los golpeos fuertes del propio jugador (main)
CMU_HIP_RANGE = (1.0, 2.0)  # momento flexor máximo de cadera en los golpeos de balón de laboratorio (N·m/kg)


def load(name):
    d2 = np.load(CACHE / f"{name}_2d.npz")
    d3 = np.load(CACHE / f"{name}_3d.npz")
    return dict(uv=d3["uv"], h=float(d2["h_native"]), fps=float(d3["fps"]), side=str(d3["side"]), c=int(d3["contact"]),
                x17=d3["x17"], hip=d3["hip_moment"], knee=d3["knee_moment"], meta=parse(Path(name)))


def frame(name, i):
    cap = cv2.VideoCapture(str(VIDEOS / f"{name}.MOV"))
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(i))
    ok, img = cap.read()
    cap.release()
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def load_levels(d, i):
    """Carga relativa del muslo (momento de cadera) y de la pierna (momento de rodilla) en el fotograma i:
    1 = el valor máximo en los golpeos fuertes de este jugador."""
    return float(abs(d["hip"][i]) / SCALE["hip"]), float(abs(d["knee"][i]) / SCALE["knee"])


def key_frames(d):
    """Final del armado, pico flexor de cadera, contacto y final del golpeo (+100 ms)."""
    seq = to_canonical(d["x17"])
    c, fps = d["c"], d["fps"]
    w0 = max(c - int(round(0.3 * fps)), 0)
    b = w0 + int(np.nanargmin(hip_flexion(seq, d["side"])[w0:c + 1]))
    ph = b + int(np.nanargmax(d["hip"][b:c + 1]))
    ft = min(c + int(round(0.1 * fps)), len(seq) - 1)
    return {"end of backswing": b, "peak hip-flexor load": ph, "ball contact": c, "follow-through": ft}


def draw_overlay(ax, d, i, crop=1.7, labels=True, title=None):
    img = frame(d["meta"]["video"], i)
    uv = d["uv"][i]
    cx, cy = uv[0]
    half = crop * d["h"] / 2
    x0, y0 = int(max(cx - half, 0)), int(max(cy - half * 1.05, 0))
    x1, y1 = int(min(cx + half, img.shape[1])), int(min(cy + half * 0.95, img.shape[0]))
    ax.imshow(img[y0:y1, x0:x1], extent=(x0, x1, y1, y0), interpolation="bicubic")
    hi, kn, an = LEG[d["side"]]
    sup = LEG["l" if d["side"] == "r" else "r"]
    hip_l, knee_l = load_levels(d, i)
    lw = max(2.0, d["h"] / 60)
    for a, b in BONES:
        if (a, b) in ((hi, kn), (kn, an)) or (a == 0 and b == hi):
            continue
        col = "#9cc3e6" if a in sup or b in sup else "white"
        ax.plot(*uv[[a, b]].T, color="black", lw=lw + 1.6, solid_capstyle="round", alpha=0.6)
        ax.plot(*uv[[a, b]].T, color=col, lw=lw, solid_capstyle="round")
    ax.plot(*uv[[0, hi]].T, color="white", lw=lw, solid_capstyle="round")
    for (a, b), lev in (((hi, kn), hip_l), ((kn, an), knee_l)):
        ax.plot(*uv[[a, b]].T, color="black", lw=lw * 2.2 + 1.6, solid_capstyle="round", alpha=0.6)
        ax.plot(*uv[[a, b]].T, color=LOAD_CMAP(min(lev, 1.0)), lw=lw * 2.2, solid_capstyle="round")
    for j, lev in ((hi, hip_l), (kn, knee_l)):
        ax.scatter(*uv[j], s=(40 + 260 * min(lev, 1.2)) * (lw / 3) ** 2, color=LOAD_CMAP(min(lev, 1.0)),
                   edgecolor="black", lw=1, zorder=5)
    ax.scatter(*uv[[0, 2, 3, 5, 6, 11, 14]].T if d["side"] == "r" else uv[[0, 1, 3, 4, 6, 11, 14]].T, s=lw * 6,
               color="white", edgecolor="black", lw=0.6, zorder=4)
    if labels:
        h, k = d["hip"][i], d["knee"][i]
        ax.text(0.02, 0.03, f"hip {h:+.2f} N·m/kg\nknee {k:+.2f} N·m/kg", transform=ax.transAxes, fontsize=7,
                color="white", va="bottom", bbox=dict(fc="black", ec="none", alpha=0.55, pad=2))
    ax.set_xlim(x0, x1), ax.set_ylim(y1, y0)
    ax.set_xticks([]), ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    if title:
        ax.set_title(title, fontsize=8, loc="left")


def colorbar(fig, rect, label="Swing-leg joint load relative to this player's strongest kick"):
    cax = fig.add_axes(rect)
    cb = fig.colorbar(ScalarMappable(Normalize(0, 1), LOAD_CMAP), cax=cax, orientation="horizontal")
    cb.set_ticks([0, 0.5, 1], labels=["0", "0.5", "1 (max)"])
    cb.ax.tick_params(labelsize=6.5)
    cb.set_label(label, fontsize=7)


def _savefig(fig, path: Path):
    """Guarda; si el fichero está abierto en un visor (Windows lo bloquea), lo deja al lado con _nuevo."""
    try:
        fig.savefig(path, dpi=300)
    except OSError:
        alt = path.with_name(path.stem + "_nuevo" + path.suffix)
        fig.savefig(alt, dpi=300)
        print(f"  aviso: {path.name} está abierto en otro programa; se ha escrito {alt.name}")


def save_pair(fig, path_en: Path):
    path_en.parent.mkdir(parents=True, exist_ok=True)
    _savefig(fig, path_en)
    localize(fig)
    _savefig(fig, path_en.with_name(path_en.stem + "_es" + path_en.suffix))


def options(data):
    """Varias opciones de fotograma para elegir la del artículo."""
    OPC.mkdir(parents=True, exist_ok=True)
    for name, d in data.items():
        if d["meta"]["intensity"] != "strong":
            continue
        kf = key_frames(d)
        fig, axes = plt.subplots(1, 4, figsize=(7.4, 2.9))
        for ax, (lab, i) in zip(axes, kf.items()):
            t = (i - d["c"]) / d["fps"] * 1000
            draw_overlay(ax, d, i, title=lab + chr(10) + ms_label(t))
        fig.suptitle(f"Kick {d['meta']['order']} · {d['meta']['view']} · strong", fontsize=9, x=0.01, ha="left")
        colorbar(fig, [0.3, 0.06, 0.4, 0.03])
        fig.subplots_adjust(left=0.01, right=0.99, top=0.8, bottom=0.17, wspace=0.03)
        save_pair(fig, OPC / f"secuencia_{d['meta']['order']:02d}_{d['meta']['view'].replace(' ', '_')}.png")
        plt.close(fig)
        fig, ax = plt.subplots(figsize=(3.6, 3.9))
        i = kf["peak hip-flexor load"]
        draw_overlay(ax, d, i, crop=1.5, title=f"Kick {d['meta']['order']} · {d['meta']['view']} · peak hip-flexor load")
        colorbar(fig, [0.15, 0.08, 0.7, 0.03], label="Swing-leg joint load\nrelative to this player's strongest kick")
        fig.subplots_adjust(left=0.02, right=0.98, top=0.92, bottom=0.2)
        save_pair(fig, OPC / f"fotograma_{d['meta']['order']:02d}_{d['meta']['view'].replace(' ', '_')}.png")
        plt.close(fig)


def ms_label(t):
    return "0 ms" if round(t) == 0 else f"{t:+.0f} ms".replace("-", "−")


def fig_compare(data, picks):
    """Fuerte frente a suave en el mismo instante (pico de carga flexora de cadera), por toma."""
    fig, axes = plt.subplots(len(picks), 2, figsize=(5.6, 2.9 * len(picks)))
    for r, (view, pair) in enumerate(picks.items()):
        for c_, name in enumerate(pair):
            d = data[name]
            i = key_frames(d)["peak hip-flexor load"]
            draw_overlay(axes[r, c_], d, i, crop=1.5,
                         title=f"{view} · {d['meta']['intensity']} (kick {d['meta']['order']})")
    colorbar(fig, [0.2, 0.045, 0.6, 0.018])
    fig.subplots_adjust(left=0.01, right=0.99, top=0.95, bottom=0.12, hspace=0.18, wspace=0.03)
    save_fig(fig, "figS10_field_compare.png")
    save_pair(fig, OPC / "comparacion_fuerte_suave.png")
    plt.close(fig)


def video_field(d, path: Path, lang: str = "en", slow: int = 4):
    """Vídeo a cámara lenta (×1/slow) del golpeo con el esqueleto y la carga coloreada, de −0,5 a +0,3 s."""
    from golpeo.video import Mp4, figure_to_rgb
    c, fps = d["c"], d["fps"]
    frames = range(max(c - int(0.5 * fps), 0), min(c + int(0.3 * fps), len(d["uv"])))
    labels = {"en": ("Kick", "slow motion", "ms from ball contact"),
              "es": ("Golpeo", "cámara lenta", "ms respecto al contacto")}[lang]
    with Mp4(path, fps / slow) as v:
        for i in frames:
            fig = plt.figure(figsize=(5.4, 6.0), dpi=150)
            ax = fig.add_axes([0.02, 0.17, 0.96, 0.76])
            draw_overlay(ax, d, i, crop=1.6, labels=True)
            t = (i - c) / fps * 1000
            fig.text(0.03, 0.96, f"{labels[0]} {d['meta']['order']} · {d['meta']['view']} · {d['meta']['intensity']}"
                     f" · {labels[1]} ×1/{slow}", fontsize=9, va="top")
            fig.text(0.97, 0.96, f"{t:+.0f} {labels[2]}".replace("-", "−"), fontsize=9, va="top", ha="right")
            colorbar(fig, [0.15, 0.08, 0.7, 0.025])
            if lang == "es":
                localize(fig)
            v.write(figure_to_rgb(fig))
            plt.close(fig)


def aligned(d, series, t_ms):
    t = (np.arange(len(series)) - d["c"]) / d["fps"] * 1000
    return np.interp(t_ms, t, series, left=np.nan, right=np.nan)


def fig_field(data, main_video):
    d = data[main_video]
    fig = plt.figure(figsize=(7.4, 6.4))
    gs = fig.add_gridspec(2, 1, height_ratios=[1.05, 1], hspace=0.55)
    top = gs[0].subgridspec(1, 4, wspace=0.03)
    kf = key_frames(d)
    for k, (lab, i) in enumerate(kf.items()):
        ax = fig.add_subplot(top[0, k])
        t = (i - d["c"]) / d["fps"] * 1000
        draw_overlay(ax, d, i, labels=k == 1, title=lab + chr(10) + ms_label(t))
    fig.text(0.01, 0.975, "a", fontsize=10, weight="bold")
    colorbar(fig, [0.32, 0.535, 0.36, 0.014])
    bottom = gs[1].subgridspec(1, 3, wspace=0.42)
    t_ms = np.arange(-400, 201, 1000 / 60)
    lat = {n: x for n, x in data.items() if x["meta"]["view"] == "lateral"}
    specs = [("Kicking-knee flexion (°)", lambda x: knee_flexion(to_canonical(x["x17"]), x["side"])),
             ("Kicking-hip flexion (°)", lambda x: hip_flexion(to_canonical(x["x17"]), x["side"])),
             ("Kicking-ankle speed (m/s)", lambda x: np.linalg.norm(np.gradient(x["x17"][:, 3], axis=0), axis=1) * x["fps"])]
    for k, (title, fn) in enumerate(specs):
        ax = fig.add_subplot(bottom[0, k])
        for inten, col in (("strong", "#c0262d"), ("soft", rep.SERIES[0])):
            ys = [aligned(x, fn(x), t_ms) for x in lat.values() if x["meta"]["intensity"] == inten]
            for y in ys:
                ax.plot(t_ms, y, color=col, lw=0.8, alpha=0.35)
            ax.plot(t_ms, np.nanmean(ys, 0), color=col, lw=2, label=f"{inten} (n = {len(ys)})")
        ax.axvline(0, color=rep.MUTED, lw=0.8)
        ax.set_title(title, loc="left", fontsize=7.5)
        ax.set_xlabel("Time relative to contact (ms)", fontsize=7)
        ax.tick_params(labelsize=7)
        if k == 0:
            ax.legend(fontsize=6.5, frameon=False, loc="upper left")
    fig.text(0.01, 0.46, "b", fontsize=10, weight="bold")
    fig.subplots_adjust(left=0.07, right=0.99, top=0.93, bottom=0.08)
    save_fig(fig, "fig11_field.png")
    plt.close(fig)


def fig_views(df):
    metrics = [("peak_ankle_speed", "Peak kicking-ankle speed (m/s)"), ("cadera_golpeo_rango", "Kicking-hip range of motion (°)"),
               ("momento_cadera_flexor_max", "Peak hip-flexor moment (N·m/kg)"),
               ("rodilla_golpeo_flexion_max", "Kicking-knee peak flexion (°)"),
               ("cadera_golpeo_extension_max", "Kicking-hip peak extension (°)"),
               ("rodilla_apoyo_flexion_contacto", "Support-knee flexion at contact (°)")]
    fig, axes = plt.subplots(2, 3, figsize=(7.4, 4.8))
    x = {v: i for i, v in enumerate(VIEW_ORDER)}
    for ax, (key, title) in zip(axes.flat, metrics):
        for (inten, res), g in df.groupby(["intensity", "resolution"]):
            col = "#c0262d" if inten == "strong" else rep.SERIES[0]
            off = (-0.12 if inten == "strong" else 0.12) + (0.0 if res == "native" else 0.05)
            ax.scatter(g.view.map(x) + off, g[key], s=22, color=col if res == "native" else "white", edgecolor=col,
                       lw=1.2, label=f"{inten}, {res}", zorder=3)
        if key == "momento_cadera_flexor_max":
            ax.axhspan(*CMU_HIP_RANGE, color=rep.GRID, alpha=0.8, lw=0, zorder=0)
            ax.text(-0.45, np.mean(CMU_HIP_RANGE), "lab ball\nkicks", fontsize=6, color=rep.INK2, ha="left",
                    va="center")
        ax.set_xticks(range(len(VIEW_ORDER)), [v.replace("diagonal ", "diag." + chr(10)) for v in VIEW_ORDER], fontsize=6.5)
        ax.set_title(title, loc="left", fontsize=7.5)
        ax.tick_params(axis="y", labelsize=7)
        ax.grid(axis="x", visible=False)
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=4, fontsize=7, frameon=False)
    fig.tight_layout(rect=(0, 0.06, 1, 1))
    save_fig(fig, "figS9_field_views.png")
    plt.close(fig)


def main():
    names = sorted([p.stem for p in VIDEOS.glob("*.MOV")], key=lambda n: parse(Path(n))["order"])
    data = {n: load(n) for n in names}
    df = pd.read_csv(OUT / "campo_rasgos.csv")
    hips, knees = [], []
    for d in data.values():
        if d["meta"]["intensity"] == "strong":
            kf = key_frames(d)
            w = slice(kf["end of backswing"], d["c"] + 1)
            hips.append(np.nanmax(np.abs(d["hip"][w]))), knees.append(np.nanmax(np.abs(d["knee"][w])))
    SCALE.update(hip=float(np.max(hips)), knee=float(np.max(knees)))
    options(data)
    strong_lat = df[(df.view == "lateral") & (df.intensity == "strong") & (df.resolution == "native")]
    main_video = strong_lat.sort_values("peak_ankle_speed").video.iloc[-1]
    fig_field(data, main_video)
    fig_views(df)
    nat = df[df.resolution == "native"]
    picks = {}
    for view in ("lateral", "diagonal behind"):
        g = nat[nat.view == view]
        strong = g[g.intensity == "strong"].sort_values("peak_ankle_speed").video.iloc[-1]
        soft = g[g.intensity == "soft"].sort_values("peak_ankle_speed").video.iloc[0]
        picks[view] = (strong, soft)
    fig_compare(data, picks)
    vid = ROOT / "resultados" / "videos"
    video_field(data[main_video], vid / "07_golpeo_real_autor.mp4", "en")
    video_field(data[main_video], vid / "07_golpeo_real_autor_es.mp4", "es")
    print("figura principal con el vídeo", main_video)


if __name__ == "__main__":
    main()
