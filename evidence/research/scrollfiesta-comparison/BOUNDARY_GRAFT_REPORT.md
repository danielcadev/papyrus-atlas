# Recuperación de bordes por caras fuente — v2

Prototipo local sobre ScrollFiesta público, base fijada `bce8a65f97652316efb084171a17d2f1f8d3ae1a`. Esta extensión se aplica encima de `split-ownership-coverage.patch`, conserva MLS suave y no modifica la predicción de entrada. No se publicó ni hizo commit/push. El 29/30 de octubre es una fecha tentativa para revisar una posible entrega, no un envío programado.

## Fallo reproducido y cambio

En el recorte central, los propietarios retenidos tenían 9.526 y 269 caras. Las piezas menores de 16 caras todavía perdían 41 triángulos fuente: rechazar su descarte por falta de cobertura no las salvaba del mínimo posterior. Unir cada pieza completa tampoco era válido: contenía caras incompatibles con sus vecinos.

La v2 conserva los propietarios originales y recupera **subconjuntos** de caras pequeñas por aristas originales. Cada cara puede incorporarse a cualquier propietario vecino conservado, incluyendo el de 269 caras; no solo al mayor. La elección es determinista: más aristas compartidas y luego menor ID. Una cara bloqueada puede reintentarse cuando otro vecino proporciona un propietario nuevo.

El grafo simétrico de incompatibilidades se consulta con las asignaciones actuales, incluidas las caras recuperadas anteriormente. No se mueven vértices, inventan triángulos, fusionan propietarios ni desactiva el mínimo de 16 caras para los fragmentos restantes. Las etiquetas se escriben solo después de verificar todos los pares incompatibles registrados. Siguen funcionando las protecciones de extracción y manifold.

El detector antes truncaba silenciosamente su lista temporal de pares. Ahora devuelve también si la lista se truncó; la recuperación nueva se desactiva en ese caso. Los llamadores anteriores conservan sus resultados previos. La lista sigue excluyendo caras con vértices compartidos; conservar sus restricciones no equivale a una prueba universal de ausencia de cruces 3D.

El trabajo está activado solo por `VES_OVERLAP_COVERAGE_GUARD=1`. El comportamiento desactivado produjo exactamente el mismo VMESH que el control congelado. La reserva adicional de memoria se limita conservadoramente a 128 MiB; las estructuras usan los límites int32 de CSR. Construirlas usa ordenación `O(E log E)`.

## Resultados del proceso completo

Comparación incremental contra la v1 con su protección de cobertura ya activada, siempre MLS suave y misma entrada. Cobertura = vóxeles anotados únicos a radio 1 de muestras de caras con separación máxima 0,75 vóxeles. No es una certificación de identidad de hojas.

| Caso | Caras recuperadas | Cobertura v1 → v2 | Área v1 → v2 (vóxel²) | Borde máximo perdido v1 → v2 | Puntos de borde a más de 1 vóxel | Auditoría 3D v1 → v2 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Desarrollo original con ruta condicionada | 16 | 2197 → 2207 | 990,914 → 993,914 | No se compara este extremo | No medido aquí | 0 → 0 |
| Ventana central de otro cubo | 13 | 2262 → 2265 | 1559,887 → 1562,788 | 2,066 → 1,526 | 5 → 4 de 400 | 0 → 0 |
| Vecina +32 X | No cambio | 1829 → 1829 | 2090,457 → 2090,457 | 0,322 → 0,322 | 0 → 0 de 401 | 0 → 0 |
| Ventana nueva +32 Y, fijada antes del resultado | 27 | 2237 → 2241 | 1275,378 → 1280,842 | 1,312 → 0,760 | 3 → 0 de 427 | 1 → 1, mismo par exacto |

La vecina +32 X tiene salida idéntica byte a byte: se reutilizaron sus métricas y auditoría en vez de repetirlas. En el recorte original, el objetivo conocido permanece a 2,649 vóxeles; esta v2 amplía superficie, no mejora ese objetivo. En la central, las 13 caras coinciden exactamente con los IDs del prototipo guardado. Tres de sus cinco pérdidas mejoran, pero cuatro puntos siguen a más de un vóxel.

La ventana nueva se fijó después de congelar el código y el binario v2, sin usar etiquetas, semilla ni objetivo para su entrada Otsu. No se buscaron otras ventanas después de ver su resultado. La cobertura por ID cambia de `{248:2237}` a `{248:2240,247:1}`; el total no debe presentarse como cobertura exclusivamente de la hoja 248. Las muestras directas de las caras no contienen ID247; el vóxel adicional entra en el radio de evaluación. No se interpreta esto como prueba de salto ni de identidad correcta.

## Solapamiento heredado localizado

La ventana nueva conserva un conflicto detectado por el auditor nativo. Se compararon las coordenadas globales float32 completas de ambos triángulos, no sus índices: es exactamente el mismo par antes y después de la v2. No se añadieron conflictos allí.

Las dos caras son el **mismo triángulo geométrico con orientación opuesta**, área individual 0,210723 vóxel². No aparecen en `step1c_devcut` ni `step5_cc`; aparecen por primera vez en `step8_holefill`. El siguiente problema concreto está en el relleno de huecos, no en la recuperación de caras. El guard final de aristas/manifold no lo detecta, por lo que debe conservarse la auditoría 3D independiente.

Evidencia: `fresh-yplus32-v2/conflict-provenance.json` y `existing-overlap-trace.json`. No se arregló ese problema en esta extensión ni se ocultó como cero cruces.

## Verificación y reproducción

- `test_boundary_graft.c` incluye el helper real de producción: propietario alternativo, rechazo, cadena, conflicto con una cara ya recuperada, reintento, determinismo, entradas inválidas, conflictos iniciales y saturación real del detector.
- Compilación focalizada `cube_mesh` correcta. Advertencias observadas pertenecen a líneas ya existentes, no al helper nuevo.
- Auditor nativo `IntersectionCleanup_audit_visit`, `gap_max=0`, `include_hinges=1`, todas las piezas juntas. Sus cuatro controles positivos/negativos pasaron. Mide intersecciones, no separación mínima.
- Fuente previa a separación idéntica a los probes congelados en cada comparación. Guard final: cero correcciones de aristas no manifold, pinches o orientación en las corridas nuevas.
- Revisión independiente de código sin bloqueantes: rollback, memoria, cola y uso de asignaciones actuales. No equivale a otra validación geométrica.
- Scripts del directorio padre: `build_boundary_graft.py`, `run_boundary_graft_case.py`, `evaluate_boundary_graft_case.py`, `check_boundary_graft_compatibility.py`, `prepare_fresh_boundary_graft.py`, `run_fresh_boundary_graft.py`, `summarize_boundary_graft.py`, `trace_fresh_overlap.py`. No ejecutarlos sobre directorios ya existentes: preservan las corridas y rechazan sobrescrituras.
- `boundary-graft-v2.patch` es el diff incremental; `boundary-graft-results.json` contiene métricas completas; `boundary-graft-sha256.txt` fija código, parche, prueba y binario.

Todas las corridas fueron secuenciales con CPUQuota=25%, Nice=19, MemoryMax=384MiB, swap=0 y GPU inaccesible; reserva del escritorio de 3GiB. El mayor pico de cgroup observado fue 158,6MiB durante compilación. No hubo terminación por memoria ni se cerraron aplicaciones.

## Alcance antes de una entrega

Son mejoras pequeñas verificadas, no una solución completa de seguimiento de capas. La ventana central ya es desarrollo para v2; +32 X es regresión. La nueva +32 Y prueba transferencia sin retoques, pero comparte cubo y rollo con desarrollo. Falta resolver el triángulo duplicado del relleno y validar un contexto mayor con halo/seams, idealmente en otro cubo o rollo. No se evaluó lectura de tinta ni el pipeline completo de un rollo. Para preparar una entrega pública todavía hay que contrastar el parche con el upstream vigente y empaquetar instrucciones/datos/licencias y atribuciones reproducibles.

## Actualización posterior: relleno v4

Las cifras y el conflicto descritos arriba corresponden a la v2 histórica. La corrección posterior del relleno en +32 Y reduce el conflicto de 1 a 0 y conserva las 5139 caras fuente y las 27 caras recuperadas por graft. Su cobertura es 2239 frente a 2241 en v2 y deja abierto el ciclo cuya propuesta de 17 caras se rechazó. Véase [HOLEFILL_DUPLICATE_REPORT.md](HOLEFILL_DUPLICATE_REPORT.md) para método, regresiones, evidencia y límites.
