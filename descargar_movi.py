"""Descarga de MoVi (BioMotion Lab, Dataverse Borealis, doi:10.5683/SP2/JRHDRN).

Licencia: solo investigación, educación o arte NO comerciales; no se puede redistribuir ni ceder a
terceros. Al descargar aceptas sus términos (https://www.biomotionlab.ca/movi/). Citar:
Ghorbani et al., "MoVi: A large multi-purpose human motion and video dataset", PLoS ONE 16(6), 2021.

Uso:
  python descargar_movi.py 3d                → parámetros de cámara + 3D Visual3D de los 90 sujetos (3,8 GB)
  python descargar_movi.py video 1 2 3 ...   → vídeo de las dos cámaras fijas (PG1, PG2) de esos sujetos
  python descargar_movi.py video todos       → las dos cámaras fijas de todos (~45 GB)
"""
import json
import sys
import tarfile
import urllib.request
from pathlib import Path

try:                                   # proxies con certificado propio: usa el almacén del sistema
    import truststore
    truststore.inject_into_ssl()
except ImportError:
    pass

ROOT = Path(__file__).parent
DEST = ROOT / "datos" / "movi"
API = "https://borealisdata.ca/api"
DOI = "doi:10.5683/SP2/JRHDRN"
TARS_3D = ("Camera Parameters.tar", "F_Subjects_1_45.tar", "F_Subjects_46_90.tar", "README.pdf")


def file_index() -> dict[str, tuple[int, int]]:
    """nombre → (id de Dataverse, tamaño en bytes)."""
    meta = json.load(urllib.request.urlopen(f"{API}/datasets/:persistentId/?persistentId={DOI}", timeout=60))
    return {f["dataFile"]["filename"]: (f["dataFile"]["id"], f["dataFile"]["filesize"])
            for f in meta["data"]["latestVersion"]["files"]}


def bajar(name: str, index: dict, dest_dir: Path) -> Path:
    fid, size = index[name]
    dest = dest_dir / name
    if dest.exists() and dest.stat().st_size == size:
        print("ya está:", name, flush=True)
        return dest
    dest_dir.mkdir(parents=True, exist_ok=True)
    print(f"descargando {name} ({size / 1e6:.0f} MB)", flush=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    urllib.request.urlretrieve(f"{API}/access/datafile/{fid}", tmp)
    assert tmp.stat().st_size == size, f"tamaño inesperado en {name}"
    tmp.replace(dest)
    return dest


def extraer(tar_path: Path, dest_dir: Path):
    """Extrae solo ficheros regulares con rutas relativas seguras (sin '..' ni absolutas)."""
    with tarfile.open(tar_path) as t:
        miembros = [m for m in t.getmembers()
                    if m.isfile() and not Path(m.name).is_absolute() and ".." not in Path(m.name).parts]
        t.extractall(dest_dir, members=miembros, filter="data")


def main():
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    index = file_index()
    if sys.argv[1] == "3d":
        for name in TARS_3D:
            p = bajar(name, index, DEST / "zip")
            if p.suffix == ".tar":
                extraer(p, DEST / "3d")
    elif sys.argv[1] == "video":
        subjects = range(1, 91) if sys.argv[2:] == ["todos"] else [int(s) for s in sys.argv[2:]]
        for s in subjects:
            for cam in ("PG1", "PG2"):
                name = f"F_{cam}_Subject_{s}_L.avi"
                if name in index:
                    bajar(name, index, DEST / "video")
                else:
                    print("no existe en MoVi:", name)
    print("Listo.")


if __name__ == "__main__":
    main()
