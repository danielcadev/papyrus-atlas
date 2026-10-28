# Letras dudosas frente a la referencia publicada

28 de octubre de 2026. Trabajo con Sol, sin Astra. **La secuencia local es compatible mediante comparación asistida con ΠΟΡΦΥΡΑϹ; no hay confirmación independiente completa de las ocho letras.** No se alteraron inferencia, probabilidades, geometría v5 ni protecciones para conseguir coincidencia. Se conserva el dictamen ciego anterior.

## Qué se pudo resolver

El nuevo dictamen `ink-reading/word-letter-comparison-v1/ASSISTED_READING.md` favorece agrupar los dos candidatos iniciales como **una Π con segunda asta curvada**, en vez de leer Τ y Ϲ por separado. La comparación de las imágenes oficiales de Luke/Nader ayuda a reconocer esa agrupación. La descripción paleográfica primaria sobre el asta curvada respalda la posibilidad formal; no es una máscara por letra ni prueba de segmentación única.

La referencia editorial identifica **ΠΟΡΦΥΡΑϹ / πορφύρας** en [First Letters](https://scrollprize.org/firstletters), con contexto **columna −12, línea 4** en [Nicolardi et al., CErc54/2024](https://www.iris.unina.it/handle/11588/985203). `PUBLISHED_WORD_LETTER_REFERENCE.md` separa las afirmaciones primarias de lo que sigue sin estar demostrado aquí. La discusión de una Υ incompleta en col.−14/l.6 es **otra ubicación**, y no se usó para justificar el quinto signo de esta palabra.

| Lugar editorial | Observación local asistida | Estado |
| --- | --- | --- |
| Π | Dos astas bajo barra común; segunda curvada a la derecha | Segmentación inicial favorecida por comparación; anterior negativa conservada |
| Ο | Contorno cerrado | Compatible y visualmente claro |
| Ρ | Bucle superior incompleto/dudoso y asta descendente | Tentativa; detalle nativo conservado |
| Φ | Asta y dos interiores oscuros | Compatible y visualmente claro |
| Υ | Barra ancha y asta central; apariencia de Τ | **Υ depende de la referencia; no se resolvió el contraste Τ/Υ** |
| Ρ | Asta y bucle superior derecho | Compatible y visualmente claro |
| Α | Oblicuos e interior triangular, enlazado al siguiente signo | Favorecida por comparación, detalle aún sujeto a lectura asistida |
| Ϲ | Curva abierta hacia la derecha | Compatible; el límite léxico procede de la edición |

Transcripción conservadora: **Π Ο Ρ? Φ [forma Τ; Υ por referencia] Ρ Α? Ϲ**. Los espacios separan posiciones para inspección, no espacios observados en el papiro. La revisión nativa posterior está completada en `word-letter-native-detail-v1/NATIVE_REVIEW.md`: el bucle de Ρ sigue dudoso, Α muestra posible travesaño sin continuidad segura, y Υ conserva forma de Τ. No cambia el veredicto ni sustituye el dictamen anterior.

## Correspondencia espacial comprobada y pendiente

Se probó un **par de imágenes nuevo**: predicción local congelada frente a imágenes oficiales de Nader/Luke, con SIFT recíproco y gates conservadores predeclarados. Resultado2/0coincidencias; ambos rechazados. No se exportó transformación aceptada, no se bajaron los gates y no se usaron los rechazos anteriores como mapas válidos. La fuente exacta ejecutada queda en `register_local_word_reference_source_v1.py`. La revisión posterior corrigió en el script activo la fase al exportar centros INTER_AREA4: `original=4*scaled+1.5`. Esta rama no se ejecutó en el resultado rechazado; no cambian sus métricas ni sus hashes.

Una comprobación distinta usó **coordenadas fijadas por los metadatos**, sin optimizar transformación: el preview moderno12160×4360 tiene la mitad de las dimensiones L2. La ROI L2 Y2048:3072,X14080:18816 corresponde a preview Y1024:1536,X7040:9408. La probabilidad local se redujo por media de área2×2.

Resultado de `ink-word-preview-coordinate-check-02`: **Pearson0,888157**, mitades0,885198/0,892192. Ocho controles con desplazamientos o reflejos alcanzaron como máximo0,320475; margen0,567682. Pasan los gates fijados de0,75global,0,70por mitad y0,15margen. La versión2 además valida estado, shape/dtype, origenROI, metadatos y SHA del original GrandPrize; versión1 conservada. Revisión estática `WORD_PREVIEW_COORDINATE_REVIEW.md` respalda el alcance de coherencia2D para esta ROI.

**Esto corrobora ubicación y orientación 2D frente al preview moderno.** No constituye una estadística de unicidad global, ni independencia entre modelos/entrenamiento, ni registro numérico a la edición, ni mapa a CT3D original. Las predicciones pueden compartir sesgos. La semejanza editorial de los paneles se declara asistida; no se convierte en certificación anatómica.

## Nuevas imágenes y conservación

`word-letter-comparison-v1` contiene paneles separados local/Luke/Nader y el original GrandPrize16317×1686 adquirido de la fuente oficial con recibo y SHA. Los paneles se redimensionan por separado únicamente para visualización y no definen un mapa geométrico. No se pegaron letras sobre la predicción.

`word-letter-native-detail-v1` conserva crops nativos de las posiciones3/5/7, sus probabilidades float32 y dos visualizaciones fijadas antes de inspeccionarlas: contraste upstream y `p*255`. No hay suavizado, relleno, OCR, umbral seleccionado, nueva profundidad ni inferencia repetida. El quinto signo conserva el aspecto de Τ en ambas vistas; no aparece una bifurcación inequívoca que autorice completar Υ por imagen.

Todas las ejecuciones fueron secuenciales bajo `run_ink_guarded.sh`, CPU25%, Nice19, IOWeight10, MemoryMax2GiB, swap0, GPU inaccesible, hilos1 y reserva3GiB. Los datos de guard y recursos están en `research/native/ink-{local-word-reference-register-01,word-letter-comparison-01,word-preview-coordinate-check-01,word-preview-coordinate-check-02,word-native-letter-render-01}.*`. No se cerraron aplicaciones ni se publicaron resultados. El inventario original `word-evidence-v1` se mantiene; el cierre de esta fase se registra por separado con enlace SHA al anterior.

## Conclusión y dato que falta

### Ensayo acotado de profundidad

Antes de otra inspección se fijó `word-uncertain-depth-probe-v1/plan.json`: evaluar **todas las cinco** ventanas17/21planos, z_start0/1/2/3/4. La centralz2 se reutiliza y las otras cuatro se calculan secuencialmente sobre XYlocalY256:768,X1920:2560. Se compara solo el interiorY320:704,X1984:2496, quitando halo64 para conservar exactamente los mismos soportes de patches que en la inferencia completa. Son63tiles por ventana nueva,252totales; no selección de profundidad por acuerdo con la palabra.

Es desarrollo asistido: desplazar la ventana cambia simultáneamente el contexto de17planos y la normalización por patch; no es una medición independiente de tinta ni certifica una profundidad anatómica. La revisión `WORD_DEPTH_PROBE_REVIEW.md` y el verificador separado preservan esa condición.

`ink-word-depth-probe-01` completó las cuatro inferencias en **281,12s**, RSSmáximo526,89MiB y MemAvailablemín10297,21MiB. Las cinco vistas están conservadas, sin escoger una profundidad. `ink-word-depth-validation-01` pasó en1,20s: SHA de todos los artefactos, parámetros y cadena de fuentes, shapes/dtypes/rangos, cobertura completa, pesos y máscaras interiores bitidénticos a z2, cuatro reconstruccionesNPZ→probabilidad bitidénticas, y recortez2 bitidéntico al resultado completo congelado.

| z_start | Diferencia media absoluta de probabilidad frente a z2 | Pearson frente a z2 |
| --- | ---: | ---: |
| 0 | 0,033336 | 0,910645 |
| 1 | 0,012880 | 0,990132 |
| 2 reutilizada | 0 | 1 |
| 3 | 0,010139 | 0,994505 |
| 4 | 0,017850 | 0,982810 |

El principal inspeccionó todas las vistas de contraste fijo y probabilidad lineal: **persiste la barra ancha con asta central; no aparece bifurcación inequívoca**. El lector Sol también completó su dictamen separado en `DEPTH_READING.md`: ninguna de las cinco ventanas ni el modo lineal discrimina Υ/Τ; no cambia el veredicto. Declara exposición previa y ausencia de revisión paleográfica certificada. No se confunde la correlación entre predicciones con precisión de letras.

Se avanzó en la segmentación inicial Π y se corroboró la ubicación2D. **La palabra editorial está identificada; su lectura completa desde nuestra salida local sigue siendo asistida y ambigua**, principalmente Υ/Τ y la primera Ρ. Con las mismas probabilidades no es honesto prometer que otra lectura automática resolverá los trazos faltantes.

Para cerrar la verificación falta una correspondencia editorial medida y evidencia adicional que discrimine los trazos, o una revisión paleográfica de las imágenes de origen. El mapa CT3D y la conexión con nuestras mallas siguen pendientes. Este ensayo aporta evidencia de reproducción asistida; no acredita por sí solo una nueva lectura ni una candidatura ganadora.
