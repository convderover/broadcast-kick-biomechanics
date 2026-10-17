"""Compara el contacto real (balón) con la aproximación del pico del tobillo en los golpeos de CMU,
y cuánto cambian los rasgos según el contacto usado.

Uso:  python comparar_contacto_cmu.py
Salida: resultados/contacto_cmu.csv y resumen por pantalla.
"""
from pathlib import Path

import numpy as np
import pandas as pd

from golpeo.cinematica import FEATURE_NAMES, contact_frame, kick_features, kicking_side
from golpeo.contacto import ball_contact
from golpeo.datos_cmu import load_cmu

ROOT = Path(__file__).parent
OUT = ROOT / "resultados"


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for path in sorted((ROOT / "datos" / "cmu").glob("10_0*.c3d")):
        trial = load_cmu(path)
        side = kicking_side(trial.seq, trial.fps)
        c_ankle = contact_frame(trial.seq, trial.fps, side)
        row = {"ensayo": path.stem, "lado": side, "fps": trial.fps, "contacto_tobillo": c_ankle}
        c_ball, v_ball = ball_contact(trial.ball, trial.fps) if trial.ball is not None else (None, None)
        row.update(contacto_balon=c_ball, velocidad_balon_ms=v_ball)
        f_ankle = kick_features(trial.seq, trial.fps)
        if c_ball is not None:
            row["diferencia_ms"] = (c_ankle - c_ball) / trial.fps * 1000
            f_ball = kick_features(trial.seq, trial.fps, contact=round(c_ball))
        for k in FEATURE_NAMES:
            row[f"{k}_tobillo"] = f_ankle[k]
            if c_ball is not None:
                row[f"{k}_balon"] = f_ball[k]
                row[f"{k}_dif"] = f_ankle[k] - f_ball[k]
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(OUT / "contacto_cmu.csv", index=False)

    pd.set_option("display.width", 160)
    print(df[["ensayo", "lado", "contacto_tobillo", "contacto_balon", "diferencia_ms", "velocidad_balon_ms"]]
          .round(1).to_string(index=False))
    with_ball = df.dropna(subset=["contacto_balon"])
    print(f"\nGolpeos con balón: {len(with_ball)} de {len(df)}")
    print(f"Pico del tobillo respecto al contacto real: media {with_ball['diferencia_ms'].mean():+.1f} ms, "
          f"rango [{with_ball['diferencia_ms'].min():+.1f}, {with_ball['diferencia_ms'].max():+.1f}] ms")
    print("\nCambio en cada rasgo al usar el pico del tobillo en vez del contacto real (grados):")
    for k in FEATURE_NAMES:
        d = with_ball[f"{k}_dif"]
        print(f"  {k:38s} media {d.mean():+6.2f}   |máx| {np.abs(d).max():5.2f}")


if __name__ == "__main__":
    main()
