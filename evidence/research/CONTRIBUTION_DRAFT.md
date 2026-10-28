# Borrador local de contribución — recuperación de superficie y relleno

**Estado: borrador para revisión; no enviado ni publicado.**

Este trabajo investiga pérdidas de superficie y un duplicado geométrico en la reconstrucción de un fragmento de papiro a partir de CT. La implementación parte de [ScrollFiesta público](https://github.com/Hob3rMallow/scrollfiesta_public), fijado en `bce8a65f97652316efb084171a17d2f1f8d3ae1a`, y añade cambios experimentales locales. ScrollFiesta y sus autores deben conservar su atribución y licencias. Las comparaciones siguientes son incrementales sobre esa base, con la misma entrada y MLS suave; no son una comparación entre motores independientes.

## Problema y cambios

Al separar componentes, pequeños fragmentos con caras fuente podían descartarse por el mínimo de tamaño incluso cuando su pérdida no estaba cubierta por la superficie retenida. La versión v1 ya protegía la cobertura en etapas anteriores. La extensión v2 recupera subconjuntos de esas caras por sus aristas originales hacia propietarios vecinos, comprobando incompatibilidades con las asignaciones actuales. Conserva los vértices y las caras fuente, y desactiva la recuperación nueva si el detector de conflictos se satura. El comportamiento desactivado produjo una malla idéntica al control congelado.

En una ventana adicional, la auditoría localizó un triángulo geométrico duplicado con orientación opuesta, introducido por el relleno de huecos. La reparación v4 rechaza la propuesta de relleno 3D que contiene ese duplicado exacto por coordenadas, incluso si usa IDs distintos, y conserva abierto el ciclo fuente. La extensión v5 encuentra otra triangulación completa del ciclo de 19 vértices mediante búsqueda acotada, sin mover fuente ni añadir Steiner. Su activación es experimental y explícita; requiere auditoría exacta posterior de cada resultado, además de los filtros nativos y certificados existentes.

## Resultados medidos

La cobertura cuenta vóxeles anotados únicos a radio 1 de muestras de caras. Puede incluir varios IDs y no certifica identidad anatómica. La distancia de borde mide la pérdida respecto de la superficie final, no la identidad de una hoja.

| Caso | Comparación | Resultado |
| --- | --- | --- |
| Original condicionado | v1 → v2 | 16 caras recuperadas; cobertura 2197 → 2207; auditoría de cruces 0 → 0. El objetivo conocido permanece a 2,649 vóxeles. |
| Central, desarrollo | v1 → v2 | 13 caras recuperadas; cobertura 2262 → 2265; pérdida máxima de borde 2,066 → 1,526 vóxeles; puntos a más de 1 vóxel 5 → 4; cruces 0 → 0. |
| +32 X, regresión | v1 → v2 | Malla idéntica byte a byte; cobertura 1829 y cero cruces en ambas. |
| +32 Y | v1 → v2 | 27 caras recuperadas; cobertura 2237 → 2241; pérdida máxima de borde 1,312 → 0,760; puntos a más de 1 vóxel 3 → 0. El mismo conflicto de relleno permaneció en ambas. |
| +32 Y | v2 → v4 | Caras finales 5160 → 5143; cobertura 2241 → 2239; conflicto 1 → 0; pérdida máxima de borde 0,759852 y cero puntos a más de 1 vóxel en v4. |
| +32 Y | v4 → v5 | Recupera las 17 caras del ciclo: 5160 finales, cobertura 2241, cero duplicados/degenerados y conflictos auditados. Conserva exactamente 5139 caras fuente y otras 4 válidas; cobertura continua bidireccional de superficies frente a v2 ≤0,25 vóxel. |

V5 pasó el pipeline completo con Status OK y guardias cero. La auditoría racional de 267 pares nuevos/fuente-v4 y nuevos/nuevos no encontró intersecciones fuera de esquinas/aristas comunes exactas; no recertifica los pares fuente/fuente inmutables. El certificado de cobertura continua usa 3303 hojas racionales, con fondo retenido idéntico; demuestra una cota de distancia, no igualdad de áreas ni identidad anatómica. Original, central y +32X con v5 activo son byteidénticos a v4/v2. El [informe completo v5](scrollfiesta-comparison/hole-recovery-v5/FULL_RECOVERY_REPORT.md) enlaza los artefactos y límites.

En +32 Y, un certificado independiente comprobó que las 5139 caras fuente se conservan con multiplicidad y orientación, junto con las 27 caras recuperadas por v2. La entrada previa al relleno es idéntica a v2. Las salidas finales central, +32 X y original son idénticas byte a byte entre v2 y v4. El auditor nativo de todas las caras, con `gap_max=0` y hinges, informó cero conflictos en +32 Y v4; mide intersecciones, no separación mínima. El certificado propio usa igualdad exacta de coordenadas float32 y no sustituye una auditoría general de cruces.

La ventana +32 Y se fijó antes de observar su resultado con v2 congelada, pero el conflicto encontrado allí se usó para desarrollar v4: es un caso de desarrollo de esa reparación. Central, +32 X, +32 Y y la nueva +32 Z comparten el mismo cubo CT y rollo; el original es otro cubo del mismo rollo. La entrada para las ventanas congeladas usa Otsu, sin etiquetas para seleccionarla; es una línea base clásica de intensidad, no un predictor entrenado.

## Halo y evidencia pendiente

La ventana +32 Z y su protocolo se fijaron antes de sus resultados. Se preparó con Otsu de umbral exclusivo 126, sin etiquetas. Las cuatro ejecuciones v2/v4 para los dos propietarios terminaron con `Status: OK` y guard cero. La auditoría posterior confirmó conservación de fuente y salidas idénticas v2/v4: unión de 13346 caras, sin duplicados exactos ni cruces auditados por core, antes del trim y en la unión final. Las distancias descriptivas de banda superan 4 vóxeles en 25/111 puntos izquierdos y 34/133 derechos; esta limitación permanece en ambas versiones. El [informe de halo](scrollfiesta-comparison/HALO_VALIDATION_REPORT.md) conserva métricas y límites completos.

El protocolo usa halo 13 y recorte de propiedad con planos separados por un gap esperado de dos vóxeles; no ejecuta soldadura. Las distancias previstas son descriptivas y no certifican continuidad anatómica. Falta evaluar otro cubo o rollo, evidencia visual de seguimiento de fibras e identidad de hoja, y un contexto más amplio. No se ha evaluado lectura de tinta ni el pipeline de un rollo completo.

La investigación posterior del mismo caso +32Z valida el preflight de diez discos y el eje del mismo papiro transformado al CT local, pero todavía no identifica un paso entre láminas defendible. Los cortes CT asistidos por etiquetas muestran bandas convergentes ambiguas; se conservan los indicadores de calibración inválida y no se desarma el gate winding. Doce vértices de una cadena también superan el límite geométrico transversal de 6 vóxeles. La continuidad entre cores sigue pendiente; v5 resuelve el hueco +32Y, no esa unión.

## Evidencia y reproducción

- [Informe de recuperación de bordes](scrollfiesta-comparison/BOUNDARY_GRAFT_REPORT.md): diseño, resultados v1/v2, controles y referencias a parches y hashes.
- [Informe del duplicado de relleno](scrollfiesta-comparison/HOLEFILL_DUPLICATE_REPORT.md): comparación v2/v4, certificado, prueba focalizada y figura de CT como contexto, sin afirmar seguimiento de fibras.
- [Alcance de validación](VALIDATION_SCOPE.md) y [protocolo de halo](NEXT_VALIDATION_PROTOCOL.md): selección de ventanas, límites y evaluación predeclarada. Los manifiestos `frozen-input.json` y los logs conservan entradas, hashes y comandos.
- [Resultados de v4](scrollfiesta-comparison/holefill-repair-v4/y32-comparison.json), [certificado independiente](scrollfiesta-comparison/holefill-repair-v4/independent-certificate.json) y [regresiones](scrollfiesta-comparison/holefill-repair-v4/regressions.json). El [wrapper](run_holefill_guarded.sh) permite nuevas ejecuciones con nombres y rutas de salida únicos, preservando los resultados existentes.

Antes de considerar una candidatura: investigar correspondencia y continuidad de hojas en la costura; ampliar validación y evidencia visual; contrastar los cambios con el upstream y preparar un paquete reproducible con datos, instrucciones, licencias y atribuciones. Este texto es una base para revisión, no una afirmación de aceptación ni de resultado garantizado.
