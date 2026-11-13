"""Rinde de soja por departamento y campaña (MAGyP, datos.gob.ar, CC-BY 4.0)."""
import urllib.request
from pathlib import Path

import pandas as pd

URL_SOJA = (
    "https://datos.magyp.gob.ar/dataset/8ae4865f-d2f2-45a2-9343-7a4a12728a90/resource/"
    "ba694aa3-99d2-4d7d-9936-60f88e36ad9a/download/soja-serie-1941-2024.csv"
)
URL_DEPARTAMENTOS = "https://infra.datos.gob.ar/georef/departamentos.geojson"


def bajar(url: str, destino: Path) -> Path:
    """Baja un archivo si no está en disco."""
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "satelites-datos-ia"})
        with urllib.request.urlopen(req, timeout=120) as r:
            destino.write_bytes(r.read())
    return destino


def cargar(ruta: Path, desde: int = 2000, hasta: int = 2024) -> pd.DataFrame:
    """Serie por departamento, con el código INDEC como texto de 5 dígitos.

    `anio` es el año de siembra: 2022 = campaña 2022/2023.
    """
    df = pd.read_csv(ruta, dtype={"departamento_id": str, "provincia_id": str})
    df["departamento_id"] = df["departamento_id"].str.zfill(5)
    df = df[(df["anio"] >= desde) & (df["anio"] <= hasta)]
    # Los códigos que terminan en 000 son totales provinciales sin departamento
    df = df[~df["departamento_id"].str.endswith("000")]
    return df[df["rendimiento_kgxha"] > 0]


def principales(df: pd.DataFrame, n: int = 100) -> pd.DataFrame:
    """Los n departamentos con más superficie sembrada, entre los que tienen dato en todas las campañas."""
    campanias = df["anio"].nunique()
    completos = df.groupby("departamento_id")["anio"].nunique()
    completos = completos[completos == campanias].index
    sup = (
        df[df["departamento_id"].isin(completos)]
        .groupby("departamento_id")["superficie_sembrada_ha"]
        .mean()
        .nlargest(n)
    )
    return df[df["departamento_id"].isin(sup.index)].copy()
