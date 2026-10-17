"""Acuerdo entre rasgos de referencia y estimados."""
import numpy as np


def _icc21(x: np.ndarray) -> float:
    """ICC(2,1) de acuerdo absoluto (Shrout y Fleiss) para una matriz (n sujetos, k evaluadores)."""
    n, k = x.shape
    m = x.mean()
    ssr = k * ((x.mean(axis=1) - m) ** 2).sum()
    ssc = n * ((x.mean(axis=0) - m) ** 2).sum()
    sse = ((x - m) ** 2).sum() - ssr - ssc
    msr, msc, mse = ssr / (n - 1), ssc / (k - 1), sse / ((n - 1) * (k - 1))
    den = msr + (k - 1) * mse + k * (msc - mse) / n
    return float((msr - mse) / den) if den > 1e-12 else float("nan")


def agreement(gt: np.ndarray, est: np.ndarray) -> dict:
    gt, est = np.asarray(gt, float), np.asarray(est, float)
    ok = np.isfinite(gt) & np.isfinite(est)
    g, e = gt[ok], est[ok]
    d = e - g
    sd = d.std(ddof=1) if len(d) > 1 else float("nan")
    r = float(np.corrcoef(g, e)[0, 1]) if len(d) > 1 and g.std() > 0 and e.std() > 0 else float("nan")
    return {
        "n": int(ok.sum()),
        "bias": float(d.mean()),
        "mae": float(np.abs(d).mean()),
        "rmse": float(np.sqrt((d ** 2).mean())),
        "loa_low": float(d.mean() - 1.96 * sd),
        "loa_high": float(d.mean() + 1.96 * sd),
        "r": r,
        "icc21": _icc21(np.column_stack([g, e])) if len(d) > 1 else float("nan"),
        # pendiente de la verdad sobre lo estimado: factor de atenuación (dilución) de cualquier asociación
        # que se estime con la medida de vídeo en lugar de la de laboratorio
        "calib_slope": float(np.cov(g, e)[0, 1] / e.var(ddof=1)) if len(d) > 1 and e.std() > 0 else float("nan"),
        # diferencia mínima detectable entre dos medidas (95 %) si el error aleatorio es independiente
        "sdd": float(1.96 * np.sqrt(2) * sd) if len(d) > 1 else float("nan"),
    }
