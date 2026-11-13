# Convenciones de código

## Estilo
- Formato: [PENDIENTE: no hay formateador definido]
- Naming: notebooks `NN_que_hace.ipynb`; módulos en snake_case; nombres en español, identificadores de librerías como vienen
- Imports: el notebook importa `satdemo` como paquete instalado (uv), sin tocar `PYTHONPATH`

## Patrones que SÍ usamos
- Notebook = narrativa de la charla: celdas cortas, un título por paso, salida visible. La lógica va en `src/satdemo/`.
- Configuración arriba del notebook, en mayúsculas: `EXTRAER`, `PROYECTO_EE`, `CAMPANIAS`, `N_DEPARTAMENTOS`.
- El notebook corre igual en local y en Colab, y sin Earth Engine con `EXTRAER = False`.
- Cómputo en Earth Engine, del lado del servidor: nunca bajar escenas.
- Anomalías contra el promedio de cada departamento, calculadas solo con campañas de entrenamiento.
- Validación hacia adelante en el tiempo; nunca mezclar campañas al azar.
- Baseline siempre primero en cualquier tabla de resultados.
- Cada gráfico se guarda en `salidas/` para las slides.

## Patrones PROHIBIDOS
- Nada que cobre: regla de costo cero en `AGENTS.md`.
- `pip install` a mano o `requirements.txt`: regla de uv en `AGENTS.md`.
- Claves o credenciales en el código o en el notebook.
- Cifras en docs o slides sin fuente y fecha.
- Material de terceros (el reel) o imágenes satelitales descargadas en el repo.

## Tests
- Dónde van: [PENDIENTE: no hay tests]
- Qué se testea sí o sí: `uv run jupyter nbconvert --to notebook --execute --inplace notebooks/01_soja_sequia.ipynb` corre de punta a punta.

## Commits
- Formato: Conventional Commits en español (`feat: ...`, `docs: ...`, `fix: ...`).
