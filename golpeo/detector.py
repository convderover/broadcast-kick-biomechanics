"""Modelos 2D de OpenMMLab (RTMW-x y YOLOX-m) con onnxruntime, en GPU cuando la hay."""
from pathlib import Path

import torch  # noqa: F401  (carga las DLL de CUDA/cuDNN que necesita onnxruntime-gpu en Windows)
import onnxruntime as ort

ort.set_default_logger_severity(3)       # solo errores (los avisos de nodos en CPU no aportan)

ROOT = Path(__file__).parents[1]
RTMW = ROOT / "modelos" / "rtmw" / "end2end.onnx"
YOLOX = ROOT / "modelos" / "yolox" / "20230928" / "yolox_onnx" / "yolox_m_8xb8-300e_humanart-c2c7a14a" / "end2end.onnx"


def device() -> str:
    return "cuda" if "CUDAExecutionProvider" in ort.get_available_providers() else "cpu"


def rtmw():
    """RTMW-x 384×288 (cuerpo completo; los 17 primeros puntos siguen el orden COCO)."""
    from rtmlib import RTMPose
    return RTMPose(str(RTMW), model_input_size=(288, 384), backend="onnxruntime", device=device())


def yolox():
    """Detector de personas YOLOX-m (HumanArt) 640×640."""
    from rtmlib import YOLOX as _YOLOX
    return _YOLOX(str(YOLOX), model_input_size=(640, 640), backend="onnxruntime", device=device())
