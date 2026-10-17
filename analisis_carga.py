"""Secondary analysis: can a joint-load ("joint suffering") score of the kicking leg be measured from broadcast
video, and what would it take to validate it as an injury predictor?

  1. Construct validity of the lab reference (inverse dynamics of the swing leg): does the load grow with
     kick intensity (peak ankle speed, MoVi n = 83; soft vs full kicks, CMU)?
  2. Measurement validity from video: agreement of the TV estimate with the lab reference (virtual camera with
     broadcast residuals; real MoVi video).
  3. Posture surrogate: a ridge model that predicts the load from the six posture features (leave-one-subject-
     out), trained on lab data and applied to TV-estimated postures.
  4. Feasibility of an injury study: number of injuries needed (Schoenfeld 1983) as a function of the
     reliability of the score (regression dilution: the measured score attenuates the true hazard ratio).

Outputs in resultados/paper/: fig8_joint_load.png, table6_joint_load.csv; numbers in resultados/resumen_carga.json.
Usage:  python analisis_carga.py
"""
import json
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
from scipy import stats

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from golpeo.carga import LOAD_NAMES
from golpeo.cinematica import FEATURE_NAMES
from golpeo.figuras_es import save_fig
from golpeo.metricas import agreement
from informe_sensibilidad import INK, INK2, MUTED, NAMES, OUT, RES, SERIES, TYPICAL, koo_li, subject_level

LOAD_SHORT = {"momento_cadera_flexor_max": "hip-flexor moment", "momento_rodilla_extensor_max": "knee-extensor moment",
              "momento_rodilla_flexor_max": "knee-flexor moment", "kli": "Kick Load Index"}
Z = stats.norm.ppf(0.975) + stats.norm.ppf(0.80)          # α = 0.05 bilateral, potencia 80 %
LALIGA_PLAYERS = 20 * 25                                   # 20 clubes × ~25 jugadores de primer equipo


def events_needed(hr_per_sd: float, reliability: float) -> float:
    """Schoenfeld (1983) para una covariable continua estandarizada, atenuada por la fiabilidad λ:
    log-HR por DE observada = √λ · log-HR por DE verdadera  →  D = Z² / (λ · ln(HR)²)."""
    return Z ** 2 / (reliability * np.log(hr_per_sd) ** 2)


def add_kli(df, ref_stats):
    """Kick Load Index: media de los z de los tres picos de carga (z con la media y DE de la referencia MoVi)."""
    wide = df.pivot_table(index=[c for c in df.columns if c not in ("rasgo", "tipo", "referencia", "estimado", "error")],
                          columns="rasgo", values=["referencia", "estimado"])
    out = []
    for col in ("referencia", "estimado"):
        z = [(wide[(col, k)] - ref_stats[k][0]) / ref_stats[k][1] for k in LOAD_NAMES]
        out.append(pd.concat(z, axis=1).mean(axis=1).rename(col))
    kli = pd.concat(out, axis=1).reset_index()
    kli["rasgo"], kli["tipo"] = "kli", "carga"
    kli["error"] = kli.estimado - kli.referencia
    return pd.concat([df, kli], ignore_index=True)


def ridge_loso(X, y, groups, alpha=1.0):
    """Predicción dejando fuera un sujeto: ridge con variables estandarizadas dentro de cada pliegue."""
    from sklearn.linear_model import Ridge
    pred = np.empty(len(y))
    for gname in np.unique(groups):
        tr, te = groups != gname, groups == gname
        mu, sd = X[tr].mean(0), X[tr].std(0) + 1e-9
        model = Ridge(alpha=alpha).fit((X[tr] - mu) / sd, y[tr])
        pred[te] = model.predict((X[te] - mu) / sd)
    return pred


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    meta = pd.read_csv(RES / "ensayos.csv")
    movi = meta[meta.dataset == "movi"]
    ref_stats = {k: (movi[k].mean(), movi[k].std()) for k in LOAD_NAMES}
    meta["kli"] = np.mean([(meta[k] - ref_stats[k][0]) / ref_stats[k][1] for k in LOAD_NAMES], axis=0)
    movi = meta[meta.dataset == "movi"]
    summary = {"ref_mean_sd": {k: [round(v[0], 3), round(v[1], 3)] for k, v in ref_stats.items()}}

    # 1. validez de constructo de la referencia de laboratorio
    construct = {}
    for k in LOAD_NAMES + ("kli",):
        rho, p = stats.spearmanr(movi.v_tobillo_max, movi[k])
        construct[k] = {"spearman_rho": float(rho), "p": float(p)}
    cmu = meta[meta.dataset == "cmu"].set_index("ensayo")
    summary["construct_movi"] = construct
    summary["cmu_loads"] = cmu[list(LOAD_NAMES) + ["kli", "v_tobillo_max"]].round(3).to_dict(orient="index")

    # 2. acuerdo desde vídeo (cámara virtual, condición típica de retransmisión; y vídeo real)
    sens = pd.read_csv(RES / "sensibilidad.csv")
    sens = sens[sens.tipo == "carga"]
    typical = subject_level(sens[np.logical_and.reduce([sens[k] == v for k, v in TYPICAL.items()])
                                 & sens.vista.isin((45, 90, 135))])
    typical = add_kli(typical, ref_stats)
    rows = []
    for (ds, k), g in typical.groupby(["dataset", "rasgo"]):
        a = agreement(g.referencia.to_numpy(), g.estimado.to_numpy())
        rows.append(dict(source=f"virtual camera ({ds}), 80 px, 25 fps, 45–135°", key=k, **a))
    real_path = RES / "video_movi.csv"
    real = None
    if real_path.exists():
        real = pd.read_csv(real_path)
        real = real[(real.tipo == "carga") & (real.contacto == "conocido")].drop(
            columns=["vista_real", "azimut_film", "elevacion", "distancia_m", "altura_nativa_px", "fps"], errors="ignore")
        real = add_kli(real, ref_stats)
        real["size"] = np.where(real.nativa, "native", real.altura_px.astype(str) + " px")   # la nativa varía por sujeto
        for (size, k), g in real.groupby(["size", "rasgo"]):
            if size not in ("native", "50 px", "80 px", "120 px"):
                continue
            a = agreement(g.referencia.to_numpy(), g.estimado.to_numpy())
            rows.append(dict(source=f"real video (MoVi), {size}", key=k, **a))

    # 3. sustituto postural: carga ← 6 rasgos de postura (entrenado en laboratorio, LOSO)
    X = movi[list(FEATURE_NAMES)].to_numpy(float)
    groups = movi.ensayo.to_numpy()
    surrogate = {}
    post = pd.read_csv(RES / "sensibilidad.csv")
    post = subject_level(post[(post.tipo == "postura") & (post.dataset == "movi")
                              & np.logical_and.reduce([post[k] == v for k, v in TYPICAL.items()])
                              & post.vista.isin((45, 90, 135))])
    tv = post.pivot_table(index=["ensayo", "vista"], columns="rasgo", values="estimado").reset_index()
    from sklearn.linear_model import Ridge
    for k in LOAD_NAMES + ("kli",):
        y = movi[k].to_numpy(float)
        pred = ridge_loso(X, y, groups)
        r2 = 1 - np.sum((y - pred) ** 2) / np.sum((y - y.mean()) ** 2)
        mu, sd = X.mean(0), X.std(0) + 1e-9
        model = Ridge(alpha=1.0).fit((X - mu) / sd, y)
        joined = tv.merge(movi[["ensayo", k]], on="ensayo")
        p_tv = model.predict((joined[list(FEATURE_NAMES)].to_numpy(float) - mu) / sd)
        a_tv = agreement(joined[k].to_numpy(), p_tv)
        surrogate[k] = {"r2_loso_lab": float(r2), "r_loso_lab": float(np.corrcoef(y, pred)[0, 1]),
                        "tv_icc": a_tv["icc21"], "tv_r": a_tv["r"], "tv_calib_slope": a_tv["calib_slope"]}
        rows.append(dict(source="posture surrogate from TV postures (MoVi, 80 px, 25 fps, 45–135°)", key=k, **a_tv))
    summary["surrogate"] = surrogate
    table = pd.DataFrame(rows)
    table["feature"] = table.key.map(LOAD_SHORT)
    table["icc_class"] = table.icc21.map(koo_li)
    table.round(3).to_csv(OUT / "table6_joint_load.csv", index=False)

    # 4. viabilidad de un estudio prospectivo de lesiones
    lam = np.linspace(0.02, 1.0, 300)
    best_tv = table[table.source.str.startswith("virtual camera (movi)")].set_index("key").calib_slope.clip(lower=0.02)
    best_sur = surrogate["kli"]["tv_calib_slope"]
    feas = {}
    for hr in (1.3, 1.5, 2.0):
        feas[str(hr)] = {"lab_events": float(events_needed(hr, 1.0)),
                         "tv_kli_events": float(events_needed(hr, max(best_tv.get("kli", 0.02), 0.02)))}
    summary["feasibility"] = feas
    summary["laliga_players"] = LALIGA_PLAYERS

    # figura
    fig, axes = plt.subplots(1, 3, figsize=(7.6, 2.9))
    a = axes[0]
    a.scatter(movi.v_tobillo_max, movi.momento_cadera_flexor_max, s=10, color=SERIES[0], alpha=0.8, label="MoVi (air kicks)")
    a.scatter(cmu.v_tobillo_max, cmu.momento_cadera_flexor_max, s=22, color=SERIES[1], marker="s", label="CMU (ball kicks)")
    rho = construct["momento_cadera_flexor_max"]["spearman_rho"]
    a.set_xlabel("Peak kicking-ankle speed (m/s)")
    a.set_ylabel("Peak hip-flexor moment (N·m/kg)")
    a.set_title(f"a  Lab reference (ρ = {rho:.2f})", loc="left")
    a.legend(fontsize=6.5, loc="upper left")
    b = axes[1]
    g = typical[(typical.dataset == "movi") & (typical.rasgo == "momento_cadera_flexor_max")]
    b.scatter(g.referencia, g.estimado, s=8, alpha=0.5, color=SERIES[0], label="virtual TV camera")
    if real is not None:
        r50 = real[(real.rasgo == "momento_cadera_flexor_max") & (real.altura_px == 80) & ~real.nativa]
        b.scatter(r50.referencia, r50.estimado, s=10, alpha=0.7, color=SERIES[1], marker="s", label="real video, 80 px")
    lim = np.nanpercentile(np.r_[g.referencia, g.estimado], 99) * 1.05
    b.plot([0, lim], [0, lim], color=MUTED, ls="--", lw=1)
    b.set_xlim(0, lim), b.set_ylim(0, lim)
    a_h = agreement(g.referencia.to_numpy(), g.estimado.to_numpy())
    b.set_title(f"b  From video: ICC = {a_h['icc21']:.2f}", loc="left")
    b.set_xlabel("Lab (N·m/kg)")
    b.set_ylabel("From 80-px video (N·m/kg)")
    b.legend(fontsize=6.5, loc="upper left", markerscale=1.6)
    c = axes[2]
    for i, hr in enumerate((1.3, 1.5, 2.0)):
        c.plot(lam, events_needed(hr, lam), color=SERIES[i], lw=1.8, label=f"HR = {hr} per SD")
        c.text(1.01, events_needed(hr, 1.0), f"HR {hr}", fontsize=6.5, color=INK2, va="center",
               )
    for rate, ls in ((0.05, ":"), (0.10, "--")):
        c.axhline(LALIGA_PLAYERS * rate, color=MUTED, ls=ls, lw=1)
        c.text(0.99, LALIGA_PLAYERS * rate * 1.08, f"1 LaLiga season, {rate:.2f} inj./player",
               ha="right", fontsize=6.5, color=INK2, transform=c.get_yaxis_transform())
    kli_tv = max(float(best_tv.get("kli", np.nan)), 0.02)
    for x, txt in ((kli_tv, "inverse\ndynamics\nfrom TV"), (best_sur, "posture\nsurrogate\nfrom TV")):
        c.axvline(x, color=INK, lw=0.9, ls="-" if x == kli_tv else "-.")
        c.text(x + 0.015, 1500, f"{txt}\nλ = {x:.2f}", fontsize=6, color=INK, va="top")
    c.set_yscale("log")
    c.set_ylim(10, 5000)
    c.set_xlabel("Reliability λ of the score")
    c.set_ylabel("Injuries needed (α 0.05, power 0.8)")
    c.set_title("c  Injury-study size", loc="left")
    c.set_xlim(0, 1.12)
    fig.tight_layout()
    save_fig(fig, "fig8_joint_load.png")
    plt.close(fig)
    summary["agreement"] = table[["source", "key", "mae", "bias", "icc21", "r", "calib_slope"]].round(3).to_dict(orient="records")
    (RES / "resumen_carga.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    pd.set_option("display.width", 200)
    print(table[["source", "key", "mae", "bias", "icc21", "r", "calib_slope"]].round(2).to_string())
    print(json.dumps({"construct": construct, "surrogate": surrogate, "feasibility": feas}, indent=1))


if __name__ == "__main__":
    main()
