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

COMISION_PCTAJE = 0.45  # Tu parte de las comisiones

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
  .tag-bruto  { background:#1f6feb22; color:#58a6ff; border:1px solid #1f6feb55; padding:2px 8px; border-radius:20px; font-size:11px; font-weight:600; }
  .tag-neto   { background:#3fb95022; color:#3fb950; border:1px solid #3fb95055; padding:2px 8px; border-radius:20px; font-size:11px; font-weight:600; }
</style>
""", unsafe_allow_html=True)

# ── CARGA DE DATOS ─────────────────────────────────────────────────────────────
DATA_PATH = APP_DIR / "data" / "cluster.csv"

@st.cache_data(ttl=60)
def load_data(path: Path) -> pd.DataFrame:
    return pd.read_csv(path)

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
    # Columnas de comisión neta (tu 45%)
    for period in ["90d", "180", "1y"]:
        col = f"Comision {period}"
        if col in df.columns:
            df[f"Neto {period}"] = df[col] * COMISION_PCTAJE
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
    pct_display = st.slider("Tu % de comisión", min_value=10, max_value=100, value=45, step=1, format="%d%%")
    pct_factor = pct_display / 100

    st.markdown("---")
    st.markdown("**💡 Para actualizar datos:**")
    st.markdown("Reemplazá `data/cluster.csv` en el repo.")

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

total_aum    = fdf["AUM en Dolares"].sum()
n_total      = len(fdf)
n_activas    = int(fdf["activo"].sum())
pct_activas  = (n_activas / n_total * 100) if n_total else 0
com_1y_bruto = fdf["Comision 1y"].sum()
com_1y_neto  = com_1y_bruto * pct_factor
com_90d_bruto= fdf["Comision 90d"].sum()
com_90d_neto = com_90d_bruto * pct_factor
aum_fondos   = fdf["Fondos Arg"].sum()
pct_fondos   = (aum_fondos / total_aum * 100) if total_aum else 0
ticket_prom  = total_aum / n_activas if n_activas else 0

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("AUM Total",         fmt_k(total_aum))
c2.metric("Cuentas",           n_total, f"{n_activas} activas")
c3.metric("Tasa actividad",    fmt_pct(pct_activas))
c4.metric("Ticket promedio",   fmt_k(ticket_prom))
c5.metric("Peso fondos",       fmt_pct(pct_fondos))
c6.metric("Tu % comisión",     fmt_pct(pct_factor * 100))

# KPIs de comisiones — bruto vs neto
st.markdown('<div class="section-title">Comisiones — Bruto vs Tu parte ({:.0f}%)</div>'.format(pct_factor*100), unsafe_allow_html=True)

k1,k2,k3,k4,k5,k6 = st.columns(6)
k1.metric("Bruto 90d",   fmt_usd(com_90d_bruto))
k2.metric(f"Neto 90d ({pct_display}%)",  fmt_usd(com_90d_neto))
k3.metric("Bruto 180d",  fmt_usd(fdf["Comision 180"].sum()))
k4.metric(f"Neto 180d ({pct_display}%)", fmt_usd(fdf["Comision 180"].sum() * pct_factor))
k5.metric("Bruto 1 año", fmt_usd(com_1y_bruto))
k6.metric(f"Neto 1 año ({pct_display}%)",fmt_usd(com_1y_neto))

# ── RANKING COMISIONES POR CUENTA ─────────────────────────────────────────────
st.markdown('<div class="section-title">Ranking de cuentas por comisión generada</div>', unsafe_allow_html=True)

col_rank, col_scatter = st.columns([1, 1])

with col_rank:
    rank = fdf[["idcuenta","comitente","AUM en Dolares","Comision 1y","arancel"]].copy()
    rank["Neto 1y"] = rank["Comision 1y"] * pct_factor
    rank = rank.sort_values("Comision 1y", ascending=False).reset_index(drop=True)
    rank.index += 1  # ranking desde 1

    fig_rank = go.Figure()
    fig_rank.add_trace(go.Bar(
        y=rank["comitente"].astype(str),
        x=rank["Comision 1y"],
        orientation="h",
        name="Bruto",
        marker_color="#1f6feb",
        text=[fmt_usd(v) for v in rank["Comision 1y"]],
        textposition="outside",
        textfont=dict(size=10, color="#8b949e"),
    ))
    fig_rank.add_trace(go.Bar(
        y=rank["comitente"].astype(str),
        x=rank["Neto 1y"],
        orientation="h",
        name=f"Tu parte ({pct_display}%)",
        marker_color="#3fb950",
        text=[fmt_usd(v) for v in rank["Neto 1y"]],
        textposition="outside",
        textfont=dict(size=10, color="#8b949e"),
    ))
    fig_rank.update_layout(
        title="Comisión 1 año por cuenta (bruto vs neto)",
        barmode="group",
        height=max(350, len(rank) * 28),
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        **PLOTLY,
    )
    st.plotly_chart(fig_rank, use_container_width=True)

with col_scatter:
    # Scatter AUM vs Comisión — todos, incluyendo los de comisión 0
    fig_sc = px.scatter(
        fdf,
        x="AUM en Dolares",
        y="Comision 1y",
        color="arancel" if "arancel" in fdf.columns else None,
        size="AUM en Dolares",
        size_max=30,
        hover_data=["idcuenta","comitente","Comision 1y"],
        title="AUM vs Comisión 1 año (todas las cuentas)",
        color_discrete_sequence=["#1f6feb","#3fb950","#ffa657","#f78166"],
    )
    fig_sc.update_layout(height=450, legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1), **PLOTLY)
    st.plotly_chart(fig_sc, use_container_width=True)

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
    fig_d = go.Figure(go.Pie(
        labels=list(aum_data.keys()), values=list(aum_data.values()),
        hole=0.6, marker_colors=["#1f6feb","#3fb950","#f78166","#ffa657"],
        textinfo="label+percent", textfont_size=12,
    ))
    fig_d.add_annotation(text=f"<b>{fmt_k(total_aum)}</b>", x=0.5, y=0.5,
                         showarrow=False, font=dict(size=13, color="#e6edf3"))
    fig_d.update_layout(title="AUM por tipo de activo", showlegend=False, height=300, **PLOTLY)
    st.plotly_chart(fig_d, use_container_width=True)

with col2:
    if "arancel" in fdf.columns:
        ar = fdf.groupby("arancel")["AUM en Dolares"].sum().sort_values()
        fig_ar = go.Figure(go.Bar(
            x=ar.values, y=ar.index, orientation="h", marker_color="#1f6feb",
            text=[fmt_k(v) for v in ar.values], textposition="outside",
            textfont=dict(color="#8b949e", size=11),
        ))
        fig_ar.update_layout(title="AUM por arancel", height=300, **PLOTLY)
        st.plotly_chart(fig_ar, use_container_width=True)

with col3:
    if "arancel" in fdf.columns:
        cnt = fdf.groupby("arancel").size().sort_values()
        fig_cnt = go.Figure(go.Bar(
            x=cnt.values, y=cnt.index, orientation="h", marker_color="#3fb950",
            text=cnt.values, textposition="outside",
            textfont=dict(color="#8b949e", size=11),
        ))
        fig_cnt.update_layout(title="Cuentas por arancel", height=300, **PLOTLY)
        st.plotly_chart(fig_cnt, use_container_width=True)

# ── COMISIONES BRUTO VS NETO ───────────────────────────────────────────────────
st.markdown('<div class="section-title">Evolución de comisiones</div>', unsafe_allow_html=True)

col_a, col_b = st.columns(2)

with col_a:
    periodos      = ["90 días", "180 días", "1 año"]
    brutos        = [fdf["Comision 90d"].sum(), fdf["Comision 180"].sum(), fdf["Comision 1y"].sum()]
    netos         = [v * pct_factor for v in brutos]

    fig_com = go.Figure()
    fig_com.add_trace(go.Bar(
        x=periodos, y=brutos, name="Bruto",
        marker_color="#1f6feb",
        text=[fmt_usd(v) for v in brutos], textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    ))
    fig_com.add_trace(go.Bar(
        x=periodos, y=netos, name=f"Tu parte ({pct_display}%)",
        marker_color="#3fb950",
        text=[fmt_usd(v) for v in netos], textposition="outside",
        textfont=dict(color="#8b949e", size=11),
    ))
    fig_com.update_layout(
        title="Comisiones bruto vs neto por período",
        barmode="group", height=320,
        legend=dict(bgcolor="#161b22", bordercolor="#30363d", borderwidth=1),
        **PLOTLY,
    )
    st.plotly_chart(fig_com, use_container_width=True)

with col_b:
    com_mix = {
        "Boletos": fdf["Comis. Boletos1y"].sum(),
        "Fondos":  fdf["Comis. Fondos1y"].sum(),
        "Otros":   fdf["Comis. Otros1y"].sum(),
    }
    com_mix = {k: v for k, v in com_mix.items() if v > 0}
    if com_mix:
        fig_mix = go.Figure(go.Pie(
            labels=list(com_mix.keys()), values=list(com_mix.values()),
            hole=0.55, marker_colors=["#1f6feb","#3fb950","#ffa657"],
            textinfo="label+percent",
        ))
        fig_mix.add_annotation(
            text=f"<b>{fmt_usd(com_1y_bruto)}</b><br><span style='font-size:10px'>bruto</span>",
            x=0.5, y=0.5, showarrow=False, font=dict(size=12, color="#e6edf3"),
        )
        fig_mix.update_layout(title="Mix comisiones 1 año (bruto)", showlegend=False, height=320, **PLOTLY)
        st.plotly_chart(fig_mix, use_container_width=True)

# ── CRECIMIENTO HISTÓRICO ──────────────────────────────────────────────────────
if "primerfondeo" in fdf.columns:
    st.markdown('<div class="section-title">Crecimiento histórico</div>', unsafe_allow_html=True)
    ff = fdf.dropna(subset=["primerfondeo"]).copy()
    ff["año"] = ff["primerfondeo"].dt.year
    por_año = ff.groupby("año").agg(cuentas=("idcuenta","count"), aum=("AUM en Dolares","sum")).reset_index()

    col_e1, col_e2 = st.columns(2)
    with col_e1:
        fig_al = go.Figure(go.Bar(
            x=por_año["año"].astype(str), y=por_año["cuentas"],
            marker_color="#1f6feb", text=por_año["cuentas"], textposition="outside",
        ))
        fig_al.update_layout(title="Cuentas fondeadas por año", height=280, **PLOTLY)
        st.plotly_chart(fig_al, use_container_width=True)
    with col_e2:
        fig_au = go.Figure(go.Bar(
            x=por_año["año"].astype(str), y=por_año["aum"], marker_color="#3fb950",
            text=[fmt_k(v) for v in por_año["aum"]], textposition="outside",
            textfont=dict(size=10),
        ))
        fig_au.update_layout(title="AUM actual por cohorte de ingreso", height=280, **PLOTLY)
        st.plotly_chart(fig_au, use_container_width=True)

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
        "AUM en Dolares","Fondos Arg","Bolsa Arg","mep","cable",
        "Comision 1y","Neto 1y","Comision 90d","Neto 90d",
        "$ Disponibles","MEP Disponibles"]
show  = [c for c in show if c in fdf.columns]
tabla = fdf[show].copy()
tabla["activo"] = tabla["activo"].map(lambda x: "✅ Activa" if x==1 else "❌ Inactiva")
for col in ["AUM en Dolares","Fondos Arg","Bolsa Arg","mep","cable",
            "Comision 1y","Neto 1y","Comision 90d","Neto 90d"]:
    if col in tabla.columns:
        tabla[col] = tabla[col].map(lambda x: f"{x:,.0f}")
if "Fecha de Alta" in tabla.columns:
    tabla["Fecha de Alta"] = pd.to_datetime(tabla["Fecha de Alta"], errors="coerce").dt.strftime("%d/%m/%Y")

st.dataframe(tabla.sort_values("Comision 1y", ascending=False),
             use_container_width=True, hide_index=True, height=450)

st.markdown("---")
st.caption(f"📋 Mostrando {len(fdf)} de {len(df)} cuentas · Para actualizar: reemplazá `data/cluster.csv` en el repo")
