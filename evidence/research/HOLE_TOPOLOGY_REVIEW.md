# Revisión matemática del ciclo de 19 vértices

Revisión independiente por lectura estática, 2026-10-27. Se leyeron AGENTS.md,
CONTEXT.md, BOUNDARY_GRAFT_REPORT.md, HOLEFILL_DUPLICATE_REPORT.md,
holefill-repair-v4/ASTRA_REVIEW.md, los dos OBJ del ciclo real, los helpers de
relleno y el auditor de intersecciones. No se ejecutaron búsquedas, compilaciones,
pruebas ni análisis numéricos en esta revisión. El principal debe ejecutar y
registrar los controles nuevos mediante la cola y el guard del proyecto.

## Conclusión

La coincidencia de dos posiciones de frontera **no demuestra que no exista otra
triangulación admisible bajo los certificados actuales**. Sí impide una
parametrización global estrictamente inyectiva del disco cerrado que conserve
esas dos posiciones y sus IDs distintos. El contrato operativo existente admite
el contacto puntual heredado; por tanto, esa imposibilidad más fuerte no es una
razón válida para abandonar la búsqueda del relleno.

Una alternativa debe ser un parche completo nuevo. Pasar de 17 caras inválidas
a 17 caras distintas no basta: deben conservarse fuente, frontera indexada,
abanicos angulares, orientación, winding y ausencia de intersecciones fuera de
los contactos comunes permitidos. No se prueba aquí la existencia de tal parche
para estas coordenadas reales.

## Datos y distinción topológica

Los archivos examinados son
`scrollfiesta-comparison/holefill-repair/replay-v2-holes/weld_hole0003_loop5_19v_in.obj`
y `weld_hole0003_loop5_filled.obj`. Las posiciones OBJ 8 y 11 coinciden:
`(61.511719, 96.965088, 52.153076)` en la impresión decimal del OBJ. La evidencia
previa conserva sus coordenadas binary32 completas. Para predicados exactos debe
usarse VMESH, no reconstruir float32 desde los seis decimales de este OBJ.

El arco 8→9→10→11 regresa geométricamente al mismo punto con dos IDs distintos.
El relleno guardado contiene las caras `(7,9,8)` y `(7,11,9)`: son el mismo
triángulo geométrico con orientaciones opuestas. El área individual previamente
medida es 0,210722909 vóxel². Los `f` del archivo PRE-fill son una visualización
en abanico del contorno, no caras fuente ni una propuesta admisible certificada.

Hay tres objetos diferentes:

1. Un ciclo indexado simple de 19 vértices, todos con identidad distinta.
2. Su imagen geométrica, que visita una posición dos veces.
3. La imagen de los interiores de las caras del parche, que puede tener o no
   duplicados/cruces independientemente de que el ciclo sea indexado simple.

Un embedding del disco cerrado es imposible porque su restricción a la frontera
sería inyectiva y aquí dos puntos distintos deben tener la misma imagen. Ni
Steiner interiores ni otra conectividad eliminan esa contradicción. Sin embargo,
es posible en general que dos vértices de frontera se toquen y todos los
interiores de las caras permanezcan disjuntos.

Contraejemplo concreto a la supuesta imposibilidad general: tomar una pirámide
con ápice `p=(0,0,1)` y base cuadrada
`a=(1,1,0), b=(-1,1,0), c=(-1,-1,0), d=(1,-1,0)`. Para el ciclo indexado
`[p₀,a,b,p₁,c,d]`, con `p₀=p₁=p` geométricamente, las caras
`(p₀,a,d), (a,b,c), (a,c,d), (b,p₁,c)` forman un disco combinatorio sin
degeneración ni intersección de interiores. Las dos caras laterales opuestas
solo se tocan en el ápice. Esto no demuestra factibilidad para el ciclo real;
demuestra por qué su posición repetida, por sí sola, no prueba imposibilidad.

## Qué sí se puede descartar

**Filtrar caras del parche guardado.** El dual de una triangulación de disco
obtenida por ears es conectado. Cualquier subconjunto propio no vacío expone una
diagonal entre una cara retenida y otra retirada. Esa arista interna se vuelve
frontera y contradice la frontera indexada exacta. El subconjunto vacío también
es rechazado. Retirar una o ambas copias del duplicado, o conservar las otras 15
caras sin reemplazo, no es una reparación del mismo ciclo.

**Soldar 8 con 11, moverlos o dividir el ciclo en lóbulos.** Cambia las estrellas
fuente o la correspondencia de la frontera indexada. No es una solución dentro
del contrato solicitado. Puede estudiarse por separado solo con un contrato y
una autorización diferentes; no debe esconderse dentro de un fallback.

**Cambiar el orden greedy y aceptar al desaparecer el duplicado.** La falta de
duplicados exactos no excluye stab, fold ni cruces contra fuente. La v3 histórica
produjo nueve stab en central. El control de ángulos también es una condición
necesaria de factibilidad de un mapa, no una prueba de mapa inyectivo ni de
ausencia de intersección 3D.

## Búsqueda finita y alcance de un resultado negativo

Con los 19 vértices de frontera y sin Steiner, todo disco triangulado de esta
familia tiene `F=n−2=17` caras. Sus triangulaciones combinatorias posibles son
`Catalan(17)=129644790`, antes de aplicar restricciones. Un greedy examina una
sola elección; varios órdenes de ears no constituyen una búsqueda completa y
pueden repetir la misma triangulación muchas veces.

Una búsqueda acotada útil precomputa las hasta `C(19,3)=969` caras candidatas y
descarta degeneración, diagonales fuente prohibidas y conflictos seguros contra
fuente. Después enumera triangulaciones del ciclo con poda por incompatibilidad
entre caras y por los mismos límites angulares de producción. La enumeración
por intervalos distingue triangulaciones sin multiplicarlas por sus órdenes de
clipping. Una tabla booleana por intervalo es insuficiente si omite los estados
de ángulos acumulados o los conflictos globales entre caras.

Cada poda empleada para concluir imposibilidad debe ser una condición necesaria
del contrato declarado. Una tolerancia conservadora o un rechazo adicional de
contactos puede ser útil para encontrar candidatos seguros, pero su agotamiento
solo prueba ausencia dentro de esa familia más restringida. Registrar límites
de nodos/tiempo, motivo de terminación, candidatos completos auditados y familias
no exploradas. `Sin candidato antes del límite` no significa `imposible`.

Con `s` Steiner interiores, un disco con la misma frontera tiene
`F=n+2s−2=17+2s`; no corresponde exigirle 17 caras. `HoleFillResult`, el stitching
y la evaluación final de abanicos ya representan Steiner, aunque el fallback de
ears actual no los genera. Un resultado exhaustivo negativo sin Steiner no
descarta esta familia continua. Tampoco certifica búsquedas que introduzcan
otros vértices fuente ajenos a los 19 del contorno: eso cambia la familia y
requiere explicitar cómo se conectan sus estrellas originales.

`fill_boundary_is_exact` por sí solo no demuestra que un complejo arbitrario sea
un disco: una componente cerrada adicional no aporta aristas de frontera y
podría escapar de esa comprobación. La construcción por ears aporta la
estructura de disco. Si se generaliza a Steiner u otra construcción, deben
verificarse también conectividad, orientación coherente y links de vértices de
disco/semidisco, además de la característica de Euler; no basta contar aristas.

## Intersecciones: blind spot real y comprobación exacta

`IntersectionCleanup_pair_test` cuenta como compartidos los IDs iguales o
posiciones a distancia ≤1e-5 (`shared_vertices`, umbral cuadrado 1e-10). Después
descarta cualquier resultado STAB con `shared>0`. Así, un par puede compartir un
vértice y cruzarse además fuera de ese vértice sin quedar reflejado en el
resultado del wrapper. `include_hinges=1` no evita esta supresión. El helper
inferior `tri_pair_test` es estático, pero invocarlo directamente tampoco aporta
un certificado racional independiente.

Se añadió `exact_patch_intersections.py`, independiente del núcleo nativo y
basado solo en biblioteca estándar. Lee VMESH estrictamente, conserva coordenadas
binary32 exactas como fracciones y extrae las caras añadidas por resta de
multiconjuntos orientados. Rechaza fuente ausente/invertida y nuevas caras
degeneradas. Comprueba todos los pares añadido/fuente y añadido/añadido con AABB
superpuesta; el AABB usa comparaciones exactas de los valores almacenados y solo
elimina pares que no pueden tocarse.

El procedimiento geométrico es:

1. Calcular normales y distancias orientadas a ambos planos con aritmética
   racional. Un lado estrictamente separado certifica intersección vacía.
2. Si los planos no son coplanares, cortar cada triángulo por el plano del otro
   usando vértices sobre el plano e interpolaciones exactas de aristas que lo
   cruzan. Ambos cortes son puntos/segmentos sobre la misma recta. Solapar sus
   intervalos sobre una componente no nula del producto de las normales.
3. Si son coplanares, eliminar un eje con componente normal no nula y recortar
   convexamente un triángulo por las tres semirrectas interiores del otro,
   mediante Sutherland–Hodgman con fracciones. Se retienen también intersecciones
   de dimensión cero o uno; no se aproxima área con un epsilon.
4. La intersección es convexa. Basta comprobar todos sus vértices contra el
   simplex de esquinas geométricas exactamente compartidas: ninguna esquina
   exige vacío, una exige solo ese punto y dos permiten solo su segmento. Tres
   esquinas compartidas en triángulos no degenerados son un duplicado y fallan.

Esto detecta el stab que el wrapper omite, incluso cuando una cara contiene un
vértice compartido. Los controles incluyen ese caso en todas las permutaciones
de sus esquinas y ambos órdenes, duplicados de ambos windings, contactos puntuales
y por arista válidos, overlap coplanar, cruces sin esquinas comunes, separación,
degeneración y coordenadas subnormales binary32.

El criterio es deliberadamente conservador respecto de contactos sin ninguna
esquina común: aun un simple toque arista/arista no indexado falla. El certificado
no audita pares fuente/fuente, ni sustituye frontera, manifold, orientación,
ángulos, winding, cobertura o identidad de hoja. Permite el simplex geométrico
compartido, sin afirmar que ese contacto sea una soldadura topológica. Si la
fuente contiene una cara degenerada, falla explícitamente porque el predicado
implementado requiere planos no degenerados; no la omite como si fuera segura.

## Criterio operativo de aceptación y de fallo

Conservar v4 como base y aceptar una alternativa solo si:

- retiene exactamente las 5139 caras fuente con multiplicidad y orientación y
  la recuperación de 27 caras de graft;
- conserva las 19 aristas indexadas del ciclo como única frontera del parche y
  no introduce ninguna otra, sin merges ni movimientos fuente, y el parche es
  un disco conexo orientable con links correctos;
- pasa los mismos abanicos de producción y la orientación de cada arista fuente,
  el certificado de winding cuando esté armado y los guards existentes;
- no tiene duplicados ni degenerados nuevos, y pasa tanto el auditor nativo como
  el certificado exacto añadido/fuente e intraparche;
- demuestra la recuperación reclamada mediante las mismas métricas guardadas,
  incluida cobertura: igualdad de número de caras o un área mayor no implica
  conservar los dos vóxeles de cobertura perdidos en v4;
- reproduce el proceso completo afectado y las regresiones necesarias con el
  mismo contrato y bajo la cola/guard, sin sobrescribir controles.

Fallo de un certificado significa rechazar la propuesta completa y conservar la
fuente; no permite declarar recuperado el hueco. Agotamiento acotado significa
búsqueda inconclusa. Imposibilidad sin Steiner exige enumeración completa o una
obstrucción demostrada para todas sus triangulaciones. Imposibilidad aun con
Steiner exige una prueba adicional; la posición repetida solo prueba la
imposibilidad del embedding estricto del disco cerrado, que es una propiedad
distinta del contrato operativo existente.

Comandos nuevos, pendientes de ejecución por el principal:

```text
python3 -m unittest discover -s research -p test_exact_patch_intersections.py -v
python3 research/exact_patch_intersections.py --source SOURCE.vmesh --candidate CANDIDATE.vmesh --output NUEVO.json
```

Ambos deben envolverse en `research/run_holefill_guarded.sh` con nombres únicos.
Este documento no registra resultados nuevos de esos comandos.
