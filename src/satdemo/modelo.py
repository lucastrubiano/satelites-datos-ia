"""Baseline, regresión lineal y gradient boosting, con validación hacia adelante en el tiempo.

Para predecir la campaña T se entrena solo con campañas anteriores a T. Las anomalías se calculan
contra el promedio de esas campañas de entrenamiento: usar el promedio de toda la serie filtraría el futuro.
"""
import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import LinearRegression

FEATURES = ["ndvi_max", "ndvi_media", "lluvia_mm"]


def _anomalias(train: pd.DataFrame, test: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Resta a cada departamento su promedio de entrenamiento: rinde y features."""
    cols = FEATURES + ["rendimiento_kgxha"]
    medias = train.groupby("departamento_id")[cols].mean().add_suffix("_prom")
    out = []
    for df in (train, test):
        df = df.join(medias, on="departamento_id")
        for c in cols:
            df[f"{c}_anom"] = df[c] - df[f"{c}_prom"]
        out.append(df)
    return out[0], out[1]


def validar(panel: pd.DataFrame, desde: int = 2008) -> pd.DataFrame:
    """Predicción por departamento para cada campaña desde `desde`, con los tres modelos."""
    X = [f"{c}_anom" for c in FEATURES]
    resultados = []
    for t in sorted(panel["anio"].unique()):
        if t < desde:
            continue
        train, test = _anomalias(panel[panel["anio"] < t], panel[panel["anio"] == t])
        train, test = train.dropna(subset=X), test.dropna(subset=X)
        y = train["rendimiento_kgxha_anom"]
        lineal = LinearRegression().fit(train[X], y)
        boosting = HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=300, random_state=0).fit(train[X], y)
        base = test["rendimiento_kgxha_prom"]
        resultados.append(
            test[["departamento_id", "anio", "rendimiento_kgxha"]].assign(
                pred_baseline=base,
                pred_lineal=base + lineal.predict(test[X]),
                pred_boosting=base + boosting.predict(test[X]),
            )
        )
    return pd.concat(resultados, ignore_index=True)


def errores(pred: pd.DataFrame) -> pd.DataFrame:
    """Error porcentual absoluto medio (MAPE) por campaña y modelo."""
    real = pred["rendimiento_kgxha"]
    tabla = pd.DataFrame({"anio": pred["anio"]})
    for m in ("baseline", "lineal", "boosting"):
        tabla[m] = (pred[f"pred_{m}"] - real).abs() / real * 100
    return tabla.groupby("anio").mean().round(1)


def resumen(err: pd.DataFrame) -> pd.Series:
    """Promedio de los errores por campaña: una sola cifra por modelo."""
    return err.mean().round(1).rename("MAPE %")


def correlacion(panel: pd.DataFrame) -> float:
    """Correlación entre anomalía de NDVI máximo y anomalía de rinde, sobre toda la serie (solo descriptiva)."""
    g = panel.groupby("departamento_id")
    a = panel["ndvi_max"] - g["ndvi_max"].transform("mean")
    b = panel["rendimiento_kgxha"] - g["rendimiento_kgxha"].transform("mean")
    return float(np.corrcoef(a, b)[0, 1])
