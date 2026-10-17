"""Construye los documentos finales a partir de sus fuentes en Markdown:

  docs/manuscrito/manuscript.md    → docs/manuscrito/manuscript.pdf (Typst) y manuscript.docx (Word, para revistas)
  docs/manuscrito/manuscrito_es.md → la misma salida en español (manuscrito_es.pdf y .docx)
  docs/dossier/dossier_clubes.md   → docs/dossier/dossier_clubes.pdf (resumen de 2 páginas para clubes y LaLiga)

Numeración automática: en el texto se escriben marcas {{fig:nombre}}, {{tbl:nombre}} o {{figS:nombre}} y en cada
figura o tabla su etiqueta {#fig:nombre}, {#tbl:nombre} o {#figS:nombre}. Los números salen del orden de aparición
(las suplementarias, S1, S2…). La línea <!-- SUPLEMENTO --> marca dónde empiezan las figuras suplementarias.
{{REPO_URL}} se rellena con docs/config.json.

Necesita pypandoc_binary y typst (pip). Uso:  python generar_documentos.py
"""
import json
import re
from pathlib import Path

import pypandoc
import typst

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
CONFIG = json.loads((DOCS / "config.json").read_text(encoding="utf-8"))

PAPER_VARS = ["-V", "papersize=a4", "-V", "fontsize=10.5pt", "-V", "margin.x=2.2cm", "-V", "margin.y=2.3cm",
              "-V", "mainfont=Libertinus Serif", "-V", "linestretch=1.15"]
LABEL = re.compile(r"\{#(fig|figS|tbl):([\w-]+)")
SUPPLEMENT_TYPST = """```{=typst}
#counter(figure.where(kind: image)).update(0)
#set figure(numbering: n => "S" + str(n))
```"""


RES = ROOT / "resultados" / "paper"
FEATURES = {   # clave: (inglés, español)
    "rodilla_apoyo_flexion_contacto": ("Support-knee flexion at contact", "Flexión de la rodilla de apoyo en el contacto"),
    "rodilla_golpeo_flexion_max": ("Kicking-knee peak flexion", "Flexión máxima de la rodilla de golpeo"),
    "cadera_golpeo_extension_max": ("Kicking-hip peak extension", "Extensión máxima de la cadera de golpeo"),
    "cadera_golpeo_rango": ("Kicking-hip range of motion", "Rango de movimiento de la cadera de golpeo"),
    "tronco_inclinacion_sagital_contacto": ("Trunk sagittal lean at contact", "Inclinación sagital del tronco en el contacto"),
    "tronco_inclinacion_lateral_contacto": ("Trunk lateral lean at contact", "Inclinación lateral del tronco en el contacto"),
    "momento_cadera_flexor_max": ("Peak hip-flexor moment", "Momento flexor máximo de cadera"),
    "momento_rodilla_extensor_max": ("Peak knee-extensor moment", "Momento extensor máximo de rodilla"),
    "momento_rodilla_flexor_max": ("Peak knee-flexor moment", "Momento flexor máximo de rodilla"),
}
ICC_CLASS = {"poor": "pobre", "moderate": "moderado", "good": "bueno", "excellent": "excelente"}
TABLE_MARK = re.compile(r"^<!-- TABLA:(\w+) -->$", re.M)


def _num(x: float, dec: int, lang: str, sign: bool = False) -> str:
    s = f"{x:+.{dec}f}" if sign else f"{x:.{dec}f}"
    s = s.replace("-", "−")
    return s.replace(".", ",") if lang == "es" else s


def _name(key: str, lang: str, unit: bool = True) -> str:
    name = FEATURES[key][lang == "es"]
    return name + ((" (N·m/kg)" if key.startswith("momento") else " (°)") if unit else "")


def table_rows(which: str, lang: str) -> str:
    """Filas de las tablas de resultados leídas de los CSV (sin copiar números a mano)."""
    import pandas as pd
    rows = []
    if which == "agreement":
        t = pd.read_csv(RES / "table3_agreement.csv")
        t = t[(t.dataset == "movi") & t.views.str.startswith("replay")]
        for r in t.itertuples():
            dec = 2 if r.key.startswith("momento") else 1
            to = " a " if lang == "es" else " to "
            cls = ICC_CLASS[r.icc_class] if lang == "es" else r.icc_class
            rows.append([_name(r.key, lang), _num(r.gt_sd, dec, lang), _num(r.bias, dec, lang, True),
                         f"{_num(r.mae, dec, lang)} ({_num(r.mae_ci_low, dec, lang)}–{_num(r.mae_ci_high, dec, lang)})",
                         _num(r.loa_low, dec, lang) + to + _num(r.loa_high, dec, lang),
                         f"{_num(r.icc21, 2, lang)} ({_num(max(r.icc_ci_low, 0), 2, lang)}–{_num(r.icc_ci_high, 2, lang)})",
                         cls])
    elif which == "real":
        t = pd.read_csv(RES / "table4_real_video.csv")
        for key in [k for k in FEATURES if not k.startswith("momento")]:
            g = t[t.rasgo == key].set_index("height")
            cells = [f"{_num(g.loc[h].mae, 1, lang)} ({_num(g.loc[h].icc21, 2, lang)})" for h in ("native", "120", "80", "50")]
            rows.append([_name(key, lang, unit=False), *cells, _num(g.loc["80"].bias, 1, lang, True)])
    elif which == "accept":
        t = pd.read_csv(RES / "table9_acceptability.csv")
        conds = ["single camera (80 px, simulated)", "3 replays + bias correction (simulated)", "real video, 80 px"]
        uses = {"en": ("norms", "ranking", "MAE", "ICC"), "es": ("normas", "ordenar", "EAM", "CCI")}[lang]
        for key in FEATURES:
            g = t[t.key == key].set_index("condition")
            cells = []
            for c in conds:
                r = g.loc[c]
                dec, unit = (2, " N·m/kg") if key.startswith("momento") else (1, "°")
                met = [u for u, ok in ((uses[0], str(r.use_lab_norms) == "True"), (uses[1], bool(r.use_ranking))) if ok]
                head = "**" + " + ".join(met) + "**" if met else "—"
                cells.append(f"{head} ({uses[2]} {_num(r.mae, dec, lang)}{unit}; {uses[3]} {_num(r.icc21, 2, lang)}, "
                             f"{_num(max(r.icc_ci_low, 0), 2, lang)}–{_num(r.icc_ci_high, 2, lang)})")
            rows.append([_name(key, lang), *cells])
    else:
        raise ValueError(f"tabla desconocida: {which}")
    return "\n".join("| " + " | ".join(r) + " |" for r in rows)


def numbering(text: str) -> dict[str, str]:
    """{'fig:design': '1', 'figS:contact': 'S1', 'tbl:data': '1', ...} por orden de aparición."""
    counters, out = {"fig": 0, "figS": 0, "tbl": 0}, {}
    for kind, name in LABEL.findall(text):
        key = f"{kind}:{name}"
        if key in out:
            raise ValueError(f"etiqueta repetida: {key}")
        counters[kind] += 1
        out[key] = ("S" if kind == "figS" else "") + str(counters[kind])
    return out


MAIN_TEXT = {"en": ("# 1. Introduction", "# Acknowledgements"), "es": ("# 1. Introducción", "# Agradecimientos")}


def main_text_words(text: str, lang: str) -> int | None:
    """Palabras del texto principal (de la introducción al final de la discusión), sin pies de figura, tablas,
    títulos de sección ni marcas, como lo cuentan las revistas."""
    start, end = MAIN_TEXT[lang]
    if start not in text or end not in text:
        return None
    body = text[text.index(start):text.index(end)]
    body = re.sub(r"!\[.*?\]\([^)]*\)\{[^}]*\}", " ", body, flags=re.S)
    keep = [l for l in body.split("\n")
            if l.strip() and not l.startswith(("|", ": ", "#", "<!--"))]
    return len(re.sub(r"\{\{[^}]*\}\}|\[@[^\]]*\]|\*", " ", " ".join(keep)).split())


def resolve(text: str, lang: str, for_docx: bool) -> str:
    text = TABLE_MARK.sub(lambda m: table_rows(m.group(1), lang), text)
    words = main_text_words(text, lang)
    if words is not None:
        text = text.replace("{{WORDS}}", f"{words:,}".replace(",", "." if lang == "es" else ","))
    nums = numbering(text)

    def ref(m):
        key = m.group(1)
        if key not in nums:
            raise ValueError(f"referencia sin figura o tabla: {key}")
        return nums[key]
    text = re.sub(r"\{\{((?:fig|figS|tbl):[\w-]+)\}\}", ref, text)
    text = text.replace("{{REPO_URL}}", CONFIG["repo_url"])
    if for_docx:                                   # Word no numera los pies: se escribe el número
        word_fig, word_tbl = ("Figura", "Tabla") if lang == "es" else ("Figure", "Table")
        text = re.sub(r"!\[(.*?)\]\(([^)]*)\)\{#(figS?:[\w-]+)",
                      lambda m: f"![{word_fig} {nums[m.group(3)]}. {m.group(1)}]({m.group(2)}){{#{m.group(3)}", text,
                      flags=re.S)
        text = re.sub(r"^: (.*?) \{#(tbl:[\w-]+)\}", lambda m: f": {word_tbl} {nums[m.group(2)]}. {m.group(1)} {{#{m.group(2)}}}",
                      text, flags=re.M)
        text = text.replace("<!-- SUPLEMENTO -->", "")
    else:
        text = text.replace("<!-- SUPLEMENTO -->", SUPPLEMENT_TYPST)
    return text


def _place(tmp: Path, final: Path):
    """Mueve el fichero recién generado a su sitio; si el destino está abierto en un visor (Windows lo bloquea),
    lo deja al lado con el sufijo _nuevo y avisa."""
    try:
        tmp.replace(final)
    except PermissionError:
        alt = final.with_name(final.stem + "_nuevo" + final.suffix)
        tmp.replace(alt)
        print(f"  aviso: {final.name} está abierto en otro programa; se ha escrito {alt.name}")


def build(md: Path, extra_typst=(), docx=True, template: Path | None = None, lang: str = "en"):
    source = md.read_text(encoding="utf-8")
    typ = md.with_suffix(".typ")
    args = ["--citeproc", "--standalone", "--resource-path", str(md.parent), *extra_typst]
    if template is not None:
        args += ["--template", str(template)]
    tmp = md.with_name(md.stem + "_resuelto.md")
    try:
        tmp.write_text(resolve(source, lang, for_docx=False), encoding="utf-8")
        pypandoc.convert_file(str(tmp), "typst", outputfile=str(typ), extra_args=args)
        pdf_tmp = md.with_name(md.stem + "_tmp.pdf")
        typst.compile(str(typ), output=str(pdf_tmp), root=str(ROOT))
        _place(pdf_tmp, md.with_suffix(".pdf"))
        if docx:
            tmp.write_text(resolve(source, lang, for_docx=True), encoding="utf-8")
            docx_tmp = md.with_name(md.stem + "_tmp.docx")
            pypandoc.convert_file(str(tmp), "docx", outputfile=str(docx_tmp),
                                  extra_args=["--citeproc", "--resource-path", str(md.parent)])
            _place(docx_tmp, md.with_suffix(".docx"))
    finally:
        tmp.unlink(missing_ok=True)
    print("listo:", md.with_suffix(".pdf").relative_to(ROOT))


OUTPUTS_README = """Supplementary file 2 - complete statistical outputs
Manuscript: What can be measured from the broadcast? Validity of single-camera video for football-kick
kinematics and swing-leg joint loads (Martin Gutierrez, 2026).

All tables are aggregated (no per-participant data, as required by the MoVi licence) and are regenerated by the
code at https://github.com/convderover/broadcast-kick-biomechanics.

table2_2d_error.csv        2D detector error on broadcast shots by player height (3DSP)
table3_agreement.csv       agreement in the typical broadcast condition (bias, MAE, LoA, ICC, CIs)
table4_real_video.csv      agreement on real video by image size (MoVi)
table5_digital_twin.csv    digital twin: simulated versus real MAE by feature, camera, size and 2D error model
table6_joint_load.csv      agreement of the swing-leg joint moments and Kick Load Index
table7_improvements.csv    remedies: replay fusion and bias correction
table8_finetune.csv        official versus kick- and broadcast-adapted lifter
table9_acceptability.csv   fitness for use: acceptability criteria and TOST
table10_spm.csv            non-parametric SPM of the knee and hip waveforms
resumen_resultados.json    key numbers of the kinematic analyses
resumen_carga.json         key numbers of the joint-load analyses
contacto_cmu.csv           ankle-speed peak versus true ball contact (CMU)
modelo_ruido.json          fitted broadcast 2D error model
"""


def package_outputs(out: Path):
    """Archivo suplementario 2: todas las salidas estadísticas agregadas en un .zip."""
    import zipfile
    files = sorted(RES.glob("table*.csv")) + [ROOT / "resultados" / n for n in
                                              ("resumen_resultados.json", "resumen_carga.json", "contacto_cmu.csv",
                                               "modelo_ruido.json")]
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("README.txt", OUTPUTS_README)
        for f in files:
            if f.exists():
                z.write(f, f.name)
    print("listo:", out.relative_to(ROOT))


def main():
    for md, lang in ((DOCS / "manuscrito" / "manuscript.md", "en"), (DOCS / "manuscrito" / "manuscrito_es.md", "es")):
        words = main_text_words(md.read_text(encoding="utf-8"), lang)
        print(f"{md.name}: {words} palabras de texto principal" + (" (límite de la revista: 4500)" if lang == "en" else " (versión de lectura, no se envía)"))
    build(DOCS / "manuscrito" / "manuscript.md", PAPER_VARS, lang="en")
    build(DOCS / "manuscrito" / "manuscrito_es.md", PAPER_VARS, lang="es")
    for extra in ("cover_letter.md", "grras_checklist.md"):
        build(DOCS / "manuscrito" / extra, PAPER_VARS, lang="en")
    package_outputs(DOCS / "manuscrito" / "supplementary_file2_statistical_outputs.zip")
    dossier = DOCS / "dossier" / "dossier_clubes.md"
    if dossier.exists():
        build(dossier, docx=False, template=DOCS / "dossier" / "plantilla.typ", lang="es")


if __name__ == "__main__":
    main()
