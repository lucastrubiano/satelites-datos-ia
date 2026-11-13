# Mapa de fuentes

Versión corta. El detalle, con links y páginas, está en
`~/Documents/goals/charla-space-apps/investigacion.md` (investigado el 2026-11-12).

## Imágenes

| Fuente | Píxel | Revisita | Acceso | Para qué demo |
|---|---|---|---|---|
| Sentinel-2 (ESA) | 10 m | 5 días | Copernicus Data Space (STAC), Earth Engine | C |
| Landsat 8/9 (NASA/USGS) | 30 m | 8 días combinados | EarthExplorer, Earth Engine | Serie larga |
| VIIRS luces nocturnas (NASA/NOAA) | 500 m | Diaria / mensual | Earth Engine `NOAA/VIIRS/DNB/MONTHLY_V1/VCMSLCFG` | D |
| NAIP (USDA, solo EE. UU.) | 60 cm | Cada 2-3 años | Planetary Computer (STAC) | A, B |
| Maxar Open Data | 30-50 cm | Solo desastres | STAC en S3, CC BY-NC 4.0 | Plan B de A |
| SAOCOM (CONAE) | 10 m, radar | 8 días | Catálogo CONAE, con registro | Mención Mendoza |

Regla de resolución: para contar autos hace falta 0,5 m o menos. Con 10 m un auto no llena un píxel.

## Datos tabulares (la variable a predecir)

| Dato | Fuente | Para qué demo |
|---|---|---|
| Ventas de supermercados por provincia, mensual | INDEC, encuesta de supermercados (Cuadro 7) | D |
| IPC, para deflactar | INDEC | D |
| Cosecha de uva por provincia | INV, anuarios | C (variante) |
| Ventas trimestrales de retailers de EE. UU. | SEC, API XBRL (`data.sec.gov`) | A (variante) |

## Fuentes globales para C y D (rev. 2)

⚠️ Identificadores escritos de memoria, **sin verificar hoy**. Confirmar en el catálogo al correr la demo.

| Dato | Qué es | Acceso | Demo |
|---|---|---|---|
| MODIS NDVI (MOD13Q1) | Verdor, 250 m, cada 16 días, global, desde 2000 | Earth Engine `MODIS/061/MOD13Q1` | C1 |
| ERA5-Land | Reanálisis de clima, ~9 km, diario, global | Earth Engine `ECMWF/ERA5_LAND/DAILY_AGGR` | C1 |
| NASA FIRMS | Focos de incendio activos, VIIRS 375 m, casi en tiempo real | firms.modaps.eosdis.nasa.gov (mapa y API con clave gratuita); Earth Engine `FIRMS` | C2 |
| MODIS área quemada (MCD64A1) | Área quemada mensual, 500 m | Earth Engine `MODIS/061/MCD64A1` | C2 |
| Sentinel-1 | Radar banda C, 10 m, atraviesa nubes | Earth Engine `COPERNICUS/S1_GRD` | C3 |
| Global Flood Database | Inundaciones históricas mapeadas con MODIS | Earth Engine `GLOBAL_FLOOD_DB/MODIS_EVENTS/V1` | C3 |
| NASA Worldview | Visor: incendios, humo, nubes, nieve, día por día | worldview.earthdata.nasa.gov | C2, C3 en vivo |
| VIIRS luces nocturnas, anual | Radiancia media anual, 500 m, global | Earth Engine `NOAA/VIIRS/DNB/ANNUAL_V22` | D1 |
| Bordes de país | Polígonos para agregar | Earth Engine `USDOS/LSIB_SIMPLE/2017` | D1 |
| Sentinel-5P NO2 | Dióxido de nitrógeno troposférico, diario | Earth Engine `COPERNICUS/S5P/OFFL/L3_NO2` | D3 |

| Variable a predecir | Fuente | Demo |
|---|---|---|
| Precio del café arábica, mensual | FMI, vía FRED (serie `PCOFFOTMUSDM`) | C1 |
| Crecimiento del PBI real por país | Banco Mundial, API abierta (indicador `NY.GDP.MKTP.KD.ZG`) | D1 |
| EMAE, actividad mensual de Argentina | INDEC | D2 |
| Producción y rindes por país y cultivo | FAOSTAT; USDA FAS (PSD) | C, D2 |

## Fuentes para el caso propio E: sequía → cosecha → precio (rev. 3)

⚠️ De memoria, **sin verificar hoy**. Luces vs. PBI (D) quedó descartado: sus filas de arriba ya no se usan.

| Dato | Qué es | Acceso |
|---|---|---|
| MODIS NDVI (MOD13Q1) | Verdor, 250 m, cada 16 días, desde 2000 | Earth Engine `MODIS/061/MOD13Q1` |
| CHIRPS | Lluvia diaria, ~5 km, desde 1981 | Earth Engine `UCSB-CHG/CHIRPS/DAILY` |
| SMAP | Humedad de suelo, desde 2015 | NASA Earthdata; Earth Engine |
| ESA WorldCover | Cobertura del suelo a 10 m, para enmascarar cultivos | Earth Engine `ESA/WorldCover/v200` |
| Límites administrativos | Provincias y departamentos | Earth Engine `FAO/GAUL/2015/level1` y `level2` |

| Variable a predecir | Fuente |
|---|---|
| Precio del aceite de oliva, mensual | FMI, vía FRED (buscar la serie "Global price of Olive Oil") |
| Precio en origen del aceite, España | Ministerio de Agricultura (MAPA); Comisión Europea, panel de mercados agrícolas |
| Producción de aceite por campaña | MAPA / AICA; Consejo Oleícola Internacional |
| Producción de soja y trigo, Argentina | Bolsa de Cereales de Buenos Aires; Secretaría de Agricultura (estimaciones agrícolas); USDA FAS (PSD) |
| Precio de la soja | Chicago (CBOT); FMI vía FRED, mensual |
| Cosecha de uva | INV (Argentina) |

## Datasets etiquetados

| Dataset | Qué trae | Licencia |
|---|---|---|
| DOTA | `small vehicle`, `large vehicle`, `storage tank`, cajas orientadas | No comercial |
| xView | 60 clases, 0,3 m | CC BY-NC-SA 4.0 |
| COWC | 32.716 autos, 15 cm | Sin confirmar |
| CARPK | 89.777 autos en estacionamientos, dron | Sin confirmar |
| Airbus Oil Storage | 13.592 tanques, ~1,2 m | CC BY-NC-SA 4.0 |

## Modelos

| Modelo | Uso |
|---|---|
| YOLO OBB (Ultralytics, AGPL-3.0) | Detectar autos y tanques en imagen submétrica |
| SAM / segment-geospatial | Segmentar sin etiquetar, también con texto |
| Prithvi-EO-2.0 (NASA + IBM, Apache 2.0) | Cultivos, inundaciones, incendios, a 30 m |
| Clay | Cultivos y uso del suelo, multisensor |

## Librerías

`pystac-client`, `planetary-computer`, `odc-stac`, `rasterio`, `geopandas`, `earthengine-api`,
`geemap`, `ultralytics`, `torchgeo`, `segment-geospatial`.

## Papers

- Katona, Painter, Patatoukas, Zeng. JFQA 60(2), 2025. Estacionamientos y retornos.
- Mukherjee, Panayotov, Shon. JFE 141, 2021. Tanques de petróleo y nubosidad.
- Henderson, Storeygard, Weil. AER 102(2), 2012. Luces nocturnas y PBI.
- Albornoz et al. Rev. FCA UNCuyo, 2019. Viñedos de Mendoza con Sentinel-2.
