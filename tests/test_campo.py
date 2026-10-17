import numpy as np

from campo_videos import fix_swaps


def _walk(T=60):
    """Esqueleto 2D sintético (H36M) con las piernas separadas que se mueven despacio."""
    t = np.arange(T)
    uv = np.zeros((T, 17, 2))
    uv[:, :, 1] = np.linspace(0, -170, 17)[None]                 # alturas distintas por articulación
    uv[:, 10, 1] = -200
    for j, x in ((1, 10), (2, 12), (3, 14), (4, -10), (5, -12), (6, -14)):
        uv[:, j, 0] = x + 0.5 * t
    uv[:, [1, 4], 1], uv[:, [2, 5], 1], uv[:, [3, 6], 1] = -90, -45, 0
    return uv


def test_corrige_un_tramo_de_piernas_cruzadas():
    clean = _walk()
    bad = clean.copy()
    bad[20:30, [2, 3, 5, 6]] = clean[20:30, [5, 6, 2, 3]]          # 10 fotogramas con rodillas y tobillos cruzados
    fixed, n = fix_swaps(bad)
    assert n == 10
    np.testing.assert_allclose(fixed, clean)


def test_no_toca_una_secuencia_limpia():
    clean = _walk()
    fixed, n = fix_swaps(clean)
    assert n == 0
    np.testing.assert_allclose(fixed, clean)
