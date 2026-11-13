# Clima y precios en Argentina: qué mueve la aguja

> Relevado por búsqueda web el 2026-11-12. Son resúmenes de notas, **no abrí cada página**.
> Las cifras de la sequía son estimaciones hechas durante la campaña, no el cierre final.

## Resumen

| Evento | Qué golpea | Qué se mueve | Escala | ¿Se ve desde el satélite? |
|---|---|---|---|---|
| **Sequía** (La Niña) | Soja, maíz, trigo en la zona núcleo | **Volumen**: cosecha, exportaciones, dólares, PBI. En precio, la **harina de soja** más que el poroto | Macro, país | Sí: verdor y lluvia, meses antes de la cosecha |
| Heladas tardías y granizo | Vid, frutales (Mendoza, San Juan) | Cosecha de uva y precio de la uva y el vino | Regional | Parcial: helada sí (temperatura), granizo es muy localizado |
| Heladas y lluvias intensas | Hortalizas (tomate, lechuga, papa) | Precio al consumidor, en semanas | Local, corto plazo | Difícil: quintas chicas |
| Inundaciones | Siembra y cosecha en Buenos Aires y Santa Fe; ganadería | Área sembrada y atrasos; sin precio claro | Regional | Sí, muy visual (radar) |

## Sequía 2022-23: el evento que más movió

- Bolsa de Comercio de Rosario, marzo 2023: unos 50 millones de toneladas perdidas y US$ 14.140
  millones de ingresos menos. Soja en 27 Mt contra 49 Mt esperadas; maíz 35 contra 54; trigo 11,5 contra 19.
- Soja, maíz y trigo: 87 % de la producción de granos y 43 % de las exportaciones del país.
- Bolsa de Comercio de Córdoba: pérdidas de US$ 21.000 a 27.000 millones, cerca del 4 % del PBI.
- Las exportaciones del agro cayeron más de 41 % en 2023 (BCR).

## El matiz del precio de la soja

- **Harina de soja:** Argentina es el 39 % del comercio mundial. En Chicago subió más de 20 % entre
  noviembre de 2022 y febrero de 2023 y tocó un máximo de nueve años (US$ 504,20 por tonelada corta).
- **Poroto de soja:** reacción débil o nula. Hay notas que señalan que Chicago incluso bajó cuando se
  recortó la cosecha argentina, porque pesa más la producción de Brasil y de EE. UU.

Conclusión para la demo: con soja, la variable a predecir es la **producción** (y, en precio, la
harina), no el precio del poroto.

## Otros eventos

- Vendimia 2023: caída de 23 % en Mendoza y 21 % en el país por heladas tardías, granizo y falta de
  agua (INV). La menor oferta subió el precio de la uva.
- Hortalizas: subas de hasta 100 % en papa y tomate en Mendoza por heladas (septiembre 2026);
  tomate +41,7 % en el NOA por frío (julio 2026).
- Inundaciones 2025: más de un millón de hectáreas anegadas en Buenos Aires según productores
  (agosto 2025). No encontré una estimación económica consolidada.

## Hitos que mueven el precio de la soja (para el dashboard)

Precio de la harina: Banco Mundial, Pink Sheet, variación interanual calculada con `data/processed/precios_soja.csv`.

| Período | Qué pasó | Tipo | Fuente |
|---|---|---|---|
| 2007-2008 | Harina hasta +95 % interanual (abr-2008); la suba vino de maíz y trigo caros, no de falta de soja | Global | https://www.bls.gov/opub/btn/volume-9/pdf/a-historical-look-at-soybean-price-increases-what-happened-since-the-year-2000.pdf |
| 2008/09 | Sequía en Argentina | Clima AR | Rinde MAGyP y NDVI del repo |
| 2011/12 | Sequía en Argentina (La Niña): soja 40,1 Mt contra 49,1 de la campaña anterior (MAGyP) | Clima AR | https://www.infobae.com/2012/01/07/1041682-argentina-enfrenta-la-que-podria-ser-la-peor-sequia-los-ultimos-46-anos/ · https://www.bcr.com.ar/sites/default/files/2019-05/informe%2520especial%2520034%25202012_04_03.pdf |
| 2012 | Sequía del Medio Oeste de EE. UU.; soja en máximos; harina +64 % interanual (dic-2012) | Clima global | https://www.ers.usda.gov/webdocs/outlooks/37906/29017_ocs12g.pdf · https://www.bloomberg.com/news/articles/2012-07-19/soybeans-surge-to-record-as-midwest-drought-scorches-crop |
| 2017/18 | Sequía en la región núcleo, "la peor de los últimos 50 años" según la BCR; soja estimada en 32 Mt (abr-2018) | Clima AR | https://bcr.com.ar/sites/default/files/2019-05/bcr2018_08_17.pdf · https://www.iprofesional.com/comex/268901-por-la-sequia-el-estado-perdio-us1-700-millones-en-retenciones |
| ago-2020 a ene-2021 | Compras de China por la recuperación porcina; soja +50 % en EE. UU. | Global | https://farmpolicynews.illinois.edu/2021/01/chinese-demand-undergirds-robust-soybean-corn-prices/ |
| 2022/23 | Sequía en Argentina; harina +24 % interanual (dic-2022) | Clima AR | BCR, arriba |

Caídas del precio (causas globales):

| Período | Qué pasó | Fuente |
|---|---|---|
| 2.º semestre 2008 | Crisis financiera: derrumbe de commodities; soja de ~566 a ~377 USD/t entre el 3.º y el 4.º trimestre | https://thedocs.worldbank.org/en/doc/357071462307042606-0050022016/original/CMO2009April.pdf |
| 2014-2015 | Cosechas récord de EE. UU. y Sudamérica, stocks récord | https://www.grainews.ca/daily/u-s-grains-soybeans-fall-most-since-june-on-big-global-supplies · https://ers.usda.gov/webdocs/outlooks/38350/53772_ocs15i.pdf |
| 2024 | Argentina se recupera de la sequía; cosecha y molienda récord en Brasil; harina sudamericana en mínimos desde 2020 (nov-2024) | https://www.spglobal.com/commodity-insights/en/news-research/latest-news/agriculture/112724-south-american-soybean-meal-prices-drop-to-four-year-lows |

Sin fuente para su causa, y por eso sin marcar: la caída de 2017.

**Efecto base en 2009:** la harina subió de 318 USD/t (dic-2008) a 460 (jun-2009), +45 %, con la sequía de Argentina y Brasil (https://world-grain.com/articles/10066-oilseeds; la BCR recortó la cosecha a 41,7 Mt). La variación interanual siguió negativa porque comparaba contra el pico de 2008, y el pico interanual de fines de 2009 compara contra el piso de la crisis. Por eso el dashboard muestra el precio en USD/t por defecto.

**Por mes** (anomalía de verdor vs. variación del precio de la harina 2 meses después, ~25 años por mes): relación débil todo el año. Lo más fuerte en temporada de soja es enero (−0,21); junio-agosto llega a −0,40, pero ese verdor es trigo y pasturas, no soja.

## Fuentes

- https://bichosdecampo.com/llorones-con-razones-como-llego-la-bolsa-de-rosario-a-calcular-que-este-ano-se-perdieron-50-millones-de-toneladas-de-granos-por-la-sequia
- https://www.lanacion.com.ar/economia/campo/el-costo-de-la-sequia-ya-asciende-a-us-10400-millones-para-los-productores-de-soja-trigo-y-maiz-nid17012023/
- https://chequeado.com/el-explicador/sequia-cuales-son-las-estimaciones-sobre-el-impacto-economico/
- https://www.bcr.com.ar/es/print/pdf/node/97508
- https://news.agrofy.com.ar/noticia/203926/sube-precio-soja-severa-sequia-que-impacta-argentina
- https://www.iprofesional.com/economia/380200-soja-argentina-por-que-el-mundo-reacciona-con-indiferencia
- https://www.unidiversidad.com.ar/vendimia-2023-heladas-tardias-granizo-y-escasez-hidrica-generaron-una-marcada-merma-en-la-cosecha
- https://www.sitioandino.com.ar/verduras-heladas-y-cambio-estacional-subieron-el-100-n5631129
- https://bichosdecampo.com/cuanto-se-pierde-si-no-se-puede-sembrar-1-millon-de-hectareas
