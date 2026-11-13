"""Verdor (MODIS NDVI) y lluvia (CHIRPS) por departamento y campaña, calculados en Earth Engine.

Nada se baja: Earth Engine hace el cómputo en sus servidores y devuelve una tabla chica.
"""
import json
from pathlib import Path

import ee
import pandas as pd

MODIS = "MODIS/061/MOD13Q1"  # NDVI 250 m, cada 16 días, desde 2000
CHIRPS = "UCSB-CHG/CHIRPS/DAILY"  # lluvia diaria, ~5 km
WORLDCOVER = "ESA/WorldCover/v200"  # cobertura del suelo 10 m; clase 40 = cultivos


def departamentos_ee(geojson: Path, ids: list[str]) -> ee.FeatureCollection:
    """Sube los polígonos de Georef (IGN) que pidamos, como FeatureCollection, sin crear assets."""
    feats = [
        f
        for f in json.loads(geojson.read_text())["features"]
        if f["properties"]["id"] in set(ids)
    ]
    return ee.FeatureCollection(
        [ee.Feature(f["geometry"], {"departamento_id": f["properties"]["id"]}) for f in feats]
    )


def _ndvi(anio_siembra: int, cultivos: ee.Image) -> ee.Image:
    """NDVI de enero a marzo de la cosecha (llenado de granos), solo píxeles de cultivo y de buena calidad."""
    inicio = ee.Date.fromYMD(anio_siembra + 1, 1, 1)
    fin = ee.Date.fromYMD(anio_siembra + 1, 4, 1)

    def limpiar(img):
        buena = img.select("SummaryQA").lte(1)  # 0 = buena, 1 = marginal
        return img.select("NDVI").multiply(0.0001).updateMask(buena).updateMask(cultivos)

    col = ee.ImageCollection(MODIS).filterDate(inicio, fin).map(limpiar)
    return col.max().rename("ndvi_max").addBands(col.mean().rename("ndvi_media"))


def _lluvia(anio_siembra: int) -> ee.Image:
    """Lluvia acumulada de noviembre a marzo, en mm."""
    inicio = ee.Date.fromYMD(anio_siembra, 11, 1)
    fin = ee.Date.fromYMD(anio_siembra + 1, 4, 1)
    return ee.ImageCollection(CHIRPS).filterDate(inicio, fin).sum().rename("lluvia_mm")


def extraer(deptos: ee.FeatureCollection, anios: range) -> pd.DataFrame:
    """Una fila por departamento y campaña. Una llamada a Earth Engine por campaña."""
    cultivos = ee.Image(ee.ImageCollection(WORLDCOVER).first()).eq(40)
    filas = []
    for anio in anios:
        ndvi = _ndvi(anio, cultivos).reduceRegions(deptos, ee.Reducer.mean(), scale=250, tileScale=4)
        # Con una sola banda, reduceRegions llama "mean" a la salida: se renombra para no perderla
        lluvia = _lluvia(anio).reduceRegions(
            deptos, ee.Reducer.mean().setOutputs(["lluvia_mm"]), scale=5000
        )
        for fn, fl in zip(ndvi.getInfo()["features"], lluvia.getInfo()["features"]):
            p, q = fn["properties"], fl["properties"]
            filas.append(
                {
                    "departamento_id": p["departamento_id"],
                    "anio": anio,
                    "ndvi_max": p.get("ndvi_max"),
                    "ndvi_media": p.get("ndvi_media"),
                    "lluvia_mm": q.get("lluvia_mm"),
                }
            )
        print(f"campaña {anio}/{anio + 1}: ok")
    return pd.DataFrame(filas)
