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
# CUSTOM CSS
# =====================================================

theme_mode = st.sidebar.segmented_control(
    "Theme",
    ["Light", "Dark"],
    default="Light",
    key="theme_mode",
)

THEMES = {
    "Light": {
        "bg": "#f3f6fb",
        "surface": "#ffffff",
        "input": "#ffffff",
        "text": "#111827",
        "muted": "#4b5563",
        "soft": "#6b7280",
        "border": "#d9e2ef",
        "primary": "#4f46e5",
        "primary_dark": "#3730a3",
        "header": "rgba(243, 246, 251, 0.96)",
        "shadow": "0 10px 28px rgba(15, 23, 42, 0.05)",
        "info_bg": "#e8f1ff",
        "info_border": "#93c5fd",
        "info_text": "#173b8f",
        "tag_bg": "#eef2ff",
        "tag_text": "#312e81",
        "grid": "#e2e8f0",
        "axis": "#cbd5e1",
        "legend_bg": "rgba(255,255,255,0.86)",
        "hover_bg": "#111827",
        "hover_text": "#ffffff",
        "bar_bg": "#e5e7eb",
        "chip_bg": "#f8fafc",
        "chip_good_bg": "#ecfdf5",
        "chip_good_text": "#047857",
        "chip_warn_bg": "#fffbeb",
        "chip_warn_text": "#b45309",
        "chip_risk_bg": "#fef2f2",
        "chip_risk_text": "#dc2626",
        "safe_color": "#059669",
        "moderate_color": "#d97706",
        "dream_color": "#dc2626",
        "badge_safe_bg": "#d1fae5",
        "badge_safe_text": "#065f46",
        "badge_moderate_bg": "#fef3c7",
        "badge_moderate_text": "#78350f",
        "badge_dream_bg": "#fee2e2",
        "badge_dream_text": "#7f1d1d",
        "safe_bg": "#f0fdf4",
        "safe_border": "#bbf7d0",
        "safe_text": "#166534",
        "moderate_bg": "#fffbeb",
        "moderate_border": "#fde68a",
        "moderate_text": "#92400e",
        "dream_bg": "#fef2f2",
        "dream_border": "#fecaca",
        "dream_text": "#7f1d1d",
    },
    "Dark": {
        "bg": "#0b1120",
        "surface": "#172033",
        "input": "#243047",
        "text": "#f8fafc",
        "muted": "#d6e0f0",
        "soft": "#a9b8ce",
        "border": "#465875",
        "primary": "#a5b4fc",
        "primary_dark": "#c4b5fd",
        "header": "rgba(11, 17, 32, 0.96)",
        "shadow": "0 18px 40px rgba(0, 0, 0, 0.28)",
        "info_bg": "#1e3a8a",
        "info_border": "#60a5fa",
        "info_text": "#eff6ff",
        "tag_bg": "#3730a3",
        "tag_text": "#ffffff",
        "grid": "#3c4d68",
        "axis": "#64748b",
        "legend_bg": "rgba(23,32,51,0.94)",
        "hover_bg": "#f8fafc",
        "hover_text": "#0f172a",
        "bar_bg": "#3f506a",
        "chip_bg": "#223049",
        "chip_good_bg": "#073b2a",
        "chip_good_text": "#6ee7b7",
        "chip_warn_bg": "#4a2f0a",
        "chip_warn_text": "#fcd34d",
        "chip_risk_bg": "#4a1515",
        "chip_risk_text": "#fca5a5",
        "safe_color": "#34d399",
        "moderate_color": "#fbbf24",
        "dream_color": "#fb7185",
        "badge_safe_bg": "#065f46",
        "badge_safe_text": "#d1fae5",
        "badge_moderate_bg": "#92400e",
        "badge_moderate_text": "#fef3c7",
        "badge_dream_bg": "#991b1b",
        "badge_dream_text": "#fee2e2",
        "safe_bg": "#0b3b2a",
        "safe_border": "#10b981",
        "safe_text": "#d1fae5",
        "moderate_bg": "#4a2f0a",
        "moderate_border": "#f59e0b",
        "moderate_text": "#fef3c7",
        "dream_bg": "#4a1515",
        "dream_border": "#fb7185",
        "dream_text": "#ffe4e6",
    },
}
theme = THEMES[theme_mode]

st.markdown("""
<style>
    /* Reset & base */
    :root {
        --vit-bg: #f3f6fb;
        --vit-surface: #ffffff;
        --vit-text: #111827;
        --vit-muted: #4b5563;
        --vit-soft: #6b7280;
        --vit-border: #d9e2ef;
        --vit-primary: #4f46e5;
        --vit-primary-dark: #3730a3;
    }
    .stApp { background: var(--vit-bg); color: var(--vit-text); }
    [data-testid="stMainBlockContainer"] {
        background: var(--vit-bg);
        padding-top: 3rem;
        max-width: 1540px;
    }
    [data-testid="stHeader"] { background: rgba(243, 246, 251, 0.96); }
    [data-testid="stToolbar"] { color: var(--vit-text); }
    [data-testid="stSidebar"] {
        background: var(--vit-surface) !important;
        border-right: 1px solid var(--vit-border);
    }
    [data-testid="stSidebar"] > div:first-child { padding: 1.25rem 1rem; }
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {
        color: var(--vit-text) !important;
    }
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {
        color: var(--vit-muted) !important;
    }
    [data-baseweb="input"],
    [data-baseweb="select"] > div,
    [data-baseweb="tag"] {
        background-color: #ffffff !important;
        border-color: #cbd5e1 !important;
        color: var(--vit-text) !important;
    }
    [data-baseweb="input"] input,
    [data-baseweb="select"] input,
    [data-baseweb="select"] span,
    [role="listbox"] li {
        color: var(--vit-text) !important;
    }
    /* Multiselect tag improvements */
    [data-baseweb="tag"] {
        background-color: #eef2ff !important;
        color: #312e81 !important;
        padding: 4px 8px !important;
        margin: 2px !important;
        border-radius: 4px !important;
        white-space: normal !important;
        word-break: break-word !important;
        max-width: 100% !important;
    }
    [data-baseweb="tag"] span { 
        color: #312e81 !important;
        word-break: break-word !important;
        overflow: visible !important;
    }
    /* Fix multiselect container height */
    [data-baseweb="select"].stMultiSelect [data-baseweb="base-select"],
    [data-baseweb="select"] {
        min-height: auto !important;
        flex-wrap: wrap !important;
    }
    [data-testid="stMultiSelect"] {
        min-height: auto !important;
    }
    [data-testid="stSidebar"] button[kind="primary"] {
        background: var(--vit-primary) !important;
        border-color: var(--vit-primary) !important;
        color: #ffffff !important;
        font-weight: 700;
    }
    [data-testid="stSidebar"] button[kind="primary"] span {
        color: #ffffff !important;
    }

    /* Page header */
    .vit-header {
        display: flex;
        align-items: center;
        gap: 14px;
        padding: 1.35rem 1.5rem;
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 8px;
        margin-bottom: 1.25rem;
        box-shadow: 0 10px 28px rgba(15, 23, 42, 0.05);
    }
    .vit-header-icon {
        width: 48px; height: 48px;
        background: var(--vit-primary);
        border-radius: 8px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.5rem; flex-shrink: 0;
    }
    .vit-header h1 { margin: 0; font-size: 1.55rem; font-weight: 750; color: var(--vit-text); }
    .vit-header p  { margin: 0.2rem 0 0; font-size: 0.9rem; color: var(--vit-muted); }

    /* Info strip */
    .info-strip {
        background: #e8f1ff;
        border: 1px solid #93c5fd;
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.9rem;
        color: #173b8f;
        margin-bottom: 1.25rem;
    }

    /* Section heading */
    .section-heading {
        font-size: 0.82rem;
        font-weight: 750;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #334155;
        margin: 1.5rem 0 0.6rem;
    }

    /* Result cards */
    .result-row {
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-left: 4px solid var(--vit-border);
        border-radius: 8px;
        padding: 1rem;
        margin-bottom: 0.75rem;
        display: grid;
        grid-template-columns: minmax(0, 1fr) 156px;
        gap: 1rem;
        box-shadow: 0 10px 24px rgba(15, 23, 42, 0.04);
    }
    .result-row.safe     { border-left-color: #059669; }
    .result-row.moderate { border-left-color: #d97706; }
    .result-row.dream    { border-left-color: #dc2626; }
    .result-row.unlikely { border-left-color: #6b7280; }

    .result-topline {
        display: flex;
        align-items: center;
        gap: 0.55rem;
        flex-wrap: wrap;
        margin-bottom: 0.55rem;
    }
    .result-name { font-size: 1.03rem; font-weight: 800; color: var(--vit-text); }
    .result-meta { font-size: 0.82rem; color: var(--vit-muted); margin-top: 4px; }
    .result-meta b { color: var(--vit-text); }
    .option-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 0.45rem;
        margin: 0.45rem 0 0.55rem;
    }
    .option-chip {
        display: inline-flex;
        align-items: center;
        gap: 0.25rem;
        padding: 0.28rem 0.52rem;
        border: 1px solid var(--vit-border);
        border-radius: 6px;
        color: var(--vit-muted);
        background: rgba(148, 163, 184, 0.08);
        font-size: 0.76rem;
        font-weight: 650;
        line-height: 1.15;
    }
    .option-chip strong { color: var(--vit-text); font-weight: 800; }
    .option-chip.good {
        color: #047857;
        border-color: rgba(5, 150, 105, 0.35);
        background: rgba(16, 185, 129, 0.10);
    }
    .option-chip.warn {
        color: #b45309;
        border-color: rgba(217, 119, 6, 0.35);
        background: rgba(245, 158, 11, 0.12);
    }
    .option-chip.risk {
        color: #dc2626;
        border-color: rgba(220, 38, 38, 0.35);
        background: rgba(239, 68, 68, 0.10);
    }
    .result-note {
        color: var(--vit-muted);
        font-size: 0.8rem;
        line-height: 1.35;
    }
    .result-note strong { color: var(--vit-text); }
    .prob-panel {
        border-left: 1px solid var(--vit-border);
        padding-left: 1rem;
        display: flex;
        flex-direction: column;
        align-items: flex-end;
        justify-content: center;
        min-width: 0;
    }

    .prob-number { font-size: 1.5rem; font-weight: 700; line-height: 1; }
    .prob-number.safe     { color: #059669; }
    .prob-number.moderate { color: #d97706; }
    .prob-number.dream    { color: #dc2626; }
    .prob-number.unlikely { color: #6b7280; }
    .prob-label { font-size: 0.76rem; color: var(--vit-muted); margin-top: 4px; text-align: right; }
    .score-label { font-size: 0.68rem; color: var(--vit-soft); margin-top: 5px; text-align: right; }

    .prob-bar-bg {
        height: 5px; background: #e5e7eb;
        border-radius: 2px; overflow: hidden;
        margin-top: 8px; min-width: 108px;
    }
    .prob-bar-fill { height: 100%; border-radius: 2px; }

    /* ── Badge ── */
    .badge {
        display: inline-block;
        font-size: 0.68rem; font-weight: 500;
        padding: 2px 8px; border-radius: 99px;
        margin-left: 6px; vertical-align: middle;
    }
    .badge-safe     { background: #d1fae5; color: #065f46; }
    .badge-moderate { background: #fef3c7; color: #78350f; }
    .badge-dream    { background: #fee2e2; color: #7f1d1d; }
    .badge-unlikely { background: #e5e7eb; color: #374151; }

    /* Metric cards */
    .metric-grid {
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.75rem;
        margin-bottom: 1.25rem;
    }
    .metric-card {
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 8px;
        padding: 1rem 1.25rem;
        min-height: 112px;
    }
    .metric-card-label { font-size: 0.74rem; color: #475569; text-transform: uppercase; letter-spacing: 0.04em; font-weight: 750; }
    .metric-card-value { font-size: 1.75rem; font-weight: 800; color: var(--vit-text); margin: 5px 0 2px; }
    .metric-card-sub   { font-size: 0.8rem; color: var(--vit-muted); }
    .metric-card-sub.green { color: #059669; }

    /* Context banner */
    .context-banner {
        border: 1px solid var(--vit-border);
        border-radius: 8px;
        padding: 0.7rem 1rem;
        font-size: 0.88rem;
        margin-bottom: 0.6rem;
        font-weight: 600;
    }
    .context-banner.safe     { background: #f0fdf4; border-color: #bbf7d0; color: #166534; }
    .context-banner.moderate { background: #fffbeb; border-color: #fde68a; color: #92400e; }
    .context-banner.dream    { background: #fef2f2; border-color: #fecaca; color: #7f1d1d; }

    /* Sidebar rank display */
    .rank-big {
        font-size: 2rem; font-weight: 800; color: var(--vit-primary);
        line-height: 1; margin: 6px 0 2px;
    }

    /* Sidebar multiselect improvements */
    [data-testid="stSidebar"] [data-baseweb="tag"] {
        padding: 5px 10px !important;
        margin: 3px 3px !important;
        font-size: 0.9rem !important;
        white-space: normal !important;
        overflow: visible !important;
    }
    [data-testid="stSidebar"] [data-baseweb="select"] {
        flex-wrap: wrap !important;
    }
    [data-testid="stSidebar"] [data-baseweb="base-select"] {
        min-height: auto !important;
    }

    /* Streamlit overrides */
    h1, h2, h3, h4, h5, h6, p, label, span, div { color: inherit; }
    div[data-testid="stMetric"] {
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 8px;
        padding: 0.9rem 1rem;
        min-height: 98px;
    }
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {
        color: #475569 !important;
        font-size: 0.8rem !important;
        font-weight: 750 !important;
    }
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {
        color: var(--vit-text) !important;
        font-size: 1.65rem !important;
        font-weight: 800 !important;
    }
    div[data-testid="stTabs"] [data-baseweb="tab-list"] { gap: 4px; }
    div[data-testid="stTabs"] [data-baseweb="tab"] {
        font-size: 0.9rem;
        padding: 8px 16px;
        border-radius: 6px;
        color: var(--vit-muted);
        font-weight: 650;
    }
    div[data-testid="stTabs"] [aria-selected="true"] { color: var(--vit-primary-dark) !important; }
    div[data-testid="stDataFrame"] { border: 1px solid var(--vit-border); border-radius: 8px; overflow: hidden; }
    .stAlert {
        border-radius: 8px;
        border: 1px solid #bfdbfe;
    }

    @media (max-width: 900px) {
        [data-testid="stMainBlockContainer"] { padding: 1.25rem 1rem; }
        .metric-grid { grid-template-columns: repeat(2, 1fr); }
        .result-row { grid-template-columns: 1fr; }
        .prob-panel {
            align-items: flex-start;
            border-left: 0;
            border-top: 1px solid var(--vit-border);
            padding-left: 0;
            padding-top: 0.85rem;
        }
        .prob-label,
        .score-label { text-align: left; }
        .prob-bar-bg { width: 100%; }
    }
</style>
""", unsafe_allow_html=True)

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
    }}
    .stApp,
    [data-testid="stMainBlockContainer"] {{
        background: var(--vit-bg) !important;
        color: var(--vit-text) !important;
    }}
    [data-testid="stHeader"] {{ background: {theme["header"]} !important; }}
    [data-testid="stSidebar"],
    .vit-header,
    .result-row,
    .metric-card,
    div[data-testid="stMetric"] {{
        background: var(--vit-surface) !important;
        border-color: var(--vit-border) !important;
    }}
    .vit-header {{ box-shadow: var(--vit-shadow) !important; }}
    .vit-header h1,
    .result-name,
    .metric-card-value,
    .result-meta b,
    .option-chip strong,
    .result-note strong,
    div[data-testid="stMetric"] [data-testid="stMetricValue"] {{
        color: var(--vit-text) !important;
    }}
    .vit-header p,
    .result-meta,
    .result-note,
    .prob-label,
    .metric-card-sub,
    [data-testid="stSidebar"] small,
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {{
        color: var(--vit-muted) !important;
    }}
    .section-heading,
    .metric-card-label,
    div[data-testid="stMetric"] label,
    div[data-testid="stMetric"] [data-testid="stMetricLabel"] {{
        color: var(--vit-soft) !important;
    }}
    .info-strip {{
        background: var(--vit-info-bg) !important;
        border-color: var(--vit-info-border) !important;
        color: var(--vit-info-text) !important;
    }}
    [data-baseweb="input"],
    [data-baseweb="select"] > div,
    [data-baseweb="textarea"],
    [data-testid="stNumberInput"] div,
    [data-testid="stSelectbox"] div,
    [data-testid="stMultiSelect"] div {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    [data-baseweb="input"] input,
    [data-baseweb="input"] div,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] input,
    [data-baseweb="select"] div,
    [data-baseweb="select"] span,
    [data-baseweb="select"] svg,
    [data-testid="stNumberInput"] input,
    [data-testid="stNumberInput"] button,
    [data-testid="stNumberInput"] button svg,
    [data-testid="stSelectbox"] input,
    [data-testid="stSelectbox"] div,
    [data-testid="stSelectbox"] span,
    [data-testid="stMultiSelect"] input,
    [data-testid="stMultiSelect"] div,
    [data-testid="stMultiSelect"] span,
    [data-testid="stSlider"] div,
    [data-testid="stSlider"] span,
    [role="listbox"] li,
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span {{
        color: var(--vit-text) !important;
    }}
    input::placeholder,
    textarea::placeholder,
    [data-baseweb="input"] input::placeholder,
    [data-baseweb="select"] input::placeholder {{
        color: var(--vit-soft) !important;
        opacity: 1 !important;
    }}
    [data-testid="stNumberInput"] button {{
        background: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-baseweb="tag"] {{
        background-color: var(--vit-tag-bg) !important;
        border-color: var(--vit-border) !important;
        color: var(--vit-tag-text) !important;
        box-shadow: inset 0 0 0 1px var(--vit-border) !important;
    }}
    [data-baseweb="tag"],
    [data-baseweb="tag"] *,
    [data-baseweb="tag"] span,
    [data-baseweb="tag"] svg,
    [data-baseweb="tag"] button,
    [data-testid="stMultiSelect"] [data-baseweb="tag"],
    [data-testid="stMultiSelect"] [data-baseweb="tag"] * {{
        color: var(--vit-tag-text) !important;
        fill: var(--vit-tag-text) !important;
    }}
    [data-testid="stMultiSelect"] [aria-label="Clear all"],
    [data-testid="stMultiSelect"] [aria-label="Open"],
    [data-testid="stSelectbox"] [aria-label="Open"] {{
        color: var(--vit-text) !important;
        fill: var(--vit-text) !important;
    }}
    [role="listbox"] {{
        background: var(--vit-surface) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stSegmentedControl"] label,
    [data-testid="stSegmentedControl"] label div,
    [data-testid="stSegmentedControl"] label span {{
        color: var(--vit-text) !important;
    }}
    [data-testid="stSegmentedControl"] div[role="radiogroup"] {{
        background: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stSegmentedControl"] label {{
        background: transparent !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stSegmentedControl"] label[aria-checked="true"],
    [data-testid="stSegmentedControl"] label[data-checked="true"] {{
        background: var(--vit-primary) !important;
        color: #0b1120 !important;
    }}
    [data-testid="stSegmentedControl"] label[aria-checked="true"] *,
    [data-testid="stSegmentedControl"] label[data-checked="true"] *,
    [data-testid="stSegmentedControl"] label[aria-checked="true"] span,
    [data-testid="stSegmentedControl"] label[data-checked="true"] span {{
        color: #0b1120 !important;
        fill: #0b1120 !important;
    }}
    [data-testid="stSegmentedControl"] label:not([aria-checked="true"]) *,
    [data-testid="stSegmentedControl"] label:not([data-checked="true"]) * {{
        color: var(--vit-text) !important;
        fill: var(--vit-text) !important;
    }}
    [role="switch"],
    [data-testid="stSwitch"] {{
        background: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [role="switch"] *,
    [data-testid="stSwitch"] * {{
        color: var(--vit-text) !important;
        fill: var(--vit-text) !important;
    }}
    [data-testid="stCaptionContainer"],
    [data-testid="stCaptionContainer"] p {{
        color: var(--vit-muted) !important;
    }}
    .stAlert,
    [data-testid="stAlert"] {{
        background: var(--vit-info-bg) !important;
        border-color: var(--vit-info-border) !important;
        color: var(--vit-info-text) !important;
    }}
    [data-testid="stAlert"] div,
    [data-testid="stAlert"] p,
    [data-testid="stAlert"] span {{
        color: var(--vit-info-text) !important;
    }}
    [data-testid="stDataFrame"] * {{
        color: var(--vit-text);
    }}
    .prob-bar-bg {{ background: var(--vit-bar-bg) !important; }}
    .option-chip {{
        border-color: var(--vit-border) !important;
        color: var(--vit-muted) !important;
        background: var(--vit-chip-bg) !important;
    }}
    .option-chip.good {{
        color: var(--vit-chip-good-text) !important;
        background: var(--vit-chip-good-bg) !important;
        border-color: var(--vit-safe-color) !important;
    }}
    .option-chip.warn {{
        color: var(--vit-chip-warn-text) !important;
        background: var(--vit-chip-warn-bg) !important;
        border-color: var(--vit-moderate-color) !important;
    }}
    .option-chip.risk {{
        color: var(--vit-chip-risk-text) !important;
        background: var(--vit-chip-risk-bg) !important;
        border-color: var(--vit-dream-color) !important;
    }}
    .option-chip.good strong,
    .option-chip.warn strong,
    .option-chip.risk strong {{
        color: inherit !important;
    }}
    .prob-number.safe {{ color: var(--vit-safe-color) !important; }}
    .prob-number.moderate {{ color: var(--vit-moderate-color) !important; }}
    .prob-number.dream {{ color: var(--vit-dream-color) !important; }}
    .result-row.safe {{ border-left-color: var(--vit-safe-color) !important; }}
    .result-row.moderate {{ border-left-color: var(--vit-moderate-color) !important; }}
    .result-row.dream {{ border-left-color: var(--vit-dream-color) !important; }}
    .result-row.unlikely {{ border-left-color: var(--vit-soft) !important; }}
    .badge-safe {{
        background: var(--vit-badge-safe-bg) !important;
        color: var(--vit-badge-safe-text) !important;
    }}
    .badge-moderate {{
        background: var(--vit-badge-moderate-bg) !important;
        color: var(--vit-badge-moderate-text) !important;
    }}
    .badge-dream {{
        background: var(--vit-badge-dream-bg) !important;
        color: var(--vit-badge-dream-text) !important;
    }}
    .badge-unlikely {{
        background: var(--vit-chip-bg) !important;
        color: var(--vit-muted) !important;
        border: 1px solid var(--vit-border) !important;
    }}
    div[data-testid="stTabs"] [data-baseweb="tab"] {{ color: var(--vit-muted) !important; }}
    div[data-testid="stTabs"] [aria-selected="true"] {{ color: var(--vit-primary-dark) !important; }}
    div[data-testid="stDataFrame"] {{ border-color: var(--vit-border) !important; }}
    .context-banner.safe {{
        background: {theme["safe_bg"]} !important;
        border-color: {theme["safe_border"]} !important;
        color: {theme["safe_text"]} !important;
    }}
    .context-banner.moderate {{
        background: {theme["moderate_bg"]} !important;
        border-color: {theme["moderate_border"]} !important;
        color: {theme["moderate_text"]} !important;
    }}
    .context-banner.dream {{
        background: {theme["dream_bg"]} !important;
        border-color: {theme["dream_border"]} !important;
        color: {theme["dream_text"]} !important;
    }}
    .footer-note {{
        color: var(--vit-muted) !important;
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
        <p>Powered by real student data &nbsp;·&nbsp; Rank-based admission probability</p>
    </div>
</div>
<div class="info-strip">
    ℹ️ Enter your VITEEE rank on the left, apply filters, and click <strong>Get Recommendations</strong> to see your personalised predictions. Accuracy improves as more students submit their allotments.
</div>
""", unsafe_allow_html=True)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.markdown("### ⚙️ Settings")

rank = st.sidebar.number_input(
    "Your VITEEE rank",
    min_value=1, max_value=250000, step=1, value=5000,
    help="Enter your VITEEE counselling rank, up to 2.5 lakh"
)
st.sidebar.markdown(f'<div class="rank-big">{rank:,}</div><div style="font-size:0.78rem;color:#9ca3af;margin-bottom:0.75rem;">rank entered</div>', unsafe_allow_html=True)

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

results_limit = st.sidebar.slider("Max results per category", min_value=5, max_value=30, value=10, step=5)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

# Quick filter for major branches
st.sidebar.markdown("**Quick Filter**")
branch_filter = st.sidebar.segmented_control(
    "Select branch group",
    ["All branches", "Just CSE", "ECE+EEE"],
    default="All branches",
    key="branch_filter"
)

# Define branch groups
cse_programs = ["CSE Core", "CSE AIML", "CSE DS", "CSE Cybersecurity", "CSE Business Systems", "CSE Robotics", "CSE IoT", "CSE CPS"]
ece_eee_programs = ["ECE Core", "Electrical"]

# Campus filter
all_campuses = sorted(master_df["Campus"].unique().tolist())
selected_campuses = st.sidebar.multiselect("Campus", all_campuses, default=all_campuses)

# Branch filter with preset
all_branches = sorted(master_df["Branch"].unique().tolist())

# Apply quick filter to default selection
if branch_filter == "Just CSE":
    default_branches = [b for b in all_branches if b in cse_programs]
elif branch_filter == "ECE+EEE":
    default_branches = [b for b in all_branches if b in ece_eee_programs]
else:
    default_branches = all_branches

selected_branches = st.sidebar.multiselect(
    "Branch (customize selection below)",
    all_branches,
    default=default_branches,
    help="Use Quick Filter above, or customize here"
)

# Fee filter
all_fees = sorted(master_df["Fee"].unique().tolist())
selected_fees = st.sidebar.multiselect(
    "Fee category",
    [str(int(f)) for f in all_fees],
    default=[str(int(f)) for f in all_fees],
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📤 Share Your Data")
st.sidebar.markdown('**Help improve predictions by sharing your counselling results**')

col1, col2 = st.sidebar.columns(2)
with col1:
    st.link_button("📋 2025 Batch", "https://forms.gle/VG28i72zpKetFA4W6", width="stretch")
with col2:
    st.info("Submit your rank & allotment", icon="ℹ️")

st.sidebar.markdown("---")

predict_button = st.sidebar.button(
    "🚀 Get Recommendations",
    width="stretch",
    type="primary",
    key="predict_btn"
)

# =====================================================
# RESULTS
# =====================================================

def prob_bar(prob, kind):
    colors = {"safe": "#059669", "moderate": "#d97706", "dream": "#dc2626", "unlikely": "#6b7280"}
    c = colors.get(kind, "#9ca3af")
    return f"""
    <div class="prob-bar-bg">
        <div class="prob-bar-fill" style="width:{min(prob,100):.1f}%;background:{c};"></div>
    </div>"""

def confidence_clean(label):
    return label.replace(" 🟢", "").replace(" 🟡", "").replace(" 🔴", "")

def confidence_class(confidence_pct):
    if confidence_pct >= 70:
        return "good"
    if confidence_pct >= 40:
        return "warn"
    return "risk"

def buffer_class(diff):
    if diff >= 5000:
        return "good"
    if diff >= 0:
        return "warn"
    return "risk"

def recommendation_reason(r):
    diff = r["rank_difference"]
    if r["chance"] == "Safe":
        if diff >= 5000:
            return "Large rank cushion. Strong option to prioritise."
        return "Inside the cutoff, but keep backups because the cushion is narrow."
    if r["chance"] == "Moderate":
        if diff >= 0:
            return "Inside the cutoff, but the margin is tight."
        return "Slightly beyond the cutoff. Keep as a backup only."
    return "Outside the observed cutoff. Add only if you are comfortable taking a chance."

def result_row_html(r, rank, kind):
    diff = r["rank_difference"]
    sign = "+" if diff >= 0 else "-"
    diff_word = "buffer" if diff >= 0 else "shortfall"
    diff_label = f"{sign}{abs(diff):,} {diff_word}"
    badge_map = {"safe": "badge-safe", "moderate": "badge-moderate", "dream": "badge-dream", "unlikely": "badge-unlikely"}
    badge_text = {"safe": "Safe", "moderate": "Moderate", "dream": "Reach", "unlikely": "Not possible"}
    badge = f'<span class="badge {badge_map[kind]}">{badge_text[kind]}</span>'
    confidence_label = confidence_clean(r["confidence"])
    option_title = escape(r["branch"])
    campus = escape(r["campus"])
    reason = escape(recommendation_reason(r))

    return f"""
    <div class="result-row {kind}">
        <div style="flex:1;min-width:0;">
            <div class="result-topline">
                <div class="result-name">{option_title}</div>
                {badge}
            </div>
            <div class="option-chip-row">
                <span class="option-chip">Campus <strong>{campus}</strong></span>
                <span class="option-chip">Fee <strong>Cat {r['fee']}</strong></span>
                <span class="option-chip">Closing <strong>{r['closing_rank']:,}</strong></span>
                <span class="option-chip {buffer_class(diff)}">Rank margin <strong>{diff_label}</strong></span>
                <span class="option-chip">Data <strong>{r['responses']} responses</strong></span>
                <span class="option-chip {confidence_class(r['confidence_pct'])}">Confidence <strong>{confidence_label}</strong></span>
            </div>
            <div class="result-note">
                <strong>Why:</strong> {reason}
            </div>
        </div>
        <div class="prob-panel">
            <div class="prob-number {kind}">{r['probability']:.1f}%</div>
            <div class="prob-label">{badge_text[kind]} chance</div>
            {prob_bar(r['probability'], kind)}
            <div class="score-label">Score {r['recommendation_score']:.1f}</div>
        </div>
    </div>"""

def section_header(icon, title, count):
    st.markdown(f'<div class="section-heading">{icon} {title} ({count})</div>', unsafe_allow_html=True)

if predict_button:
    all_results = recommend(rank, sort_by=sort_mapping[sort_option])
    selected_fees_int = [int(f) for f in selected_fees]

    filtered_results = [
        r for r in all_results
        if r["campus"] in selected_campuses
        and r["branch"] in selected_branches
        and r["fee"] in selected_fees_int
    ]

    if not filtered_results:
        st.markdown("""
        <div class="context-banner dream">
            No options found for your selected filters. Try selecting more campuses, branches, or fee categories.
        </div>
        """, unsafe_allow_html=True)
    else:
        rank_stats = get_rank_statistics(rank)
        safe_list     = [r for r in filtered_results if r["chance"] == "Safe"]
        moderate_list = [r for r in filtered_results if r["chance"] == "Moderate"]
        dream_list    = [r for r in filtered_results if r["chance"] == "Dream"]
        unlikely_list = [r for r in filtered_results if r["chance"] == "Very Unlikely"]
        avg_prob = sum(r["probability"] for r in filtered_results) / len(filtered_results)

        # ── Metrics ──────────────────────────────────────────────────
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
                <div class="metric-card-sub {'green' if safe_list else ''}">{"High chance" if safe_list else "None found"}</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Avg probability</div>
                <div class="metric-card-value">{avg_prob:.1f}%</div>
                <div class="metric-card-sub">across all options</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        categorized = get_recommendations_by_category(filtered_results)

        # ── Safe ─────────────────────────────────────────────────────
        if safe_list:
            section_header("✅", "Primary picks — strong rank fit", len(safe_list))
            st.markdown('<div class="context-banner safe">Best fit for your rank. Sort these by branch preference, campus, and fee category first.</div>', unsafe_allow_html=True)
            rows_html = "".join(result_row_html(r, rank, "safe") for r in safe_list[:results_limit])
            st.markdown(rows_html, unsafe_allow_html=True)

        # ── Moderate ─────────────────────────────────────────────────
        if moderate_list:
            section_header("⚡", "Backup picks — possible but tighter", len(moderate_list))
            st.markdown('<div class="context-banner moderate">Useful backups. These may have a narrow buffer, low confidence, or a branch/campus tradeoff.</div>', unsafe_allow_html=True)
            rows_html = "".join(result_row_html(r, rank, "moderate") for r in moderate_list[:results_limit])
            st.markdown(rows_html, unsafe_allow_html=True)

        # ── Dream ────────────────────────────────────────────────────
        if dream_list:
            section_header("🔥", "Reach picks — add sparingly", len(dream_list))
            st.markdown('<div class="context-banner dream">These are outside or near the observed cutoff. Keep them low in your preference order.</div>', unsafe_allow_html=True)
            rows_html = "".join(result_row_html(r, rank, "dream") for r in dream_list[:results_limit])
            st.markdown(rows_html, unsafe_allow_html=True)

        # ── Very unlikely / no possible options ──────────────────────
        if not safe_list and not moderate_list and not dream_list:
            section_header("⛔", "No possible options for this filter", len(unlikely_list))
            st.markdown('<div class="context-banner dream">Your rank is far outside the observed cutoffs for these filters. Broaden campus, branch, or fee category to find realistic choices.</div>', unsafe_allow_html=True)
            rows_html = "".join(result_row_html(r, rank, "unlikely") for r in unlikely_list[:results_limit])
            st.markdown(rows_html, unsafe_allow_html=True)
        elif unlikely_list:
            section_header("⛔", "Not recommended — very unlikely", len(unlikely_list))
            st.markdown('<div class="context-banner dream">These match your filters but are far outside the observed cutoff. Use only for awareness.</div>', unsafe_allow_html=True)
            rows_html = "".join(result_row_html(r, rank, "unlikely") for r in unlikely_list[:min(results_limit, 5)])
            st.markdown(rows_html, unsafe_allow_html=True)

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
        **CHART_THEME,
        showlegend=showlegend,
        legend=dict(
            font=dict(size=12, color=theme["text"]),
            bgcolor=theme["legend_bg"],
            bordercolor=theme["border"],
            borderwidth=1,
        ),
        xaxis=dict(
            title_font=dict(color=theme["text"], size=13),
            tickfont=dict(color=theme["muted"], size=12),
            gridcolor=theme["grid"],
            zerolinecolor=theme["axis"],
            linecolor=theme["axis"],
        ),
        yaxis=dict(
            title_font=dict(color=theme["text"], size=13),
            tickfont=dict(color=theme["muted"], size=12),
            gridcolor=theme["grid"],
            zerolinecolor=theme["axis"],
            linecolor=theme["axis"],
        ),
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
        fig = px.bar(
            x=branch_counts.values,
            y=branch_counts.index,
            orientation="h",
            labels={"x": "Responses", "y": "Branch"},
            title="Top branches by responses",
            color=branch_counts.values,
            color_continuous_scale=["#c7d2fe", "#4f46e5", "#1e1b4b"],
        )
        fig.update_layout(coloraxis_showscale=False, yaxis=dict(autorange="reversed"))
        style_chart(fig)
        fig.update_traces(marker_line_width=0, text=branch_counts.values, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(
            values=branch_counts.values, names=branch_counts.index,
            title="Branch share",
            color_discrete_sequence=px.colors.qualitative.Safe,
        )
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab2:
    c1, c2 = st.columns(2)
    campus_counts = master_df["Campus"].value_counts()
    with c1:
        fig = px.bar(
            x=campus_counts.index, y=campus_counts.values,
            labels={"x": "Campus", "y": "Responses"},
            title="Responses by campus",
            color=campus_counts.values,
            color_continuous_scale=["#bae6fd", "#0284c7", "#0c4a6e"],
        )
        fig.update_layout(coloraxis_showscale=False)
        style_chart(fig)
        fig.update_traces(marker_line_width=0, text=campus_counts.values, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(
            values=campus_counts.values, names=campus_counts.index,
            title="Share by campus",
            color_discrete_sequence=px.colors.qualitative.Bold,
        )
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab3:
    c1, c2 = st.columns(2)
    fee_counts = master_df["Fee"].value_counts().sort_index()
    fee_labels = ["Category " + str(int(f)) for f in fee_counts.index]
    with c1:
        fig = px.bar(
            x=fee_labels, y=fee_counts.values,
            labels={"x": "Fee category", "y": "Students"},
            title="Students by fee category",
            color=fee_counts.values,
            color_continuous_scale=["#bbf7d0", "#16a34a", "#14532d"],
        )
        fig.update_layout(coloraxis_showscale=False)
        style_chart(fig)
        fig.update_traces(marker_line_width=0, text=fee_counts.values, textposition="outside", cliponaxis=False)
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(
            values=fee_counts.values, names=fee_labels,
            title="Share by fee category",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab4:
    c1, c2 = st.columns([0.7, 0.3])
    with c1:
        search_branch = st.selectbox("Filter by branch", ["All"] + sorted(master_df["Branch"].unique().tolist()))
    with c2:
        display_count = st.slider("Rows to show", min_value=10, max_value=100, value=20, step=10)

    display_df = master_df if search_branch == "All" else master_df[master_df["Branch"] == search_branch]
    display_df = display_df.head(display_count)

    st.dataframe(
        display_df, width="stretch", height=400,
        column_config={
            "Rank": st.column_config.NumberColumn(format="%d"),
            "Fee":  st.column_config.NumberColumn(format="Category %d"),
        }
    )
    st.caption(f"Showing {len(display_df):,} of {len(master_df):,} records")

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

c1, c2, c3 = st.columns(3)
with c1: st.info(f"📊 Data updated: {pd.Timestamp.now().strftime('%Y-%m-%d')}")
with c2: st.info(f"📌 {len(master_df):,} student records")
with c3: st.info("🔄 Accuracy improves with more responses")

st.markdown("""
<div class="footer-note" style="font-size:0.82rem;margin-top:1rem;line-height:1.7;">
<strong>How to read the results</strong><br>
<b>Safe (75%+)</b> — Very likely. Make these your primary choices.<br>
<b>Moderate (40–75%)</b> — Possible but not guaranteed. Good backups.<br>
<b>Dream (15–40%)</b> — Unlikely. Include as last-resort options only.<br><br>
<em>Disclaimer: Predictions are based on historical allotment data. Actual results may differ. Always consult official VIT counselling resources.</em>
</div>
""", unsafe_allow_html=True)
