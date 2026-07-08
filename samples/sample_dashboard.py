import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

import html

# Add this helper at the top of sample_dashboard.py
def esc(val) -> str:
    """Escape special HTML characters in data values."""
    if pd.isna(val) or val is None:
        return "—"
    return html.escape(str(val))

# ─────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────
SCOPE = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

COL_BRANCH      = "Branch"
COL_AREA        = "Area"
COL_ENQ_DATE    = "Enquiry sent to Principal date"
COL_HO_DATE     = "Hand over to customer date"
COL_CUSTOMER    = "Name of Customer / Party"
COL_CONTACT     = "Contact Person at Customer / Party"
COL_CUST_PROD   = "Product Mfgd. By Customer / Party"
COL_SAMPLE_PROD = "Our Sample Product Name"
COL_QTY         = "Sample Quantity"
COL_HO_BY       = "Handed over By"
COL_FEEDBACK    = "Feedback"

ALL_COLS = [
    COL_BRANCH, COL_AREA, COL_ENQ_DATE, COL_HO_DATE,
    COL_CUSTOMER, COL_CONTACT, COL_CUST_PROD,
    COL_SAMPLE_PROD, COL_QTY, COL_HO_BY, COL_FEEDBACK
]

# ─────────────────────────────────────────
# URGENCY CONFIG
# ─────────────────────────────────────────
URGENCY_LEVELS = {
    "Freshly Handed": {
        "days":    (0, 6),
        "color":   "#2E7D32",
        "bg":      "#E8F5E9",
        "border":  "#A5D6A7",
        "icon":    "🟢",
        "pulse":   False,
    },
    "Initial Follow-up": {
        "days":    (7, 14),
        "color":   "#F57F17",
        "bg":      "#FFF8E1",
        "border":  "#FFD54F",
        "icon":    "🟡",
        "pulse":   False,
    },
    "Push Required": {
        "days":    (15, 20),
        "color":   "#E65100",
        "bg":      "#FFF3E0",
        "border":  "#FFAB40",
        "icon":    "🟠",
        "pulse":   True,
    },
    "Critical": {
        "days":    (21, 9999),
        "color":   "#B71C1C",
        "bg":      "#FFEBEE",
        "border":  "#EF9A9A",
        "icon":    "🔴",
        "pulse":   True,
    },
}

def get_urgency(days_since_handover, feedback_status):
    """Return urgency level name. Responded entries skip urgency."""
    if feedback_status == "Responded":
        return "Responded"
    if pd.isna(days_since_handover):
        return "Unknown"
    d = int(days_since_handover)
    for level, cfg in URGENCY_LEVELS.items():
        lo, hi = cfg["days"]
        if lo <= d <= hi:
            return level
    return "Critical"


# ─────────────────────────────────────────
# CSS
# ─────────────────────────────────────────
SAMPLE_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,600;0,700;1,400&family=Outfit:wght@300;400;500;600;700&display=swap');

:root {
    --navy:      #1B2A4A;
    --gold:      #C9A84C;
    --gold-lt:   #E8C96A;
    --cream:     #FAF7F2;
    --warm-gray: #F0EBE1;
    --border:    #DDD5C5;
    --muted:     #6B7A99;
    --green:     #2E7D32;
    --green-bg:  #E8F5E9;
    --green-bd:  #A5D6A7;
    --red:       #B71C1C;
    --amber:     #E65100;
}

[data-testid="stAppViewContainer"],
[data-testid="stAppViewContainer"] > .main {
    background-color: var(--cream) !important;
}
[data-testid="stHeader"] { background-color: var(--cream) !important; }

section[data-testid="stSidebar"] {
    background: var(--navy) !important;
    border-right: 3px solid var(--gold) !important;
}
section[data-testid="stSidebar"] * {
    color: #E8E4DC !important;
    font-family: 'Outfit', sans-serif !important;
}
section[data-testid="stSidebar"] .stButton > button {
    background: transparent !important;
    color: #E8C97A !important;
    border: 1px solid var(--gold) !important;
    border-radius: 8px !important;
    font-size: 0.9rem !important;
    font-weight: 600 !important;
    margin-bottom: 4px !important;
    transition: all 0.2s ease !important;
}
section[data-testid="stSidebar"] .stButton > button:hover {
    background: rgba(201,168,76,0.15) !important;
    color: #FFFFFF !important;
}

/* ── Pulse animation ── */
@keyframes pulse-red {
    0%   { box-shadow: 0 0 0 0 rgba(183,28,28,0.5); }
    70%  { box-shadow: 0 0 0 8px rgba(183,28,28,0); }
    100% { box-shadow: 0 0 0 0 rgba(183,28,28,0); }
}
@keyframes pulse-orange {
    0%   { box-shadow: 0 0 0 0 rgba(230,81,0,0.45); }
    70%  { box-shadow: 0 0 0 8px rgba(230,81,0,0); }
    100% { box-shadow: 0 0 0 0 rgba(230,81,0,0); }
}
.badge-critical {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #FFEBEE;
    border: 1.5px solid #EF9A9A;
    color: #B71C1C;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    animation: pulse-red 1.4s infinite;
    letter-spacing: 0.04em;
}
.badge-push {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #FFF3E0;
    border: 1.5px solid #FFAB40;
    color: #E65100;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
    animation: pulse-orange 1.8s infinite;
    letter-spacing: 0.04em;
}
.badge-initial {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #FFF8E1;
    border: 1.5px solid #FFD54F;
    color: #F57F17;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
}
.badge-fresh {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #E8F5E9;
    border: 1.5px solid #A5D6A7;
    color: #2E7D32;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
}
.badge-responded {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    background: #E3F2FD;
    border: 1.5px solid #90CAF9;
    color: #1565C0;
    border-radius: 20px;
    padding: 4px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    font-family: 'Outfit', sans-serif;
}
.badge-positive {
    display: inline-flex; align-items: center; gap: 5px;
    background: #E8F5E9; border: 1px solid #A5D6A7;
    color: #2E7D32; border-radius: 20px;
    padding: 3px 10px; font-size: 0.68rem; font-weight: 600;
    font-family: 'Outfit', sans-serif;
}
.badge-negative {
    display: inline-flex; align-items: center; gap: 5px;
    background: #FFEBEE; border: 1px solid #EF9A9A;
    color: #B71C1C; border-radius: 20px;
    padding: 3px 10px; font-size: 0.68rem; font-weight: 600;
    font-family: 'Outfit', sans-serif;
}
.badge-pending {
    display: inline-flex; align-items: center; gap: 5px;
    background: #FFF8E1; border: 1px solid #FFD54F;
    color: #F57F17; border-radius: 20px;
    padding: 3px 10px; font-size: 0.68rem; font-weight: 600;
    font-family: 'Outfit', sans-serif;
}

/* ── Hero ── */
.sd-hero { padding: 1.5rem 0 1rem 0; margin-bottom: 1rem; }
.sd-eyebrow {
    font-family: 'Outfit', sans-serif;
    font-size: 0.72rem; font-weight: 600;
    letter-spacing: 0.22em; text-transform: uppercase;
    color: var(--gold); margin-bottom: 0.4rem;
}
.sd-title {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.8rem; font-weight: 700;
    color: var(--navy); line-height: 1.1; margin-bottom: 0.3rem;
}
.sd-title em { color: var(--gold); font-style: italic; }
.sd-sub {
    font-family: 'Outfit', sans-serif;
    font-size: 0.95rem; color: var(--muted); font-weight: 400;
}
.sd-divider {
    width: 60px; height: 3px;
    background: linear-gradient(90deg, var(--gold), var(--gold-lt));
    border-radius: 2px; margin: 0.8rem 0 1.5rem 0;
}

/* ── KPI Cards ── */
.kpi-card {
    background: #FFFFFF;
    border: 1.5px solid var(--border);
    border-radius: 14px;
    padding: 1.4rem 1.6rem;
    position: relative; overflow: hidden;
    box-shadow: 0 2px 10px rgba(27,42,74,0.06);
    transition: transform 0.15s ease, box-shadow 0.15s ease;
    height: 100%;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 24px rgba(27,42,74,0.1);
}
.kpi-card::before {
    content: ''; position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, var(--gold), var(--gold-lt));
}
.kpi-card.green::before { background: linear-gradient(90deg,#2E7D32,#4CAF50); }
.kpi-card.amber::before { background: linear-gradient(90deg,#E65100,#FF9800); }
.kpi-card.red::before   { background: linear-gradient(90deg,#B71C1C,#EF5350); }
.kpi-card.blue::before  { background: linear-gradient(90deg,#1565C0,#42A5F5); }
.kpi-label {
    font-family: 'Outfit', sans-serif;
    font-size: 0.7rem; font-weight: 700;
    letter-spacing: 0.14em; text-transform: uppercase;
    color: var(--muted); margin-bottom: 0.5rem;
}
.kpi-value {
    font-family: 'Cormorant Garamond', serif;
    font-size: 2.6rem; font-weight: 700;
    color: var(--navy); line-height: 1; margin-bottom: 0.2rem;
}
.kpi-value.green { color: var(--green); }
.kpi-value.amber { color: var(--amber); }
.kpi-value.red   { color: var(--red); }
.kpi-value.blue  { color: #1565C0; }
.kpi-sub { font-family: 'Outfit', sans-serif; font-size: 0.75rem; color: var(--muted); }

/* ── Section titles ── */
.sd-section {
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.5rem; font-weight: 700;
    color: var(--navy);
    border-bottom: 2px solid var(--border);
    padding-bottom: 8px; margin: 2.5rem 0 1.2rem 0;
    position: relative;
}
.sd-section::after {
    content: ''; position: absolute;
    bottom: -2px; left: 0; width: 45px; height: 2px;
    background: var(--gold);
}

/* ── Hierarchy ── */
.hier-branch {
    background: var(--navy);
    color: #FFFFFF;
    border-radius: 10px;
    padding: 0.8rem 1.2rem;
    margin-bottom: 0.5rem;
    font-family: 'Cormorant Garamond', serif;
    font-size: 1.1rem;
    font-weight: 700;
    cursor: pointer;
}
.hier-area {
    background: var(--warm-gray);
    border: 1.5px solid var(--border);
    border-left: 4px solid var(--gold);
    border-radius: 8px;
    padding: 0.6rem 1rem;
    margin: 0.3rem 0 0.3rem 1.5rem;
    font-family: 'Outfit', sans-serif;
    font-size: 0.88rem;
    font-weight: 600;
    color: var(--navy);
}
.hier-sample {
    background: #FFFFFF;
    border: 1.5px solid var(--border);
    border-radius: 8px;
    padding: 0.7rem 1rem;
    margin: 0.25rem 0 0.25rem 3rem;
    font-family: 'Outfit', sans-serif;
    font-size: 0.82rem;
    color: var(--navy);
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 8px;
}
.hier-sample-info { display: flex; flex-direction: column; gap: 2px; }
.hier-sample-name { font-weight: 600; font-size: 0.88rem; }
.hier-sample-meta { color: var(--muted); font-size: 0.75rem; }

/* ── Follow-up card ── */
.followup-row {
    background: #FFFFFF;
    border: 1.5px solid var(--border);
    border-radius: 10px;
    padding: 0.9rem 1.2rem;
    margin-bottom: 0.6rem;
    font-family: 'Outfit', sans-serif;
}
.followup-row.critical { border-left: 5px solid #B71C1C; }
.followup-row.push     { border-left: 5px solid #E65100; }
.followup-row.initial  { border-left: 5px solid #F57F17; }
.followup-row.fresh    { border-left: 5px solid #2E7D32; }
.followup-customer {
    font-size: 0.95rem; font-weight: 600; color: var(--navy);
}
.followup-meta { font-size: 0.78rem; color: var(--muted); margin-top: 3px; }

/* ── Feedback history ── */
.fb-history-item {
    background: var(--warm-gray);
    border-radius: 6px;
    padding: 6px 10px;
    margin-top: 6px;
    font-size: 0.8rem;
    color: var(--navy);
    font-family: 'Outfit', sans-serif;
}
.fb-history-meta {
    font-size: 0.7rem;
    color: var(--muted);
    margin-bottom: 2px;
}

/* ── Insight box ── */
.insight-box {
    background: #FFFFFF;
    border: 1.5px solid var(--border);
    border-left: 4px solid var(--gold);
    border-radius: 10px;
    padding: 1rem 1.2rem;
    margin-bottom: 0.8rem;
    font-family: 'Outfit', sans-serif;
    font-size: 0.9rem; color: var(--navy);
}
.insight-box b { color: var(--gold); }

/* ── Urgency legend ── */
.urgency-legend {
    display: flex; gap: 12px; flex-wrap: wrap;
    margin-bottom: 1.2rem; align-items: center;
}
.legend-item {
    display: flex; align-items: center; gap: 6px;
    font-family: 'Outfit', sans-serif;
    font-size: 0.78rem; color: var(--navy);
}

/* ── Tabs ── */
[data-testid="stTabs"] [role="tab"] {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.95rem !important; font-weight: 500 !important;
}
[data-testid="stTabs"] [role="tab"][aria-selected="true"] {
    font-weight: 700 !important;
    border-bottom: 2px solid var(--gold) !important;
}

/* ── Widgets ── */
[data-testid="stSelectbox"] > div > div {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.92rem !important;
    border-radius: 8px !important;
    border: 1.5px solid var(--border) !important;
    background: #FFFFFF !important;
}
[data-testid="stSelectbox"] input {
    border: none !important; box-shadow: none !important;
    background: transparent !important;
}
[data-testid="stWidgetLabel"] p {
    font-family: 'Outfit', sans-serif !important;
    font-size: 0.85rem !important; font-weight: 600 !important;
    color: var(--navy) !important;
}
[data-testid="stDataFrame"] {
    border-radius: 10px !important;
    border: 1.5px solid var(--border) !important;
    overflow: hidden !important;
}
.stButton > button {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 600 !important; font-size: 0.9rem !important;
    border-radius: 8px !important;
}
</style>
"""


# ─────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────
@st.cache_data(ttl=1800, show_spinner=False)
def load_sample_data() -> pd.DataFrame:
    try:
        creds  = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=SCOPE
        )
        client   = gspread.authorize(creds)
        sheet_id = st.secrets["spreadsheets"]["samples"]
        ws       = client.open_by_key(sheet_id).sheet1
        records  = ws.get_all_records()

        if not records:
            return pd.DataFrame(columns=ALL_COLS)

        df = pd.DataFrame(records)
        df.columns = df.columns.str.strip()

        for col in [COL_ENQ_DATE, COL_HO_DATE]:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], dayfirst=True, errors="coerce")

        for col in [COL_BRANCH, COL_AREA, COL_CUSTOMER,
                    COL_SAMPLE_PROD, COL_HO_BY, COL_FEEDBACK]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                df[col] = df[col].replace(["nan", "None", ""], pd.NA)

        if COL_ENQ_DATE in df.columns and COL_HO_DATE in df.columns:
            df["Days to Handover"] = (df[COL_HO_DATE] - df[COL_ENQ_DATE]).dt.days

        df["Days Since Handover"] = (
            pd.Timestamp.now() - df[COL_HO_DATE]
        ).dt.days

        return df

    except Exception as e:
        st.error(f"Failed to load sample data: {e}")
        return pd.DataFrame(columns=ALL_COLS)


# ─────────────────────────────────────────
# FIRESTORE — FEEDBACK HISTORY
# ─────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def load_all_feedback_history() -> dict:
    """
    Returns dict keyed by (customer, product, ho_date_str) →
    list of feedback dicts sorted by created_at desc.
    """
    try:
        from auth.firebase_config import get_db
        db   = get_db()
        docs = db.collection("sample_feedback_updates").stream()
        result = {}
        for doc in docs:
            d = doc.to_dict()
            key = (
                str(d.get("customer", "")).strip(),
                str(d.get("product", "")).strip(),
                str(d.get("ho_date", ""))[:10]
            )
            result.setdefault(key, []).append({
                "feedback":   d.get("new_feedback", ""),
                "updated_by": d.get("updated_by", ""),
                "updated_at": d.get("updated_at", ""),
            })
        # Sort each list newest first
        for key in result:
            result[key].sort(key=lambda x: x["updated_at"], reverse=True)
        return result
    except Exception:
        return {}


def get_feedback_for_row(row, history: dict):
    """Get feedback history list for a given row."""
    ho_date = row[COL_HO_DATE]
    ho_str  = str(ho_date.date()) if pd.notna(ho_date) else ""
    key = (
        str(row.get(COL_CUSTOMER, "")).strip(),
        str(row.get(COL_SAMPLE_PROD, "")).strip(),
        ho_str
    )
    return history.get(key, [])


def get_latest_feedback(row, history: dict):
    """Return latest feedback text — Firestore first, sheet fallback."""
    fb_list = get_feedback_for_row(row, history)
    if fb_list:
        return fb_list[0]["feedback"]
    return str(row.get(COL_FEEDBACK, "")) if pd.notna(row.get(COL_FEEDBACK)) else ""


def classify_feedback(text: str) -> str:
    if not text or str(text).strip() in ("", "nan", "None", "-", "_"):
        return "Pending"
    v = str(text).lower()
    pos_kw = ["good", "positive", "interested", "approved", "accepted",
               "excellent", "great", "liked", "satisfied", "happy",
               "ok", "fine", "proceed", "confirmed", "yes"]
    neg_kw = ["reject", "negative", "not interested", "declined",
               "no", "bad", "poor", "failed", "not suitable", "cancelled"]
    if any(k in v for k in pos_kw): return "Positive"
    if any(k in v for k in neg_kw): return "Negative"
    return "Pending"


# ─────────────────────────────────────────
# BADGE HTML HELPERS
# ─────────────────────────────────────────
def urgency_badge(urgency: str) -> str:
    cls_map = {
        "Freshly Handed":    "badge-fresh",
        "Initial Follow-up": "badge-initial",
        "Push Required":     "badge-push",
        "Critical":          "badge-critical",
        "Responded":         "badge-responded",
    }
    icon_map = {
        "Freshly Handed":    "🟢",
        "Initial Follow-up": "🟡",
        "Push Required":     "🟠",
        "Critical":          "🔴",
        "Responded":         "✅",
    }
    cls  = cls_map.get(urgency, "badge-fresh")
    icon = icon_map.get(urgency, "")
    return f'<span class="{cls}">{icon} {urgency}</span>'


def feedback_badge(status: str) -> str:
    cls_map = {"Positive": "badge-positive",
               "Negative": "badge-negative",
               "Pending":  "badge-pending"}
    icon_map = {"Positive": "👍", "Negative": "👎", "Pending": "⏳"}
    cls  = cls_map.get(status, "badge-pending")
    icon = icon_map.get(status, "")
    return f'<span class="{cls}">{icon} {status}</span>'


# ─────────────────────────────────────────
# CHART HELPERS
# ─────────────────────────────────────────
CHART_COLORS = ["#1B2A4A", "#C9A84C", "#5A6A85", "#E8C96A",
                "#8A9BBB", "#2E7D32", "#B71C1C", "#E65100"]

def chart_layout(fig, height=340):
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(250,247,242,1)",
        font=dict(family="Outfit", color="#6B7A99", size=11),
        margin=dict(l=10, r=10, t=30, b=10),
        height=height,
        xaxis=dict(gridcolor="#DDD5C5", linecolor="#DDD5C5"),
        yaxis=dict(gridcolor="#DDD5C5", linecolor="#DDD5C5"),
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(size=11)),
    )
    return fig


def kpi(label, value, sub="", variant="default"):
    val_class  = variant if variant != "default" else ""
    card_class = f"kpi-card {variant}" if variant != "default" else "kpi-card"
    st.markdown(f"""
    <div class="{card_class}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value {val_class}">{value}</div>
        <div class="kpi-sub">{sub}</div>
    </div>""", unsafe_allow_html=True)


# ─────────────────────────────────────────
# MAIN PAGE
# ─────────────────────────────────────────
def show_sample_dashboard():
    st.markdown(SAMPLE_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="sd-hero">
        <div class="sd-eyebrow">Sample Intelligence</div>
        <div class="sd-title">Sample <em>Tracker</em></div>
        <div class="sd-sub">Track samples, monitor feedback urgency and identify follow-up opportunities.</div>
        <div class="sd-divider"></div>
    </div>""", unsafe_allow_html=True)

    col_back, col_btn = st.columns([3, 1])
    with col_back:
        if st.button("← Back to Dashboard", key="back_from_sd"):
            st.session_state["page"] = "dashboard"
            st.rerun()
    with col_btn:
        if st.button("✏️ Add / Update Sample", key="nav_sample_entry",
                    width='stretch'):
            st.session_state["page"] = "sample_entry"
            st.rerun()

    # ── Load data ──
    with st.spinner("Loading sample data..."):
        df      = load_sample_data()
        history = load_all_feedback_history()

    if df.empty:
        st.warning("No sample data found. Check your Google Sheet.")
        return

    # ── Enrich with latest feedback + urgency ──
    df["Latest Feedback"]  = df.apply(
        lambda r: get_latest_feedback(r, history), axis=1
    )
    df["Feedback Status"]  = df["Latest Feedback"].apply(classify_feedback)
    df["Has Response"]     = df["Feedback Status"] != "Pending"
    df["Urgency"]          = df.apply(
        lambda r: "Responded" if r["Has Response"]
        else get_urgency(r.get("Days Since Handover"), "Pending"),
        axis=1
    )

    # ── Sidebar filters ──
    with st.sidebar:
        st.markdown("---")
        st.markdown(
            "<div style='font-size:0.7rem;font-weight:700;letter-spacing:0.15em;"
            "text-transform:uppercase;color:#C9A84C;margin-bottom:8px;'>Filters</div>",
            unsafe_allow_html=True
        )
        branches   = ["All"] + sorted(df[COL_BRANCH].dropna().unique().tolist())
        sel_branch = st.selectbox("Branch",   branches, key="sd_branch")

        products   = ["All"] + sorted(df[COL_SAMPLE_PROD].dropna().unique().tolist())
        sel_prod   = st.selectbox("Product",  products, key="sd_product")

        ho_by_opts = ["All"] + sorted(df[COL_HO_BY].dropna().unique().tolist())
        sel_ho     = st.selectbox("Handed Over By", ho_by_opts, key="sd_ho")

        urgency_opts = ["All", "Critical", "Push Required",
                        "Initial Follow-up", "Freshly Handed", "Responded"]
        sel_urg    = st.selectbox("Urgency", urgency_opts, key="sd_urg")

        fb_opts    = ["All", "Positive", "Negative", "Pending"]
        sel_fb     = st.selectbox("Feedback Status", fb_opts, key="sd_fb")

        if st.button("🔄 Reset Filters", key="sd_reset", width='stretch'):
            for k in ["sd_branch","sd_product","sd_ho","sd_urg","sd_fb"]:
                st.session_state.pop(k, None)
            st.rerun()

    # ── Apply filters ──
    fdf = df.copy()
    if sel_branch != "All": fdf = fdf[fdf[COL_BRANCH]       == sel_branch]
    if sel_prod   != "All": fdf = fdf[fdf[COL_SAMPLE_PROD]  == sel_prod]
    if sel_ho     != "All": fdf = fdf[fdf[COL_HO_BY]        == sel_ho]
    if sel_urg    != "All": fdf = fdf[fdf["Urgency"]        == sel_urg]
    if sel_fb     != "All": fdf = fdf[fdf["Feedback Status"]== sel_fb]

    # ══════════════════════════════════════
    # KPI CARDS
    # ══════════════════════════════════════
    total    = len(fdf)
    positive = len(fdf[fdf["Feedback Status"] == "Positive"])
    negative = len(fdf[fdf["Feedback Status"] == "Negative"])
    pending  = len(fdf[fdf["Feedback Status"] == "Pending"])
    critical = len(fdf[fdf["Urgency"] == "Critical"])
    push_req = len(fdf[fdf["Urgency"] == "Push Required"])
    conv_rt  = f"{positive/total*100:.0f}%" if total > 0 else "—"

    c1,c2,c3,c4,c5,c6 = st.columns(6)
    with c1: kpi("Total Samples", total)
    with c2: kpi("Positive",  positive, f"{conv_rt} rate", "green")
    with c3: kpi("Pending",   pending,  "awaiting feedback", "amber")
    with c4: kpi("Negative",  negative, "rejected", "red")
    with c5: kpi("🔴 Critical",  critical, "21+ days no feedback", "red")
    with c6: kpi("🟠 Push Reqd", push_req, "15-20 days", "amber")

    st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

    # ══════════════════════════════════════
    # TABS
    # ══════════════════════════════════════
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊  Overview",
        "🏢  By Branch & Area",
        "🔔  Follow-up Tracker",
        "📋  All Samples",
    ])

    # ──────────────────────────────────────
    # TAB 1 — OVERVIEW
    # ──────────────────────────────────────
    with tab1:
        col_a, col_b = st.columns(2, gap="large")

        with col_a:
            st.markdown('<div class="sd-section">Samples by Branch</div>',
                       unsafe_allow_html=True)
            branch_counts = fdf[COL_BRANCH].value_counts().reset_index()
            branch_counts.columns = ["Branch", "Count"]
            fig = px.bar(branch_counts, x="Branch", y="Count",
                        color_discrete_sequence=[CHART_COLORS[0]], text="Count")
            fig.update_traces(textposition="outside")
            st.plotly_chart(chart_layout(fig), width='stretch',
                           config={"displayModeBar": False})

        with col_b:
            st.markdown('<div class="sd-section">Urgency Distribution</div>',
                       unsafe_allow_html=True)
            urg_order  = ["Freshly Handed","Initial Follow-up",
                          "Push Required","Critical","Responded"]
            urg_colors = {"Freshly Handed":   "#2E7D32",
                          "Initial Follow-up": "#F57F17",
                          "Push Required":     "#E65100",
                          "Critical":          "#B71C1C",
                          "Responded":         "#1565C0"}
            urg_counts = fdf["Urgency"].value_counts().reset_index()
            urg_counts.columns = ["Urgency","Count"]
            fig2 = px.pie(urg_counts, names="Urgency", values="Count",
                         color="Urgency", color_discrete_map=urg_colors, hole=0.5)
            fig2.update_traces(textinfo="percent+label", textfont_size=12)
            st.plotly_chart(chart_layout(fig2), width='stretch',
                           config={"displayModeBar": False})

        # ── Stacked bar — Top products with feedback breakdown ──
        st.markdown('<div class="sd-section">Top Products — Feedback Breakdown</div>',
                   unsafe_allow_html=True)

        top_prods = (fdf[COL_SAMPLE_PROD].value_counts()
                     .head(12).index.tolist())
        prod_fb = (fdf[fdf[COL_SAMPLE_PROD].isin(top_prods)]
                   .groupby([COL_SAMPLE_PROD, "Feedback Status"])
                   .size().reset_index(name="Count"))

        fig3 = px.bar(
            prod_fb, x="Count", y=COL_SAMPLE_PROD,
            color="Feedback Status", orientation="h",
            color_discrete_map={
                "Positive": "#2E7D32",
                "Negative": "#B71C1C",
                "Pending":  "#F57F17"
            },
            barmode="stack",
            category_orders={COL_SAMPLE_PROD: top_prods}
        )
        fig3.update_layout(yaxis=dict(autorange="reversed"))
        st.plotly_chart(chart_layout(fig3, height=420), width='stretch',
                       config={"displayModeBar": False})

        # ── Top customers stacked ──
        col_c, col_d = st.columns(2, gap="large")

        with col_c:
            st.markdown('<div class="sd-section">Top Customers</div>',
                       unsafe_allow_html=True)
            top_custs = fdf[COL_CUSTOMER].value_counts().head(10).index.tolist()
            cust_fb = (fdf[fdf[COL_CUSTOMER].isin(top_custs)]
                       .groupby([COL_CUSTOMER, "Feedback Status"])
                       .size().reset_index(name="Count"))
            fig4 = px.bar(
                cust_fb, x="Count", y=COL_CUSTOMER,
                color="Feedback Status", orientation="h",
                color_discrete_map={"Positive":"#2E7D32",
                                    "Negative":"#B71C1C","Pending":"#F57F17"},
                barmode="stack",
                category_orders={COL_CUSTOMER: top_custs}
            )
            fig4.update_layout(yaxis=dict(autorange="reversed"))
            st.plotly_chart(chart_layout(fig4, height=380), width='stretch',
                           config={"displayModeBar": False})

        with col_d:
            st.markdown('<div class="sd-section">Team Activity</div>',
                       unsafe_allow_html=True)
            ho_counts = fdf[COL_HO_BY].value_counts().reset_index()
            ho_counts.columns = ["Person","Samples"]
            fig5 = px.bar(ho_counts, x="Person", y="Samples",
                         color_discrete_sequence=CHART_COLORS, text="Samples")
            fig5.update_traces(textposition="outside")
            st.plotly_chart(chart_layout(fig5, height=380), width='stretch',
                           config={"displayModeBar": False})

        # ── Timeline ──
        st.markdown('<div class="sd-section">Sample Activity Timeline</div>',
                   unsafe_allow_html=True)
        if COL_HO_DATE in fdf.columns:
            tl = (fdf[fdf[COL_HO_DATE].notna()]
                  .groupby(fdf[COL_HO_DATE].dt.to_period("M"))
                  .size().reset_index())
            tl.columns = ["Month","Samples"]
            tl["Month"] = tl["Month"].astype(str)
            fig6 = px.line(tl, x="Month", y="Samples", markers=True,
                          color_discrete_sequence=[CHART_COLORS[0]],
                          line_shape="spline")
            fig6.update_traces(line_width=2.5, marker_size=7)
            st.plotly_chart(chart_layout(fig6, height=260), width='stretch',
                           config={"displayModeBar": False})

        # ── Insights ──
        st.markdown('<div class="sd-section">Key Insights</div>',
                   unsafe_allow_html=True)
        i1, i2 = st.columns(2)
        with i1:
            top_prod   = fdf[COL_SAMPLE_PROD].value_counts().idxmax() if total>0 else "—"
            top_cust   = fdf[COL_CUSTOMER].value_counts().idxmax()    if total>0 else "—"
            top_branch = fdf[COL_BRANCH].value_counts().idxmax()      if total>0 else "—"
            st.markdown(f"""
            <div class="insight-box">🏆 Most sampled product: <b>{top_prod}</b></div>
            <div class="insight-box">👥 Most sampled customer: <b>{top_cust}</b></div>
            <div class="insight-box">📍 Most active branch: <b>{top_branch}</b></div>
            """, unsafe_allow_html=True)
        with i2:
            top_person = fdf[COL_HO_BY].value_counts().idxmax() if total>0 else "—"
            pending_pct = f"{pending/total*100:.0f}%" if total>0 else "—"
            crit_pct    = f"{critical/total*100:.0f}%" if total>0 else "—"
            st.markdown(f"""
            <div class="insight-box">🤝 Most active team member: <b>{top_person}</b></div>
            <div class="insight-box">⏳ Feedback pending: <b>{pending_pct}</b> of all samples</div>
            <div class="insight-box">🔴 Critical follow-ups: <b>{crit_pct}</b> of all samples</div>
            """, unsafe_allow_html=True)

    # ──────────────────────────────────────
    # TAB 2 — HIERARCHICAL VIEW
    # ──────────────────────────────────────
    with tab2:
        st.markdown('<div class="sd-section">Branch → Area → Sample Overview</div>',
                   unsafe_allow_html=True)

        # Urgency legend
        st.markdown("""
        <div class="urgency-legend">
            <span style="font-family:Outfit,sans-serif;font-size:0.78rem;
                         font-weight:600;color:#6B7A99;">Urgency:</span>
            <span class="badge-fresh">🟢 Freshly Handed</span>
            <span class="badge-initial">🟡 Initial Follow-up</span>
            <span class="badge-push">🟠 Push Required</span>
            <span class="badge-critical">🔴 Critical</span>
            <span class="badge-responded">✅ Responded</span>
        </div>
        """, unsafe_allow_html=True)

        branches_list = sorted(fdf[COL_BRANCH].dropna().unique().tolist())

        for branch in branches_list:
            branch_df    = fdf[fdf[COL_BRANCH] == branch]
            branch_total = len(branch_df)
            branch_crit  = len(branch_df[branch_df["Urgency"] == "Critical"])
            crit_txt     = f' &nbsp;<span style="color:#B71C1C;font-weight:700;">⚠ {branch_crit} critical</span>' \
                           if branch_crit > 0 else ""

            with st.expander(
                f"📍 {branch}  —  {branch_total} samples{(' · ⚠ ' + str(branch_crit) + ' critical') if branch_crit else ''}",
                expanded=(branch_crit > 0)   # auto-expand if critical items
            ):
                areas_list = sorted(branch_df[COL_AREA].dropna().unique().tolist())

                for area in areas_list:
                    area_df    = branch_df[branch_df[COL_AREA] == area]
                    area_total = len(area_df)
                    area_crit  = len(area_df[area_df["Urgency"] == "Critical"])

                    st.markdown(
                        f'<div class="hier-area">🗺 {area} &nbsp;·&nbsp; '
                        f'{area_total} samples'
                        f'{(" &nbsp;·&nbsp; ⚠ " + str(area_crit) + " critical") if area_crit else ""}'
                        f'</div>',
                        unsafe_allow_html=True
                    )

                    for _, row in area_df.iterrows():
                        urg      = row["Urgency"]
                        fb_stat  = row["Feedback Status"]
                        latest   = row["Latest Feedback"]
                        ho_date  = row[COL_HO_DATE].strftime("%d %b %Y") \
                                   if pd.notna(row.get(COL_HO_DATE)) else "—"
                        days_ago = int(row["Days Since Handover"]) \
                                   if pd.notna(row.get("Days Since Handover")) else 0

                        st.markdown(f"""
                        <div class="hier-sample">
                            <div class="hier-sample-info">
                                <div class="hier-sample-name">
                                    {row.get(COL_CUSTOMER,'—')}
                                </div>
                                <div class="hier-sample-meta">
                                    📦 {row.get(COL_SAMPLE_PROD,'—')} &nbsp;·&nbsp;
                                    📅 {ho_date} ({days_ago}d ago) &nbsp;·&nbsp;
                                    🤝 {row.get(COL_HO_BY,'—')}
                                </div>
                                {f'<div class="hier-sample-meta" style="margin-top:3px;font-style:italic;">💬 {latest[:80]}{"..." if len(str(latest))>80 else ""}</div>' if latest and latest not in ("nan","None","") else ""}
                            </div>
                            <div style="display:flex;gap:6px;align-items:center;flex-wrap:wrap;">
                                {urgency_badge(urg)}
                                {feedback_badge(fb_stat)}
                            </div>
                        </div>
                        """, unsafe_allow_html=True)

    # ──────────────────────────────────────
    # TAB 3 — FOLLOW-UP TRACKER
    # ──────────────────────────────────────
    with tab3:
        st.markdown('<div class="sd-section">🔔 Action Required</div>',
                   unsafe_allow_html=True)

        # Urgency legend
        st.markdown("""
        <div class="urgency-legend">
            <span class="badge-critical">🔴 Critical — 21+ days</span>
            <span class="badge-push">🟠 Push Required — 15-20 days</span>
            <span class="badge-initial">🟡 Initial Follow-up — 7-14 days</span>
            <span class="badge-fresh">🟢 Freshly Handed — 0-6 days</span>
        </div>
        """, unsafe_allow_html=True)

        pending_df = fdf[fdf["Urgency"] != "Responded"].copy()

        if pending_df.empty:
            st.success("🎉 All samples have responses — nothing pending!")
        else:
            # Sort by urgency priority then days desc
            urg_order = {"Critical":4,"Push Required":3,
                         "Initial Follow-up":2,"Freshly Handed":1}
            pending_df["_urg_sort"] = pending_df["Urgency"].map(urg_order).fillna(0)
            pending_df = pending_df.sort_values(
                ["_urg_sort","Days Since Handover"], ascending=[False,False]
            )

            st.caption(f"{len(pending_df)} samples need attention")

            for _, row in pending_df.iterrows():
                urg     = row["Urgency"]
                css_cls = {
                    "Critical":          "critical",
                    "Push Required":     "push",
                    "Initial Follow-up": "initial",
                    "Freshly Handed":    "fresh",
                }.get(urg, "fresh")

                ho_date  = row[COL_HO_DATE].strftime("%d %b %Y") \
                           if pd.notna(row.get(COL_HO_DATE)) else "—"
                days_ago = int(row["Days Since Handover"]) \
                           if pd.notna(row.get("Days Since Handover")) else 0

                # Feedback history
                fb_list = get_feedback_for_row(row, history)
                fb_html = ""
                if fb_list:
                    for fb in fb_list[:3]:
                        ts = fb["updated_at"][:10] if fb["updated_at"] else ""
                        fb_html += (
                            f'<div class="fb-history-item">'
                            f'<div class="fb-history-meta">'
                            f'📝 {fb["updated_by"]} · {ts}</div>'
                            f'{fb["feedback"]}'
                            f'</div>'
                        )

                st.markdown(f"""
                <div class="followup-row {css_cls}">
                    <div style="display:flex;justify-content:space-between;
                                align-items:flex-start;flex-wrap:wrap;gap:8px;">
                        <div class="followup-customer">
                            {row.get(COL_CUSTOMER,'—')}
                        </div>
                        {urgency_badge(urg)}
                    </div>
                    <div class="followup-meta" style="margin-top:5px;">
                        📦 {row.get(COL_SAMPLE_PROD,'—')} &nbsp;·&nbsp;
                        📍 {row.get(COL_BRANCH,'—')} — {row.get(COL_AREA,'—')} &nbsp;·&nbsp;
                        🤝 {row.get(COL_HO_BY,'—')} &nbsp;·&nbsp;
                        📅 Handed over: {ho_date} (<b>{days_ago} days ago</b>)
                    </div>
                    <div class="followup-meta">
                        👤 Contact: {row.get(COL_CONTACT,'—')}
                    </div>
                    {fb_html}
                </div>
                """, unsafe_allow_html=True)

            # Download
            from io import BytesIO
            dl_cols = [COL_BRANCH, COL_AREA, COL_CUSTOMER, COL_CONTACT,
                      COL_SAMPLE_PROD, COL_HO_DATE, COL_HO_BY,
                      "Days Since Handover", "Urgency"]
            dl_cols = [c for c in dl_cols if c in pending_df.columns]
            dl_df   = pending_df[dl_cols].copy()
            if COL_HO_DATE in dl_df.columns:
                dl_df[COL_HO_DATE] = dl_df[COL_HO_DATE].dt.strftime("%d %b %Y")
            buf = BytesIO()
            with pd.ExcelWriter(buf, engine="xlsxwriter") as writer:
                dl_df.to_excel(writer, index=False, sheet_name="Follow-ups")
                ws = writer.sheets["Follow-ups"]
                ws.set_column(0, len(dl_df.columns)-1, 22)
            st.download_button(
                "📥 Download Follow-up List", data=buf.getvalue(),
                file_name=f"Followup_{datetime.now().strftime('%d%b%Y')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    # ──────────────────────────────────────
    # TAB 4 — ALL SAMPLES
    # ──────────────────────────────────────
    with tab4:
        st.markdown('<div class="sd-section">All Sample Records</div>',
                   unsafe_allow_html=True)

        search = st.text_input(
            "🔍 Search", placeholder="Search customer, product, area...",
            key="sd_search", label_visibility="collapsed"
        )

        display_df = fdf.copy()
        if search:
            s = search.lower()
            mask = (
                display_df[COL_CUSTOMER].fillna("").str.lower().str.contains(s) |
                display_df[COL_SAMPLE_PROD].fillna("").str.lower().str.contains(s) |
                display_df[COL_AREA].fillna("").str.lower().str.contains(s) |
                display_df[COL_BRANCH].fillna("").str.lower().str.contains(s)
            )
            display_df = display_df[mask]

        st.caption(f"{len(display_df)} records")

        show_df = display_df.copy()
        for col in [COL_ENQ_DATE, COL_HO_DATE]:
            if col in show_df.columns:
                show_df[col] = show_df[col].dt.strftime("%d %b %Y").fillna("—")

        show_cols = [COL_BRANCH, COL_AREA, COL_CUSTOMER, COL_SAMPLE_PROD,
                    COL_QTY, COL_HO_DATE, COL_HO_BY,
                    "Latest Feedback", "Feedback Status", "Urgency",
                    "Days Since Handover"]
        show_cols = [c for c in show_cols if c in show_df.columns]

        st.dataframe(show_df[show_cols].reset_index(drop=True),
                    width='stretch', height=500)

        from io import BytesIO
        buf2 = BytesIO()
        with pd.ExcelWriter(buf2, engine="xlsxwriter") as writer:
            show_df[show_cols].to_excel(writer, index=False, sheet_name="Samples")
            ws = writer.sheets["Samples"]
            ws.set_column(0, len(show_cols)-1, 22)
        st.download_button(
            "📥 Download All Records", data=buf2.getvalue(),
            file_name=f"Samples_{datetime.now().strftime('%d%b%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )