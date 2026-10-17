"""Degradación de vídeo de referencia a condiciones de retransmisión."""
import cv2
import numpy as np


def scale_for_height(bbox_height_px: float, target_px: float) -> float:
    """Factor de escala para que la persona mida `target_px` de alto."""
    return target_px / bbox_height_px


def degrade_frame(img: np.ndarray, scale: float, blur_px: int, jpeg_quality: int | None) -> np.ndarray:
    """Reduce la resolución, aplica desenfoque de movimiento horizontal y compresión JPEG."""
    out = img
    if scale != 1.0:
        size = (max(1, round(img.shape[1] * scale)), max(1, round(img.shape[0] * scale)))
        out = cv2.resize(out, size, interpolation=cv2.INTER_AREA)
    if blur_px > 0:
        kernel = np.full((1, blur_px), 1.0 / blur_px, dtype=np.float32)
        out = cv2.filter2D(out, -1, kernel, borderType=cv2.BORDER_REFLECT)
    if jpeg_quality is not None:
        ok, buf = cv2.imencode(".jpg", out, [cv2.IMWRITE_JPEG_QUALITY, jpeg_quality])
        out = cv2.imdecode(buf, cv2.IMREAD_UNCHANGED)
    return out


def subsample(x: np.ndarray, fps_in: float, fps_out: float) -> tuple[np.ndarray, float]:
    """Se queda con 1 de cada k elementos (eje 0). k = fps_in / fps_out debe ser entero."""
    k = fps_in / fps_out
    if abs(k - round(k)) > 1e-9:
        raise ValueError(f"fps_in/fps_out = {k:.3f} no es entero; no se puede submuestrear sin interpolar")
    return x[:: int(round(k))], fps_out
