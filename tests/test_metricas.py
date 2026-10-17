import numpy as np
import pytest

from golpeo.metricas import agreement


def _gt():
    return np.random.default_rng(2).normal(30, 8, 40)


def test_identicos():
    g = _gt()
    a = agreement(g, g.copy())
    assert a["bias"] == pytest.approx(0) and a["mae"] == pytest.approx(0)
    assert a["r"] == pytest.approx(1) and a["icc21"] == pytest.approx(1)


def test_sesgo_constante():
    g = _gt()
    a = agreement(g, g + 5)
    assert a["bias"] == pytest.approx(5) and a["mae"] == pytest.approx(5)
    assert a["icc21"] < 1


def test_icc_varianza_cero():
    a = agreement(np.full(10, 3.0), np.full(10, 3.0))
    assert np.isnan(a["icc21"])


def test_ignora_nan():
    g = _gt()
    e = g.copy()
    e[3] = np.nan
    a = agreement(g, e)
    assert a["n"] == len(g) - 1
    assert a["mae"] == pytest.approx(0)


def test_pendiente_de_calibracion_y_sdd():
    rng = np.random.default_rng(0)
    gt = rng.normal(0, 10, 5000)
    perfect = agreement(gt, gt)
    assert perfect["calib_slope"] == pytest.approx(1.0) and perfect["sdd"] == pytest.approx(0.0)
    noisy = agreement(gt, gt + rng.normal(0, 10, 5000))       # fiabilidad 0,5 → pendiente ≈ 0,5
    assert noisy["calib_slope"] == pytest.approx(0.5, abs=0.03)
    assert noisy["sdd"] == pytest.approx(1.96 * np.sqrt(2) * 10, rel=0.05)


def test_traduccion_de_figuras():
    from golpeo.figuras_es import translate
    assert translate("b  From video: ICC = 0.12") == "b  Desde vídeo: CCI = 0,12"
    assert translate("Kicking-knee peak flexion") == "Flexión máx. rodilla de golpeo"
    assert translate("6 000 detections") == "6.000 detections"
    assert translate("laboratory") == "laboratorio"


def test_spm_detecta_solo_la_diferencia_real():
    from golpeo.spm import paired_snpm
    rng = np.random.default_rng(1)
    t = np.linspace(0, 1, 30)
    base = 40 * np.sin(np.pi * t)[None] + rng.normal(0, 5, (60, 1))     # 60 participantes con su propio nivel
    a = base + rng.normal(0, 3, (60, 30))
    b = base + rng.normal(0, 3, (60, 30)) + np.where(t > 0.6, 6.0, 0.0)  # diferencia solo al final
    r = paired_snpm(a, b, n_perm=2000, rng=np.random.default_rng(2))
    assert r["mask"][t > 0.7].all() and not r["mask"][t < 0.5].any()
    assert len(r["clusters"]) == 1 and r["clusters"][0][2] < 0.05
    nulo = paired_snpm(a, base + rng.normal(0, 3, (60, 30)), n_perm=2000, rng=np.random.default_rng(3))
    assert not nulo["mask"].any()
