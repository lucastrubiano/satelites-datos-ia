# Arquitectura

## En una frase
Un notebook que cruza el verdor satelital (NASA MODIS, calculado en Earth Engine) con el rinde oficial de
soja por departamento, y compara un baseline contra dos modelos para anticipar la cosecha.

## Stack
- Lenguaje / runtime: Python 3.12, entorno con uv (`pyproject.toml` + `uv.lock`)
- Framework principal: Jupyter; corre en local y en Google Colab
- Base de datos: ninguna; CSV en `data/`
- Servicios externos: Google Earth Engine (proyecto `satelites-datos-ia`, tier Community), solo si `EXTRAER = True`
- Librerías clave: `earthengine-api`, `pandas`, `scikit-learn`, `geopandas`, `matplotlib`

## Mapa de carpetas
- `notebooks/01_soja_sequia.ipynb` → la demo, corrida, con salidas guardadas
- `app/dashboard.py` → dashboard Streamlit: mapa en el tiempo, mapa por campaña, tendencias, embudo de imágenes, features, modelo y alertas
- `src/satdemo/` → paquete: `rinde.py` (MAGyP), `features.py` (Earth Engine: features por campaña y serie cada 16 días), `modelo.py` (baseline, modelos, validación), `pipeline.py` (imágenes por etapa y embudo de píxeles)
- `data/processed/ndvi_16dias.csv` → NDVI por departamento en cada imagen MODIS, para el mapa en el tiempo
- `salidas/pipeline/` → una imagen por etapa del tratamiento y `pipeline.json` con el embudo
- `data/raw/` → CSV de MAGyP y GeoJSON de departamentos, tal como se bajan
- `data/processed/features.csv` → NDVI y lluvia por departamento y campaña; versionado para no depender de Earth Engine
- `salidas/` → PNG para las slides
- `extras/` → scripts de otros casos, sin verificar
- `docs/` → contexto para agentes y material de la charla

## Flujo de datos
1. `rinde.py` baja el CSV de MAGyP y elige los 100 departamentos con más soja y serie completa.
2. `features.py` sube los polígonos a Earth Engine y, por campaña, reduce NDVI (ene-mar, cultivo, buena calidad) y lluvia (nov-mar). Devuelve 2.500 filas.
3. El notebook cruza por `departamento_id` + `anio`.
4. `modelo.py` valida hacia adelante: para cada campaña, entrena con las anteriores y calcula anomalías con esos promedios.
5. Salidas: tabla de errores y PNG en `salidas/`.

## Lo que NO existe (y no hay que crear)
- No hay bucket, base de datos ni stack de nube propio: Earth Engine computa del lado del servidor.
- No hay modelos de visión ni entrenamiento sobre imágenes.
- No hay predicción de precios: solo rinde.
- No hay app ni API propia.
- No hay datos comerciales pagos.
