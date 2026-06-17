import streamlit as st
import pandas as pd
import sqlite3
import plotly.express as px

# ======================
# PAGE CONFIG
# ======================
st.set_page_config(page_title="Müştəri Dashboard", layout="wide")

# ======================
# DB
# ======================
conn = sqlite3.connect("data.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS sales (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    magaz TEXT,
    tarix TEXT,
    musteri INTEGER
)
""")
conn.commit()

# ======================
# SESSION STATE
# ======================
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user = None
    st.session_state.role = None

# ======================
# USERS
# ======================
USERS = {
    "admin": {"password": "1234", "role": "admin"},
    "user": {"password": "1111", "role": "viewer"}
}

# ======================
# LOGIN
# ======================
def login():
    st.title("🔐 Login")

    u = st.text_input("Username")
    p = st.text_input("Password", type="password")

    if st.button("Login"):
        if u in USERS and USERS[u]["password"] == p:
            st.session_state.logged_in = True
            st.session_state.user = u
            st.session_state.role = USERS[u]["role"]
            st.rerun()
        else:
            st.error("Yanlış login")

if not st.session_state.logged_in:
    login()
    st.stop()

# ======================
# SIDEBAR
# ======================
st.sidebar.success(f"👤 {st.session_state.user}")
st.sidebar.info(f"🔑 Role: {st.session_state.role}")

if st.sidebar.button("Logout"):
    st.session_state.logged_in = False
    st.rerun()

# ======================
# LOAD DATA
# ======================
df = pd.read_sql("SELECT * FROM sales", conn)

if df.empty:
    df = pd.DataFrame(columns=["ID", "Mağaza", "Tarix", "Müştəri sayı"])
else:
    df.columns = ["ID", "Mağaza", "Tarix", "Müştəri sayı"]
    df["Tarix"] = pd.to_datetime(df["Tarix"], errors="coerce")

# ======================
# ADMIN PANEL
# ======================
if st.session_state.role == "admin":

    st.sidebar.subheader("🛠 Admin Panel")

    tab1, tab2, tab3 = st.tabs(["➕ Əlavə et", "✏️ Redaktə et", "🗑 Sil"])

    # ADD
    with tab1:
        magaza = st.text_input("Mağaza")
        tarix = st.date_input("Tarix")
        musteri = st.number_input("Müştəri sayı", min_value=0)

        if st.button("Əlavə et"):
            c.execute(
                "INSERT INTO sales (magaz, tarix, musteri) VALUES (?, ?, ?)",
                (magaza, str(tarix), musteri)
            )
            conn.commit()
            st.success("Əlavə olundu!")
            st.rerun()

    # EDIT
    with tab2:
        if not df.empty:
            selected_id = st.selectbox("ID seç", df["ID"])
            row = df[df["ID"] == selected_id].iloc[0]

            new_magaza = st.text_input("Mağaza", row["Mağaza"])
            new_tarix = st.date_input("Tarix", pd.to_datetime(row["Tarix"]))
            new_musteri = st.number_input("Müştəri sayı", value=int(row["Müştəri sayı"]))

            if st.button("Yenilə"):
                c.execute("""
                    UPDATE sales
                    SET magaz = ?, tarix = ?, musteri = ?
                    WHERE id = ?
                """, (new_magaza, str(new_tarix), new_musteri, selected_id))

                conn.commit()
                st.success("Yeniləndi!")
                st.rerun()
        else:
            st.info("Data yoxdur")

    # DELETE
    with tab3:
        if not df.empty:
            del_id = st.selectbox("Sil ID", df["ID"])

            if st.button("Sil"):
                c.execute("DELETE FROM sales WHERE id = ?", (del_id,))
                conn.commit()
                st.warning("Silindi!")
                st.rerun()
        else:
            st.info("Data yoxdur")

# ======================
# FILTER
# ======================
st.sidebar.subheader("📊 Filter")

if not df.empty:
    magaza_filter = st.sidebar.multiselect(
        "Mağaza",
        df["Mağaza"].dropna().unique(),
        default=df["Mağaza"].dropna().unique()
    )
    filtered = df[df["Mağaza"].isin(magaza_filter)]
else:
    filtered = df

# ======================
# DASHBOARD SAFETY CHECK
# ======================
st.title("📊 Müştəri Dashboard")

if filtered.empty:
    st.warning("Data yoxdur")
    st.stop()

# ======================
# KPI (SAFE FIX)
# ======================
total = filtered["Müştəri sayı"].sum()
avg = filtered["Müştəri sayı"].mean()
max_val = filtered["Müştəri sayı"].max()

c1, c2, c3 = st.columns(3)

c1.metric("Ümumi", int(total) if pd.notna(total) else 0)
c2.metric("Orta", round(avg, 2) if pd.notna(avg) else 0)
c3.metric("Max", int(max_val) if pd.notna(max_val) else 0)

st.divider()

# ======================
# CHART
# ======================
fig = px.line(
    filtered,
    x="Tarix",
    y="Müştəri sayı",
    color="Mağaza",
    markers=True
)

st.plotly_chart(fig, use_container_width=True)

# ======================
# TABLE
# ======================
st.subheader("📋 Data")
st.dataframe(filtered, use_container_width=True)
