# Primera conexión de nuestras mallas reparadas con CT y un campo de tinta

28 de octubre de 2026. **Puente técnico ejecutado y verificado; recuperación de tinta/texto NO validada.** Se conservaron todas las mallas, los controles y los intentos. Solo se usó Sol, sin Astra. Base geométrica experimental ScrollFiesta `bce8a65f97652316efb084171a17d2f1f8d3ae1a`, con sus atribuciones y licencias.

## Resultado principal

La comparación antes/después ya consulta datos reales en las caras que recuperamos. Boundary Grafting añade27caras con una señal candidata en una **predicción volumétrica pública**; Hole Recovery v5 añade17caras cuya puntuación es muy baja. Las caras comunes conservan sus consultas exactamente. Esto demuestra la conexión técnica y la conservación del muestreo, **no demuestra letras rescatadas**.

La comprobación CTantiguo→CTmoderno no superó los criterios de coherencia local predeclarados, tanto con muestreo puntual como con promediado de la huella de vóxel. Por ello **no se acepta la asociación anatómica de la señal predicha con nuestra superficie**. No se corrigió el afín buscando tinta ni se rebajaron los criterios. El afín catalogado sigue siendo una hipótesis reproducible; este fallo diagnóstico no prueba que la matriz sea incorrecta.

## Comparaciones que aíslan los dos cambios

| Experimento | Antes | Después | Conservación comprobada |
| --- | --- | --- | --- |
| Boundary Grafting, antes del relleno | v1, step7:5112caras | v5, step7:5139caras | 5112caras idénticas+27recuperadas; ninguna eliminada |
| Hole Recovery | v4 seguro, final:5143caras | v5, final:5160caras | 5143caras idénticas+17recuperadas; ninguna eliminada |

Se usa el step7 para aislar grafting y v4 seguro para aislar el hueco. No se utiliza como control una malla con el duplicado opuesto de v2, que introduciría ambigüedad de normales. Coordenadas y orientación se conservan mediante triángulos canónicos: rotación cíclica y orden lexicográfico; sus índices guardados **no son el orden original de caras VMESH**. Cada triángulo y cada entrada quedan trazables por coordenadas y SHA.

Las27caras aportan0,000341903mm² y las17caras0,001362358mm², calculados en el marco histórico7,91µm. Son superficies muy pequeñas. Todas las caras originales, los resultados geométricos v5 y sus certificados permanecen sin cambios.

## CT propio y límite del detector2D

Fuente: cubo `01744_02256_04048`, CT históricoPHercParis4 `20230205180739`,7,91µm, NRRDuint8nativeXYZ. Se verificaron su SHA y la reconstrucción byteidéntica del parentRAW ya congelado. VMESHworldZYX→sourceXYZ se comprueba con tres anclas no colineales, roundtrip0, control de interpolación lineal sintética y muestra de rejilla exacta. No se interpreta genéricamente el `space origin`NRRD como un mundoXYZ nuevo: se conserva el convenio del dataset y la cadena de preparación existente.

Se extrajeron21planos de diagnóstico a lo largo de cada normal de cara, con84consultas trilineales y pooling4: offsets físicos `(j-54)*2,4µm`, j13:97. Los perfiles de las5112/5143caras comunes son **bitidénticos** antes/después. Son perfiles por cara, **no un surface-volume aplanado ni entrada válida del detector**. El signo anatómico de las normales no está certificado.

La selección original tiene253,12µm por eje. El detectorink9um necesita128×128píxeles a9,6µm:1228,8µm por lado. El área total de v5 es0,080560595mm², frente a1,50994944mm² de un parche del modelo:5,335% sumando todas las piezas. Por ello el gate2D se mantiene **rechazado**. No se estiró la malla ni se rellenó con ceros para fabricar contexto; no se ejecutó aquí el detector2D sobre esta región.

## Alternativa ejecutada: proyección de ink3D publicado

Se reutilizó el [campo público oficial](https://vesuvius-challenge-open-data.s3.amazonaws.com/PHercParis4/representations/predictions/ink-3d/20260411134726-ink3d-20260428123845-v3-78k-fullsup.zarr/.zattrs), catalogado para el CTmoderno20260411134726. **Es inferencia ajena publicada, no un detector propio ni inferencia ejecutada aquí.** La revisión `REPAIRED_MESH_PUBLIC_INK3D_REVIEW.md` documenta sus fuentes y el uso upstream de proyecciones3D sobre superficies. No se atribuye un checkpoint binario exacto sin su procedencia.

La metadata adquirida confirma ZYX, L0shape75784×32693×32693, chunks256³, uint8, BloscZstd, sin filtros. Se usa el afín completoXYZantiguo→XYZmoderno del catálogo, y se recalculan normales en el destino. L0 evita incertidumbres de fase de pirámide. Doschunks descargados proporcionaron todas las muestras, sin faltantes ni sustituciones por cero.

Protocolo nuevo declarado: nearest`floor(q+.5)`; centro de cada cara y11offsets normales−5..5vóxelesL0, es decir±12µm. Se conservan las11puntuaciones, posiciones, índices, máscara y primerargmáx. La banda simétrica evita elegir un lado por el signo de la normal, pero no certifica hoja ni orientación anatómica. No es un replay del compositeupstreamL2±48µm.

Se usan **scoresuint8 crudos0..255**. No se encontró certificación de la fórmula de cuantización de este artefacto; no se presentan como probabilidades calibradas. PHercParis4 intervino en entrenamiento/desarrollo del enfoque; el solapamiento de estaROI con entrenamiento es desconocido. No es holdout.

## Comprobación densa de la señal candidata

Para evitar depender de un único centroide, se incluyeron **todas** las27/17caras añadidas y sus17/16vecinas retenidas por arista, seleccionadas geométricamente sin usar scores. Cada triángulo se subdivide en n²celdas de igual área, n=ceil(arista máxima enL0), y se muestrea su centro. La arista máxima de subtriángulo es≤2,4µm. Centro es la medida principal; máximo11 es secundaria. No se seleccionaron caras, profundidad o umbral para producir letras.

| Grupo | Caras | Muestras | Media de score en superficie, ponderada por área | Media del máximo11, ponderada por área | Máximo en superficie |
| --- | ---: | ---: | ---: | ---: | ---: |
| Borde recuperado | 27 | 372 | 58,6073 | 82,8913 | 204 |
| Vecinas retenidas del borde | 17 | 211 | 51,4596 | 92,0379 | 196 |
| Hueco recuperado | 17 | 1970 | 1,23287 | 1,89518 | 2 |
| Vecinas retenidas del hueco | 16 | 562 | 1,55973 | 1,94685 | 2 |

El máximo11 alcanza245 en parte del borde recuperado y su vecindad; no se limita a un centroide aislado. El hueco y su vecindad mantienen valores1..2 en este campo. No se convierte ese fondo no nulo en tinta. La media del borde recuperado no supera sistemáticamente a la vecindad: **no es una mejora medida de precisión del detector**.

Los puntos comparten vóxeles/campo y no son observaciones independientes. La cuadratura es aproximada, no integral exacta ni certificado de cobertura continua de tinta. Los pesos corresponden al área física original7,91µm. En torno al13% del área de las caras de borde, un extremo de la banda supera estrictamente al interior; se conserva el perfil completo para no ocultar sensibilidad a desplazamientos.

`verification-v1.json` pasó: hashes de artefactos e índices/áreas, matriz frente a la entrada real de catálogo, triángulos y perfiles comunes, consultas al campo reproducidas desde los chunks recibidos, máximos/argmáx,CSV de centroides y medias/histogramas densos. La generación de cuadratura/ring se revisó estáticamente; el replay usa sus coordenadas guardadas y no es una segunda reconstrucción independiente. LosCSV por cara densos tienen hash, no se afirma replay de su contenido aritmético.

## Comprobación local entre escaneos: no aceptada

Se adquirieron12chunks reales del CTmodernoL0, uint8sincompresión, para la mismaROI. El afín queda fijo; no se usaron scores de tinta ni se optimizó transformación. Se comparan32768centros del ROIantiguo32³ con el CTmoderno, frente a seis controles desplazados±4vóxeles antiguos enXYZ. Antes de medir se fijaron Pearson≥0,6 y margen≥0,1 sobre el mejor control.

| Ensayo | Pearson sin desplazamiento | Mejor control | Margen | Gate |
| --- | ---: | ---: | ---: | --- |
| CTmoderno trilineal puntual | 0,593729 | 0,582866 | 0,010863 | Rechazado |
| Media de64puntos de la huella de cada vóxel antiguo | 0,617110 | 0,605313 | 0,011797 | Rechazado |

El segundo ensayo aproxima la integración sobre cada celda antigua mediante4³midpoints transformados al CTmoderno. Mantiene laROI, controles, afín y gates; no estima la función de dispersión real de los escáneres. Se conservan ambos resultados. Mejora algo la correlación, pero **no discrimina suficientemente el emplazamiento frente a los desplazamientos de control**. Las adquisiciones tienen distinta resolución, energía y respuesta; esta comprobación no identifica la causa ni demuestra que la matriz sea errónea.

Por tanto, `anatomical_registration_error_voxels` permanece`null`. Las puntuaciones altas son una candidata bajo el afín nominal, **no una asociación anatómica validada ni prueba irrefutable de tinta o texto rescatado**. Este es el límite principal de aceptación actual.

## Recursos, fallos preservados y archivos

Todo se ejecutó secuencialmente con CPU25%, Nice19, IOWeight10, **MemoryMax384MiB**, swap0, GPU inaccesible, hilos1 y reserva3072MiB. No se necesitó el presupuesto2GiB de inferencia. MáximoRSSobservado del pilotoCT144,63MiB; el controlCTpuntual tuvo mínimoMemAvailable8207,22MiB. No se cerraron aplicaciones, publicaron datos, hicieron commits/push ni enviaron candidaturas.

Se conservaron dos errores de preparación: la primera proyección falló al serializar índicesNumPy antes de descargar campo, y la primera comprobaciónCT supuso un compresor cuando la metadata declaraba`null`. Se corrigieron en destinos nuevos; no se sustituyeron sus logs ni snapshots. El404 de`zarr.json` es una consulta de formato descartada; la metadataZarrv2 fue adquirida con200.

Directorio de trabajo: `research/repaired-mesh-ink-v1/`:

- `mesh-ct-pilot-v1/`: geometría, perfilesCT y vistas antes/después.
- `public-ink3d-projection-v2/`:11consultas por cara, posiciones y scores publicados, con dos chunks de fuente.
- `dense-ink3d-v1/`: todos los puntos añadidos/vecindad, pesos y perfiles.
- `ct-registration-v2/` y `ct-registration-footprint-v1/`: CTreal, controles y rechazos.
- `verification-v1.json`: replay técnico pasado.
- `evidence-manifest-v1.json`: cierre con fuentes, datos recibidos y hashes; comprobar el resultado del job de cierre antes de citarlo como completado.

Las imágenes son proyecciones ortogonales de mallas o cortesCT, no un aplanado legible. **Naranja marca geometría añadida, nunca tinta.** Las regiones blancas del mapa3D representan el score publicado en escala visual0..255, no caracteres confirmados.

## Decisión

La prueba produjo un puente técnico reutilizable y una candidata localizada en el borde; **no pasó la aceptación de recuperación de tinta/texto**. El siguiente dato necesario es una correspondencia local entre escaneos con suficiente contexto y controles estructurales reservados, usandoCT y sin ajustar por tinta. Para el detector2D también hace falta una superficie continua de contexto real mayor, a escala métrica correcta. La reparación geométrica sigue verificada por sus certificados previos, independientemente de estos rechazos.
