"""Figures and tables for the paper. Reads resultados/*.csv and writes every figure twice: English in
resultados/paper/ and Spanish in resultados/paper_es/ (golpeo.figuras_es). Figure 1 and the skeleton figures
come from figuras_articulo.py.

  fig2_contact.png          ankle-speed peak vs true ball contact (CMU)
  fig3_2d_error.png         2D detector error: broadcast (3DSP) vs lab video (MoVi), per joint
  fig4_sensitivity.png      MAE vs player height, per camera view (virtual broadcast camera, MoVi)
  figS1_sensitivity_cmu.png the same for the 7 real ball kicks (CMU)
  fig5_ablation.png         noise model, frame rate and contact-detection effects
  fig6_reliability.png      ICC(2,1) between subjects, feature × view (80 px, 25 fps)
  fig7_real_video.png       real-image validation (MoVi video) and simulation-vs-real check
  table2_2d_error.csv, table3_agreement.csv, table4_real_video.csv, table5_digital_twin.csv
  resumen_resultados.json   key numbers used by the text, the videos and the CV material

Usage:  python informe_sensibilidad.py
"""
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from golpeo.carga import LOAD_NAMES
from golpeo.cinematica import FEATURE_NAMES
from golpeo.figuras_es import OUT_ES, save_fig
from golpeo.metricas import agreement

ROOT = Path(__file__).parent
RES = ROOT / "resultados"
OUT = RES / "paper"
NAMES = {
    "rodilla_apoyo_flexion_contacto": "Support-knee flexion\nat contact",
    "rodilla_golpeo_flexion_max": "Kicking-knee\npeak flexion",
    "cadera_golpeo_extension_max": "Kicking-hip\npeak extension",
    "cadera_golpeo_rango": "Kicking-hip\nrange of motion",
    "tronco_inclinacion_sagital_contacto": "Trunk sagittal lean\nat contact",
    "tronco_inclinacion_lateral_contacto": "Trunk lateral lean\nat contact",
    "momento_cadera_flexor_max": "Peak hip-flexor\nmoment",
    "momento_rodilla_extensor_max": "Peak knee-extensor\nmoment",
    "momento_rodilla_flexor_max": "Peak knee-flexor\nmoment (pre-contact)",
}
VIEWS = {0: "frontal", 45: "45°", 90: "lateral", 135: "135°", 180: "rear"}
SERIES = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#6250d6", "#e34948"]
MARKERS = ["o", "s", "^", "D", "v"]
INK, INK2, MUTED, GRID = "#0b0b0b", "#52514e", "#898781", "#e1e0d9"
SEQ = matplotlib.colors.LinearSegmentedColormap.from_list(
    "blue", ["#cde2fb", "#86b6ef", "#3987e5", "#2a78d6", "#1c5cab", "#104281", "#0d366b"])
TYPICAL = dict(altura_px=80, fps=25, ruido="residuos", contacto="conocido")      # typical broadcast condition
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.edgecolor": "#c3c2b7",
                     "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2, "axes.titlesize": 9.5,
                     "axes.titlecolor": INK, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6,
                     "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False,
                     "figure.dpi": 150, "savefig.dpi": 300, "savefig.bbox": "tight", "lines.linewidth": 2})


def koo_li(icc):
    return "excellent" if icc >= 0.9 else "good" if icc >= 0.75 else "moderate" if icc >= 0.5 else "poor"


def agree_by(df, keys):
    rows = []
    for k, g in df.groupby(keys):
        rows.append({**dict(zip(keys, k if isinstance(k, tuple) else (k,))),
                     **agreement(g.referencia.to_numpy(), g.estimado.to_numpy())})
    return pd.DataFrame(rows)


def subject_level(df):
    """One value per kick and condition: averages the noise seeds (CMU has 3; MoVi 1)."""
    keys = [c for c in ("ensayo", "dataset", "fps", "vista", "altura_px", "ruido", "contacto", "rasgo", "tipo")
            if c in df.columns]
    return df.groupby(keys, as_index=False)[["referencia", "estimado"]].mean()


# ------------------------------------------------------------------------------------------------ fig 1
BONES = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (0, 7), (7, 8), (8, 9), (9, 10),
         (8, 11), (11, 12), (12, 13), (8, 14), (14, 15), (15, 16)]
KICK_SIDE = {(0, 1), (1, 2), (2, 3)}


def fig_contact():
    from golpeo.cinematica import contact_frame, kicking_side
    from golpeo.datos_cmu import load_cmu
    c = pd.read_csv(RES / "contacto_cmu.csv").dropna(subset=["contacto_balon"])
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.7), gridspec_kw=dict(width_ratios=[2.2, 1]))
    for i, row in c.reset_index().iterrows():
        tr = load_cmu(ROOT / "datos" / "cmu" / f"{row.ensayo}.c3d")
        side = kicking_side(tr.seq, tr.fps)
        v = np.linalg.norm(np.gradient(tr.seq[:, 7 if side == "r" else 6], axis=0), axis=1) * tr.fps
        t = (np.arange(len(v)) - row.contacto_balon) / tr.fps * 1000
        sel = (t > -300) & (t < 120)
        a.plot(t[sel], v[sel], color=SERIES[0], alpha=0.75, lw=1.4)
        a.plot((contact_frame(tr.seq, tr.fps, side) - row.contacto_balon) / tr.fps * 1000, v.max(), "o",
               color=SERIES[1], ms=5, zorder=5)
    a.axvline(0, color=INK, lw=1)
    a.text(4, a.get_ylim()[1] * 0.08, "ball contact\n(extrapolated)", color=INK2, fontsize=8)
    a.set_xlabel("Time relative to ball contact (ms)")
    a.set_ylabel("Kicking-ankle speed (m/s)")
    a.set_title("a  Ankle-speed peak (dots) precedes contact", loc="left")
    b.scatter(np.zeros(len(c)) + np.linspace(-0.08, 0.08, len(c)), c.diferencia_ms, color=SERIES[1], s=22, zorder=3)
    b.axhline(c.diferencia_ms.mean(), color=INK, lw=1)
    b.axhspan(-40, 0, color=GRID, alpha=0.5, zorder=0)
    b.text(0.14, -38, "one frame\nat 25 fps", fontsize=7.5, color=INK2, va="bottom")
    b.set_xlim(-0.3, 0.6)
    b.set_xticks([])
    b.set_ylim(-42, 2)
    b.set_ylabel("Ankle peak − contact (ms)")
    b.set_title(f"b  Offset: {c.diferencia_ms.mean():.1f} ms", loc="left")
    fig.tight_layout()
    save_fig(fig, "fig2_contact.png")
    plt.close(fig)
    return {"contact_offset_ms_mean": float(c.diferencia_ms.mean()), "contact_offset_ms_min": float(c.diferencia_ms.min()),
            "contact_offset_ms_max": float(c.diferencia_ms.max()), "n_ball_kicks": int(len(c)),
            "feature_change_max_deg": float(np.nanmax(np.abs(c[[f"{k}_dif" for k in FEATURE_NAMES]].to_numpy())))}


# ------------------------------------------------------------------------------------------------ fig 3
JOINT_GROUPS = {"hips": [1, 4], "knees": [2, 5], "ankles": [3, 6], "shoulders": [11, 14], "elbows": [12, 15],
                "wrists": [13, 16]}
JOINT_GROUPS_3DSP = {"hips": [1, 4], "knees": [2, 5], "ankles": [3, 6], "shoulders": [11, 14],
                     "elbows": [12, 15], "wrists": [13, 16]}       # by name, both orders hold the same pairs


def fig_2d_error():
    d = pd.read_csv(RES / "error2d_3dsp.csv")
    m = json.loads((RES / "modelo_ruido.json").read_text())
    d["bin"] = pd.cut(d.altura_px, [0, 30, 40, 50, 60, 80, 120, 400])
    tab = d.groupby("bin", observed=True).agg(n=("sigma_eje_px", "size"), height_px=("altura_px", "median"),
                                              sigma_px=("sigma_eje_px", lambda x: np.sqrt((x ** 2).mean())))
    tab["sigma_rel_pct"] = 100 * tab.sigma_px / tab.height_px
    tab.round(2).to_csv(OUT / "table2_2d_error.csv")
    fig, (a, b) = plt.subplots(1, 2, figsize=(7.2, 2.9))
    a.scatter(d.altura_px, 100 * d.sigma_eje_px / d.altura_px, s=2, alpha=0.12, color=SERIES[0], rasterized=True)
    a.plot(tab.height_px, tab.sigma_rel_pct, "o-", color=SERIES[0], label="broadcast (3DSP, RTMW-x)", ms=5)
    hh = np.linspace(15, 400, 200)
    a.plot(hh, 100 * np.hypot(m["sigma_frac"] * hh, m["sigma_floor_px"]) / hh, color=INK, lw=1, ls="--",
           label=f"fit σ = √(({m['sigma_frac']:.3f}H)² + {m['sigma_floor_px']:.1f}²)")
    out = {"sigma_frac": m["sigma_frac"], "sigma_floor_px": m["sigma_floor_px"], "n_2d_frames": int(len(d)),
           "n_2d_shots": int(d.disparo.nunique()),
           "lr_swap_px": [float(d.error_medio_px.mean()), float(d.error_medio_cruzado_px.mean())]}
    lab_path = RES / "video_movi_2d.csv"
    if lab_path.exists():
        v = pd.read_csv(lab_path)
        lab = v.groupby("altura_px").sigma_eje_px.apply(lambda x: np.sqrt((x ** 2).mean()))
        lab = lab.groupby(pd.cut(lab.index, [0, 60, 100, 160, 1000]), observed=True).mean()
        hv = v.groupby(pd.cut(v.altura_px, [0, 60, 100, 160, 1000]), observed=True).altura_px.median()
        a.plot(hv.to_numpy(), 100 * lab.to_numpy() / hv.to_numpy(), "s-", color=SERIES[1], ms=5,
               label="lab video (MoVi, RTMW-x)")
        out["lab_sigma_rel_pct"] = dict(zip([int(h) for h in hv], (100 * lab.to_numpy() / hv.to_numpy()).round(2).tolist()))
    a.set_xscale("log")
    a.set_xticks([20, 50, 100, 200, 400], ["20", "50", "100", "200", "400"])
    a.set_ylim(0, 30)
    a.set_xlabel("Player height in image, H (px)")
    a.set_ylabel("2D error, RMS per axis (% of H)")
    a.set_title("a  Detector error vs player size", loc="left")
    a.legend(fontsize=7, loc="upper right")
    s = d[d.escala == 1.0]
    vals = [100 * np.sqrt(np.mean(np.concatenate([(s[f"err_j{j}"] / s.altura_px) ** 2 for j in idx]) / 2))
            for idx in JOINT_GROUPS_3DSP.values()]
    b.barh(list(JOINT_GROUPS_3DSP), vals, color=SERIES[0], height=0.6)
    for y, val in enumerate(vals):
        b.text(val + 0.2, y, f"{val:.1f}", va="center", fontsize=8, color=INK2)
    b.invert_yaxis()
    b.set_xlabel("2D error, RMS per axis (% of H)")
    b.set_title("b  Broadcast, by joint", loc="left")
    b.grid(axis="y", visible=False)
    out["joint_error_pct"] = dict(zip(JOINT_GROUPS_3DSP, np.round(vals, 2).tolist()))
    fig.tight_layout()
    save_fig(fig, "fig3_2d_error.png")
    plt.close(fig)
    return out


# ------------------------------------------------------------------------------------------------ fig 4 / S1
def fig_sensitivity(df, dataset, name, title):
    sub = df[(df.dataset == dataset) & (df.fps == 25) & (df.ruido == "residuos") & (df.contacto == "conocido")
             & (df.tipo == "postura")]
    ac = agree_by(sub, ["rasgo", "vista", "altura_px"])
    fig, axes = plt.subplots(2, 3, figsize=(7.2, 4.4), sharex=True)
    for ax, k in zip(axes.flat, FEATURE_NAMES):
        for i, (v, g) in enumerate(ac[ac.rasgo == k].groupby("vista")):
            g = g.sort_values("altura_px")
            ax.plot(g.altura_px, g.mae, marker=MARKERS[i], ms=4, color=SERIES[i], lw=1.6, label=VIEWS[v])
        ax.set_xscale("log")
        ax.set_xticks([50, 80, 120, 200, 400], ["50", "80", "120", "200", "400"])
        ax.xaxis.set_minor_formatter(matplotlib.ticker.NullFormatter())
        ax.set_title(NAMES[k].replace("\n", " "), loc="left", fontsize=8.5)
        ax.set_ylim(0, None)
    for ax in axes[:, 0]:
        ax.set_ylabel("MAE (°)")
    for ax in axes[1]:
        ax.set_xlabel("Player height (px)")
    handles, labels = axes[0, 0].get_legend_handles_labels()
    fig.legend(handles, labels, title="camera view", loc="lower center", ncol=5, fontsize=7.5, title_fontsize=7.5,
               bbox_to_anchor=(0.5, -0.04))
    fig.suptitle(title, x=0.01, ha="left", fontsize=10, color=INK)
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    save_fig(fig, name)
    plt.close(fig)
    return ac


# ------------------------------------------------------------------------------------------------ fig 5
def fig_ablation(df):
    base = df[(df.tipo == "postura") & (df.altura_px == 80)]
    panels = [
        ("a  2D noise model (25 fps)", base[(base.fps == 25) & (base.contacto == "conocido")], "ruido",
         [("sin_ruido", "none"), ("gauss", "Gaussian i.i.d."), ("residuos", "broadcast residuals")]),
        ("b  Frame rate", base[(base.ruido == "residuos") & (base.contacto == "conocido")], "fps",
         [(50, "50 fps"), (25, "25 fps")]),
        ("c  Contact instant (25 fps)", base[(base.ruido == "residuos") & (base.fps == 25)], "contacto",
         [("conocido", "known"), ("auto", "automatic")]),
    ]
    fig, axes = plt.subplots(1, 3, figsize=(7.2, 3.3), sharey=True)
    out = {}
    y = np.arange(len(FEATURE_NAMES))
    for ax, (title, sub, key, levels) in zip(axes, panels):
        w = 0.8 / len(levels)
        for i, (lv, lab) in enumerate(levels):
            mae = sub[sub[key] == lv].assign(ae=lambda x: x.error.abs()).groupby("rasgo").ae.mean()
            vals = [mae.get(k, np.nan) for k in FEATURE_NAMES]
            ax.barh(y + (i - (len(levels) - 1) / 2) * w, vals, w * 0.9, color=SERIES[i], label=lab)
            out[f"{key}={lv}"] = dict(zip(FEATURE_NAMES, np.round(vals, 2).tolist()))
        ax.set_title(title, loc="left", fontsize=9)
        ax.set_xlabel("MAE (°)")
        ax.legend(fontsize=7, loc="upper center", bbox_to_anchor=(0.5, -0.2), frameon=False)
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(y, [NAMES[k].replace("\n", " ") for k in FEATURE_NAMES], fontsize=7.5)
    axes[0].invert_yaxis()
    fig.tight_layout(w_pad=1.5)
    save_fig(fig, "fig5_ablation.png")
    plt.close(fig)
    return out


# ------------------------------------------------------------------------------------------------ fig 6
def fig_reliability(df):
    sub = subject_level(df[(df.dataset == "movi") & (df.tipo == "postura")
                           & np.logical_and.reduce([df[k] == v for k, v in TYPICAL.items()])])
    ac = agree_by(sub, ["rasgo", "vista"])
    m = ac.pivot(index="rasgo", columns="vista", values="icc21").loc[list(FEATURE_NAMES)]
    fig, ax = plt.subplots(figsize=(4.6, 3.0))
    im = ax.imshow(m.clip(lower=0).to_numpy(), cmap=SEQ, vmin=0, vmax=1, aspect="auto")
    for i in range(m.shape[0]):
        for j in range(m.shape[1]):
            val = m.iat[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", fontsize=8,
                    color="white" if val > 0.55 else INK)
    ax.set_xticks(range(m.shape[1]), [VIEWS[v] for v in m.columns])
    ax.set_yticks(range(m.shape[0]), [NAMES[k].replace("\n", " ") for k in m.index], fontsize=7.5)
    ax.grid(False)
    cb = fig.colorbar(im, ax=ax, shrink=0.85)
    cb.set_label("ICC(2,1)", fontsize=7)
    ax.set_title(f"Agreement between participants (MoVi, n = {sub.ensayo.nunique()}), 80 px, 25 fps",
                 loc="left", fontsize=9)
    fig.tight_layout()
    save_fig(fig, "fig6_reliability.png")
    plt.close(fig)
    return ac


# ------------------------------------------------------------------------------------------------ tabla 3
def bootstrap_ci(g, n_boot=1000, seed=0):
    """IC 95 % del MAE y del ICC remuestreando golpeos (todas sus vistas juntas), no filas."""
    rng = np.random.default_rng(seed)
    groups = {e: gg for e, gg in g.groupby("ensayo")}
    keys = list(groups)
    maes, iccs = [], []
    for _ in range(n_boot):
        s = pd.concat([groups[keys[i]] for i in rng.integers(0, len(keys), len(keys))])
        a = agreement(s.referencia.to_numpy(), s.estimado.to_numpy())
        maes.append(a["mae"]), iccs.append(a["icc21"])
    return np.nanpercentile(maes, [2.5, 97.5]), np.nanpercentile(iccs, [2.5, 97.5])


def table_agreement(df):
    rows = []
    for dataset, views in (("movi", (45, 90, 135)), ("movi", (0, 45, 90, 135, 180)), ("cmu", (45, 90, 135))):
        sub = subject_level(df[(df.dataset == dataset) & df.vista.isin(views)
                               & np.logical_and.reduce([df[k] == v for k, v in TYPICAL.items()])])
        for k in FEATURE_NAMES + LOAD_NAMES:
            g = sub[sub.rasgo == k]
            a = agreement(g.referencia.to_numpy(), g.estimado.to_numpy())
            (m_lo, m_hi), (i_lo, i_hi) = bootstrap_ci(g)
            rows.append(dict(dataset=dataset, views="replay (45–135°)" if len(views) == 3 else "all",
                             feature=NAMES[k].replace("\n", " "), key=k, unit="N·m/kg" if k in LOAD_NAMES else "deg",
                             gt_mean=g.referencia.mean(), gt_sd=g.groupby("ensayo").referencia.first().std(),
                             **a, mae_ci_low=m_lo, mae_ci_high=m_hi, icc_ci_low=i_lo, icc_ci_high=i_hi,
                             icc_class=koo_li(a["icc21"])))
    t = pd.DataFrame(rows)
    t.round(4).to_csv(OUT / "table3_agreement.csv", index=False)
    return t


# ------------------------------------------------------------------------------------------------ fig 7
def view_bin(az):
    return pd.cut(az, [-1, 30, 60, 120, 150, 181], labels=["frontal", "45°", "lateral", "135°", "rear"])


def fig_real_video():
    path = RES / "video_movi.csv"
    if not path.exists():
        return None, None
    v = pd.read_csv(path)
    v["height"] = np.where(v.nativa, "native", v.altura_px.astype(str))
    v["view"] = view_bin(v.vista_real)
    post = v[(v.tipo == "postura") & (v.contacto == "conocido")]
    rows = []
    for (k, h), g in post.groupby(["rasgo", "height"]):
        rows.append(dict(rasgo=k, height=h, **agreement(g.referencia.to_numpy(), g.estimado.to_numpy())))
    tab = pd.DataFrame(rows)
    tab.round(4).to_csv(OUT / "table4_real_video.csv", index=False)
    twin_path = RES / "gemelo_movi.csv"
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.9), gridspec_kw=dict(width_ratios=[1.35, 1]))
    a = axes[0]
    order = ["native", "120", "80", "50"]
    for i, k in enumerate(FEATURE_NAMES):
        g = tab[tab.rasgo == k].set_index("height").reindex(order)
        a.plot(range(4), g.mae, marker=MARKERS[i % 5] if i < 5 else "P", color=SERIES[i], ms=4, lw=1.5,
               label=NAMES[k].replace("\n", " "))
    a.set_xticks(range(4), ["native\n(~300 px)", "120 px", "80 px", "50 px"])
    a.set_ylabel("MAE vs motion capture (°)")
    a.set_ylim(0, None)
    recordings = post[["sujeto", "camara"]].drop_duplicates().shape[0]
    a.set_title(f"a  Real video: {recordings} recordings, {post.sujeto.nunique()} people", loc="left")
    a.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.2), ncol=2, frameon=False)
    twin = None
    if twin_path.exists():
        tw = pd.read_csv(twin_path)
        tw = tw[(tw.tipo == "postura") & (tw.contacto == "conocido")]
        merged = []
        for (k, cam, h, noise), g in tw.groupby(["rasgo", "camara", "altura_label", "ruido"]):
            r = post[(post.rasgo == k) & (post.camara == cam) & (post.height == h)]
            pair = g.merge(r[["sujeto", "error"]], on="sujeto", suffixes=("_sim", "_real"))
            merged.append(dict(rasgo=k, camara=cam, height=h, ruido=noise, mae_sim=pair.error_sim.abs().mean(),
                               mae_real=pair.error_real.abs().mean(), n=len(pair),
                               r_err=pair[["error_sim", "error_real"]].corr().iat[0, 1]))
        twin = pd.DataFrame(merged)
        twin.round(4).to_csv(OUT / "table5_digital_twin.csv", index=False)
        b = axes[1]
        lab = {"ninguno": "no 2D noise", "movi": "lab-video residuals", "3dsp": "broadcast residuals"}
        for i, (noise, g) in enumerate(twin.groupby("ruido")):
            r = np.corrcoef(g.mae_sim, g.mae_real)[0, 1]
            b.scatter(g.mae_sim, g.mae_real, s=14, color=SERIES[i], marker=MARKERS[i],
                      label=f"{lab.get(noise, noise)} (r = {r:.2f})", alpha=0.85)
        lim = max(twin.mae_sim.max(), twin.mae_real.max()) * 1.05
        b.plot([0, lim], [0, lim], color=MUTED, lw=1, ls="--")
        b.set_xlim(0, lim), b.set_ylim(0, lim)
        b.set_xlabel("MAE predicted by simulation (°)")
        b.set_ylabel("MAE on real video (°)")
        b.set_title("b  Digital twin of each recording", loc="left")
        b.legend(fontsize=6.5, loc="upper center", bbox_to_anchor=(0.5, -0.27), frameon=False)
    else:
        axes[1].axis("off")
    fig.tight_layout()
    save_fig(fig, "fig7_real_video.png")
    plt.close(fig)
    return tab, twin


def _calibrate_loso(train_est, train_ref, groups, test_est=None):
    """GT ≈ a + b·estimate, fitted leaving each group out (or on all, applied to `test_est`)."""
    if test_est is not None:
        b, a = np.polyfit(train_est, train_ref, 1)
        return a + b * test_est
    out = np.empty(len(train_est))
    for gname in np.unique(groups):
        tr = groups != gname
        b, a = np.polyfit(train_est[tr], train_ref[tr], 1)
        out[~tr] = a + b * train_est[~tr]
    return out


def fig_improvements(df):
    """Two cheap remedies evaluated on the typical broadcast condition (80 px, 25 fps, broadcast residuals):
    view-specific linear bias correction learnt in the lab (leave-one-subject-out), and late fusion of the
    replay angles a broadcast usually shows (mean of the per-view estimates)."""
    sub = subject_level(df[(df.tipo == "postura") & np.logical_and.reduce([df[k] == v for k, v in TYPICAL.items()])])
    movi, cmu = sub[sub.dataset == "movi"], sub[sub.dataset == "cmu"]
    rows = []

    def add(name, k, ref, est):
        a = agreement(np.asarray(ref), np.asarray(est))
        rows.append(dict(method=name, rasgo=k, mae=a["mae"], r=a["r"], icc21=a["icc21"], bias=a["bias"]))

    for k in FEATURE_NAMES:
        mk = movi[movi.rasgo == k]
        for v, label in ((90, "lateral"), (45, "45°")):
            g = mk[mk.vista == v]
            add(f"single view {label}", k, g.referencia, g.estimado)
            add(f"single view {label} + bias correction", k, g.referencia,
                _calibrate_loso(g.estimado.to_numpy(), g.referencia.to_numpy(), g.ensayo.to_numpy()))
        for views, label in (((45, 135), "2 replays (45°+135°)"), ((45, 90, 135), "3 replays (45°–135°)")):
            g = mk[mk.vista.isin(views)].groupby("ensayo")[["referencia", "estimado"]].mean().reset_index()
            add(f"{label}", k, g.referencia, g.estimado)
            add(f"{label} + bias correction", k, g.referencia,
                _calibrate_loso(g.estimado.to_numpy(), g.referencia.to_numpy(), g.ensayo.to_numpy()))
        # transfer to real ball kicks: calibration learnt on all MoVi subjects, applied to CMU (lateral)
        gm, gc = mk[mk.vista == 90], cmu[(cmu.rasgo == k) & (cmu.vista == 90)]
        add("CMU ball kicks, lateral", k, gc.referencia, gc.estimado)
        add("CMU ball kicks, lateral + MoVi calibration", k, gc.referencia,
            _calibrate_loso(gm.estimado.to_numpy(), gm.referencia.to_numpy(), None, gc.estimado.to_numpy()))
    t = pd.DataFrame(rows)
    t.round(4).to_csv(OUT / "table7_improvements.csv", index=False)
    methods = ["single view lateral", "single view lateral + bias correction", "3 replays (45°–135°)",
               "3 replays (45°–135°) + bias correction"]
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 2.9), sharey=True)
    y = np.arange(len(FEATURE_NAMES))
    for ax, metric, xlabel in ((axes[0], "mae", "MAE (°)"), (axes[1], "icc21", "ICC(2,1)")):
        w = 0.8 / len(methods)
        for i, m in enumerate(methods):
            vals = t[t.method == m].set_index("rasgo").reindex(list(FEATURE_NAMES))[metric]
            ax.barh(y + (i - 1.5) * w, vals, w * 0.9, color=SERIES[i], label=m)
        ax.set_xlabel(xlabel)
        ax.grid(axis="y", visible=False)
    axes[1].axvline(0.75, color=MUTED, ls="--", lw=1)
    axes[1].text(0.76, len(FEATURE_NAMES) - 0.6, "good", fontsize=7, color=INK2)
    axes[0].set_yticks(y, [NAMES[k].replace("\n", " ") for k in FEATURE_NAMES], fontsize=7.5)
    axes[0].invert_yaxis()
    axes[0].set_title("a  Error", loc="left")
    axes[1].set_title("b  Agreement between subjects", loc="left")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=7, bbox_to_anchor=(0.5, -0.08))
    fig.tight_layout(rect=(0, 0.08, 1, 1))
    save_fig(fig, "fig9_improvements.png")
    plt.close(fig)
    return t


STATUS = {"good": "#0ca30c", "moderate": "#fab219", "poor": "#d03b3b"}
LABELS = {
    "en": dict(title="What is measurable from broadcast video?", sub="ICC(2,1) against motion capture between players",
               cls={"good": "good", "moderate": "moderate", "poor": "poor"},
               ctx=["Real video,\nlarge player", "Simulated broadcast,\n1 replay (80 px)",
                    "Simulated broadcast,\n3 replays (80 px)", "Real video 80 px,\nadapted lifter"],
               loads="Kick Load Index (joint load)"),
    "es": dict(title="¿Qué se puede medir desde la tele?", sub="CCI(2,1) frente a captura óptica, entre jugadores",
               cls={"good": "bueno", "moderate": "moderado", "poor": "pobre"},
               ctx=["Vídeo real,\njugador grande", "Tele simulada,\n1 repetición (80 px)",
                    "Tele simulada,\n3 repeticiones (80 px)", "Vídeo real a 80 px,\nmodelo ajustado"],
               loads="Índice de carga articular (KLI)"),
}
NAMES_ES = {
    "rodilla_apoyo_flexion_contacto": "Flexión rodilla de apoyo", "rodilla_golpeo_flexion_max": "Flexión máx. rodilla de golpeo",
    "cadera_golpeo_extension_max": "Extensión máx. cadera (armado)", "cadera_golpeo_rango": "Rango de cadera de golpeo",
    "tronco_inclinacion_sagital_contacto": "Inclinación del tronco (sagital)",
    "tronco_inclinacion_lateral_contacto": "Inclinación del tronco (lateral)",
}


def fig_traffic_light(lang="en"):
    """Graphical summary: ICC class per feature and usage context (needs tables 4, 7 and, if present, 8)."""
    L = LABELS[lang]
    cols = []
    t4 = pd.read_csv(OUT / "table4_real_video.csv") if (OUT / "table4_real_video.csv").exists() else None
    cols.append(t4[t4.height == "native"].set_index("rasgo").icc21 if t4 is not None else None)
    t7 = pd.read_csv(OUT / "table7_improvements.csv")
    cols.append(t7[t7.method == "single view lateral"].set_index("rasgo").icc21)
    cols.append(t7[t7.method == "3 replays (45°–135°)"].set_index("rasgo").icc21)
    t8 = pd.read_csv(OUT / "table8_finetune.csv") if (OUT / "table8_finetune.csv").exists() else None
    cols.append(t8[(t8.condition == "real video, 80 px") & (t8.dataset == "movi")
                   & (t8.elevador == "ajustado")].set_index("rasgo").icc21 if t8 is not None else None)
    keep = [i for i, c in enumerate(cols) if c is not None]
    names = NAMES_ES if lang == "es" else {k: NAMES[k].replace("\n", " ") for k in FEATURE_NAMES}
    fig, ax = plt.subplots(figsize=(6.6, 3.5))
    for j, i in enumerate(keep):
        for r, k in enumerate(FEATURE_NAMES):
            v = float(cols[i].get(k, np.nan))
            cls = "good" if v >= 0.75 else "moderate" if v >= 0.5 else "poor"
            ax.add_patch(plt.Rectangle((j + 0.04, r + 0.06), 0.92, 0.88, color=STATUS[cls], alpha=0.9, lw=0))
            near = any(v < th <= round(v, 2) for th in (0.5, 0.75))   # p. ej. 0,747 no es «bueno»
            txt = f"{v:.3f}" if near else f"{v:.2f}".replace("-0.00", "0.00")
            ax.text(j + 0.5, r + 0.42, txt.replace(".", ",") if lang == "es" else txt, ha="center", va="center",
                    fontsize=9, color="white", weight="bold")
            ax.text(j + 0.5, r + 0.72, L["cls"][cls], ha="center", va="center", fontsize=6.5, color="white")
    ax.set_xlim(0, len(keep)), ax.set_ylim(len(FEATURE_NAMES), 0)
    ax.set_xticks(np.arange(len(keep)) + 0.5, [L["ctx"][i] for i in keep], fontsize=7.5)
    ax.xaxis.tick_top()
    ax.set_yticks(np.arange(len(FEATURE_NAMES)) + 0.5, [names[k] for k in FEATURE_NAMES], fontsize=8)
    ax.tick_params(length=0)
    ax.grid(False)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.set_title(f"{L['title']}\n", loc="left", fontsize=10.5, color=INK, weight="bold", pad=24)
    fig.text(0.01, 0.015, L["sub"] + ("  ·  Koo & Li: < 0.5 poor, 0.5–0.75 moderate, ≥ 0.75 good" if lang == "en" else
                                       "  ·  Koo y Li: < 0,5 pobre, 0,5–0,75 moderado, ≥ 0,75 bueno"),
             fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(OUT / ("fig0_graphical_abstract.png" if lang == "en" else "semaforo_es.png"))
    if lang == "es":
        OUT_ES.mkdir(parents=True, exist_ok=True)
        fig.savefig(OUT_ES / "fig0_graphical_abstract.png")
    plt.close(fig)


def fig_intensity(df):
    """Does the lifter's error (no 2D noise) grow with kick intensity? Error averaged over views and sizes."""
    from scipy import stats
    meta = pd.read_csv(RES / "ensayos.csv")
    sub = df[(df.ruido == "sin_ruido") & (df.fps == 25) & (df.contacto == "conocido") & (df.tipo == "postura")]
    err = sub.assign(ae=sub.error.abs()).groupby(["ensayo", "rasgo"]).ae.mean().unstack()
    err["mean_ae"] = err[list(FEATURE_NAMES)].mean(axis=1)
    err = err.join(meta.set_index("ensayo")[["dataset", "v_tobillo_max"]])
    m = err[err.dataset == "movi"]
    rho, p = stats.spearmanr(m.v_tobillo_max, m.mean_ae)
    out = {"spearman_rho": float(rho), "p": float(p),
           "per_feature_rho": {k: float(stats.spearmanr(m.v_tobillo_max, m[k])[0]) for k in FEATURE_NAMES},
           "mean_ae_movi": float(m.mean_ae.mean()), "mean_ae_cmu": float(err[err.dataset == "cmu"].mean_ae.mean())}
    fig, ax = plt.subplots(figsize=(3.6, 2.8))
    ax.scatter(m.v_tobillo_max, m.mean_ae, s=12, color=SERIES[0], label=f"MoVi air kicks (ρ = {rho:.2f})")
    c = err[err.dataset == "cmu"]
    ax.scatter(c.v_tobillo_max, c.mean_ae, s=26, marker="s", color=SERIES[1], label="CMU ball kicks")
    ax.set_xlabel("Peak kicking-ankle speed (m/s)")
    ax.set_ylabel("Mean abs. error, 6 features (°)")
    ax.set_title("Lifter error without 2D noise", loc="left")
    ax.legend(fontsize=7)
    fig.tight_layout()
    save_fig(fig, "figS2_intensity.png")
    plt.close(fig)
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    summary = {"contact": fig_contact(), "error2d": fig_2d_error()}
    df = pd.read_csv(RES / "sensibilidad.csv")
    summary["n_kicks"] = df.groupby("dataset").ensayo.nunique().to_dict()
    ac_m = fig_sensitivity(df, "movi", "fig4_sensitivity.png",
                           f"Virtual broadcast camera · MoVi kicks (n = {df[df.dataset == 'movi'].ensayo.nunique()}) · "
                           "25 fps · broadcast 2D residuals")
    fig_sensitivity(df, "cmu", "figS1_sensitivity_cmu.png",
                    f"Virtual broadcast camera · real ball kicks (CMU, n = {df[df.dataset == 'cmu'].ensayo.nunique()}) · "
                    "25 fps · broadcast 2D residuals")
    summary["ablation"] = fig_ablation(df)
    if (RES / "ensayos.csv").exists():
        summary["intensity"] = fig_intensity(df)
    fig_reliability(df)
    t3 = table_agreement(df)
    summary["agreement_typical"] = {
        f"{r.dataset}|{r.views}|{r.key}": {k: round(float(getattr(r, k)), 3) for k in
                                           ("mae", "bias", "loa_low", "loa_high", "icc21", "r", "calib_slope", "sdd")}
        for r in t3.itertuples()}
    imp = fig_improvements(df)
    summary["improvements"] = {m: g.set_index("rasgo")[["mae", "r", "icc21"]].round(3).to_dict(orient="index")
                               for m, g in imp.groupby("method")}
    best = ac_m.groupby("rasgo").mae.min()
    summary["best_case_mae"] = best.round(2).to_dict()
    tab, twin = fig_real_video()
    if tab is not None:
        summary["real_video_mae"] = tab.pivot(index="rasgo", columns="height", values="mae").round(2).to_dict()
        summary["real_video_icc"] = tab.pivot(index="rasgo", columns="height", values="icc21").round(3).to_dict()
    if twin is not None:
        summary["digital_twin_r"] = {n: float(np.corrcoef(g.mae_sim, g.mae_real)[0, 1]) for n, g in twin.groupby("ruido")}
    for lang in ("en", "es"):
        fig_traffic_light(lang)
    (RES / "resumen_resultados.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 200)
    print(t3[["dataset", "views", "key", "mae", "bias", "icc21", "r", "calib_slope", "icc_class"]].round(2).to_string())


if __name__ == "__main__":
    main()
