"""Dashboard de la demo: de la imagen satelital a la decisión.

Correr: uv run streamlit run app/dashboard.py
Solo lee archivos del repo: no necesita Earth Engine.
"""
import json
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    from satdemo import modelo, rinde
except ModuleNotFoundError:  # hosting que instala dependencias pero no el paquete (Streamlit Community Cloud)
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
    from satdemo import modelo, rinde

RAIZ = Path(__file__).resolve().parents[1]
DATOS, PIPELINE = RAIZ / "data", RAIZ / "salidas" / "pipeline"
NARANJA, GRIS = "#ec6600", "#9b958c"
# Mapa base oscuro de CARTO (gratis, sin clave), centrado en la zona sojera
MAPA = dict(map_style="carto-darkmatter", map_center=dict(lat=-32.6, lon=-61.6), map_zoom=4.6)

st.set_page_config(page_title="Soja desde el espacio", page_icon="🛰️", layout="wide")


@st.cache_data
def cargar():
    soja = rinde.principales(rinde.cargar(DATOS / "raw" / "soja-serie-1941-2024.csv"), 100)
    feats = pd.read_csv(DATOS / "processed" / "features.csv", dtype={"departamento_id": str})
    panel = soja.merge(feats, on=["departamento_id", "anio"])
    g = panel.groupby("departamento_id")
    for c in ("ndvi_max", "lluvia_mm", "rendimiento_kgxha"):
        panel[f"{c}_anom"] = panel[c] - g[c].transform("mean")
    panel["rinde_anom_pct"] = panel["rendimiento_kgxha_anom"] / g["rendimiento_kgxha"].transform("mean") * 100
    pred = modelo.validar(panel, desde=2008)
    pred["caida_esperada_pct"] = (pred["pred_lineal"] / pred["pred_baseline"] - 1) * 100
    pred["error_pct"] = (pred["pred_lineal"] - pred["rendimiento_kgxha"]) / pred["rendimiento_kgxha"] * 100
    geo = json.loads((DATOS / "raw" / "departamentos.geojson").read_text())
    ids = set(panel["departamento_id"])
    geo["features"] = [f for f in geo["features"] if f["properties"]["id"] in ids]
    pipe = json.loads((PIPELINE / "pipeline.json").read_text())
    return panel, pred, geo, pipe


@st.cache_data
def cargar_serie():
    """NDVI cada 16 días por depto, como anomalía contra el promedio del mismo depto en la misma fecha del año."""
    s = pd.read_csv(DATOS / "processed" / "ndvi_16dias.csv", dtype={"departamento_id": str}, parse_dates=["fecha"])
    s["dia"] = s["fecha"].dt.strftime("%m-%d")  # MODIS repite siempre los mismos días del año
    s["ndvi_normal"] = s.groupby(["departamento_id", "dia"])["ndvi"].transform("mean")
    s["anom"] = s["ndvi"] - s["ndvi_normal"]
    # Campaña de soja: de julio a junio (2022 = jul-2022 a jun-2023)
    s["campania"] = s["fecha"].dt.year - (s["fecha"].dt.month < 7)
    zona = s.groupby("fecha").agg(ndvi=("ndvi", "mean"), anom=("anom", "mean")).reset_index()
    return s, zona


panel, pred, geo, pipe = cargar()
serie, zona = cargar_serie()
err = modelo.errores(pred)
res = modelo.resumen(err)

# --- Encabezado y KPIs ---------------------------------------------------------------
st.title("🛰️ ¿Se ve la sequía desde el espacio antes de la cosecha?")
st.caption(
    "Soja en los 100 departamentos con más superficie sembrada · campañas 2000/01 a 2024/25 · "
    "NASA MODIS (NDVI), CHIRPS (lluvia), MAGyP (rinde) · demo educativa, no es un modelo para invertir"
)
p22 = pred[pred["anio"] == 2022]
k = st.columns(5)
k[0].metric("Filas analizadas", f"{len(panel):,}".replace(",", "."), "100 deptos × 25 campañas", delta_color="off")
k[1].metric("Correlación verdor ↔ rinde", f"{modelo.correlacion(panel):.2f}", "anomalías", delta_color="off")
k[2].metric("Error del baseline", f"{res['baseline']:.0f} %", "MAPE 2008-2024", delta_color="off")
k[3].metric("Error del modelo", f"{res['lineal']:.0f} %", f"{res['lineal'] - res['baseline']:.0f} pp", delta_color="inverse")
k[4].metric(
    "Sequía 2022/23: real vs. modelo",
    f"{p22['rendimiento_kgxha'].mean():,.0f} kg/ha".replace(",", "."),
    f"modelo {p22['pred_lineal'].mean():,.0f} · baseline {p22['pred_baseline'].mean():,.0f}".replace(",", "."),
    delta_color="off",
)

tab_vivo, tab_precio, tab_mapa, tab_tend, tab_img, tab_feat, tab_dec = st.tabs(
    ["⏱️ Mapa en el tiempo", "💲 De la sequía al precio", "🗺️ Mapa por campaña", "📈 Tendencias",
     "🧪 Cómo se tratan las imágenes", "🔢 Features", "🎯 Modelo y decisiones"]
)

# --- Mapa vivo: línea de tiempo + mapa, los dos con el mismo slider (corre en el navegador) ---
@st.cache_data
def precios_mensuales():
    p = pd.read_csv(DATOS / "processed" / "precios_soja.csv", parse_dates=["fecha"]).set_index("fecha")
    return p, (p.pct_change(12) * 100)


# Hitos con fuente (docs/clima-precios-argentina.md). Tipo: sequía en Argentina, o causa global que sube o baja el precio
HITOS = [
    ("2007-07-01", "2008-07-01", "boom de granos", "sube"),
    ("2008-07-01", "2008-12-01", "crisis financiera", "baja"),
    ("2008-12-01", "2009-04-01", "sequía AR 08/09", "sequia"),
    ("2011-12-01", "2012-04-01", "sequía AR 11/12", "sequia"),
    ("2012-06-01", "2013-01-01", "sequía EE. UU.", "sube"),
    ("2014-07-01", "2015-06-01", "cosechas récord EE. UU. y Sudamérica", "baja"),
    ("2017-12-01", "2018-04-01", "sequía AR 17/18", "sequia"),
    ("2020-08-01", "2021-02-01", "demanda China", "sube"),
    ("2022-11-01", "2023-04-01", "sequía AR 22/23", "sequia"),
    ("2024-04-01", "2024-12-01", "récord Brasil + AR se recupera", "baja"),
]
# Ciclo de la soja (docs/clima-precios-argentina.md, "Ciclo de la soja"): país, fase, tipo, inicio y fin (MM-DD)
CICLO = [
    ("Argentina", "siembra (1ra y 2da)", "siembra", "11-10", "01-10"),
    ("Argentina", "período crítico R3-R6", "critico", "01-15", "03-15"),
    ("Argentina", "cosecha", "cosecha", "03-20", "06-15"),
    ("Brasil", "siembra", "siembra", "09-01", "12-31"),
    ("Brasil", "cosecha", "cosecha", "01-01", "06-30"),
    ("EE. UU.", "siembra", "siembra", "05-01", "06-30"),
    ("EE. UU.", "período crítico", "critico", "08-01", "08-31"),
    ("EE. UU.", "cosecha", "cosecha", "09-01", "10-31"),
]
COLOR_FASE = {"siembra": "#1a9850", "critico": "#d73027", "cosecha": "#f2b33d"}
CRITICO_AR = next((ini, fin) for p, _, t, ini, fin in CICLO if p == "Argentina" and t == "critico")


def dia_campania(mmdd: str) -> int:
    """Días desde el 1 de julio, inicio de la campaña (año no bisiesto)."""
    m, d = map(int, mmdd.split("-"))
    return (pd.Timestamp(2001 + (m < 7), m, d) - pd.Timestamp(2001, 7, 1)).days


COLOR_HITO = {"sequia":("rgba(215,48,39,.20)", "#ff8a80", "🌵 "), "sube": ("rgba(78,168,222,.18)", "#4ea8de", "🌎↑ "),
              "baja": ("rgba(179,157,219,.18)", "#c5b3ef", "🌎↓ ")}


@st.cache_data
def cosecha_anual():
    """Producción de soja del país por campaña (todos los departamentos, MAGyP), ubicada en mayo: se cosecha en abril-mayo."""
    todo = rinde.cargar(DATOS / "raw" / "soja-serie-1941-2024.csv")
    t = (todo.groupby("anio")["produccion_tm"].sum() / 1e6).rename("produccion_mt").to_frame()
    t["fecha"] = pd.to_datetime((t.index + 1).astype(str) + "-05-01")
    return t


def campania_de(fecha: str) -> int:
    f = pd.Timestamp(fecha)
    return f.year - (f.month < 7)


@st.cache_data
def figura_tiempo(inicio: str, hitos: tuple, critico: tuple | None = None, atenuar: bool = True):
    """Tres paneles con el mismo eje de tiempo (verdor, volumen, precio) + mapa.

    El slider es de Plotly, no de Streamlit: mueve la línea y recolorea el mapa mientras se arrastra,
    sin ida y vuelta al servidor.
    """
    from plotly.subplots import make_subplots

    tabla = serie.pivot(index="fecha", columns="departamento_id", values="anom").sort_index()
    ids = list(tabla.columns)
    nombres = panel.drop_duplicates("departamento_id").set_index("departamento_id").loc[ids]
    texto = (nombres["departamento"] + ", " + nombres["provincia"]).tolist()
    fechas = list(tabla.index)
    k0 = min(range(len(fechas)), key=lambda i: abs(fechas[i] - pd.Timestamp(inicio)))
    sequias = [h for h in hitos if h[3] == "sequia"]
    globales = [h for h in hitos if h[3] != "sequia"]

    fig = make_subplots(
        rows=4, cols=1, row_heights=[0.15, 0.12, 0.15, 0.58], vertical_spacing=0.035, shared_xaxes=True,
        specs=[[{}], [{}], [{}], [{"type": "map"}]],
        subplot_titles=["Verdor: más verde o más seco de lo normal", "Volumen: soja cosechada en Argentina (millones de t)",
                        "Precio de la soja (USD/t)", ""],
    )
    # 1 · Verdor
    fig.add_scatter(x=zona["fecha"], y=zona["anom"], mode="lines", line=dict(color="#1a9850", width=1.2),
                    fill="tozeroy", fillcolor="rgba(26,152,80,.15)", name="más verde que lo normal", row=1, col=1)
    fig.add_scatter(x=zona["fecha"], y=zona["anom"].where(zona["anom"] < 0), mode="lines",
                    line=dict(color="#d73027", width=1.2), fill="tozeroy", fillcolor="rgba(215,48,39,.3)",
                    name="más seco que lo normal", row=1, col=1)
    # 2 · Volumen: una barra por campaña, en la cosecha; rojas las de sequía
    c = cosecha_anual()
    c = c[c["fecha"] >= zona["fecha"].min()]
    secas = {campania_de(ini) for ini, *_ in sequias}
    fig.add_bar(x=c["fecha"], y=c["produccion_mt"], width=200 * 86_400_000, showlegend=False,
                marker_color=["#d73027" if a in secas else "#4ea8de" for a in c.index],
                customdata=c.index.map(lambda a: f"{a}/{str(a + 1)[2:]}"),
                hovertemplate="campaña %{customdata}: %{y:.1f} Mt<extra></extra>", row=2, col=1)
    # 3 · Precio: una sola serie (harina); en gris tenue dentro de los períodos con otros factores globales
    nivel, _ = precios_mensuales()
    p = nivel["harina"][nivel.index >= zona["fecha"].min()]
    dentro = pd.Series(False, index=p.index)
    for ini, fin, *_ in globales:
        dentro |= (p.index >= ini) & (p.index <= fin)
    if atenuar:
        borde = dentro | dentro.shift(1, fill_value=False) | dentro.shift(-1, fill_value=False)
        fig.add_scatter(x=p.index, y=p.where(borde), mode="lines", line=dict(color="rgba(155,149,140,.55)", width=2),
                        name="precio con otros factores globales", hovertemplate="%{y:.0f} USD/t<extra></extra>", row=3, col=1)
        p = p.where(~dentro)
    fig.add_scatter(x=p.index, y=p, mode="lines", line=dict(color="#4ea8de", width=2.2), name="precio de la soja",
                    hovertemplate="%{y:.0f} USD/t<extra></extra>", row=3, col=1)

    fig.add_choroplethmap(geojson=geo, locations=ids, featureidkey="properties.id", z=tabla.iloc[k0].values,
                          colorscale="RdYlGn", zmin=-0.2, zmax=0.2, marker_opacity=0.8, text=texto,
                          hovertemplate="%{text}<br>NDVI vs. normal: %{z:+.3f}<extra></extra>",
                          colorbar=dict(title="NDVI vs.<br>normal", len=0.45, y=0.27), row=4, col=1)
    i_mapa = len(fig.data) - 1

    # Formas: van en cada frame, porque un frame reemplaza todas las formas del layout
    arriba, abajo = fig.layout.yaxis.domain[1], fig.layout.yaxis3.domain[0]
    bandas = [  # sequías AR: cruzan los tres paneles
        dict(type="rect", x0=ini, x1=fin, xref="x", yref="paper", y0=abajo, y1=arriba, line_width=0, layer="below",
             fillcolor=COLOR_HITO["sequia"][0])
        for ini, fin, *_ in sequias
    ] + [  # otros factores globales: solo en el panel de precio
        dict(type="rect", x0=ini, x1=fin, xref="x3", yref="y3 domain", y0=0, y1=1, line_width=0, layer="below",
             fillcolor="rgba(155,149,140,.13)")
        for ini, fin, *_ in globales
    ]
    if critico:  # período crítico de cada campaña, sobre el verdor
        bandas += [
            dict(type="rect", x0=f"{a}-{critico[0]}", x1=f"{a}-{critico[1]}", xref="x", yref="y domain", y0=0, y1=1,
                 line_width=0, layer="below", fillcolor="rgba(242,179,61,.16)")
            for a in range(fechas[0].year, fechas[-1].year + 1)
        ]

    def linea(f):
        return bandas + [dict(type="line", x0=f, x1=f, xref="x", yref="paper", y0=abajo, y1=arriba,
                              line=dict(color=NARANJA, width=3))]

    fig.frames = [
        go.Frame(name=str(i), data=[go.Choroplethmap(z=tabla.iloc[i].values)], traces=[i_mapa],
                 layout=dict(shapes=linea(f)))
        for i, f in enumerate(fechas)
    ]
    fig.update_layout(
        shapes=linea(fechas[k0]), height=1180, margin=dict(l=0, r=0, t=70, b=130), hovermode="x unified",
        legend=dict(orientation="h", y=1.06), map=dict(style="carto-darkmatter", center=dict(lat=-32.6, lon=-61.6), zoom=4.6),
        sliders=[dict(
            active=k0, x=0.06, y=0, len=0.94, yanchor="top", pad=dict(t=30, b=0), currentvalue=dict(prefix="Imagen del ", xanchor="right", font=dict(color=NARANJA, size=16)),
            steps=[dict(method="animate", label=f.strftime("%d-%m-%Y"),
                        args=[[str(i)], dict(mode="immediate", frame=dict(duration=0, redraw=True), transition=dict(duration=0))])
                   for i, f in enumerate(fechas)],
        )],
        updatemenus=[dict(type="buttons", direction="left", x=0, y=0, xanchor="left", yanchor="top", pad=dict(t=40), showactive=False, buttons=[
            dict(label="▶", method="animate", args=[None, dict(frame=dict(duration=250, redraw=True), fromcurrent=True)]),
            dict(label="⏸", method="animate", args=[[None], dict(mode="immediate", frame=dict(duration=0, redraw=False))]),
        ])],
    )
    fig.update_annotations(font=dict(size=13), x=0, xanchor="left")  # títulos de los paneles, a la izquierda
    for ini, fin, rotulo, tipo in sequias:  # rótulo arriba de la barra roja, que queda baja
        a = campania_de(ini)
        if a in c.index:
            fig.add_annotation(x=c.loc[a, "fecha"], xref="x2", y=c.loc[a, "produccion_mt"], yref="y2", yanchor="bottom",
                               text=COLOR_HITO[tipo][2] + rotulo, showarrow=False, bgcolor="rgba(20,19,18,.75)",
                               font=dict(size=11, color=COLOR_HITO[tipo][1]))
    for n, (ini, fin, rotulo, tipo) in enumerate(globales):
        fig.add_annotation(x=pd.Timestamp(ini) + (pd.Timestamp(fin) - pd.Timestamp(ini)) / 2, xref="x3", y=1, yref="y3 domain",
                           yanchor="top", yshift=-14 if n % 2 else 0, text=("↑ " if tipo == "sube" else "↓ ") + rotulo,
                           showarrow=False, bgcolor="rgba(20,19,18,.75)", font=dict(size=10, color=GRIS))
    fig.update_yaxes(title_text="NDVI vs. normal", row=1, col=1)
    fig.update_yaxes(title_text="Mt", row=2, col=1)
    fig.update_yaxes(title_text="USD/t", row=3, col=1)
    fig.update_xaxes(showticklabels=True, row=3, col=1)
    return fig

with tab_vivo:
    st.markdown(
        "**Cómo se lee, de arriba abajo:** el verdor de la zona sojera cada 16 días (🟩 más verde, 🟥 más seco que lo normal "
        "para esa fecha) → cuánta soja se cosechó en el país → el precio. Las franjas 🌵 rojas son sequías en Argentina: "
        "cae el verdor, cae el volumen y el precio sube. En el panel de precio, las franjas grises marcan **otros factores "
        "globales** (crisis, cosechas de EE. UU., China) que también mueven el precio.  \n"
        "Arrastrá el slider: la línea naranja y el mapa se mueven juntos."
    )
    c1, c2 = st.columns(2)
    atenuar = c1.checkbox("Atenuar períodos con otros factores globales", value=True)
    marcar = c2.checkbox("Marcar el período crítico de la soja argentina en cada campaña (mediados de enero a mediados de marzo)")
    # Hitos y opciones van como parámetro: si cambian, la caché de Streamlit se invalida
    st.plotly_chart(figura_tiempo("2023-02-02", tuple(HITOS), CRITICO_AR if marcar else None, atenuar), width="stretch")
    st.caption(
        "Precio de la soja = **harina de soja**, lo que más exporta Argentina (Banco Mundial, Pink Sheet, USD/t, promedio "
        "mensual, hasta dic-2024). Volumen: producción de soja de todos los departamentos (MAGyP), una barra por campaña "
        "ubicada en mayo, cuando se cosecha; en rojo, las campañas con sequía."
        + (" Franjas amarillas: período crítico R3-R6 (formación y llenado de grano), 15-ene a 15-mar; fuente: BCR (GEA) "
           "y USDA, en `docs/clima-precios-argentina.md`." if marcar else "")
    )

    st.markdown("**Las cuatro sequías, sin y con otros factores a la vez**")
    cad = pd.read_csv(DATOS / "processed" / "cadena_precio.csv", index_col="anio")
    otro = {2008: "salida de la crisis financiera de 2008", 2011: "sequía también en Brasil; después, en EE. UU. (2012)",
            2017: "ninguno fuerte: el caso más limpio", 2022: "récord de Brasil: compensó para mayo"}
    s4 = cad.loc[list(otro)]
    st.dataframe(
        pd.DataFrame({
            "Campaña": [f"🌵 {a % 100:02d}/{(a + 1) % 100:02d}" for a in s4.index],
            "Verdor ene-mar vs. normal": s4["ndvi_anom"].map("{:+.1f} %".format).values,
            "Volumen vs. tendencia": s4["sorpresa_ar"].map("{:+.1f} %".format).values,
            "Precio nov → feb": s4["harina_nov_02"].map("{:+.1f} %".format).values,
            "Precio nov → may": s4["harina_nov_05"].map("{:+.1f} %".format).values,
            "Otro factor a la vez": list(otro.values()),
        }),
        hide_index=True, width="stretch",
    )
    st.caption(
        "Precio: harina de soja, del promedio de noviembre (siembra) al de febrero (sequía a la vista) y al de mayo (cosecha). "
        "Volumen: producción argentina contra su tendencia (USDA PSD). Detalle en la pestaña 💲 De la sequía al precio. "
        "En las cuatro el precio subió de noviembre a febrero; para mayo, en 2022/23 lo borró la cosecha récord de Brasil."
    )

    nivel, yoy = precios_mensuales()
    mensual = zona.set_index("fecha")["anom"].resample("MS").mean()
    c = cosecha_anual()
    verano = zona[zona["fecha"].dt.month.isin([1, 2, 3])]
    c["ndvi_ene_mar"] = verano.groupby(verano["fecha"].dt.year - 1)["anom"].mean()
    d = c.dropna()
    sin_tend = d["produccion_mt"] - d["produccion_mt"].rolling(5, center=True, min_periods=3).mean()
    m = st.columns(3)
    m[0].metric("Verdor ↔ volumen", f"{d['ndvi_ene_mar'].corr(sin_tend):+.2f}", "sin tendencia, por campaña", delta_color="off")
    m[1].metric("Verdor ↔ cambio % de volumen", f"{d['ndvi_ene_mar'].corr(d['produccion_mt'].pct_change()):+.2f}",
                "vs. campaña anterior", delta_color="off")
    m[2].metric("Volumen ↔ precio nov → feb", f"{cad['sorpresa_ar'].corr(cad['harina_nov_02']):+.2f}",
                f"{len(cad)} campañas", delta_color="off")
    st.caption(
        "El verdor de enero-marzo anticipa el volumen del país; cuando falta soja argentina, el precio de la harina sube "
        "mientras dura la sequía. La tendencia del volumen se descuenta con una media móvil centrada de 5 campañas: "
        "sirve para describir, no para predecir."
    )

    with st.expander("¿Hay meses más críticos? Relación verdor ↔ precio de la harina, mes por mes"):
        prox = pd.concat([mensual.rename("anom"), yoy["harina"].shift(-2).rename("harina_2m")], axis=1, sort=True).dropna()
        por_mes = prox.groupby(prox.index.month).apply(lambda g: g["anom"].corr(g["harina_2m"]))
        nombres_mes = ["ene", "feb", "mar", "abr", "may", "jun", "jul", "ago", "sep", "oct", "nov", "dic"]
        fig = go.Figure(go.Bar(x=nombres_mes, y=por_mes.values,
                               marker_color=[NARANJA if m in (1, 2, 3) else GRIS for m in por_mes.index]))
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0), yaxis_title="correlación")
        st.plotly_chart(fig, width="stretch")
        st.caption(
            "Anomalía de verdor de cada mes contra la variación interanual del precio de la harina 2 meses después; "
            "~25 años por mes, así que son señales débiles. Lo más fuerte en la temporada de la soja es **enero**, "
            "su período crítico. Junio-agosto también da negativo, pero en invierno no hay soja: ese verdor es trigo "
            "y pasturas. **Hitos del gráfico:** rojo = sequías en Argentina; gris en el panel de precio = otros factores globales (boom de granos "
            "2007-08, sequía de EE. UU. 2012, compras de China 2020-21). Fuentes en `docs/clima-precios-argentina.md`."
        )

    st.subheader("Una campaña contra las demás")
    camp = st.selectbox("Campaña", list(range(2024, 1999, -1)), index=2, format_func=lambda a: f"{a}/{str(a + 1)[2:]}")
    s = serie.assign(orden=(serie["fecha"] - pd.to_datetime(serie["campania"].astype(str) + "-07-01")).dt.days)
    curvas = s.groupby(["campania", "orden"])["ndvi"].mean().reset_index()
    otras = curvas[curvas["campania"] != camp].groupby("orden")["ndvi"]
    banda = pd.DataFrame({"p10": otras.quantile(0.1), "p50": otras.median(), "p90": otras.quantile(0.9)}).reset_index()
    esta = curvas[curvas["campania"] == camp]
    fig = go.Figure()
    fig.add_scatter(x=banda["orden"], y=banda["p90"], line=dict(width=0), showlegend=False, hoverinfo="skip")
    fig.add_scatter(x=banda["orden"], y=banda["p10"], line=dict(width=0), fill="tonexty",
                    fillcolor="rgba(155,149,140,.3)", name="años normales (10-90 %)")
    fig.add_scatter(x=banda["orden"], y=banda["p50"], line=dict(color=GRIS, dash="dot"), name="mediana")
    fig.add_scatter(x=esta["orden"], y=esta["ndvi"], line=dict(color=NARANJA, width=3), name=f"{camp}/{str(camp + 1)[2:]}")
    meses = pd.date_range(f"{camp}-07-01", periods=12, freq="MS")
    for pais, fase, tipo, ini, fin in CICLO:
        if pais == "Argentina":
            fig.add_vrect(x0=dia_campania(ini), x1=dia_campania(fin), fillcolor=COLOR_FASE[tipo], line_width=0, layer="below",
                          opacity=0.22 if tipo == "critico" else 0.09, annotation_text=f"{fase} AR",
                          annotation_position="top left", annotation_font=dict(size=11, color=COLOR_FASE[tipo]))
        elif pais == "Brasil" and tipo == "cosecha":  # tenue y abajo, para no tapar las bandas de Argentina
            fig.add_shape(type="rect", x0=dia_campania(ini), x1=dia_campania(fin), xref="x", yref="y domain", y0=0, y1=0.07,
                          fillcolor="rgba(78,168,222,.25)", line_width=0, layer="below")
            fig.add_annotation(x=dia_campania(ini), xref="x", y=0.035, yref="y domain", xanchor="left", showarrow=False,
                               text="cosecha Brasil", font=dict(size=10, color="#4ea8de"))
    fig.update_layout(
        height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.1), yaxis_title="NDVI medio de la zona",
        xaxis=dict(tickvals=[(mm - meses[0]).days for mm in meses], ticktext=[mm.strftime("%b") for mm in meses]),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "Bandas: siembra, período crítico (R3-R6: formación y llenado de grano) y cosecha en Argentina; abajo, en azul, la "
        "cosecha de Brasil. **En el período crítico se separa una sequía de un año normal**: el satélite lo ve en ene-mar, "
        "el dato oficial llega con la cosecha. Calendario: USDA (IPAD) y BCR, en `docs/clima-precios-argentina.md`."
    )

# --- Mapa ----------------------------------------------------------------------------
with tab_mapa:
    VARIABLES = {
        "Anomalía de verdor (NDVI máx. ene-mar)": ("ndvi_max_anom", "RdYlGn", (-0.12, 0.12)),
        "Anomalía de rinde (%)": ("rinde_anom_pct", "RdYlGn", (-60, 60)),
        "Anomalía de lluvia nov-mar (mm)": ("lluvia_mm_anom", "RdBu", (-250, 250)),
        "Rinde (kg/ha)": ("rendimiento_kgxha", "YlGn", (500, 4000)),
    }
    c1, c2 = st.columns([1, 2])
    anio = c1.select_slider(
        "Campaña", options=list(range(2000, 2025)), value=2022, format_func=lambda a: f"{a}/{str(a + 1)[2:]}"
    )
    var = c2.radio("Qué mostrar", list(VARIABLES), horizontal=True)
    col, escala, rango = VARIABLES[var]
    d = panel[panel["anio"] == anio]
    izq, der = st.columns([3, 2])
    fig = px.choropleth_map(
        d, geojson=geo, locations="departamento_id", featureidkey="properties.id", opacity=0.8, color=col,
        color_continuous_scale=escala, range_color=rango, hover_name="departamento",
        hover_data={"provincia": True, "rendimiento_kgxha": ":,.0f", "ndvi_max": ":.3f", "lluvia_mm": ":.0f", "departamento_id": False},
    )
    fig.update_layout(**MAPA)
    fig.update_layout(height=620, margin=dict(l=0, r=0, t=10, b=0))
    izq.plotly_chart(fig, width="stretch")
    der.subheader(f"Más afectados en {anio}/{str(anio + 1)[2:]}")
    der.dataframe(
        d.nsmallest(12, "rinde_anom_pct")[["departamento", "provincia", "rendimiento_kgxha", "rinde_anom_pct", "ndvi_max_anom"]]
        .rename(columns={"rendimiento_kgxha": "rinde", "rinde_anom_pct": "rinde vs. normal %", "ndvi_max_anom": "anom. NDVI"})
        .style.format({"rinde": "{:,.0f}", "rinde vs. normal %": "{:+.0f}", "anom. NDVI": "{:+.3f}"}),
        hide_index=True, width="stretch",
    )

# --- Tendencias ----------------------------------------------------------------------
with tab_tend:
    from plotly.subplots import make_subplots

    anual = panel.groupby("anio").agg(
        rinde=("rendimiento_kgxha", "mean"), ndvi=("ndvi_max", "mean"), lluvia=("lluvia_mm", "mean")
    )
    anom = anual - anual.mean()  # cada año contra lo normal de esa misma ventana del año
    anom["rinde_pct"] = anom["rinde"] / anual["rinde"].mean() * 100
    fig = make_subplots(rows=3, cols=1, shared_xaxes=True, vertical_spacing=0.06,
                        subplot_titles=("Rinde de soja vs. normal (%)", "Verdor ene-mar vs. normal (NDVI)",
                                        "Lluvia nov-mar vs. normal (mm)"))
    for fila, col, fmt in ((1, "rinde_pct", "{:+.0f} %"), (2, "ndvi", "{:+.3f}"), (3, "lluvia", "{:+.0f} mm")):
        v = anom[col]
        fig.add_bar(x=anom.index, y=v, marker_color=["#d73027" if x < 0 else "#1a9850" for x in v],
                    text=[fmt.format(x) for x in v], textposition="none",
                    hovertemplate="%{x}: %{text}<extra></extra>", showlegend=False, row=fila, col=1)
    for a, txt in ((2008, "sequía 2008/09"), (2011, "sequía 2011/12"), (2017, "sequía 2017/18"), (2022, "sequía 2022/23")):
        fig.add_vrect(x0=a - 0.5, x1=a + 0.5, fillcolor=NARANJA, opacity=0.12, line_width=0)
        fig.add_annotation(x=a, y=1.07, yref="paper", text=txt, showarrow=False, font=dict(color=NARANJA))
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=40, b=0), bargap=0.15)
    fig.update_xaxes(title_text="año de siembra (2022 = campaña 2022/23)", row=3, col=1)
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        "**Cómo leerlo:** cada barra es un año contra el promedio de esa misma ventana del año (verdor en ene-mar, "
        "lluvia en nov-mar), así la estacionalidad no confunde. **Rojo = por debajo de lo normal.** Cuando las tres "
        "filas se ponen rojas a la vez, es sequía: 2008/09, 2011/12, 2017/18 y 2022/23. El verdor y la lluvia se conocen en marzo; "
        "el rinde, meses después."
    )

# --- Imágenes: el embudo -------------------------------------------------------------
with tab_img:
    e = pipe["embudo"]
    st.subheader("De 53 millones de observaciones a 100 filas")
    st.caption("Campaña 2022/23 · enero a marzo de 2023 · píxeles de 250 m dentro de los 100 departamentos")
    def miles(n):
        return f"{n:,.0f}".replace(",", ".")

    etapas_n = [e["observaciones"], e["observaciones_buena_calidad"], e["observaciones_en_cultivo"]]
    izq, der = st.columns([3, 1])
    fig = go.Figure(go.Funnel(
        y=["Observaciones (píxel × escena)", "Con buena calidad (sin nubes)", "Sobre cultivo"],
        x=etapas_n, marker=dict(color=[GRIS, "#5ab4ac", "#1a9850"]),
        text=[f"{n / 1e6:.1f} M · {n / etapas_n[0]:.0%}".replace(".", ",", 1) for n in etapas_n], textinfo="text",
    ))
    fig.update_layout(height=300, margin=dict(l=0, r=0, t=10, b=0))
    izq.plotly_chart(fig, width="stretch")
    der.metric("Se reducen a", f"{e['filas_finales']} filas", "1 por departamento", delta_color="off")
    der.metric("Escenas MODIS", e["escenas"], "ene-mar 2023", delta_color="off")
    st.markdown(
        f"{e['escenas']} escenas × {miles(e['pixeles_zona'])} píxeles. Nada de esto se bajó: Earth Engine filtró, "
        "limpió y promedió en sus servidores y devolvió una tabla."
    )
    st.subheader("Las etapas, sobre la misma zona")
    cols = st.columns(3)
    for i, et in enumerate(pipe["etapas"]):
        with cols[i % 3]:
            st.image(str(PIPELINE / et["archivo"]), caption=f"{i + 1}. {et['titulo']}", width="stretch")
    st.info(
        "**Qué resaltar:** (2) el NDVI crudo trae nubes y bordes; (3) la máscara de calidad las saca; (4) sin la máscara "
        "de cultivo, pastizales y ciudades ensucian el promedio; (6) la anomalía es lo que el modelo usa: cada píxel "
        "contra su propio pasado."
    )

# --- Features ------------------------------------------------------------------------
with tab_feat:
    st.markdown(
        "| Feature | Qué mide | Cómo se calcula |\n|---|---|---|\n"
        "| `ndvi_max` | El pico de verdor del cultivo | Máximo de ene-mar, píxeles de cultivo y buena calidad, promedio del depto |\n"
        "| `ndvi_media` | Verdor sostenido | Media de ene-mar, mismo filtro |\n"
        "| `lluvia_mm` | Agua disponible | Lluvia acumulada nov-mar (CHIRPS) |\n"
        "| `*_anom` | Cuánto se aparta del normal de ese depto | Valor menos el promedio del departamento |"
    )
    c1, c2 = st.columns(2)
    fig = px.scatter(
        panel, x="ndvi_max_anom", y="rinde_anom_pct", color=panel["anio"].eq(2022).map({True: "2022/23", False: "otras"}),
        color_discrete_map={"2022/23": NARANJA, "otras": GRIS}, opacity=0.6, hover_name="departamento",
        labels={"ndvi_max_anom": "anomalía de NDVI", "rinde_anom_pct": "rinde vs. normal (%)", "color": "campaña"},
        title="Verdor vs. rinde: cada punto es un depto en una campaña",
    )
    c1.plotly_chart(fig, width="stretch")
    fig = px.scatter(
        panel, x="lluvia_mm_anom", y="rinde_anom_pct", color=panel["anio"].eq(2022).map({True: "2022/23", False: "otras"}),
        color_discrete_map={"2022/23": NARANJA, "otras": GRIS}, opacity=0.6, hover_name="departamento",
        labels={"lluvia_mm_anom": "anomalía de lluvia (mm)", "rinde_anom_pct": "rinde vs. normal (%)", "color": "campaña"},
        title="Lluvia vs. rinde",
    )
    c2.plotly_chart(fig, width="stretch")
    st.dataframe(
        panel[["anio", "provincia", "departamento", "rendimiento_kgxha", "ndvi_max", "ndvi_media", "lluvia_mm", "ndvi_max_anom", "rinde_anom_pct"]]
        .sort_values(["anio", "provincia", "departamento"]),
        hide_index=True, width="stretch", height=320,
    )
    st.download_button("Bajar el panel (CSV)", panel.to_csv(index=False), "panel_soja_satelite.csv", "text/csv")

# --- De la sequía al precio: la cadena eslabón por eslabón ---------------------------
with tab_precio:
    cad = pd.read_csv(DATOS / "processed" / "cadena_precio.csv", index_col="anio")
    seco = cad["ndvi_anom"] < -2  # campañas con verdor ene-mar claramente bajo lo normal
    st.markdown(
        "**La pregunta:** si el satélite ve la sequía en enero, ¿anticipa cuánta soja va a haber y hacia dónde va el precio? "
        "Se prueba eslabón por eslabón, una campaña por punto (2005/06 a 2023/24). "
        "Precio: **harina de soja**, porque Argentina es su primer exportador (≈ 40 % del comercio mundial, USDA). "
        "El poroto se forma en Chicago y casi no reacciona."
    )

    # Calendario: fases por país y las tres fechas de precio que usan los gráficos de abajo
    fig = go.Figure()
    for tipo, nombre in (("siembra", "siembra"), ("critico", "período crítico"), ("cosecha", "cosecha")):
        filas = [c for c in CICLO if c[2] == tipo]
        fig.add_bar(
            y=[c[0] for c in filas], base=[dia_campania(c[3]) for c in filas],
            x=[dia_campania(c[4]) - dia_campania(c[3]) for c in filas], orientation="h", name=nombre,
            marker_color=COLOR_FASE[tipo], text=[c[1] for c in filas], textposition="inside", insidetextanchor="middle",
            customdata=[f"{c[3][3:]}/{c[3][:2]} a {c[4][3:]}/{c[4][:2]}" for c in filas],
            hovertemplate="%{y} · %{text}<br>%{customdata}<extra></extra>",
        )
    for mmdd, rotulo in (("11-15", "nov · siembra AR: punto de partida"), ("02-15", "feb · sequía a la vista"),
                         ("05-15", "may · cosecha AR + BR")):
        fig.add_vline(x=dia_campania(mmdd), line=dict(color=NARANJA, width=2, dash="dash"))
        fig.add_annotation(x=dia_campania(mmdd), y=1, yref="paper", yanchor="bottom", showarrow=False, text=rotulo,
                           font=dict(color=NARANJA, size=12))
    meses = pd.date_range("2001-07-01", periods=12, freq="MS")
    fig.update_layout(
        barmode="overlay", height=260, margin=dict(l=0, r=0, t=40, b=0), legend=dict(orientation="h", y=-0.2),
        title=None, yaxis=dict(categoryorder="array", categoryarray=["EE. UU.", "Brasil", "Argentina"]),
        xaxis=dict(range=[0, 365], tickvals=[(mm - meses[0]).days for mm in meses],
                   ticktext=[mm.strftime("%b") for mm in meses]),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption(
        "**Por qué esas fechas.** El satélite ve la sequía argentina en enero-febrero, en pleno período crítico; el dato "
        "oficial de producción llega con la cosecha, en abril-mayo. Brasil cosecha desde enero, antes que Argentina: "
        "en mayo su cosecha ya se conoce y pesa en el precio. EE. UU. va a contramano (siembra may-jun, cosecha sep-oct). "
        "Precio: promedio mensual de nov, feb y may (Banco Mundial). Calendario: USDA (IPAD), BCR y Univ. de Missouri, "
        "en `docs/clima-precios-argentina.md`."
    )

    def eslabon(col, x, y, titulo, xt, yt):
        r = cad[x].corr(cad[y])
        fig = go.Figure()
        m, c0 = np.polyfit(cad[x], cad[y], 1)
        xs = [cad[x].min(), cad[x].max()]
        fig.add_scatter(x=xs, y=[m * v + c0 for v in xs], mode="lines", line=dict(color=GRIS, dash="dot"), showlegend=False, hoverinfo="skip")
        fig.add_scatter(
            x=cad[x], y=cad[y], mode="markers+text", text=[f"{a % 100:02d}/{(a + 1) % 100:02d}" for a in cad.index],
            textposition="top center", textfont=dict(size=10),
            marker=dict(size=11, color=["#d73027" if s else NARANJA for s in seco]), showlegend=False,
            hovertemplate="%{text}<br>x %{x:+.1f} %<br>y %{y:+.1f} %<extra></extra>",
        )
        fig.add_hline(y=0, line=dict(color=GRIS, width=0.5)); fig.add_vline(x=0, line=dict(color=GRIS, width=0.5))
        fig.update_layout(title=f"{titulo} · r = {r:+.2f}", xaxis_title=xt, yaxis_title=yt, height=420, margin=dict(t=60))
        col.plotly_chart(fig, width="stretch")

    c1, c2, c3 = st.columns(3)
    eslabon(c1, "ndvi_anom", "sorpresa_ar", "1 · Verdor → toneladas", "verdor ene-mar vs. normal (%)", "producción AR vs. tendencia (%)")
    eslabon(c2, "sorpresa_ar", "harina_nov_02", "2 · Toneladas AR → precio en plena sequía", "producción AR vs. tendencia (%)", "harina nov → feb (%)")
    eslabon(c3, "sorpresa_ar_br", "harina_nov_05", "3 · AR + Brasil → precio a la cosecha", "producción AR + BR vs. tendencia (%)", "harina nov → may (%)")

    k = st.columns(4)
    k[0].metric("Harina nov→feb en sequía", f"{cad.loc[seco, 'harina_nov_02'].mean():+.0f} %", f"{seco.sum()} campañas en rojo", delta_color="off")
    k[1].metric("Harina nov→feb el resto", f"{cad.loc[~seco, 'harina_nov_02'].mean():+.0f} %", f"{(~seco).sum()} campañas", delta_color="off")
    k[2].metric("Subió en sequía", f"{(cad.loc[seco, 'harina_nov_02'] > 0).sum()} de {seco.sum()}", delta_color="off")
    k[3].metric("Poroto nov→may vs. AR + BR", f"{cad['sorpresa_ar_br'].corr(cad['poroto_nov_05']):+.2f}", "más débil que la harina", delta_color="off")

    st.markdown(
        "**Cómo se lee:** "
        "1) el verdor anticipa la cosecha argentina (r ≈ +0,8), meses antes del dato oficial. "
        "2) Mientras dura la sequía, la harina sube cuando falta soja argentina (r ≈ −0,75). "
        "3) A la cosecha manda la oferta de Sudamérica: Brasil cosecha al mismo tiempo y puede compensar (r ≈ −0,84 sumando los dos).\n\n"
        "**2022/23 es el ejemplo:** Argentina −39 % contra su tendencia; la harina subió 17 % de noviembre a febrero. "
        "Pero Brasil tuvo récord (+12 %): para mayo la harina había vuelto al nivel de noviembre. "
        "Para anticipar el precio no alcanza con mirar Argentina: hay que mirar a los dos con el satélite.\n\n"
        "*Datos: verdor MODIS (este repo), producción USDA PSD, precios Banco Mundial (Pink Sheet). "
        "Son 19 campañas: es una correlación, no un modelo para operar.*"
    )

# --- Modelo y decisiones -------------------------------------------------------------
with tab_dec:
    c1, c2 = st.columns(2)
    fig = go.Figure()
    for m, color in (("baseline", GRIS), ("lineal", NARANJA), ("boosting", "#2166ac")):
        fig.add_scatter(x=err.index, y=err[m], name=m, line=dict(color=color, width=3 if m == "lineal" else 1.5))
    fig.update_layout(title="Error por campaña (MAPE %): entrenando solo con el pasado", height=420, yaxis_title="%")
    c1.plotly_chart(fig, width="stretch")
    anio_d = c2.selectbox("Campaña a evaluar", sorted(pred["anio"].unique(), reverse=True), index=2,
                          format_func=lambda a: f"{a}/{str(a + 1)[2:]}")
    pd_ = pred[pred["anio"] == anio_d].merge(panel[["departamento_id", "departamento"]].drop_duplicates(), on="departamento_id")
    fig = go.Figure()
    fig.add_scatter(x=pd_["rendimiento_kgxha"], y=pd_["pred_baseline"], mode="markers", name="baseline", marker=dict(color=GRIS), text=pd_["departamento"])
    fig.add_scatter(x=pd_["rendimiento_kgxha"], y=pd_["pred_lineal"], mode="markers", name="modelo con satélite", marker=dict(color=NARANJA), text=pd_["departamento"])
    fig.add_scatter(x=[0, 4500], y=[0, 4500], mode="lines", line=dict(color="black", width=0.6), showlegend=False)
    fig.update_layout(title="Predicho vs. real (cada punto, un depto)", xaxis_title="real (kg/ha)", yaxis_title="predicho (kg/ha)", height=420)
    c2.plotly_chart(fig, width="stretch")

    st.subheader("🚨 Alerta temprana: de la predicción a la acción")
    umbral = st.slider("Avisar si el modelo espera una caída mayor a (%)", 5, 60, 20)
    alertas = pd_[pd_["caida_esperada_pct"] <= -umbral].sort_values("caida_esperada_pct")
    a1, a2, a3 = st.columns(3)
    a1.metric("Departamentos en alerta", len(alertas))
    cayeron = (pd_["rendimiento_kgxha"] < pd_["pred_baseline"] * (1 - umbral / 100))
    acierto = (pd_["caida_esperada_pct"] <= -umbral) & cayeron
    a2.metric("De esos, cayeron de verdad", int(acierto.sum()))
    a3.metric("Caídas reales que no avisó", int((cayeron & ~(pd_["caida_esperada_pct"] <= -umbral)).sum()))
    st.dataframe(
        alertas[["departamento", "pred_baseline", "pred_lineal", "caida_esperada_pct", "rendimiento_kgxha"]]
        .rename(columns={"pred_baseline": "normal", "pred_lineal": "esperado", "caida_esperada_pct": "caída esperada %", "rendimiento_kgxha": "real"})
        .style.format({"normal": "{:,.0f}", "esperado": "{:,.0f}", "caída esperada %": "{:+.0f}", "real": "{:,.0f}"}),
        hide_index=True, width="stretch",
    )
    st.markdown(
        "**Qué decisiones habilita esta señal en marzo, antes de la cosecha:** un seguro agrícola que prioriza dónde "
        "tasar daños; un acopio o una exportadora que ajusta compras y logística; un banco que anticipa pedidos de "
        "refinanciación; un municipio que planifica la emergencia agropecuaria. "
        "*El modelo dice dónde mirar primero; no reemplaza la recorrida a campo.*"
    )
