# Plan

> **Rev. 4 (2026-11-12, noche) — vigente.** Plan aprobado por Lucas: una sola demo, sequía 2022/23 → rinde
> de soja por departamento, en `notebooks/01_soja_sequia.ipynb`. **Prototipo funcionando**: corre de punta
> a punta con datos reales.
>
> Pendiente: deck (slides 2 a 14), probar el camino de Colab, repo público (Lucas confirma antes), Linear LUC-267.
>
> Lo que sigue abajo es la rev. 3, histórica: las demos A y C pasaron a ser casos explicados en slides.

# Plan rev. 3 (histórico)

> Estado: **recorte validado por Lucas el 2026-11-12** (rev. 3). Falta elegir el caso propio.
> La charla es el 13-11 a las 17 h.
> Orden de trabajo: (1) validar enfoque → (2) prototipo de demos → (3) charla.

## Enfoque

El foco son los **fundamentos de big data e IA para procesar imágenes satelitales**. La predicción de
mercados es el gancho y el cierre, no el tema. Se suma un bloque corto de ML y series de tiempo.

## Recorte

| # | Caso | Tratamiento | Dato (gratis) | Técnica | Fundamento que enseña | Estado |
|---|---|---|---|---|---|---|
| A | Autos en estacionamientos | **Demo** | NAIP 60 cm, Planetary Computer (STAC) | Detección con YOLO OBB preentrenado en DOTA | Resolución, COG y lectura por ventana, tiling, transfer learning | Script escrito, **sin correr** |
| B | Tanques de petróleo | **Solo explicado** | — | Sombra interna del techo flotante | De píxel a medida física | Slide |
| C | Helada del café, Brasil, julio 2021 | **Demo** | Temperatura mínima ERA5-Land + NDVI MODIS sobre la zona cafetera; precio del café (FMI vía FRED) | Anomalía contra el promedio histórico, serie temporal | Bandas, data cube, cómputo al lado del dato | Sin empezar |
| E | **Caso propio**: sequía o inundación → cosecha y precio | **Demo** | Ver opciones | Mismo pipeline que C, cambiando polígono y cultivo; regresión con rezago | Baseline, validación temporal, pocos datos, correlación vs. causa | Sin empezar |
| ~~D~~ | ~~Luces nocturnas vs. PBI~~ | Descartado por Lucas | | | | |

## E — opciones para el caso propio

| | Caso | Señal satelital | Variable a predecir | A favor | En contra |
|---|---|---|---|---|---|
| E1 | **Aceite de oliva, España**, sequía 2022-23 | Anomalía de NDVI y de lluvia sobre el olivar de Andalucía (Jaén) | Producción de la campaña y precio del aceite | España es el mayor productor mundial: una sequía local mueve el precio global. La cadena satélite → cosecha → precio se ve limpia | No es Argentina |
| E2 | **Soja, Argentina**, sequía 2022-23 | Anomalía de NDVI y de lluvia sobre la zona núcleo | Producción estimada de la campaña | Caso local y reciente | El precio de la soja se forma en Chicago: la sequía argentina pega en la producción y las exportaciones, no tanto en el precio |
| E3 | Trigo, Argentina, misma sequía | Ídem, en invierno | Producción | Mismo código que E2 | Mismo límite de precio |
| E4 | Vino (Mendoza o España) | NDVI de viñedos, heladas tardías | Cosecha (INV) | Público local | El precio del vino no es un commodity con serie limpia |
| E5 | Inundación puntual | Sentinel-1 antes / después | Área sembrada afectada | Muy visual | Un evento solo: no hay serie para predecir |

**Recomendación:** E1 (aceite de oliva) como caso principal y E2 (soja) como "ahora cambien el
polígono" para el público local: es el mismo código con otro recorte y otro cultivo. La diferencia
entre los dos enseña algo en sí: cuándo un dato local mueve un precio y cuándo no.

Límite a decir en la charla: MODIS arranca en 2000, así que son unas 25 campañas. Alcanza para un
gráfico y una regresión simple, no para un modelo complejo.

⚠️ Las cifras de producción y precio de E1 y E2 **no están verificadas**: no pongo números hasta
bajar las series. Los identificadores de catálogo de `docs/fuentes.md` están de memoria.

## Qué falta mapear

- [ ] A: elegir el local (bbox) y confirmar que NAIP tiene dos fechas ahí. Probar `conf` de YOLO sobre 60 cm.
- [ ] C: polígono de la zona cafetera (sur de Minas Gerais). Chequea el "+33 % en una semana" del reel.
- [ ] E: polígono de olivar (Jaén) y de zona núcleo; máscara de cultivos; series de producción y precio.
- [x] Proyecto de Earth Engine: `satelites-datos-ia`, no comercial, tier Community (2026-11-12). Falta `earthengine authenticate` en la máquina.
- [ ] Leer los 14 desafíos de 2026 (`docs/competencia.md`).

## Decisiones que necesito de Lucas

1. ¿E1 + E2, como recomiendo, u otra combinación?
2. ¿Cuántos minutos dura la charla?
3. ~~¿Tenés cuenta de Earth Engine?~~ Resuelto: proyecto `satelites-datos-ia`.

## Mapa del repo

- `docs/reel.md`: qué dice el reel, escena por escena, y qué se verificó.
- `docs/fuentes.md`: de dónde sale cada dato, dataset y modelo.
- `docs/competencia.md`: de dónde sacan datos los equipos y proyectos de años anteriores.
- `docs/charla.md`: esqueleto de la charla.
- `demos/`: un script por demo. `02_ndvi_vinedos_mendoza.py` queda como base de C y E (mismo patrón).
