# Decisión siguiente: continuidad sin desarmar winding

**Decisión:** no existe en el camino revisado una alternativa de soldadura que elimine la necesidad de pitch y conserve todos sus filtros. El siguiente trabajo útil es calibrar el incremento radial de winding en el dominio de esta costura. Si esa calibración no queda sustentada, conservar la unión sin soldar y registrar el bloqueo. Esta conclusión procede de lectura estática y resultados ya guardados; no se ejecutó análisis, compilación, remallado ni prueba nueva para este documento.

## Lo ya resuelto y lo que la geometría no resuelve

`scrollfiesta-comparison/core-weld-preflight-02/native.json` registra10componentes,10discos,0superficies inválidas,0componentes con winding inconsistente,beta1=0 y exactamente el plano esperado X=4176. `weld_attempted=false`: ese resultado no es un ensayo de puentes. No hace falta repetir el preflight ni reparar charts ahora.

`next-zplus32-halo13-v1/continuity-diagnostic-v1/results.json` confirma CT/crop, umbral y ambos stdin completos, incluido su solape. Conserva111/133muestras y25/34a>4vóxeles. Sus3cadenas izquierdas y4derechas figuran como `candidate_geometric_support=uncertain`, `anatomical_correspondence=unverified`, `authorizes_weld=false`. No aportan una correspondencia certificada que permita sustituir winding.

Los indicios de los59puntos alejados tampoco identifican una causa única. Izquierda:20cerca del límite artificial ROI,20con indicio de desalineación/curvatura y13con soporte local de predicción; derecha:8,2y29respectivamente. Son categorías solapadas. Las25/34muestras alejadas no son recíprocas bajo la consulta de vértice de banda más cercano. Estas observaciones no convierten Otsu o proximidad en identidad de hoja.

Hay una limitación geométrica concreta independiente del pitch: la cadena izquierda1 tiene12muestras, distancia mínima al conjunto completo del otro core8.474266vóxeles y máxima11.940224. ChartZipper mantiene `max_cross_edge=2*BRIDGE_RHO_MAX=6`. Por tanto ninguno de **esos12vértices** puede ser extremo de una arista transversal de≤6hacia un vértice del otro core. No aumentar el radio para recuperarlos. Esto no demuestra que su componente completo carezca de otra frontera utilizable: el diagnóstico usa±4 respecto a los planos de propiedad y ChartZipper band6 respecto al plano central.

## Requisito exacto del camino existente

En `source/src/remesh/chart_zipper.c:204`, `cz_gate_armed` exige gate existente, `pitch>0` y eje muestreado de al menos2puntos o umbilicus constante no nulo. Si no está armado, `cz_gate_pair` devuelve aceptación sin evaluar winding. La CLI grid_weld lo impide por defecto; el adaptador exige calibración válida.

Para cada par de vértices candidato, `cz_winding_delta` usa el eje interpolado a la Z de cada extremo y calcula:

```
r_a = hypot(y_a-axis_y(z_a), x_a-axis_x(z_a))
r_b = hypot(y_b-axis_y(z_b), x_b-axis_x(z_b))
dtheta = wrap_to_minus_pi_pi(theta_b-theta_a)
dw = integral(r_a..r_b, dr/pitch(r)) - dtheta/(2*pi)
```

Sin tabla, la integral es `(r_b-r_a)/pitch_scalar`. Con las constantes actuales, `cz_gate_pair` acepta `abs(dw)<=0.40`: `hard=.40` tiene prioridad sobre `tol=.35`. No afirmar que se aplican simultáneamente dos umbrales, ni que el miembro `span` de BpaBridgeGate activa una comprobación acumulada en ChartZipper: esta función no lo consulta.

El gate participa en generación/compatibilidad de candidatos, apertura de ciertas cadenas cerradas, extremos, triangulación DP y recorte de intervalos. La búsqueda de correspondencias `ChartZipper_match` pasa por la misma generación y gate; no es un modo de correspondencia protegida sin pitch. Los filtros de cobertura, normales, arista máxima, ambigüedad, bosque de componentes, uso único de intervalos, geometría embebida y certificados posteriores siguen siendo obligatorios y no sustituyen winding.

**Mínimo matemático necesario:** el incremento radial de fase entre radios de los extremos evaluados, en el eje y unidades correctos. No es necesario reconstruir el pitch de todo el rollo ni conocer un offset absoluto de fase. **Mínimo de la API actual:** un scalar positivo sustentado para ese dominio o una tabla radial válida, manteniendo también un scalar positivo para el armado de la estructura. Una tabla no elimina el problema de calibración; expresa un modelo radial menos restrictivo.

## Por qué no usar los aparentes atajos

| Alternativa | Consecuencia | Decisión |
| --- | --- | --- |
| `--allow-unarmed`, gateNULL, `sf_weld` o scalar inventado | Se omite el filtro físico o se calcula con una calibración ficticia. | No usar. |
| SheetReweld con nube restringida y gateNULL | Sustituye el gate por una hipótesis de correspondencia; no conserva todos los filtros. La fixture no certifica esa hipótesis. | No usar para superar este bloqueo. |
| Match-only sin pitch | Acepta pares sin el criterio winding aunque no materialice caras. No produce correspondencias certificadas. | El diagnóstico guardado ya permite inspección; no llamarlo soldadura segura. |
| `ChartZipper_enumerate_transactions` y aceptar todas | Omite selección de bosque, pares repetidos e intervalos para construir alternativas de planificación. Requiere selección posterior. | No sustituir `ChartZipper_process`. |
| Mayor radio, banda, tolerancia o pitch elegido para conseguir puentes | Cambia la protección o ajusta el resultado a posteriori. | No usar. |
| Juntar vértices coincidentes o cambiar gap2→0 | La fuente fija tiene gap2; reextraer/mover/cambiar triangulación es otro experimento. | No resuelve la soldadura solicitada de las mallas guardadas. |
| Normales paralelas, CT brillante, mismo label o0intersecciones | Son evidencias parciales; ninguno evalúa el incremento de winding faltante. | Mantener como diagnóstico complementario. |

El caso matemático `r_a=r_b` anula el término de pitch para ese par, pero no existe en el código un camino que lo certifique para todos los pares de un strip sin armado, ni evidencia guardada que demuestre esa igualdad. No usar un scalar señuelo para aprovecharlo.

## Estado de calibración y decisión implementable

`native/paris4-winding-calibration-v1/calibration.json` conserva `axis_valid=true`, `pitch_identifiable=false`, `calibration_valid=false`, `winding_gate_ready=false`, pitch e intervalo superioresnull. La prueba congelada aceptó0/81perfiles. Hay picos candidatos numéricos dentro del informe, pero son diagnósticos rechazados. No extraer uno para rellenar el campo superior. El soporte radial objetivo tampoco quedó cubierto: intervalos documentados aproximadamente247.823..293.972vóxeles a través de las tres Z objetivo. El eje transformado no autoriza por sí solo un pitch.

1. **Continuar con evidencia asistida ya autorizada, sin modificar filtros.** Revisar el inventario CT+manualmask de45rayos previsto por el agente de calibración. Cada intervalo candidato debe documentar radios, muestra/ángulo/Z, CT original, IDs anotados, incertidumbre y si hay picos o soporte sin anotar intermedios. Un0de máscara es desconocido, no ausencia de hoja. Distancia entre centros de dos labels no equivale automáticamente a una vuelta radial ni acredita adyacencia.
2. **Decidir el modelo por esa evidencia antes de soldar.** Si demuestra vueltas adyacentes con spacing compatible en el dominio local, emitir scalar e intervalo de incertidumbre con método/provenance. Si demuestra variación radial resoluble, preparar una tabla sustentada. Si la variación depende de Z/ángulo y no es representable por el modelo radial usado, no promediarla para forzar la API. Registrar qué falta.
3. **Separar el resultado asistido del ensayo ciego.** La fixture Otsu previa no usó etiquetas. Una calibración posterior apoyada en manualmask es calibración asistida para esta investigación, no validación independiente sin etiquetas. Congelar los datos y criterio de aceptación antes de observar resultados del zipper.
4. **Usar el ejecutable preservado solo cuando el contrato superior sea válido.** El runner ya exige ambos booleanos `is True` antes de leer datos numéricos, hashes de evidencia, mismoCT/worldZYX y pitchpositivo dentro del intervalo. Con scalar válido, reutilizar `build/saved_core_weld.v1` sin recompilar y escribir directorio/unidad nuevos según CORE_CONTINUITY_DESIGN.md. Con tabla, completar primero el soporte explícito indicado abajo; no ejecutar el runner actual suponiendo que leerá un campo nuevo.
5. **Conservar la aceptación geométrica completa.** Fuente orientada/multiplicidad exacta,0duplicados/degenerados, auditorallfaces overlap/stab/fold0, discos/fans/winding, ecuación de componentes, bandas originales y conexión entre propietarios. Un candidato rechazado no justifica ajustar pitch. Si añade0puentes, es un resultado válido sin avance de continuidad. Ninguno de estos certificados demuestra identidad anatómica.

El mínimo de evidencia es local, pero debe cubrir **todos los extremos y radios que el zipper pueda consultar**, no solo244puntos del diagnóstico±4 ni los puentes que finalmente sobrevivan. En scalar, documentar validez en esa región. En tabla, cubrir todo intervalo radial integrado para evitar extrapolación no sustentada. Mantener explícita la incertidumbre del registro/eje: v1 declara `registration_error_voxels=null` y sentido winding no medido independientemente. Eso limita la interpretación física aunque la transformación y el cálculo numérico sean reproducibles.

## Requisitos si se decide usar PitchTable existente

`source/src/common/pitch_table.{h,c}` ya carga CSV `r,pitch[,count]`, interpola pitch linealmente e integra analíticamente `1/pitch`. Admite1..4096nudos, exige valores finitos, pitch≥.25 y radios distintos después de ordenar. La cifra.25 es un límite del parser, **no evidencia de pitch físico mínimo**. La columna count no se utiliza como confianza en los gates.

Hay dos comportamientos que obligan a un adaptador estricto:

- `PitchTable_from_env` lee `VES_WRAP_PITCH_TABLE` una sola vez. Si no puede cargarlo devuelveNULL y el cálculo **continúa con scalar**; un mensaje stderr no constituye rechazo. Debe cargarse y comprobarse nativamente antes del primer gate, exigir número de nudos esperado y abortar anteNULL/discordancia. No puede existir fallback no declarado.
- Fuera de los nudos extremos extiende pitch constante. El ensayo debe comprobar que los radios y cada intervalo integrado están dentro del dominio sustentado; de otro modo rechazar la transacción/ensayo, no aceptar esa extensión como medición.

Contrato mínimo adicional propuesto, todavía **no implementado**:

```
pitch_model.kind = "radial_table"
pitch_model.path / sha256 / knot_count
pitch_model.radius_units = "target_volume_voxels"
pitch_model.radius_definition = "hypot(worldY-axisY(worldZ),worldX-axisX(worldZ))"
pitch_model.supported_radius_interval_voxels
pitch_model.supported_z_interval_world
pitch_model.evidence = [{path, sha256, method, uncertainty}]
pitch_model.scalar_anchor = {radius, measured_table_pitch}
pitch_model.load_failure_policy = "reject"
pitch_model.out_of_domain_policy = "reject"
```

El scalar de armado debe derivar de un valor medido de la propia tabla en un radio soportado; no usar un número arbitrario. Una comprobación nativa debe garantizar que nunca se consume como fallback. Copiar/fijar CSV en el directorio nuevo, registrar hash y habilitar solo esa variable explícita en el entorno limpio. El runner vigente elimina esa variable y el C vigente solo recibe scalar+eje; por tanto estos son cambios posteriores acotados del adaptador/runner, sin modificar ChartZipper o sus tolerancias. No se implementaron en esta revisión.

Una tabla estimada a partir de separaciones entre labels sin probar vueltas adyacentes sigue sin estar calibrada. Dos caras del mismo estrato, capas internas de un papiro o labels no exhaustivos pueden dar periodicidades distintas; el criterio debe distinguirlos mediante la evidencia CT antes de autorizar el gate.

## Incertidumbre y cierre honesto

Para un scalar con intervalo físico validado `[p_lo,p_hi]` y eje fijo, el valor `dr/p-dtheta/(2*pi)` es monótono en p; evaluar el criterio absoluto en ambos extremos acota ese **par fijo**. Es una posibilidad de validación conservadora futura, no una función implementada ni una calibración nueva. No implica que ejecutar todo el zipper en dos extremos certifique todas las correspondencias intermedias: la selección de candidatos y del bosque también cambia. Incertidumbre del eje o una tabla radial requieren cotas adicionales. Nunca elegir el extremo que produzca más puentes.

Si el inventario no sustenta el incremento radial, la entrega correcta sigue siendo: fuente13346caras preservada,10discos,0conflictos y continuidad no soldada por calibración insuficiente. Mantener los artefactos de fracaso informativo y localizar la evidencia que falta es avance; afirmar que las59muestras alejadas quedaron resueltas no lo sería.

Fuentes consultadas: los JSON citados; `chart_zipper.c` funciones `cz_gate_armed`, `cz_winding_delta`, `cz_gate_pair`, `cz_match_compatible`, `cz_process_transactions`; `pitch_table.c`; `pipeline_constants.h` para BRIDGE_RHO_MAX=3 y windingtol/hard; y el preflight02 preservado. Solo se creó este documento; no se cambió código.
