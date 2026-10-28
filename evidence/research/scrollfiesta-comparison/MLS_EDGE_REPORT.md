# Proyección MLS adaptativa en bordes — experimento local

Implementada y ejecutada sobre el mismo recorte real y la misma máscara limpia de 7.459 vóxeles. Se conserva el radio 12, cinco iteraciones, los normales ajustados y las protecciones de separación nativas.

## Regla

Se mide el desplazamiento tangencial del centro ponderado de vecinos en las dos direcciones principales del plano, normalizado por sus varianzas: `q = Σ ((b·t_j)² / max(λ_j, 1e-12))`. Si `q > 0.25`, el paso normal se divide por `1 + s(q - 0.25)`; `s=2` (suave) o `s=8` (fuerte). La dirección del paso se conserva y su longitud no aumenta. Es un indicador geométrico de asimetría, no un detector certificado de bordes.
Activación experimental: `MLS_EDGE_ADAPT=soft` o `strong`. Sin esa variable, comportamiento anterior. La regla no consulta las etiquetas ni las coordenadas del objetivo.

## Resultado

| Variante | Cobertura de referencia | Área (vóxel²) | Distancia al extremo | Contactos numéricos |
| --- | ---: | ---: | ---: | ---: |
| off | 1999 | 897.137 | 4.103 | 0 (control previo equivalente) |
| soft | 2115 | 956.180 | 5.259 | 1 |
| strong | 2253 | 1013.890 | 7.017 | 0 |

La variante fuerte aumenta cobertura un 12,7 % frente al control limpio y un 10,3 % frente a los 2.042 vóxeles de la selección estable anterior. Todas sus 13.263 muestras de caras corresponden directamente a la capa 390; no aparecen muestras etiquetadas como capa vecina. El área apoyada por CT a distancia ≤1 es 1.013,726 / 1.013,890 vóxel². Sin embargo, empeora la llegada al extremo de 4,103 a 7,017 vóxeles. No cumple el objetivo conjunto.

## Localización de la pérdida

| Variante | Nube tras MLS | Tras BPA | Tras separación |
| --- | ---: | ---: | ---: |
| off | 2.550 | 2.994 | 4.103 |
| soft | 2.498 | 2.686 | 5.259 |
| strong | 2.496 | 4.587 | 7.017 |

Estas son distancias mínimas a puntos, no seguimiento del mismo vértice. La amortiguación propuesta apenas reduce la distancia de la nube MLS; la triangulación y separación posteriores amplifican la pérdida. No basta reducir el tamaño del paso para recuperar esta punta. No se han desactivado las protecciones ni forzado vértices hacia el objetivo.

## Verificación y límites

- Compilación incremental de cube_mesh correcta.
- Los 7 tests MLS existentes pasan con el cambio desactivado. El límite de un hilo impide validar paralelismo real.
- La geometría final con el cambio desactivado coincide exactamente con el control limpio anterior (vértices, normales y caras).
- Las dos variantes activas producen geometría distinta y ambas completan la ejecución nativa.
- QA inicial: enlace del ejecutable de tests incompleto; se añadió except.c y el segundo intento pasó. No fue un fallo de la corrida nativa.
- Se ejecutaron solo pruebas focalizadas; no la suite CTest completa del proyecto.
- Recorte de desarrollo condicionado por ruta conocida; falta un recorte independiente. Las comprobaciones geométricas y de etiquetas son finitas.

Todas las ejecuciones de cálculo fueron secuenciales: memoria máxima 384 MiB, swap cero, CPU 25 % de un núcleo, Nice=19, IOWeight=10 y dispositivos GPU inaccesibles. La corrida de tres variantes tuvo un pico del servicio de aproximadamente 151 MiB y mantuvo más de 12.046 MiB disponibles en el sistema. El monitor detiene trabajo si MemAvailable baja de 3.072 MiB.

## Estado

Se conserva la selección estable adaptive8 y la máscara limpia anterior. El cambio queda como prototipo optativo y no se publica ni se promueve. Binario original: build/cube_mesh.baseline. Binario experimental: build/cube_mesh.edge-adaptive. Diff: mls-edge-adaptive.patch.
