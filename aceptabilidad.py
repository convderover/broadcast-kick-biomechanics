"""¿Para qué sirve cada variable medida desde la retransmisión? Criterios de aceptabilidad tomados de la literatura
(no ajustados a estos datos), uno por cada uso práctico:

  1. Comparar con normas de laboratorio (valor absoluto, solo ángulos): error absoluto medio ≤ 5° y sesgo
     equivalente a cero dentro de ±5° (prueba de equivalencia TOST, α = 0,05, con un valor por participante).
     5° es el umbral a partir del cual el error de la cinemática articular se considera preocupante (McGinley 2009).
  2. Ordenar jugadores (scouting, comparación entre jugadores): CCI(2,1) ≥ 0,75 («bueno», Koo y Li 2016) con el
     límite inferior de su IC 95 % ≥ 0,5 (bootstrap por participantes).
  3. Seguir a un jugador (detectar un cambio real): error aleatorio, DE de las diferencias, ≤ cambio mínimo
     relevante, 0,2 × DE entre jugadores de la referencia (Hopkins et al. 2009).
Los IC 95 % del CCI remuestrean participantes con todas sus filas (bootstrap_ci, como la tabla 3).

Condiciones: una cámara de retransmisión simulada (80 px, 25 fps, residuos reales, contacto conocido, vistas de
repetición 45–135°); tres repeticiones fusionadas con corrección de sesgo aprendida en laboratorio; y vídeo real
reducido a 80 px. Salida: resultados/paper/table9_acceptability.csv.

Uso:  python aceptabilidad.py
"""
import numpy as np
import pandas as pd
from scipy import stats

from golpeo.carga import LOAD_NAMES
from golpeo.cinematica import FEATURE_NAMES
from golpeo.metricas import agreement
from informe_sensibilidad import NAMES, OUT, RES, TYPICAL, _calibrate_loso, bootstrap_ci, subject_level

ANGLE_MARGIN = 5.0          # grados (McGinley et al. 2009)
SWC_FRACTION = 0.2          # cambio mínimo relevante = 0,2 DE entre jugadores (Hopkins et al. 2009)
ICC_GOOD, ICC_FLOOR = 0.75, 0.5


def tost(d: np.ndarray, margin: float, alpha: float = 0.05) -> dict:
    """Prueba de equivalencia de dos unilaterales (Schuirmann 1987) para la media de `d` dentro de ±margin."""
    d = np.asarray(d, float)
    d = d[np.isfinite(d)]
    n, m = len(d), d.mean()
    se = d.std(ddof=1) / np.sqrt(n)
    p_low = 1 - stats.t.cdf((m + margin) / se, n - 1)
    p_high = stats.t.cdf((m - margin) / se, n - 1)
    half = stats.t.ppf(1 - alpha, n - 1) * se
    return {"tost_p": float(max(p_low, p_high)), "bias_ci90_low": float(m - half), "bias_ci90_high": float(m + half)}


def evaluate(g: pd.DataFrame, key: str) -> dict:
    """g: filas con sujeto, referencia y estimado (una o varias por participante)."""
    a = agreement(g.referencia.to_numpy(), g.estimado.to_numpy())
    per_subject = g.assign(d=g.estimado - g.referencia).groupby("sujeto").d.mean()
    ref_sd = g.groupby("sujeto").referencia.mean().std(ddof=1)
    sd_d = (g.estimado - g.referencia).std(ddof=1)
    swc = SWC_FRACTION * ref_sd
    _, (lo, hi) = bootstrap_ci(g.assign(ensayo=g.sujeto))      # el mismo remuestreo que la tabla 3
    angle = key in FEATURE_NAMES
    t = tost(per_subject.to_numpy(), ANGLE_MARGIN) if angle else {"tost_p": np.nan, "bias_ci90_low": np.nan,
                                                                  "bias_ci90_high": np.nan}
    return dict(n_participants=int(per_subject.size), mae=a["mae"], bias=a["bias"], **t, icc21=a["icc21"],
                icc_ci_low=lo, icc_ci_high=hi, sd_diff=float(sd_d), swc=float(swc), noise_to_swc=float(sd_d / swc),
                use_lab_norms=(bool(a["mae"] <= ANGLE_MARGIN and t["tost_p"] < 0.05) if angle else None),
                use_ranking=bool(a["icc21"] >= ICC_GOOD and lo >= ICC_FLOOR),
                use_monitoring=bool(sd_d <= swc))


def conditions() -> dict[str, pd.DataFrame]:
    df = pd.read_csv(RES / "sensibilidad.csv")
    typ = subject_level(df[(df.dataset == "movi") & np.logical_and.reduce([df[k] == v for k, v in TYPICAL.items()])])
    typ = typ.assign(sujeto=typ.ensayo)
    out = {"single camera (80 px, simulated)": typ[typ.vista.isin((45, 90, 135))]}
    fused = []
    for k in FEATURE_NAMES + LOAD_NAMES:
        g = typ[(typ.rasgo == k) & typ.vista.isin((45, 90, 135))]
        g = g.groupby("ensayo")[["referencia", "estimado"]].mean().reset_index()
        if g.empty:
            continue
        g["estimado"] = _calibrate_loso(g.estimado.to_numpy(), g.referencia.to_numpy(), g.ensayo.to_numpy())
        fused.append(g.assign(rasgo=k, sujeto=g.ensayo))
    out["3 replays + bias correction (simulated)"] = pd.concat(fused, ignore_index=True)
    real = RES / "video_movi.csv"
    if real.exists():
        v = pd.read_csv(real)
        out["real video, 80 px"] = v[(~v.nativa) & (v.altura_px == 80) & (v.contacto == "conocido")]
    return out


def main():
    rows = []
    for cond, data in conditions().items():
        for k in FEATURE_NAMES + LOAD_NAMES:
            g = data[data.rasgo == k]
            if len(g) < 10:
                continue
            rows.append(dict(condition=cond, key=k, feature=NAMES[k].replace("\n", " "),
                             unit="N·m/kg" if k in LOAD_NAMES else "deg", **evaluate(g, k)))
    t = pd.DataFrame(rows)
    t.round(3).to_csv(OUT / "table9_acceptability.csv", index=False)
    pd.set_option("display.width", 220)
    print(t[["condition", "key", "n_participants", "mae", "bias", "tost_p", "icc21", "icc_ci_low", "noise_to_swc",
             "use_lab_norms", "use_ranking", "use_monitoring"]].round(3).to_string())


if __name__ == "__main__":
    main()
