"""Ruido 2D "de retransmisión" por remuestreo de residuos reales de RTMW sobre 3DSP.

A diferencia del ruido gaussiano independiente, conserva la estructura temporal (los 20 fotogramas
consecutivos de cada disparo, a 25 fps), la correlación entre articulaciones y los fallos groseros
(p. ej. confundir piernas). Los residuos se escalan por la altura del jugador: σ crece casi
proporcionalmente con ella (ajuste σ ≈ 0,063·H en 3DSP), así que para jugadores de más de
~90 px el remuestreo es una extrapolación.
"""
import numpy as np
import pandas as pd

# índice 3DSP con el mismo nombre anatómico que cada índice H36M estándar (1 = cadera DERECHA)
H36M_FROM_3DSP = {0: 0, 1: 4, 2: 5, 3: 6, 4: 1, 5: 2, 6: 3, 7: 7, 8: 8, 9: 9, 10: 10,
                  11: 14, 12: 15, 13: 16, 14: 11, 15: 12, 16: 13}
FPS_3DSP = 25.0


class ResidualBank:
    def __init__(self, seqs: list[np.ndarray], heights: np.ndarray, fps: float = FPS_3DSP):
        self.seqs = seqs                  # cada una (n, 17, 2) en píxeles, orden H36M
        self.heights = np.asarray(heights, float)
        self.fps = fps

    def __len__(self):
        return len(self.seqs)

    @classmethod
    def from_frame(cls, df: pd.DataFrame, order: str = "3dsp", fps: float = FPS_3DSP) -> "ResidualBank":
        """Desde resultados/error2d_3dsp.csv (solo la escala original, sin reducir) o, con order="h36m",
        desde una tabla con las columnas ya en orden H36M (p. ej. el vídeo de MoVi)."""
        df = df[df.escala == 1.0]
        src = H36M_FROM_3DSP if order == "3dsp" else {j: j for j in range(17)}
        cols = [c for j in range(17) for c in (f"x_j{src[j]}", f"y_j{src[j]}")]
        seqs, heights = [], []
        for _, g in df.sort_values(["disparo", "fotograma"]).groupby("disparo", sort=True):
            seqs.append(g[cols].to_numpy(float).reshape(len(g), 17, 2))
            heights.append(float(g.altura_px.median()))
        return cls(seqs, np.array(heights), fps)

    def half(self, which: str) -> "ResidualBank":
        """Mitad de los disparos, estratificada por altura (ordenados por altura, alternos): "entrenamiento" o
        "prueba". Separa el ruido con el que se entrena el elevador ajustado del ruido con el que se evalúa."""
        if which not in ("entrenamiento", "prueba"):
            raise ValueError(which)
        order = np.argsort(self.heights, kind="stable")
        idx = order[0::2] if which == "entrenamiento" else order[1::2]
        return ResidualBank([self.seqs[i] for i in idx], self.heights[idx], self.fps)

    def sample(self, T: int, fps: float, height_px: float, rng: np.random.Generator) -> np.ndarray:
        """(T, 17, 2) residuos en píxeles para un jugador de `height_px`, concatenando disparos al azar.
        Se usan los disparos con altura dentro de ±30 % de la pedida si los hay; si no, los 20 % más grandes."""
        close = np.flatnonzero(np.abs(self.heights / height_px - 1) <= 0.3)
        pool = close if len(close) else np.argsort(self.heights)[-max(1, len(self) // 5):]
        out, n = [], 0
        while n < T:
            i = rng.choice(pool)
            seq = self.seqs[i] * (height_px / self.heights[i])
            if fps != self.fps:
                t_in = np.arange(len(seq)) / self.fps
                t_out = np.arange(0, t_in[-1] + 1e-9, 1 / fps)
                flat = seq.reshape(len(seq), -1)
                seq = np.stack([np.interp(t_out, t_in, flat[:, k]) for k in range(flat.shape[1])], 1)
                seq = seq.reshape(len(t_out), 17, 2)
            out.append(seq)
            n += len(seq)
        return np.concatenate(out)[:T]
