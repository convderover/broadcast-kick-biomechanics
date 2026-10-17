"""Escritura de vídeo H.264 (yuv420p), que se reproduce en navegadores, móviles y redes sociales."""
from pathlib import Path

import cv2
import imageio_ffmpeg
import numpy as np


def figure_to_rgb(fig) -> np.ndarray:
    """Figura de matplotlib → imagen RGB (H, W, 3) uint8."""
    fig.canvas.draw()
    return np.asarray(fig.canvas.buffer_rgba())[..., :3].copy()


class Mp4:
    """Uso:  with Mp4(path, fps) as v: v.write(rgb)  — el tamaño lo fija el primer fotograma (se rellena a par)."""

    def __init__(self, path: str | Path, fps: float, quality: int = 8):
        self.path, self.fps, self.quality = str(path), fps, quality
        self._gen, self._size = None, None

    def __enter__(self):
        return self

    def write(self, rgb: np.ndarray):
        if self._gen is None:
            h, w = rgb.shape[:2]
            self._size = (w + w % 2, h + h % 2)
            self._gen = imageio_ffmpeg.write_frames(self.path, self._size, fps=self.fps, codec="libx264",
                                                    pix_fmt_out="yuv420p", quality=self.quality,
                                                    macro_block_size=2)
            self._gen.send(None)
        if (rgb.shape[1], rgb.shape[0]) != self._size:
            canvas = np.zeros((self._size[1], self._size[0], 3), np.uint8)
            h, w = min(rgb.shape[0], self._size[1]), min(rgb.shape[1], self._size[0])
            canvas[:h, :w] = rgb[:h, :w]
            rgb = canvas
        self._gen.send(np.ascontiguousarray(rgb, dtype=np.uint8))

    def close(self):
        if self._gen is not None:
            self._gen.close()

    def __exit__(self, *exc):
        self.close()


def _font(size: int, bold: bool = False):
    from matplotlib import font_manager
    from PIL import ImageFont
    path = font_manager.findfont(font_manager.FontProperties(family="DejaVu Sans", weight="bold" if bold else "normal"))
    return ImageFont.truetype(path, size)


def put_text(img: np.ndarray, text: str, xy, size: int = 22, color=(232, 237, 243), bold: bool = False,
             anchor: str = "la") -> np.ndarray:
    """Texto Unicode (acentos, °, ¿) sobre una imagen RGB; devuelve la imagen."""
    from PIL import Image, ImageDraw
    im = Image.fromarray(img)
    ImageDraw.Draw(im).text(xy, text, font=_font(size, bold), fill=tuple(color), anchor=anchor)
    img[:] = np.asarray(im)
    return img


def title_card(text: str, sub: str = "", size=(1280, 720), seconds: float = 2.5, fps: float = 25,
               bg=(15, 23, 36), fg=(232, 237, 243), accent=(255, 138, 61)) -> list[np.ndarray]:
    """Fotogramas RGB de una cartela de título (líneas separadas por saltos de línea)."""
    img = np.zeros((size[1], size[0], 3), np.uint8)
    img[:] = bg
    scale = size[0] / 1280
    lines, subs = text.splitlines(), (sub.splitlines() if sub else [])
    y = size[1] / 2 - (len(lines) * 70 + len(subs) * 42) * scale / 2
    for line in lines:
        put_text(img, line, (size[0] / 2, y), int(52 * scale), fg, bold=True, anchor="ma")
        y += 70 * scale
    y += 10 * scale
    for line in subs:
        put_text(img, line, (size[0] / 2, y), int(28 * scale), accent, anchor="ma")
        y += 42 * scale
    return [img] * int(round(seconds * fps))
