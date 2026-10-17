from pathlib import Path

import numpy as np
import pytest

from golpeo.camara import film
from golpeo.h36m import H36M_JOINTS, to_canonical
from tests.sintetico import kick_sequence

ROOT = Path(__file__).parents[1]
CMU = ROOT / "datos" / "cmu" / "10_01.c3d"
CKPT = ROOT / "modelos" / "motionagformer_pesos" / "motionagformer-b-h36m.pth.tr"


def _person17(T=60):
    """Persona de 17 puntos H36M construida a partir del golpeo sintético (metros, z arriba)."""
    s = kick_sequence(fps=100, T_s=max(1.0, T / 100), contact_s=0.5)[:T]
    x = np.zeros((T, 17, 3))
    lsh, rsh, lhip, rhip, lkn, rkn, lan, ran = (s[:, i] for i in range(8))
    x[:, 0] = 0.5 * (lhip + rhip)
    x[:, 1], x[:, 2], x[:, 3] = rhip, rkn, ran
    x[:, 4], x[:, 5], x[:, 6] = lhip, lkn, lan
    x[:, 8] = 0.5 * (lsh + rsh)
    x[:, 7] = 0.5 * (x[:, 0] + x[:, 8])
    x[:, 9] = x[:, 8] + [0, 0.05, 0.15]
    x[:, 10] = x[:, 8] + [0, 0, 0.3]
    x[:, 11], x[:, 14] = lsh, rsh
    x[:, 12], x[:, 15] = lsh - [0, 0, 0.3], rsh - [0, 0, 0.3]
    x[:, 13], x[:, 16] = lsh - [0, 0, 0.55], rsh - [0, 0, 0.55]
    return x


def test_canonico_desde_h36m():
    x = _person17()
    c = to_canonical(x)
    assert c.shape == (60, 8, 3)
    np.testing.assert_allclose(c[:, 3], x[:, 1])      # r_hip
    np.testing.assert_allclose(c[:, 6], x[:, 6])      # l_ankle
    assert len(H36M_JOINTS) == 17


def test_film_altura_en_pixeles():
    uv, conf = film(_person17(), azimuth_deg=90, elevation_deg=15, height_px=120,
                    sigma_frac=0.0, sigma_floor_px=0.0, rng=np.random.default_rng(0))
    h = np.median(uv[..., 1].max(axis=1) - uv[..., 1].min(axis=1))
    assert h == pytest.approx(120, rel=0.03)
    assert uv.shape == (60, 17, 2) and conf.shape == (60, 17)
    assert (uv[..., 0] > 0).all() and (uv[..., 0] < 1920).all()


def test_film_ruido_escala():
    x = _person17()
    clean, _ = film(x, 90, 15, 200, 0.0, 0.0, np.random.default_rng(1))
    noisy, _ = film(x, 90, 15, 200, 0.02, 0.0, np.random.default_rng(1))
    assert np.std(noisy - clean) == pytest.approx(0.02 * 200, rel=0.1)


def test_film_vista_frontal_y_lateral_distintas():
    x = _person17()
    a, _ = film(x, 0, 15, 200, 0, 0, np.random.default_rng(0))
    b, _ = film(x, 90, 15, 200, 0, 0, np.random.default_rng(0))
    assert not np.allclose(a, b)


@pytest.mark.skipif(not CMU.exists(), reason="faltan los C3D de CMU")
def test_cmu_h36m_proporciones():
    from golpeo.datos_cmu import load_cmu_h36m
    x, fps = load_cmu_h36m(CMU)
    assert x.shape[1:] == (17, 3) and fps == 120
    z = np.nanmedian(x[..., 2], axis=0)
    assert z[10] > z[8] > z[0] > z[2] > z[3]       # cabeza > tórax > pelvis > rodilla > tobillo


@pytest.mark.skipif(not (CKPT.exists() and CMU.exists()), reason="faltan pesos o C3D")
def test_elevador_recorte_no_depende_del_tamano():
    """Sin ruido, reconstruir desde un jugador de 400 px o de 80 px debe dar casi la misma pose 3D."""
    from experimento_sensibilidad import resample
    from golpeo.datos_cmu import load_cmu_h36m
    from golpeo.elevador import Lifter
    x, fps = load_cmu_h36m(CMU)
    x = resample(x, fps, 50)
    lifter = Lifter()
    outs = []
    for h in (400, 80):
        uv, conf = film(x, 90, 15, h, 0.0, 0.0, np.random.default_rng(0))
        outs.append(lifter.lift_person(uv, conf))
    scale = np.linalg.norm(outs[0][:, 1] - outs[0][:, 2], axis=1).mean()
    assert np.abs(outs[0] - outs[1]).mean() < 0.02 * scale


@pytest.mark.skipif(not CKPT.exists(), reason="faltan los pesos de MotionAGFormer")
def test_elevador_forma_y_finitud():
    from golpeo.elevador import Lifter
    x = _person17(T=300)
    uv, conf = film(x, 90, 15, 200, 0.0, 0.0, np.random.default_rng(0))
    out = Lifter().lift(uv, conf, w=1920, h=1080)
    assert out.shape == (300, 17, 3)
    assert np.isfinite(out).all()


def test_coco_a_h36m_como_la_demo():
    from golpeo.h36m import coco_to_h36m
    k = np.zeros((1, 17, 2))
    k[0] = np.arange(17)[:, None] * [1.0, 10.0]          # el punto COCO i vale (i, 10·i)
    s = np.tile(np.linspace(0.1, 0.9, 17), (1, 1))
    uv, conf = coco_to_h36m(k, s)
    np.testing.assert_allclose(uv[0, 1], [12, 120])     # cadera DERECHA H36M ← COCO 12
    np.testing.assert_allclose(uv[0, 4], [11, 110])     # cadera izquierda ← COCO 11
    np.testing.assert_allclose(uv[0, 11], [5, 50])      # hombro izquierdo ← COCO 5
    np.testing.assert_allclose(uv[0, 0], [11.5, 115])   # pelvis = media de caderas
    assert conf[0, 0] == pytest.approx(s[0, [11, 12]].mean())
    assert conf[0, 3] == pytest.approx(s[0, 16])


def test_camera_view_y_espacio_imagen():
    from golpeo.camara import camera_view, image_space_3d
    x = _person17()
    uv, _ = film(x, 45, 15, 120, 0.0, 0.0, np.random.default_rng(0))
    uv2, xc, focal = camera_view(x, 45, 15, 120)
    np.testing.assert_allclose(uv, uv2)
    t = image_space_3d(uv2, xc, focal)
    assert t.shape == (60, 17, 3)
    np.testing.assert_allclose(t[:, 0], 0, atol=1e-9)
    # a 40 m la perspectiva es casi débil: la profundidad en píxeles escala como x e y
    seg_img = np.linalg.norm(t[:, 2] - t[:, 1], axis=-1)        # muslo derecho en "píxeles 3D"
    seg_m = np.linalg.norm(x[:, 2] - x[:, 1], axis=-1)
    ratio = seg_img / seg_m
    assert ratio.std() / ratio.mean() < 0.02 and ratio.mean() == pytest.approx(focal / 40, rel=0.05)
