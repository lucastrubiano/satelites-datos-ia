"""Etapas del tratamiento de imágenes, para mostrar en el dashboard: imágenes por etapa y embudo de píxeles.

Se genera una vez con Earth Engine y se guarda en `salidas/pipeline/`; el dashboard solo lee esos archivos.
"""
import json
import urllib.request
from pathlib import Path

import ee

from satdemo import features

# Campaña de la sequía: enero a marzo de 2023
INICIO, FIN = "2023-01-01", "2023-04-01"


def _bajar_thumb(img: ee.Image, region: ee.Geometry, vis: dict, destino: Path) -> None:
    # MODIS viene en proyección sinusoidal: se muestra en lat/lon para que no salga torcido
    url = img.visualize(**vis).getThumbURL(
        {"region": region, "dimensions": 900, "format": "png", "crs": "EPSG:4326"}
    )
    with urllib.request.urlopen(url, timeout=120) as r:
        destino.write_bytes(r.read())


def generar(deptos: ee.FeatureCollection, salida: Path) -> dict:
    """Guarda una imagen por etapa y devuelve el embudo de píxeles de ene-mar 2023."""
    salida.mkdir(parents=True, exist_ok=True)
    zona = deptos.geometry()
    region = zona.bounds()
    cultivos = ee.Image(ee.ImageCollection(features.WORLDCOVER).first()).eq(40)
    col = ee.ImageCollection(features.MODIS).filterDate(INICIO, FIN)
    escena = ee.Image(col.first())
    ndvi_vis = {"min": 0.1, "max": 0.9, "palette": ["8c510a", "dfc27d", "f6e8c3", "c7eae5", "5ab4ac", "01665e"]}

    def ndvi(img):
        return img.select("NDVI").multiply(0.0001)

    def buena(img):
        return img.select("SummaryQA").lte(1)

    etapas = [
        ("01_escena_falso_color", "Una escena MODIS cruda (falso color: infrarrojo, rojo, azul)",
         escena.select(["sur_refl_b02", "sur_refl_b01", "sur_refl_b03"]).clip(zona),
         {"min": 0, "max": 5000}),
        ("02_ndvi_escena", "NDVI de esa escena, sin limpiar",
         ndvi(escena).clip(zona), ndvi_vis),
        ("03_calidad", "Calidad del píxel (SummaryQA): verde se usa, rojo se descarta (nubes, sombra)",
         buena(escena).clip(zona), {"min": 0, "max": 1, "palette": ["d73027", "1a9850"]}),
        ("04_cultivos", "Máscara de cultivos (ESA WorldCover, clase 40)",
         cultivos.clip(zona), {"min": 0, "max": 1, "palette": ["f0f0f0", "238b45"]}),
        ("05_ndvi_limpio", "NDVI máximo ene-mar 2023, solo cultivo y buena calidad",
         col.map(lambda i: ndvi(i).updateMask(buena(i))).max().updateMask(cultivos).clip(zona), ndvi_vis),
    ]
    # Lo normal = promedio de los máximos de ene-mar de cada año 2001-2022 (máximo contra máximo)
    def maximo_anual(anio):
        anio = ee.Number(anio)
        return (
            ee.ImageCollection(features.MODIS)
            .filterDate(ee.Date.fromYMD(anio, 1, 1), ee.Date.fromYMD(anio, 4, 1))
            .map(lambda i: ndvi(i).updateMask(buena(i)))
            .max()
        )

    normal = ee.ImageCollection(ee.List.sequence(2001, 2022).map(maximo_anual)).mean()
    anom = etapas[-1][2].subtract(normal.updateMask(cultivos)).clip(zona)
    etapas.append(("06_anomalia", "Anomalía: NDVI máximo 2023 menos el máximo promedio 2001-2022 (rojo = menos verde que lo normal)",
                   anom, {"min": -0.2, "max": 0.2, "palette": ["b2182b", "f4a582", "f7f7f7", "92c5de", "2166ac"]}))

    for nombre, _, img, vis in etapas:
        _bajar_thumb(img, region, vis, salida / f"{nombre}.png")
        print("imagen:", nombre)

    # Embudo: observaciones píxel × escena dentro de los 100 departamentos, a 250 m
    def contar(img):
        return img.reduceRegion(ee.Reducer.count(), zona, scale=250, maxPixels=1e10, tileScale=4).values().get(0)

    unos = ee.Image.constant(1).clip(zona)
    escenas = col.size()
    pixeles = ee.Number(contar(unos.reproject(escena.select("NDVI").projection())))
    validas = col.map(lambda i: buena(i).selfMask().set("n", contar(buena(i).selfMask()))).aggregate_sum("n")
    en_cultivo = col.map(
        lambda i: buena(i).updateMask(cultivos).selfMask().set("n", contar(buena(i).updateMask(cultivos).selfMask()))
    ).aggregate_sum("n")
    embudo = {
        "escenas": escenas.getInfo(),
        "pixeles_zona": pixeles.getInfo(),
        "observaciones": pixeles.multiply(escenas).getInfo(),
        "observaciones_buena_calidad": validas.getInfo(),
        "observaciones_en_cultivo": en_cultivo.getInfo(),
        "filas_finales": deptos.size().getInfo(),
    }
    meta = {"embudo": embudo, "etapas": [{"archivo": f"{n}.png", "titulo": t} for n, t, _, _ in etapas]}
    (salida / "pipeline.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2))
    return meta
