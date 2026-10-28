# Aceptación previa de la inspección local de ramas

**Estado y alcance:** criterios fijados antes de inspeccionar resultados de `diagnose_paris4_local_branches.py`. Se revisaron el contrato del runner y los informes `PARIS4_CONTEXT_REVIEW.md`, `PARIS4_RADIAL_ADJACENCY_REVIEW.md`, `PARIS4_ORTHOGONAL_REVIEW.md` y `PARIS4_CALIBRATION_METHOD.md`. No se ejecutó análisis ni se modificaron runner, adaptador o gates. El producto buscado es una decisión local sobre la regiónB, o una ambigüedad localizada; no una reconstrucción anatómica completa.

## Dominio y preguntas congelados

Caja del CT existente en índices sourceXYZ, con semántica de slice semiabierto: `X112:176, Y112:160, Z144:192`. Equivale a worldZYX `[1888,1936) × [2368,2416) × [4160,4224)` usando el origen `[1744,2256,4048]`. Registrar siempre coordenadas, unidades, orden de ejes y planos. No ampliar la caja ni buscar otras semillas después de ver una dificultad dentro de esta operación.

En el rayo preexistente de Zlocal160 hacia XY128,128, las ventanas radialesB1=277–288 yB2=294–312 son **ventanas de búsqueda ya documentadas**, no interfaces, centros ni intervalos de confianza. La cuestión es si sus prominencias pertenecen a:

- un mismo cuerpo de material visto oblicuamente o con estructura interna;
- dos ramas que pueden enlazarse mediante un pliegue local visible;
- dos bandas separables que se aproximan y eventualmente contactan;
- una asociación que este CT/caja no permite decidir.

Un máximo único en cada ventana y una normal local estable solo localizan candidatos. No deciden ninguna de esas relaciones por sí solos. El diagnóstico mínimo anunciado —semillas CT, tensor local de gradiente, cortes enlazados y perfiles normales— puede terminar correctamente con datos útiles y relación todavía desconocida. No se le exige fingir un tracker completo ni emitir pitch.

## Distinguir cresta, interfaz y referencia media

**Cresta CT:** máximo local de intensidad o una traza de máximos. Puede representar una cara, material interno, dos caras no resueltas o un efecto de sección. Su continuidad numérica no convierte la cresta en superficie media física.

**Interfaz óptica candidata:** transición de intensidad localizada en un perfil. El borde que devuelve un umbral o gradiente queda registrado como candidato; una segunda transición cercana no prueba automáticamente la otra cara del mismo papiro. Guardar intensidades crudas y regla de localización, y comprobar a qué cuerpo corresponden ambas transiciones en cortes vecinos.

**Referencia media local utilizable:** solo después de asociar las dos interfaces de un mismo cuerpo, definir explícitamente una convención, por ejemplo el punto medio del segmento que las une a lo largo de una normal local documentada. Guardar ambas posiciones, normal, punto derivado e incertidumbre de asociación/localización. No usar el punto medio de una ventana radial, de soporte de máscara, o de dos máximos de bandas distintas. El centro derivado sigue siendo una referencia geométrica experimental, no una identificación histológica.

Es posible medir entre **interfaces homólogas** en vez de centros si se identifica de manera consistente la misma cara de cada cuerpo y se declara esa convención y su incertidumbre. No mezclar en una tabla centros en un corte e interfaces en otro. El requisito es una referencia material comparable, no una preferencia obligatoria por un estimador de centros.

## Evidencia que permitiría cerrar cada hipótesis

Toda conclusión de relación debe referirse a las mismas posiciones3D, con capturas CT sin overlay y su correspondencia en cortes enlazados. En un evento de conexión/contacto, revisar el corte del evento y sus vecinos inmediatamente anterior/posterior; confirmar además en un plano que atraviese el mismo evento y en una sección aproximadamente normal. Si un vecino necesario queda fuera del dominio, registrar soporte incompleto. No sustituir persistencia por una sola vista favorable o por interpolación del tracker.

| Resultado local admisible | Observación positiva necesaria | Límite de la conclusión |
| --- | --- | --- |
| `one_body_oblique_or_internal_structure_supported` | Al mirar aproximadamente normal a la banda se pueden asociar las dos interfaces exteriores de un único cuerpo a través del vecindario. Las dos prominencias radiales se localizan dentro de ese cuerpo o en sus caras, y su aparición en la sección oblicua queda explicada por posiciones3D y perfiles guardados. | Se descarta contar esas dos prominencias como dos referencias medias distintas en ese vecindario. No basta que se fusionen al suavizar. |
| `local_fold_supported` | Las dos ramas pueden seguirse hasta un doblez **visible dentro de la caja**, con continuidad compatible de sus dos caras alrededor del doblez en cortes enlazados vecinos. La conexión no depende de atravesar un corredor oscuro ni de un puente creado por umbral/interpolación. | Identifica dos ramas de un cuerpo local. No asigna dos vueltas ni convierte su distancia en pitch. Una proximidad o tangencia sin doblez resuelto no pasa. |
| `two_separate_bands_supported_on_domain` | Ambas bandas tienen referencias/interfaces distinguibles y un corredor separador observado entre ellas sobre el dominio declarado, con asociaciones persistentes en las vistas enlazadas. Las incertidumbres de las interfaces no se solapan hasta hacer indeterminada la separación. | Respalda separación local al límite de resolución observado. Todavía requiere comprobar vecindad radial y convención material antes de medir paso. No demuestra independencia global de hojas. |
| `contact_or_connection_unresolved` | Se observan dos trazas separadas antes de aproximarse, pero en la zona de encuentro desaparece la separación resoluble o hay dos asociaciones compatibles de interfaces. | Localiza el punto/volumen donde no puede distinguirse contacto, doblez o mezcla por resolución. No decidir conexión topológica ni número de cuerpos en ese encuentro. |
| `ambiguous_association` | Semilla no única, cambios de rama igualmente plausibles, normal no determinada, interfaces no asociables o cortes normales discordantes. | Conservar alternativas/posiciones y causa. No elegir la que produzca una traza más suave o el pitch más conveniente. |
| `out_of_domain_before_decision` | Una rama/interfaz relevante sale de la caja antes de resolver su asociación. | El seguimiento se detiene allí. No inferir continuidad fuera ni ampliar automáticamente la caja. |

Los estados pueden aplicarse a subdominios distintos: una parte claramente separada no resuelve un contacto posterior. Delimitar dónde vale cada afirmación. Un fallo de asociación deB no borra la continuidad parcial deA ya observada.

La ausencia de banda intermedia se registra como **“ninguna otra interfaz material resuelta en el corredor inspeccionado a esta resolución”**, acompañada del CT y su incertidumbre. No se exige demostrar ausencia de todo material subvoxel, pero tampoco basta la ausencia de picos de un detector ni un0de máscara. Un corredor con señal intermedia no identificada queda desconocido.

## Reglas de evidencia y parada del diagnóstico

Para cada candidato conservar: ventana original; posiciónsourceXYZ/worldZYX; intensidad y alternativas competidoras; método/fiabilidad de normal; perfiles crudos y muestreados; transiciones candidatas; planos enlazados que pasan por ese punto; referencia a CT/mask/eje mediante rutas y hashes. La máscara es apoyo secundario; mismoID no prueba misma rama, IDs distintos no prueban vueltas adyacentes y0no prueba vacío.

No considerar centro/interfaz identificados cuando el resultado depende de suavizar a través de un hueco, del máximo de una banda ancha sin caras reconocibles o de asumir que un tensor orientado distingue las dos bandas. La normal del tensor puede reflejar una mezcla de estructuras próximas. Si hay más de una normal/semilla/asociación plausible, guardar la ambigüedad. No hace falta inventar un umbral adicional después del resultado: deben respetarse las reglas numéricas que el script haya fijado antes de correr.

Una operación que consigue `seed_and_profile_diagnostics_complete` puede conservar `branch_relation=unresolved`. Esa combinación es válida y útil. Terminar la ejecución no cambia `calibration_valid=false` ni `winding_gate_ready=false`. No se espera una transición automática atrue en este diagnóstico.

## Paso mínimo desde la observación hacia winding local

El requerimiento del gate es el incremento radial de fase entre los extremos de aristas consultables, usando el eje y la convención nativa `dr/pitch-dtheta/(2*pi)`. No se necesita conocer números absolutos de vuelta, reconstruir todo el rollo ni probar anatomía universal. Para que esta inspección fundamente una calibración asistida posterior basta resolver **en el dominio local requerido**:

1. Qué referencias materiales se están midiendo, manteniendo una convención homogénea de centro o interfaz; qué incertidumbre tiene su posición y asociación.
2. Qué pares son vecinos radiales locales con corredor inspeccionado, sin contar dos caras de un espesor ni dos intersecciones de un pliegue como pasos de vuelta por defecto. Una separación física local no se convierte en un incremento de1vuelta sin justificar esa correspondencia con el modelo de láminas usado.
3. Cómo esas referencias y vecindades se prolongan por las Z/ángulos que aportan soporte al dominio del zipper; los radios de una misma traza en muchos cortes son observaciones correlacionadas, no réplicas independientes.
4. Que el scalar o la tabla radial representan esos incrementos con su incertidumbre en el dominio declarado. No se requiere calibración en regiones del rollo que el ensayo no consulta. Una calibración limitada a una rama/zona no autoriza el ensayo sobre todos los pares del core: haría falta restringir explícitamente el dominio de consulta en un trabajo posterior conservando filtros, o conseguir el soporte faltante.

El modelo y las asociaciones deben congelarse antes de mirar una soldadura. La etiqueta “asistida” permanece: esta operación consulta el mismo CT y la máscara de desarrollo. Si no se identifican las referencias materiales, conservar distancias de crestas/interfaces candidatas como diagnóstico, no renombrarlas pitch. La nueva revisión no cambia retroactivamente el protocolo estadístico v1; v1 falló bajo sus propios criterios y esta es una vía de evidencia distinta, declarada.

## Cuándo rechazar una tabla solo radial

`PitchTable` modela una función única `p(r)` e integra `1/p(r)`; no dispone de argumentosZ/ángulo ni identidad de rama. La evidencia actual muestra que las prominencias deBse aproximan entreZ160–176 y que la cortina haciaXY128,128 cambia también de ángulo. **Eso no demuestra todavía que ninguna p(r) pueda funcionar.** Antes de resolver ramas, atribuir la aproximación a variación de pitch sería convertir la ambigüedad en medición. Lo correcto ahora es “soporte insuficiente para emitir tabla”, no “modelo radial refutado”.

Una vez fijadas referencias y asociaciones, se rechaza el modelo radial para el dominio completo si observaciones respaldadas que recorren el **mismo soporte radial** en diferentesZ/ángulos exigen incrementos incompatibles con una sola función positiva dentro de sus incertidumbres y del criterio fijo del gate. También queda fuera de soporte si una asociación necesaria es multivaluada/no resuelta por pliegue o contacto, de modo que el radio no permite asignar el incremento material local. Una traslación común de bandas o variación aparente causada por corte oblicuo no basta para ese rechazo.

La comprobación debe conservar las observaciones discrepantes y sus incertidumbres; no promediarZ/ángulos, mezclar ramas, descartar el tramo de contacto ni aumentar tolerancias para conseguir una tabla. Si solo un subdominio admite el modelo, declararlo así. No extrapolarlo al resto de la caja ni a todas las aristas de la costura. Esta operación no propone números nuevos para cuantificar una incompatibilidad aún no medida.

## Lo que una traza CT no certifica

Ni el tracker más suave ni su normal/perfil demuestran por sí solos: identidad global de hoja, vuelta absoluta, sentido helicoidal, fibra continua, lectura de tinta, contacto versus fusión bajo la resolución, ausencia de una lámina subresuelta, o precisión física del eje transferido. Tampoco prueban ausencia de cruces en una futura malla. Esas limitaciones deben acompañar el resultado sin impedir una conclusión local cuando las interfaces y su relación sí estén visibles.

Si las evidencias anteriores resuelven localmenteB, el resultado puede ser **“relación local respaldada; lista para medir referencias y validar el modelo”**. Eso es un avance suficiente; no exige ampliar indefinidamente la investigación. Si no la resuelven, entregar las posiciones exactas del desacuerdo, las alternativas compatibles y la observación adicional mínima que faltaría —por ejemplo separación de interfaces en el punto de contacto o continuación de una rama fuera de la caja—. No solicitar por defecto otro volumen entero ni una anotación global.

El runner continuará exigiendo los dos booleanos explícitos de validez y la procedencia del CT. Solo un artefacto posterior de calibración, con criterio de aceptación propio satisfecho, podrá establecerlostrue; no este inventario de ramas. No se modificó código ni se ejecutó análisis al fijar estos criterios.
