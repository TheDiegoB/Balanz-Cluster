"""
Cluster Asesor – Streamlit App
Correr con: streamlit run app.py
Datos: reemplazar data/cluster.csv con el nuevo reporte exportado desde Balanz
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import sys
import datetime
from pathlib import Path

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

# ── CONFIG ────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Cluster Asesor · Balanz",
    page_icon="📊",
    layout="wide",
)

# ── ESTILOS ───────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
  html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
  .stApp { background-color: #0d1117; color: #e6edf3; }
  [data-testid="stSidebar"] { background-color: #161b22; border-right: 1px solid #30363d; }
  [data-testid="stMetric"] {
    background: #161b22; border: 1px solid #30363d;
    border-radius: 10px; padding: 16px 20px;
  }
  [data-testid="stMetricLabel"]  { color: #8b949e !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: .06em; }
  [data-testid="stMetricValue"]  { color: #e6edf3 !important; font-size: 22px !important; font-weight: 700 !important; }
  [data-testid="stMetricDelta"]  { font-size: 12px !important; }
  .section-title {
    font-size: 11px; font-weight: 700; color: #8b949e;
    text-transform: uppercase; letter-spacing: .1em;
    margin: 28px 0 12px; border-bottom: 1px solid #21262d; padding-bottom: 8px;
  }
  .main-header {
    background: linear-gradient(135deg,#161b22 0%,#0d1117 100%);
    border: 1px solid #30363d; border-radius: 14px;
    padding: 22px 32px; margin-bottom: 20px;
  }
</style>
""", unsafe_allow_html=True)

# ── CARGA DE DATOS ─────────────────────────────────────────────────────────────
DATA_PATH = APP_DIR / "data" / "cluster.csv"

@st.cache_data(ttl=60)
def load_data(path: Path) -> pd.DataFrame:
    df = pd.read_csv(path)
    return df

def clean_df(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = [
        "AUM en Dolares", "Bolsa Arg", "Fondos Arg", "pesos", "mep", "cable",
        "Comision 90d", "Comision 180", "Comision 1y",
        "Comis. Boletos1y", "Comis. Fondos1y", "Comis. Otros1y",
        "$ Disponibles", "MEP Disponibles", "Cable Disponibles",
        "cv7000", "cv10000", "activo", "Activo ult. 12 meses",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    for col in ["Fecha de Alta", "primerfondeo"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df

def fmt_usd(v): return f"USD {v:,.0f}"
def fmt_pct(v): return f"{v:.1f}%"
def fmt_k(v):
    if v >= 1_000_000: return f"USD {v/1_000_000:.1f}M"
    if v >= 1_000:     return f"USD {v/1_000:.0f}K"
    return f"USD {v:.0f}"

PLOTLY = dict(
    paper_bgcolor="#0d1117", plot_bgcolor="#0d1117",
    font_color="#e6edf3", font_family="Inter",
    margin=dict(l=16, r=16, t=36, b=16),
    xaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d"),
    yaxis=dict(gridcolor="#21262d", zerolinecolor="#30363d"),
)

# ── SIDEBAR ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 Cluster Asesor")
    st.markdown("---")

    if not DATA_PATH.exists():
        st.error("No se encontró `data/cluster.csv`.\n\nSubí el archivo exportado de Balanz a esa ruta en el repo.")
        st.stop()

    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df_raw = load_data(DATA_PATH)
    df = clean_df(df_raw)

    mtime = DATA_PATH.stat().st_mtime
    ultima_act = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
    st.success(f"✅ {len(df)} cuentas cargadas")
    st.caption(f"Archivo actualizado: {ultima_act}")

    st.markdown("---")
    st.markdown("### Filtros")

    estado_filter = st.radio("Estado", ["Todas", "Activas", "Inactivas"], index=1)

    aranceles = ["Todos"] + sorted(df["arancel"].dropna().unique().tolist()) if "arancel" in df.columns else ["Todos"]
    arancel_filter = st.selectbox("Arancel", aranceles)

    aum_max = int(df["AUM en Dolares"].max()) if df["AUM en Dolares"].max() > 0 else 10000
    aum_min = st.slider("AUM mínimo (USD)", 0, aum_max, 0, step=100, format="$%d")

    st.markdown("---")
    st.markdown("**💡 Para actualizar datos:**")
    st.markdown("Exportá el cluster desde Balanz y reemplazá `data/cluster.csv` en el repo de GitHub.")

# ── FILTROS ────────────────────────────────────────────────────────────────────
fdf = df.copy()
if estado_filter == "Activas":   fdf = fdf[fdf["activo"] == 1]
if estado_filter == "Inactivas": fdf = fdf[fdf["activo"] == 0]
if arancel_filter != "Todos":    fdf = fdf[fdf["arancel"] == arancel_filter]
fdf = fdf[fdf["AUM en Dolares"] >= aum_min]

# ── HEADER ─────────────────────────────────────────────────────────────────────
equipo = df["equipo"].iloc[0] if "equipo" in df.columns and len(df) > 0 else "—"

st.markdown(f"""
<div class="main-header">
  <div style="display:flex;justify-content:space-between;align-items:center">
    <div>
      <div style="font-size:22px;font-weight:700;color:#e6edf3;margin-bottom:4px">📊 Dashboard Asesor</div>
      <div style="font-size:13px;color:#8b949e">Cluster de cuentas · Balanz Capital</div>
    </div>
    <div style="text-align:right">
      <div style="font-size:11px;color:#8b949e;text-transform:uppercase;letter-spacing:.05em">Equipo</div>
      <div style="font-size:14px;font-weight:600;color:#58a6ff">{equipo}</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── KPIs ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Resumen general</div>', unsafe_allow_html=True)

total_aum   = fdf["AUM en Dolares"].sum()
n_total     = len(fdf)
n_activas   = int(fdf["activo"].sum())
pct_activas = (n_activas / n_total * 100) if n_total else 0
com_1y      = fdf["Comision 1y"].sum()
com_90d     = fdf["Comision 90d"].sum()
aum_fondos  = fdf["Fondos Arg"].sum()
pct_fondos  = (aum_fondos / total_aum * 100) if total_aum else 0
ticket_prom = total_aum / n_activas if n_activas else 0

c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
c1.metric("AUM Total",        fmt_k(total_aum))
c2.metric("Cuentas",          n_total, f"{n_activas} activas")
c3.metric("Tasa actividad",   fmt_pct(pct_activas))
c4.metric("Ticket promedio",  fmt_k(ticket_prom))
c5.metric("Comisiones 1 año", fmt_usd(com_1y))
c6.metric("Comisiones 90d",   fmt_usd(com_90d))
c7.metric("Peso fondos",      fmt_pct(pct_fondos))

# ── COMPOSICIÓN AUM ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Composición de cartera</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    aum_data = {
        "Fondos Arg": fdf["Fondos Arg"].sum(),
        "Bolsa Arg":  fdf["Bolsa Arg"].sum(),
        "MEP":        fdf["mep"].sum(),
        "Cable":      fdf["cable"].sum(),
    }
    aum_data = {k: v for k, v in aum_data.items() if v > 0}
    fig = go.Figure(go.Pie(
        labels=list(aum_data.keys()), values=list(aum_data.values()),
        hole=0.6, marker_colors=["#1f6feb","#3fb950","#f78166","#ffa657"],
        textinfo="label+percent", textfont_size=12,
    ))
    fig.add_annotation(text=f"<b>{fmt_k(total_aum)}</b>", x=0.5, y=0.5,
                       showarrow=False, font=dict(size=13, color="#e6edf3"))
    fig.update_layout(title="AUM por tipo de activo", showlegend=False, height=300, **PLOTLY)
    st.plotly_chart(fig, use_container_width=True)

with col2:
    if "arancel" in fdf.columns:
        ar = fdf.groupby("arancel")["AUM en Dolares"].sum().sort_values()
        fig2 = go.Figure(go.Bar(
            x=ar.values, y=ar.index, orientation="h", marker_color="#1f6feb",
            text=[fmt_k(v) for v in ar.values], textposition="outside",
            textfont=dict(color="#8b949e", size=11),
        ))
        fig2.update_layout(title="AUM por arancel", height=300, **PLOTLY)
        st.plotly_chart(fig2, use_container_width=True)

with col3:
    if "arancel" in fdf.columns:
        cnt = fdf.groupby("arancel").size().sort_values()
        fig3 = go.Figure(go.Bar(
            x=cnt.values, y=cnt.index, orientation="h", marker_color="#3fb950",
            text=cnt.values, textposition="outside",
            textfont=dict(color="#8b949e", size=11),
        ))
        fig3.update_layout(title="Cuentas por arancel", height=300, **PLOTLY)
        st.plotly_chart(fig3, use_container_width=True)

# ── COMISIONES ─────────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Comisiones generadas</div>', unsafe_allow_html=True)

col_a, col_b, col_c = st.columns(3)

with col_a:
    periodos = ["90 días", "180 días", "1 año"]
    valores  = [fdf["Comision 90d"].sum(), fdf["Comision 180"].sum(), fdf["Comision 1y"].sum()]
    fig4 = go.Figure(go.Bar(
        x=periodos, y=valores,
        marker_color=["#3fb950","#1f6feb","#ffa657"],
        text=[fmt_usd(v) for v in valores], textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    ))
    fig4.update_layout(title="Comisiones por período", height=300, **PLOTLY)
    st.plotly_chart(fig4, use_container_width=True)

with col_b:
    com_mix = {
        "Boletos": fdf["Comis. Boletos1y"].sum(),
        "Fondos":  fdf["Comis. Fondos1y"].sum(),
        "Otros":   fdf["Comis. Otros1y"].sum(),
    }
    com_mix = {k: v for k, v in com_mix.items() if v > 0}
    if com_mix:
        fig5 = go.Figure(go.Pie(
            labels=list(com_mix.keys()), values=list(com_mix.values()),
            hole=0.55, marker_colors=["#1f6feb","#3fb950","#ffa657"],
            textinfo="label+percent",
        ))
        fig5.add_annotation(text=f"<b>{fmt_usd(com_1y)}</b>", x=0.5, y=0.5,
                            showarrow=False, font=dict(size=12, color="#e6edf3"))
        fig5.update_layout(title="Mix comisiones (1 año)", showlegend=False, height=300, **PLOTLY)
        st.plotly_chart(fig5, use_container_width=True)

with col_c:
    scatter_df = fdf[fdf["Comision 1y"] > 0].copy()
    if not scatter_df.empty:
        fig6 = px.scatter(
            scatter_df, x="AUM en Dolares", y="Comision 1y",
            color="arancel" if "arancel" in scatter_df.columns else None,
            hover_data=["idcuenta","comitente"],
            title="AUM vs Comisión por cuenta",
            color_discrete_sequence=["#1f6feb","#3fb950","#ffa657","#f78166"],
        )
        fig6.update_layout(height=300, **PLOTLY)
        st.plotly_chart(fig6, use_container_width=True)

# ── CRECIMIENTO HISTÓRICO ──────────────────────────────────────────────────────
if "primerfondeo" in fdf.columns:
    st.markdown('<div class="section-title">Crecimiento histórico</div>', unsafe_allow_html=True)

    ff = fdf.dropna(subset=["primerfondeo"]).copy()
    ff["año"] = ff["primerfondeo"].dt.year
    por_año = ff.groupby("año").agg(cuentas=("idcuenta","count"), aum=("AUM en Dolares","sum")).reset_index()

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        fig7 = go.Figure(go.Bar(
            x=por_año["año"].astype(str), y=por_año["cuentas"],
            marker_color="#1f6feb", text=por_año["cuentas"], textposition="outside",
        ))
        fig7.update_layout(title="Cuentas fondeadas por año", height=280, **PLOTLY)
        st.plotly_chart(fig7, use_container_width=True)

    with col_e2:
        fig8 = go.Figure(go.Bar(
            x=por_año["año"].astype(str), y=por_año["aum"], marker_color="#3fb950",
            text=[fmt_k(v) for v in por_año["aum"]], textposition="outside",
            textfont=dict(size=10),
        ))
        fig8.update_layout(title="AUM actual por cohorte de ingreso", height=280, **PLOTLY)
        st.plotly_chart(fig8, use_container_width=True)

# ── OPORTUNIDADES ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Oportunidades de acción</div>', unsafe_allow_html=True)

op1, op2, op3 = st.columns(3)

with op1:
    st.markdown("**💤 Inactivas con AUM > 0**")
    sub = fdf[(fdf["activo"]==0) & (fdf["AUM en Dolares"]>0)][
        ["idcuenta","comitente","AUM en Dolares","arancel"]
    ].sort_values("AUM en Dolares", ascending=False)
    if not sub.empty:
        sub2 = sub.copy(); sub2["AUM en Dolares"] = sub2["AUM en Dolares"].map(fmt_usd)
        st.dataframe(sub2, use_container_width=True, hide_index=True)
    else:
        st.info("Sin cuentas inactivas con saldo.")

with op2:
    st.markdown("**💰 Cash ARS disponible**")
    sub = fdf[fdf["$ Disponibles"]>500][
        ["idcuenta","comitente","$ Disponibles","AUM en Dolares"]
    ].sort_values("$ Disponibles", ascending=False).head(10)
    if not sub.empty:
        sub2 = sub.copy()
        sub2["$ Disponibles"]  = sub2["$ Disponibles"].map(lambda x: f"${x:,.0f}")
        sub2["AUM en Dolares"] = sub2["AUM en Dolares"].map(fmt_usd)
        st.dataframe(sub2, use_container_width=True, hide_index=True)
    else:
        st.info("Sin saldos disponibles significativos.")

with op3:
    st.markdown("**💵 MEP disponible**")
    sub = fdf[fdf["MEP Disponibles"]>100][
        ["idcuenta","comitente","MEP Disponibles","AUM en Dolares"]
    ].sort_values("MEP Disponibles", ascending=False).head(10)
    if not sub.empty:
        sub2 = sub.copy()
        sub2["MEP Disponibles"] = sub2["MEP Disponibles"].map(fmt_usd)
        sub2["AUM en Dolares"]  = sub2["AUM en Dolares"].map(fmt_usd)
        st.dataframe(sub2, use_container_width=True, hide_index=True)
    else:
        st.info("Sin MEP disponible significativo.")

# ── TABLA COMPLETA ─────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Detalle de cuentas</div>', unsafe_allow_html=True)

show = ["idcuenta","comitente","Fecha de Alta","activo","arancel",
        "AUM en Dolares","Bolsa Arg","Fondos Arg","pesos","mep","cable",
        "Comision 90d","Comision 180","Comision 1y",
        "$ Disponibles","MEP Disponibles"]
show  = [c for c in show if c in fdf.columns]
tabla = fdf[show].copy()
tabla["activo"] = tabla["activo"].map(lambda x: "✅ Activa" if x==1 else "❌ Inactiva")
for col in ["AUM en Dolares","Bolsa Arg","Fondos Arg","mep","cable",
            "Comision 90d","Comision 180","Comision 1y"]:
    if col in tabla.columns:
        tabla[col] = tabla[col].map(lambda x: f"{x:,.0f}")
if "Fecha de Alta" in tabla.columns:
    tabla["Fecha de Alta"] = pd.to_datetime(tabla["Fecha de Alta"], errors="coerce").dt.strftime("%d/%m/%Y")

st.dataframe(tabla.sort_values("AUM en Dolares", ascending=False),
             use_container_width=True, hide_index=True, height=420)

st.markdown("---")
st.caption(f"📋 Mostrando {len(fdf)} de {len(df)} cuentas · Para actualizar: reemplazá `data/cluster.csv` en el repo")
