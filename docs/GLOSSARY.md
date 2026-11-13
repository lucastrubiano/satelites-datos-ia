# Glosario y entidades

## Términos del dominio
- **NDVI** → índice de verdor de la vegetación, calculado con las bandas roja e infrarroja cercana. Acá, la señal de cultivos.
- **Anomalía** → diferencia contra el promedio histórico de la misma fecha del año. Es como sacamos la estacionalidad.
- **Fill rate** → autos / cocheras de un estacionamiento. La señal del paper de retailers.
- **Resolución espacial** → tamaño del píxel en el suelo. Define qué objetos se ven: un auto necesita 0,5 m o menos.
- **Revisita** → cada cuántos días el satélite vuelve a pasar por el mismo lugar.
- **Datos alternativos** → datos no oficiales (imágenes, tráfico, etc.) que anticipan a los datos oficiales.
- **Zona núcleo** → región agrícola pampeana más productiva de Argentina. Polígono exacto: [PENDIENTE].

## Entidades principales
- **Demo** → un script de `demos/` que corre solo y deja una imagen de salida. Se identifica por letra en `PLAN.md` (A, C, E).
- **Caso** → una historia de la charla (autos, petróleo, helada, caso propio). No todo caso tiene demo.
- **Fuente** → un catálogo, API o dataset de `docs/fuentes.md`, con licencia anotada.

## Siglas y nombres internos
- **STAC** → estándar para buscar imágenes en catálogos (Planetary Computer, Copernicus).
- **COG** → GeoTIFF optimizado para leer solo una parte del archivo por HTTP.
- **EECU** → unidad de cómputo de Earth Engine. La cuota del tier Community se mide en EECU-horas.
- **NAIP** → fotos aéreas de 60 cm del USDA, solo de EE. UU.
- **FIRMS** → sistema de NASA de focos de incendio activos.
- **INV** → Instituto Nacional de Vitivinicultura.
- **BCR** → Bolsa de Comercio de Rosario.
