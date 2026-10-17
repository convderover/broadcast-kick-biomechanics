"""Evaluación del elevador ajustado (ajustar_elevador.py) frente al oficial, siempre en sujetos no vistos.

  1. Cámara virtual (experimento_sensibilidad.py --rapido): para cada pliegue, sus sujetos de prueba de MoVi y
     los 7 golpeos de balón de CMU (nunca vistos en el entrenamiento). Ambos elevadores reciben la misma 2D,
     con residuos de la mitad de prueba del banco (disparos que el elevador ajustado no vio al entrenar).
  2. Vídeo real (validar_video_movi.py con la 2D ya detectada): sujetos de prueba de cada pliegue.
Salidas: resultados/ajuste_sensibilidad.csv, ajuste_video.csv, paper/fig10_finetune.png, paper/table8_finetune.csv.

Uso:  python evaluar_ajuste.py [--sin-simular]
"""
import subprocess
import sys
from pathlib import Path

import matplotlib
import numpy as np
import pandas as pd
import torch

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from golpeo.carga import LOAD_NAMES
from golpeo.cinematica import FEATURE_NAMES
from golpeo.figuras_es import save_fig
from golpeo.metricas import agreement
from informe_sensibilidad import INK2, MUTED, NAMES, OUT, RES, SERIES, koo_li

ROOT = Path(__file__).parent
CKPTS = {k: ROOT / "modelos" / "ajustado" / f"fold{k}.pth.tr" for k in (0, 1)}


def test_subjects(k):
    return torch.load(CKPTS[k], map_location="cpu", weights_only=False)["test_subjects"]


def run(cmd):
    print(">", " ".join(cmd), flush=True)
    subprocess.run([sys.executable, *cmd], check=True, cwd=ROOT)


def simulate():
    parts_s, parts_v = [], []
    for k in (0, 1):
        ids = ",".join(str(s) for s in test_subjects(k))
        run(["experimento_sensibilidad.py", "todo" if k == 0 else "movi", "--rapido", "--sujetos", ids,
             "--elevadores", f"oficial,{CKPTS[k]}", "--salida", f"_ajuste_sens_fold{k}",
             "--banco", "prueba"])
        parts_s.append(pd.read_csv(RES / f"_ajuste_sens_fold{k}.csv").assign(pliegue=k))
        run(["validar_video_movi.py", *[str(s) for s in test_subjects(k)], "--elevador", str(CKPTS[k]),
             "--salida", f"_ajuste_video_fold{k}"])
        parts_v.append(pd.read_csv(RES / f"_ajuste_video_fold{k}.csv").assign(pliegue=k, elevador="ajustado"))
    sens = pd.concat(parts_s, ignore_index=True)
    sens["elevador"] = np.where(sens.elevador == "oficial", "oficial", "ajustado")
    sens.to_csv(RES / "ajuste_sensibilidad.csv", index=False)
    pd.concat(parts_v, ignore_index=True).to_csv(RES / "ajuste_video.csv", index=False)


def subject_mean(df, keys):
    return df.groupby(keys, as_index=False)[["referencia", "estimado"]].mean()


def compare():
    sens = pd.read_csv(RES / "ajuste_sensibilidad.csv")
    rows = []
    conds = {
        "virtual, 80 px, replay views": (sens.altura_px == 80) & sens.vista.isin((45, 90, 135)),
        "virtual, 50 px, replay views": (sens.altura_px == 50) & sens.vista.isin((45, 90, 135)),
        "virtual, 80 px, all views": sens.altura_px == 80,
    }
    base = (sens.ruido == "residuos") & (sens.contacto == "conocido")
    for name, mask in conds.items():
        for ds in ("movi", "cmu"):
            g = sens[base & mask & (sens.dataset == ds)]
            g = subject_mean(g, ["ensayo", "vista", "elevador", "rasgo"])
            for (lev, k), gg in g.groupby(["elevador", "rasgo"]):
                rows.append(dict(condition=name, dataset=ds, elevador=lev, rasgo=k,
                                 **agreement(gg.referencia.to_numpy(), gg.estimado.to_numpy())))
    real_path = RES / "video_movi.csv"
    if (RES / "ajuste_video.csv").exists() and real_path.exists():
        tuned = pd.read_csv(RES / "ajuste_video.csv")
        off = pd.read_csv(real_path)
        off = off[off.sujeto.isin(tuned.sujeto.unique())].assign(elevador="oficial")
        both = pd.concat([off, tuned], ignore_index=True)
        both = both[both.contacto == "conocido"]
        for (nat, h, lev, k), g in both.groupby(["nativa", "altura_px", "elevador", "rasgo"]):
            if not nat and h not in (120, 80, 50):
                continue
            rows.append(dict(condition=f"real video, {'native' if nat else f'{h} px'}", dataset="movi", elevador=lev,
                             rasgo=k, **agreement(g.referencia.to_numpy(), g.estimado.to_numpy())))
    t = pd.DataFrame(rows)
    t["icc_class"] = t.icc21.map(koo_li)
    t.round(3).to_csv(OUT / "table8_finetune.csv", index=False)
    return t


def figure(t):
    panels = [("virtual, 80 px, replay views", "movi", "a  Virtual camera,\n    unseen MoVi participants"),
              ("virtual, 80 px, replay views", "cmu", "b  Virtual camera,\n    real ball kicks (CMU)"),
              ("real video, 80 px", "movi", "c  Real video downscaled\n    to 80 px (unseen)")]
    fig, axes = plt.subplots(1, 3, figsize=(7.4, 3.3), sharey=True)
    y = np.arange(len(FEATURE_NAMES))
    for ax, (cond, ds, title) in zip(axes, panels):
        sub = t[(t.condition == cond) & (t.dataset == ds)]
        for i, lev in enumerate(("oficial", "ajustado")):
            v = sub[sub.elevador == lev].set_index("rasgo").reindex(list(FEATURE_NAMES)).mae
            ax.barh(y + (i - 0.5) * 0.38, v, 0.36, color=SERIES[i],
                    label="official weights" if lev == "oficial" else "kick- & broadcast-adapted")
        ax.set_title(title, loc="left", fontsize=8.5)
        ax.set_xlabel("MAE (°)")
        ax.grid(axis="y", visible=False)
    axes[0].set_yticks(y, [NAMES[k].replace("\n", " ") for k in FEATURE_NAMES], fontsize=7.5)
    axes[0].invert_yaxis()
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="lower center", ncol=2, fontsize=7.5, bbox_to_anchor=(0.5, -0.02))
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    save_fig(fig, "fig10_finetune.png")
    plt.close(fig)


def main():
    if "--sin-simular" not in sys.argv:
        simulate()
    t = compare()
    figure(t)
    piv = t[t.rasgo.isin(FEATURE_NAMES)].pivot_table(index=["condition", "dataset", "rasgo"], columns="elevador",
                                                     values=["mae", "icc21"])
    pd.set_option("display.width", 220)
    print(piv.round(2).to_string())


if __name__ == "__main__":
    main()
