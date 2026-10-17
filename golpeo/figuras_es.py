"""Figuras en dos idiomas: se dibujan en inglés y, tras guardarlas, se traducen los textos (títulos, ejes,
leyendas, anotaciones, marcas) y se pone coma decimal en los números para la versión en español.

Uso:  save_fig(fig, "fig4_sensitivity.png")  → resultados/paper/… (inglés) y resultados/paper_es/… (español)
"""
import re
from pathlib import Path

import matplotlib.text
from matplotlib.ticker import FixedFormatter, Formatter, NullFormatter

ROOT = Path(__file__).parents[1]
OUT_EN = ROOT / "resultados" / "paper"
OUT_ES = ROOT / "resultados" / "paper_es"
_DECIMAL = re.compile(r"(?<=\d)\.(?=\d)")
_THOUSANDS = re.compile(r"(?<=\d) (?=\d{3}\b)")          # «6 000» → «6.000»

FEATURES = {
    "Support-knee flexion at contact": "Flexión rodilla apoyo (contacto)",
    "Support-knee flexion": "Flexión rodilla de apoyo",
    "Kicking-knee peak flexion": "Flexión máx. rodilla de golpeo",
    "Kicking-hip peak extension": "Extensión máx. cadera de golpeo",
    "Kicking-hip range of motion": "Rango de cadera de golpeo",
    "Trunk sagittal lean at contact": "Inclinación sagital del tronco",
    "Trunk lateral lean at contact": "Inclinación lateral del tronco",
    "Peak hip-flexor moment": "Momento flexor máx. de cadera",
    "Peak knee-extensor moment": "Momento extensor máx. de rodilla",
    "Peak knee-flexor moment (pre-contact)": "Momento flexor máx. de rodilla (pre-contacto)",
}

# frases (de más larga a más corta al aplicarlas); las claves pueden contener saltos de línea
PHRASES = {
    # comunes
    "Player height in image, H (px)": "Altura del jugador en la imagen, H (px)",
    "Player height (px)": "Altura del jugador (px)",
    "Time relative to ball contact (ms)": "Tiempo respecto al contacto con el balón (ms)",
    "Time relative to contact (ms)": "Tiempo respecto al contacto (ms)",
    "ms relative to contact": "ms respecto al contacto",
    "camera view": "vista de cámara",
    "frontal": "frontal", "lateral": "lateral", "rear": "espalda",
    "MAE (°)": "EAM (°)",
    "MAE vs motion capture (°)": "EAM frente a captura óptica (°)",
    "MAE predicted by simulation (°)": "EAM predicho por la simulación (°)",
    "MAE on real video (°)": "EAM en vídeo real (°)",
    "Mean abs. error, 6 features (°)": "Error abs. medio, 6 rasgos (°)",
    "ICC(2,1)": "CCI(2,1)",
    "ICC": "CCI",
    "official weights": "pesos oficiales",
    "kick- & broadcast-adapted": "adaptado al golpeo y a la TV",
    "motion capture": "captura óptica",
    "Motion capture": "Captura óptica",
    "reconstruction": "reconstrucción",
    "Reconstruction": "Reconstrucción",
    "laboratory": "laboratorio",
    # fig 2 contacto
    "a  Ankle-speed peak (dots) precedes contact": "a  El pico del tobillo (puntos) precede al contacto",
    "Kicking-ankle speed (m/s)": "Velocidad del tobillo de golpeo (m/s)",
    "ball contact\n(extrapolated)": "contacto con el balón\n(extrapolado)",
    "one frame\nat 25 fps": "un fotograma\na 25 fps",
    "Ankle peak − contact (ms)": "Pico del tobillo − contacto (ms)",
    "b  Offset:": "b  Desfase:",
    # fig 3 error 2D
    "a  Detector error vs player size": "a  Error del detector frente al tamaño",
    "2D error, RMS per axis (% of H)": "Error 2D, RMS por eje (% de H)",
    "broadcast (3DSP, RTMW-x)": "retransmisión (3DSP, RTMW-x)",
    "lab video (MoVi, RTMW-x)": "vídeo de laboratorio (MoVi, RTMW-x)",
    "fit σ": "ajuste σ",
    "b  Broadcast, by joint": "b  Retransmisión, por articulación",
    "hips": "caderas", "knees": "rodillas", "ankles": "tobillos", "shoulders": "hombros", "elbows": "codos",
    "wrists": "muñecas",
    # fig 4 / S
    "Virtual broadcast camera · MoVi kicks": "Cámara de TV virtual · golpeos de MoVi",
    "Virtual broadcast camera · real ball kicks (CMU,": "Cámara de TV virtual · golpeos reales de balón (CMU,",
    "25 fps · broadcast 2D residuals": "25 fps · residuos 2D de retransmisión",
    # ablación
    "a  2D noise model (25 fps)": "a  Ruido 2D (25 fps)",
    "b  Frame rate": "b  Frecuencia de imagen",
    "c  Contact instant (25 fps)": "c  Instante de contacto (25 fps)",
    "Gaussian i.i.d.": "gaussiano independiente",
    "broadcast residuals": "residuos de retransmisión",
    "none": "ninguno", "known": "conocido", "automatic": "automático",
    # fiabilidad
    "Agreement between participants (MoVi, n =": "Acuerdo entre participantes (MoVi, n =",
    # vídeo real y gemelo
    "a  Real video (MoVi,": "a  Vídeo real (MoVi,",
    "subjects × 2 cameras)": "participantes × 2 cámaras)",
    "native\n(~300 px)": "nativa\n(~300 px)",
    "b  Digital twin of each recording": "b  Gemelo digital de cada grabación",
    "no 2D noise": "sin ruido 2D",
    "lab-video residuals": "residuos de vídeo de laboratorio",
    # cargas
    "a  Lab reference": "a  Laboratorio",
    "MoVi (air kicks)": "MoVi (golpeos al aire)",
    "CMU (ball kicks)": "CMU (golpeos de balón)",
    "Peak kicking-ankle speed (m/s)": "Velocidad máx. del tobillo de golpeo (m/s)",
    "Peak hip-flexor moment (N·m/kg)": "Momento flexor máx. de cadera (N·m/kg)",
    "b  From video:": "b  Desde vídeo:",
    "virtual TV camera": "cámara de TV virtual",
    "real video, 80 px": "vídeo real, 80 px",
    "Lab (N·m/kg)": "Laboratorio (N·m/kg)",
    "From 80-px video (N·m/kg)": "Desde vídeo de 80 px (N·m/kg)",
    "c  Injury-study size": "c  Tamaño del estudio de lesiones",
    "Reliability λ of the score": "Fiabilidad λ del índice",
    "Injuries needed (α 0.05, power 0.8)": "Lesiones necesarias (α 0,05; potencia 0,8)",
    "1 LaLiga season,": "1 temporada de LaLiga,",
    "inj./player": "les./jugador",
    "inverse\ndynamics\nfrom TV": "dinámica\ninversa\ndesde TV",
    "inverse\ndynamics": "dinámica\ninversa",
    "posture\nsurrogate": "sustituto\npostural",
    "Injuries needed\n(α 0.05, power 0.8)": "Lesiones necesarias\n(α 0,05; potencia 0,8)",
    "posture\nsurrogate\nfrom TV": "sustituto\npostural\ndesde TV",
    # mejoras
    "a  Error": "a  Error",
    "b  Agreement between subjects": "b  Acuerdo entre participantes",
    "single view lateral + bias correction": "una vista lateral + corrección de sesgo",
    "single view lateral": "una vista lateral",
    "3 replays (45°–135°) + bias correction": "3 repeticiones (45°–135°) + corrección de sesgo",
    "3 replays (45°–135°)": "3 repeticiones (45°–135°)",
    "good": "bueno",
    # ajuste
    "a  Virtual camera,\n    unseen MoVi participants": "a  Cámara virtual,\n    MoVi no vistos",
    "b  Virtual camera,\n    real ball kicks (CMU)": "b  Cámara virtual,\n    balón real (CMU)",
    "c  Real video downscaled\n    to 80 px (unseen)": "c  Vídeo real a 80 px\n    (no visto)",
    # intensidad
    "MoVi air kicks": "golpeos al aire de MoVi",
    "CMU ball kicks": "golpeos de balón de CMU",
    "Lifter error without 2D noise": "Error del elevador sin ruido 2D",
    # figura 1 (diseño)
    "Laboratory\nground truth": "Referencia de\nlaboratorio",
    "Broadcast\nvideo": "Vídeo de\nretransmisión",
    "2D → 3D\nreconstruction": "Reconstrucción\n2D → 3D",
    "Agreement\nwith the lab": "Acuerdo con el\nlaboratorio",
    "optical motion capture": "captura óptica de movimiento",
    "CMU · 7 ball kicks": "CMU · 7 golpeos de balón",
    "MoVi · 83 participants": "MoVi · 83 participantes",
    "real 2D-detector residuals": "residuos reales del detector 2D",
    "+ real video (digital twin)": "+ vídeo real (gemelo digital)",
    "RTMW-x 2D detector": "detector 2D RTMW-x",
    "official vs fine-tuned": "oficial frente a ajustado",
    "6 joint angles · 3 moments": "6 ángulos · 3 momentos",
    "bias · MAE · LoA · ICC": "sesgo · EAM · LdA · CCI",
    "→ injury-study sample size": "→ tamaño del estudio de lesiones",
    "≥ 0.75 · 0.5–0.75\n· < 0.5": "≥ 0,75 · 0,5–0,75\n· < 0,5",
    "moderate": "moderado", "poor": "pobre",
    "Laboratory ground truth": "Referencia de laboratorio",
    "Broadcast conditions": "Condiciones de retransmisión",
    "3D reconstruction": "Reconstrucción 3D",
    "Agreement with the lab": "Acuerdo con el laboratorio",
    "optical motion capture · 120 Hz": "captura óptica · 120 Hz",
    "CMU: 7 ball kicks": "CMU: 7 golpeos de balón",
    "MoVi: 83 participants": "MoVi: 83 participantes",
    "virtual camera": "cámara virtual",
    "5 views × 5 sizes × 25/50 fps": "5 vistas × 5 tamaños × 25/50 fps",
    "real detector residuals from\n200 Premier League shots": "residuos reales del detector en\n200 disparos de la Premier",
    "real video + synchronised 3D": "vídeo real + 3D sincronizada",
    "2 calibrated cameras · digital twin": "2 cámaras calibradas · gemelo digital",
    "MotionAGFormer lifter": "elevador MotionAGFormer",
    "2D keypoints": "puntos 2D",
    "6 kinematic features": "6 rasgos cinemáticos",
    "3 swing-leg joint moments": "3 momentos de la pierna de golpeo",
    "bias · MAE · limits of agreement · ICC": "sesgo · EAM · límites de acuerdo · CCI",
    "injury-study size": "tamaño del estudio de lesiones",
    "lab": "lab.", "estimate": "estimado",
    # figura del modelo
    "a  End of backswing": "a  Final del armado",
    "b  Peak knee flexion": "b  Flexión máx. de rodilla",
    "c  Ball contact": "c  Contacto con el balón",
    "d  Contact, frontal view": "d  Contacto, vista frontal",
    "e  Swing-leg free-body diagram (−50 ms)": "e  Diagrama de cuerpo libre (−50 ms)",
    "f  Net joint moments, kicking leg": "f  Momentos articulares netos, pierna de golpeo",
    "segment centre of mass (de Leva 1996)": "centro de masas del segmento (de Leva 1996)",
    "segment weight, m·g": "peso del segmento, m·g",
    "joint reaction force": "fuerza de reacción articular",
    "net joint moment": "momento articular neto",
    "Newton–Euler, open chain:\nno force plate needed": "Newton–Euler, cadena abierta:\nsin plataforma de fuerzas",
    "a  Backswing (peak knee flexion)": "a  Armado (flexión máx. de rodilla)",
    "b  Ball contact": "b  Contacto con el balón",
    "c  Contact, frontal view": "c  Contacto, vista frontal",
    "d  Swing-leg free-body diagram": "d  Diagrama de cuerpo libre",
    "e  Net joint moments": "e  Momentos articulares netos",
    "kicking-knee\nflexion": "flexión\nrodilla\nde golpeo",
    "kicking-hip\nextension": "extensión\ncadera\nde golpeo",
    "support-knee\nflexion": "flexión\nrodilla\nde apoyo",
    "trunk\nsagittal lean": "inclinación\nsagital tronco",
    "trunk lateral\nlean": "inclinación\nlateral tronco",
    "Hip (+ flexor), N·m/kg": "Cadera (+ flexor), N·m/kg",
    "Knee (+ extensor), N·m/kg": "Rodilla (+ extensor), N·m/kg",
    "full kick (10_01)": "golpeo fuerte (10_01)",
    "slow kick (10_04)": "golpeo lento (10_04)",
    "backswing → contact": "armado → contacto",
    "last 100 ms": "últimos 100 ms",
    "last\n100 ms": "últimos\n100 ms",
    "Hip (N·m/kg)\n+ flexor / − extensor": "Cadera (N·m/kg)\n+ flexor / − extensor",
    "Knee (N·m/kg)\n+ extensor / − flexor": "Rodilla (N·m/kg)\n+ extensor / − flexor",
    r"$\mathbf{F}_{hip}$": r"$\mathbf{F}_{cadera}$", r"$M_{hip}$": r"$M_{cadera}$", r"$M_{knee}$": r"$M_{rodilla}$",
    "peak hip flexor": "pico flexor de cadera",
    "peak knee extensor": "pico extensor de rodilla",
    "peak knee flexor": "pico flexor de rodilla",
    # figura de reconstrucción
    "Motion capture (truth)": "Captura óptica (verdad)",
    "TV input, lateral, 80 px": "Entrada TV, lateral, 80 px",
    "3D from lateral camera": "3D desde cámara lateral",
    "3D from frontal camera": "3D desde cámara frontal",
    "Lateral camera · kicking-knee flexion (°)": "Cámara lateral · flexión rodilla de golpeo (°)",
    "Lateral camera · kicking-hip flexion (°)": "Cámara lateral · flexión cadera de golpeo (°)",
    "Frontal camera · kicking-knee flexion (°)": "Cámara frontal · flexión rodilla de golpeo (°)",
    "Frontal camera · kicking-hip flexion (°)": "Cámara frontal · flexión cadera de golpeo (°)",
    "lab (mean ± SD, n =": "laboratorio (media ± DE, n =",
    "from TV (mean ± SD)": "desde TV (media ± DE)",
    "SPM difference, p < 0.05": "diferencia SPM, p < 0,05",
    "Motion\ncapture\n(truth)": "Captura\nóptica\n(verdad)",
    "TV input\nlateral\n80 px": "Entrada\nTV lateral\n80 px",
    "3D from\nlateral\ncamera": "3D desde\ncámara\nlateral",
    "3D from\nfrontal\ncamera": "3D desde\ncámara\nfrontal",
    "grey/orange: motion capture   ·   blue: 3D reconstructed from one TV camera (80 px, 25 fps, broadcast 2D noise)":
        "gris/naranja: captura óptica   ·   azul: 3D reconstruida desde una cámara de TV (80 px, 25 fps, "
        "ruido 2D de retransmisión)",
    # Bland–Altman
    "Mean of lab and video (°)": "Media de laboratorio y vídeo (°)",
    # ejemplo de campo
    "Swing-leg joint load relative to this player's strongest kick": "Carga articular de la pierna de golpeo respecto a su golpeo más fuerte",
    "1 (max)": "1 (máx.)",
    "Swing-leg joint load\nrelative to this player's strongest kick": "Carga articular de la pierna de golpeo\nrespecto a su golpeo más fuerte",
    "end of backswing": "final del armado", "peak hip-flexor load": "pico de carga flexora de cadera",
    "ball contact": "contacto con el balón", "follow-through": "final del golpeo",
    "Kicking-knee flexion (°)": "Flexión rodilla de golpeo (°)", "Kicking-hip flexion (°)": "Flexión cadera de golpeo (°)",
    "Peak kicking-ankle speed (m/s)": "Velocidad máx. del tobillo de golpeo (m/s)",
    "lab ball\nkicks": "balón en\nlaboratorio",
    "diag.\nfront": "diag.\ndelante", "diag.\nbehind": "diag.\natrás",
    "diagonal front": "diagonal delante", "diagonal behind": "diagonal atrás",
    "kick": "golpeo", "strong": "fuerte", "soft": "suave", "native": "nativa", "front": "frente", "Kick": "Golpeo", "hip": "cadera", "knee": "rodilla",
    "Video − lab (°)": "Vídeo − laboratorio (°)",
    "bias": "sesgo",
    "LoA": "LdA",
}
for en, es in FEATURES.items():
    PHRASES.setdefault(en, es)
    PHRASES.setdefault(en.replace(" at contact", "\nat contact"), es.replace(" en el contacto", "\nen el contacto"))
_ORDERED = sorted(PHRASES.items(), key=lambda kv: -len(kv[0]))


def translate(text: str) -> str:
    if text in PHRASES:
        out = PHRASES[text]
    else:
        out = text
        for en, es in _ORDERED:
            if len(en) <= 5:                                   # palabras cortas: solo como palabra completa
                out = re.sub(rf"(?<![\w-]){re.escape(en)}(?![\w-])", es, out)
            elif en in out:
                out = out.replace(en, es)
    out = _DECIMAL.sub(",", out)
    return _THOUSANDS.sub(".", out)


class _Translated(Formatter):
    """Envuelve el formateador original de un eje: mismas marcas, texto traducido y con coma decimal."""

    def __init__(self, inner):
        self.inner = inner

    def set_axis(self, axis):
        super().set_axis(axis)
        self.inner.set_axis(axis)

    def set_locs(self, locs):
        self.inner.set_locs(locs)

    def __call__(self, x, pos=None):
        return translate(self.inner(x, pos))

    def get_offset(self):
        return translate(self.inner.get_offset())


def localize(fig):
    """Traduce in situ una figura ya dibujada (después de guardar la versión inglesa)."""
    fig.canvas.draw()
    for t in fig.findobj(matplotlib.text.Text):
        s = t.get_text()
        if s:
            t.set_text(translate(s))
    for ax in fig.axes:
        for axis in (ax.xaxis, ax.yaxis) + ((ax.zaxis,) if hasattr(ax, "zaxis") else ()):
            fmt = axis.get_major_formatter()
            if isinstance(fmt, FixedFormatter):
                axis.set_major_formatter(FixedFormatter([translate(str(s)) for s in fmt.seq]))
            elif not isinstance(fmt, NullFormatter):
                axis.set_major_formatter(_Translated(fmt))


def save_fig(fig, name: str, **kw):
    OUT_EN.mkdir(parents=True, exist_ok=True)
    OUT_ES.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT_EN / name, **kw)
    localize(fig)
    fig.savefig(OUT_ES / name, **kw)
