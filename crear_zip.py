"""Empaqueta el proyecto (código, documentos, resultados y el prototipo del radar) sin modelos ni datos.
Uso:  python crear_zip.py   → ../proyecto_golpeo_laliga_<fecha>.zip
"""
import datetime
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent
DEMO = ROOT.parent
EXCLUIR = {"modelos", "datos", "__pycache__", ".pytest_cache"}


def archivos(base):
    for p in sorted(base.rglob("*")):
        if p.is_file() and not EXCLUIR & set(p.relative_to(base).parts):
            yield p


def main():
    dest = DEMO / f"proyecto_golpeo_laliga_{datetime.date.today():%Y-%m-%d}.zip"
    with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as z:
        for carpeta in ("postura_golpeo", "radar_balon"):
            for p in archivos(DEMO / carpeta):
                z.write(p, Path(carpeta) / p.relative_to(DEMO / carpeta))
    print(dest, f"{dest.stat().st_size / 1e6:.1f} MB")


if __name__ == "__main__":
    main()
