# Preservación de superficie en la separación de ScrollFiesta

Se corrigieron dos decisiones en el pipeline local, como prototipo optativo. Se conserva el detector de solapamientos, el multicut, el descarte de menos de 16 caras, el re-mallado y los guards de manifold.

## Fallos reproducidos con mallas guardadas

En MLS suave, la propiedad por tamaño/área descartaba 17 piezas (241 caras); 237 centroides están etiquetados como capa 390 y cuatro sin etiqueta. Las caras descartadas no presentan cruces 3D con las retenidas en el chequeo numérico, aunque muchas son incompatibles en la proyección 2D.
Una prueba de añadir solo caras compatibles y otra de optimizar área en componentes bipartitos no recuperaron la punta. No se integraron esas alternativas.
Al preservar las piezas, se activa el re-mallado por pieza. El owner suave pasó de 5.960 a 5.922 caras y de 946,550 a 885,283 vóxel²; un vértice de su borde original quedó a 6,660 vóxeles de la reconstrucción. El API devolvía cero también al aplazar o fallar y el caller lo contaba como reconstrucción.

## Cambio concreto

- Antes de borrar una pieza por tamaño, exigir que cada triángulo esté cubierto en 3D por un triángulo del owner, dentro de 0,25 vóxeles.
- Antes de sustituir una pieza por su re-mallado, exigir cobertura en ambas direcciones dentro de 0,5 vóxeles y cero pares de solapamiento proyectado en el candidato. Si no se demuestra, restaurar la pieza original y recuperar temporales.
- No contar como reconstrucción los no-op, aplazamientos o candidatos rechazados. API y comportamiento geométrico por defecto preservados.

La cobertura exige que los tres vértices de una cara estén cerca del mismo triángulo destino. Por convexidad de la distancia a un conjunto convexo, esto acota también el interior de la cara en aritmética exacta. La implementación usa punto flotante y no es una certificación formal. El criterio es conservador: puede rechazar una retriangulación idéntica con diagonal distinta; al superar un millón de comparaciones considera la cobertura no demostrada. No se interpreta ese rechazo como una pérdida medida ni se ajustaron los umbrales para forzar aceptación.

## Resultados en el mismo recorte limpio

| Caso | Cobertura total de referencia | Distancia total al extremo (vóxeles) | Piezas | Cruces nativos |
| --- | ---: | ---: | ---: | ---: |
| mls-edge-off | 1999 | 4.103 | 1 | 0 |
| mls-edge-soft | 2115 | 5.259 | 1 | 0 |
| split-shape-off | 2056 | 2.994 | 2 | 0 |
| split-shape-soft | 2197 | 2.649 | 3 | 0 |

Con MLS suave fijo, cobertura total 2.115 → 2.197 (+3,9 %) y distancia 5,259 → 2,649. La versión sin MLS adaptativo también recupera superficie: 1.999 → 2.056 y 4,103 → 2,994. El conjunto suave conserva 14.684 muestras de caras directamente en 390 y 14 sin etiqueta; ninguna en otra capa etiquetada. Las 14.698 corresponden a 390 dentro del radio de evaluación de dos vóxeles. El área total es 990,914 vóxel² y 988,113 tienen apoyo CT dentro de un vóxel.

**La mejora corresponde al conjunto de piezas, no a una malla indexada única.** El componente de la semilla suave conserva cobertura 2.115 y distancia 5,259. La pieza que conserva la punta comparte 17 aristas de borde con el owner, exactamente coincidentes en las coordenadas float32 guardadas y presentes en la fuente anterior al corte. La tercera comparte siete aristas con el owner. No se soldaron índices ni se revirtieron los cortes del separador. Esta coincidencia geométrica no certifica por sí sola identidad anatómica.

## Validación

- Compilación incremental correcta; cinco pruebas del helper de cobertura pasan.
- Cuatro fixtures positivos/negativos calibran el predicado nativo: duplicado, borde compartido, planos separados y cruce.
- IntersectionCleanup_audit_visit sobre cada VMESH completo, con gap_max=0 e include_hinges=1: cero overlap, stab y fold en ambos controles y ambas salidas corregidas. Incluye pares entre piezas; no se modificó ninguna cara durante el audit.
- El chequeo anterior de un contacto en soft no equivalía a un cruce interior: el auditor nativo de cruces da cero también sobre ese control anterior.
- Guard final nativo: cero aristas no manifold, cero pinch-split y cero reorientaciones en ambas salidas nuevas.
- Con el prototipo desactivado, vértices/normales/caras finales coinciden exactamente con el control anterior.
- Revisión independiente de código por un subagente Sol/high: sin bloqueantes en rollback/arena/default/API. No ejecutó las pruebas.
- Fallos iniciales de preparación de helpers: faltó -fopenmp al enlazar el auditor y GNU17/POSIX al compilar el fixture. Se corrigieron los comandos; los logs fallidos se conservan. No fueron fallos del juego ni de las corridas nativas.

## Recursos y alcance

Ejecuciones de cálculo secuenciales, 384 MiB máximos, swap cero, CPU 25 % de un núcleo, Nice=19, IOWeight=10 y GPU inaccesible. El mínimo disponible observado fue 9553 MiB, por encima de la reserva de 3.072 MiB. El mayor pico de servicio observado en las compilaciones/pruebas fue aproximadamente 160 MiB; la integración final alcanzó aproximadamente 149 MiB.
Un único recorte de desarrollo con corredor condicionado por ruta conocida. No se ha validado generalización, ni corrido la suite CTest completa, ni certificado una separación mínima entre hojas. El wrapper de cobertura se aplica al re-mallado de esta fase de split; la llamada anterior del pipeline queda fuera del alcance.

## Artefactos y estado

Diff enfocado: split-ownership-coverage.patch (solo pipeline_cube.c). Binario: build/cube_mesh.split-coverage. Activación: VES_OVERLAP_COVERAGE_GUARD=1; añadir MLS_EDGE_ADAPT=soft para la variante suave.
Se conserva adaptive8 como selección estable anterior; split-shape-soft queda como candidato de investigación. No se publicó ni se hizo commit/push. No se tocó AnyPS5 ni se cambió su rama.
