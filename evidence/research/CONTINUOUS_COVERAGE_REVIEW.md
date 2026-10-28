# Revisión del certificado de cobertura continua

Fecha: 2026-10-28. Revisión matemática y estática de
`certify_patch_coverage.py`, su lector de VMESH en
`exact_patch_intersections.py` y
`scrollfiesta-comparison/hole-recovery-v5/continuous-coverage-02.json`.
No se ejecutaron comandos de análisis, pruebas, búsquedas, cálculos geométricos
ni un replay de testigos. No se recalcularon hashes. El principal informó que
pasaron los 16 controles sintéticos; esto no se presenta como una segunda
ejecución independiente.

## Veredicto

No se encontró un bloqueo matemático o de implementación para la afirmación:
**la distancia de Hausdorff entre las dos superficies trianguladas completas
guardadas es como máximo 1/4 en sus coordenadas de vóxel**. El resultado es un
límite superior continuo, no una estimación basada en muestreo ni el cálculo del
valor exacto de esa distancia.

La afirmación corresponde a las uniones geométricas de triángulos cerrados en
los archivos identificados por el certificado. No afirma igualdad de área,
igualdad de superficies, conservación de multiplicidad de la zona sustituida,
topología, correspondencia anatómica, fibras o ausencia de intersecciones.
Esas propiedades requieren sus comprobaciones separadas. Los vértices no
referenciados por caras no forman parte de la superficie aquí definida.

## Archivos y resultado declarado

Estos son los SHA-256 **registrados** en JSON02, no recalculados por esta revisión:

| Entrada | Caras | SHA-256 |
| --- | ---: | --- |
| Fondo compartido v4 (`source`) | 5143 | `5106f6cbec34df7decca0d3a01c33597f14da73ac3bdc35faa0f8f92180ef60e` |
| Superficie v2 (`before`) | 5160 | `d15db1d0cd0e08078c8ef786e121ae8189ddcca1bffe1aba51e551709c3e8a94` |
| Candidato combinado guardado (`after`) | 5160 | `6c8666e673df057b010f9824e6bef5071b106810b1ad9efe22966752eb81a6b1` |

El archivo `after` es `hole-recovery-v5/saved-evaluation-02/combined.vmesh`.
El resultado no se transfiere automáticamente a otra ejecución de producción:
se necesita igualdad de archivo o una comprobación adicional de igualdad de la
geometría pertinente. La igualdad de multiconjuntos de triángulos por coordenadas
es suficiente para transferir esta propiedad; coincidir en cantidad de caras o
métricas muestreadas no lo es.

JSON02 declara `passed=true`, `status=certified`,
`include_retained_background=true`, `delta_exact=1/4`,
`delta_squared_exact=1/16`, y cero caras fuente ausentes o invertidas en ambas
entradas. La resta deja 17 caras antiguas y 17 nuevas.

| Dirección explícita | Geometrías raíz únicas | Celdas visitadas | Hojas certificadas | Profundidad máxima | Pendientes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Parche antiguo → superficie nueva completa | 16 | 1020 | 769 | 4 | 0 |
| Parche nuevo → superficie antigua completa | 17 | 3373 | 2534 | 5 | 0 |

Las 17 caras antiguas tienen 16 geometrías únicas debido al par duplicado. El
destino antiguo tiene 5159 geometrías únicas entre 5160 caras; el destino nuevo
tiene 5160. Estas deduplicaciones son correctas para distancia entre conjuntos.
El informe contiene 3303 testigos de hojas entre ambas direcciones. Sus contadores
y estados son consistentes con el algoritmo; esta revisión no revalidó cada
testigo real mediante ejecución.

## Por qué la conclusión cubre las superficies completas

Sean `S`, `O` y `N` las uniones geométricas de fondo retenido, parche antiguo y
parche nuevo. El código resta primero el **multiconjunto orientado** de `source`
de cada archivo completo. Canonicaliza solo rotaciones cíclicas de las tres
coordenadas, de modo que preserva multiplicidad y orientación durante esta
comprobación. No aceptar caras fuente ausentes asegura:

```text
before = S ∪ O
after  = S ∪ N
```

Estas igualdades son entre conjuntos geométricos, aunque la comprobación de
retención que las fundamenta es más fuerte y usa multiconjuntos orientados.
Todo punto de `S` pertenece a ambos archivos y tiene distancia cero al otro.
Solo quedan las dos obligaciones explícitas:

```text
para todo x de O: distancia(x, S ∪ N) ≤ 1/4
para todo y de N: distancia(y, S ∪ O) ≤ 1/4
```

En modo background, el código usa como destinos los triángulos de los archivos
completos opuestos, no una copia de `source` con índices potencialmente
desplazados. Por tanto, los IDs de cara exportados se resuelven contra el archivo
destino real. Ambas obligaciones, junto al fondo común, dan las dos distancias
dirigidas de Hausdorff y su máximo ≤1/4.

Un triángulo repetido, incluso con winding opuesto, vuelve a aportar exactamente
los mismos puntos al conjunto. Deduplicarlo después de la resta no elimina
ningún punto cuya distancia hubiera que demostrar. Esto no es un certificado
de conservación de masa, área contada con multiplicidad ni superficies
orientadas: el par inválido antiguo cuenta una sola vez para Hausdorff.

La comparación de JSON01 entre parches aislados era una obligación diferente y
más fuerte en zonas donde un parche nuevo se aproxima al fondo retenido. Añadir
el fondo de ambos archivos no cambia delta ni modifica las superficies; formula
la comparación correcta de las superficies completas. Conservar JSON01 como
evidencia inconclusa de su alcance más restringido es apropiado.

## Validez del test local exacto

Para una microcara con vértices `a,b,c`, el programa calcula con fracciones su
centroide `m` y
`R²=max(||a−m||²,||b−m||²,||c−m||²)`. Para cualquier punto `x` del triángulo,
la convexidad de la norma garantiza `||x−m||≤R`.

Los tres pesos enteros exportados son no negativos y suman `2^24`. Su combinación
baricéntrica racional define un punto `q` que pertenece al triángulo destino
cerrado. No es necesario que sea el punto más cercano. Si `D²=||m−q||²`, entonces:

```text
distancia(x, destino) ≤ ||x−q|| ≤ ||x−m|| + ||m−q|| ≤ R + D
```

El test racional del código es equivalente a `R+D≤delta` para cantidades no
negativas. Define `t=delta²−D²−R²` y exige:

```text
t ≥ 0
t² ≥ 4 D² R²
```

El primer requisito fija el signo que se perdería al elevar al cuadrado. Juntos
implican `t≥2DR`, y por tanto `delta²≥(D+R)²`. Delta también es no negativo.
Esto prueba el límite para **todos** los puntos de la microcara, no solo para su
centroide y vértices.

Las coordenadas se leen de binary32 como valores exactos y se convierten a
`Fraction`; no se reconstruyen desde los OBJ decimales. La búsqueda flotante de
un punto cercano solo propone pesos. La cuantización fuerza pesos enteros
dentro del simplex y las distancias de aceptación se recalculan racionalmente.
Un error de la heurística puede impedir terminar, pero no convertir un test
racional falso en verdadero.

Las cuatro subdivisiones por puntos medios son exactas y cubren íntegramente
la cara padre. Una pila vacía con todas las hojas aceptadas cubre cada raíz.
La ruta alternativa `identical` también es válida: exige igualdad exacta del
multiconjunto de tres esquinas y proporciona distancia cero para toda la raíz.

El filtro AABB usa una cota inferior exacta de distancia entre las cajas raíz y
destino. Solo excluye un destino si esa cota es estrictamente mayor que delta;
la igualdad se conserva. Además, el replay de una prueba aceptada no necesita
revalidar el filtro: cada punto `q` exportado pertenece a una cara real del
destino completo y demuestra su hoja directamente.

## Cómo revalidar los testigos sin repetir la búsqueda

Un verificador de replay puede prescindir de la heurística flotante, ordenación
de destinos, AABB y búsqueda adaptativa. Debe realizar las comprobaciones
siguientes, siempre contra los archivos cuyos hashes declara JSON02:

1. Validar los tres VMESH y sus hashes, leer coordenadas binary32 exactas y
   repetir únicamente la inclusión/resta de multiconjuntos orientados. Comprobar
   que no falta ninguna copia fuente. Reconstruir los parches de 17 caras con
   sus índices reales, que son **base cero**.
2. Agrupar sus caras por el multiconjunto no orientado de tres esquinas exactas.
   Usar el primer representante de cada geometría, como el productor, y comprobar
   que todas las 16/17 geometrías raíz tienen testigos. Para cualquier copia
   descartada por deduplicación, verificar su igualdad geométrica exacta con su
   representante; no deduplicar por proximidad.
3. Comprobar formato, índices y rutas. Cada ruta contiene solo `0,1,2,3`; los
   índices de raíz pertenecen al parche correcto y los de destino al archivo
   completo opuesto. Rechazar testigos duplicados y raíces ajenas a la resta.
4. Para cada raíz, insertar las rutas en un trie. Ninguna hoja puede tener
   descendientes y todo nodo interno debe tener los cuatro hijos. El árbol debe
   terminar en hojas para toda la raíz. Alternativamente, verificar ausencia de
   prefijos y duplicados y `sum(4^(-longitud_ruta))=1` exactamente. Esto certifica
   la partición, incluso con niveles adaptativos mezclados.
5. Para un testigo regular de seis campos, reconstruir la microcara siguiendo la
   ruta desde los tres vértices **en el orden almacenado de la cara raíz**. Los
   hijos están especificados en `proof.subdivision_children`; calcular todos los
   puntos medios racionalmente. Leer la cara destino en su orden real y exigir
   que los tres pesos sean enteros no negativos cuya suma sea exactamente
   16777216. Reconstruir `q`, `m`, `D²`, `R²` y repetir las dos desigualdades
   racionales anteriores con delta²=1/16.
6. Para un testigo `identical` de cuatro campos, exigir ruta vacía e igualdad
   exacta del multiconjunto de esquinas raíz/destino. Esa hoja cubre toda la raíz
   y excluye otras hojas de la misma raíz mediante el control de prefijos.
7. Verificar ambas direcciones y la retención común. Los contadores y límites
   declarados pueden cotejarse como metadatos, pero no sustituyen estas
   comprobaciones geométricas y de partición.

Este procedimiento solo reproduce 3303 pruebas explícitas y las restas de
multiconjuntos; no busca triángulos destino ni candidatos nuevos. No se ejecutó
durante esta revisión. Se preparó `verify_patch_coverage_witnesses.py` para ese
replay, acompañado de `test_verify_patch_coverage_witnesses.py`; ambos quedan
pendientes de ejecución por el principal. Comparte únicamente el lector estricto
VMESH con el certificado de intersecciones y no importa código del productor de
cobertura. Reconstruye por separado subdivisiones, particiones e inequaciones.
Por defecto exige exactamente 3303 testigos, limita hojas, profundidad, tamaño
de JSON/entradas y memoria, y guarda un resultado nuevo sin sobrescritura.

```text
python3 -m unittest discover -s research -p test_verify_patch_coverage_witnesses.py -v
python3 research/verify_patch_coverage_witnesses.py --certificate research/scrollfiesta-comparison/hole-recovery-v5/continuous-coverage-02.json --output NUEVO-REPLAY.json
```

Ambos comandos requieren `research/run_holefill_guarded.sh` con nombres nuevos.
El resultado del replay no debe sustituir JSON02. Si otra salida de producción
ya tiene igualdad exacta de multiconjuntos orientados con `combined.vmesh`, esa
evidencia separada permite transferir la propiedad de conjuntos sin buscar otra
geometría ni repetir el certificado adaptativo.

## Límites de la conclusión

El certificado es una aproximación bidireccional de conjuntos a escala 1/4 en
las coordenadas guardadas. No demuestra que cada punto nuevo corresponda a una
fibra o a la misma hoja, que las áreas sean iguales ni que exista un mapa
biyectivo entre triángulos. Un plegado o una superficie adicional muy cercana
puede satisfacer Hausdorff; por eso siguen siendo necesarios los certificados
independientes de frontera, fuente, ángulos, winding e intersecciones.

Los límites de búsqueda producen `inconclusive`, nunca una aceptación de hojas
pendientes. Una separación exactamente delta puede no terminar con este método
de bolas; esa limitación afecta completitud y coste, no la validez de una prueba
aceptada. JSON02 terminó con ambas direcciones certificadas y cero pendientes.
