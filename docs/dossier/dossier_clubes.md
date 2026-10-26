---
title: "Biomecánica del disparo desde la retransmisión"
subtitle: "Qué se puede medir de verdad, cómo mejorarlo y qué haría falta para un índice de riesgo de lesión"
author: "Roberto Martín Gutiérrez · convderover@gmail.com"
date: "Octubre de 2026"
---

**Roberto Martín Gutiérrez** · Ingeniero biomédico (Grado y Máster, Universidad de Valladolid) · ORCID 0009-0004-5724-3502
convderover@gmail.com · www.linkedin.com/in/roberto-martín-gutiérrez-ingeniería-biomédica

# En una frase

El balón conectado de LaLiga mide el balón; este trabajo mide **el cuerpo que lo golpea desde la tele**, y compara sus estimaciones con captura óptica bajo condiciones controladas y criterios exploratorios.

# Qué he hecho

- **Error real del detector en emisiones de fútbol:** 6.000 detecciones en 200 disparos de la Premier League.
- **Verdad de laboratorio:** 7 golpeos de balón de 2 personas (CMU) y 83 golpeos al aire de 83 personas (MoVi), con captura óptica a 120 Hz.
- **Cámara de TV virtual:** 5 ángulos, jugador de 400 a 50 px, 25/50 fps, con el error real de la retransmisión.
- **Vídeo real con 3D sincronizada:** 162 grabaciones de 82 personas, y un gemelo digital para contrastar errores agregados.
- **Carga articular de la pierna de golpeo** (cadera y rodilla) por dinámica inversa, sin plataformas de fuerza.
- **Tres remedios evaluados:** corrección de sesgos, fusión de repeticiones y un modelo 3D adaptado al golpeo con ruido de retransmisión.
- **Código abierto:** pruebas unitarias y protocolo reproducible de evaluación de acuerdo.

# Qué acuerdo se observó desde la tele

![Acuerdo entre participantes (ICC) por rasgo y contexto. Clasificación descriptiva: verde, bueno; ámbar, moderado; rojo, pobre; no son umbrales clínicos ni deportivos.](../../resultados/paper/semaforo_es.png){width=80%}

**Lectura para un club:**

- **Criterios operativos exploratorios:** ninguna variable de una sola cámara superó los criterios seleccionados (15–20° de error en la pierna). Con 3 repeticiones simuladas y corrección de laboratorio, la flexión de rodilla superó el criterio de ordenación y el tronco el de comparación con laboratorio; no son umbrales deportivos ni clínicos validados. **Ninguna sirve aún para seguir los cambios de un jugador.**
- **Acuerdo observado:** la flexión de rodilla de golpeo y la extensión de cadera en el armado tuvieron acuerdo moderado; combinar repeticiones mejoró algunas medidas. La rodilla de apoyo tuvo acuerdo pobre en las condiciones estudiadas.
- **Frecuencia de imagen:** pasar de 25 a 50 fps no mejoró los resultados de este experimento. Influyeron la vista de cámara, el error del detector y conocer el contacto.
- **Contacto conocido:** usar el instante de referencia redujo el error alrededor del 25% frente a detectarlo desde la reconstrucción. No se evaluó directamente un sensor de balón ni una integración con xBALL.
- **El gemelo digital predice errores agregados de laboratorio:** asociación entre errores simulados y de vídeo real (r = 0,84, ~4° de diferencia).
- **Comprobado con golpeos reales:** con mis propios disparos grabados con un móvil, la velocidad del tobillo y la postura distinguen un golpeo fuerte de uno suave desde el lateral, pero no de frente.
- **Adaptar el modelo 3D al golpeo:**
  - **Con golpeos al aire:** baja el error de 14,7° a 8,3° en simulación y mejora 4 de 6 rasgos en vídeo real.
  - **Con golpeos reales con balón:** **empeora**.

# ¿Y un índice de "sufrimiento articular" o de riesgo de lesión?

- **Consistencia en laboratorio:** KLI y velocidad del tobillo se correlacionan (ρ = 0,79), pero comparten la entrada cinemática. No es validación independiente de carga tisular ni de riesgo de lesión.
- **Acuerdo desde vídeo:** KLI CCI = 0,090 (IC 95% 0,018–0,181), r = 0,204 y pendiente b = 0,081. El sustituto postural dio r = 0,303, CCI = 0,275 y b = 0,380; su transferencia se ajustó con todos los participantes y no es una validación externa. Las pendientes no estiman fiabilidad.
- **Sensibilidad hipotética:** HR = 1,5 y fracciones de información q = 1, 0,5, 0,2 y 0,1 dan 48, 96, 239 y 478 eventos. No son muestras para validar este KLI ni se traducen en temporadas. No se midieron lesiones ni incidencia.
- **Conclusión práctica:** hacen falta datos de fútbol con referencia, repetición entre sesiones y validación prospectiva antes de atribuir utilidad individual o predictiva.

# Qué puedo aportar a un club o a LaLiga

1. **Auditoría de métricas de proveedores:** comparar métricas de técnica o carga con una referencia y documentar sus límites por condición.
2. **Fase 2 con datos del club:** vídeo de partidos y entrenamientos + xBALL + sesiones de captura del propio equipo para adaptar el modelo al fútbol. El primer entregable es un informe de fiabilidad por rasgo y cámara.
3. **Investigación prospectiva con el cuerpo médico:** solo tras caracterizar el error y la repetibilidad en fútbol, justificar un modelo clínico y definir el efecto y los resultados relevantes; este estudio no fija su tamaño ni duración.

**Material:** artículo (preprint en inglés), código, vídeos explicativos y figuras en {{REPO_URL}}. Las imágenes de retransmisión y las de MoVi no se publican por licencia.

**Versión y límites:** preprint publicado el 26/10/2026 en [SportRxiv](https://doi.org/10.51224/SportRxiv.1131), sin revisión por pares. La escala y el alineamiento de las condiciones principales proceden de la referencia; el contacto y la pierna se conocen. El ejemplo de campo son 13 golpeos del autor, sin referencia. No se ha validado seguimiento longitudinal ni predicción de lesiones. [Estado de versiones](../PUBLICATION_VERSION.md).
