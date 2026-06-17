import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import os
# ======================
# TEMP EXCEL → DB IMPORT (1 TIME ONLY)
# ======================
import pandas as pd
import sqlite3
import os

if not os.path.exists("data.db"):
    excel_file = "hesabat.xlsx"

    df = pd.read_excel(excel_file)
    df.columns = df.columns.str.strip()

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS sales (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        magaz TEXT,
        tarix TEXT,
        musteri INTEGER
    )
    """)

    for _, row in df.iterrows():
        c.execute("""
            INSERT INTO sales (magaz, tarix, musteri)
            VALUES (?, ?, ?)
        """, (
            row["Mağaza"],
            str(row["Tarix"]),
            int(row["Müştəri sayı"]) if pd.notna(row["Müştəri sayı"]) else 0
        ))

    conn.commit()
    conn.close()

    print("Excel → DB import tamamlandı!")
# ======================
# DATABASE SETUP
# ======================
conn = sqlite3.connect("users.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS users (
    username TEXT PRIMARY KEY,
    password TEXT,
    role TEXT
)
""")
conn.commit()

# ======================
# DEFAULT ADMIN (ilk açılış üçün)
# ======================
c.execute("SELECT * FROM users WHERE username='admin'")
if not c.fetchone():
    c.execute("INSERT INTO users VALUES ('admin','2211','admin')")
    conn.commit()

# ======================
# SESSION INIT
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None

# ======================
# LOGIN FUNCTION
# ======================
def login():
    st.title("🔐 Dashboard Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        c.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
        user = c.fetchone()

        if user:
            st.session_state.logged_in = True
            st.session_state.user = user[0]
            st.session_state.role = user[2]
            st.rerun()
        else:
            st.error("Yanlış login")

# ======================
# USER MANAGEMENT (ADMIN PANEL)
# ======================
def admin_panel():
    st.sidebar.subheader("👑 Admin Panel")

    new_user = st.sidebar.text_input("Yeni user")
    new_pass = st.sidebar.text_input("Password")
    new_role = st.sidebar.selectbox("Role", ["admin", "manager", "viewer"])

    if st.sidebar.button("➕ User yarat"):
        try:
            c.execute("INSERT INTO users VALUES (?,?,?)", (new_user, new_pass, new_role))
            conn.commit()
            st.sidebar.success("User yaradıldı")
        except:
            st.sidebar.error("User artıq var")

    st.sidebar.divider()

    st.sidebar.subheader("👥 Userlər")
    users = c.execute("SELECT username, role FROM users").fetchall()
    for u in users:
        st.sidebar.write(f"{u[0]} → {u[1]}")

# ======================
# LOGIN CHECK
# ======================
if not st.session_state.logged_in:
    login()
    st.stop()

# ======================
# LOGGED IN HEADER
# ======================
st.sidebar.success(f"👤 {st.session_state.user}")
st.sidebar.info(f"🔑 {st.session_state.role}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None
    st.rerun()

# ======================
# ADMIN ACCESS
# ======================
if st.session_state.role == "admin":
    admin_panel()

# ======================
# DASHBOARD CONTENT (SƏNİN KODUN BURADA OLACAQ)
# ======================

# Example lock by role
if st.session_state.role != "viewer":
    st.success("📈 Analitika bölməsi aktivdir")
else:
    st.warning("Siz yalnız baxış hüququna maliksiniz")
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
