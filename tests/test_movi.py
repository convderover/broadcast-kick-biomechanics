from pathlib import Path

import numpy as np
import pytest
import scipy.io as sio

from golpeo.datos_movi import VIRTUAL, MoviCamera, load_movi

MOVI = Path(__file__).parents[1] / "datos" / "movi" / "3d"


def _fake_movi(tmp_path, gap=False):
    """Fichero con la estructura de F_v3d_Subject_X.mat: 2 movimientos, 'kicking' en los fotogramas 10–29."""
    T = 40
    names = list(VIRTUAL) + ["LFHD", "RFHD", "LBHD", "RBHD"]
    virt = np.arange(1, len(VIRTUAL) + 1)
    loc = np.zeros((T, len(VIRTUAL), 3))
    for j in range(len(VIRTUAL)):
        loc[:, j] = [100.0 * j, 10.0 * j, 1000.0 + j]           # mm
    if gap:
        loc[15, VIRTUAL.index("RAJC")] = -999999000.0
    markers = np.full((T, 4, 3), 1800.0)
    move = {"motions_list": np.array(["walking", "kicking"], dtype=object),
            "flags120": np.array([[0, 9], [10, 29]]), "flags30": np.array([[0, 2], [3, 7]]),
            "markerName": np.array(names, dtype=object), "virtualMarkers": virt,
            "physicalMarkers": np.arange(len(VIRTUAL) + 1, len(names) + 1),
            "virtualMarkerLocation": loc, "markerLocation": np.concatenate([loc, markers], axis=1)}
    subject = {"id": "Subject_7", "sex": "female", "height": 170, "mass": 60, "age": 22}
    path = tmp_path / "F_v3d_Subject_7.mat"
    sio.savemat(path, {"Subject_7_F": {"id": "Subject_7", "subject": subject, "move": move}})
    return path


def test_movi_ventana_y_unidades(tmp_path):
    tr = load_movi(_fake_movi(tmp_path), margin_s=0.0)
    assert tr.subject == 7 and tr.mass_kg == 60 and tr.height_m == pytest.approx(1.70)
    assert tr.x17.shape == (20, 17, 3) and tr.fps == 120 and tr.frame0 == 10
    rhip = VIRTUAL.index("RHIP")
    np.testing.assert_allclose(tr.x17[0, 1], [0.1 * rhip, 0.01 * rhip, 1.0 + rhip / 1000])
    np.testing.assert_allclose(tr.x17[:, 0], 0.5 * (tr.x17[:, 1] + tr.x17[:, 4]))
    assert tr.video_frame0 == 3 and tr.video_frames == 5


def test_movi_huecos_son_nan(tmp_path):
    tr = load_movi(_fake_movi(tmp_path, gap=True), margin_s=0.0)
    assert np.isnan(tr.x17[5, 3]).all() and np.isfinite(tr.x17[4, 3]).all()


def test_movi_ceros_son_huecos(tmp_path):
    """Visual3D deja a (0, 0, 0) las articulaciones que no pudo calcular: deben ser NaN, no el origen."""
    path = _fake_movi(tmp_path)
    d = sio.loadmat(path, simplify_cells=True)
    d["Subject_7_F"]["move"]["virtualMarkerLocation"][12, VIRTUAL.index("LEJC")] = 0.0
    sio.savemat(path, d)
    tr = load_movi(path, margin_s=0.0)
    assert np.isnan(tr.x17[2, 12]).all() and np.isfinite(tr.x17[3, 12]).all()


def test_relleno_de_huecos_cortos_y_largos():
    from golpeo.ensayos import fill_gaps
    x = np.tile(np.arange(100.0)[:, None, None], (1, 2, 3))
    x[10:13, 0] = np.nan                       # 3 fotogramas: se rellena
    x[40:80, 1] = np.nan                       # 40 fotogramas a 120 fps (0,33 s): demasiado largo
    filled, ok = fill_gaps(x, fps=120, max_gap_s=0.25)
    np.testing.assert_allclose(filled[10:13, 0], x[[10, 11, 12], 1] * 0 + np.arange(10, 13)[:, None])
    assert not ok and np.isnan(filled[40:80, 1]).all()
    assert fill_gaps(x[:30], fps=120)[1]


def test_movi_margen_recortado(tmp_path):
    tr = load_movi(_fake_movi(tmp_path), margin_s=1.0)          # 120 fotogramas de margen: se recorta
    assert tr.frame0 == 0 and len(tr.x17) == 40


def test_camara_movi_convenio_matlab():
    K_matlab = np.array([[1000.0, 0, 0], [0, 900.0, 0], [400.0, 300.0, 1.0]])   # transpuesta, como en MATLAB
    cam = MoviCamera(K_matlab, np.zeros(2), np.eye(3), np.array([0.0, 0.0, 5000.0]))
    uv = cam.project(np.array([[0.5, -0.25, 0.0]]))                              # metros
    np.testing.assert_allclose(uv, [[400 + 1000 * 500 / 5000, 300 - 900 * 250 / 5000]])


@pytest.mark.skipif(not (MOVI / "F_Subjects_1_45" / "F_v3d_Subject_1.mat").exists(), reason="MoVi no descargado")
def test_movi_real_sujeto_1():
    from golpeo.cinematica import kicking_side
    from golpeo.h36m import to_canonical
    tr = load_movi(MOVI / "F_Subjects_1_45" / "F_v3d_Subject_1.mat")
    seq = to_canonical(tr.x17)
    assert kicking_side(seq, tr.fps) == "r"
    thigh = np.nanmedian(np.linalg.norm(seq[:, 3] - seq[:, 5], axis=1))
    assert 0.35 < thigh < 0.55
    assert tr.mass_kg == 92
