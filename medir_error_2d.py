"""Error 2D real de RTMW sobre disparos de retransmisión (3DSP, Premier League vía SoccerNet).

Protocolo: top-down con la caja de la persona conocida (extensión de la anotación + 20 % de margen),
como en la evaluación estándar de COCO. Se mide a resolución original y reducida (75 % y 50 %).
Limitación: la anotación manual sobre recortes pequeños tiene su propio error, así que lo medido
es una cota superior del error del detector.

Uso:  python medir_error_2d.py [paso]   → resultados/error2d_3dsp.csv, modelo_ruido.json, fig5_error2d_vs_altura.png
      paso = 1 usa los 200 disparos (unos 47 min en CPU, ~5 min en GPU); paso = 2, 1 de cada 2.
Guarda también el residuo (dx, dy) de cada articulación, que usa el ruido "residuos reales" del
experimento de sensibilidad (conserva la estructura temporal y los fallos groseros del detector).
"""
import json
import sys
import time
from pathlib import Path

import cv2
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from golpeo.detector import rtmw
from golpeo.error2d import LIMB_JOINTS, coco_to_3dsp, fit_noise_model, player_height

ROOT = Path(__file__).parent
TRAIN = ROOT / "datos" / "3dsp" / "3dsp" / "train"
OUT = ROOT / "resultados"
ESCALAS = (1.0, 0.75, 0.5)
SWAP = {1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3, 11: 14, 12: 15, 13: 16, 14: 11, 15: 12, 16: 13}
LIMBS = list(LIMB_JOINTS)


def load_gt(path):
    kp = json.loads(path.read_text())["keypoint_2d"]
    return np.array([[kp[str(i)]["x"], kp[str(i)]["y"]] for i in range(17)], float)


def box(g, shape, margin=0.2):
    h = g[:, 1].max() - g[:, 1].min()
    lo, hi = g.min(axis=0) - margin * h, g.max(axis=0) + margin * h
    return [max(lo[0], 0), max(lo[1], 0), min(hi[0], shape[1] - 1), min(hi[1], shape[0] - 1)]


def main():
    OUT.mkdir(exist_ok=True)
    pose = rtmw()
    rows, t0 = [], time.time()
    paso = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    shots = sorted(p for p in TRAIN.iterdir() if p.is_dir())[::paso]
    for n, shot in enumerate(shots):
        for jf in sorted((shot / "posture").glob("*.json")):
            img = cv2.imread(str(shot / "img" / f"{jf.stem}.jpg"))
            if img is None:
                continue
            gt = load_gt(jf)
            h0 = player_height(gt)
            if h0 < 5:
                continue
            for s in ESCALAS:
                if s < 1 and n % 4:                   # escalas reducidas en 1 de cada 4 disparos
                    continue
                im = img if s == 1 else cv2.resize(img, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
                g = gt * s
                k, _ = pose(im, bboxes=[box(g, im.shape)])
                est = coco_to_3dsp(k[0])
                swapped = est.copy()
                for a, b in SWAP.items():
                    swapped[a] = est[b]
                d = est[LIMBS] - g[LIMBS]
                rows.append(dict(
                    disparo=shot.name, fotograma=jf.stem, escala=s, altura_px=h0 * s,
                    error_medio_px=float(np.linalg.norm(d, axis=1).mean()),
                    error_medio_cruzado_px=float(np.linalg.norm(swapped[LIMBS] - g[LIMBS], axis=1).mean()),
                    sigma_eje_px=float(np.sqrt((d ** 2).mean())),
                    **{f"err_j{j}": float(np.linalg.norm(est[j] - g[j])) for j in LIMBS},
                    **{f"{ax}_j{j}": float(est[j, i] - g[j, i]) for j in range(17) for i, ax in enumerate("xy")}))
        if n % 20 == 0:
            print(f"{n + 1}/{len(shots)} disparos ({time.time() - t0:.0f} s)", flush=True)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "error2d_3dsp.csv", index=False)

    print(f"\n{len(df)} medidas en {time.time() - t0:.0f} s")
    print(f"Convenio: error medio por nombre = {df.error_medio_px.mean():.2f} px, "
          f"con izq./dcha. cruzadas = {df.error_medio_cruzado_px.mean():.2f} px")
    df["bin"] = pd.cut(df.altura_px, [0, 20, 30, 40, 50, 60, 80, 120, 400])
    tabla = df.groupby("bin", observed=True).agg(n=("sigma_eje_px", "size"), altura=("altura_px", "median"),
                                                 sigma_px=("sigma_eje_px", lambda x: np.sqrt((x ** 2).mean())),
                                                 error_medio_px=("error_medio_px", "mean"))
    tabla["sigma_rel_%"] = 100 * tabla.sigma_px / tabla.altura
    print(tabla.round(2).to_string())
    frac, floor = fit_noise_model(tabla.altura.to_numpy(), tabla.sigma_px.to_numpy())
    (OUT / "modelo_ruido.json").write_text(json.dumps(
        {"sigma_frac": frac, "sigma_floor_px": floor, "n_medidas": len(df),
         "fuente": "RTMW-x sobre 3DSP (top-down con caja conocida)"}, indent=2))
    print(f"\nModelo ajustado: sigma = sqrt(({frac:.4f}·H)² + {floor:.2f}²) px por eje")

    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(df.altura_px, df.sigma_eje_px, s=3, alpha=0.2, label="fotogramas 3DSP")
    ax.plot(tabla.altura, tabla.sigma_px, "ko", label="RMS por tramo de altura")
    hh = np.linspace(df.altura_px.min(), df.altura_px.max(), 100)
    ax.plot(hh, np.hypot(frac * hh, floor), "r-", label=f"ajuste: √(({frac:.3f}·H)² + {floor:.2f}²)")
    ax.set_xlabel("Altura del jugador en la imagen (px)")
    ax.set_ylabel("Error 2D RMS por eje (px)")
    ax.set_ylim(0, np.percentile(df.sigma_eje_px, 99))
    ax.set_title("Error real de RTMW en disparos de retransmisión (3DSP)")
    ax.legend()
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(OUT / "fig5_error2d_vs_altura.png", dpi=150)


if __name__ == "__main__":
    main()
