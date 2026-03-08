"""
Cluster Asesor – Streamlit App
Correr con: streamlit run app.py
Datos: reemplazar data/cluster.csv con el nuevo reporte exportado desde Balanz
"""

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import sys
import datetime
from pathlib import Path

APP_DIR = Path(__file__).parent
sys.path.insert(0, str(APP_DIR))

PCT_NETO = 0.45  # Tu parte de las comisiones

st.set_page_config(page_title="Cluster Asesor · Balanz", page_icon="📊", layout="wide")

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
  [data-testid="stMetricLabel"] { color: #8b949e !important; font-size: 11px !important; font-weight: 600 !important; text-transform: uppercase; letter-spacing: .06em; }
  [data-testid="stMetricValue"] { color: #e6edf3 !important; font-size: 22px !important; font-weight: 700 !important; }
  [data-testid="stMetricDelta"] { font-size: 12px !important; }
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
  /* Dataframe */
  .stDataFrame { border-radius: 10px; overflow: hidden; }
</style>
""", unsafe_allow_html=True)

# ── DATOS ──────────────────────────────────────────────────────────────────────
DATA_PATH = APP_DIR / "data" / "cluster.xlsx"

@st.cache_data(ttl=60)
def load_data(path):
    return pd.read_excel(path)

def clean_df(df):
    nums = [
        "AUM en Dolares","Bolsa Arg","Fondos Arg","pesos","mep","cable",
        "Comision 90d","Comision 180","Comision 1y",
        "Comis. Boletos1y","Comis. Fondos1y","Comis. Otros1y",
        "Comis. Boletos90d","Comis. Fondos90d",
        "$ Disponibles","MEP Disponibles","activo","Activo ult. 12 meses",
    ]
    for c in nums:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
    for c in ["Fecha de Alta","primerfondeo"]:
        if c in df.columns:
            df[c] = pd.to_datetime(df[c], errors="coerce")
    # Mes corriente estimado = comisión 90d / 3
    df["Comision mes"] = df["Comision 90d"] / 3
    # Netos
    df["Neto 1y"]  = df["Comision 1y"]  * PCT_NETO
    df["Neto 90d"] = df["Comision 90d"] * PCT_NETO
    df["Neto mes"] = df["Comision mes"] * PCT_NETO
    return df

def fmt_usd(v): return f"USD {v:,.0f}"
def fmt_k(v):
    if abs(v) >= 1_000_000: return f"USD {v/1_000_000:.1f}M"
    if abs(v) >= 1_000:     return f"USD {v/1_000:.0f}K"
    return f"USD {v:.0f}"
def fmt_pct(v): return f"{v:.1f}%"

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
        st.error("No se encontró `data/cluster.xlsx`.")
        st.stop()

    if st.button("🔄 Recargar datos", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    df_raw = load_data(DATA_PATH)
    df = clean_df(df_raw)

    mtime = DATA_PATH.stat().st_mtime
    ultima_act = datetime.datetime.fromtimestamp(mtime).strftime("%d/%m/%Y %H:%M")
    st.success(f"✅ {len(df)} cuentas cargadas")
    st.caption(f"Actualizado: {ultima_act}")

    st.markdown("---")
    st.markdown("### Filtros")
    estado_filter  = st.radio("Estado", ["Todas","Activas","Inactivas"], index=1)
    aranceles      = ["Todos"] + sorted(df["arancel"].dropna().unique().tolist()) if "arancel" in df.columns else ["Todos"]
    arancel_filter = st.selectbox("Arancel", aranceles)
    aum_max        = max(int(df["AUM en Dolares"].max()), 1000)
    aum_min        = st.slider("AUM mínimo (USD)", 0, aum_max, 0, step=100, format="$%d")

    st.markdown("---")
    pct_display = st.slider("Tu % de comisión", 10, 100, 45, step=1, format="%d%%")
    pct_factor  = pct_display / 100

    st.markdown("---")
    st.markdown("**💡 Para actualizar:** reemplazá `data/cluster.xlsx` en el repo.")

# ── FILTROS ────────────────────────────────────────────────────────────────────
fdf = df.copy()
if estado_filter == "Activas":   fdf = fdf[fdf["activo"] == 1]
if estado_filter == "Inactivas": fdf = fdf[fdf["activo"] == 0]
if arancel_filter != "Todos":    fdf = fdf[fdf["arancel"] == arancel_filter]
fdf = fdf[fdf["AUM en Dolares"] >= aum_min]

# Recalcular netos con el slider
fdf = fdf.copy()
fdf["Neto 1y"]  = fdf["Comision 1y"]  * pct_factor
fdf["Neto 90d"] = fdf["Comision 90d"] * pct_factor
fdf["Neto mes"] = fdf["Comision mes"] * pct_factor

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

# ── KPIs CARTERA ───────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Cartera</div>', unsafe_allow_html=True)

total_aum   = fdf["AUM en Dolares"].sum()
n_total     = len(fdf)
n_activas   = int(fdf["activo"].sum())
pct_act     = (n_activas / n_total * 100) if n_total else 0
ticket_prom = total_aum / n_activas if n_activas else 0
pct_fondos  = (fdf["Fondos Arg"].sum() / total_aum * 100) if total_aum else 0

c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("AUM Total",       fmt_k(total_aum))
c2.metric("Cuentas",         n_total, f"{n_activas} activas")
c3.metric("Tasa actividad",  fmt_pct(pct_act))
c4.metric("Ticket promedio", fmt_k(ticket_prom))
c5.metric("Peso fondos",     fmt_pct(pct_fondos))

# ── KPIs COMISIONES ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Comisiones</div>', unsafe_allow_html=True)

bruto_mes = fdf["Comision mes"].sum()
neto_mes  = bruto_mes * pct_factor
bruto_90  = fdf["Comision 90d"].sum()
neto_90   = bruto_90 * pct_factor
bruto_1y  = fdf["Comision 1y"].sum()
neto_1y   = bruto_1y * pct_factor

# Mes corriente
st.markdown("**🗓 Mes corriente** *(estimado = 90d ÷ 3)*")
m1,m2,m3 = st.columns(3)
m1.metric("Bruto mes",                    fmt_usd(bruto_mes))
m2.metric(f"Tu parte ({pct_display}%)",   fmt_usd(neto_mes))
m3.metric("Diferencia (Balanz se queda)", fmt_usd(bruto_mes - neto_mes))

st.markdown("**📅 Últimos 90 días**")
q1,q2,q3 = st.columns(3)
q1.metric("Bruto 90d",                    fmt_usd(bruto_90))
q2.metric(f"Tu parte ({pct_display}%)",   fmt_usd(neto_90))
q3.metric("Diferencia",                   fmt_usd(bruto_90 - neto_90))

st.markdown("**📆 Último año**")
y1,y2,y3 = st.columns(3)
y1.metric("Bruto 1 año",                  fmt_usd(bruto_1y))
y2.metric(f"Tu parte ({pct_display}%)",   fmt_usd(neto_1y))
y3.metric("Diferencia",                   fmt_usd(bruto_1y - neto_1y))

# ── RANKING COMISIONES POR CLIENTE ─────────────────────────────────────────────
st.markdown('<div class="section-title">Ranking de comisiones por cliente</div>', unsafe_allow_html=True)

rank = fdf[["comitente","idcuenta","arancel","AUM en Dolares",
            "Comision mes","Neto mes",
            "Comision 90d","Neto 90d",
            "Comision 1y","Neto 1y",
            "activo"]].copy()

rank = rank.sort_values("Comision 1y", ascending=False).reset_index(drop=True)
rank.index += 1

# Formato para mostrar
rank_display = rank.copy()
rank_display["Estado"]       = rank_display["activo"].map(lambda x: "✅" if x==1 else "❌")
rank_display["AUM"]          = rank_display["AUM en Dolares"].map(fmt_k)
rank_display["Bruto mes"]    = rank_display["Comision mes"].map(fmt_usd)
rank_display["Neto mes"]     = rank_display["Neto mes"].map(fmt_usd)
rank_display["Bruto 90d"]    = rank_display["Comision 90d"].map(fmt_usd)
rank_display["Neto 90d"]     = rank_display["Neto 90d"].map(fmt_usd)
rank_display["Bruto 1 año"]  = rank_display["Comision 1y"].map(fmt_usd)
rank_display["Neto 1 año"]   = rank_display["Neto 1y"].map(fmt_usd)

cols_show = ["Estado","comitente","idcuenta","arancel","AUM",
             "Bruto mes","Neto mes",
             "Bruto 90d","Neto 90d",
             "Bruto 1 año","Neto 1 año"]

st.dataframe(
    rank_display[cols_show].rename(columns={"comitente":"Comitente","idcuenta":"Cuenta","arancel":"Arancel"}),
    use_container_width=True,
    hide_index=False,
    height=500,
)

# ── COMPOSICIÓN AUM ────────────────────────────────────────────────────────────
st.markdown('<div class="section-title">Composición de cartera</div>', unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)

with col1:
    aum_data = {"Fondos Arg": fdf["Fondos Arg"].sum(), "Bolsa Arg": fdf["Bolsa Arg"].sum(),
                "MEP": fdf["mep"].sum(), "Cable": fdf["cable"].sum()}
    aum_data = {k: v for k, v in aum_data.items() if v > 0}
    fig_d = go.Figure(go.Pie(
        labels=list(aum_data.keys()), values=list(aum_data.values()),
        hole=0.6, marker_colors=["#1f6feb","#3fb950","#f78166","#ffa657"],
        textinfo="label+percent", textfont_size=12,
    ))
    fig_d.add_annotation(text=f"<b>{fmt_k(total_aum)}</b>", x=0.5, y=0.5,
                         showarrow=False, font=dict(size=13, color="#e6edf3"))
    fig_d.update_layout(title="AUM por tipo", showlegend=False, height=300, **PLOTLY)
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

# ── FOOTER ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.caption(f"📋 Mostrando {len(fdf)} de {len(df)} cuentas · Para actualizar: reemplazá data/cluster.xlsx en el repo · Mes corriente estimado como promedio de los últimos 90 días")
