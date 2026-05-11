import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from html import escape
from datetime import datetime

from load_data import master_df
from recommender import recommend, get_recommendations_by_category, get_rank_statistics

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="VIT Counselling Predictor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# =====================================================
# THEME
# =====================================================

theme_mode = st.sidebar.segmented_control(
    "Theme", ["Light", "Dark (Beta)"], default="Light", key="theme_mode",
)

THEMES = {
    "Light": {
        "bg": "#f0f4fa",
        "surface": "#ffffff",
        "input": "#ffffff",
        "text": "#0f172a",
        "muted": "#475569",
        "soft": "#64748b",
        "border": "#dde5f0",
        "primary": "#4f46e5",
        "primary_dark": "#3730a3",
        "header": "rgba(240,244,250,0.97)",
        "shadow": "0 8px 30px rgba(15,23,42,0.07)",
        "info_bg": "#eff6ff",
        "info_border": "#bfdbfe",
        "info_text": "#1e40af",
        "tag_bg": "#eef2ff",
        "tag_text": "#312e81",
        "grid": "#e2e8f0",
        "axis": "#cbd5e1",
        "legend_bg": "rgba(255,255,255,0.9)",
        "hover_bg": "#0f172a",
        "hover_text": "#ffffff",
        "bar_bg": "#e2e8f0",
        "chip_bg": "#f8fafc",
        "chip_good_bg": "#f0fdf4",
        "chip_good_text": "#15803d",
        "chip_warn_bg": "#fefce8",
        "chip_warn_text": "#a16207",
        "chip_risk_bg": "#fef2f2",
        "chip_risk_text": "#dc2626",
        "safe_color": "#16a34a",
        "moderate_color": "#d97706",
        "dream_color": "#dc2626",
        "badge_safe_bg": "#dcfce7",
        "badge_safe_text": "#14532d",
        "badge_moderate_bg": "#fef9c3",
        "badge_moderate_text": "#713f12",
        "badge_dream_bg": "#fee2e2",
        "badge_dream_text": "#7f1d1d",
        "safe_bg": "#f0fdf4",
        "safe_border": "#86efac",
        "safe_text": "#15803d",
        "moderate_bg": "#fefce8",
        "moderate_border": "#fde047",
        "moderate_text": "#854d0e",
        "dream_bg": "#fff1f2",
        "dream_border": "#fda4af",
        "dream_text": "#9f1239",
    },
    "Dark (Beta)": {
        "bg": "#0b1120",
        "surface": "#172033",
        "input": "#1e2d45",
        "text": "#f1f5f9",
        "muted": "#94a3b8",
        "soft": "#64748b",
        "border": "#2d4060",
        "primary": "#818cf8",
        "primary_dark": "#a5b4fc",
        "header": "rgba(11,17,32,0.97)",
        "shadow": "0 8px 30px rgba(0,0,0,0.35)",
        "info_bg": "#1e3a5f",
        "info_border": "#3b82f6",
        "info_text": "#dbeafe",
        "tag_bg": "#312e81",
        "tag_text": "#c7d2fe",
        "grid": "#1e3048",
        "axis": "#334155",
        "legend_bg": "rgba(23,32,51,0.95)",
        "hover_bg": "#f1f5f9",
        "hover_text": "#0f172a",
        "bar_bg": "#1e3048",
        "chip_bg": "#1a2a40",
        "chip_good_bg": "#052e16",
        "chip_good_text": "#4ade80",
        "chip_warn_bg": "#3b1e06",
        "chip_warn_text": "#fbbf24",
        "chip_risk_bg": "#3b0a0a",
        "chip_risk_text": "#f87171",
        "safe_color": "#4ade80",
        "moderate_color": "#fbbf24",
        "dream_color": "#f87171",
        "badge_safe_bg": "#14532d",
        "badge_safe_text": "#bbf7d0",
        "badge_moderate_bg": "#713f12",
        "badge_moderate_text": "#fef9c3",
        "badge_dream_bg": "#7f1d1d",
        "badge_dream_text": "#fecaca",
        "safe_bg": "#052e16",
        "safe_border": "#16a34a",
        "safe_text": "#bbf7d0",
        "moderate_bg": "#3b1e06",
        "moderate_border": "#d97706",
        "moderate_text": "#fef9c3",
        "dream_bg": "#3b0a0a",
        "dream_border": "#dc2626",
        "dream_text": "#fecaca",
    },
}
THEMES["Dark"] = THEMES["Dark (Beta)"]
theme = THEMES["Dark" if theme_mode == "Dark (Beta)" else theme_mode]

# =====================================================
# CSS
# =====================================================

st.markdown(f"""
<style>
    :root {{
        --vit-bg: {theme["bg"]};
        --vit-surface: {theme["surface"]};
        --vit-input: {theme["input"]};
        --vit-text: {theme["text"]};
        --vit-muted: {theme["muted"]};
        --vit-soft: {theme["soft"]};
        --vit-border: {theme["border"]};
        --vit-primary: {theme["primary"]};
        --vit-primary-dark: {theme["primary_dark"]};
        --vit-shadow: {theme["shadow"]};
        --vit-info-bg: {theme["info_bg"]};
        --vit-info-border: {theme["info_border"]};
        --vit-info-text: {theme["info_text"]};
        --vit-tag-bg: {theme["tag_bg"]};
        --vit-tag-text: {theme["tag_text"]};
        --vit-bar-bg: {theme["bar_bg"]};
        --vit-chip-bg: {theme["chip_bg"]};
        --vit-chip-good-bg: {theme["chip_good_bg"]};
        --vit-chip-good-text: {theme["chip_good_text"]};
        --vit-chip-warn-bg: {theme["chip_warn_bg"]};
        --vit-chip-warn-text: {theme["chip_warn_text"]};
        --vit-chip-risk-bg: {theme["chip_risk_bg"]};
        --vit-chip-risk-text: {theme["chip_risk_text"]};
        --vit-safe-color: {theme["safe_color"]};
        --vit-moderate-color: {theme["moderate_color"]};
        --vit-dream-color: {theme["dream_color"]};
        --vit-badge-safe-bg: {theme["badge_safe_bg"]};
        --vit-badge-safe-text: {theme["badge_safe_text"]};
        --vit-badge-moderate-bg: {theme["badge_moderate_bg"]};
        --vit-badge-moderate-text: {theme["badge_moderate_text"]};
        --vit-badge-dream-bg: {theme["badge_dream_bg"]};
        --vit-badge-dream-text: {theme["badge_dream_text"]};
        --safe-bg: {theme["safe_bg"]};
        --safe-border: {theme["safe_border"]};
        --safe-text: {theme["safe_text"]};
        --moderate-bg: {theme["moderate_bg"]};
        --moderate-border: {theme["moderate_border"]};
        --moderate-text: {theme["moderate_text"]};
        --dream-bg: {theme["dream_bg"]};
        --dream-border: {theme["dream_border"]};
        --dream-text: {theme["dream_text"]};
    }}

    /* ── App shell ── */
    .stApp, [data-testid="stMainBlockContainer"] {{
        background: var(--vit-bg) !important;
        color: var(--vit-text) !important;
    }}
    [data-testid="stMainBlockContainer"] {{
        padding-top: 2.5rem;
        max-width: 1560px;
    }}
    [data-testid="stHeader"] {{ background: {theme["header"]} !important; }}

    /* ── Sidebar ── */
    [data-testid="stSidebar"] {{
        background: var(--vit-surface) !important;
        border-right: 1px solid var(--vit-border);
    }}
    [data-testid="stSidebar"] > div:first-child {{ padding: 1.25rem 1rem; }}
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {{ color: var(--vit-text) !important; }}
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: var(--vit-muted) !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"] {{
        background: var(--vit-primary) !important;
        border-color: var(--vit-primary) !important;
        color: #ffffff !important;
        font-weight: 700;
    }}
    [data-testid="stSidebar"] button[kind="primary"] span {{ color: #ffffff !important; }}

    /* ── Form controls ── */
    [data-baseweb="input"],
    [data-baseweb="select"] > div,
    [data-baseweb="tag"],
    [data-baseweb="textarea"] {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    [data-baseweb="input"] input,
    [data-baseweb="select"] input,
    [data-baseweb="select"] span,
    [role="listbox"] li,
    [data-testid="stNumberInput"] input,
    [data-testid="stSelectbox"] span {{ color: var(--vit-text) !important; }}
    [data-testid="stNumberInput"] button {{
        background: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    [role="listbox"] {{
        background: var(--vit-surface) !important;
        border-color: var(--vit-border) !important;
    }}

    /* ── Multiselect tags ── */
    [data-baseweb="tag"] {{
        background-color: var(--vit-tag-bg) !important;
        color: var(--vit-tag-text) !important;
        padding: 5px 10px !important;
        margin: 3px !important;
        border-radius: 5px !important;
        white-space: normal !important;
        word-break: break-word !important;
        max-width: 100% !important;
        font-size: 0.82rem !important;
    }}
    [data-baseweb="tag"] span,
    [data-baseweb="tag"] * {{ color: var(--vit-tag-text) !important; fill: var(--vit-tag-text) !important; }}

    /* ── Page header ── */
    .vit-header {{
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 1.5rem 1.75rem;
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 12px;
        margin-bottom: 1.25rem;
        box-shadow: var(--vit-shadow);
    }}
    .vit-header-icon {{
        width: 54px; height: 54px;
        background: var(--vit-primary);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.65rem; flex-shrink: 0;
    }}
    .vit-header h1 {{ margin: 0; font-size: 1.65rem; font-weight: 800; color: var(--vit-text); }}
    .vit-header p  {{ margin: 0.25rem 0 0; font-size: 0.95rem; color: var(--vit-muted); }}

    /* ── Info strip ── */
    .info-strip {{
        background: var(--vit-info-bg);
        border: 1px solid var(--vit-info-border);
        border-radius: 10px;
        padding: 0.85rem 1.1rem;
        font-size: 0.93rem;
        color: var(--vit-info-text);
        margin-bottom: 1.5rem;
    }}

    /* ── Section heading ── */
    .section-heading {{
        font-size: 0.85rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.06em;
        color: var(--vit-soft);
        margin: 1.75rem 0 0.75rem;
    }}

    /* ── Result card ── */
    .result-row {{
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-left: 5px solid var(--vit-border);
        border-radius: 10px;
        padding: 1.35rem 1.5rem;
        margin-bottom: 1rem;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 180px;
        gap: 1.25rem;
        box-shadow: var(--vit-shadow);
        transition: box-shadow 0.15s;
    }}
    .result-row:hover {{ box-shadow: 0 12px 36px rgba(15,23,42,0.10); }}
    .result-row.safe     {{ border-left-color: var(--vit-safe-color); }}
    .result-row.moderate {{ border-left-color: var(--vit-moderate-color); }}
    .result-row.dream    {{ border-left-color: var(--vit-dream-color); }}
    .result-row.unlikely {{ border-left-color: var(--vit-soft); }}

    /* ── Card header ── */
    .result-topline {{
        display: flex;
        align-items: center;
        gap: 0.65rem;
        flex-wrap: wrap;
        margin-bottom: 0.9rem;
    }}
    .result-branch {{
        font-size: 1.2rem;
        font-weight: 800;
        color: var(--vit-text);
        line-height: 1.2;
    }}

    /* ── Chip row ── */
    .chip-row {{
        display: flex;
        flex-wrap: wrap;
        gap: 0.55rem;
        margin-bottom: 1rem;
    }}

    /* ── Individual chip ── */
    .chip {{
        display: inline-flex;
        flex-direction: column;
        gap: 2px;
        padding: 0.45rem 0.75rem;
        border: 1px solid var(--vit-border);
        border-radius: 8px;
        background: var(--vit-chip-bg);
        min-width: 90px;
    }}
    .chip-label {{
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--vit-soft);
    }}
    .chip-value {{
        font-size: 1rem;
        font-weight: 800;
        color: var(--vit-text);
        line-height: 1.2;
    }}
    .chip-sub {{
        font-size: 0.75rem;
        color: var(--vit-muted);
        line-height: 1.2;
    }}
    .chip.good {{
        border-color: var(--vit-safe-color);
        background: var(--vit-chip-good-bg);
    }}
    .chip.good .chip-label,
    .chip.good .chip-sub {{ color: var(--vit-chip-good-text); opacity: 0.85; }}
    .chip.good .chip-value {{ color: var(--vit-chip-good-text); }}
    .chip.warn {{
        border-color: var(--vit-moderate-color);
        background: var(--vit-chip-warn-bg);
    }}
    .chip.warn .chip-label,
    .chip.warn .chip-sub {{ color: var(--vit-chip-warn-text); opacity: 0.85; }}
    .chip.warn .chip-value {{ color: var(--vit-chip-warn-text); }}
    .chip.risk {{
        border-color: var(--vit-dream-color);
        background: var(--vit-chip-risk-bg);
    }}
    .chip.risk .chip-label,
    .chip.risk .chip-sub {{ color: var(--vit-chip-risk-text); opacity: 0.85; }}
    .chip.risk .chip-value {{ color: var(--vit-chip-risk-text); }}

    /* ── Why note ── */
    .result-note {{
        font-size: 0.88rem;
        color: var(--vit-muted);
        line-height: 1.5;
        padding: 0.55rem 0.8rem;
        border-left: 3px solid var(--vit-border);
        background: rgba(100,116,139,0.06);
        border-radius: 0 6px 6px 0;
    }}
    .result-note strong {{ color: var(--vit-text); }}

    /* ── Probability panel ── */
    .prob-panel {{
        border-left: 1px solid var(--vit-border);
        padding-left: 1.25rem;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        gap: 6px;
    }}
    .prob-number {{
        font-size: 2.4rem;
        font-weight: 800;
        line-height: 1;
        letter-spacing: -1px;
    }}
    .prob-number.safe     {{ color: var(--vit-safe-color); }}
    .prob-number.moderate {{ color: var(--vit-moderate-color); }}
    .prob-number.dream    {{ color: var(--vit-dream-color); }}
    .prob-number.unlikely {{ color: var(--vit-soft); }}
    .prob-label {{
        font-size: 0.82rem;
        color: var(--vit-muted);
        text-align: right;
        font-weight: 600;
    }}
    .prob-bar-bg {{
        height: 6px;
        background: var(--vit-bar-bg);
        border-radius: 3px;
        overflow: hidden;
        min-width: 130px;
        margin-top: 2px;
    }}
    .prob-bar-fill {{ height: 100%; border-radius: 3px; }}
    .score-label {{ font-size: 0.72rem; color: var(--vit-soft); text-align: right; }}
    .cutoff-note {{
        font-size: 0.75rem;
        color: var(--vit-muted);
        text-align: right;
        margin-top: 2px;
    }}

    /* ── Badge ── */
    .badge {{
        display: inline-block;
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 10px;
        border-radius: 99px;
        letter-spacing: 0.02em;
    }}
    .badge-safe     {{ background: var(--vit-badge-safe-bg);     color: var(--vit-badge-safe-text); }}
    .badge-moderate {{ background: var(--vit-badge-moderate-bg); color: var(--vit-badge-moderate-text); }}
    .badge-dream    {{ background: var(--vit-badge-dream-bg);    color: var(--vit-badge-dream-text); }}
    .badge-unlikely {{ background: var(--vit-chip-bg); color: var(--vit-muted); border: 1px solid var(--vit-border); }}

    /* ── Metric cards ── */
    .metric-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.5rem;
    }}
    .metric-card {{
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        min-height: 110px;
        box-shadow: var(--vit-shadow);
    }}
    .metric-card-label {{
        font-size: 0.76rem;
        color: var(--vit-soft);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
    }}
    .metric-card-value {{
        font-size: 1.95rem;
        font-weight: 800;
        color: var(--vit-text);
        margin: 6px 0 3px;
        line-height: 1;
    }}
    .metric-card-sub   {{ font-size: 0.83rem; color: var(--vit-muted); }}
    .metric-card-sub.green {{ color: var(--vit-safe-color); font-weight: 600; }}

    /* ── Context banner ── */
    .context-banner {{
        border: 1px solid var(--vit-border);
        border-radius: 10px;
        padding: 0.8rem 1.1rem;
        font-size: 0.9rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
    }}
    .context-banner.safe     {{ background: var(--safe-bg);     border-color: var(--safe-border);     color: var(--safe-text); }}
    .context-banner.moderate {{ background: var(--moderate-bg); border-color: var(--moderate-border); color: var(--moderate-text); }}
    .context-banner.dream    {{ background: var(--dream-bg);    border-color: var(--dream-border);    color: var(--dream-text); }}

    /* ── Rank display ── */
    .rank-big {{
        font-size: 2.1rem;
        font-weight: 800;
        color: var(--vit-primary);
        line-height: 1;
        margin: 6px 0 2px;
    }}

    /* ── Streamlit native overrides ── */
    h1, h2, h3, h4, h5, h6, p, label, span, div {{ color: inherit; }}
    div[data-testid="stMetric"] {{
        background: var(--vit-surface) !important;
        border: 1px solid var(--vit-border) !important;
        border-radius: 10px;
        padding: 0.9rem 1rem;
    }}
    .stAlert, [data-testid="stAlert"] {{
        background: var(--vit-info-bg) !important;
        border-color: var(--vit-info-border) !important;
        color: var(--vit-info-text) !important;
        border-radius: 10px;
    }}
    div[data-testid="stTabs"] [data-baseweb="tab"] {{
        font-size: 0.92rem;
        padding: 8px 18px;
        border-radius: 6px;
        color: var(--vit-muted);
        font-weight: 650;
    }}
    div[data-testid="stTabs"] [aria-selected="true"] {{ color: var(--vit-primary-dark) !important; }}
    [data-testid="stSegmentedControl"] label[aria-checked="true"],
    [data-testid="stSegmentedControl"] label[data-checked="true"] {{
        background: var(--vit-primary) !important;
    }}
    [data-testid="stSegmentedControl"] div[role="radiogroup"] {{
        background: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stSegmentedControl"] label {{ color: var(--vit-text) !important; }}
    [data-testid="stCaptionContainer"] p {{ color: var(--vit-muted) !important; }}
    .footer-note {{ color: var(--vit-muted) !important; }}

    /* ── Responsive ── */
    @media (max-width: 900px) {{
        [data-testid="stMainBlockContainer"] {{ padding: 1.25rem 1rem; }}
        .metric-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .result-row {{ grid-template-columns: 1fr; }}
        .prob-panel {{
            align-items: flex-start;
            border-left: none;
            border-top: 1px solid var(--vit-border);
            padding-left: 0;
            padding-top: 1rem;
        }}
        .prob-bar-bg {{ width: 100%; }}
        .prob-label, .score-label, .cutoff-note {{ text-align: left; }}
    }}
</style>
""", unsafe_allow_html=True)

# =====================================================
# PAGE HEADER
# =====================================================

st.markdown("""
<div class="vit-header">
    <div class="vit-header-icon">🎓</div>
    <div>
        <h1>VIT Counselling Predictor</h1>
        <p>Powered by real student data &nbsp;·&nbsp; Percentile-calibrated admission probability</p>
    </div>
</div>
<div class="info-strip">
    ℹ️ Enter your VITEEE rank on the left, apply filters, and click <strong>Get Recommendations</strong>
    to see your personalised predictions. The predictor uses a <strong>90th-percentile cutoff model</strong>
    so outlier ranks don't inflate estimates.
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.markdown("### ⚙️ Settings")

rank = st.sidebar.number_input(
    "Your VITEEE rank",
    min_value=1, max_value=250000, step=1, value=5000,
    help="Enter your VITEEE counselling rank (up to 2.5 lakh)"
)
st.sidebar.markdown(
    f'<div class="rank-big">{rank:,}</div>'
    f'<div style="font-size:0.8rem;color:var(--vit-muted);margin-bottom:0.85rem;">rank entered</div>',
    unsafe_allow_html=True
)


sort_option = st.sidebar.selectbox(
    "Sort results by",
    ["Recommended", "Probability", "Fee Category", "Confidence Level", "Number of Responses", "Closing Rank"],
)
sort_mapping = {
    "Recommended": "recommended",
    "Probability": "probability",
    "Fee Category": "fee",
    "Confidence Level": "confidence",
    "Number of Responses": "responses",
    "Closing Rank": "closing_rank",
}

# Add radio for probability order
prob_order = "desc"
if sort_option == "Probability":
    prob_order = st.sidebar.radio(
        "Order",
        ["High to Low (default)", "Low to High (riskier first)"],
        index=0,
        help="Choose 'Low to High' to see riskier options first."
    )

results_limit = st.sidebar.slider("Max results per category", min_value=5, max_value=30, value=10, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

branch_filter = st.sidebar.segmented_control(
    "Quick branch filter",
    ["All", "CSE", "ECE+EEE"],
    default="All",
    key="branch_filter"
)

cse_programs = ["CSE Core", "CSE AIML", "CSE DS", "CSE Cybersecurity",
                "CSE Business Systems", "CSE Robotics", "CSE IoT", "CSE CPS"]
ece_eee_programs = ["ECE Core", "Electrical"]

all_campuses = sorted(master_df["Campus"].unique().tolist())
selected_campuses = st.sidebar.multiselect("Campus", all_campuses, default=all_campuses)

all_branches = sorted(master_df["Branch"].unique().tolist())
if branch_filter == "CSE":
    default_branches = [b for b in all_branches if b in cse_programs]
elif branch_filter == "ECE+EEE":
    default_branches = [b for b in all_branches if b in ece_eee_programs]
else:
    default_branches = all_branches

selected_branches = st.sidebar.multiselect(
    "Branch", all_branches, default=default_branches
)

all_fees = sorted(master_df["Fee"].unique().tolist())
selected_fees = st.sidebar.multiselect(
    "Fee category",
    [str(int(f)) for f in all_fees],
    default=[str(int(f)) for f in all_fees],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 Share Your Data")
st.sidebar.markdown("**Help improve predictions by sharing your counselling results**")

col1, col2 = st.sidebar.columns(2)
with col1:
    st.link_button("📋 Submit 2025", "https://forms.gle/VG28i72zpKetFA4W6", width="stretch")
with col2:
    st.info("Share your rank & allotment", icon="ℹ️")

st.sidebar.markdown("---")

predict_button = st.sidebar.button(
    "🚀 Get Recommendations",
    width="stretch", type="primary", key="predict_btn"
)

# =====================================================
# HELPER FUNCTIONS
# =====================================================

def prob_bar(prob, kind):
    colors = {
        "safe": theme["safe_color"],
        "moderate": theme["moderate_color"],
        "dream": theme["dream_color"],
        "unlikely": theme["soft"],
    }
    c = colors.get(kind, "#9ca3af")
    return (
        f'<div class="prob-bar-bg">'
        f'<div class="prob-bar-fill" style="width:{min(prob,100):.1f}%;background:{c};"></div>'
        f'</div>'
    )


def confidence_clean(label):
    return label.replace(" 🟢", "").replace(" 🟡", "").replace(" 🔴", "")


def chip_class_from_buffer(diff):
    if diff >= 5000:
        return "good"
    if diff >= 0:
        return "warn"
    return "risk"


def chip_class_from_confidence(pct):
    if pct >= 70:
        return "good"
    if pct >= 40:
        return "warn"
    return "risk"


def recommendation_reason(r):
    diff = r["rank_difference"]
    chance = r["chance"]
    sd = r.get("std_dev", 0)
    sd_note = f" (±{sd:,} rank spread observed)" if sd > 3000 else ""
    if chance == "Safe":
        if diff >= 10000:
            return f"Large rank cushion of <strong>{diff:,}</strong> ranks. Very strong primary choice{sd_note}."
        if diff >= 3000:
            return f"Comfortable buffer of <strong>{diff:,}</strong> ranks. Good primary pick{sd_note}."
        return f"Inside the cutoff with a <strong>{diff:,}</strong> rank buffer{sd_note}. Keep 1–2 backups."
    if chance == "Moderate":
        if diff >= 0:
            return f"Within the cutoff but margin is narrow (<strong>{diff:,}</strong> ranks){sd_note}. Solid backup."
        return f"Slightly beyond the observed cutoff by <strong>{abs(diff):,}</strong> ranks{sd_note}. Backup only."
    if chance == "Dream":
        return f"Outside the cutoff by <strong>{abs(diff):,}</strong> ranks. List last if at all{sd_note}."
    return f"Far outside the cutoff ({abs(diff):,} ranks). Not recommended{sd_note}."


def result_row_html(r, rank, kind):
    diff = r["rank_difference"]
    sign = "+" if diff >= 0 else "−"
    margin_label = f"{sign}{abs(diff):,}"
    margin_sub = "buffer ✓" if diff >= 0 else "shortfall ✗"

    badge_map  = {"safe": "badge-safe", "moderate": "badge-moderate",
                  "dream": "badge-dream", "unlikely": "badge-unlikely"}
    badge_text = {"safe": "Safe ✓", "moderate": "Moderate", "dream": "Reach", "unlikely": "Very Unlikely"}
    badge_html = f'<span class="badge {badge_map[kind]}">{badge_text[kind]}</span>'

    conf_label = confidence_clean(r["confidence"])
    conf_class = chip_class_from_confidence(r["confidence_pct"])
    buf_class  = chip_class_from_buffer(diff)

    reason = recommendation_reason(r)
    branch = escape(r["branch"])
    campus = escape(r["campus"])
    sd_val = r.get("std_dev", 0)

    # Build spread chip separately — never inline conditionals inside f-strings
    if sd_val > 1500:
        spread_chip = (
            '<div class="chip warn">'
            '<span class="chip-label">Spread</span>'
            f'<span class="chip-value">&#177;{sd_val:,}</span>'
            '<span class="chip-sub">rank std dev</span>'
            '</div>'
        )
    else:
        spread_chip = ""

    true_max = r.get("true_max", r["closing_rank"])
    prob_bar_html = prob_bar(r["probability"], kind)
    badge_label = badge_text[kind]

    return (
        f'<div class="result-row {kind}">'
        f'<div style="min-width:0;">'
        f'<div class="result-topline">'
        f'<span class="result-branch">{branch}</span>'
        f'{badge_html}'
        f'</div>'
        f'<div class="chip-row">'
        f'<div class="chip"><span class="chip-label">Campus</span><span class="chip-value">{campus}</span></div>'
        f'<div class="chip"><span class="chip-label">Fee Cat.</span><span class="chip-value">{r["fee"]}</span></div>'
        f'<div class="chip"><span class="chip-label">Cutoff Rank</span><span class="chip-value">{r["closing_rank"]:,}</span><span class="chip-sub">90th pct &#183; true max {true_max:,}</span></div>'
        f'<div class="chip {buf_class}"><span class="chip-label">Rank Margin</span><span class="chip-value">{margin_label}</span><span class="chip-sub">{margin_sub}</span></div>'
        f'<div class="chip {conf_class}"><span class="chip-label">Confidence</span><span class="chip-value">{conf_label}</span><span class="chip-sub">{r["responses"]} responses</span></div>'
        f'{spread_chip}'
        f'</div>'
        f'<div class="result-note">{reason}</div>'
        f'</div>'
        f'<div class="prob-panel">'
        f'<div class="prob-number {kind}">{r["probability"]:.0f}%</div>'
        f'<div class="prob-label">{badge_label} chance</div>'
        f'{prob_bar_html}'
        f'<div class="cutoff-note">cutoff {r["closing_rank"]:,}</div>'
        f'<div class="score-label">score {r["recommendation_score"]:.1f}</div>'
        f'</div>'
        f'</div>'
    )


def section_header(icon, title, count):
    st.markdown(
        f'<div class="section-heading">{icon} {title} &nbsp;·&nbsp; {count} option{"s" if count != 1 else ""}</div>',
        unsafe_allow_html=True
    )

# =====================================================
# RESULTS
# =====================================================

if predict_button:
    if sort_option == "Probability":
        if prob_order == "Low to High (riskier first)":
            all_results = recommend(rank, sort_by="probability_asc")
        else:
            all_results = recommend(rank, sort_by="probability")
    else:
        all_results = recommend(rank, sort_by=sort_mapping[sort_option])
    selected_fees_int = [int(f) for f in selected_fees]

    filtered_results = [
        r for r in all_results
        if r["campus"] in selected_campuses
        and r["branch"] in selected_branches
        and r["fee"] in selected_fees_int
    ]

    if not filtered_results:
        st.markdown(
            '<div class="context-banner dream">'
            'No options match your filters. Try selecting more campuses, branches, or fee categories.'
            '</div>', unsafe_allow_html=True
        )
    else:
        rank_stats = get_rank_statistics(rank)
        safe_list     = [r for r in filtered_results if r["chance"] == "Safe"]
        moderate_list = [r for r in filtered_results if r["chance"] == "Moderate"]
        dream_list    = [r for r in filtered_results if r["chance"] == "Dream"]
        unlikely_list = [r for r in filtered_results if r["chance"] == "Very Unlikely"]
        avg_prob = sum(r["probability"] for r in filtered_results) / len(filtered_results)

        # ── Metrics ──────────────────────────────────────────
        st.markdown(f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-card-label">Your rank</div>
                <div class="metric-card-value">{rank:,}</div>
                <div class="metric-card-sub">Top {rank_stats['percentile']:.1f}% of candidates</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Total options</div>
                <div class="metric-card-value">{len(filtered_results)}</div>
                <div class="metric-card-sub">of {rank_stats['total_options']} overall</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Safe options</div>
                <div class="metric-card-value">{len(safe_list)}</div>
                <div class="metric-card-sub {'green' if safe_list else ''}">{"High probability seats" if safe_list else "None in current filters"}</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Avg probability</div>
                <div class="metric-card-value">{avg_prob:.1f}%</div>
                <div class="metric-card-sub">across all filtered options</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        # ── Safe ─────────────────────────────────────────────
        if safe_list:
            section_header("✅", "Primary picks — strong rank fit", len(safe_list))
            st.markdown(
                '<div class="context-banner safe">Your rank sits comfortably inside these cutoffs. Prioritise by campus preference and fee category.</div>',
                unsafe_allow_html=True
            )
            for r in safe_list[:results_limit]:
                st.markdown(result_row_html(r, rank, "safe"), unsafe_allow_html=True)

        # ── Moderate ─────────────────────────────────────────
        if moderate_list:
            section_header("⚡", "Backup picks — possible but tighter", len(moderate_list))
            st.markdown(
                '<div class="context-banner moderate">These are within reach but have a narrow buffer, high spread, or limited data. Good backups.</div>',
                unsafe_allow_html=True
            )
            for r in moderate_list[:results_limit]:
                st.markdown(result_row_html(r, rank, "moderate"), unsafe_allow_html=True)

        # ── Dream ────────────────────────────────────────────
        if dream_list:
            section_header("🔥", "Reach picks — low probability", len(dream_list))
            st.markdown(
                '<div class="context-banner dream">Outside or near the observed cutoff. Add sparingly — list these last in your preference order.</div>',
                unsafe_allow_html=True
            )
            for r in dream_list[:results_limit]:
                st.markdown(result_row_html(r, rank, "dream"), unsafe_allow_html=True)

        # ── Very Unlikely ─────────────────────────────────────
        if not safe_list and not moderate_list and not dream_list:
            section_header("⛔", "No viable options for these filters", len(unlikely_list))
            st.markdown(
                '<div class="context-banner dream">Your rank is far outside observed cutoffs. Broaden your campus, branch, or fee selection.</div>',
                unsafe_allow_html=True
            )
            for r in unlikely_list[:results_limit]:
                st.markdown(result_row_html(r, rank, "unlikely"), unsafe_allow_html=True)
        elif unlikely_list:
            section_header("⛔", "Not recommended", len(unlikely_list))
            st.markdown(
                '<div class="context-banner dream">These match your filters but are well outside the observed cutoff. For awareness only.</div>',
                unsafe_allow_html=True
            )
            for r in unlikely_list[:min(results_limit, 5)]:
                st.markdown(result_row_html(r, rank, "unlikely"), unsafe_allow_html=True)

# =====================================================
# DATASET ANALYTICS
# =====================================================

st.markdown("---")
st.markdown('<div class="section-heading">📊 Dataset statistics</div>', unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)
with col1: st.metric("Total responses",   len(master_df))
with col2: st.metric("Best rank",         f"{int(master_df['Rank'].min()):,}")
with col3: st.metric("Worst rank",        f"{int(master_df['Rank'].max()):,}")
with col4: st.metric("Unique variations", len(master_df[["Campus", "Branch", "Fee"]].drop_duplicates()))

CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Arial, sans-serif", size=13, color=theme["text"]),
    title=dict(font=dict(size=17, color=theme["text"]), x=0.02, xanchor="left"),
    margin=dict(t=58, b=48, l=20, r=24),
    height=430,
    hoverlabel=dict(bgcolor=theme["hover_bg"], font_size=13, font_color=theme["hover_text"]),
)


def readable_count_series(series, limit=12):
    counts = series.value_counts()
    if len(counts) <= limit:
        return counts
    visible = counts.head(limit - 1)
    visible.loc["Other"] = counts.iloc[limit - 1:].sum()
    return visible


def style_chart(fig, *, showlegend=False):
    fig.update_layout(
        **CHART_THEME, showlegend=showlegend,
        legend=dict(font=dict(size=12, color=theme["text"]), bgcolor=theme["legend_bg"],
                    bordercolor=theme["border"], borderwidth=1),
        xaxis=dict(title_font=dict(color=theme["text"], size=13),
                   tickfont=dict(color=theme["muted"], size=12),
                   gridcolor=theme["grid"], zerolinecolor=theme["axis"], linecolor=theme["axis"]),
        yaxis=dict(title_font=dict(color=theme["text"], size=13),
                   tickfont=dict(color=theme["muted"], size=12),
                   gridcolor=theme["grid"], zerolinecolor=theme["axis"], linecolor=theme["axis"]),
    )
    return fig


def style_pie(fig):
    style_chart(fig, showlegend=True)
    fig.update_traces(
        textposition="inside",
        textinfo="percent+label",
        textfont=dict(color="#ffffff", size=12),
        marker=dict(line=dict(color="#ffffff", width=2)),
        hovertemplate="<b>%{label}</b><br>%{value} responses<br>%{percent}<extra></extra>",
    )
    return fig


tab1, tab2, tab3, tab4 = st.tabs(["Branch", "Campus", "Fee category", "Raw data"])

with tab1:
    c1, c2 = st.columns(2)
    branch_counts = readable_count_series(master_df["Branch"], limit=14)
    with c1:
        fig = px.bar(x=branch_counts.values, y=branch_counts.index, orientation="h",
                     labels={"x": "Responses", "y": "Branch"}, title="Top branches by responses",
                     color=branch_counts.values,
                     color_continuous_scale=["#c7d2fe", "#4f46e5", "#1e1b4b"])
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        style_chart(fig)
        fig.update_traces(marker_line_width=0, text=branch_counts.values,
                          textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(values=branch_counts.values, names=branch_counts.index,
                     title="Branch share", color_discrete_sequence=px.colors.qualitative.Safe)
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab2:
    c1, c2 = st.columns(2)
    campus_counts = master_df["Campus"].value_counts()
    with c1:
        fig = px.bar(x=campus_counts.index, y=campus_counts.values,
                     labels={"x": "Campus", "y": "Responses"}, title="Responses by campus",
                     color=campus_counts.values,
                     color_continuous_scale=["#bae6fd", "#0284c7", "#0c4a6e"])
        fig.update_layout(coloraxis_showscale=False)
        style_chart(fig)
        fig.update_traces(marker_line_width=0, text=campus_counts.values,
                          textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(values=campus_counts.values, names=campus_counts.index,
                     title="Share by campus", color_discrete_sequence=px.colors.qualitative.Bold)
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab3:
    c1, c2 = st.columns(2)
    fee_counts = master_df["Fee"].value_counts().sort_index()
    fee_labels = ["Category " + str(int(f)) for f in fee_counts.index]
    with c1:
        fig = px.bar(x=fee_labels, y=fee_counts.values,
                     labels={"x": "Fee category", "y": "Students"}, title="Students by fee category",
                     color=fee_counts.values,
                     color_continuous_scale=["#bbf7d0", "#16a34a", "#14532d"])
        fig.update_layout(coloraxis_showscale=False)
        style_chart(fig)
        fig.update_traces(marker_line_width=0, text=fee_counts.values,
                          textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(values=fee_counts.values, names=fee_labels,
                     title="Share by fee category", color_discrete_sequence=px.colors.qualitative.Pastel)
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab4:
    c1, c2 = st.columns([0.7, 0.3])
    with c1:
        search_branch = st.selectbox("Filter by branch", ["All"] + sorted(master_df["Branch"].unique().tolist()))
    with c2:
        display_count = st.slider("Rows to show", min_value=10, max_value=100, value=20, step=10)
    display_df = master_df if search_branch == "All" else master_df[master_df["Branch"] == search_branch]
    st.dataframe(
        display_df.head(display_count), width="stretch", height=400,
        column_config={
            "Rank": st.column_config.NumberColumn(format="%d"),
            "Fee":  st.column_config.NumberColumn(format="Category %d"),
        }
    )
    st.caption(f"Showing {min(display_count, len(display_df)):,} of {len(display_df):,} records")

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1: st.info(f"📊 Data updated: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
with c2: st.info(f"📌 {len(master_df):,} student records")
with c3: st.info("🔄 Accuracy improves with more responses")

st.markdown("""
<div class="footer-note" style="font-size:0.84rem;margin-top:1rem;line-height:1.8;">
<strong>How to read the results</strong><br>
<b>Safe (75%+)</b> — Very likely to get a seat. These should be your primary choices.<br>
<b>Moderate (40–75%)</b> — Possible but not guaranteed. Use as backups.<br>
<b>Reach (15–40%)</b> — Unlikely. Include only as last-resort options.<br><br>
<strong>About the model</strong><br>
Closing ranks use the <strong>90th percentile</strong> of observed data (not the maximum) so a single outlier doesn't inflate the cutoff. Standard deviation of observed ranks is factored in — options with volatile historical cutoffs receive lower probabilities. Both the historical Excel dataset and live Google Form responses are merged and deduplicated before analysis.<br><br>
<strong style="color:#e11d48;">Disclaimer</strong>: <em>This tool is <u>unofficial</u> and not affiliated with VIT or any official counselling authority. All predictions are based on historical data and statistical models, and may not reflect actual results. The recommendations are for informational purposes only and are not perfect or guaranteed. Always verify with official VIT counselling resources before making any final decisions. Use at your own discretion.</em>
</div>
""", unsafe_allow_html=True)