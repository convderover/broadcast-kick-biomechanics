"""Mapeo estadístico paramétrico 1D (SPM) no paramétrico para curvas emparejadas (Nichols y Holmes 2002;
Pataky et al. 2015): prueba t emparejada en cada instante, umbral corregido por comparaciones múltiples a partir de
la distribución del máximo |t| bajo permutaciones de signo, y valor p de cada racimo (instantes consecutivos por
encima del umbral) según su masa (suma de |t|).
"""
import numpy as np


def _t_curve(d: np.ndarray) -> np.ndarray:
    n = d.shape[-2]
    sd = d.std(axis=-2, ddof=1)
    return d.mean(axis=-2) / np.where(sd > 0, sd, np.nan) * np.sqrt(n)


def _clusters(mask: np.ndarray) -> list[tuple[int, int]]:
    out, start = [], None
    for i, m in enumerate(mask):
        if m and start is None:
            start = i
        if not m and start is not None:
            out.append((start, i - 1))
            start = None
    if start is not None:
        out.append((start, len(mask) - 1))
    return out


def paired_snpm(a: np.ndarray, b: np.ndarray, n_perm: int = 10000, alpha: float = 0.05,
                rng: np.random.Generator | None = None) -> dict:
    """a, b: (participantes, instantes). Contrasta media(b − a) = 0 en cada instante, bilateral.
    Devuelve la curva t, el umbral t*, la máscara significativa y los racimos [(inicio, fin, p)]."""
    rng = np.random.default_rng(0) if rng is None else rng
    d = np.asarray(b, float) - np.asarray(a, float)
    t = _t_curve(d)
    signs = rng.choice((-1.0, 1.0), size=(n_perm, d.shape[0], 1))
    t_perm = np.abs(_t_curve(signs * d[None]))                  # (n_perm, instantes)
    t_star = float(np.quantile(np.nanmax(t_perm, axis=1), 1 - alpha))
    mask = np.abs(t) > t_star
    perm_mass = np.array([max((tp[i:j + 1].sum() for i, j in _clusters(tp > t_star)), default=0.0)
                          for tp in t_perm])
    clusters = []
    for i, j in _clusters(mask):
        mass = float(np.abs(t[i:j + 1]).sum())
        clusters.append((i, j, float((np.sum(perm_mass >= mass) + 1) / (n_perm + 1))))
    return {"t": t, "t_star": t_star, "mask": mask, "clusters": clusters}
