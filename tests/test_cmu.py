from pathlib import Path

import numpy as np
import pytest

from golpeo.cinematica import contact_frame, kick_features, kicking_side
from golpeo.contacto import ball_contact
from tests.sintetico import kick_sequence

CMU = Path(__file__).parents[1] / "datos" / "cmu"


def _ball(fps=120, contact=50, speed=20.0, T=100):
    t = np.arange(T)
    p = np.tile([1.0, 2.0, 0.11], (T, 1))
    moving = t > contact
    p[moving, 1] += speed * (t[moving] - contact) / fps
    return p


def test_contacto_balon_sin_huecos():
    contact, v = ball_contact(_ball(), 120)
    assert contact == pytest.approx(50, abs=1)
    assert v == pytest.approx(20, abs=0.5)


def test_contacto_balon_ocluido_en_el_impacto():
    b = _ball()
    b[46:56] = np.nan                       # el pie tapa el balón justo en el contacto
    contact, v = ball_contact(b, 120)
    assert contact == pytest.approx(50, abs=1)
    assert v == pytest.approx(20, abs=0.5)


def test_contacto_balon_que_nunca_se_mueve():
    assert ball_contact(np.tile([0.0, 0.0, 0.11], (50, 1)), 120) == (None, None)


def test_features_con_contacto_explicito():
    seq = kick_sequence()
    c = contact_frame(seq, 100, "r")
    assert kick_features(seq, 100, contact=c) == kick_features(seq, 100)


@pytest.mark.skipif(not (CMU / "10_01.c3d").exists(), reason="faltan los C3D de CMU")
def test_lector_cmu_real():
    from golpeo.datos_cmu import load_cmu
    trial = load_cmu(CMU / "10_01.c3d")
    assert trial.seq.shape == (801, 8, 3) and trial.fps == 120
    z = np.nanmedian(trial.seq[..., 2], axis=0)
    assert z[0] > z[2] > z[4] > z[6]          # hombro > cadera > rodilla > tobillo (izq.)
    thigh = np.nanmedian(np.linalg.norm(trial.seq[:, 2] - trial.seq[:, 4], axis=1))
    assert 0.35 < thigh < 0.50                # metros
    assert kicking_side(trial.seq, trial.fps) == "r"
    assert trial.ball is not None and trial.ball.shape == (801, 3)


@pytest.mark.skipif(not (CMU / "10_04.c3d").exists(), reason="faltan los C3D de CMU")
def test_lector_cmu_sin_balon():
    from golpeo.datos_cmu import load_cmu
    assert load_cmu(CMU / "10_04.c3d").ball is None
