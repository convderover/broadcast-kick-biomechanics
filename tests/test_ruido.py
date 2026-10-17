import numpy as np
import pandas as pd
import pytest

from golpeo.ruido import H36M_FROM_3DSP, ResidualBank


def _df(n_shots=6, frames=20, h=60.0):
    rows = []
    for s in range(n_shots):
        for f in range(frames):
            r = dict(disparo=f"{s:05d}", fotograma=f"{f + 1:03d}", escala=1.0, altura_px=h + s)
            for j in range(17):
                r[f"x_j{j}"], r[f"y_j{j}"] = float(j), float(100 * s + f)     # x = índice 3DSP, y = (disparo, fotograma)
            rows.append(r)
    return pd.DataFrame(rows)


def test_mapeo_3dsp_a_h36m_por_nombre():
    assert H36M_FROM_3DSP[1] == 4 and H36M_FROM_3DSP[4] == 1          # cadera derecha H36M ← "Right Hip" de 3DSP
    assert H36M_FROM_3DSP[11] == 14 and H36M_FROM_3DSP[14] == 11      # hombro izquierdo H36M ← "Left Shoulder"
    assert sorted(H36M_FROM_3DSP) == list(range(17))


def test_banco_ordena_articulaciones_y_fotogramas():
    bank = ResidualBank.from_frame(_df())
    assert len(bank) == 6
    seq = bank.seqs[0]
    assert seq.shape == (20, 17, 2)
    np.testing.assert_allclose(seq[:, 1, 0], 4.0)                       # cadera derecha ← índice 3DSP 4
    np.testing.assert_allclose(seq[:, 0, 1], np.arange(20))             # orden temporal conservado


def test_muestra_longitud_y_escala():
    bank = ResidualBank.from_frame(_df(h=60.0))
    rng = np.random.default_rng(0)
    out = bank.sample(T=55, fps=25, height_px=120, rng=rng)
    assert out.shape == (55, 17, 2)
    # a 120 px (el doble que los disparos del banco) el residuo se escala ×≈2
    assert np.abs(out[:, 1, 0]).mean() == pytest.approx(8.0, rel=0.1)


def test_muestra_50fps_interpola_en_el_tiempo():
    bank = ResidualBank.from_frame(_df(n_shots=1, h=50.0))
    out = bank.sample(T=10, fps=50, height_px=50, rng=np.random.default_rng(0))
    d = np.diff(out[:, 0, 1])
    np.testing.assert_allclose(d[d > 0], 0.5, atol=1e-9)               # medio fotograma de 25 fps por paso


def test_solo_usa_escala_original():
    df = pd.concat([_df(), _df().assign(escala=0.5)])
    assert len(ResidualBank.from_frame(df)) == 6
