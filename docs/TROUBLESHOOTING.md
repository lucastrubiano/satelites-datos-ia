# Troubleshooting

> Las trampas que ya te mordieron. Cada una ahorra una hora de agente (y tuya).

## La columna de lluvia sale vacía
- **Pasa cuando:** se hace `reduceRegions` sobre una imagen de una sola banda (CHIRPS).
- **Causa real:** con una sola banda, Earth Engine llama `mean` a la salida, no el nombre de la banda.
- **Solución:** `ee.Reducer.mean().setOutputs(["lluvia_mm"])`. Ya está en `features.py`.

## `earthengine authenticate` no hace nada
- **Pasa cuando:** se corre desde el `!` de Claude Code o sin `gcloud` instalado.
- **Causa real:** el modo por defecto espera input interactivo y no encuentra `gcloud`.
- **Solución:** `uv run earthengine authenticate --auth_mode=localhost:8085 --quiet` en segundo plano; imprime un link, se abre en el navegador y el token queda en `~/.config/earthengine/credentials`.

## El registro de Earth Engine como "trainer" pide datos que no tenemos
- **Pasa cuando:** se elige "Earth Engine trainer or trainee" como tipo de organización.
- **Causa real:** pide empresa de capacitación, curso y link a un curso formal, y vence al terminar el curso.
- **Solución:** "Other" + "Individual research or noncommercial use". Ya está registrado así.

## El formulario de Earth Engine cambia los campos al elegir una opción
- **Pasa cuando:** se completa el formulario tipeando por posición.
- **Causa real:** los campos se reacomodan según la respuesta anterior.
- **Solución:** mirar el formulario después de cada elección, antes de tipear.

## Códigos de departamento que no cruzan
- **Pasa cuando:** se cruza MAGyP con Georef.
- **Causa real:** los `XX000` de MAGyP son totales provinciales sin departamento; Chascomús (06217) cambió de código.
- **Solución:** `rinde.cargar` descarta los `XX000`; Chascomús queda afuera por no estar en Georef.

## Cosas que parecen rotas pero son a propósito
- El modelo predice rindes muy bajos en algunos departamentos en 2022/23: se pasa de rosca donde el NDVI cayó mucho. Se muestra así, no se "corrige".
- `extras/01_contar_autos_naip.py` no se corrió nunca: los autos son un caso explicado, no una demo.
- El repo no trae el video ni los fotogramas del reel: son de terceros.
