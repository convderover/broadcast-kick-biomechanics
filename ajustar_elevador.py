"""Ajuste del elevador 3D (MotionAGFormer-B) al golpeo con ruido de retransmisión.

Datos de entrenamiento sintéticos y "a la carta": la captura óptica de MoVi (los 21 movimientos de cada sujeto
de entrenamiento, con la mitad de las muestras centradas en su golpeo) filmada por la cámara virtual con
  - azimut 0–360°, elevación 5–25°, distancia 15–60 m, jugador de 40 a 400 px, 25 o 50 fps;
  - 2D con residuos reales de RTMW en la Premier League (60 %), gaussiano σ(H) (20 %) o exacto (20 %);
  - volteo izquierda/derecha aleatorio.
El objetivo es la 3D "en espacio imagen" relativa a la pelvis, el mismo convenio del entrenamiento original
(comprobado: la salida del modelo oficial coincide en escala, 0,99–1,01). Pérdida de MotionAGFormer:
MPJPE + 0,5·N-MPJPE + 20·velocidad.

Validación cruzada por sujetos en 2 pliegues (sujetos de índice par / impar): el modelo del pliegue k nunca
ve a los sujetos del pliegue k. Los golpeos de CMU (con balón) no se usan nunca para entrenar.
MoVi tiene licencia de investigación no comercial: estos pesos no sirven para un producto.

Uso:  python ajustar_elevador.py PLIEGUE [iteraciones, 1000 por defecto]   → modelos/ajustado/fold{PLIEGUE}.pth.tr
"""
import json
import re
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from golpeo.camara import CONF, camera_view, image_space_3d
from golpeo.datos_movi import load_movi
from golpeo.ensayos import fill_gaps
from golpeo.elevador import _ARGS, _flip, CKPT, N, REPO
from golpeo.ruido import ResidualBank

ROOT = Path(__file__).parent
OUT = ROOT / "modelos" / "ajustado"
MOVI3D = ROOT / "datos" / "movi" / "3d"
BATCH = 8
LR = 5e-5


def subject_ids():
    return sorted(int(re.findall(r"(\d+)\.mat", p.name)[0]) for p in MOVI3D.glob("F_Subjects_*/F_v3d_Subject_*.mat"))


def folds():
    """Sujetos de MoVi con golpeo útil (los mismos que en la sensibilidad), repartidos en 2 pliegues por orden."""
    from golpeo.ensayos import movi_trials
    ids = sorted(int(e.subject) for e in movi_trials())
    return {0: ids[0::2], 1: ids[1::2]}


def load_training(subjects):
    paths = {int(re.findall(r"(\d+)\.mat", p.name)[0]): p for p in MOVI3D.glob("F_Subjects_*/F_v3d_Subject_*.mat")}
    data = []
    for s in subjects:
        full = load_movi(paths[s], margin_s=1e6)                 # toda la grabación (21 movimientos)
        kick = load_movi(paths[s])                               # ventana del golpeo
        x, _ = fill_gaps(full.x17, full.fps)                     # huecos cortos rellenos; los largos quedan NaN
        x = x.astype(np.float32)
        ok = np.isfinite(x).all(axis=(1, 2))
        data.append(dict(x=x, ok=ok, kick=(kick.frame0, kick.frame0 + len(kick.x17))))
    return data


class Sampler:
    def __init__(self, data, bank, sigma, rng):
        self.data, self.bank, self.sigma, self.rng = data, bank, sigma, rng

    def window(self):
        rng = self.rng
        while True:
            d = self.data[rng.integers(len(self.data))]
            fps = rng.choice([25.0, 50.0])
            span = int(np.ceil(N / fps * 120)) + 2                # fotogramas de captura que cubre la ventana
            if rng.random() < 0.5:                               # centrada en el golpeo
                a, b = d["kick"]
                centre = rng.integers(a, max(a + 1, b))
                start = int(np.clip(centre - span // 2 + rng.integers(-span // 4, span // 4 + 1), 0, len(d["x"]) - span))
            else:
                start = int(rng.integers(0, max(1, len(d["x"]) - span)))
            seg = d["x"][start:start + span]
            if len(seg) < span or not d["ok"][start:start + span].all():
                continue
            t = np.arange(N) / fps * 120
            i0 = np.floor(t).astype(int)
            w = (t - i0)[:, None, None]
            return seg[i0] * (1 - w) + seg[np.minimum(i0 + 1, span - 1)] * w, fps

    def sample(self):
        rng = self.rng
        x17, fps = self.window()
        h = float(np.exp(rng.uniform(np.log(40), np.log(400))))
        uv, xc, focal = camera_view(x17, rng.uniform(0, 360), rng.uniform(5, 25), h, rng.uniform(15, 60))
        target = image_space_3d(uv, xc, focal)
        u = rng.random()
        if u < 0.6:
            uv = uv + self.bank.sample(N, fps, h, rng)
        elif u < 0.8:
            uv = uv + rng.normal(0, np.hypot(self.sigma[0] * h, self.sigma[1]), uv.shape)
        side = 2.0 * np.nanmedian(uv[..., 1].max(axis=1) - uv[..., 1].min(axis=1))
        inp = np.concatenate([(uv - uv[:, :1]) * 2 / side, np.full((N, 17, 1), CONF)], axis=-1)
        target = target * 2 / side
        if rng.random() < 0.5:
            inp, target = _flip(inp), _flip(target)
        return inp.astype(np.float32), target.astype(np.float32)

    def batch(self, n):
        xs, ys = zip(*(self.sample() for _ in range(n)))
        return torch.from_numpy(np.stack(xs)), torch.from_numpy(np.stack(ys))


def build_model(device):
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from model.MotionAGFormer import MotionAGFormer
    safe = [(np._core.multiarray.scalar, "numpy.core.multiarray.scalar"), np.dtype,
            np.dtypes.Float64DType, np.dtypes.Float32DType]
    with torch.serialization.safe_globals(safe):
        state = torch.load(CKPT, map_location="cpu", weights_only=True)["model"]
    model = MotionAGFormer(**_ARGS)
    model.load_state_dict({k.removeprefix("module."): v for k, v in state.items()}, strict=True)
    return model.to(device)


def forward_checkpointed(model, x):
    """Forward de MotionAGFormer recomputando cada bloque en el backward: 13,8 GB → <2 GB con lotes de 8."""
    from torch.utils.checkpoint import checkpoint
    x = model.joints_embed(x) + model.pos_embed
    for layer in model.layers:
        x = checkpoint(layer, x, use_reentrant=False)
    return model.head(model.rep_logit(model.norm(x)))


def losses(pred, y):
    if str(REPO) not in sys.path:
        sys.path.insert(0, str(REPO))
    from loss.pose3d import loss_mpjpe, loss_velocity, n_mpjpe
    return loss_mpjpe(pred, y) + 0.5 * n_mpjpe(pred, y) + 20.0 * loss_velocity(pred, y)


@torch.no_grad()
def val_mpjpe(model, batches, device):
    model.eval()
    errs = []
    for x, y in batches:
        x, y = x.to(device), y.to(device)
        pred = model(x)
        pred = pred - pred[..., :1, :]
        errs.append(torch.norm(pred - y, dim=-1).mean().item())
    model.train()
    return float(np.mean(errs))


def main():
    fold = int(sys.argv[1])
    iters = int(sys.argv[2]) if len(sys.argv) > 2 else 1000
    device = "cuda"
    torch.manual_seed(fold)
    f = folds()
    train_subjects, test_subjects = f[1 - fold], f[fold]
    print(f"pliegue {fold}: {len(train_subjects)} sujetos de entrenamiento, {len(test_subjects)} de prueba", flush=True)
    res = ROOT / "resultados"
    bank = ResidualBank.from_frame(pd.read_csv(res / "error2d_3dsp.csv"))
    m = json.loads((res / "modelo_ruido.json").read_text())
    sigma = (m["sigma_frac"], m["sigma_floor_px"])
    tr = Sampler(load_training(train_subjects), bank, sigma, np.random.default_rng(100 + fold))
    va = Sampler(load_training(test_subjects[:12]), bank, sigma, np.random.default_rng(200 + fold))
    val = [va.batch(BATCH) for _ in range(20)]               # validación fija: sujetos no vistos
    model = build_model(device)
    model.train()
    opt = torch.optim.AdamW(model.parameters(), lr=LR, weight_decay=0.01)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=iters, eta_min=LR / 20)
    scaler = torch.amp.GradScaler("cuda")
    log = [{"iter": 0, "val_mpjpe": val_mpjpe(model, val, device)}]
    print(f"inicio: MPJPE de validación {log[0]['val_mpjpe']:.4f} (unidades de altura del jugador)", flush=True)
    t0, running = time.time(), []
    for it in range(1, iters + 1):
        x, y = tr.batch(BATCH)
        x, y = x.to(device), y.to(device)
        with torch.autocast("cuda", dtype=torch.float16):
            pred = forward_checkpointed(model, x)
        pred = pred.float()
        pred = pred - pred[..., :1, :]
        loss = losses(pred, y)
        opt.zero_grad(set_to_none=True)
        scaler.scale(loss).backward()
        scaler.unscale_(opt)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(opt)
        scaler.update()
        sched.step()
        running.append(loss.item())
        if it % 250 == 0 or it == iters:
            v = val_mpjpe(model, val, device)
            log.append({"iter": it, "train_loss": float(np.mean(running)), "val_mpjpe": v})
            running = []
            print(f"iter {it}: pérdida {log[-1]['train_loss']:.4f}, MPJPE validación {v:.4f} ({time.time() - t0:.0f} s)",
                  flush=True)
            OUT.mkdir(parents=True, exist_ok=True)               # copia parcial por si se interrumpe
            torch.save({"model": model.state_dict(), "fold": fold, "iter": it, "train_subjects": train_subjects,
                        "test_subjects": test_subjects, "log": log}, OUT / f"fold{fold}_parcial.pth.tr")
    OUT.mkdir(parents=True, exist_ok=True)
    torch.save({"model": model.state_dict(), "fold": fold, "train_subjects": train_subjects,
                "test_subjects": test_subjects, "log": log}, OUT / f"fold{fold}.pth.tr")
    (OUT / f"fold{fold}_log.json").write_text(json.dumps(log, indent=1))


if __name__ == "__main__":
    main()
