import numpy as np
import pytest

from golpeo.carga import DE_LEVA, LOAD_NAMES, kick_loads, lowpass, swing_leg_moments
from tests.sintetico import kick_sequence

G = 9.81


def _static_leg(T=200, thigh=0.45, shank=0.42, knee_deg=0.0):
    """Pierna derecha quieta, colgando (o con la rodilla flexionada `knee_deg` hacia atrás)."""
    seq = np.zeros((T, 8, 3))
    seq[:, 0], seq[:, 1] = [-0.2, 0, 1.4], [0.2, 0, 1.4]          # hombros
    seq[:, 2], seq[:, 3] = [-0.1, 0, 0.9], [0.1, 0, 0.9]          # caderas
    seq[:, 4], seq[:, 6] = [-0.1, 0, 0.9 - thigh], [-0.1, 0, 0.9 - thigh - shank]
    k = np.radians(knee_deg)
    seq[:, 5] = [0.1, 0, 0.9 - thigh]
    seq[:, 7] = seq[:, 5] + shank * np.array([0, -np.sin(k), -np.cos(k)])
    return seq


def test_pierna_colgando_sin_momentos():
    m = swing_leg_moments(_static_leg(), fps=100, side="r", mass_kg=70, sex="male", cutoff_hz=None)
    assert np.abs(m["rodilla_momento"]).max() < 1e-6
    assert np.abs(m["cadera_momento"]).max() < 1e-6


def test_pierna_estatica_flexionada_momento_gravitatorio():
    """Muslo vertical y pierna horizontal hacia atrás, quieta: la gravedad tiende a extender la rodilla,
    así que el momento neto que la sostiene es flexor (negativo) e igual al peso de pierna y pie por su brazo."""
    seq = _static_leg(knee_deg=90)
    m = swing_leg_moments(seq, fps=100, side="r", mass_kg=70, sex="male", cutoff_hz=None)
    p = DE_LEVA["male"]
    shank, foot = p["shank"], p["foot"]
    expected = 70 * G * 0.42 * (shank["mass"] * shank["com"] + foot["mass"])       # brazo horizontal
    assert m["rodilla_momento"][100] == pytest.approx(-expected, rel=1e-6)


def test_pierna_estatica_hacia_delante_momento_extensor():
    seq = _static_leg(knee_deg=-90)                 # pierna extendida hacia delante: hace falta extensor
    m = swing_leg_moments(seq, fps=100, side="r", mass_kg=70, sex="male", cutoff_hz=None)
    assert m["rodilla_momento"][100] > 0


def test_cargas_del_golpeo_sintetico_finitas_y_simetricas():
    seq = kick_sequence(fps=120)
    a = kick_loads(seq, 120, mass_kg=75, sex="male")
    assert set(a) == set(LOAD_NAMES) and all(np.isfinite(v) for v in a.values())
    mirror = seq.copy()
    mirror[..., 0] *= -1
    mirror = mirror[:, [1, 0, 3, 2, 5, 4, 7, 6]]
    b = kick_loads(mirror, 120, mass_kg=75, sex="male")
    for k in LOAD_NAMES:
        assert b[k] == pytest.approx(a[k], rel=1e-6, abs=1e-9)


def test_cargas_escalan_con_la_velocidad():
    """Generado a 240 fps y leído a 120, el golpeo va a la mitad de velocidad: los momentos inerciales
    caen a ~1/4 (no del todo, por la gravedad)."""
    normal = kick_loads(kick_sequence(fps=120, T_s=2.0, contact_s=1.0), 120, 75, "male")
    slow = kick_loads(kick_sequence(fps=240, T_s=2.0, contact_s=1.0), 120, 75, "male")
    assert normal["momento_cadera_flexor_max"] > 2.5 * slow["momento_cadera_flexor_max"]


def test_lowpass_conserva_la_constante_y_quita_ruido():
    rng = np.random.default_rng(0)
    x = np.full((300, 3), 2.0) + rng.normal(0, 0.1, (300, 3))
    y = lowpass(x, fps=100, cutoff_hz=5)
    assert np.abs(y.mean(0) - 2.0).max() < 0.02 and y.std(0).max() < 0.05


def test_cargas_con_lado_y_contacto_explicitos():
    seq = kick_sequence(fps=120)
    a = kick_loads(seq, 120, 75, "male")
    from golpeo.cinematica import contact_frame
    b = kick_loads(seq, 120, 75, "male", contact=contact_frame(seq, 120, "r"), side="r")
    assert a == b
