# Propuesta opt-in de recuperación del ciclo completo

Actualización del principal: propuesta aplicada y compilada como `cube_mesh.holefill-v5`; replay, pipeline completo +32Y y tres regresiones pasaron. La auditoría exacta offline sigue siendo obligatoria. Resultado vigente en `scrollfiesta-comparison/hole-recovery-v5/FULL_RECOVERY_REPORT.md`; las secciones siguientes conservan el estado de entrega estática del agente antes de la aplicación.

Estado: propuesta escrita e inspeccionada estáticamente. No aplicada a producción, compilada ni ejecutada por este agente. El candidato guardado previo sí fue validado por el principal: 17 caras en 1206 nodos, combinación de 5139 caras fuente + 4 rellenos v4 + 17 nuevas = 5160 caras, auditoría nativa y exacta sin conflictos, cobertura 2241 restaurada. Eso no valida todavía esta generalización.

## Archivos y aplicación por el principal tras revisión

- `hole_recovery_production_proposal.patch`: tres modificaciones pequeñas en `source/src/holefill/hole_fill.c`; rutas relativas a `research/scrollfiesta-comparison/source`.
- `hole_recovery_search.inc`: nuevo helper privado, a copiar **sin cambios** desde `research/` a `research/scrollfiesta-comparison/source/src/holefill/` junto con la aplicación del parche. Se entrega separado para no duplicar 230 líneas en dos archivos de investigación. El parche requiere ese archivo acompañante; por sí solo no compila.

Se conserva la firma de `fill_chart_cycle_3d` y la API pública. El código interno -3 aparece exclusivamente cuando la propuesta greedy completa contiene duplicado geométrico y `VES_HOLE_RECOVERY_SEARCH` vale exactamente `1`. Con el flag ausente o distinto de `1`, se conserva el rechazo -2 de v4. Solo el caller del fallback 3D reconoce -3 y llama al nuevo helper con fuente completa, índice, métrica y rellenos ya aceptados.

## Cotas y transacción

Dominio 3≤n≤19, sin IDs/coordenadas/cantidad de caras de fixture. La cota 19 conserva el dominio del experimento ya verificado y limita a 969 triples posibles y menos de 470000 pares internos. Se permite aumentar esta cota únicamente como trabajo posterior con memoria y coste reevaluados.

La búsqueda tiene tope de 2000000 nodos y el preprocesamiento tope adicional de 20000000 llamadas a predicados de pares; el último evita trabajo proporcional ilimitado a una fuente grande aun con n pequeño. Alcanzar cualquier cota devuelve rechazo atómico, sin un candidato parcial. El estado de heap es aproximadamente 1 MiB, comprobado frente a un techo de 128 MiB; ninguna reserva depende de la cantidad de caras fuente. La pila recursiva tiene profundidad máxima 17. Los arrays de salida solo se reservan después del éxito; el scratch se libera antes. El caller conserva su arena transaccional existente.

No se mueve ni cambia una cara/vértice fuente, ni se fusiona un índice. El relleno contiene n-2 caras y usa exactamente los IDs y coordenadas fuente del ciclo. Se exige métrica real no nula, grado de frontera 2, IDs únicos, orientación coherente en **todas** las aristas del ciclo y cotas finitas. Se conservan el suelo de forma relativo del fallback, prohibición de diagonales fuente, certificado de frontera exacta, certificado angular completo y `orient_fill`.

## Intersecciones y alcance exacto

Cada triple posible se comprueba contra **todas las caras fuente** usando el predicado nativo (gap=0, hinges=1) y la comparación exacta de triángulos duplicados. También se comprueba contra todas las caras de todos los rellenos ya aceptados. Para estos últimos se transportan solo dos triángulos a un buffer de seis vértices; el detector nativo reconoce posiciones compartidas. Las aristas compartidas por ID con un relleno anterior se rechazan por topología. Si algún relleno anterior contiene merges, se rechaza la búsqueda completa porque el contexto todavía no representa el estado tras merges. Los pares del candidato se precalculan y se consultan en cada elección. Es una auditoría exhaustiva de todos los pares que involucran caras candidatas, sin reauditar pares fuente-fuente inmutables ni copiar toda la fuente.

El detector nativo conserva sus blindspots de contacto compartido. El log dice explícitamente `strict_geometry=offline_required`: pasar estos certificados no es una prueba general de inmersión/inyección ni de identidad anatómica. La validación exacta independiente de la malla completa sigue siendo un gate obligatorio del experimento, incluidos rellenos que el pipeline acepte **después** de esta propuesta. La recuperación no cambia los otros caminos del rellenador para hacerlos auditar cada par en tiempo de ejecución.

## Revisión y comprobaciones siguientes

Revisión estática independiente antes de aplicar; luego compilación focalizada bajo el wrapper secuencial vigente. Reutilizar el replay completo guardado con el flag y comprobar 5139 caras fuente + 4 válidas + 17 recuperadas, certificación exacta de fuente, frontera y auditoría estricta. El helper no contiene constantes del caso real fuera de la cota de complejidad n≤19.

Validar flag ausente y `0` contra v4 congelado, luego full pipeline +32Y y regresiones central, +32X y original con el flag activo. Conservar fuentes y orientaciones, guards cero y auditorías nativa/exacta del resultado completo; medir cobertura y superficie, sin inferir identidad anatómica del área añadida. Los resultados previos de malla guardada no sustituyen estas ejecuciones. Si el caller recibe presupuesto agotado, no candidato o error, debe conservar el ciclo abierto exactamente como v4.
