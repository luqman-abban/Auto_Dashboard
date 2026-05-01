import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Toyota Experience Dashboard",
    layout="wide"
)

# ─────────────────────────────────────────────
# GOOGLE SHEETS DATA LOADER
# ─────────────────────────────────────────────
def load_data():
    SHEET_ID = "1zJfFeIWiy3zc3BwGmsPug3_dAwtUplI2"
    GID = "307200564"

    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"

    r = requests.get(url)
    r.raise_for_status()

    df = pd.read_csv(io.StringIO(r.text))
    return df


df = load_data()

# ─────────────────────────────────────────────
# TITLE
# ─────────────────────────────────────────────
st.title("🚗 Toyota Experience Dashboard")

# ─────────────────────────────────────────────
# KPI CALCULATIONS
# ─────────────────────────────────────────────
total = len(df)

def pct(col, val):
    s = df[col].dropna()
    return round(100 * (s == val).sum() / len(s), 1) if len(s) else 0

def avg(col):
    s = df[col].dropna().astype(str).str.extract(r"(\d+)").astype(float)
    return round(s.mean()[0], 2) if len(s) else 0


pct_likely = pct("Q2.4 - How likely are you to consider Toyota for your next vehicle?", "Very likely")
pct_best = pct("Q6.3 - Which brand had the best display at the show?", "Toyota")
pct_owners = pct("Q2.1 - Do you currently own or lease a Toyota?", "Yes")
overall_avg = avg("Q3.4_9 - Overall experience")

# ─────────────────────────────────────────────
# KPI ROW
# ─────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Responses", total)
col2.metric("Very Likely %", f"{pct_likely}%")
col3.metric("Toyota Best Display %", f"{pct_best}%")
col4.metric("Overall Avg Score", overall_avg)

st.divider()

# ─────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────

def vc(col, n=10):
    return df[col].value_counts().head(n).reset_index()


# Experience
exp_df = vc("Q3.4_9 - Overall experience")
exp_df.columns = ["Rating", "Count"]

fig1 = px.bar(exp_df, x="Rating", y="Count", title="Overall Experience")

# Intent
intent_df = vc("Q2.4 - How likely are you to consider Toyota for your next vehicle?")
intent_df.columns = ["Intent", "Count"]

fig2 = px.pie(intent_df, names="Intent", values="Count", title="Purchase Intent")

# Age
age_df = vc("Q8.1 - What is your age?", 10)
age_df.columns = ["Age Group", "Count"]

fig3 = px.bar(age_df, x="Age Group", y="Count", title="Age Distribution")

# ─────────────────────────────────────────────
# LAYOUT
# ─────────────────────────────────────────────
col1, col2 = st.columns(2)

with col1:
    st.plotly_chart(fig1, use_container_width=True)
    st.plotly_chart(fig3, use_container_width=True)

with col2:
    st.plotly_chart(fig2, use_container_width=True)

# ─────────────────────────────────────────────
# REFRESH BUTTON
# ─────────────────────────────────────────────
if st.button("🔄 Refresh Data"):
    st.rerun()
