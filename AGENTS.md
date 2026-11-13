# AGENTS.md

Instrucciones para cualquier agente (Claude Code, Cursor, etc.) que trabaje en este repo.

## Qué es

Demos de procesamiento de imágenes satelitales con datos abiertos e IA, para la charla
"Lo que ven los satélites antes que Wall Street" (NASA Space Apps Challenge Mendoza, 13-11-2026).

## Regla: el entorno se maneja con uv

Decidido por Lucas el 2026-11-12.

- Las dependencias viven en `pyproject.toml`; `uv.lock` se versiona. No hay `requirements.txt`.
- Agregar o sacar una dependencia: `uv add <paquete>` / `uv remove <paquete>`. Las de desarrollo
  (Jupyter), con `--dev`. Nunca `pip install` a mano.
- Todo se corre con `uv run ...`. No se activa el entorno ni se usa `python` o `pip` del sistema.
- Python fijado en 3.12 (`.python-version`).
- El código de `src/satdemo/` es un paquete instalable: el notebook lo importa sin tocar `PYTHONPATH`.

## Setup

```sh
uv sync                                   # crea .venv con todo, incluido Jupyter
uv run earthengine authenticate           # una vez; abre el navegador, lo hace Lucas
```

## Correr

```sh
uv run jupyter lab notebooks/01_soja_sequia.ipynb
uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_soja_sequia.ipynb
uv run streamlit run app/dashboard.py     # dashboard en http://localhost:8501, sin Earth Engine
```

Los datos que lee el dashboard (`data/processed/*.csv`, `salidas/pipeline/`) se regeneran con Earth Engine
desde `satdemo.features` (`extraer`, `serie_16dias`) y `satdemo.pipeline.generar`.

No hay linter, tests ni build: [PENDIENTE: definir si hacen falta].

## Regla dura: costo cero

Todo corre gratis. Decidido por Lucas el 2026-11-12; el porqué, en `docs/DECISIONS.md`.

**Se puede:**
- Datos de APIs o catálogos abiertos y públicos: NASA (Earthdata, Worldview, GIBS, FIRMS), ESA/Copernicus,
  USGS, NOAA, Microsoft Planetary Computer (STAC), Banco Mundial, FMI/FRED, INDEC, INV, USDA, FAO.
- Servicios con capa gratuita **que no piden cuenta de facturación**: Earth Engine en tier Community.
- Registros gratuitos con clave (FIRMS, FRED, Copernicus Data Space), siempre que no pidan tarjeta.
- Librerías y modelos open source.

**No se puede:**
- Vincular una cuenta de facturación a un proyecto de Google Cloud, ni subir de tier en Earth Engine
  (Contributor la exige). Proyecto vigente: `satelites-datos-ia`, tier Community, 150 EECU-horas/mes.
- Usar otros servicios de Google Cloud desde ese proyecto (Storage, BigQuery, Vertex, Compute): cobran.
- Imágenes o datos comerciales pagos (Maxar, Planet pagos, Airbus, proveedores de datos alternativos).
  Maxar Open Data sí, porque es gratuito.
- Cualquier servicio que pida tarjeta, aunque tenga prueba gratis.

**Ante la duda:** si una fuente o servicio no dice claramente que es gratis y sin tarjeta, no se usa.
Se anota en `PLAN.md` como pendiente y se le pregunta a Lucas.

**Si una demo se pasa de la cuota gratuita:** se achica (menos área, menos fechas, menor resolución) o
se precomputa. No se busca más cuota.

## Gotchas de setup

- `gcloud` no está instalado en la Mac de Lucas: lo de Google Cloud se hace por la consola web.
- El material del reel (video, audio, fotogramas) **no va al repo**: es de @socialai.ok. Vive en
  una carpeta local fuera del repo.
