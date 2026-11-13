"""Oferta mundial de soja (USDA PSD, dominio público) y su cruce con el verdor y el precio.

La cadena que se prueba: verdor de ene-mar → producción argentina → precio de la harina durante la campaña.
El precio no se forma solo con Argentina: Brasil cosecha al mismo tiempo, así que se mira la oferta de los dos.

Regenerar: uv run python -m satdemo.oferta  (baja ~4 MB a data/raw/psd/, que no se versiona)
"""
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

URL_PSD = "https://apps.fas.usda.gov/psdonline/downloads/psd_oilseeds_csv.zip"
PAISES = {"Argentina": "ar", "Brazil": "br", "United States": "us"}


def produccion(zip_psd: Path) -> pd.DataFrame:
    """Producción de soja por campaña (Mt): Argentina, Brasil, EE. UU. y el mundo.

    En el PSD, la campaña 2022 de Argentina es la que se cosecha en 2023 (22/23), igual que en MAGyP.
    """
    with zipfile.ZipFile(zip_psd) as z:
        psd = pd.read_csv(z.open(z.namelist()[0]))
    soja = psd[(psd["Commodity_Description"] == "Oilseed, Soybean") & (psd["Attribute_Description"] == "Production")]
    t = soja.pivot_table(index="Market_Year", columns="Country_Name", values="Value", aggfunc="sum") / 1000
    out = t[list(PAISES)].rename(columns=PAISES)
    out["mundo"] = t.sum(axis=1)
    return out.rename_axis("anio")


def sorpresa(s: pd.Series, ventana: int = 8) -> pd.Series:
    """Desvío contra la tendencia lineal de las campañas anteriores (sin mirar el futuro)."""
    esperado = {}
    for a in s.index:
        prev = s.loc[: a - 1].dropna().iloc[-ventana:]
        if len(prev) >= 5:
            esperado[a] = np.polyval(np.polyfit(prev.index, prev.values, 1), a)
    return s / pd.Series(esperado) - 1


def cadena(prod: pd.DataFrame, ndvi_zona: pd.Series, precios: pd.DataFrame) -> pd.DataFrame:
    """Una fila por campaña: anomalía de verdor, sorpresa de producción y cambio del precio en la campaña.

    Precio: de noviembre (siembra) a febrero (sequía a la vista, antes de cosechar) y a mayo (cosecha de Argentina y Brasil).
    """
    t = pd.DataFrame({
        "ndvi_anom": ndvi_zona - ndvi_zona.rolling(8, min_periods=5).mean().shift(1),
        "sorpresa_ar": sorpresa(prod["ar"]),
        "sorpresa_br": sorpresa(prod["br"]),
        "sorpresa_ar_br": sorpresa(prod["ar"] + prod["br"]),
    })
    for c in ("harina", "poroto"):
        for mes in ("02", "05"):
            t[f"{c}_nov_{mes}"] = [
                precios[c].get(pd.Timestamp(f"{a + 1}-{mes}-01"), np.nan) / precios[c].get(pd.Timestamp(f"{a}-11-01"), np.nan) - 1
                for a in t.index
            ]
    return (t * 100).dropna().round(1).rename_axis("anio")


if __name__ == "__main__":
    from urllib.request import urlretrieve

    raiz = Path(__file__).resolve().parents[2] / "data"
    destino = raiz / "raw" / "psd" / "psd_oilseeds_csv.zip"
    if not destino.exists():
        destino.parent.mkdir(parents=True, exist_ok=True)
        urlretrieve(URL_PSD, destino)
    feats = pd.read_csv(raiz / "processed" / "features.csv")
    precios = pd.read_csv(raiz / "processed" / "precios_soja.csv", parse_dates=["fecha"]).set_index("fecha")
    prod = produccion(destino)
    prod.loc[2000:].round(2).to_csv(raiz / "processed" / "oferta_soja.csv")
    out = cadena(prod, feats.groupby("anio")["ndvi_max"].mean(), precios)
    out.to_csv(raiz / "processed" / "cadena_precio.csv")
    print(out.corr().round(2))
