# Reproducción local de tinta desde una superficie CT pública

2026-10-28. Trabajo local, sin publicación ni envío. Esta prueba usa una superficie aplanada pública de PHercParis4; todavía no conecta nuestras mallas v5 al detector ni demuestra una lectura nueva.

## Recursos autorizados

El usuario autorizó ampliar el límite tras fallar la instalación de Torch con 384 MiB. `run_ink_guarded.sh` y `ink_guard.py` fijan y verifican MemoryMax=2 GiB, CPUQuota=25%, Nice=19, IOWeight=10, swap=0, GPU inaccesible, cinco límites de hilos=1 y reserva de escritorio de 3072 MiB. Las ejecuciones son secuenciales. Los límites y evidencias históricos de geometría no se modificaron.

Se conserva el fallo `native/ink-cpu-runtime-install-01.failure.json`. La extracción posterior por streaming reutilizó la rueda descargada; el runtime está aislado en `ink-reading/runtime-stream-v1`. La primera inferencia terminó correctamente en 39,79 s, con RSS máximo del proceso hijo de 501,14 MiB y memoria disponible mínima de 5936,28 MiB, según `native/ink-cpu-pilot-01.status.json`.

## Fuente, modelo y transformación

Se reproduce el detector público [ScrollPrize ink_9um](https://huggingface.co/scrollprize/ink_9um), revisión 7109667, checkpoint `hybrid_3d2d-seed42/step-075000.pth`, SHA256 `e635558ae6a1a807a7e5ec1e83adfd45bc3c0ac53883ea43f1d4e085d62a9cab`. El código oficial se fija a ScrollPrize/villa `47a9c37f6f8e99afdab47bb46ad425aa726f5dc0`; originales, atribuciones, MIT y cambios de imports opcionales están en `ink-reading/vendor-v1`. No se alteraron operaciones matemáticas del modelo.

La fuente publicada es PHercParis4, segmento `20231016151002`, volumen `2.4um-0.22m-78keV-volume-20260411134726.zarr`, nivel 2, ZYX/C/uint8. La selección Z13:97 se agrupa por cuatro con media float32, redondeo `rint` y conversión uint8, siguiendo el pooling oficial guardado; produce 21 planos a 9,6 µm. El modelo recibe 17 planos centrales, normalización robusta oficial por parche, parches 128², stride 64, CPU float32, lote 1 y composición Hann de probabilidades. No hay entrenamiento, TTA ni etiquetas en la entrada del modelo.

El criterio completo del protocolo (palabra con referencia espacial y transformación a CT 3D) no se cumplió antes de inferir. Se avanzó únicamente como reproducción técnica asistida de la superficie publicada, un alcance más limitado; no se considera superada la aceptación del protocolo ni se sustituye el mapa faltante por parecido visual.

**El segmento w00 se utilizó en el entrenamiento publicado.** La selección inicial usa la distribución de anotaciones y la ampliación posterior usa inspección visual del primer resultado. Son pruebas asistidas de desarrollo. Las métricas contra esas etiquetas no miden generalización ni una transcripción independiente. Véanse `INK_READING_PROTOCOL.md`, `INK_CPU_MODEL_REVIEW.md` e `INK_PIPELINE_REVIEW.md`.

## Primer recorte conservado

`ink-reading/paris4-w00-reference-v1`: ROI Y3200:3456, X8064:8832, 21×256×768. Los 33 parches terminaron con probabilidades finitas y cobertura completa. A umbral fijo 0,5, el acuerdo con las etiquetas asistidas fue Dice 0,92799; TP84742, TN98714, FP9034 y FN4118. Se guardan probabilidades sin contraste y visualización con `clip((p-0.25)/0.5)`.

La inspección local y una revisión independiente coincidieron en trazos grandes cortados y una posible Ο central (`?Ο?`), sin palabra completa verificable. No se declara traducción. El control de entrada constante produjo estructura espacial (media 0,461638, desviación 0,083245); no es un control limpio sin tinta y limita la interpretación de trazos aislados.

## Ampliación de contexto

`ink-reading/paris4-w00-context-v2`: ROI Y2944:3712, X7424:9472, 21×768×2048; 96 chunks CT. Se congeló antes de su inferencia, manteniendo modelo y parámetros. La adquisición terminó en 176,99 s, RSS máximo 93,28 MiB y reserva mínima 4425,55 MiB. El nombre histórico del archivo de entrada dice `21x256x768`, pero su cabecera y manifiesto certifican la forma real 21×768×2048; se conserva para no sustituir evidencia. El script actual corrige nombres futuros y se preserva el snapshot usado.

La revisión detectó que faltaba exigir igualdad entre el SHA de la entrada y el SHA declarado por su manifiesto. Se añadió esa comprobación antes de importar el modelo para v2. Los SHA existentes de v1 ya coincidían; no se repitió su inferencia. Los snapshots de scripts permiten distinguir ambas versiones.

La inferencia ampliada **no terminó**: el guard la detuvo a los 304,03 s tras registrar 302 de 341 parches. `native/ink-cpu-context-02.status.json` declara `reason="desktop reserve"`, retorno -15 y memoria disponible mínima 3031,49 MiB, inferior a la reserva 3072 MiB. El RSS máximo del hijo fue 510,27 MiB; systemd registró pico de cgroup 526,8 MiB y swap 0. No fue agotamiento del límite nuevo de 2 GiB. No se aumentó ese límite ni se redujo la reserva para reintentar.

No se escribió `result.json` ni una probabilidad completa: las acumulaciones intermedias estaban en RAM y no constituyen una salida recuperable. Los datos adquiridos, controles y logs quedan conservados. `render_ink_context_result.py` quedó preparado y revisado estáticamente, pero no se ejecuta sobre un intento incompleto. No hay transcripción ni métricas v2. Reanudar requiere primero suficiente memoria disponible del sistema; el runner actual tendría que repetir la inferencia, no la descarga.

Tras avisar el usuario de que ya no estaba jugando, se comprobó de nuevo `/proc/meminfo`: MemAvailable=6467248 KiB (unos 6,17 GiB). Se inició el reintento `ink-cpu-context-03`, salida nueva `paris4-w00-context-v2/inference-v2`, reutilizando exactamente entrada, checkpoint y parámetros. Se conservó el intento interrumpido y no se modificó la reserva ni otro límite.

**Reintento completado:** 341/341 parches, 341,50 s, RSS máximo 517,60 MiB, mínimo de memoria disponible 5605,44 MiB; systemd registró pico de cgroup 721,7 MiB y swap 0. Cobertura completa de 1572864 píxeles y probabilidades finitas. SHA256 de `probability.npy`: `d59e924ceabebdf6aaf1ba62552c17daf0b814f33c1c53841c21fc4ae20f3141`. Render posterior completado, sin modificar resultados numéricos.

Comparación a umbral fijo 0,5 **solo en 483793 píxeles supervisados**: TP117523, TN345930, FP16716, FN3624, Dice0,920356, precisión0,875476, recall0,970086. Es acuerdo con etiquetas públicas asistidas de un segmento de entrenamiento, no exactitud de transcripción ni generalización. Métricas y hashes de imágenes: `paris4-w00-context-v2/review-v1/metrics.json`.

La inspección local previa a abrir etiquetas distingue tentativamente `…ϹΟ…`, sin palabra verificable; véase `review-v1/VISUAL_REVIEW.md`. No se rellenan caracteres por contexto ni se declara traducción. El control constante sigue siendo no uniforme; ampliar contexto no lo corrige.

La segunda revisión visual, realizada sin ver etiquetas v2 ni recibir la lectura del coordinador, registró `? Ι? Ϲ Ο Λ? Υ? ?` y tampoco identificó palabra verificable. Coincide en las formas centrales. No es cegamiento completo: ese revisor había visto v1 y su máscara en una tarea anterior. Registro: `review-v1/INDEPENDENT_VISUAL_REVIEW.md`.

## Límite de lectura y siguiente conexión

Hay una [transcripción editorial publicada de Paris4](https://www.iris.unina.it/handle/11588/985203), pero no se encontró todavía un registro espacial verificable entre esta ROI moderna y columna/línea/palabra editorial. La búsqueda acotada y sus fuentes están en `INK_TRANSCRIPTION_REFERENCE.md`; no demuestra que ese registro no exista. No se ha adquirido el mapa de esta superficie al CT 3D original. Faltan esas correspondencias para verificar una palabra y para conectar el detector a nuestra geometría con controles de coordenadas.

Las mallas recuperadas v5 y sus certificados se preservan aparte; esta reproducción no resuelve la continuidad entre cores ni autoriza relajar sus gates.

Inventario final: `ink-reading/evidence-manifest-v1.json`, producido por `freeze_ink_evidence.py` bajo el mismo guard tras completar el reintento. Incluye casos, entradas y salidas, scripts, fuentes vendor, revisiones, recibos y logs de trabajos previos. Excluye los archivos de runtime instalados y los grandes binarios de caché: sus hashes anteriores quedan referenciados en recibos de adquisición/extracción. El log y status del propio inventariado quedan fuera para evitar inventariar un archivo que todavía estaba escribiéndose.
