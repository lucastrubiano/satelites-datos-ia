"""Dashboard de la demo: de la imagen satelital a la decisión.

Correr: uv run streamlit run app/dashboard.py
Solo lee archivos del repo: no necesita Earth Engine.
"""
import json
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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

tab_vivo, tab_mapa, tab_tend, tab_img, tab_feat, tab_dec = st.tabs(
    ["⏱️ Mapa en el tiempo", "🗺️ Mapa por campaña", "📈 Tendencias", "🧪 Cómo se tratan las imágenes", "🔢 Features", "🎯 Modelo y decisiones"]
)

# --- Mapa vivo: línea de tiempo + mapa, los dos con el mismo slider (corre en el navegador) ---
@st.cache_data
def precios_mensuales():
    p = pd.read_csv(DATOS / "processed" / "precios_soja.csv", parse_dates=["fecha"]).set_index("fecha")
    return p, (p.pct_change(12) * 100)


# Hitos con fuente (docs/clima-precios-argentina.md): rojo = clima en Argentina, azul = causas globales
HITOS = [
    ("2007-07-01", "2008-07-01", "boom de granos", "global"),
    ("2008-11-01", "2009-04-01", "sequía AR 08/09", "clima AR"),
    ("2012-06-01", "2013-01-01", "sequía EE. UU.", "global"),
    ("2017-12-01", "2018-04-01", "sequía AR 17/18", "clima AR"),
    ("2020-08-01", "2021-02-01", "demanda China", "global"),
    ("2022-11-01", "2023-04-01", "sequía AR 22/23", "clima AR"),
]


@st.cache_data
def figura_tiempo(precio: str, modo: str, inicio: str):
    """Gráfico de líneas + mapa en una sola figura de Plotly.

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

    fig = make_subplots(rows=2, cols=1, row_heights=[0.38, 0.62], vertical_spacing=0.04,
                        specs=[[{"secondary_y": True}], [{"type": "map"}]])
    fig.add_scatter(x=zona["fecha"], y=zona["anom"], mode="lines", line=dict(color="#1a9850", width=1.2),
                    fill="tozeroy", fillcolor="rgba(26,152,80,.15)", name="verdor vs. normal", row=1, col=1)
    fig.add_scatter(x=zona["fecha"], y=zona["anom"].where(zona["anom"] < 0), mode="lines",
                    line=dict(color="#d73027", width=1.2), fill="tozeroy", fillcolor="rgba(215,48,39,.3)",
                    name="más seco que lo normal", row=1, col=1)
    if precio != "Ninguno":
        nivel, yoy = precios_mensuales()
        col = "harina" if precio.startswith("Harina") else "poroto"
        y = yoy[col] if modo.startswith("Variación") else nivel[col]
        y = y[y.index >= zona["fecha"].min()]
        fig.add_scatter(x=y.index, y=y, mode="lines", line=dict(color="#4ea8de", width=2),
                        name=f"precio {col} ({'var. interanual %' if modo.startswith('Variación') else 'USD/t'})",
                        row=1, col=1, secondary_y=True)
    fig.add_choroplethmap(geojson=geo, locations=ids, featureidkey="properties.id", z=tabla.iloc[k0].values,
                          colorscale="RdYlGn", zmin=-0.2, zmax=0.2, marker_opacity=0.8, text=texto,
                          hovertemplate="%{text}<br>NDVI vs. normal: %{z:+.3f}<extra></extra>",
                          colorbar=dict(title="NDVI vs.<br>normal", len=0.6, y=0.32), row=2, col=1)
    i_mapa = len(fig.data) - 1

    # Bandas de hitos: van en cada frame, porque un frame reemplaza todas las formas del layout
    bandas = [
        dict(type="rect", x0=ini, x1=fin, xref="x", yref="y domain", y0=0, y1=1, line_width=0, layer="below",
             fillcolor="rgba(215,48,39,.18)" if tipo == "clima AR" else "rgba(78,168,222,.18)")
        for ini, fin, _, tipo in HITOS
    ]

    def linea(f):
        return bandas + [dict(type="line", x0=f, x1=f, xref="x", yref="y domain", y0=0, y1=1, line=dict(color=NARANJA, width=3))]

    fig.frames = [
        go.Frame(name=str(i), data=[go.Choroplethmap(z=tabla.iloc[i].values)], traces=[i_mapa],
                 layout=dict(shapes=linea(f)))
        for i, f in enumerate(fechas)
    ]
    fig.update_layout(
        shapes=linea(fechas[k0]), height=980, margin=dict(l=0, r=0, t=60, b=110), hovermode="x unified",
        legend=dict(orientation="h", y=1.09), map=dict(style="carto-darkmatter", center=dict(lat=-32.6, lon=-61.6), zoom=4.6),
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
    for ini, fin, texto, tipo in HITOS:
        sequia = tipo == "clima AR"
        fig.add_annotation(x=pd.Timestamp(ini) + (pd.Timestamp(fin) - pd.Timestamp(ini)) / 2, xref="x",
                           y=0.0 if sequia else 1.0, yref="y domain", yanchor="top" if sequia else "bottom",
                           text=("🌵 " if sequia else "🌎 ") + texto, showarrow=False, bgcolor="rgba(20,19,18,.75)",
                           font=dict(size=12, color="#ff8a80" if sequia else "#4ea8de"))
    fig.update_yaxes(title_text="NDVI vs. normal", row=1, col=1, secondary_y=False)
    if precio != "Ninguno":
        fig.update_yaxes(title_text="precio", row=1, col=1, secondary_y=True, showgrid=False)
    return fig


with tab_vivo:
    st.markdown(
        "**Cómo se usa:** arriba, el verdor de toda la zona cada 16 días contra lo normal para esa fecha. "
        "Arrastrá el slider: la línea naranja y el mapa se mueven juntos. Los pozos rojos son sequías.  \n"
        "**Hitos:** 🌵 bandas rojas = sequías en Argentina (cae el verdor); 🌎 bandas azules = causas globales del "
        "precio (boom de granos 2007-08, sequía de EE. UU. 2012, compras de China 2020-21), con el verdor argentino normal."
    )
    c1, c2 = st.columns([3, 2])
    precio = c1.radio("Superponer precio internacional", ["Ninguno", "Harina de soja", "Poroto de soja"], index=1, horizontal=True)
    modo = c2.radio("Precio como", ["Variación interanual %", "USD/t"], horizontal=True)
    st.plotly_chart(figura_tiempo(precio, modo, "2023-02-02"), width="stretch")

    nivel, yoy = precios_mensuales()
    mensual = zona.set_index("fecha")["anom"].resample("MS").mean()
    cruce = pd.concat([mensual.rename("anom"), yoy], axis=1, sort=True).dropna()
    temporada = cruce[cruce.index.month.isin([1, 2, 3])]
    m = st.columns(4)
    m[0].metric("Correlación verdor ↔ harina", f"{cruce['anom'].corr(cruce['harina']):+.2f}", "todos los meses", delta_color="off")
    m[1].metric("Solo ene-mar", f"{temporada['anom'].corr(temporada['harina']):+.2f}", "harina", delta_color="off")
    m[2].metric("Correlación verdor ↔ poroto", f"{cruce['anom'].corr(cruce['poroto']):+.2f}", "todos los meses", delta_color="off")
    m[3].metric("Harina dic-2022 vs. dic-2021", f"{yoy.loc['2022-12-01', 'harina']:+.0f} %",
                f"poroto {yoy.loc['2022-12-01', 'poroto']:+.0f} %", delta_color="off")
    st.caption(
        "Precios: Banco Mundial, Pink Sheet (CC-BY 4.0), USD/t, hasta dic-2024. **Lectura honesta:** la correlación "
        "general es casi nula; el precio es global y Argentina es un jugador entre varios. En la temporada (ene-mar) "
        "la harina reacciona algo, con el signo esperable (menos verde, precio más alto), y en la sequía 2022/23 subió "
        "fuerte. El poroto, que se forma en Chicago, casi no acompaña."
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
            "y pasturas. **Hitos del gráfico:** rojo = clima en Argentina; azul = causas globales (boom de granos "
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
    fig.update_layout(
        height=380, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=1.1), yaxis_title="NDVI medio de la zona",
        xaxis=dict(tickvals=[(mm - meses[0]).days for mm in meses], ticktext=[mm.strftime("%b") for mm in meses]),
    )
    st.plotly_chart(fig, width="stretch")
    st.caption("La soja se siembra en nov-dic y llena granos en ene-mar: ahí se separa una sequía de un año normal.")

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
    for a, txt in ((2008, "sequía 2008/09"), (2017, "sequía 2017/18"), (2022, "sequía 2022/23")):
        fig.add_vrect(x0=a - 0.5, x1=a + 0.5, fillcolor=NARANJA, opacity=0.12, line_width=0)
        fig.add_annotation(x=a, y=1.07, yref="paper", text=txt, showarrow=False, font=dict(color=NARANJA))
    fig.update_layout(height=640, margin=dict(l=0, r=0, t=40, b=0), bargap=0.15)
    fig.update_xaxes(title_text="año de siembra (2022 = campaña 2022/23)", row=3, col=1)
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        "**Cómo leerlo:** cada barra es un año contra el promedio de esa misma ventana del año (verdor en ene-mar, "
        "lluvia en nov-mar), así la estacionalidad no confunde. **Rojo = por debajo de lo normal.** Cuando las tres "
        "filas se ponen rojas a la vez, es sequía: 2008/09, 2017/18 y 2022/23. El verdor y la lluvia se conocen en marzo; "
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
