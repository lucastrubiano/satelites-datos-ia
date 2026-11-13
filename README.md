# satelites-datos-ia

¿Se ve la sequía desde el espacio antes de la cosecha? Una demo de datos satelitales + IA para anticipar
el rinde de la soja por departamento en Argentina, con datos abiertos y gratis.

Material de la charla "Lo que ven los satélites antes que Wall Street" (NASA Space Apps Challenge Mendoza,
13-11-2026), de Lucas Trubiano · Trubi Data.

> Demo educativa. No es un modelo para producción ni para invertir.

## Qué hace

1. **Datos:** rinde de soja de MAGyP (100 departamentos × 25 campañas), verdor NASA MODIS, lluvia CHIRPS.
2. **Procesamiento:** Earth Engine calcula el verdor de enero a marzo sobre los píxeles de cultivo de cada departamento, sin bajar ninguna imagen.
3. **Predicción:** baseline contra regresión lineal y gradient boosting, validando hacia adelante en el tiempo.

**Resultado** (`notebooks/01_soja_sequia.ipynb`):
- La anomalía de verdor y la de rinde correlacionan 0,70.
- Error medio, validando año por año desde 2008: 27 % el baseline, 16 % el modelo lineal.
- Sequía 2022/23: el baseline esperaba 2.644 kg/ha, el modelo 1.890, y el real fue 1.720.

## Correrlo

**En Google Colab (lo más fácil):** abrí el notebook desde GitHub en Colab y ejecutá todo. No necesitás
cuenta de Earth Engine: usa las features ya calculadas en `data/processed/features.csv`.

**En tu máquina**, con [uv](https://docs.astral.sh/uv/):

```sh
uv sync
uv run jupyter lab notebooks/01_soja_sequia.ipynb
```

**Dashboard** (mapa en el tiempo, tendencias, cómo se tratan las imágenes, modelo y alertas):

```sh
uv run streamlit run app/dashboard.py
```

Para recalcular las features, poné `EXTRAER = True` y un proyecto de Earth Engine propio (tier Community,
gratis): `uv run earthengine authenticate`.

## Ideas para la hackathon

- Cambiá el cultivo: MAGyP publica maíz, trigo y girasol con el mismo formato.
- Probá otras features: NDVI de diciembre, temperatura máxima (ERA5-Land), humedad de suelo (SMAP).
- Inundaciones: Sentinel-1 (radar) atraviesa las nubes.

## Fuentes y licencias

| Dato | Fuente | Licencia |
|---|---|---|
| Rinde de soja | MAGyP, datos.gob.ar | CC-BY 4.0 |
| Departamentos | IGN, vía Georef | CC-BY 4.0 |
| NDVI | NASA MODIS MOD13Q1 v061 | Datos abiertos de NASA |
| Lluvia | CHIRPS | Abierta |
| Cultivos | ESA WorldCover 2021 | CC-BY 4.0 |

Más fuentes abiertas: `docs/fuentes.md`. Código bajo licencia MIT.

## Para agentes y colaboradores

`AGENTS.md` (setup, reglas de costo cero y de uv), `CLAUDE.md` y `docs/` (arquitectura, convenciones,
decisiones, glosario, flujo de trabajo, troubleshooting). Plan y pendientes: `PLAN.md`.
