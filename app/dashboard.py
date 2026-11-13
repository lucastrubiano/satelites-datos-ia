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

# --- Mapa vivo: línea de tiempo + mapa que sigue al slider ----------------------------
with tab_vivo:
    st.markdown(
        "**Cómo se usa:** arriba, el verdor de toda la zona cada 16 días, comparado con lo normal para esa fecha. "
        "Cuando veas un pozo (sequía), mové el slider hasta ahí y mirá abajo qué departamentos estaban en rojo."
    )
    fechas = list(zona["fecha"].dt.date)
    por_defecto = min(fechas, key=lambda f: abs(pd.Timestamp(f) - pd.Timestamp("2023-02-02")))
    fecha = st.select_slider("Fecha de la imagen", options=fechas, value=por_defecto, format_func=lambda f: f.strftime("%d-%m-%Y"))

    fig = go.Figure()
    fig.add_scatter(x=zona["fecha"], y=zona["anom"], mode="lines", line=dict(color="#1a9850", width=1.5),
                    fill="tozeroy", fillcolor="rgba(26,152,80,.15)", name="anomalía de NDVI (zona)")
    seco = zona["anom"].where(zona["anom"] < 0)
    fig.add_scatter(x=zona["fecha"], y=seco, mode="lines", line=dict(color="#d73027", width=1.5),
                    fill="tozeroy", fillcolor="rgba(215,48,39,.25)", name="más seco que lo normal")
    fig.add_vline(x=pd.Timestamp(fecha), line=dict(color=NARANJA, width=3))
    for x, txt in (("2009-01-15", "sequía 2008/09"), ("2023-01-15", "sequía 2022/23")):
        fig.add_annotation(x=x, y=zona["anom"].min(), text=txt, showarrow=False, yshift=-12, font=dict(color="#d73027"))
    fig.update_layout(height=260, margin=dict(l=0, r=0, t=10, b=0), showlegend=False, hovermode="x unified",
                      yaxis_title="NDVI vs. normal")
    st.plotly_chart(fig, width="stretch")

    d = serie[serie["fecha"].dt.date == fecha].merge(
        panel[["departamento_id", "departamento", "provincia"]].drop_duplicates(), on="departamento_id"
    )
    izq, der = st.columns([3, 2])
    fig = px.choropleth_map(
        d, geojson=geo, locations="departamento_id", featureidkey="properties.id", opacity=0.8, color="anom",
        color_continuous_scale="RdYlGn", range_color=(-0.2, 0.2), hover_name="departamento",
        hover_data={"provincia": True, "ndvi": ":.3f", "ndvi_normal": ":.3f", "anom": ":+.3f", "departamento_id": False},
        labels={"anom": "NDVI vs. normal"},
    )
    fig.update_layout(**MAPA)
    fig.update_layout(height=560, margin=dict(l=0, r=0, t=30, b=0), title=f"Imagen del {fecha:%d-%m-%Y}")
    izq.plotly_chart(fig, width="stretch")

    camp = int(fecha.year - (fecha.month < 7))
    der.subheader(f"La campaña {camp}/{str(camp + 1)[2:]} contra las demás")
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
    fig.add_vline(x=(pd.Timestamp(fecha) - pd.Timestamp(f"{camp}-07-01")).days, line=dict(color=NARANJA, dash="dash"))
    meses = pd.date_range(f"{camp}-07-01", periods=12, freq="MS")
    fig.update_layout(
        height=420, margin=dict(l=0, r=0, t=10, b=0), legend=dict(orientation="h", y=-0.15), yaxis_title="NDVI medio de la zona",
        xaxis=dict(tickvals=[(m - meses[0]).days for m in meses], ticktext=[m.strftime("%b") for m in meses]),
    )
    der.plotly_chart(fig, width="stretch")
    der.caption("La soja se siembra en nov-dic y llena granos en ene-mar: ahí se separa una sequía de un año normal.")

    with st.expander("▶ Reproducir la campaña completa como animación"):
        anim = serie[serie["campania"] == camp].copy()
        anim["imagen"] = anim["fecha"].dt.strftime("%Y-%m-%d")
        fig = px.choropleth_map(
            anim.sort_values("fecha"), geojson=geo, locations="departamento_id", featureidkey="properties.id", opacity=0.8,
            color="anom", animation_frame="imagen", color_continuous_scale="RdYlGn", range_color=(-0.2, 0.2),
            labels={"anom": "NDVI vs. normal"},
        )
        fig.update_layout(**MAPA)
        fig.update_layout(height=600, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, width="stretch")

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
    serie = panel.groupby("anio").agg(
        rinde=("rendimiento_kgxha", "mean"), ndvi=("ndvi_max", "mean"), lluvia=("lluvia_mm", "mean")
    ).reset_index()
    fig = go.Figure()
    fig.add_bar(x=serie["anio"], y=serie["lluvia"], name="lluvia nov-mar (mm)", marker_color="#c7dcef", yaxis="y3")
    fig.add_scatter(x=serie["anio"], y=serie["rinde"], name="rinde medio (kg/ha)", line=dict(color=NARANJA, width=3))
    fig.add_scatter(x=serie["anio"], y=serie["ndvi"], name="NDVI máx. medio", line=dict(color="#1a9850", width=2, dash="dot"), yaxis="y2")
    for a, txt in ((2008, "sequía 2008/09"), (2022, "sequía 2022/23")):
        fig.add_vrect(x0=a - 0.5, x1=a + 0.5, fillcolor="red", opacity=0.08, line_width=0, annotation_text=txt)
    fig.update_layout(
        height=480, hovermode="x unified", legend=dict(orientation="h", y=1.1),
        xaxis=dict(title="año de siembra"), yaxis=dict(title="rinde (kg/ha)"),
        yaxis2=dict(title="NDVI", overlaying="y", side="right"),
        yaxis3=dict(overlaying="y", visible=False),
    )
    st.plotly_chart(fig, width="stretch")
    st.markdown(
        "**Lectura:** el verdor de enero-marzo acompaña al rinde. Las dos sequías (2008/09 y 2022/23) se ven en "
        "las tres series antes de que se publique la cosecha. La tendencia del rinde es plana: el promedio "
        "histórico es un baseline razonable."
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
