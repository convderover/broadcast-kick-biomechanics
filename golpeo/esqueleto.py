"""Esqueleto canónico: 8 articulaciones, metros, eje z hacia arriba."""

JOINTS = ("l_shoulder", "r_shoulder", "l_hip", "r_hip", "l_knee", "r_knee", "l_ankle", "r_ankle")
_INDEX = {name: i for i, name in enumerate(JOINTS)}


def idx(name: str) -> int:
    return _INDEX[name]
