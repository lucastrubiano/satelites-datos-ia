# El reel que inspiró la charla

- Fuente: https://www.instagram.com/reel/DfPSFHToMyE/ (@socialai.ok, 02-11-2026, 81 s).
- Material extraído (local, **no va al repo**: es contenido de terceros):
  una carpeta local fuera del repo
  - `reel.mp4`, `audio.wav`
  - `transcripcion.txt` (whisper local, con marcas de tiempo)
  - `keyframes/` (9 fotogramas clave), `frames/` (27 cambios de escena), `contact_sheet.jpg`
- Si un fotograma va a una slide, va con crédito a @socialai.ok.

## Estructura

| Tiempo | Qué dice | Fotograma clave | Caso → demo |
|---|---|---|---|
| 0:00-0:17 | Fondos que cuentan autos en estacionamientos y saben cuánto vendió Walmart antes del anuncio | `01_satelite-fotografia`, `02_estacionamiento-ocupacion-35` | A |
| 0:17-0:36 | Estudio de Berkeley: ~5 M de fotos, 67.000 locales, 4-5 % en 3 días; del otro lado, inversores comunes | `03_retorno-antes-de-resultados`, `04_resultados-trimestrales` | A |
| 0:36-0:48 | Tanques con techo flotante: la sombra interna mide el volumen | `05_tanque-techo-flotante`, `06_sombras-tanques`, `07_petroleo-guardado` | B |
| 0:49-1:00 | Helada en Brasil, julio 2021: el café +33 % en una semana | `08_cafe-helada-2021` | C |
| 1:00-1:18 | "Datos alternativos": legal, pero no es una pelea pareja | `09_datos-alternativos-vs-oficiales` | D |

## Qué se verificó

Chequeo completo, con página del paper: notas de investigación locales, fuera del repo, §1.3.

| Afirmación | Veredicto |
|---|---|
| "Un estudio de Berkeley" | Correcto con matiz: 2 de 4 autores son de UC Berkeley |
| "Casi 5 millones de fotos" | Distorsionado: el paper dice 4,7 M de observaciones diarias, no fotos crudas |
| "67.000 locales" | Correcto: 67.078 |
| "4-5 % en 3 días" | Correcto en magnitud (4,60-4,76 %), pero son los 3 días alrededor del anuncio trimestral y es una estrategia long-short |
| Sombra de los tanques | Método confirmado (Orbital Insight, Satellite Today 2017) |
| Café +33 % en una semana | **Sin verificar** |
