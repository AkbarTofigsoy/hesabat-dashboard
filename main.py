import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ======================
# PAGE SETUP
# ======================
st.set_page_config(page_title="Müştəri Dashboard", layout="wide")

# ======================
# LOAD DATA
# ======================
BASE_DIR = os.path.dirname(__file__)
file_path = os.path.join(BASE_DIR, "hesabat.xlsx")

df = pd.read_excel(file_path)
df.columns = df.columns.str.strip()

df["Tarix"] = pd.to_datetime(df["Tarix"], dayfirst=True)
df["Ay"] = df["Tarix"].dt.to_period("M").astype(str)

# ======================
# SIDEBAR
# ======================
st.sidebar.title("📊 Filter Panel")

# Logo (old style)
logo_path = os.path.join(BASE_DIR, "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)

# ======================
# FILTER 1: MAĞAZA
# ======================
magaza = st.sidebar.multiselect(
    "Mağaza seç",
    df["Mağaza"].unique(),
    default=df["Mağaza"].unique()
)

# ======================
# FILTER 2: AY
# ======================
ay = st.sidebar.selectbox(
    "Ay seç",
    sorted(df["Ay"].unique())
)

# ======================
# FILTER 3: DATE RANGE
# ======================
min_date = df["Tarix"].min()
max_date = df["Tarix"].max()

date_range = st.sidebar.date_input(
    "Tarix aralığı seç",
    value=(min_date, max_date)
)

# ======================
# FILTER DATA
# ======================
filtered = df[
    (df["Mağaza"].isin(magaza)) &
    (df["Ay"] == ay) &
    (df["Tarix"] >= pd.to_datetime(date_range[0])) &
    (df["Tarix"] <= pd.to_datetime(date_range[1]))
]

# ======================
# HEADER
# ======================
st.title("📊 Müştəri Analitika Dashboard")
st.divider()

# ======================
# KPI CARDS
# ======================
c1, c2, c3 = st.columns(3)

c1.metric("👥 Ümumi Müştəri", int(filtered["Müştəri sayı"].sum()))
c2.metric("📊 Orta Günlük", round(filtered["Müştəri sayı"].mean(), 2))
c3.metric("🔥 Max Gün", int(filtered["Müştəri sayı"].max()))

st.divider()

# ======================
# DAILY TREND
# ======================
st.subheader("📈 Günlük Trend")

fig = px.line(
    filtered,
    x="Tarix",
    y="Müştəri sayı",
    color="Mağaza",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ======================
# STORE ANALYSIS
# ======================
st.subheader("🏪 Mağaza Performansı")

store = filtered.groupby("Mağaza")["Müştəri sayı"].sum().reset_index()

fig2 = px.bar(
    store,
    x="Mağaza",
    y="Müştəri sayı",
    text="Müştəri sayı",
    color="Mağaza"
)

st.plotly_chart(fig2, use_container_width=True)

# ======================
# TABLE VIEW
# ======================
st.subheader("📋 Detallı məlumat")

st.dataframe(filtered)

# ======================
# INSIGHT BOX
# ======================
if not filtered.empty:
    best = filtered.loc[filtered["Müştəri sayı"].idxmax()]

    msg = (
        f"📌 Ən güclü gün: {best['Tarix'].date()} | "
        f"{best['Mağaza']} | {best['Müştəri sayı']} müştəri"
    )

    st.success(msg)