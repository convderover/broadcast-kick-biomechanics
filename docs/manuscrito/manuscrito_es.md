---
title: "¿Qué se puede medir desde la retransmisión? Validez del vídeo de una sola cámara para la cinemática del golpeo y las cargas articulares de la pierna de golpeo en el fútbol"
author:
  - "Roberto Martín Gutiérrez^1^"
date: "Preprint, octubre de 2026"
lang: es-ES
bibliography: referencias.bib
link-citations: true
header-includes: |
  ```{=typst}
  #show table: set par(justify: false)
  #show table: set text(size: 8.5pt)
  ```
---

^1^ Investigador independiente, España. ORCID: [0009-0004-5724-3502](https://orcid.org/0009-0004-5724-3502). Correspondencia: convderover@gmail.com

**Título abreviado:** Biomecánica del golpeo desde la retransmisión

**Palabras clave:** fútbol; golpeo; captura de movimiento sin marcadores; estimación monocular de la postura 3D; vídeo de retransmisión; dinámica inversa; prevención de lesiones; validez

*Versión en español del manuscrito original en inglés.*

# Resumen

**Objetivo.** Las ligas profesionales ya miden el balón directamente, como hace el balón conectado de LaLiga EA Sports desde la temporada 2026/27. En cambio, el cuerpo que lo golpea solo se puede observar a través del vídeo de la retransmisión. Existen sistemas que extraen la postura del disparo desde una sola cámara, pero nadie ha cuantificado su error en condiciones de retransmisión: jugadores pequeños en la imagen, ángulos de cámara arbitrarios y 25–50 imágenes por segundo (fps). Tampoco se sabe si se pueden recuperar las cargas articulares de la pierna de golpeo, la magnitud más ligada a las lesiones musculares que provoca el golpeo.

**Métodos.** Combinamos:

- el error 2D real de un detector de referencia (RTMW-x), medido en 200 disparos de retransmisiones de la Premier League inglesa (3DSP, 6.000 detecciones);
- una referencia de laboratorio de 90 golpeos (7 golpeos de balón con el empeine de CMU y 83 participantes de MoVi);
- una cámara de retransmisión virtual (5 vistas × 5 tamaños de jugador × 25/50 fps) alimentada con remuestreo de residuos reales de retransmisión;
- un elevador temporal 2D→3D publicado (MotionAGFormer);
- una validación con vídeo real de MoVi con captura sincronizada, que incluye un gemelo digital de cada grabación para comprobar si la simulación predice el error del vídeo real;
- tres remedios: corrección de sesgos aprendida en laboratorio, fusión de los ángulos de repetición y un elevador adaptado al golpeo con ruido de retransmisión.

Evaluamos seis rasgos cinemáticos y tres momentos articulares netos de la pierna de golpeo, obtenidos por dinámica inversa de Newton–Euler (cadena cinética abierta, sin plataformas de fuerza). Además estimamos el tamaño del estudio prospectivo necesario para validar un índice basado en la carga como predictor de lesiones.

**Resultados.**

- **Error del detector:** en retransmisión fue del 7,6–12,9 % de la altura del jugador, más del doble que en vídeo de laboratorio con el mismo tamaño en píxeles.
- **Condición típica de retransmisión** (jugador de 80 px de alto, 25 fps, vistas de repetición): los errores de los rasgos de la pierna fueron de 16–20°. Solo la flexión máxima de la rodilla de golpeo y la extensión de la cadera en el armado alcanzaron un acuerdo moderado entre jugadores (CCI 0,64 y 0,55). Las inclinaciones del tronco tuvieron errores pequeños (7°) pero acuerdo pobre, porque los jugadores difieren poco entre sí.
- **Qué importa y qué no:** la frecuencia de imagen no influyó (25 frente a 50 fps). Sí influyeron la vista de cámara y el instante de contacto: conocerlo, como permite el balón conectado, redujo los errores un 25 %.
- **Gemelo digital:** predijo los errores del vídeo real (r = 0,84; discrepancia media de 3,9°). Los errores con vídeo real fueron coherentes con la simulación una vez corregido un error de escala de las confianzas.
- **Remedios:** fusionar tres ángulos de repetición elevó el acuerdo de la extensión de cadera de 0,40 a 0,78. Un elevador adaptado al golpeo con ruido de retransmisión redujo a la mitad los errores simulados y mejoró cinco rasgos con imágenes reales, pero empeoró los golpeos reales de balón.
- **Carga articular:** el Índice de Carga del Golpeo de la pierna de golpeo fue válido en laboratorio (ρ = 0,79 con la intensidad del golpeo), pero no se pudo recuperar desde vídeo de tipo retransmisión (fiabilidad λ = 0,08). Validarlo como predictor de lesiones exigiría unas 590 lesiones relacionadas con el golpeo (12–24 temporadas de LaLiga), frente a 48 con una medida de calidad de laboratorio.

**Conclusiones.** Con modelos abiertos, el vídeo de retransmisión de una sola cámara solo permite una cinemática del golpeo gruesa y agregada, y no permite ningún índice de carga articular ni de riesgo de lesión. Las palancas son tres:

- anclar cada golpeo al instante de contacto del balón conectado;
- fusionar repeticiones;
- adaptar los modelos con datos específicos de fútbol.

Un índice de lesión solo debería validarse de forma prospectiva después de elevar su fiabilidad con datos de club. El protocolo y el código se publican como banco de pruebas abierto.

# 1. Introducción

El golpeo es la habilidad que define el fútbol, y también es un mecanismo de lesión.

- **Peso de las lesiones musculares:** casi un tercio de todas las lesiones con baja en el fútbol profesional masculino. Las de aductores (23 %) y cuádriceps (19 %) son una gran parte de ellas [@ekstrand2011]. Las lesiones de cadera e ingle representan por sí solas el 12–16 % de todas las lesiones de cada temporada [@werner2009; @werner2019].
- **El golpeo como mecanismo:** es una de las dos acciones principales tras las roturas agudas del aductor largo [@serner2019] y un mecanismo principal de las roturas del recto femoral [@mendiguchia2013].
- **Biomecánica del golpeo:** el armado que estira los flexores de cadera, la extensión rápida de la rodilla y el frenado de la pierna antes del impacto se han descrito en detalle en el laboratorio [@lees2010; @kellis2007; @nunome2002; @dorge2002; @apriantono2006; @shan2005; @charnock2009].

En los partidos, sin embargo, el golpeo solo se observa a través del vídeo de la retransmisión. Desde agosto de 2026, LaLiga EA Sports instrumenta cada balón de partido con un sensor inercial y de radiofrecuencia que informa de la posición y del instante de cada contacto [@laliga2026]. El balón ya se mide; el cuerpo que lo golpea, no.

La estimación monocular de la postura humana ha avanzado deprisa, y varios grupos han empezado a extraer la postura del golpeo desde vídeo de una sola cámara:

- AutoSoccerPose construye secuencias 2D y 3D de la postura del disparo a partir de retransmisiones [@yeung2024].
- Noworolnik y Jaworek-Korjakowska obtienen nueve rasgos del golpeo con una cámara lateral para valorar la técnica de disparo con un modelo de visión y lenguaje [@noworolnik2025].
- La postura 3D global de los jugadores en retransmisiones es el objetivo de WorldPose [@jiang2024worldpose] y de métodos afines [@khan2026; @baumgartner2023].

Lo que falta es caracterizar el error de medida de las propias variables del golpeo en condiciones de retransmisión. Los sistemas sin marcadores se han validado para la marcha y otras tareas de laboratorio con varias cámaras [@kanko2021; @needham2021; @uhlrich2023], y para el golpeo en el campo frente a la digitalización manual [@palucci2022]. Pero una cámara de retransmisión es distinta:

- el jugador que dispara suele ocupar entre 30 y 90 píxeles de altura en la imagen;
- el ángulo de cámara es arbitrario;
- la frecuencia es de 25 o 50 fps;
- las imágenes están comprimidas.

AthletePose3D demostró que, en gestos atléticos, los ángulos articulares monoculares pueden correlacionar fuertemente con la captura de movimiento mientras que las velocidades articulares no lo hacen [@yeung2025]. Las cargas articulares requieren derivadas segundas de la posición y, por tanto, cabe esperar que sean aún más frágiles. Sin embargo, son justo las magnitudes que querría un servicio médico para un índice de «sufrimiento articular» o de riesgo de lesión. Si no se conoce el error de medida, ninguna métrica de técnica o de carga obtenida de la retransmisión es interpretable, y ningún modelo de lesión construido sobre ella puede validarse.

Este estudio se pregunta qué variables del golpeo se pueden medir con modelos abiertos desde vídeo de tipo retransmisión, con qué tamaños de jugador y vistas de cámara, y si se puede recuperar un índice de carga articular de la pierna de golpeo. Nuestras contribuciones son:

1. El error 2D real de un detector moderno en disparos de retransmisión en función del tamaño del jugador, incluida su estructura temporal.
2. Un estudio de sensibilidad que propaga ese error a seis rasgos del golpeo y a tres momentos articulares de la pierna de golpeo, con referencia de laboratorio de 90 golpeos y una cámara de retransmisión virtual.
3. Una validación con vídeo real y captura sincronizada, y una prueba de la propia simulación mediante un gemelo digital.
4. La evaluación de tres remedios prácticos: corrección de sesgos, fusión de los ángulos de repetición que la retransmisión ya ofrece y adaptación del elevador 3D al golpeo con ruido de retransmisión.
5. Una caracterización del instante de contacto del golpeo, que el balón conectado ya registra.
6. Una respuesta cuantitativa a qué haría falta para validar en una liga profesional un índice de carga obtenido de la retransmisión como predictor de lesiones.

El protocolo, el código y el banco de residuos derivado se publican como banco de pruebas abierto. Así, los nuevos modelos de postura podrán evaluarse por su validez en golpeos de retransmisión y no solo por un error genérico de posición articular.

# 2. Métodos

## 2.1 Visión general

La Figura {{fig:design}} resume el diseño y la Tabla {{tbl:data}}, los datos:

- **Referencia:** golpeos de laboratorio con captura óptica de movimiento (apartado 2.2). De cada golpeo calculamos seis rasgos cinemáticos y tres cargas articulares de la pierna de golpeo (apartados 2.3–2.4).
- **Simulación:** una cámara de retransmisión virtual filma el golpeo con tamaños de jugador, vistas y frecuencias controlados. A sus proyecciones 2D exactas se les añade el error 2D que comete de verdad un detector en disparos de retransmisión (apartados 2.5–2.6).
- **Reconstrucción y comparación:** un elevador temporal reconstruye el 3D (apartado 2.7), y los rasgos y cargas se vuelven a calcular y se comparan con la referencia (apartado 2.10).
- **Vídeo real:** la misma cadena se aplica a vídeo real con captura sincronizada, y cada grabación real se reproduce con su gemelo digital (apartado 2.8).

![Diseño del estudio. (1) Los golpeos de laboratorio registrados con captura óptica aportan la referencia (se muestra un golpeo de balón de CMU, con las posturas difuminadas hasta el contacto). (2) Una cámara de retransmisión virtual filma cada golpeo desde cinco vistas, con cinco tamaños de jugador y a 25 o 50 fps (miniaturas: el mismo instante a 200, 80 y 50 px), y sus proyecciones 2D exactas se contaminan con los residuos que comete un detector en disparos reales de retransmisión; el vídeo real con captura sincronizada (MoVi) y un gemelo digital de cada grabación ponen a prueba la simulación. (3) Los puntos 2D se elevan a 3D con MotionAGFormer, con los pesos oficiales o con los adaptados al golpeo. (4) Seis rasgos cinemáticos y tres momentos de la pierna de golpeo se comparan con el laboratorio (sesgo, error absoluto medio, límites de acuerdo y CCI con las clases de Koo y Li), y la fiabilidad se traduce en el tamaño del estudio de lesiones necesario para validar un índice de carga.](../../resultados/paper_es/fig1_design.png){#fig:design width=100%}

## 2.2 Golpeos de referencia

**CMU (golpeos de balón).**

- **Datos:** siete ensayos etiquetados «soccer – kick ball» de la CMU Graphics Lab Motion Capture Database [@cmu]: sujeto 10, ensayos 01–06; sujeto 11, ensayo 01. Se capturaron con un sistema Vicon a 120 Hz.
- **Centros articulares:** se usaron los virtuales que exporta el programa de captura (cadera HJ0, rodilla FE0, tobillo TI0, hombro CL0, codo HU0, muñeca WR0). Se verificaron mediante las longitudes de los segmentos del sujeto 10: muslo 403 mm, pierna 459 mm, brazo 293 mm y antebrazo 281 mm.
- **Balón:** había tres marcadores sobre el balón en seis ensayos.
- **Particularidades:** el ensayo 11_01 incluye carrera previa. El 10_04 es un golpeo lento sin marcadores de balón (velocidad máxima del tobillo de 4,1 m/s, frente a 10,2–13,1 m/s en el resto).
- **Masa corporal:** no se proporciona. Las cargas se normalizan por la masa, lo que las hace independientes de ella.

**MoVi (varios sujetos, con vídeo).**

- **Datos:** la ronda F de MoVi [@ghorbani2021] contiene una acción de golpeo («kicking») para cada uno de sus 90 participantes (60 mujeres y 30 hombres).
  - Se capturó con 67 marcadores a 120 Hz (Qualisys) y se procesó con Visual3D.
  - Incluye vídeo sincronizado de dos cámaras fijas calibradas (800 × 600 px, 30 fps).
  - Se proporcionan la estatura y la masa corporal.
- **Limpieza:**
  - Visual3D guarda como (0, 0, 0) las articulaciones que no pudo reconstruir. Se trataron como huecos.
  - Los huecos de hasta 0,25 s se rellenaron por interpolación lineal (también en CMU).
  - Se excluyeron los golpeos con huecos más largos.
  - Ochenta y tres participantes tenían un segmento de golpeo utilizable y sin huecos (55 mujeres y 28 hombres).
- **Naturaleza de los golpeos:** son golpeos sin balón realizados por no futbolistas, así que sirven para validar la cadena de medida, no para describir la técnica futbolística.
- **Puntos usados:** los centros articulares de Visual3D (cadera, rodilla, tobillo, hombro, codo, muñeca y cabeza) y los cuatro marcadores de la cabeza.
- **Sincronía:** vídeo y captura se sincronizaron como fotograma de captura = 4 × fotograma de vídeo. Lo verificamos proyectando la captura con la calibración publicada sobre las detecciones de RTMW: mejor desfase de 0 ± 2 fotogramas de captura y residuo de 2–4 px en rodillas y tobillos.

Todas las posiciones articulares se expresaron en metros con el eje *z* vertical y se asignaron al esqueleto de 17 articulaciones de Human3.6M que espera el elevador [@ionescu2014]. La pelvis es el punto medio de las caderas, el tórax el punto medio de los hombros y la columna el punto medio entre ambos.

: Conjuntos de datos utilizados. {#tbl:data}

| Conjunto | Papel | Tamaño | Frecuencia | Notas |
|:--------|:--------------|:----------------|:-------|:----------------|
| CMU | Referencia: golpeos reales de balón | 2 participantes, 7 golpeos | 120 Hz | Vicon; balón con marcadores en 6 golpeos; uno con carrera previa |
| MoVi (ronda F) | Referencia y vídeo real | 83 participantes, 83 golpeos al aire, 2 cámaras | 120 Hz; vídeo a 30 fps | Visual3D; estatura y masa; licencia no comercial |
| 3DSP | Error 2D del detector en retransmisión | 200 disparos de la Premier League, 6.000 detecciones | 25 fps | Anotación 2D manual del jugador que dispara |

## 2.3 Eventos del golpeo y rasgos cinemáticos

La pierna de golpeo es aquella cuyo tobillo alcanza la mayor velocidad máxima. El instante de contacto se aproxima por el pico de velocidad del tobillo de golpeo. En los ensayos de CMU con marcadores de balón lo comparamos con el contacto real, que se obtuvo extrapolando hacia atrás la recta de salida del balón hasta su posición de reposo. Esto fue necesario porque el pie tapa el balón en el impacto en el 22–57 % de los fotogramas.

Los seis rasgos se calcularon con el esqueleto de ocho articulaciones (hombros, caderas, rodillas y tobillos; Figura {{fig:model}}a–d):

- flexión de la rodilla de apoyo en el contacto;
- flexión máxima de la rodilla de golpeo, en la ventana de −0,3 s al contacto;
- extensión máxima de la cadera de golpeo, en la misma ventana;
- rango de movimiento de la cadera de golpeo, de −0,3 s a +0,2 s;
- inclinación sagital del tronco en el contacto, respecto a la vertical, positiva hacia delante;
- inclinación lateral del tronco en el contacto, positiva hacia la pierna de apoyo.

La flexión de cadera se mide en el sistema de referencia del cuerpo (eje del tronco y eje lateral de la pelvis). Estos rasgos coinciden en parte con los de sistemas previos de una sola cámara [@noworolnik2025] y con los determinantes del rendimiento del golpeo [@lees2010; @kellis2007].

## 2.4 Cargas articulares de la pierna de golpeo (dinámica inversa sin plataformas de fuerza)

**Principio.** Entre el final del armado y el contacto con el balón, la pierna de golpeo no toca el suelo. Por eso los momentos netos en su rodilla y su cadera quedan completamente determinados por la cinemática y la inercia del muslo, la pierna y el pie (Figura {{fig:model}}e).

**Modelo.** Usamos un modelo de Newton–Euler con los parámetros de los segmentos de de Leva [-@deleva1996]: fracciones de masa, posición de los centros de masas y radios de giro sagitales para hombres y mujeres.

- **Pie:** como los esqueletos compatibles con la retransmisión no tienen puntos del pie, se modeló como una masa puntual en el tobillo.
- **Velocidad angular:** se calculó a partir del eje longitudinal de cada segmento (ω = u × u̇), lo que ignora la rotación axial.
- **Signos:** los momentos se proyectaron sobre el eje lateral de la pelvis; los valores positivos indican momentos extensores de rodilla y flexores de cadera.
- **Filtrado:** filtro Butterworth de cuarto orden y fase cero, a 12 Hz para la captura a 120 Hz y a mín(12 Hz; 0,35 × fps) para el vídeo.

**Picos extraídos,** normalizados por la masa corporal (N·m/kg):

- momento flexor máximo de cadera, entre el final del armado (mínima flexión de cadera en los 0,3 s previos al contacto) y el contacto;
- momento extensor máximo de rodilla, en la misma ventana;
- momento flexor máximo de rodilla en los 100 ms previos al contacto, que corresponde al frenado de la pierna por los isquiotibiales.

La fuerza del impacto del balón no se modela; todas las ventanas acaban en el contacto.

**Índice compuesto.** El Índice de Carga del Golpeo (KLI, por sus siglas en inglés) es la media de los tres picos expresados como puntuaciones z respecto a la distribución de referencia de MoVi.

**Validación del modelo.** El mismo modelo se aplicó a la referencia y a las estimaciones desde vídeo, de modo que la comparación aísla la cadena de medida de las simplificaciones del modelo. Se verificó analíticamente con un miembro estático (momento solo gravitatorio), con la simetría especular y con el escalado cuadrático con la velocidad del movimiento.

**Ejemplo.** La Figura {{fig:model}}f muestra las curvas de momento de un golpeo fuerte y de uno lento del mismo jugador: el golpeo fuerte alcanza 1,01 N·m/kg de momento flexor de cadera durante el balanceo hacia delante y 0,89 N·m/kg de momento flexor (de frenado) de rodilla justo antes del contacto, frente a 0,43 y 0,12 N·m/kg en el golpeo lento.

![El modelo del golpeo sobre un golpeo real de balón (CMU 10_01, 120 Hz). (a–d) Cinco de los seis rasgos cinemáticos leídos sobre el esqueleto (el sexto es el rango de movimiento de la cadera de golpeo): extensión de la cadera de golpeo al final del armado (a), flexión máxima de la rodilla de golpeo (b), flexión de la rodilla de apoyo e inclinación sagital del tronco en el contacto con el balón (c) e inclinación lateral del tronco en el contacto (d); naranja: pierna de golpeo; verde: pierna de apoyo. (e) Diagrama de cuerpo libre de la pierna de golpeo 50 ms antes del contacto: pesos de los segmentos en sus centros de masas, fuerza de reacción en la cadera y momentos articulares netos. (f) Momentos netos de cadera y rodilla de este golpeo y de un golpeo lento del mismo jugador (10_04, discontinua); franja gris: del final del armado al contacto; franja naranja: últimos 100 ms; puntos: los tres picos de carga usados como variables.](../../resultados/paper_es/fig2_model.png){#fig:model width=100%}

## 2.5 Error del detector 2D en disparos de retransmisión

- **Datos:** el conjunto 3D Shot Posture (3DSP) [@yeung2024], con 200 disparos de retransmisiones de la Premier League inglesa (vía SoccerNet [@deliege2021]). Cada disparo tiene 20 fotogramas consecutivos a 25 fps y 17 puntos anotados a mano del jugador que dispara.
- **Detector:** RTMW-x (384 × 288, entrenamiento cocktail-14, ONNX) [@jiang2024rtmw; @jiang2023rtmpose], aplicado de arriba abajo con la caja de la persona dada por la extensión de la anotación más un margen del 20 %.
- **Jugadores más pequeños:** para explorarlos, un cuarto de los disparos se procesó también al 75 % y al 50 % de escala; en total, 6.000 detecciones.
- **Emparejamiento:** los puntos se emparejaron por nombre anatómico. Como control, se calculó también el emparejamiento con izquierda y derecha intercambiadas.
- **Medida:** el error RMS por eje de imagen en 12 articulaciones de las extremidades, en función de la altura del jugador *H* (de la cabeza al tobillo más bajo). Se ajustó σ(*H*) = √((*aH*)² + *b*²).

Como la anotación manual de jugadores pequeños tiene su propio error, estos valores son una cota superior del error del detector.

## 2.6 Cámara de retransmisión virtual

- **Geometría:** cada golpeo de referencia se remuestreó a 50 o 25 fps y se filmó con una cámara estenopeica situada a 40 m del jugador, con 15° de elevación y azimuts de 0° (frontal), 45°, 90° (lateral, del lado de la pierna de golpeo), 135° y 180° (espalda).
- **Tamaño:** la focal se ajustó para que la mediana de la altura del jugador fuera *H* ∈ {400, 200, 120, 80, 50} px.
- **Error 2D:** a las proyecciones exactas se añadieron tres modelos.
  - **Ninguno.**
  - **Gaussiano:** ruido independiente con el σ(*H*) medido.
  - **Residuos reales:** un remuestreo de secuencias completas de 20 fotogramas de residuos reales de RTMW en 3DSP, emparejados por nombre anatómico, escalados por *H*, remuestreados en el tiempo y concatenados. Este remuestreo conserva la correlación temporal, el error propio de cada articulación y los fallos groseros, como la confusión entre izquierda y derecha. Por encima de unos 90 px, los residuos de retransmisión se extrapolan por escalado.
- **Semillas:** los golpeos de CMU usaron tres semillas aleatorias por condición y los de MoVi una; la réplica la aportan los 83 participantes.

## 2.7 Elevación de 2D a 3D

- **Modelo:** MotionAGFormer-B con sus pesos oficiales de Human3.6M [@mehraban2024], con ventanas de 243 fotogramas y aumento por volteo en la inferencia.
- **Normalización de la entrada:** la entrada 2D se normaliza dentro de un recorte cuadrado centrado en la pelvis, de lado 2 × *H*. Con la normalización a la imagen completa de la demo pública, un jugador pequeño produce errores de 50–90° incluso sin ruido, porque el modelo nunca vio personas de ese tamaño respecto al encuadre.
- **Conversión de las detecciones reales:** de COCO a Human3.6M, con las reglas de la demo oficial.
- **Confianzas:** las puntuaciones que devuelve RTMW son máximos SimCC sin normalizar (normalmente entre 3 y 7), mientras que el elevador se entrenó con confianzas en [0, 1]. Pasarlas sin cambios deformaba la reconstrucción: la flexión máxima de la rodilla de golpeo se infraestimaba en 41° de media. Por eso se usó una confianza constante de 0,9, igual para la entrada real y la simulada.
- **Escala y orientación:** la reconstrucción se escaló para que la mediana de la longitud del muslo coincidiera con la de referencia, lo que equivale a conocer la estatura del jugador. Después se alineó rígidamente con la referencia (Kabsch, rotación y traslación, una vez por secuencia), lo que equivale a conocer la vertical por la calibración del campo.
- **Contacto:** se trató de dos formas.
  - **Conocido:** se dan el fotograma y la pierna de golpeo, como haría un analista o un sistema de seguimiento del balón.
  - **Automático:** pico de velocidad del tobillo en la reconstrucción.

## 2.8 Validación con vídeo real y gemelo digital

**Validación.** Para cada participante de MoVi y cada una de las dos cámaras:

1. YOLOX-m [@ge2021yolox] detectó a la persona en la imagen original y se conservó la caja que contenía la pelvis proyectada.
2. La imagen se redujo para que el participante midiera 120, 80 o 50 px y se comprimió en JPEG (calidad 70), o se mantuvo a resolución nativa (unos 280–380 px).
3. RTMW-x estimó la postura dentro de la caja escalada.
4. Medimos el error 2D frente a la captura proyectada, elevamos a 3D y calculamos rasgos y cargas a 30 fps.

De la calibración se obtuvieron el azimut de la cámara respecto a la dirección en que miraba el participante, la elevación (6–8°) y la distancia (4–5 m).

**Gemelo digital.** Cada grabación se volvió a simular con la cámara virtual colocada exactamente en esa geometría y con el mismo conjunto de fotogramas, con tres modelos de error 2D:

- ninguno;
- residuos reales de RTMW de los *demás* participantes de MoVi (residuos de vídeo de laboratorio);
- residuos de retransmisión de 3DSP.

Si el gemelo con residuos de vídeo de laboratorio reproduce los errores medidos con imágenes reales, la simulación es válida y su variante con residuos de retransmisión es una estimación creíble del error en retransmisión.

## 2.9 Remedios

*Corrección de sesgos.* Para cada vista de cámara se ajustó una calibración lineal, referencia ≈ *a* + *b*·estimación, en los golpeos de laboratorio y se aplicó a participantes no vistos (dejando fuera un participante cada vez). Para probar la transferencia al fútbol, se ajustó en todos los golpeos de MoVi y se aplicó a los golpeos de balón de CMU.

*Fusión de repeticiones.* Las retransmisiones suelen repetir un disparo desde varias cámaras. Promediamos las estimaciones de los rasgos de dos (45° y 135°) o tres (45°, 90° y 135°) repeticiones virtuales del mismo golpeo. Los errores 2D de las distintas cámaras se generaron de forma independiente.

*Elevador adaptado al golpeo y a la retransmisión.* MotionAGFormer-B se ajustó con datos de retransmisión sintéticos generados sobre la marcha a partir de la captura de MoVi.

- **Datos de entrenamiento:** las 21 acciones grabadas de los participantes de entrenamiento, con la mitad de las ventanas centradas en su golpeo.
- **Cámara virtual aleatoria:** azimut 0–360°, elevación 5–25°, distancia 15–60 m, altura del jugador 40–400 px (log-uniforme) y 25 o 50 fps.
- **Error 2D:** residuos de retransmisión (60 % de las muestras), ruido gaussiano (20 %) o proyecciones exactas (20 %), con volteo izquierda–derecha aleatorio.
- **Objetivos:** siguieron el convenio 3D en espacio imagen del entrenamiento original. Comprobamos que el modelo oficial lo reproduce con una escala de 0,99–1,01.
- **Entrenamiento:** pérdida original (MPJPE + 0,5 × MPJPE normalizado en escala + 20 × error de velocidad), AdamW (tasa de aprendizaje 5 × 10⁻⁵ con decaimiento coseno), lotes de 8 y 1.000 iteraciones. Se usaron recomputación de activaciones y precisión mixta para que cupiera en una GPU de 8 GB.
- **Evaluación:** los participantes se dividieron en dos pliegues y cada modelo se evaluó solo con los participantes que nunca vio. Los golpeos de balón de CMU no se usaron nunca para entrenar. En todas las comparaciones, ambos elevadores recibieron exactamente la misma entrada 2D.
- **Licencia:** la de MoVi permite este uso de investigación no comercial, pero no desplegar esos pesos en un producto comercial.

## 2.10 Estadística

Para cada variable y condición se calcularon:

- el sesgo (media de estimación − referencia) y el error absoluto medio (EAM);
- los límites de acuerdo al 95 % [@bland1986];
- la *r* de Pearson y el coeficiente de correlación intraclase CCI(2,1) de acuerdo absoluto [@shrout1979], interpretado con los umbrales de Koo y Li: < 0,5 pobre; 0,5–0,75 moderado; 0,75–0,9 bueno; > 0,9 excelente [@koo2016];
- la pendiente de calibración λ (regresión de la referencia sobre la estimación);
- la diferencia mínima detectable entre dos golpeos, 1,96 × √2 × DE(error).

El CCI y λ se calcularon entre participantes de MoVi dentro de cada condición, con intervalos de confianza del 95 % obtenidos de 1.000 remuestreos de golpeos (todas las vistas de un golpeo se remuestrearon juntas). La condición «típica de retransmisión» es *H* = 80 px, 25 fps, residuos de retransmisión y contacto conocido; las vistas de repetición son las de 45–135°.

## 2.11 ¿Qué necesitaría un estudio de lesiones?

**Dilución.** Si un índice de carga *W* mide la carga verdadera *X* con error aleatorio, cualquier asociación entre *X* y la lesión estimada a través de *W* queda atenuada por la fiabilidad λ, en lo que se conoce como dilución de la regresión [@hutcheon2010]. El logaritmo del cociente de riesgos (hazard ratio, HR) por desviación estándar de *W* es √λ veces el correspondiente por desviación estándar de *X*.

**Tamaño del estudio.** Combinando esto con la fórmula de Schoenfeld para una covariable continua [@schoenfeld1983], el número de lesiones necesario para detectar un HR verdadero por DE con α bilateral de 0,05 y potencia de 0,8 es *D* = (*z*~0,975~ + *z*~0,8~)² / (λ · ln² HR).

**Traducción a temporadas de LaLiga.** Supusimos 20 clubes × 25 jugadores de primer equipo y 0,05–0,10 lesiones musculares de aductores o cuádriceps relacionadas con el golpeo por jugador y temporada. La cifra sale de 0,6 lesiones musculares por jugador y temporada, el 42 % de ellas de aductores o cuádriceps [@ekstrand2011], de las cuales aproximadamente entre un cuarto y la mitad son atribuibles al golpeo [@serner2019; @mendiguchia2013]. Es una suposición explícita.

## 2.12 Implementación y disponibilidad de datos

Python 3.11, NumPy, SciPy, PyTorch 2.10 (CUDA), ONNX Runtime y rtmlib, con 59 pruebas unitarias (`python -m pytest`). El código, los resultados numéricos agregados y las figuras están disponibles en {{REPO_URL}}.

Los conjuntos de datos no se redistribuyen:

- CMU es libre para investigación.
- 3DSP es de investigación; sus imágenes de retransmisión tienen derechos y no se muestran en la publicación.
- MoVi tiene licencia de investigación no comercial.

Todos los datos son públicos y fueron recogidos por sus propietarios con aprobación ética; no se recogieron datos humanos nuevos.

# 3. Resultados

## 3.1 El instante de contacto

En los cinco golpeos de CMU con marcadores de balón, el pico de velocidad del tobillo de golpeo precedió al contacto real en 19,6 ms de media (rango 6,8–32,2 ms; Figura suplementaria {{figS:contact}}). Eso son 1–4 fotogramas de captura y menos de un fotograma de retransmisión a 25 fps. Calcular los rasgos en el pico del tobillo en lugar del contacto real los cambió como mucho 2,1° (flexión de la rodilla de apoyo); los rasgos de máximos no se vieron afectados. Por tanto, el pico del tobillo es un sustituto aceptable cuando no se conoce el instante de contacto.

Un ensayo descrito antes como un toque suave (10_06, velocidad del balón de 3,5 m/s) es en realidad un golpeo completo (velocidad máxima del tobillo de 11,7 m/s): el sistema de captura perdió el balón tres fotogramas después del impacto. El golpeo lento del conjunto es el 10_04 (4,1 m/s).


## 3.2 Error del detector en disparos de retransmisión

El emparejamiento por nombre anatómico dio un error 2D medio de 4,35 px, frente a 16,6 px con izquierda y derecha intercambiadas, lo que confirma la correspondencia de las articulaciones.

- **Crecimiento con el tamaño:** el error RMS por eje creció con la altura del jugador, σ(*H*) = √((0,063 *H*)² + 3,9²) px (6.000 detecciones). Su tamaño relativo bajó del 12,9 % de la altura del jugador con unos 27 px al 7,6 % con unos 86 px (Tabla {{tbl:2d}}, Figura {{fig:2d}}a).
- **Por articulación:** las distales fueron las menos precisas, con los tobillos al 14,4 % y las muñecas al 13,7 % de *H*, frente al 5,6 % de las caderas y el 5,5 % de los hombros (Figura {{fig:2d}}b).
- **Frente al laboratorio:** en vídeo de laboratorio reducido a los mismos tamaños, el error del mismo detector fue del 3,1–4,0 % de *H* (2,7 % a resolución nativa). Es decir, las imágenes de retransmisión son bastante más difíciles que las de laboratorio con el mismo número de píxeles.

: Error 2D real de RTMW-x en 200 disparos de la Premier League (3DSP), por altura del jugador. {#tbl:2d}

| Altura del jugador (mediana, px) | Detecciones | Error RMS por eje (px) | % de la altura |
|---|---|---|---|
| 26,6 | 481 | 3,45 | 12,9 |
| 36,3 | 743 | 4,37 | 12,1 |
| 45,5 | 903 | 4,73 | 10,4 |
| 55,3 | 1.388 | 5,75 | 10,4 |
| 68,0 | 2.063 | 5,90 | 8,7 |
| 85,8 | 422 | 6,50 | 7,6 |

![Error del detector 2D. (a) Error RMS por eje relativo a la altura del jugador en disparos de retransmisión (3DSP; puntos: fotogramas; línea: RMS por tramos; discontinua: modelo ajustado) y en vídeo de laboratorio reducido a tamaños de retransmisión (MoVi). (b) Error en retransmisión por articulación.](../../resultados/paper_es/fig3_2d_error.png){#fig:2d width=100%}

## 3.3 Sensibilidad a la vista de cámara, el tamaño del jugador, la frecuencia de imagen, el modelo de ruido y el contacto

**Sin ruido 2D.** El elevador por sí solo produjo un error absoluto medio (seis rasgos, todas las vistas y tamaños, 25 fps) de 9,2° en los golpeos de MoVi y de 15,0° en los golpeos de balón de CMU. Dentro de MoVi, el error no se relacionó con la intensidad del golpeo (ρ de Spearman = 0,12; *p* = 0,27; Figura suplementaria {{figS:intensity}}). Por tanto, el mayor error de los golpeos de balón refleja un movimiento distinto y propio del fútbol (carrera previa e impacto), no solo la velocidad.

**Vista de cámara.** Fue el factor dominante (Figura {{fig:sens}}; CMU en la Figura suplementaria {{figS:senscmu}}). En MoVi, sin ruido, los errores fueron de 5,0° (lateral), 7,3° (45°), 9,0° (135°), 11,1° (frontal) y 13,6° (espalda). Con residuos de retransmisión fueron, en el mismo orden, 11,9°, 19,0°, 13,5°, 22,6° y 20,0°.

**Tamaño del jugador.** Influyó poco entre 50 y 400 px (16,8–18,2°), porque el error relativo del detector es casi constante en ese rango.

**Modelo de error.** Sí importó. El ruido gaussiano independiente de la magnitud medida exageró el error, respecto a las secuencias de residuos reales, entre 1,05 y 1,8 veces según el rasgo. Por ejemplo, el rango de la cadera de golpeo dio 42,8° frente a 23,8° (Figura suplementaria {{figS:ablation}}a).

**Frecuencia de imagen.** No importó: 16,7° a 50 fps frente a 17,4° a 25 fps (Figura suplementaria {{figS:ablation}}b).

**Instante de contacto.** Sí importó. Detectarlo en la postura reconstruida en vez de conocerlo aumentó el error medio de 17,4° a 23,1° (+33 %), y entre un 26 y un 33 % en los rasgos de la pierna y el tronco salvo la flexión de la rodilla de apoyo (Figura suplementaria {{figS:ablation}}c).

![Cámara de retransmisión virtual, golpeos de MoVi (n = 83), 25 fps, residuos de retransmisión y contacto conocido: error absoluto medio de cada rasgo frente a la altura del jugador, por vista de cámara.](../../resultados/paper_es/fig4_sensitivity.png){#fig:sens width=100%}

**Cómo se ve en un golpeo.** La Figura {{fig:recon}} muestra qué significan estas cifras en un golpeo concreto y en la curva media. Desde una cámara lateral, la flexión de cadera reconstruida siguió de cerca la curva de laboratorio (diferencia absoluta media entre las curvas medias de 3,3°). La flexión de rodilla la siguió hasta el máximo, pero se perdió la extensión de la rodilla durante el contacto: la rodilla reconstruida quedó 18° más flexionada en el contacto y 36° más 120 ms después. Desde una cámara frontal, en la que la flexión de rodilla ocurre sobre todo en profundidad, el ángulo de rodilla reconstruido fue casi plano (85–101° frente a 19–86° en el laboratorio), mientras que la curva de cadera se siguió con una diferencia media de 6°.

![Lo que ve la cámara de retransmisión y lo que se reconstruye. (a) Un golpeo real de balón (CMU 10_01) en cinco instantes alrededor del contacto: captura óptica (fila superior); entrada 2D de una cámara de retransmisión lateral con el jugador a 80 px, 25 fps y residuos 2D reales de retransmisión (segunda fila); y 3D reconstruida desde una cámara lateral y desde una frontal (azul) superpuesta a la verdad (gris, pierna de golpeo en naranja), alineadas en la pelvis. (b) Flexión de la rodilla y de la cadera de golpeo alrededor del contacto, laboratorio frente a reconstrucción desde una sola cámara en la misma condición: media ± DE de los 83 participantes de MoVi; el tiempo 0 es el contacto tomado del esqueleto de laboratorio.](../../resultados/paper_es/fig3_recon.png){#fig:recon width=100%}


## 3.4 Acuerdo en la condición típica de retransmisión

La Tabla {{tbl:agreement}} resume el acuerdo a 80 px y 25 fps, con residuos de retransmisión y contacto conocido.

- **Acuerdo moderado:** en las vistas de repetición (45–135°), solo dos rasgos lo alcanzaron entre jugadores:
  - la flexión máxima de la rodilla de golpeo (EAM 16,6°, IC 95 % 14,6–18,8; CCI 0,64, 0,55–0,71);
  - la extensión máxima de la cadera de golpeo (EAM 15,7°, 13,9–17,6; CCI 0,55, 0,39–0,68).
- **Acuerdo pobre:** el rango de movimiento de la cadera de golpeo (CCI 0,45) y ambas inclinaciones del tronco (CCI 0,42). En el tronco, el error absoluto fue pequeño (7,0–7,1°), pero la propia desviación estándar entre jugadores de la inclinación del tronco era de solo unos 7°.
- **Sin acuerdo:** la flexión de la rodilla de apoyo tuvo un sesgo de +15,6° y un CCI de 0,07; su gráfico de Bland–Altman muestra un sesgo proporcional, que crece con la flexión (Figura suplementaria {{figS:bland}}).
- **Dispersión:** los límites de acuerdo de los rasgos de la pierna abarcaron ±40–60°. La diferencia mínima detectable entre dos golpeos fue de 59–82°, mayor que el rango de valores observado entre jugadores.

El acuerdo fue menor al considerar todas las vistas, incluidas la frontal y la de espalda (Figura {{fig:icc}}).

: Acuerdo entre la estimación de tipo retransmisión y la captura óptica (MoVi, n = 83; 80 px, 25 fps, residuos de retransmisión, contacto conocido, vistas de repetición de 45–135°). EAM y CCI con intervalos de confianza del 95 % por remuestreo; DE: desviación estándar de la referencia entre jugadores. {#tbl:agreement}

| Variable | DE de referencia | Sesgo | EAM (IC 95 %) | Límites de acuerdo 95 % | CCI(2,1) (IC 95 %) | Clase |
|:---------------------|------:|-----:|----------------:|-------------:|----------------:|:-----|
| Flexión de la rodilla de apoyo en el contacto (°) | 8,8 | +15,6 | 20,4 (18,8–22,1) | −25,6 a 56,8 | 0,07 (0,02–0,13) | pobre |
| Flexión máxima de la rodilla de golpeo (°) | 28,7 | +3,0 | 16,6 (14,6–18,8) | −41,2 a 47,1 | 0,64 (0,55–0,71) | moderado |
| Extensión máxima de la cadera de golpeo (°) | 20,0 | +1,2 | 15,7 (13,9–17,6) | −40,9 a 43,3 | 0,55 (0,39–0,68) | moderado |
| Rango de movimiento de la cadera de golpeo (°) | 22,0 | +2,7 | 18,0 (15,5–21,1) | −55,3 a 60,7 | 0,45 (0,31–0,63) | pobre |
| Inclinación sagital del tronco en el contacto (°) | 7,0 | −1,6 | 7,1 (6,3–8,0) | −19,9 a 16,8 | 0,42 (0,28–0,54) | pobre |
| Inclinación lateral del tronco en el contacto (°) | 7,5 | −4,3 | 7,0 (6,2–7,9) | −19,9 a 11,3 | 0,42 (0,32–0,51) | pobre |
| Momento flexor máximo de cadera (N·m/kg) | 0,30 | +0,54 | 0,63 (0,54–0,72) | −1,01 a 2,09 | 0,10 (0,06–0,17) | pobre |
| Momento extensor máximo de rodilla (N·m/kg) | 0,11 | +0,11 | 0,17 (0,15–0,20) | −0,38 a 0,60 | 0,16 (0,04–0,30) | pobre |
| Momento flexor máximo de rodilla (N·m/kg) | 0,08 | +0,17 | 0,21 (0,18–0,24) | −0,30 a 0,64 | 0,06 (0,00–0,12) | pobre |

![Acuerdo entre jugadores, CCI(2,1), por rasgo y vista de cámara (MoVi, 80 px, 25 fps, residuos de retransmisión, contacto conocido).](../../resultados/paper_es/fig6_reliability.png){#fig:icc width=80%}

## 3.5 Vídeo real y gemelo digital

**Error 2D.** En las grabaciones reales de MoVi (82 participantes × 2 cámaras calibradas; 30 fps), el error 2D del detector frente a la captura proyectada fue del 2,7 % de la altura del jugador a resolución nativa (unos 330 px). Tras reducir a 120–50 px y comprimir en JPEG fue del 3,1–4,0 %, menos de la mitad del error en retransmisión con tamaños comparables.

**Rasgos.** Sus errores crecieron solo moderadamente de la resolución nativa a 50 px (Tabla {{tbl:real}}, Figura {{fig:real}}a):

- flexión máxima de la rodilla de golpeo, de 16,5° a 24,5°;
- rango de movimiento de la cadera de golpeo, de 16,0° a 17,7°;
- flexión de la rodilla de apoyo, de 10,3° a 12,8°;
- inclinación lateral del tronco, de 3,5° a 4,4°.

**Sesgos sistemáticos.** Dos rasgos tuvieron grandes sesgos que no dependían del tamaño de la imagen: la extensión máxima de la cadera de golpeo (+22°) y la inclinación sagital del tronco (−13°). Es coherente con las distintas definiciones de los puntos del detector (caderas y hombros en la superficie de la piel) y de los centros articulares biomecánicos.

**Acuerdo entre participantes a 80 px:**

- bueno para la inclinación lateral del tronco (CCI 0,71; 0,77 a resolución nativa);
- moderado para el rango de movimiento de la cadera de golpeo (0,67) y la flexión máxima de la rodilla de golpeo (0,56);
- pobre para los demás rasgos.

Conocer el instante de contacto redujo el error medio de 16,2° a 14,8°.

**Gemelo digital.** Reprodujo los errores con imagen real (Figura {{fig:real}}b, Tabla suplementaria S1). Simulamos cada grabación con su propia geometría de cámara y los residuos de RTMW de los demás participantes.

- **Error medio:** la simulación predijo el EAM medido con imágenes reales en las distintas combinaciones de rasgo, cámara y tamaño con *r* = 0,84 y una discrepancia absoluta media de 3,9° (13,0° simulado frente a 14,8° real).
- **Error individual:** también predijo qué participantes tendrían errores mayores (correlación media de los errores individuales por celda de 0,42).
- **Otros modelos de error:** sin ruido 2D, el gemelo fue demasiado optimista (8,9°). Con residuos de retransmisión fue más pesimista que las imágenes de laboratorio (17,6°), como cabía esperar por el mayor error del detector en retransmisión.
- **Rasgos con sesgo de definición:** la simulación fue algo optimista (extensión máxima de la cadera de golpeo, 17,8° frente a 24,0°; inclinación sagital del tronco, 8,9° frente a 13,4°).

Por tanto, los errores en retransmisión de los apartados 3.3–3.4 son, en todo caso, cotas inferiores.

: Acuerdo con la captura óptica en vídeo real (MoVi, 82 participantes, dos cámaras, contacto conocido). EAM en grados y, entre paréntesis, CCI(2,1). {#tbl:real}

| Rasgo | Nativa (~330 px) | 120 px | 80 px | 50 px | Sesgo a 80 px |
|:----------------------|----------:|----------:|----------:|----------:|------:|
| Flexión de la rodilla de apoyo en el contacto | 10,3 (0,45) | 11,4 (0,39) | 12,5 (0,27) | 12,8 (0,24) | −8,5 |
| Flexión máxima de la rodilla de golpeo | 16,5 (0,62) | 18,4 (0,61) | 20,3 (0,56) | 24,5 (0,48) | −8,8 |
| Extensión máxima de la cadera de golpeo | 22,4 (0,48) | 23,7 (0,42) | 24,1 (0,39) | 25,9 (0,29) | +23,4 |
| Rango de movimiento de la cadera de golpeo | 16,0 (0,68) | 15,5 (0,68) | 15,5 (0,67) | 17,7 (0,57) | +3,5 |
| Inclinación sagital del tronco en el contacto | 13,1 (0,18) | 13,5 (0,16) | 13,6 (0,15) | 13,4 (0,16) | −13,4 |
| Inclinación lateral del tronco en el contacto | 3,5 (0,77) | 3,8 (0,73) | 3,8 (0,71) | 4,4 (0,63) | −0,9 |

![Validación con imagen real. (a) EAM de cada rasgo en vídeo real a resolución nativa y reducido a tamaños de jugador de retransmisión. (b) Gemelo digital: EAM predicho al simular cada grabación con su propia geometría de cámara frente al EAM medido con las imágenes reales, para tres modelos de error 2D.](../../resultados/paper_es/fig7_real_video.png){#fig:real width=100%}

## 3.6 Cargas articulares de la pierna de golpeo

**Validez en laboratorio.** El índice de carga de laboratorio se comportó como cabe esperar de una medida de carga. Cada momento máximo aumentó con la intensidad del golpeo en los 83 participantes de MoVi (ρ de Spearman = 0,56–0,58 con la velocidad máxima del tobillo, todos con *p* < 10⁻⁷), y el Índice de Carga del Golpeo lo hizo con fuerza (ρ = 0,79; *p* < 10⁻¹⁸; Figura {{fig:load}}a). Los golpeos de balón de CMU produjeron momentos flexores máximos de cadera de 1,0–2,0 N·m/kg, frente a 0,71 ± 0,30 N·m/kg en los golpeos al aire de MoVi; el golpeo lento de CMU dio 0,43 N·m/kg.

**Desde vídeo de tipo retransmisión, no se recuperaron.** Los momentos máximos salieron sesgados al alza y su acuerdo entre jugadores fue pobre (CCI 0,06–0,16; Tabla {{tbl:agreement}}, Figura {{fig:load}}b), con pendientes de calibración λ de 0,05–0,11. El índice medido conservaría aproximadamente una décima parte de cualquier asociación verdadera.

**Sustituto postural.** Un modelo ridge que predice las cargas de laboratorio a partir de los seis rasgos posturales (dejando fuera un participante cada vez) explicó el 19–34 % de su varianza con la cinemática de laboratorio (*r* = 0,45–0,59). Aplicado a posturas estimadas en retransmisión alcanzó λ = 0,30–0,38: mejor que la dinámica inversa desde vídeo, pero todavía pobre.

**Tamaño del estudio de lesiones.** Con el modelo de dilución de la regresión, detectar un cociente de riesgos de 1,5 por desviación estándar del Índice de Carga del Golpeo verdadero requiere:

- con una medida de calidad de laboratorio, 48 lesiones (1–2 temporadas de LaLiga);
- con el sustituto postural, 126 (3–5 temporadas);
- con dinámica inversa desde vídeo de tipo retransmisión, unas 590 (12–24 temporadas).

Las temporadas suponen 0,05–0,10 lesiones de aductores o cuádriceps relacionadas con el golpeo por jugador y temporada: LaLiga EA Sports completa (≈ 500 jugadores) acumularía 25–50 lesiones de este tipo por temporada (Figura {{fig:load}}c).

![Cargas articulares de la pierna de golpeo. (a) Momento flexor máximo de cadera en laboratorio frente a la velocidad máxima del tobillo de golpeo (validez de constructo). (b) Momento flexor máximo de cadera desde vídeo de tipo retransmisión (80 px, 25 fps, vistas de repetición) frente a la referencia de laboratorio. (c) Lesiones necesarias para detectar un cociente de riesgos dado por DE de la carga verdadera en función de la fiabilidad λ del índice medido; líneas horizontales: lesiones que acumularía toda la liga en una temporada con dos incidencias supuestas.](../../resultados/paper_es/fig8_joint_load.png){#fig:load width=100%}

## 3.7 Remedios

*Fusión de repeticiones.* Promediar tres ángulos de repetición (45°, 90° y 135°) elevó el acuerdo entre jugadores respecto a una única cámara a 45° en:

- la extensión máxima de la cadera de golpeo: CCI 0,40 → 0,78, ya «bueno»; EAM 19,3° → 9,4°;
- la flexión máxima de la rodilla de golpeo: 0,61 → 0,76;
- el rango de movimiento de la cadera: 0,32 → 0,66;
- la inclinación sagital del tronco: 0,48 → 0,68.

Respecto a la vista lateral única, mejoró todos los rasgos salvo la inclinación lateral del tronco (Figura {{fig:improve}}). Dos repeticiones (45° y 135°) ya obtuvieron la mayor parte de la mejora.

*Corrección de sesgos.* Una corrección lineal por vista aprendida en golpeos de laboratorio:

- redujo los errores absolutos donde el sesgo era grande (flexión de la rodilla de apoyo, de 12,9–34,7° a unos 7°);
- no aumentó el acuerdo entre jugadores, porque no puede añadir información;
- aprendida en los golpeos al aire de MoVi y aplicada a los golpeos de balón de CMU, los empeoró claramente (flexión de la rodilla de apoyo, 4,8° → 31,2°; extensión máxima de la cadera de golpeo, 7,1° → 27,8°).

![Remedios a 80 px y 25 fps (MoVi, participantes no vistos): una sola cámara lateral frente a la fusión de tres repeticiones, cada una sin y con la corrección de sesgos aprendida en laboratorio.](../../resultados/paper_es/fig9_improvements.png){#fig:improve width=100%}

*Elevador adaptado al golpeo y a la retransmisión.*

- **Error 3D:** el ajuste fino redujo el MPJPE (en unidades de altura del jugador) en las ventanas sintéticas de los participantes reservados de 0,096 a 0,035 y 0,037 en los dos pliegues (−62 %).
- **Cámara virtual a 80 px** (participantes de MoVi no vistos, vistas de repetición): el error medio de los rasgos bajó de 14,3° a 7,8°. Cinco de los seis rasgos alcanzaron un acuerdo bueno entre jugadores (CCI 0,75–0,83); la flexión de la rodilla de apoyo pasó de 0,10 a 0,50 (Tabla suplementaria S2, Figura {{fig:finetune}}a). Como se usó el mismo banco de residuos de retransmisión en el entrenamiento y en esta prueba, estas cifras son una cota superior.
- **Vídeo real reducido a 80 px** (detecciones reales sobre imágenes que el modelo nunca vio): la mejora fue menor pero consistente en cinco rasgos.
  - Error medio: 15,0° → 13,1°.
  - Rango de movimiento de la cadera de golpeo: CCI 0,67 → 0,76.
  - Flexión máxima de la rodilla de golpeo: 0,56 → 0,67.
  - Inclinación lateral del tronco: 0,71 → 0,76.
  - Inclinación sagital del tronco: error 13,6° → 10,1°.
  - La flexión de la rodilla de apoyo empeoró ligeramente (12,5° → 14,5°).
- **Golpeos de balón de CMU,** ausentes de los datos de entrenamiento: el elevador adaptado fue peor que el oficial (error medio 12,0° → 17,9°; rango de movimiento de la cadera de golpeo 19,7° → 36,9°; Figura {{fig:finetune}}b). La adaptación a golpeos al aire no se transfiere a golpeos de fútbol con carrera previa e impacto.
- **Cargas articulares:** siguieron sin ser fiables tras la adaptación (CCI ≤ 0,33).

![MotionAGFormer oficial frente al adaptado al golpeo y a la retransmisión en (a) la cámara virtual con participantes de MoVi no vistos, (b) la cámara virtual con los golpeos de balón de CMU, nunca usados en el entrenamiento, y (c) vídeo real reducido a 80 px. Error absoluto medio; 80 px, residuos de retransmisión o detecciones reales, contacto conocido.](../../resultados/paper_es/fig10_finetune.png){#fig:finetune width=100%}


# 4. Discusión

## 4.1 Qué puede y qué no puede medir hoy el vídeo de retransmisión

Con modelos abiertos y de propósito general, el vídeo de calidad de retransmisión no ofrece una cinemática del golpeo fiable a nivel individual. En la condición típica de retransmisión, el error de los rasgos de la pierna fue del orden de 15–20°, comparable o mayor que las diferencias entre jugadores. Solo la flexión máxima de la rodilla de golpeo y la extensión de la cadera en el armado alcanzaron un acuerdo moderado entre jugadores.

Dos resultados merecen subrayarse porque van contra la intuición:

- **Un error absoluto pequeño no basta.** Las inclinaciones del tronco se midieron con errores de unos 7°, pero su acuerdo entre jugadores fue pobre, porque los jugadores difieren poco en esas variables. Una métrica de retransmisión debe juzgarse frente a la dispersión de la población que va a ordenar, no frente a su propio error.
- **La frecuencia de imagen no importó** (25 frente a 50 fps). Sí importaron la vista de cámara, el instante de contacto y el error del detector con jugadores pequeños.

Mejorar la biomecánica desde la retransmisión no es, por tanto, una cuestión de más imágenes por segundo. Es cuestión de detectar mejor en 2D a los jugadores pequeños, de elegir la cámara adecuada y de saber cuándo toca el pie el balón.

La estructura del error 2D también condiciona las conclusiones de un estudio. El ruido gaussiano independiente de la misma magnitud que el error real del detector exageró el error de varios rasgos hasta 1,8 veces. El temblor fotograma a fotograma es más dañino para un elevador temporal que los errores correlacionados en el tiempo que comete un detector real. Las simulaciones de biomecánica desde vídeo deberían usar secuencias de residuos reales, como hicimos aquí, o mejor aún validarse frente a imágenes reales. El gemelo digital mostró que una simulación alimentada con residuos reales predice con precisión los errores con imagen real (r = 0,84; discrepancia media de 3,9°) y, si acaso, los infraestima ligeramente.

## 4.2 El balón conectado y el cuerpo

La información más eficaz de nuestros experimentos fue el instante de contacto. Detectarlo en la postura reconstruida (pico de velocidad del tobillo) aumentó en un tercio el error de los rasgos de la pierna respecto a conocerlo (error absoluto medio de 23,1° frente a 17,4°).

En LaLiga EA Sports, el balón conectado ya mide este instante en cada contacto [@laliga2026], con una resolución inferior a un fotograma. Nuestro análisis de CMU indica que esa resolución es suficiente: el pico de velocidad del tobillo precede al contacto real en unos 20 ms, menos de un fotograma de retransmisión, y desplazar el instante esa cantidad altera los rasgos como mucho 2°. Fusionar la marca temporal del balón con la postura de la retransmisión no es, por tanto, un refinamiento menor, sino un requisito para que la biomecánica del golpeo desde vídeo sea utilizable.

Las repeticiones son una segunda fuente de mejora gratuita. Promediar los tres ángulos de repetición elevó el acuerdo entre jugadores en todos los rasgos de la pierna y el tronco salvo la flexión de la rodilla de apoyo. La extensión máxima de la cadera de golpeo pasó de pobre a buena (CCI 0,40 → 0,78 respecto a una sola cámara a 45°).

## 4.3 Un índice de carga articular («sufrimiento articular»): medible en el laboratorio, aún no desde la televisión

El modelo de dinámica inversa de la pierna de golpeo se comportó como debe hacerlo una medida de carga:

- el Índice de Carga del Golpeo aumentó con fuerza con la intensidad del golpeo en 83 participantes (ρ de Spearman = 0,79);
- los golpeos de balón de CMU cargaron los flexores de cadera entre dos y tres veces más que los suaves golpeos al aire de MoVi;
- el único golpeo lento de CMU tuvo un tercio de la carga de los golpeos completos.

Los momentos máximos flexor de cadera y extensor de rodilla son la contrapartida mecánica de la exigencia excéntrica sobre el recto femoral y el iliopsoas en la transición del armado al balanceo hacia delante. Es la fase implicada en las roturas del recto femoral y de los aductores [@mendiguchia2013; @serner2019; @charnock2009].

Sin embargo, desde vídeo de tipo retransmisión el mismo índice no se pudo recuperar: su fiabilidad cayó a λ ≈ 0,08. La dinámica inversa necesita derivadas segundas de las posiciones articulares que una reconstrucción a 25 fps no contiene. Un sustituto basado solo en la postura, que predice la carga de laboratorio a partir de los seis ángulos, fue más robusto (λ ≈ 0,38). Pero, incluso con una cinemática de laboratorio perfecta, explicó solo un tercio de la varianza de la carga.

Esto tiene una consecuencia directa para quien quiera un «índice de lesión» desde el vídeo de retransmisión:

- **El error de medida atenúa cualquier asociación verdadera con la lesión,** así que el número de lesiones que necesita un estudio de validación crece como 1/λ.
- **Con una medida de calidad de laboratorio,** detectar un cociente de riesgos de 1,5 por desviación estándar de la carga requeriría unas 48 lesiones relacionadas con el golpeo, de una a dos temporadas de LaLiga con la incidencia supuesta.
- **Con la estimación actual desde la retransmisión,** el requisito sube a unas 590 lesiones: entre doce y veinticuatro temporadas de toda la liga. Un estudio tan largo estaría confundido por los cambios de plantillas, entrenamiento y práctica médica.

El camino práctico, por tanto, no es ajustar ahora un modelo de lesión con rasgos de retransmisión. Primero hay que elevar la fiabilidad de la medida, con adaptación específica al fútbol, entrada multivista y el balón conectado. Solo entonces conviene realizar un estudio prospectivo con los servicios médicos de los clubes.

## 4.4 Qué hace falta: datos específicos de fútbol

Dos remedios fueron baratos y útiles, pero ninguno se transfirió a los golpeos reales de balón:

- **Corrección de sesgos aprendida en laboratorio:** redujo el error absoluto donde el sesgo era grande, por ejemplo en la flexión de la rodilla de apoyo. Pero no añade información y, sobre todo, una corrección aprendida con golpeos al aire empeoró los errores de los golpeos reales de balón (rodilla de apoyo 4,8° → 31,2°; extensión máxima de la cadera de golpeo 7,1° → 27,8°).
- **Elevador adaptado al golpeo con ruido de retransmisión:** redujo aproximadamente a la mitad el error simulado con participantes no vistos y mejoró cinco de seis rasgos con imágenes reales. Pero empeoró los golpeos de balón de CMU (error medio 12,0° → 17,9°).

Ambos hallazgos apuntan al mismo cuello de botella: los modelos y las correcciones deben entrenarse y validarse con golpeos de fútbol. Es decir, disparos con carrera previa e impacto con el balón, filmados con cámaras de retransmisión y con 3D sincronizada. Esos datos existen dentro de los clubes (laboratorios de biomecánica, sistemas multicámara en los campos de entrenamiento) y de las ligas (sistemas de cámaras en los estadios para el seguimiento). Ahí es donde una colaboración con un club aportaría más valor. El protocolo que se publica con este trabajo convierte cualquier conjunto de ese tipo en un banco de validación en cuestión de horas.

Dos detalles de implementación tuvieron efectos de primer orden y son fáciles de hacer mal:

- **Normalizar la entrada 2D a la imagen completa,** como hace la demo pública, hizo ilegibles para el elevador a los jugadores pequeños (errores de 50–90° sin ningún ruido). Un recorte centrado en el jugador lo resuelve.
- **Pasar como confianzas las puntuaciones brutas del detector,** que en RTMW no son probabilidades, sesgó la flexión reconstruida de la rodilla de golpeo en unos 40°.

Ninguno de los dos problemas produce un mensaje de error: solo una biomecánica equivocada.

## 4.5 Recomendaciones para analistas y servicios médicos

1. **Ángulos de la pierna en un disparo individual:** considerarlos poco fiables salvo que el jugador mida al menos 80 px, la vista sea lateral o a 45° y se conozca el instante de contacto. Agregar varias repeticiones y varios disparos por jugador.
2. **Inclinación del tronco:** no interpretar las diferencias entre jugadores como reales sin comprobar la dispersión entre jugadores de la población que se ordena.
3. **Cargas:** no usar la dinámica inversa, las velocidades articulares ni las cargas desde la retransmisión para decisiones individuales. Si hace falta un índice de carga, preferir sustitutos posturales e informar de su fiabilidad.
4. **Contacto:** anclar cada golpeo al instante de contacto del balón conectado.
5. **Métricas de proveedores:** antes de implantar cualquier métrica de técnica o carga, pedir su acuerdo con la captura óptica en condiciones de retransmisión. El protocolo aquí presentado ofrece uno.

## 4.6 Limitaciones

**Verdad de referencia.**

- Procede del laboratorio. Solo siete golpeos (de dos participantes) son golpeos de fútbol auténticos con balón.
- Los 83 golpeos de MoVi son golpeos al aire de no futbolistas, más lentos que los disparos de partido.
- Los errores del elevador fueron mayores en los golpeos de balón (15,0° frente a 9,2° sin ruido 2D). Por tanto, los errores aquí descritos probablemente sean optimistas para disparos de partido a máxima potencia.

**Error 2D.**

- Se midió en 200 disparos de retransmisión de una sola competición, con anotaciones manuales que incluyen su propio error; es una cota superior del error del detector.
- Para jugadores de más de unos 90 px se extrapola por escalado.

**Simulación y vídeo real.**

- La cámara virtual reproduce la geometría, el tamaño, la frecuencia de imagen y el error del detector. No reproduce el desenfoque de movimiento, la oclusión por otros jugadores ni el movimiento de la cámara de retransmisión; el gemelo digital solo lo aborda para imágenes de laboratorio.
- La validación con vídeo real usó dos cámaras fijas a 4–5 m, no cámaras de estadio.
- La escala y la vertical se dieron como conocidas (estatura y calibración del campo); en la práctica ambas añaden error.

**Cargas e incidencia.**

- Las cargas articulares se calcularon con un modelo simplificado (sin inercia del pie, sin rotación axial y sin impacto del balón), idéntico para la referencia y la estimación. Por eso cuantifican la medibilidad, no la carga tisular absoluta.
- La incidencia de lesiones del análisis de viabilidad es una suposición explícita, no una medida.

**Ajuste y modelos.**

- El banco de residuos de retransmisión usado para ajustar el elevador se usó también en la prueba correspondiente con la cámara virtual, así que esa mejora es una cota superior. La prueba con vídeo real no tiene ese solapamiento.
- Evaluamos un solo detector y un solo elevador. Otros modelos pueden comportarse de otra forma, y por eso se publica el banco de pruebas.

## 4.7 Trabajo futuro con un club o una liga

Una Fase 2 prospectiva combinaría:

1. vídeo de retransmisión y de cámara táctica de cada disparo;
2. el instante de contacto y la velocidad del balón conectado;
3. sesiones de captura óptica o multicámara del club con los mismos jugadores, para adaptar y validar con datos específicos de fútbol;
4. los registros de lesiones del servicio médico.

El primer entregable sería un informe de fiabilidad por rasgo y por cámara. Solo los rasgos que alcanzaran λ ≥ 0,75 entrarían en un modelo de lesión, lo que mantendría el estudio prospectivo en una o dos temporadas.

# 5. Conclusiones

1. **La detección en la retransmisión es el cuello de botella.** Su error es de en torno al 10 % de la altura de un jugador típico que dispara, más del doble que en vídeo de laboratorio. Su estructura temporal importa: los modelos de ruido gaussiano exageran su efecto hasta 1,8 veces.
2. **Lo medible con una sola cámara y modelos abiertos:** la flexión máxima de la rodilla de golpeo y la extensión de la cadera en el armado son los únicos rasgos con un acuerdo moderado entre jugadores. La flexión de la rodilla de apoyo no es medible. Las inclinaciones del tronco tienen errores pequeños, pero no permiten ordenar a los jugadores.
3. **La frecuencia de imagen es irrelevante entre 25 y 50 fps.** La vista de cámara y el instante de contacto son decisivos, y la marca temporal del balón conectado reduce los errores en una cuarta parte.
4. **La fusión de repeticiones es una mejora gratuita.** La adaptación con datos sintéticos de retransmisión ayuda dentro del movimiento con el que se entrenó, pero no se transfirió a los golpeos reales de balón. Hacen falta datos de entrenamiento y validación específicos de fútbol.
5. **Un índice de carga articular de la pierna de golpeo es válido en el laboratorio, pero hoy no es medible desde la retransmisión.** Con la fiabilidad actual, validarlo como predictor de lesiones llevaría una década de datos de lesiones de toda la liga. El camino es primero elevar la fiabilidad, con captura óptica del club, el balón conectado y entrada multivista, y después realizar un estudio prospectivo con los servicios médicos.

# Agradecimientos

Los datos de CMU usados en este proyecto se obtuvieron de mocap.cs.cmu.edu; la base de datos se creó con financiación de la NSF (EIA-0196217). Agradecemos al BioMotion Lab (MoVi), a los autores de 3DSP/AutoSoccerPose y de SoccerNet, a OpenMMLab (RTMW, YOLOX) y a los autores de MotionAGFormer que hayan publicado sus datos y modelos.

# Financiación

Esta investigación no recibió financiación específica.

# Conflicto de intereses

Ninguno. El autor trabaja como Research Engineer en IA y Cardiología Computacional en el ICICOR – Hospital Clínico Universitario de Valladolid (HCUV); este estudio se realizó de forma independiente, al margen de ese puesto, y no utilizó recursos ni datos de la institución.

# Referencias

::: {#refs}
:::

# Figuras suplementarias

<!-- SUPLEMENTO -->

![Pico de velocidad del tobillo frente al contacto real con el balón en los golpeos de CMU. (a) Velocidad del tobillo de golpeo alineada con el contacto extrapolado; los puntos marcan el pico. (b) Desfase del pico respecto al contacto; la franja gris es un fotograma a 25 fps.](../../resultados/paper_es/fig2_contact.png){#figS:contact width=100%}

![Efecto de (a) el modelo de error 2D, (b) la frecuencia de imagen y (c) conocer el instante de contacto, con el jugador a 80 px.](../../resultados/paper_es/fig5_ablation.png){#figS:ablation width=100%}

![Cámara de retransmisión virtual, golpeos reales de balón (CMU, n = 7), 25 fps, residuos de retransmisión y contacto conocido: error absoluto medio de cada rasgo frente a la altura del jugador, por vista de cámara.](../../resultados/paper_es/figS1_sensitivity_cmu.png){#figS:senscmu width=100%}

![Error del elevador sin ruido 2D (error absoluto medio de los seis rasgos, todas las vistas y tamaños, 25 fps) frente a la intensidad del golpeo (velocidad máxima del tobillo de golpeo). Golpeos al aire de MoVi y golpeos de balón de CMU.](../../resultados/paper_es/figS2_intensity.png){#figS:intensity width=60%}

![Gráficos de Bland–Altman de los seis rasgos cinemáticos en la condición típica de retransmisión (MoVi, n = 83; 80 px, 25 fps, residuos de retransmisión, contacto conocido; vistas de repetición 45°, lateral y 135°). Línea continua: sesgo; discontinuas: límites de acuerdo del 95 %.](../../resultados/paper_es/figS3_bland.png){#figS:bland width=100%}
