import numpy as np
import pytest

from golpeo.error2d import LIMB_JOINTS, coco_to_3dsp, fit_noise_model, player_height


def test_coco_a_3dsp_por_nombre():
    k = np.zeros((133, 2))
    k[:17] = np.arange(17)[:, None] * [1, 10]          # COCO cuerpo: el punto i vale (i, 10·i)
    out = coco_to_3dsp(k)
    assert out.shape == (17, 2)
    np.testing.assert_allclose(out[1], [11, 110])      # Left Hip ← COCO 11
    np.testing.assert_allclose(out[6], [16, 160])      # Right Ankle ← COCO 16
    np.testing.assert_allclose(out[11], [6, 60])       # Right Shoulder ← COCO 6
    np.testing.assert_allclose(out[0], [11.5, 115])    # Center of Hips = media de 11 y 12
    assert len(LIMB_JOINTS) == 12


def test_altura_jugador():
    kp = np.zeros((17, 2))
    kp[10] = [0, 5]      # cabeza
    kp[3] = [0, 65]      # tobillo
    assert player_height(kp) == pytest.approx(60)


def test_ajuste_modelo_ruido_recupera_parametros():
    rng = np.random.default_rng(0)
    h = rng.uniform(20, 120, 400)
    sigma = np.hypot(0.04 * h, 1.2)
    frac, floor = fit_noise_model(h, sigma)
    assert frac == pytest.approx(0.04, abs=0.002)
    assert floor == pytest.approx(1.2, abs=0.1)
