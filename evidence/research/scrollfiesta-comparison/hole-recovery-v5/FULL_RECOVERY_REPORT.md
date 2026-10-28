# Recuperación v5 y continuidad entre cores — 28 de octubre de 2026

La recuperación del hueco de +32Y está integrada como experimento opt-in y validada desde la entrada congelada completa. La continuidad entre los dos cores +32Z sigue pendiente: no se ejecutó una soldadura sin calibración válida. Se preservan los controles y todo el historial. Base experimental: ScrollFiesta público, revisión bce8a65f97652316efb084171a17d2f1f8d3ae1a, con sus atribuciones y licencias.

## Resultado del hueco

Se sustituye la propuesta greedy que introducía un triángulo geométrico duplicado por una búsqueda acotada de triangulaciones completas del mismo ciclo de 19 vértices. No se mueve, fusiona ni elimina ningún vértice o cara fuente; no hay Steiner. Se conservan los certificados de frontera, orientación, fans angulares reales y los filtros de intersección existentes. La búsqueda devuelve rechazo atómico si no encuentra candidato o agota sus presupuestos.

| Medida +32Y | v4 | v5 completo |
| --- | ---: | ---: |
| Caras fuente retenidas exactamente | 5139 | 5139 |
| Otras caras válidas del relleno | 4 | 4 |
| Caras del ciclo recuperado | 0 | 17 |
| Caras finales | 5143 | 5160 |
| Cobertura anotada a radio 1 | 2239 | 2241 |
| Área de malla, vóxel² | 1265,792586 | 1287,566595 |
| Conflictos nativos | 0 | 0 |
| Duplicados / degenerados finales | 0 / 0 | 0 / 0 |
| Máxima distancia de 427 sondas de borde | 0,759852 | 0,759852 |

`full-evaluation-01/metrics.json` exige igualdad binaria de step7 con el control, conservación de índices/coordenadas y multiconjuntos orientados en step8 y step11. La geometría orientada completa coincide exactamente con `saved-evaluation-02/combined.vmesh`: se reutilizan sus auditorías y métricas, sin repetirlas por un cambio de orden de caras. SHA256 de step8/final: `b93672d63891ad10c079215a5d7296f9ba4a7a5134e25750f8ba35761c11d65f`.

La auditoría racional independiente cubre todos los pares nuevos/fuente-v4 y nuevos/nuevos con AABB solapada: 267 pares, cero intersecciones fuera del simplex de esquinas exactas comunes. Los pares fuente/fuente no se recertifican con ese predicado; la auditoría nativa sí incluye la malla completa. No se presenta el detector nativo como prueba exacta general, pues puede omitir ciertos contactos con vértices compartidos.

`continuous-coverage-02.json` certifica que cada punto de ambas superficies completas, antigua v2 y nueva, está a distancia ≤1/4 vóxel de la otra. Usa aritmética racional, subdivisión y testigos baricéntricos; el fondo v4 se retiene exactamente. Las dos direcciones tienen 769 y 2534 hojas, profundidades máximas 4 y 5, sin pendientes. Esto es una cota de distancia continua, no igualdad de áreas, topología o identidad anatómica. La prueba parche-contra-parche previa `continuous-coverage-01.json` fue inconclusa en una dirección; se conserva, y no se aumentó la tolerancia para obtener el certificado posterior.

Un segundo programa, `research/verify_patch_coverage_witnesses.py`, verificó los 3303 testigos sin importar el productor ni usar búsqueda, AABB o heurísticas de punto cercano. Reconstruyó hashes, inclusión orientada, índices, pesos racionales, particiones completas sin prefijos y cada desigualdad exacta. Sus nueve pruebas pasaron; resultado `continuous-coverage-witness-replay-01.json`, passed=true. Comparte únicamente el lector estricto VMESH con el auditor exacto. La igualdad geométrica orientada certificada del pipeline transfiere esa cota a la salida completa.

El replay con flag `0` es byteidéntico a v4; con flag `1` coincide como multiconjunto geométrico orientado con la combinación certificada (`replay-certificate.json`). El pipeline completo activo terminó Status OK, guardias cero. Original, central y +32X también terminaron Status OK, guardias cero, step7 y finales byteidénticos a v4/v2: `regressions-v5-01/regressions.json`. Las auditorías de esos controles se reutilizan por esa igualdad.

Se ejecutaron además los dos cores +32Z con el mismo v5 activo, comandos/stdin congelados y destinos nuevos: `halo-regressions-v5-01/regressions.json`. En ambos, step7/8/11/12 son byteidénticos a v4, Status OK y guardias cero. Se reutilizan la unión de 13346 caras, sus auditorías y distancias de costura de `evaluation-v2`; no se volvió a medir la misma geometría ni se hizo una soldadura.

## Activación y límites

Binario congelado `../build/cube_mesh.holefill-v5`; activación explícita `VES_HOLE_RECOVERY_SEARCH=1`, junto a `MLS_EDGE_ADAPT=soft` y `VES_OVERLAP_COVERAGE_GUARD=1`. El flag no es una autorización para aceptar otras salidas sin auditoría exacta posterior. El helper es genérico para ciclos de hasta 19 vértices, con máximo 2 millones de nodos y 20 millones de pruebas de pares; no contiene coordenadas o cantidades de caras del fixture. En el pipeline real usó 1241 nodos y 1740580 pares. La búsqueda no vuelve exacto el predicado nativo ni audita automáticamente rellenos futuros: el gate offline sigue siendo obligatorio para este experimento.

La cobertura 2241 incluye ID248:2240 e ID247:1. La proximidad a anotaciones, el soporte CT y el área triangulada no demuestran identidad anatómica ni seguimiento de fibras. Las ventanas siguen perteneciendo al mismo cubo/rollo; falta validación independiente.

## Continuidad entre cores

El preflight existente certifica diez componentes que son discos, sin winding inválido ni no-manifold, y detecta el plano worldX4176. Se obtuvo el umbilicus oficial de PHercParis4 y su transformación catalogada al CT local; no se usa el eje de otro papiro. La medición CT v1 no identificó un pitch defendible en ninguno de sus 81 perfiles. Se conservaron `axis_valid=true`, `calibration_valid=false` y `winding_gate_ready=false`.

Los inventarios de etiquetas y las vistas CT nuevas son desarrollo asistido, no validación ciega. La región anotada 248 muestra varias bandas que convergen en Z; sus centros de soporte no son centros de hojas ni pasos entre vueltas. No se arma el gate con un promedio arbitrario. El adaptador rechaza explícitamente calibraciones no válidas antes de soldar. Las futuras tablas deben verificar carga nativa, hash y cobertura radial, sin fallback a scalar ni extrapolación silenciosa.

También se generaron seis cortes ortogonales completos YZ/XZ del cubo ya local (`research/native/paris4-seam-orthogonal-v1/`). La inspección de YZ-X128 y XZ-Y128 conserva la ambigüedad de interfaces/ramas de la región exterior, sin justificar todavía un pitch. Revisión y operación siguiente concreta: `research/PARIS4_ORTHOGONAL_REVIEW.md`; no se declara que sea obligatorio obtener datos externos antes de trazar ese vecindario 3D.

Se ejecutó una única comprobación local inicial, con criterios de aceptación escritos antes de sus resultados: `research/native/paris4-local-branches-v1/diagnosis.json`. El detector de prominencia local no aceptó semillas de ninguna de las dos bandas anchas. Guardó perfiles CT y cortes ortogonales por las mismas posiciones3D; no ejecutó normales, interfaces ni seguimiento posterior. Es una parada del método congelado, no prueba de ausencia de material ni de imposibilidad de identificación manual. No se retocaron reglas para forzar una semilla o un pitch. `research/PARIS4_LOCAL_BRANCH_RESULT.md` conserva cifras, inspección visual, alcance y el dato asistido local que falta.

Además, doce vértices de una cadena izquierda están a distancia mínima 8,474 del otro core, superior al límite transversal existente de 6. Esto impide una arista transversal desde esos vértices, aunque se resuelva winding; no demuestra imposibilidad de unir todo el componente. Diagnóstico y decisión: `../../CORE_CONTINUITY_NEXT_DECISION.md`. No se amplían distancias ni se desarman filtros para obtener una unión aparente.

## Evidencia y ejecución

Fuentes: `source/src/holefill/hole_fill.c` y `hole_recovery_search.inc` bajo la carpeta de comparación; snapshot anterior `hole_fill.v4.c` en esta carpeta. Evaluadores, pruebas exactas y revisión independiente están en `research/`. Logs y estados únicos: `research/native/hf-recovery-*`, `hf-full-y32-v5-01.*`, `paris4-*`; artefactos CT en `research/native/paris4-calibration-context-v1/`. Se preservaron también los intentos fallidos de harness, las propuestas rechazadas y sus salidas.

Todo cómputo fue secuencial bajo CPUQuota25%, Nice19, IOWeight10, MemoryMax384MiB, swap0, dispositivos GPU inaccesibles, un hilo numérico y reserva de escritorio3072MiB. Hubo varios agentes Astra para tareas independientes y Sol ultra para revisión crítica. No se publicó, envió, hizo commit ni push.
