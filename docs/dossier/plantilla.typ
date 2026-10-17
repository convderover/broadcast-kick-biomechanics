// Plantilla de pandoc (salida typst) para el dossier de 2 páginas en español.
#let accent = rgb("#ff8a3d")
#let ink = rgb("#0f1724")
#let horizontalrule = line(length: 100%, stroke: 0.5pt + luma(200))

#show terms.item: it => block(breakable: false)[
  #text(weight: "bold")[#it.term]
  #block(inset: (left: 1.2em, top: -0.4em))[#it.description]
]

#set table(
  inset: (x: 5pt, y: 4pt),
  stroke: (x, y) => if y == 0 { (bottom: 0.8pt + ink) } else { (bottom: 0.3pt + luma(215)) },
)
#show table.cell.where(y: 0): set text(weight: "bold")
#show figure.where(kind: table): set figure.caption(position: top)
#show figure.caption: set text(size: 7.8pt, fill: luma(80))

#set page(
  paper: "a4",
  margin: (x: 1.6cm, top: 1.5cm, bottom: 1.5cm),
  footer: context [
    #set text(size: 7pt, fill: luma(120))
    $for(author)$$author$$sep$, $endfor$ · $date$ #h(1fr) #counter(page).display("1 / 1", both: true)
  ],
)
#set text(font: ("Segoe UI", "DejaVu Sans"), size: 9.2pt, lang: "es")
#set par(justify: true, leading: 0.52em, spacing: 0.75em)
#show heading.where(level: 1): it => block(above: 1.0em, below: 0.5em)[
  #text(fill: ink, size: 11.5pt, weight: "bold")[#it.body]
  #v(-0.65em)
  #line(length: 100%, stroke: 1.2pt + accent)
]
#show heading.where(level: 2): it => block(above: 0.8em, below: 0.4em)[
  #text(fill: ink, size: 10pt, weight: "bold")[#it.body]
]
#show strong: set text(fill: ink)

#block(fill: ink, inset: (x: 14pt, y: 12pt), radius: 4pt, width: 100%)[
  #text(fill: white, size: 17pt, weight: "bold")[$title$]
  #v(-0.3em)
  #text(fill: accent, size: 10.5pt)[$subtitle$]
]

$body$
