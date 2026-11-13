# Decisiones tomadas

> Una entrada por decisión. Lo importante es el "por qué" y el "qué descartamos".

## 2026-11-12 · Costo cero: solo capas gratuitas y APIs abiertas
- **Decisión:** todo corre gratis. Earth Engine en tier Community, sin cuenta de facturación. Reglas en `AGENTS.md`.
- **Por qué:** pedido de Lucas. Es una charla y una mentoría, sin cliente que lo pague.
- **Descartado:** tier Contributor de Earth Engine (exige cuenta de facturación); imágenes comerciales (Maxar, Planet).
- **Estado:** vigente

## 2026-11-12 · Entorno con uv
- **Decisión:** `pyproject.toml` + `uv.lock`, Python 3.12, todo con `uv run`. Reglas en `AGENTS.md`.
- **Por qué:** pedido de Lucas. Un solo comando (`uv sync`) deja el entorno igual para cualquier participante.
- **Descartado:** `venv` + `pip` + `requirements.txt`; un bucket o stack local de nube (no hace falta: Earth Engine computa del lado del servidor y los datos locales pesan pocos MB).
- **Estado:** vigente

## 2026-11-12 · Colab para los asistentes, uv para desarrollar
- **Decisión:** el notebook corre igual en Google Colab y en local. En Colab, la primera celda clona el repo e instala el paquete. Con `EXTRAER = False` (default) usa `data/processed/features.csv` y no necesita Earth Engine.
- **Por qué:** pedido de Lucas, para simplificar el arranque de los asistentes: un link y listo. Colab gratuito no pide tarjeta.
- **Descartado:** solo local (cada asistente tendría que instalar uv y autenticar Earth Engine).
- **Estado:** vigente. Depende de que el repo sea público. **El camino de Colab no está probado todavía.**

## 2026-11-12 · Departamentos por regla objetiva y cruce por código INDEC
- **Decisión:** los 100 departamentos con más soja sembrada 2000-2024 y dato en todas las campañas. Polígonos de Georef (IGN), cruzados con MAGyP por `departamento_id`.
- **Por qué:** reproducible y explicable en una línea; el código evita el cruce por nombre.
- **Descartado:** dibujar a mano la zona núcleo; polígonos FAO GAUL (cruce por nombre).
- **Estado:** vigente

## 2026-11-12 · Dashboard en Streamlit
- **Decisión:** `app/dashboard.py` en Streamlit + Plotly, con mapas MapLibre sobre teselas de CARTO (gratis, sin clave). Solo lee archivos del repo.
- **Por qué:** pedido de Lucas (insights, mapa, embudo de imágenes, features). Es código, se levanta con un comando y se puede publicar gratis en Streamlit Community Cloud.
- **Descartado:** Metabase (pide Docker y una base, y los tableros se arman a mano en la interfaz, no con código).
- **Estado:** vigente

## 2026-11-12 · Serie de NDVI cada 16 días para el mapa en el tiempo
- **Decisión:** `data/processed/ndvi_16dias.csv`, NDVI de cultivo por departamento en cada imagen MODIS, feb-2000 a oct-2026 (61.400 filas). Anomalía contra el mismo departamento en la misma fecha del año.
- **Por qué:** pedido de Lucas: un gráfico de líneas con los pozos de sequía y un mapa que sigue al slider.
- **Estado:** vigente

## 2026-11-12 · La sequía se mide en toneladas, no en precio
- **Decisión:** el gráfico del mapa en el tiempo superpone por defecto la **producción de soja del país** (MAGyP, todos los departamentos) y ofrece el **valor de la cosecha** (producción × precio del poroto en abril-junio, Banco Mundial). El precio queda como opción.
- **Por qué:** idea de Lucas: la sequía golpea la cantidad, y la plata que entra es cantidad × precio. Con datos: verdor ene-mar ↔ producción 0,93 descontando la tendencia (0,69 en cambio % interanual), contra −0,35 con el precio del poroto. En 2022/23 la producción cayó 43 % y el valor de la cosecha 53 %, aun con precio alto.
- **Descartado:** el precio como métrica principal (lo mueven causas globales; ver `docs/clima-precios-argentina.md`). Datos de exportaciones del INDEC: más directos, pero no se bajaron todavía.
- **Estado:** reemplazada en el gráfico por "Mapa en el tiempo en tres paneles" (el valor de la cosecha ya no se muestra). La conclusión (la sequía se ve en las toneladas) sigue.

## 2026-11-12 · Foco de la charla: fundamentos, no mercados
- **Decisión:** el eje son los fundamentos de big data e IA para procesar imágenes satelitales, más un bloque de ML y series de tiempo. Los mercados son gancho y cierre.
- **Por qué:** pedido de Lucas, alineado con lo que pidió Nahuel ("tenemos estos datos, ¿cómo los procesaríamos?").
- **Descartado:** una charla centrada en trading con datos alternativos.
- **Estado:** vigente

## 2026-11-12 · Recorte de casos
- **Decisión:** demos de estacionamientos (autos) y de la helada del café; el petróleo solo explicado; un caso propio de sequía o inundación contra cosecha.
- **Por qué:** validado por Lucas.
- **Descartado:** luces nocturnas vs. PBI (descartado por Lucas); viñedos de Mendoza como caso central (mercado chico).
- **Estado:** vigente

## 2026-11-12 · Caso propio: soja con producción como variable
- **Decisión:** sequía 2022-23, prediciendo el rinde de soja por departamento. Es la única demo; el resto de los casos va en slides.
- **Por qué:** la sequía argentina movió mucho el volumen y la harina, pero poco el precio del poroto, que se forma en Chicago (`docs/clima-precios-argentina.md`).
- **Descartado:** precio del poroto de soja como variable; aceite de oliva en España (Lucas prefirió soja).
- **Estado:** vigente (confirmado por Lucas el 2026-11-12)

## 2026-11-12 · Proyecto de Earth Engine registrado como no comercial
- **Decisión:** proyecto `satelites-datos-ia`, tipo "Other", uso individual no comercial. La elegibilidad vence el 2028-05-12.
- **Por qué:** es el registro que corresponde a una charla sin fin comercial.
- **Descartado:** "Earth Engine trainer" (pide link a un curso formal y vence al terminar el curso).
- **Estado:** vigente. Si el proyecto se usa para un cliente, hay que registrar otro como comercial.

## 2026-11-12 · Ciclo de la soja marcado en el dashboard
- **Decisión:** constante `CICLO` en `app/dashboard.py` con siembra, período crítico y cosecha de Argentina, Brasil y EE. UU.
  Se marca en tres lugares: bandas en "Una campaña contra las demás", franjas opcionales del período crítico (15-ene a 15-mar)
  en el gráfico grande del mapa en el tiempo (apagadas por defecto) y un calendario por país con las fechas de precio
  (nov, feb, may) en "De la sequía al precio".
- **Por qué:** pedido de Lucas, para que se entienda por qué el verdor de ene-mar anticipa la cosecha y por qué el precio se
  mide de noviembre a febrero y a mayo. Fechas con fuente en `docs/clima-precios-argentina.md` ("Ciclo de la soja").
- **Descartado:** período crítico feb-mar (la BCR lo ubica desde el 15-ene para la soja de 1ra); bandas de Brasil a altura
  completa (se superponen con las de Argentina: van como franja tenue abajo).
- **Estado:** vigente. Sin fuente para el período crítico de Brasil ni de la soja de 2da.

## 2026-11-12 · Mapa en el tiempo en tres paneles: verdor, volumen, precio
- **Decisión:** el gráfico principal muestra tres paneles con el mismo eje de tiempo, sin selectores: verdor vs. normal,
  producción de soja del país por campaña (rojas las de sequía) y una sola serie de precio, la harina de soja (USD/t). Las
  sequías AR cruzan los tres paneles; las causas globales van solo en el de precio, como "otros factores", con un checkbox
  que atenúa el precio dentro de esas bandas. Debajo, una tabla de las cuatro sequías con datos de `cadena_precio.csv`.
- **Por qué:** pedido de Lucas: las opciones de harina, poroto, valor y variación interanual confundían. Se lee de arriba
  abajo: cae el verdor, cae el volumen, sube el precio.
- **Descartado:** precio del poroto, valor de la cosecha y variación interanual en ese gráfico.
- **Estado:** vigente.
