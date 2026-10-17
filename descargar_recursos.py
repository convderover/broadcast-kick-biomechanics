"""Vuelve a descargar los modelos y datos que no van en el ZIP del proyecto (pesan ~500 MB y algunas
licencias no permiten redistribuirlos). Al descargar los datos aceptas sus licencias:
  - CMU Graphics Lab Motion Capture: libre para investigación; citar la base de datos.
  - 3DSP (AutoSoccerPose): repositorio Apache-2.0; las imágenes vienen de retransmisiones (SoccerNet),
    úsalas solo para investigación y no las publiques.
  - Modelos RTMW / YOLOX (OpenMMLab, Apache-2.0) y MotionAGFormer (Apache-2.0).

Uso:  python descargar_recursos.py
Además: pip install rtmlib==0.0.16 --no-deps  y  pip install ezc3d==1.7.2
MoVi (validación con vídeo real) se baja aparte: python descargar_movi.py 3d  y  python descargar_movi.py video todos
"""
import re
import subprocess
import urllib.request
import zipfile
from pathlib import Path

try:                                   # proxies con certificado propio: usa el almacén del sistema
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).parent
MODELOS, DATOS = ROOT / "modelos", ROOT / "datos"

ARCHIVOS = [  # (url, destino, tamaño exacto en bytes)
    ("https://download.openmmlab.com/mmpose/v1/projects/rtmposev1/onnx_sdk/yolox_m_8xb8-300e_humanart-c2c7a14a.zip",
     MODELOS / "yolox" / "yolox_m.zip", 94223081),
    ("https://download.openmmlab.com/mmpose/v1/projects/rtmw/onnx_sdk/rtmw-dw-x-l_simcc-cocktail14_270e-384x288_20231122.zip",
     MODELOS / "rtmw" / "rtmw_x.zip", 213433855),
    ("https://raw.githubusercontent.com/calvinyeungck/3D-Shot-Posture-Dataset/master/3dsp.zip",
     DATOS / "3dsp" / "3dsp.zip", 23496450),
] + [(f"http://mocap.cs.cmu.edu/subjects/10/10_0{i}.c3d", DATOS / "cmu" / f"10_0{i}.c3d", s)
     for i, s in zip(range(1, 7), (4292816, 3168608, 1953824, 2932080, 2348096, 3072704))] + [
    ("http://mocap.cs.cmu.edu/subjects/11/11_01.c3d", DATOS / "cmu" / "11_01.c3d", 3205904)]   # 2.º sujeto con balón

DRIVE_ID = "1Iii5EwsFFm9_9lKBUPfN8bV5LmfkNUMP"           # motionagformer-b-h36m.pth.tr, 141930389 bytes


def bajar(url, dest, size):
    if dest.exists() and dest.stat().st_size == size:
        print("ya está:", dest.name)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    print("descargando", dest.name)
    urllib.request.urlretrieve(url, dest)
    assert dest.stat().st_size == size, f"tamaño inesperado en {dest}"
    if dest.suffix == ".zip":
        zipfile.ZipFile(dest).extractall(dest.parent)


def bajar_drive(dest, size=141930389):
    if dest.exists() and dest.stat().st_size == size:
        print("ya está:", dest.name)
        return
    dest.parent.mkdir(parents=True, exist_ok=True)
    base = f"https://drive.usercontent.google.com/download?id={DRIVE_ID}&export=download"
    page = urllib.request.urlopen(base).read().decode("utf-8", "ignore")
    uuid = re.search(r'name="uuid" value="([^"]+)"', page).group(1)
    confirm = re.search(r'name="confirm" value="([^"]+)"', page).group(1)
    urllib.request.urlretrieve(f"{base}&confirm={confirm}&uuid={uuid}", dest)
    assert dest.stat().st_size == size, "tamaño inesperado en los pesos de MotionAGFormer"


def main():
    for url, dest, size in ARCHIVOS:
        bajar(url, dest, size)
    bajar_drive(MODELOS / "motionagformer_pesos" / "motionagformer-b-h36m.pth.tr")
    if not (MODELOS / "MotionAGFormer").exists():
        subprocess.run(["git", "clone", "--depth", "1", "https://github.com/TaatiTeam/MotionAGFormer.git",
                        str(MODELOS / "MotionAGFormer")], check=True)
    print("Listo.")


if __name__ == "__main__":
    main()
