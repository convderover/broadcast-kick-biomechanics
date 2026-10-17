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


def resolve(text: str, lang: str, for_docx: bool) -> str:
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


def main():
    build(DOCS / "manuscrito" / "manuscript.md", PAPER_VARS, lang="en")
    build(DOCS / "manuscrito" / "manuscrito_es.md", PAPER_VARS, lang="es")
    dossier = DOCS / "dossier" / "dossier_clubes.md"
    if dossier.exists():
        build(dossier, docx=False, template=DOCS / "dossier" / "plantilla.typ", lang="es")


if __name__ == "__main__":
    main()
