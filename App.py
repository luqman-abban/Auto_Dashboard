import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import io
from collections import Counter

# ─────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Autoshow Experience Dashboard",
    layout="wide"
)

# ─────────────────────────────────────────────
# CUSTOM CSS — compact KPIs, clean layout
# ─────────────────────────────────────────────
st.markdown("""
<style>
    /* Compact KPI cards */
    [data-testid="metric-container"] {
        background: #f8f9fa;
        border: 1px solid #e9ecef;
        border-radius: 8px;
        padding: 8px 12px !important;
    }
    [data-testid="metric-container"] label {
        font-size: 11px !important;
        color: #6c757d !important;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        font-size: 20px !important;
        font-weight: 700 !important;
    }
    /* Section headers */
    .section-header {
        font-size: 13px;
        font-weight: 600;
        color: #495057;
        text-transform: uppercase;
        letter-spacing: 0.8px;
        margin: 0 0 8px 0;
        padding-bottom: 6px;
        border-bottom: 2px solid #dee2e6;
    }
    /* Logo area */
    .logo-area {
        display: flex;
        align-items: center;
        gap: 16px;
        margin-bottom: 12px;
    }
    /* Chart size control label */
    .size-label {
        font-size: 12px;
        color: #6c757d;
        margin-bottom: 2px;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# GOOGLE SHEETS DATA LOADER
# ─────────────────────────────────────────────
@st.cache_data(ttl=300)
def load_data():
    SHEET_ID = "1zJfFeIWiy3zc3BwGmsPug3_dAwtUplI2"
    GID = "307200564"
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid={GID}"
    r = requests.get(url)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    return df

df = load_data()
total = len(df)

# ─────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────
def pct(col, val):
    s = df[col].dropna()
    return round(100 * (s == val).sum() / len(s), 1) if len(s) else 0

def avg(col):
    s = df[col].dropna().astype(str).str.extract(r"(\d+)").astype(float)
    return round(s.mean()[0], 2) if len(s) else 0

def value_counts_simple(col, n=10):
    vc = df[col].value_counts().head(n).reset_index()
    vc.columns = ["Category", "Count"]
    return vc

def value_counts_split(col, n=20):
    """Split comma-separated values and count each separately."""
    all_vals = []
    for v in df[col].dropna():
        parts = [p.strip() for p in str(v).split(",")]
        all_vals.extend([p for p in parts if p])
    counter = Counter(all_vals)
    df_out = pd.DataFrame(counter.most_common(n), columns=["Category", "Count"])
    return df_out

def make_bar(df_chart, title, height, pct_labels=True):
    total_count = df_chart["Count"].sum()
    df_chart = df_chart.copy()
    if pct_labels:
        df_chart["Pct"] = (df_chart["Count"] / total_count * 100).round(1)
        df_chart["Label"] = df_chart["Pct"].apply(lambda x: f"{x}%")
    else:
        df_chart["Label"] = df_chart["Count"].astype(str)

    fig = go.Figure(go.Bar(
        x=df_chart["Count"],
        y=df_chart["Category"],
        orientation="h",
        text=df_chart["Label"],
        textposition="outside",
        marker_color="#4361ee",
        cliponaxis=False
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#495057"), x=0),
        height=height,
        margin=dict(l=0, r=60, t=36, b=10),
        xaxis=dict(visible=False),
        yaxis=dict(title=None, tickfont=dict(size=11)),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=False
    )
    return fig

def make_pie(df_chart, title, height):
    total_count = df_chart["Count"].sum()
    labels_with_pct = [
        f"{r['Category']} ({r['Count']/total_count*100:.1f}%)"
        for _, r in df_chart.iterrows()
    ]
    fig = go.Figure(go.Pie(
        labels=df_chart["Category"],
        values=df_chart["Count"],
        text=labels_with_pct,
        textinfo="percent",
        hovertemplate="%{label}: %{value} (%{percent})<extra></extra>",
    ))
    fig.update_layout(
        title=dict(text=title, font=dict(size=13, color="#495057"), x=0),
        height=height,
        margin=dict(l=0, r=0, t=36, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(font=dict(size=10), orientation="v")
    )
    return fig

# ─────────────────────────────────────────────
# SIDEBAR — SETTINGS
# ─────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Dashboard Settings")

    # Logo upload
    st.subheader("🖼️ Logo")
    logo_file = st.file_uploader("Upload logo (PNG)", type=["png", "jpg", "jpeg"])

    st.subheader("📐 Chart Sizes")
    bar_h = st.slider("Bar chart height (px)", 200, 700, 350, 25)
    pie_h = st.slider("Pie chart height (px)", 200, 600, 350, 25)
    age_h = st.slider("Age chart height (px)", 200, 600, 300, 25)

    st.subheader("🔢 Max Chart Items")
    bar_n = st.slider("Items in bar charts", 3, 20, 8)

    st.subheader("➕ Extra Charts")
    st.markdown("Add additional columns to chart below.")
    all_cols = [c for c in df.columns if df[c].nunique() < 50 and df[c].nunique() > 1]
    extra_cols = st.multiselect("Select columns", options=all_cols)
    extra_split = st.checkbox("Split by comma for extra charts", value=False)
    extra_type = st.radio("Chart type for extras", ["Bar", "Pie"], horizontal=True)

    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()

# ─────────────────────────────────────────────
# HEADER — Logo + Title
# ─────────────────────────────────────────────
logo_col, title_col = st.columns([1, 5])
with logo_col:
    if logo_file:
        st.image(logo_file, width=120)
    else:
        st.markdown(
            '<div style="width:100px;height:60px;background:#4361ee;border-radius:8px;'
            'display:flex;align-items:center;justify-content:center;color:white;font-weight:700;font-size:18px;">'
            '🚗</div>',
            unsafe_allow_html=True
        )
with title_col:
    st.markdown("## Autoshow Experience Dashboard")
    st.caption(f"Live data · {total:,} total responses")

st.divider()

# ─────────────────────────────────────────────
# COMPACT KPI ROW
# ─────────────────────────────────────────────
pct_likely  = pct("Q2.4 - How likely are you to consider brand for your next vehicle?", "Very likely")
pct_best    = pct("Q6.3 - Which brand had the best display at the show?", "brand")
pct_owners  = pct("Q2.1 - Do you currently own or lease a brand?", "Yes")

# All individual experience score KPIs (matching original left-side cards)
score_cols = {
    "Overall experience":          "Q3.4_9 - Overall experience",
    "Vehicle appearance":          "Q3.4_1 - Vehicle appearance",
    "Variety of vehicles":         "Q3.4_2 - Variety of vehicles",
    "Staff helpfulness":           "Q3.4_3 - Staff helpfulness",
    "Quality of activities/games": "Q3.4_4 - Quality of activities and games",
    "Quality of giveaways":        "Q3.4_5 - Quality of giveaways",
    "Display layout & design":     "Q3.4_6 - Display layout and design",
}
scores = {label: avg(col) for label, col in score_cols.items() if col in df.columns}

# ── Top compact KPI row ───────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Responses", f"{total:,}")
k2.metric("Very Likely %", f"{pct_likely}%")
k3.metric("Best Display %", f"{pct_best}%")
k4.metric("Owners %", f"{pct_owners}%")

st.markdown("<div style='margin-top:8px'></div>", unsafe_allow_html=True)

# ── Experience score cards (original left-side KPIs, now in a compact row) ──
if scores:
    score_items = list(scores.items())
    cols = st.columns(len(score_items))
    for i, (label, val) in enumerate(score_items):
        cols[i].metric(label, val)

st.divider()

# ─────────────────────────────────────────────
# MAIN CHARTS (columns with comma-split)
# ─────────────────────────────────────────────

# Column names — update these to match your actual sheet columns
WORDS_COL  = "Q5.1 - After visiting the brand display, which words best describe brand? (select all that apply)"
DREW_COL   = "Q4.1 - What first drew you to the brand display? (select all that apply)"
HEARD_COL  = "Q4.2 - How did you hear about the brand Ride & Drive?"
INTENT_COL = "Q2.4 - How likely are you to consider brand for your next vehicle?"
AGE_COL    = "Q8.1 - What is your age?"

# Detect if columns exist, else fallback gracefully
def col_exists(c):
    return c in df.columns

row1_a, row1_b = st.columns(2)

with row1_a:
    # ── Words describing brand (comma-split) ──────────────────────────
    if col_exists(WORDS_COL):
        d = value_counts_split(WORDS_COL, bar_n)
        st.plotly_chart(make_bar(d, "Words that best describe the brand", bar_h), use_container_width=True)
    else:
        st.info(f"Column not found: {WORDS_COL}")

with row1_b:
    # ── What drew you to the display (comma-split) ─────────────────────
    if col_exists(DREW_COL):
        d = value_counts_split(DREW_COL, bar_n)
        st.plotly_chart(make_bar(d, "What first drew you to the brand display", bar_h), use_container_width=True)
    else:
        st.info(f"Column not found: {DREW_COL}")

row2_a, row2_b = st.columns(2)

with row2_a:
    # ── How heard about Ride & Drive (simple) ─────────────────────────
    if col_exists(HEARD_COL):
        d = value_counts_simple(HEARD_COL, bar_n)
        st.plotly_chart(make_bar(d, "How did you hear about the Ride & Drive?", bar_h), use_container_width=True)
    else:
        st.info(f"Column not found: {HEARD_COL}")

with row2_b:
    # ── Purchase intent (pie) ─────────────────────────────────────────
    if col_exists(INTENT_COL):
        d = value_counts_simple(INTENT_COL, 10)
        st.plotly_chart(make_pie(d, "Purchase Intent", pie_h), use_container_width=True)
    else:
        st.info(f"Column not found: {INTENT_COL}")

# ── Age distribution ─────────────────────────────────────────────────
if col_exists(AGE_COL):
    d = value_counts_simple(AGE_COL, bar_n)
    st.plotly_chart(make_bar(d, "Age Distribution", age_h), use_container_width=True)

st.divider()

# ─────────────────────────────────────────────
# EXTRA CHARTS (added via sidebar)
# ─────────────────────────────────────────────
if extra_cols:
    st.markdown('<p class="section-header">➕ Custom Charts</p>', unsafe_allow_html=True)
    num_cols = min(len(extra_cols), 2)
    cols = st.columns(num_cols)
    for i, col_name in enumerate(extra_cols):
        with cols[i % num_cols]:
            if extra_split:
                d = value_counts_split(col_name, bar_n)
            else:
                d = value_counts_simple(col_name, bar_n)
            label = col_name[:50] + "…" if len(col_name) > 50 else col_name
            if extra_type == "Bar":
                st.plotly_chart(make_bar(d, label, bar_h), use_container_width=True)
            else:
                st.plotly_chart(make_pie(d, label, pie_h), use_container_width=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.caption("Dashboard auto-refreshes every 5 min · Use sidebar to customise chart sizes and add charts · Upload your logo in ⚙️ Settings")
