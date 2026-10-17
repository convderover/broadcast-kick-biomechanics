# Biomecánica del disparo desde la retransmisión: ¿qué se puede medir de verdad?

*[English version](README.md)* · Roberto Martín Gutiérrez · [ORCID 0009-0004-5724-3502](https://orcid.org/0009-0004-5724-3502)

Validación, frente a captura óptica, de los rasgos del golpeo (rodilla, cadera, tronco) y de la **carga articular de la pierna de golpeo** estimados desde una sola cámara en condiciones de retransmisión. Aplicación prevista: LaLiga EA Sports e Hypermotion, como complemento del balón conectado (xBALL). El sensor mide el balón; esto mide el cuerpo.

## 🟢 En sencillo

¿Puede un ordenador, viendo un disparo por la tele, medir bien cómo golpea el jugador y cuánto "sufren" su cadera y su rodilla? Para saberlo hay que comparar con golpeos en los que se conoce la verdad, porque se grabaron en laboratorio con marcadores. Lo hacemos de tres maneras:

1. **Cámara de TV virtual:** 90 golpeos de laboratorio (7 golpeos reales de balón y 83 participantes de MoVi) "filmados" desde 5 ángulos, con el jugador de 400 a 50 píxeles y a 25 o 50 fps. A lo que ve la cámara se le añade el error real del detector, medido en 200 disparos de la Premier League.
2. **Vídeo real:** grabaciones con la 3D de laboratorio sincronizada (MoVi, 83 personas utilizables, 2 cámaras), reducidas al tamaño de un jugador en TV.
3. **Gemelo digital:** cada grabación real se simula con su misma geometría para comprobar que el simulador predice el error real.

Para la carga articular, la pierna que golpea va por el aire, así que sus momentos en cadera y rodilla se calculan con dinámica inversa sin plataformas de fuerza. Así hay una "verdad" de laboratorio con la que validar lo que se mide desde la tele.

**Lo que no es:** un predictor de lesiones validado. Eso exige datos médicos de clubes. Aquí se calcula cuántas lesiones habría que observar para validarlo, en función de la fiabilidad medida.

## 🗺️ El mapa técnico

```
datos/cmu/*.c3d  (7 golpeos de balón, 120 Hz)      datos/movi/3d (83 sujetos útiles, Visual3D) + datos/movi/video (PG1/PG2, 30 fps)
        └──────────────┬──────────────────────────────────┘
               golpeo/ensayos.py → Ensayo(x17, fps, contacto, masa, sexo)
                       │
   golpeo/cinematica.py (6 rasgos)   golpeo/carga.py (dinámica inversa de la pierna de golpeo, de Leva 1996)
                       │
datos/3dsp (200 disparos Premier) → medir_error_2d.py → error2d_3dsp.csv, modelo_ruido.json
                                              └→ golpeo/ruido.py (banco de residuos reales con estructura temporal)
                       │
experimento_sensibilidad.py: golpeo/camara.py (cámara virtual) + ruido → golpeo/elevador.py (MotionAGFormer-B)
                       │                                              → resultados/sensibilidad.csv, ensayos.csv
validar_video_movi.py: YOLOX + RTMW (golpeo/detector.py) sobre vídeo real reducido → video_movi.csv, video_movi_2d.csv
gemelo_movi.py: simulación de cada toma real con su geometría                       → gemelo_movi.csv
                       │
informe_sensibilidad.py → figuras de resultados, tablas 2–7, resumen_resultados.json
ondas_movi.py + figuras_articulo.py → fig1_design (diseño), fig2_model (esqueleto y momentos),
                          fig3_recon (reconstrucción y curvas medias), figS3_bland (Bland–Altman)
    (todas las figuras salen en inglés en resultados/paper/ y en español en resultados/paper_es/)
analisis_carga.py       → fig8_joint_load.png, table6_joint_load.csv, resumen_carga.json
videos.py               → resultados/videos/*.mp4 (H.264)
generar_documentos.py   → docs/manuscrito/manuscript.pdf/.docx (inglés), manuscrito_es.pdf/.docx (español),
                          docs/dossier/dossier_clubes.pdf
```

Módulos de `golpeo/`:
- `esqueleto`, `h36m`: esqueletos canónico (8) y Human3.6M (17); `coco_to_h36m` como en la demo oficial.
- `cinematica`: ángulos, pierna de golpeo, contacto aproximado y los 6 rasgos; alineamiento rígido (Kabsch).
- `carga`: momentos netos de rodilla y cadera de la pierna de golpeo, con filtro Butterworth y picos normalizados por la masa.
- `contacto`: contacto real extrapolado desde la salida del balón.
- `camara`: cámara de TV virtual.
- `ruido`: banco de residuos 2D reales (3DSP o MoVi).
- `elevador`: MotionAGFormer-B sobre un recorte centrado en la pelvis.
- `detector`: RTMW-x y YOLOX-m con onnxruntime en GPU.
- `datos_cmu`, `datos_movi` (con la cámara calibrada de MoVi en convenio MATLAB), `ensayos`: lectores de datos.
- `metricas`: sesgo, MAE, Bland–Altman, r, ICC(2,1), pendiente de calibración y diferencia mínima detectable.
- `degradacion`, `error2d`: degradación de imágenes y emparejamiento de COCO con 3DSP.
- `video`: escritura en MP4 H.264 y texto Unicode.

## Cómo reproducirlo

```bash
pip install -r requirements.txt
pip install rtmlib==0.0.16 --no-deps
python descargar_recursos.py            # ~500 MB: modelos, 3DSP y CMU
python descargar_movi.py 3d             # 3,8 GB: 3D de MoVi (licencia no comercial)
python descargar_movi.py video todos    # ~41 GB: vídeo de las cámaras fijas de MoVi
python -m pytest -q                     # tests
python comparar_contacto_cmu.py
python medir_error_2d.py 1              # ~2,5 min en GPU
python experimento_sensibilidad.py      # ~1 h en GPU
python validar_video_movi.py            # ~2 h en GPU
python gemelo_movi.py
python informe_sensibilidad.py
python analisis_carga.py
python videos.py
python generar_documentos.py
```

Probado en Windows 11, Python 3.11, RTX 5060 (8 GB). Si hay un proxy con certificado propio, instala `truststore`: los descargadores lo usan solos.

## Usarlo como banco de pruebas con otro modelo

Para evaluar otro elevador 2D→3D, o una versión ajustada, con la misma entrada 2D que el oficial:

```bash
python experimento_sensibilidad.py todo --rapido --elevadores oficial,ruta/a/pesos.pth.tr --salida mi_modelo
python validar_video_movi.py --elevador ruta/a/pesos.pth.tr --salida mi_modelo_video   # usa la 2D ya detectada
```

- **Pesos:** deben tener la arquitectura de MotionAGFormer-B. Para otro modelo distinto, basta con una clase con el método `lift_person(uv, conf)` como la de `golpeo/elevador.py`.
- **Ruido de retransmisión:** el banco de residuos (`resultados/error2d_3dsp.csv`, solo números, sin imágenes) permite reproducirlo sin acceso a las imágenes de 3DSP.
- **Ajuste propio:** `ajustar_elevador.py` adapta MotionAGFormer al golpeo con ruido de retransmisión; `evaluar_ajuste.py` lo compara con el oficial en sujetos no vistos.

## Licencias de los datos

No redistribuyas datos ni imágenes:
- **3DSP:** imágenes de retransmisión con derechos; las figuras y vídeos marcados `USO_INTERNO` no se publican.
- **MoVi:** solo investigación no comercial; no se puede ceder a terceros.
- **CMU:** libre para investigación, citando la base.

Hay que citar CMU, MoVi, 3DSP/AutoSoccerPose (y SoccerNet), RTMW/YOLOX (OpenMMLab) y MotionAGFormer. Las referencias están en `docs/manuscrito/referencias.bib`.
