import numpy as np
import pytest

from golpeo.degradacion import degrade_frame, scale_for_height, subsample


def _img():
    rng = np.random.default_rng(1)
    return rng.integers(0, 256, (1080, 1920, 3), dtype=np.uint8)


def test_escala_tamano():
    assert scale_for_height(400, 100) == pytest.approx(0.25)
    out = degrade_frame(_img(), 0.25, blur_px=0, jpeg_quality=None)
    assert out.shape == (270, 480, 3)


def test_blur_conserva_media():
    img = _img()
    out = degrade_frame(img, 1.0, blur_px=7, jpeg_quality=None)
    assert out.mean() == pytest.approx(img.mean(), abs=1.0)
    assert not np.array_equal(out, img)


def test_jpeg_cambia_pixeles():
    img = _img()
    out = degrade_frame(img, 1.0, blur_px=0, jpeg_quality=50)
    assert out.shape == img.shape
    assert not np.array_equal(out, img)


def test_subsample_100_a_25():
    x = np.arange(100)
    out, fps = subsample(x, 100, 25)
    assert fps == 25
    np.testing.assert_array_equal(out[:3], [0, 4, 8])


def test_subsample_no_entero_falla():
    with pytest.raises(ValueError, match="entero"):
        subsample(np.arange(60), 60, 25)
