# Recuperación completa sobre mallas guardadas — candidato v5

Actualización posterior: la integración y el pipeline completo ya pasaron; también se obtuvo el certificado de cobertura continua de superficies completas. Véase `FULL_RECOVERY_REPORT.md`. El texto siguiente conserva el alcance y estado de esta evaluación guardada al realizarse.

Estado: candidato de investigación verificado en geometría guardada; la integración y ejecución completa todavía están pendientes. Base experimental atribuida a ScrollFiesta público bce8a65f97652316efb084171a17d2f1f8d3ae1a; no se modificaron ni sustituyeron los binarios v1/v2/v4 congelados.

La búsqueda canónica de triangulaciones del ciclo original de 19 IDs conserva todas las coordenadas e índices fuente. Con la métrica angular real de las 5139 caras, v4 rechaza la propuesta greedy duplicada; la búsqueda encontró una alternativa completa de 17 caras tras 1206 nodos. Se examinaron 969 triples, de los que 713 resultaron admisibles bajo los filtros existentes. No se añadieron Steiner ni se soldaron o movieron vértices.

El candidato pasa frontera indexada exacta, fans angulares reales, orientación y auditoría nativa de todas las caras. Además, el verificador independiente con fracciones exactas de binary32 comprobó 267 pares con AABB solapada: ninguna intersección fuera del punto/arista geométricos comunes. Sus 16 controles pasaron, incluido un STAB con vértice compartido que el auditor nativo puede omitir. Esta comprobación solo audita pares nuevos/fuente y nuevos/nuevos, no vuelve a certificar todos los pares fuente/fuente.

Se combinaron las 17 caras nuevas con las 4 de otro relleno válido de v4, conservando todas las 5139 caras fuente. La diferencia de orden en dumps por componentes se trató como tal, con inclusión de multiconjuntos orientados, sin borrar ni reorientar fuente.

| Medida +32Y | v4 | Candidato guardado |
| --- | ---: | ---: |
| Caras finales | 5143 | 5160 |
| Cobertura anotada a radio1 | 2239 | 2241 |
| Área total, vóxel² | 1265,792586 | 1287,566595 |
| Conflictos nativos | 0 | 0 |
| Conflictos exactos nuevos/fuente y nuevos/nuevos | No había parche nuevo | 0 |
| Borde fuente máximo perdido | 0,759852 | 0,759852 |

La cobertura recuperada cuenta ID248:2240 e ID247:1, como v2; no certifica identidad anatómica. Toda la fuente y las otras cuatro caras sobreviven exactamente. El área es área de triangulación, no una medición independiente del área física del papiro.

Como evaluación finita adicional, 221 muestras del relleno rechazado de v2 quedaron como máximo a0,083666vóxeles de la nueva superficie; 387 muestras nuevas quedaron como máximo a0,117177vóxeles de v2. Ninguna superó0,25. Esto por sí solo no demuestra cobertura continua: se está preparando un certificado conservador de subdivisión con aritmética exacta. La proximidad y el soporte de intensidad tampoco certifican seguimiento de fibras.

Evidencia: `candidate-boundary-only-01.vmesh` y su `*-exact.json`; combinación y métricas en `saved-evaluation-02/{combined.vmesh,strict.json,native.json,native-pairs.csv,metrics.json}`. Los intentos previos y errores de harness se conservaron; `saved-evaluation-01` falló antes del análisis geométrico por una suposición incorrecta sobre orden de caras en dumps. Logs guardados `research/native/hf-recovery-*`. Todo cómputo fue secuencial con CPU25%, Nice19, IOWeight10, memoria384MiB, swap0, GPU inaccesible, un hilo y reserva de escritorio3072MiB. No hubo publicación ni envío.
