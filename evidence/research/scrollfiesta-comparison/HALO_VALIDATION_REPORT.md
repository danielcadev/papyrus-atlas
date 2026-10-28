# Validación adicional +32Z con halo13

Comparación congelada v2/v4 en una ventana nueva del mismo cubo CT y rollo. No es un holdout por cubo o rollo. Predicción Otsu exclusiva >126, sin etiquetas para selección; cuatro ejecuciones secuenciales con origen y solape global comprobados. No se ajustaron parámetros tras ver los resultados.

| Caso | Caras fuente conservadas | Caras finales | Área (vóxel²) | Duplicados exactos | Overlap/stab/fold finales |
| --- | ---: | ---: | ---: | ---: | --- |
| v2-left | 6326 | 6332 | 1074.538108 | 0 | 0/0/0 |
| v2-right | 7011 | 7014 | 1212.101456 | 0 | 0/0/0 |
| v4-left | 6326 | 6332 | 1074.538108 | 0 | 0/0/0 |
| v4-right | 7011 | 7014 | 1212.101456 | 0 | 0/0/0 |

La fuente step7 y las salidas step8/step11/step12 son idénticas byte a byte entre v2 y v4 en ambos propietarios. Los certificados conservan multiplicidad y orientación de toda la fuente antes del trim. Todos los contadores de guard fueron cero. Las auditorías pretrim se registran por core; los halos pretrim no se unen porque se solapan intencionalmente.

Unión final v2: 7125 vértices, 13346 caras, área 2286.639564, duplicados 0, auditoría overlap/stab/fold 0/0/0. Es concatenación globalZYX, sin soldadura ni segunda traslación.

Unión final v4: 7125 vértices, 13346 caras, área 2286.639564, duplicados 0, auditoría overlap/stab/fold 0/0/0. Es concatenación globalZYX, sin soldadura ni segunda traslación.

## Bordes y alcance

Los planos de propiedad fijados son X=4175 y X=4177, con gap intencional de 2 vóxeles. Se usaron todos los vértices incidentes a aristas de frontera dentro de ±4 vóxeles de su plano. La distancia se mide a todos los triángulos del otro propietario. La fracción sin correspondencia aquí significa distancia estrictamente mayor que 4 vóxeles, no un fallo anatómico certificado.

left_to_right: 111 vértices; distancia al plano media 0.759915, máxima 3.606934; al otro core mediana 2.548283, p95 9.819084, máxima 11.940224; >4 vóxeles 25/111 (22.52%).

right_to_left: 133 vértices; distancia al plano media 0.997702, máxima 3.637207; al otro core mediana 2.791086, p95 5.628050, máxima 6.710584; >4 vóxeles 34/133 (25.56%).

Las métricas de v4 reutilizan v2 porque ambas mallas finales tienen hashes idénticos. Se evitó repetir auditorías y cálculos de geometría idéntica mediante caché SHA256.

El trim final informó cero caras cortadas en los cuatro casos: la extracción ya realiza un recorte de puntos antes de BPA. Esta prueba ejercita entrada con halo y propiedad, pero no demuestra activación del corte final de triángulos ni continuidad soldada. Hay contexto remoto incompleto de tres slices y predicción artificial cero fuera de 32³. No se evaluaron lectura de tinta ni seguimiento de fibras.

## Evidencia y recursos

Preparador: `research/prepare_next_validation.py`. Protocolo previo: `research/NEXT_VALIDATION_PROTOCOL.md` y manifiesto congelado `next-zplus32-halo13-v1/frozen-input.json`. Runner por caso con stdin explícito, hashes y marcadores exclusivos. Logs: `research/native/next-z32-h13-*`. Todos los jobs se ejecutaron secuencialmente con CPUQuota25%, Nice19, IOWeight10, MemoryMax384MiB, swap0, GPU inaccesible, cinco límites de un hilo y reserva de escritorio3072MiB.

Evaluación completa: `next-zplus32-halo13-v1/evaluation-v2/results.json`; resumen: `summary.json`; auditorías y pares por hash en el mismo directorio. La evaluación-v1 falló al contar los espejos all_obj como mallas extra, antes de analizar geometría; sus resultados y fuente se conservaron. Se corrigió únicamente la selección del directorio canónico y se ejecutó evaluation-v2 sin repetir meshing.

Base atribuida: ScrollFiesta público bce8a65f97652316efb084171a17d2f1f8d3ae1a. Estas mediciones amplían la comparación incremental, no prueban superioridad general ni un motor propio completo. No se publicó ni envió candidatura.
