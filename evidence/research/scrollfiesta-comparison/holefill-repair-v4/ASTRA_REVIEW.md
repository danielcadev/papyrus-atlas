# Revisión estática de holefill v4

Fecha: 2026-10-27. Revisión independiente mediante lectura estática del código, parche, certificados, scripts de comprobación y logs existentes. No se ejecutaron compilaciones, pruebas, análisis geométricos ni verificaciones nuevas de hashes; no se modificó la implementación. Se leyeron AGENTS.md, CONTEXT.md, MIGRATION.json y BOUNDARY_GRAFT_REPORT.md.

## Veredicto y alcance

V4 es aceptable para corregir el duplicado concreto observado en +32Y. No se encontraron defectos bloqueantes en el cambio. Este juicio cubre el rechazo atómico de una propuesta del fallback 3D que contiene triángulos geométricamente coincidentes, y su interacción con los certificados y el llamador existentes. No certifica universalmente el algoritmo de relleno ni la identidad anatómica de las superficies.

Referencias de líneas corresponden al código revisado `source/src/holefill/hole_fill.c`, identificado en `sha256.txt`; no se recalcularon sus hashes durante esta revisión.

## Corrección, rollback y coste

- Líneas 2483–2505: `hf_same_triangle` compara correctamente el multiconjunto de tres posiciones exactas, independientemente de IDs y orientación. La máscara `used` impide reutilizar un vértice y conserva multiplicidades. La igualdad exacta evita confundir hojas cercanas con coincidentes.
- Líneas 2651–2654: el rechazo ocurre antes de escribir `result`, restaura la marca local y no modifica fuente ni rellenos aceptados antes. El llamador inicializa `res`, restaura el intento CDT fallido y solo añade propuestas con `rc == 0` (líneas 3800–3829). No se encontró uso de memoria restaurada en esta ruta.
- Se mantienen la triangulación original, la frontera exacta, la comprobación de diagonales existentes, la orientación y la factibilidad de los abanicos angulares. V4 no cambia las elecciones de ears para esquivar un duplicado.
- La búsqueda previa de posiciones repetidas es O(n²); cuando las hay, la comparación de pares de triángulos también es O(n²). La memoria auxiliar nueva es constante y no se añaden asignaciones. El ear clipping existente ya es cuadrático. Para el ciclo de 19 vértices el trabajo es pequeño; esta revisión no aporta una medición para ciclos grandes.

## Evidencia existente examinada

`y32-comparison.json` e `independent-certificate.json` registran 5.139 caras fuente conservadas con multiplicidad y orientación, las 27 caras recuperadas intactas, cuatro caras de otro relleno conservadas y duplicados exactos 1→0. Se retiran las 17 caras del parche inválido, equivalentes a 16 geometrías únicas. Cobertura 2241→2239; máximo de borde 0,759852 y cero puntos de borde a más de un vóxel. La auditoría nativa registra cero overlap, stab y fold, y el guard cero cambios.

`regressions.json` registra salidas byteidénticas a v2 para central, +32X y original. Reutilizar sus métricas y auditorías previas resulta adecuado. El historial `holefill-repair/central-audit.json` registra nueve stab para v3; eso justifica no adoptar el cambio de selección de ears de aquella versión.

La prueba pequeña `research/test_holefill_duplicate.c`, líneas 14 y 29, llama al fallback con métrica nula y espera aceptar ambos ciclos. Comprueba la conservación de propuestas válidas y el helper de coincidencia, pero **no cubre por sí sola el rechazo con la métrica productiva**. El replay guardado sí lo cubre: `research/native/hf-small-v4-02.log`, líneas 27–37, muestra el ciclo de 19 vértices y el rechazo explícito por duplicado. Debe conservarse ese replay como parte de la evidencia de regresión.

## Por qué no basta conservar un subconjunto

Un subconjunto propio no vacío de las 17 caras producidas por ear clipping no puede mantener exactamente el mismo borde indexado del disco completo. El dual de esa triangulación es conectado: separar caras aceptadas y rechazadas expone alguna diagonal interna. Retirar caras del perímetro puede además eliminar aristas originales. Ambos efectos contradicen `fill_boundary_is_exact` (líneas 1574–1616); la condición `ntri == n_loop-2` de la línea 2642 también exige el parche completo.

Eliminar una o ambas caras duplicadas, o conservar solo las otras 15, por tanto no es una reparación admisible bajo el contrato actual. Dividir por posiciones coincidentes cambiaría el ciclo indexado que chart mode preserva. Esto no demuestra que sea imposible otra triangulación completa válida: únicamente descarta el filtrado de caras del parche actual sin cambiar sus certificados.

## Límites y siguiente paso

El nuevo guard compara únicamente caras de una misma propuesta del fallback 3D. No compara contra caras fuente, entre distintos rellenos ni las propuestas de CDT, y no detecta intersecciones generales. Es una limitación de alcance, no un bloqueo del arreglo localizado.

La evidencia procede del mismo cubo y rollo, sin validación de halo/seams. Las coordenadas guardadas son float32 globales y la cobertura no certifica identidad anatómica ni lectura de tinta.

Se recomienda conservar v4 como base y validar después un contexto independiente o halo/seams. Recuperar el hueco de 19 vértices debe ser un experimento separado sobre malla guardada: otra triangulación completa, todos los certificados actuales intactos y auditoría de intersecciones tanto internas como contra la fuente. No hay evidencia aquí de que exista esa alternativa. Reseleccionar ears sin dicha auditoría repetiría el riesgo mostrado por v3.
