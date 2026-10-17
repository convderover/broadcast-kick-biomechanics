"""Elevación 2D → 3D con MotionAGFormer-B (pesos oficiales H36M), según el preprocesado de su demo."""
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).parents[1]
REPO = ROOT / "modelos" / "MotionAGFormer"
CKPT = ROOT / "modelos" / "motionagformer_pesos" / "motionagformer-b-h36m.pth.tr"
N = 243
_LEFT, _RIGHT = [1, 2, 3, 14, 15, 16], [4, 5, 6, 11, 12, 13]
_ARGS = dict(n_layers=16, dim_in=3, dim_feat=128, dim_rep=512, dim_out=3, mlp_ratio=4,
             act_layer=torch.nn.GELU, attn_drop=0.0, drop=0.0, drop_path=0.0, use_layer_scale=True,
             layer_scale_init_value=1e-5, use_adaptive_fusion=True, num_heads=8, qkv_bias=False,
             qkv_scale=None, hierarchical=False, use_temporal_similarity=True, neighbour_num=2,
             temporal_connection_len=1, use_tcn=False, graph_only=False, n_frames=N)


def _flip(x):
    out = x.copy()
    out[..., 0] *= -1
    out[..., _LEFT + _RIGHT, :] = out[..., _RIGHT + _LEFT, :]
    return out


def _resample(n):
    return np.clip(np.floor(np.linspace(0, n, N, endpoint=False)), 0, n - 1).astype(int)


class Lifter:
    def __init__(self, device: str | None = None, ckpt: Path = CKPT):
        if str(REPO) not in sys.path:
            sys.path.insert(0, str(REPO))
        from model.MotionAGFormer import MotionAGFormer

        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        safe = [(np._core.multiarray.scalar, "numpy.core.multiarray.scalar"), np.dtype,
                np.dtypes.Float64DType, np.dtypes.Float32DType]
        with torch.serialization.safe_globals(safe):
            state = torch.load(ckpt, map_location="cpu", weights_only=True)["model"]
        state = {k.removeprefix("module."): v for k, v in state.items()}
        self.model = MotionAGFormer(**_ARGS)
        self.model.load_state_dict(state, strict=True)
        self.model.to(self.device).eval()

    @torch.no_grad()
    def _run(self, clips):
        """(B, N, 17, 3) → (B, N, 17, 3): media de la predicción y la del volteo, todo en un lote."""
        x = np.concatenate([clips, _flip(clips)]).astype("float32")
        y = self.model(torch.from_numpy(x).to(self.device)).cpu().numpy()
        return (y[:len(clips)] + _flip(y[len(clips):])) / 2

    def lift(self, uv: np.ndarray, conf: np.ndarray, w: int, h: int) -> np.ndarray:
        """uv (T, 17, 2) en píxeles y conf (T, 17) → (T, 17, 3) relativo a la pelvis, en unidades del modelo."""
        x = np.concatenate([uv, conf[..., None]], axis=-1).astype(float)
        x[..., :2] = x[..., :2] / w * 2 - [1, h / w]
        T = len(x)
        starts = list(range(0, T, N))
        idxs = [np.arange(N) if T - s >= N else _resample(T - s) for s in starts]
        ys = self._run(np.stack([x[s + i] for s, i in zip(starts, idxs)]))
        out = np.empty((T, 17, 3))
        for s, i, y in zip(starts, idxs, ys):
            n = min(N, T - s)
            out[s:s + n] = y if n == N else y[np.unique(i, return_index=True)[1]]
        out -= out[:, :1]
        return out

    def lift_person(self, uv: np.ndarray, conf: np.ndarray, crop_factor: float = 2.0) -> np.ndarray:
        """Como `lift`, pero sobre un recorte cuadrado centrado en la pelvis de cada fotograma, de lado
        `crop_factor` × la altura mediana del jugador. Así el modelo ve al jugador al mismo tamaño
        relativo con el que fue entrenado, sea cual sea su tamaño en la imagen de TV."""
        height = np.nanmedian(uv[..., 1].max(axis=1) - uv[..., 1].min(axis=1))
        side = crop_factor * height
        local = uv - uv[:, :1] + side / 2
        return self.lift(local, conf, w=side, h=side)
