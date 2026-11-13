# Esqueleto de la charla

> Borrador sin validar. Título: "Lo que ven los satélites antes que Wall Street".
> Foco: fundamentos y tips de big data e IA para procesar imágenes satelitales.
> Los mercados son el gancho y el cierre.

| # | Bloque | Idea central | Apoyo |
|---|---|---|---|
| 0 | Gancho | Sam Walton contaba autos desde una avioneta; hoy se hace desde el espacio | Paper JFQA, ~4,7 % en 3 días. Petróleo: solo explicado (sombra de los tanques) |
| 1 | Una imagen satelital es una tabla | Raster, bandas, píxel. Tres resoluciones: espacial, temporal, espectral. Elegís dos | Tabla de fuentes; ¿se ve un auto? |
| 2 | Big data: no bajes nada | Los archivos pesan gigas. STAC para buscar, COG para leer solo una ventana, data cubes, llevar el cómputo al dato | Demo A (lectura por ventana), Earth Engine |
| 3 | Limpiar antes de modelar | Nubes, sombras, corrección atmosférica, niveles de producto (L1C vs L2A). Óptico vs. radar: el radar ve de noche y con nubes | Incendios e inundaciones en Worldview (C2, C3) |
| 4 | IA: de píxeles a números | Índices (NDVI) vs. detección vs. segmentación vs. modelos fundacionales. Arrancar con preentrenado, etiquetar al final | Demo A (YOLO), Prithvi para inundaciones e incendios |
| 5 | De números a predicción | Agregar por lugar y fecha. Anomalía contra el promedio histórico. Baseline primero. Validar hacia adelante en el tiempo, nunca al azar | Demo C (helada del café y precio), demo E (sequía → cosecha → precio: aceite de oliva o soja) |
| 6 | Tips | Lista corta de errores típicos | Ver abajo |
| 7 | Cierre | Es legal, pero el dato cuesta cientos de miles de dólares por año. Los fundamentos son gratis | Recursos y repo |

## Tips candidatos (elegir 5)

- Mirá la resolución antes que el modelo: si el objeto no llena varios píxeles, ningún modelo lo ve.
- Filtrá por nubes en la búsqueda, no después de bajar.
- Leé por ventana (COG) y procesá por teselas con solape.
- Compará contra el mismo período del año anterior: la estacionalidad engaña.
- Un baseline tonto primero (el valor del año pasado). Si tu modelo no le gana, no hay señal.
- Separá train y test por fecha. Mezclar al azar filtra el futuro.
- Deflactá todo lo que esté en pesos.
- Guardá el polígono y la fecha de cada número: sin linaje no se puede auditar.
- Revisá la licencia: mucho dato y modelo "abierto" es no comercial.

## Pendiente de definir

- Duración y formato (ver `PLAN.md`, decisiones).
- Qué demos van en vivo.
- Slide de recursos: conecta con LUC-269.
