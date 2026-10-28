# Revisión visual del contexto continuo

Actualización posterior del principal: se ejecutó la comprobación inicial de semillas en una caja local, con perfiles y cortes enlazados. El método se detuvo antes de normales/interfaces/tracking porque ninguna semilla pasó su detector fijado. Véase `PARIS4_LOCAL_BRANCH_RESULT.md`. El resto conserva el análisis visual y la propuesta previos, no afirma que el seguimiento3D ya se haya completado.

Se inspeccionaron `native/paris4-calibration-context-v1/xy-z144.png`,
`xy-z160.png` y `radial-z-curtain.png`, además de las tiras ya guardadas
`z152-x128-y128.png` y `z168-x128-y128.png`. Revisión visual únicamente:
no se ejecutaron cálculos, código ni nuevas pruebas; no se cambió v1.

**Resultado: la continuidad visual resuelve parte de la fragmentación, pero
no identifica aún un pitch radial defendible para todo el ROI.** Hay regiones
de material separadas y candidatos a adyacencia; no falta señal en general.
Lo que sigue sin resolverse es qué superficies medias corresponden a las
prominencias de la región exterior y cuál es su relación de vecindad radial.

## Qué añade el contexto

En la cortina, una banda interior aproximadamente en radio263 al inicio
Z144 se desplaza hacia radio235 al llegar aZ176. Se puede seguir visualmente
esa banda oblicua durante el intervalo. A su derecha existe un corredor de
menor intensidad antes de la región de material exterior.

En esa región exterior se distinguen cerca deZ160 dos bandas aproximadamente
en radios282 y300–305. HaciaZ168–176 se aproximan y dejan de distinguirse como
dos trazas separadas. Esto explica por qué los segmentos y máximos de intensidad
del inventario no se pueden contar como pasos independientes constantes.
La continuidad se observa en el CT sin color; no se deduce del ID248.

La convergencia es compatible con pliegue, intersección oblicua de una banda
con estructura interna o contacto entre superficies. Esta imagen no permite
elegir entre esas hipótesis. La cortina sigue el rayo haciaXY128,128 en cadaZ:
su ángulo cambia. Una aproximación de trazas en esta superficie curva tampoco
es por sí sola una prueba de conexión física de superficies en3D.

En los cortesXY144/160, las bandas próximas al ROI presentan curvatura y
estructura interna; la región exterior no ofrece una única interfaz central
nítida que pueda prolongarse sin ambigüedad hastaZ176. El corredor oscuro
entre regiones es evidencia favorable de separación local, pero no resuelve
el centro de la banda exterior ni la identidad de sus dos prominencias.

## Ventanas visuales congelables, sin convertirlas en centros

Estas ventanas aproximadas sirven para referir las mismas regiones en una
revisión posterior. **No son intervalos de confianza, espesores medidos ni
centros de hoja**, y no se emiten como calibración. La lectura visual tiene
precisión de varios vóxeles; los límites deliberadamente amplios incluyen
material y su incertidumbre de identificación. No reducirlos después para
obtener un pitch favorable al zipper.

| Zlocal | Banda interior A: intervalo radial aproximado | Región exterior B: identificación posible |
| --- | --- | --- |
| 144 | 258–272 | Material entre284–316; no congelar dos centros separados. |
| 152 | 251–266 | Prominencia interior aproximadamente281–292 y exterior294–313, candidatas que requieren asociación3D. |
| 160 | 247–259 | Dos bandas candidatas:277–288 y294–312; separadas en esta sección. |
| 168 | 238–251 | Región274–307; unión/contacto/proyección no resueltos, no asignar centro único. |
| 176 | 227–244 | Región267–297; las ramas previas no se separan de manera inequívoca. |

La lista permite señalar una bandaA trazable y localizar el problema deB.
No permite afirmar queA–Binterior es una pareja de vueltas adyacentes en todo
Z144–176. Tampoco permite considerarBinterior–Bexterior como un paso adicional.
No se calcula separación de estas ventanas ni se toma su punto medio como
medición física.

## Dato local mínimo que falta

Falta una **identificación3D de las interfaces y superficie media deB en la
zona de convergencia Z160–176**, enlazada a las dos bandas visibles enZ152/160.
Debe resolver si hay una lámina plegada con dos ramas, un solo espesor oblicuo,
o dos láminas que se aproximan/contactan. Después debe comprobarse la ausencia
de otra superficie entreA y la rama deB seleccionada, conservando la asociación
al menos en varios ángulos próximos al ROI.

Ese dato podría obtenerse del CT local mediante cortes ortogonales y trazado
volumétrico centrados en esas ventanas, incluyendo el vecindario posterior
aZ176 si allí continúa la convergencia. Todavía no se ha demostrado que haga
falta descargar otro volumen. Si la resolución del CT local no separa las
interfaces, se necesita una anotación local explícita de superficies medias y
adyacencias, o contexto CT de mayor resolución/alcance de la misma región con
transformación documentada. No basta otra asignación del mismo ID volumétrico.

Esto no exige certificar el rollo entero: exige resolver esas ramas y sus
centros antes de convertir distancias de material en paso de láminas. Una
vez fijados, la medición puede ser asistida y experimental, con incertidumbre
y validación del modelo radial. El número de muestras actuales no sustituye
esa identificación, porque los rayos observan repetidamente la misma región.

**Decisión operativa:** no emitir nueva tabla ni scalar, y mantener
`calibration_valid=false` y `winding_gate_ready=false` con la evidencia actual.
La nueva inspección aporta continuidad parcial y localiza la obstrucción;
no convierte las candidatas en adyacencias confirmadas ni invalida la opción
de resolverlas con un dato local específico.

## Revisión posterior: cortes ortogonales completos

Se inspeccionaron `native/paris4-seam-orthogonal-v1/yz-x128.png`,
`xz-y128.png` y `xz-y144.png`, sin ejecutar cálculos. EnYZ128, la regiónB es
una banda curva relativamente ancha; enXZ128 yXZ144 contiene estructura
interna y corredores de baja intensidad cuya sección cambia. No se ve una
superficie media única con sus dos caras identificadas ni un doblez inequívoco
que enlace exactamente las dos prominencias radiales deZ160. El color común
de la máscara no resuelve esa relación. Por tanto, **estos cortes tampoco
distinguen ramas de una hoja de interfaces de espesor**.

Hay además una limitación geométrica concreta: YZ128 atraviesa el plano de
costura, pero las dos prominencias del rayo oblicuo no están ambas enX128.
XZ128 tampoco contiene todo ese rayo. Su comparación muestra el vecindario,
pero no sigue los mismos dos puntos en3D. Eso explica por qué seis cortes
fijos pueden conservar la ambigüedad sin que falte información en el cubo.

### Una operación3D local mínima, con parada

Usar una sola subregión del CT ya disponible: sourceXYZ
`[112,176]×[112,160]×[144,192]`, que cubre ambas bandas y su convergencia
aparente, con margen. No generar superficies por umbral ni reutilizar mallas
del pipeline. Inicializar dos **ventanas de seguimiento**, no centros conocidos,
en el rayoZ160: radios277–288 y294–312 ya registrados arriba.

La operación es un seguimiento local con cortes multiplanares enlazados:
identificar la cresta y ambas interfaces de cada banda enZ160, seguirlas en
cortesZ consecutivos dentro de esa caja y comprobar cada conexión dudosa en
un corteY/X que pase **por la misma posición3D seguida**. Guardar polilíneas
de cresta/interfaces, posiciones de duda y capturasCT sin color; la máscara
se usa como referencia secundaria. Bastan estas dos trazas locales: no se
propone entrenar un modelo, reconstruir todo el cubo ni crear un nuevo mesher.

En la zona donde se aproximan, extraer un perfil/sección aproximadamente normal
a cada banda usando su tangente local seguida. Este es el dato adicional:
separar espesor normal real de anchura causada por cortar material oblicuamente.
No promediar las dos crestas ni suavizar atravesando un hueco para obtener
una traza única.

Criterios de cierre de esta única operación:

- **Pliegue local respaldado:** las dos crestas continúan hasta un doblez
  visible, con interfaces enlazadas consistentemente en cortes ortogonales
  vecinos y sin unión creada por umbral. Esto identifica dos ramas de una
  misma banda local; no las convierte automáticamente en dos vueltas.
- **Espesor aparente respaldado:** al observar normal a la banda se identifica
  un único cuerpo delimitado por dos interfaces, y se explica cómo su sección
  oblicua produjo las dos prominencias. Guardar la normal y los perfiles;
  no concluirlo solo porque dos picos se hayan unido al suavizar.
- **Ambiguo o contacto:** si no se pueden seguir las interfaces sin saltar,
  si las bandas tocan y la conexión no se resuelve, o si una traza sale de la
  caja antes de decidir, parar con esa localización y causa. No ampliar
  iterativamente el dominio ni cambiar umbrales para conseguir una respuesta.

La comparación exige persistencia en cortes contiguos y correspondencia del
mismo punto3D; una sola sección favorable no basta. El producto es una decisión
local trazable o una ambigüedad localizada, nunca un pitch automático. Solo
después de fijar esa relación tendría sentido decidir qué separación medir
para el gate. Esta operación todavía no se realizó y no presupone datos externos.
