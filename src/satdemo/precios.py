"""Precios internacionales mensuales de soja (Banco Mundial, Pink Sheet, CC-BY 4.0), en USD por tonelada.

FRED publica las mismas series del FMI, pero no responde a descargas automáticas: por eso el Banco Mundial.
"""
from pathlib import Path

import pandas as pd

URL_PINK_SHEET = (
    "https://thedocs.worldbank.org/en/doc/5d903e848db1d1b83e0ec8f744e55570-0350012021/related/"
    "CMO-Historical-Data-Monthly.xlsx"
)
COLUMNAS = {"Soybeans": "poroto", "Soybean meal": "harina", "Soybean oil": "aceite"}


def cargar(xlsx: Path) -> pd.DataFrame:
    """Una fila por mes, con poroto, harina y aceite de soja en USD/t."""
    df = pd.read_excel(xlsx, "Monthly Prices", header=None)
    encabezado = df.iloc[4].tolist()
    cols = {j: COLUMNAS[h] for j, h in enumerate(encabezado) if h in COLUMNAS}
    out = df.iloc[6:, [0, *cols]].rename(columns={0: "mes", **cols})
    out["fecha"] = pd.to_datetime(out["mes"].str.replace("M", "-") + "-01")
    out = out.drop(columns="mes").set_index("fecha").apply(pd.to_numeric, errors="coerce")
    return out.dropna(how="all").reset_index()
