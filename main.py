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

# ======================
# CLEAN DATA (CRITICAL FIX)
# ======================
df["Tarix"] = pd.to_datetime(df["Tarix"], errors="coerce", dayfirst=True)
df["Müştəri sayı"] = pd.to_numeric(df["Müştəri sayı"], errors="coerce").fillna(0)

df["Ay"] = df["Tarix"].dt.to_period("M").astype(str)
df["Həftə"] = df["Tarix"].dt.isocalendar().week

# ======================
# SIDEBAR
# ======================
st.sidebar.title("📊 Filter Panel")

# LOGO (TOP POSITION FIXED)
logo_path = os.path.join(BASE_DIR, "logo.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path)

# FILTERS
magaza = st.sidebar.multiselect(
    "Mağaza seç",
    df["Mağaza"].dropna().unique(),
    default=df["Mağaza"].dropna().unique()
)

ay = st.sidebar.selectbox(
    "Ay seç",
    sorted(df["Ay"].dropna().unique())
)

min_date = df["Tarix"].min()
max_date = df["Tarix"].max()

date_range = st.sidebar.date_input(
    "Tarix aralığı",
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
].copy()

# ======================
# HEADER
# ======================
st.title("📊 Müştəri Dashboard")
st.divider()

# ======================
# KPI (SAFE FIX - NO NaN CRASH)
# ======================
total = int(filtered["Müştəri sayı"].sum()) if not filtered.empty else 0
avg = float(filtered["Müştəri sayı"].mean()) if not filtered.empty else 0
max_val = int(filtered["Müştəri sayı"].max()) if not filtered.empty else 0

c1, c2, c3 = st.columns(3)
c1.metric("👥 Ümumi", total)
c2.metric("📊 Orta", round(avg, 2))
c3.metric("🔥 Max", max_val)

st.divider()

# ======================
# DAILY TREND
# ======================
st.subheader("📈 Günlük trend")

if not filtered.empty:
    fig = px.line(
        filtered,
        x="Tarix",
        y="Müştəri sayı",
        color="Mağaza",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)

# ======================
# PIVOT: AY + HƏFTƏ
# ======================
st.subheader("📊 Ay / Həftə Analizi (Pivot)")

pivot = filtered.pivot_table(
    index="Həftə",
    columns="Mağaza",
    values="Müştəri sayı",
    aggfunc="sum",
    fill_value=0
)

st.dataframe(pivot)

# ======================
# MONTH CHART
# ======================
st.subheader("📅 Ay üzrə ümumi trend")

month_data = df.groupby("Ay")["Müştəri sayı"].sum().reset_index()

fig2 = px.bar(
    month_data,
    x="Ay",
    y="Müştəri sayı",
    text="Müştəri sayı"
)

st.plotly_chart(fig2, use_container_width=True)

# ======================
# SUMMARY
# ======================
st.subheader("📌 Ümumi məlumat")

if not filtered.empty:
    best_day = filtered.loc[filtered["Müştəri sayı"].idxmax()]

    st.success(
        f"Ən güclü gün: {best_day['Tarix'].date()} | "
        f"{best_day['Mağaza']} | "
        f"{int(best_day['Müştəri sayı'])}"
    )
else:
    st.warning("Seçilmiş filter üzrə məlumat yoxdur")
