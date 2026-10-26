"""The illustration uses assumed information fractions, never measured slopes."""
import numpy as np
import pytest

from analisis_carga import events_needed


def test_hypothetical_event_counts():
    q = np.array([1.0, 0.5, 0.2, 0.1])
    assert np.ceil(events_needed(1.5, information_fraction=q)).tolist() == [48, 96, 239, 478]


@pytest.mark.parametrize("q", [0, -0.1, 1.1, np.nan])
def test_invalid_information_fraction(q):
    with pytest.raises(ValueError, match="information fraction"):
        events_needed(1.5, information_fraction=q)


@pytest.mark.parametrize("hr", [0, 1, np.nan, np.inf])
def test_invalid_hazard_ratio(hr):
    with pytest.raises(ValueError, match="hazard ratio"):
        events_needed(hr, information_fraction=0.5)
