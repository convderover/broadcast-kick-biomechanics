import numpy as np
import pytest
from scipy.spatial.transform import Rotation

from golpeo.cinematica import FEATURE_NAMES, contact_frame, kick_features, kicking_side, rigid_align
from tests.sintetico import kick_sequence, mirror


def test_lado_y_contacto():
    seq = kick_sequence(fps=100, side="r", contact_s=0.5)
    assert kicking_side(seq, 100) == "r"
    # La extensión de rodilla adelanta el pico de velocidad del tobillo ~50 ms respecto al pico
    # de giro de cadera (contact_s), como en golpeos reales: aceptamos hasta 60 ms.
    assert abs(contact_frame(seq, 100, "r") - 50) <= 6


def test_rasgos_valores_conocidos():
    f = kick_features(kick_sequence(), 100)
    assert set(f) == set(FEATURE_NAMES)
    assert f["rodilla_apoyo_flexion_contacto"] == pytest.approx(20, abs=1e-6)
    assert f["rodilla_golpeo_flexion_max"] == pytest.approx(90, abs=1.0)
    assert f["tronco_inclinacion_lateral_contacto"] == pytest.approx(8, abs=1e-6)
    assert f["cadera_golpeo_extension_max"] > 25


def test_golpeo_izquierda_simetrico():
    seq = kick_sequence(side="r")
    assert kicking_side(mirror(seq), 100) == "l"
    a, b = kick_features(seq, 100), kick_features(mirror(seq), 100)
    for k in FEATURE_NAMES:
        assert a[k] == pytest.approx(b[k], abs=1e-6)


def test_ventana_recortada():
    f = kick_features(kick_sequence(contact_s=0.05), 100)
    assert all(np.isfinite(v) for v in f.values())


def test_features_ignoran_nan():
    seq = kick_sequence()
    ref = kick_features(seq, 100)
    rng = np.random.default_rng(0)
    frames = np.setdiff1d(np.arange(len(seq)), np.arange(40, 61))
    holes = rng.choice(frames, size=len(seq) // 10, replace=False)
    seq[holes] = np.nan
    got = kick_features(seq, 100)
    for k in FEATURE_NAMES:
        assert np.isfinite(got[k])
        assert got[k] == pytest.approx(ref[k], abs=0.5)


def test_rigid_align_recupera():
    gt = kick_sequence()
    rot = Rotation.from_rotvec([0.1, -0.2, np.radians(30)]).as_matrix()
    est = gt @ rot.T + [3.0, -1.0, 0.5]
    np.testing.assert_allclose(rigid_align(est, gt), gt, atol=1e-9)


def test_lado_explicito_manda_sobre_el_estimado():
    """Con el lado conocido, un tobillo de apoyo ruidoso (más rápido que el de golpeo) no cambia los rasgos."""
    seq = kick_sequence()
    noisy = seq.copy()
    noisy[10, 6] += [0, 0, 0.5]                          # pico espurio en el tobillo izquierdo
    assert kicking_side(noisy, 100) == "l"
    c = contact_frame(seq, 100, "r")
    assert kick_features(noisy, 100, contact=c, side="r") == kick_features(seq, 100, contact=c, side="r")
