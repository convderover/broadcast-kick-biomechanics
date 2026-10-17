import numpy as np
import pytest

from golpeo.cinematica import hip_flexion, knee_flexion, trunk_lean
from golpeo.esqueleto import JOINTS, idx


def standing():
    """Sujeto de pie mirando a +y, cadera derecha en +x. Forma (1, 8, 3)."""
    p = np.zeros((len(JOINTS), 3))
    p[idx("l_shoulder")] = [-0.2, 0, 1.5]
    p[idx("r_shoulder")] = [0.2, 0, 1.5]
    p[idx("l_hip")] = [-0.1, 0, 1.0]
    p[idx("r_hip")] = [0.1, 0, 1.0]
    p[idx("l_knee")] = [-0.1, 0, 0.55]
    p[idx("r_knee")] = [0.1, 0, 0.55]
    p[idx("l_ankle")] = [-0.1, 0, 0.1]
    p[idx("r_ankle")] = [0.1, 0, 0.1]
    return p[None]


def test_pierna_recta_flexion_cero():
    assert knee_flexion(standing(), "r")[0] == pytest.approx(0, abs=1e-6)


def test_rodilla_90():
    s = standing()
    s[0, idx("r_ankle")] = s[0, idx("r_knee")] + [0, -0.45, 0]
    assert knee_flexion(s, "r")[0] == pytest.approx(90, abs=1e-6)


def test_cadera_flexion_signo():
    s = standing()
    hip = s[0, idx("r_hip")]
    a = np.radians(45)
    s[0, idx("r_knee")] = hip + 0.45 * np.array([0, np.sin(a), -np.cos(a)])
    assert hip_flexion(s, "r")[0] == pytest.approx(45, abs=1e-6)
    b = np.radians(30)
    s[0, idx("r_knee")] = hip + 0.45 * np.array([0, -np.sin(b), -np.cos(b)])
    assert hip_flexion(s, "r")[0] == pytest.approx(-30, abs=1e-6)


def _tilt_trunk(s, axis_vec):
    """Rota los hombros alrededor del centro de caderas según el vector de rotación dado."""
    from scipy.spatial.transform import Rotation
    rot = Rotation.from_rotvec(axis_vec).as_matrix()
    mid_hip = s[0, [idx("l_hip"), idx("r_hip")]].mean(axis=0)
    for j in ("l_shoulder", "r_shoulder"):
        s[0, idx(j)] = mid_hip + rot @ (s[0, idx(j)] - mid_hip)
    return s


def test_tronco_vertical_y_adelante():
    np.testing.assert_allclose(trunk_lean(standing())[0], [0, 0], atol=1e-6)
    adelante = _tilt_trunk(standing(), [-np.radians(20), 0, 0])   # rota z hacia +y
    np.testing.assert_allclose(trunk_lean(adelante)[0], [20, 0], atol=1e-6)
    derecha = _tilt_trunk(standing(), [0, np.radians(10), 0])     # rota z hacia +x
    np.testing.assert_allclose(trunk_lean(derecha)[0], [0, 10], atol=1e-6)
