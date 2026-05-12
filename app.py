from datetime import datetime
from html import escape

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import database as db
from load_data import get_reports, master_df, submit_report
from recommender import get_rank_statistics, get_recommendations_by_category, recommend

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="VIT Counselling Predictor",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# THEME
# =====================================================

if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "Light"

theme_mode = st.sidebar.segmented_control(
    "Theme",
    ["Light", "Dark (Beta)"],
    key="theme_mode",
)
_theme_valid = ("Light", "Dark (Beta)")
_sel_theme = (
    theme_mode if theme_mode in _theme_valid else st.session_state.get("theme_mode", "Light")
)
if _sel_theme not in _theme_valid:
    _sel_theme = "Light"
    st.session_state.theme_mode = _sel_theme
REPORT_TYPE_META = {
    "wrong_cutoff": {"label": "Wrong cutoff", "color": "#f59e0b"},
    "got_allotted": {"label": "Got allotted", "color": "#10b981"},
    "not_allotted": {"label": "Not allotted", "color": "#ef4444"},
    "prob_high": {"label": "Prob too high", "color": "#6366f1"},
    "prob_low": {"label": "Prob too low", "color": "#ec4899"},
    "other": {"label": "Other", "color": "#64748b"},
}
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
        # Report panel colours
        "report_bg": "#fafafa",
        "report_border": "#e2e8f0",
        "report_header_bg": "#f8fafc",
        "report_success_bg": "#f0fdf4",
        "report_success_border": "#86efac",
        "report_success_text": "#15803d",
        # Extra shadows / surfaces (hover, notes, badges)
        "note_bg": "rgba(100, 116, 139, 0.08)",
        "insufficient_bg": "#fef3c7",
        "insufficient_text": "#92400e",
        "insufficient_border": "#fcd34d",
        "hover_safe": "0 8px 32px rgba(74, 222, 128, 0.10)",
        "hover_moderate": "0 8px 32px rgba(251, 191, 36, 0.10)",
        "hover_dream": "0 8px 32px rgba(239, 68, 68, 0.12)",
        "hover_unlikely": "0 6px 24px rgba(100, 116, 139, 0.12)",
        "stat_card_hover_shadow": "0 8px 24px rgba(15, 23, 42, 0.12)",
    },
    "Dark (Beta)": {
        # Base surfaces — slightly warmer deep blue
        "bg": "#080e1a",
        "surface": "#0f1d2e",
        "input": "#162436",
        "text": "#e8edf5",
        "muted": "#8b9db5",
        "soft": "#556070",
        "border": "#1e3248",
        # Brand colour — vivid indigo that pops on dark
        "primary": "#7c8dfa",
        "primary_dark": "#a0adfb",
        "header": "rgba(8,14,26,0.97)",
        "shadow": "0 8px 32px rgba(0,0,0,0.5)",
        # Info / alerts
        "info_bg": "#0f2744",
        "info_border": "#2563eb",
        "info_text": "#bfdbfe",
        # Tags
        "tag_bg": "#1e1b4b",
        "tag_text": "#c7d2fe",
        # Chart helpers
        "grid": "#182840",
        "axis": "#253848",
        "legend_bg": "rgba(15,29,46,0.95)",
        "hover_bg": "#e8edf5",
        "hover_text": "#080e1a",
        "bar_bg": "#182840",
        # Chips
        "chip_bg": "#12223a",
        "chip_good_bg": "#062011",
        "chip_good_text": "#34d399",
        "chip_warn_bg": "#2d1a04",
        "chip_warn_text": "#fbbf24",
        "chip_risk_bg": "#2d0a0a",
        "chip_risk_text": "#f87171",
        # Status colours — slightly more vivid
        "safe_color": "#34d399",
        "moderate_color": "#fbbf24",
        "dream_color": "#f87171",
        # Badges
        "badge_safe_bg": "#064e2b",
        "badge_safe_text": "#a7f3d0",
        "badge_moderate_bg": "#5c3207",
        "badge_moderate_text": "#fef3c7",
        "badge_dream_bg": "#6b1010",
        "badge_dream_text": "#fecaca",
        # Context banners
        "safe_bg": "#062011",
        "safe_border": "#059669",
        "safe_text": "#a7f3d0",
        "moderate_bg": "#2d1a04",
        "moderate_border": "#d97706",
        "moderate_text": "#fef3c7",
        "dream_bg": "#2d0a0a",
        "dream_border": "#dc2626",
        "dream_text": "#fecaca",
        # Report panel
        "report_bg": "#101f30",
        "report_border": "#1e3248",
        "report_header_bg": "#0f1d2e",
        "report_success_bg": "#062011",
        "report_success_border": "#059669",
        "report_success_text": "#34d399",
        "note_bg": "rgba(139, 157, 181, 0.12)",
        "insufficient_bg": "#2d1a04",
        "insufficient_text": "#fde68a",
        "insufficient_border": "#b45309",
        "hover_safe": "0 8px 36px rgba(52, 211, 153, 0.18)",
        "hover_moderate": "0 8px 36px rgba(251, 191, 36, 0.16)",
        "hover_dream": "0 8px 36px rgba(248, 113, 113, 0.18)",
        "hover_unlikely": "0 6px 28px rgba(0, 0, 0, 0.45)",
        "stat_card_hover_shadow": "0 10px 36px rgba(0, 0, 0, 0.55)",
    },
}
THEMES["Dark"] = THEMES["Dark (Beta)"]
theme = THEMES[_sel_theme]


# =====================================================
# SESSION STATE — report tracking
# =====================================================

if "report_open" not in st.session_state:
    st.session_state.report_open = {}
if "report_submitted" not in st.session_state:
    st.session_state.report_submitted = {}
if "report_text" not in st.session_state:
    st.session_state.report_text = {}
if "report_type" not in st.session_state:
    st.session_state.report_type = {}
# Cached recommendation results — survive reruns triggered by report-panel buttons
if "_pred_ready" not in st.session_state:
    st.session_state["_pred_ready"] = False
if "_pred_rank" not in st.session_state:
    st.session_state["_pred_rank"] = None
if "_pred_results" not in st.session_state:
    st.session_state["_pred_results"] = []
# Admin: which report ID is awaiting delete confirmation (None = none)
if "_admin_delete_pending" not in st.session_state:
    st.session_state["_admin_delete_pending"] = None

# =====================================================
# CSS
# =====================================================

st.markdown(
    f"""
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
        --report-bg: {theme["report_bg"]};
        --report-border: {theme["report_border"]};
        --report-header-bg: {theme["report_header_bg"]};
        --report-success-bg: {theme["report_success_bg"]};
        --report-success-border: {theme["report_success_border"]};
        --report-success-text: {theme["report_success_text"]};
        --vit-note-bg: {theme["note_bg"]};
        --vit-insufficient-bg: {theme["insufficient_bg"]};
        --vit-insufficient-text: {theme["insufficient_text"]};
        --vit-insufficient-border: {theme["insufficient_border"]};
        --vit-hover-safe: {theme["hover_safe"]};
        --vit-hover-moderate: {theme["hover_moderate"]};
        --vit-hover-dream: {theme["hover_dream"]};
        --vit-hover-unlikely: {theme["hover_unlikely"]};
        --vit-stat-card-hover: {theme["stat_card_hover_shadow"]};
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
    [data-testid="stSidebar"] > div:first-child {{
        padding: 1rem 1rem 1.5rem;
        display: flex;
        flex-direction: column;
        gap: 0;
    }}
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

    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button[kind="primary"] * {{
        color: #ffffff !important;
    }}

    /* ── Form controls ── */
    [data-baseweb="input"],
    [data-baseweb="base-input"],
    [data-baseweb="select"] > div,
    [data-baseweb="tag"],
    [data-baseweb="textarea"] {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    /* Streamlit 1.5x: target child divs of number-input & selectbox directly */
    [data-testid="stNumberInput"] > div,
    [data-testid="stNumberInput"] > div > div {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stSelectbox"] > div > div,
    [data-testid="stSelectbox"] > div > div > div {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stTextInput"] > div > div {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-baseweb="input"] input,
    [data-baseweb="base-input"] input,
    [data-testid="stNumberInput"] input {{
        background-color: var(--vit-input) !important;
        color: var(--vit-text) !important;
        caret-color: var(--vit-primary) !important;
    }}
    [data-baseweb="select"] input,
    [data-baseweb="select"] span,
    [role="listbox"] li,
    [data-testid="stSelectbox"] span {{ color: var(--vit-text) !important; }}
    [data-baseweb="textarea"] textarea,
    textarea {{
        background-color: var(--vit-input) !important;
        color: var(--vit-text) !important;
        caret-color: var(--vit-primary) !important;
    }}
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
        border-radius: 10px;
        margin-bottom: 1.25rem;
        box-shadow: var(--vit-shadow);
    }}
    .vit-header-icon {{
        width: 46px; height: 46px;
        background: var(--vit-primary);
        border-radius: 9px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.45rem; flex-shrink: 0;
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
        font-size: 0.78rem;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--vit-soft);
        margin: 2rem 0 0.75rem;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}


    /* ── Sidebar section divider ── */
    .sidebar-section {{
        border-top: 1px solid var(--vit-border);
        margin: 0.75rem -1rem;
        padding: 0.85rem 1rem 0;
    }}

    /* ── Result card: submitted path uses .result-card-wrap; interactive path uses Streamlit columns + .vit-pred-card marker ── */
    .result-card-wrap {{
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-left: 5px solid var(--vit-border);
        border-radius: 10px;
        margin-bottom: 0.9rem;
        box-shadow: var(--vit-shadow);
        transition: box-shadow 0.18s ease, border-color 0.18s ease;
        overflow: hidden;
    }}
    .result-card-wrap.safe     {{ border-left-color: var(--vit-safe-color); }}
    .result-card-wrap.moderate {{ border-left-color: var(--vit-moderate-color); }}
    .result-card-wrap.dream    {{ border-left-color: var(--vit-dream-color); }}
    .result-card-wrap.unlikely {{ border-left-color: var(--vit-soft); }}

    .result-row {{
        display: grid;
        grid-template-columns: minmax(0, 1fr) 180px;
        gap: 1.25rem;
        padding: 1.35rem 1.5rem;
    }}

    span.vit-pred-card {{
        position: absolute;
        width: 1px;
        height: 1px;
        padding: 0;
        margin: -1px;
        overflow: hidden;
        clip: rect(0, 0, 0, 0);
        white-space: nowrap;
        border: 0;
    }}

    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card) {{
        position: relative;
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 10px;
        padding: 1.15rem 1.35rem 1.25rem;
        margin-bottom: 0.9rem;
        box-shadow: var(--vit-shadow);
        transition: box-shadow 0.18s ease, border-color 0.18s ease;
        align-items: flex-start;
        overflow: hidden;
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--safe) {{
        border-left: 5px solid var(--vit-safe-color);
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--moderate) {{
        border-left: 5px solid var(--vit-moderate-color);
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--dream) {{
        border-left: 5px solid var(--vit-dream-color);
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--unlikely) {{
        border-left: 5px solid var(--vit-soft);
    }}

    .vit-pred-col-main {{
        position: relative;
        min-width: 0;
    }}
    .vit-pred-col-side {{
        display: flex;
        flex-direction: column;
        align-items: stretch;
        gap: 0.55rem;
        min-width: 0;
        width: 100%;
    }}

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
        transition: border-color 0.15s, box-shadow 0.15s;
    }}
    .chip:hover {{
        border-color: var(--vit-soft) !important;
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
        background: var(--vit-note-bg);
        border-radius: 0 6px 6px 0;
    }}
    .badge-insufficient {{
        margin-left: 4px;
        background: var(--vit-insufficient-bg) !important;
        color: var(--vit-insufficient-text) !important;
        border: 1px solid var(--vit-insufficient-border) !important;
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
    .prob-panel.prob-panel--column {{
        border-left: none;
        padding-left: 0;
        align-items: flex-end;
        justify-content: flex-start;
        width: 100%;
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
        font-size: 0.72rem;
        color: var(--vit-soft);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-weight: 700;
    }}
    .metric-card-value {{
        font-size: 2rem;
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
        font-size: 0.88rem;
        margin-bottom: 0.75rem;
        font-weight: 600;
        line-height: 1.5;
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

    /* ── Report card ── */
    .report-card {{
        background: var(--report-bg);
        border: 1px solid var(--report-border);
        border-radius: 10px;
        margin-top: 0.35rem;
        margin-bottom: 0.75rem;
        overflow: hidden;
    }}
    .report-card-header {{
        display: flex;
        align-items: center;
        justify-content: space-between;
        padding: 0.75rem 1rem;
        background: var(--report-header-bg);
        border-bottom: 1px solid var(--report-border);
    }}
    .report-card-title {{
        font-size: 0.88rem;
        font-weight: 700;
        color: var(--vit-text);
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }}
    .report-card-sub {{
        font-size: 0.80rem;
        color: var(--vit-muted);
        font-weight: 400;
    }}
    .report-card-body {{
        padding: 1rem;
    }}
    .report-type-grid {{
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 0.5rem;
        margin-bottom: 0.9rem;
    }}
    .report-type-option {{
        border: 1.5px solid var(--vit-border);
        border-radius: 8px;
        padding: 0.6rem 0.75rem;
        cursor: pointer;
        background: var(--vit-surface);
        text-align: center;
        transition: all 0.15s;
    }}
    .report-type-option.selected {{
        border-color: var(--vit-primary);
        background: var(--vit-info-bg);
    }}
    .report-type-icon {{ font-size: 1.2rem; display: block; margin-bottom: 2px; }}
    .report-type-label {{ font-size: 0.75rem; font-weight: 600; color: var(--vit-text); }}
    .report-hint {{
        font-size: 0.80rem;
        color: var(--vit-muted);
        margin-bottom: 0.65rem;
        line-height: 1.5;
    }}
    .report-footer {{
        font-size: 0.76rem;
        color: var(--vit-muted);
        font-style: italic;
        margin-top: 0.5rem;
        padding-top: 0.5rem;
        border-top: 1px solid var(--report-border);
    }}
    .report-success {{
        background: var(--report-success-bg);
        border: 1px solid var(--report-success-border);
        border-radius: 8px;
        padding: 0.75rem 1rem;
        font-size: 0.88rem;
        color: var(--report-success-text);
        font-weight: 600;
        display: flex;
        align-items: center;
        gap: 0.5rem;
        margin-top: 0.35rem;
    }}
    .report-success--embedded {{
        margin: 0;
        border-radius: 0 0 10px 10px;
        border-top: 1px solid var(--report-success-border);
        padding: 0.75rem 1.25rem;
    }}

    /* ── Admin dashboard ── */
    .admin-header {{
        background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e40af 100%);
        border-radius: 12px;
        padding: 1.75rem 2rem;
        margin-bottom: 1.5rem;
        display: flex;
        align-items: center;
        gap: 1.25rem;
    }}
    .admin-header-icon {{
        width: 56px; height: 56px;
        background: rgba(255,255,255,0.15);
        border-radius: 12px;
        display: flex; align-items: center; justify-content: center;
        font-size: 1.8rem; flex-shrink: 0;
        border: 1px solid rgba(255,255,255,0.2);
    }}
    .admin-header h2 {{ margin: 0; font-size: 1.5rem; font-weight: 800; color: #ffffff; }}
    .admin-header p  {{ margin: 0.2rem 0 0; font-size: 0.9rem; color: rgba(255,255,255,0.7); }}
    .admin-stat-grid {{
        display: grid;
        grid-template-columns: repeat(4, 1fr);
        gap: 0.85rem;
        margin-bottom: 1.5rem;
    }}
    .admin-stat-card {{
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 10px;
        padding: 1.1rem 1.4rem;
        box-shadow: var(--vit-shadow);
    }}
    .admin-stat-label {{
        font-size: 0.74rem;
        color: var(--vit-soft);
        text-transform: uppercase;
        letter-spacing: 0.05em;
        font-weight: 700;
        margin-bottom: 6px;
    }}
    .admin-stat-value {{
        font-size: 1.9rem;
        font-weight: 800;
        color: var(--vit-primary);
        line-height: 1;
        margin-bottom: 4px;
    }}
    .admin-stat-sub {{ font-size: 0.82rem; color: var(--vit-muted); }}
    .admin-report-row {{
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 0.5rem;
        display: grid;
        grid-template-columns: 120px 1fr 1fr 100px 1fr;
        gap: 1rem;
        align-items: center;
        box-shadow: var(--vit-shadow);
    }}
    .admin-report-meta {{
        font-size: 0.78rem;
        color: var(--vit-muted);
    }}
    .admin-report-branch {{ font-weight: 700; color: var(--vit-text); font-size: 0.95rem; }}
    .admin-report-campus {{ font-size: 0.82rem; color: var(--vit-muted); margin-top: 2px; }}
    .admin-report-reason {{
        font-size: 0.84rem;
        color: var(--vit-text);
        line-height: 1.45;
        background: var(--vit-note-bg);
        border-radius: 6px;
        padding: 0.4rem 0.6rem;
        border-left: 3px solid var(--vit-border);
    }}
    .admin-report-reason.no-reason {{
        color: var(--vit-muted);
        font-style: italic;
    }}
    .admin-filter-bar {{
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 10px;
        padding: 1rem 1.25rem;
        margin-bottom: 1.25rem;
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
    /* ── Segmented control — comprehensive fix (covers all Streamlit 1.5x variants) ── */
    [data-testid="stSegmentedControl"] > div,
    [data-testid="stSegmentedControl"] [role="radiogroup"],
    [data-testid="stSegmentedControl"] div[role="radiogroup"] {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
        border-radius: 8px !important;
        padding: 3px !important;
        gap: 2px !important;
    }}
    [data-testid="stSegmentedControl"] label,
    [data-testid="stSegmentedControl"] button {{
        background-color: transparent !important;
        color: var(--vit-muted) !important;
        border-radius: 6px !important;
        border: none !important;
        transition: color 0.15s !important;
    }}
    [data-testid="stSegmentedControl"] label[aria-checked="true"],
    [data-testid="stSegmentedControl"] label[data-checked="true"],
    [data-testid="stSegmentedControl"] label[aria-selected="true"],
    [data-testid="stSegmentedControl"] button[aria-pressed="true"],
    [data-testid="stSegmentedControl"] button[aria-selected="true"],
    [data-testid="stSegmentedControl"] button[data-selected="true"] {{
        background-color: var(--vit-primary) !important;
        color: #ffffff !important;
        box-shadow: 0 1px 6px rgba(0,0,0,0.25) !important;
    }}
    [data-testid="stSegmentedControl"] label {{ color: var(--vit-text) !important; }}
    [data-testid="stCaptionContainer"] p {{ color: var(--vit-muted) !important; }}
    .footer-note {{ color: var(--vit-muted) !important; }}

    /* ── Metric cards — fix invisible text on dark bg (config.toml base=light) ── */
    [data-testid="stMetricValue"],
    [data-testid="stMetricValue"] > div,
    [data-testid="stMetricValue"] label {{ color: var(--vit-text) !important; }}
    [data-testid="stMetricLabel"],
    [data-testid="stMetricLabel"] > div,
    [data-testid="stMetricLabel"] p {{ color: var(--vit-muted) !important; }}
    [data-testid="stMetricDelta"],
    [data-testid="stMetricDelta"] > div {{ color: var(--vit-muted) !important; }}

    /* ── App / page background ── */
    [data-testid="stAppViewContainer"] {{ background-color: var(--vit-bg) !important; }}
    [data-testid="stBottom"] {{ background-color: var(--vit-bg) !important; }}
    [data-testid="stDecoration"] {{ display: none; }}

    /* ── Block containers — transparent so the bg shows through ── */
    [data-testid="stVerticalBlock"],
    [data-testid="stHorizontalBlock"] {{ background: transparent; }}

    /* ── Primary buttons (main canvas; sidebar rules stay scoped above) ── */
    [data-testid="stMainBlockContainer"] button[kind="primary"],
    [data-testid="stMainBlockContainer"] button[kind="primary"] * {{
        background-color: var(--vit-primary) !important;
        border-color: var(--vit-primary) !important;
        color: #ffffff !important;
    }}

    /* ── Secondary / tertiary buttons ── */
    button[kind="secondary"] {{
        background-color: var(--vit-surface) !important;
        border: 1px solid var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    button[kind="secondary"]:hover {{
        border-color: var(--vit-primary) !important;
        color: var(--vit-primary) !important;
    }}
    button[kind="tertiary"] {{ color: var(--vit-text) !important; }}
    button[kind="tertiary"]:hover {{ color: var(--vit-primary) !important; }}

    /* ── Download button ── */
    [data-testid="stDownloadButton"] > button {{
        background-color: var(--vit-surface) !important;
        border: 1px solid var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    [data-testid="stDownloadButton"] > button:hover {{
        border-color: var(--vit-primary) !important;
        color: var(--vit-primary) !important;
    }}

    /* ── Link button ── */
    [data-testid="stLinkButton"] a {{
        background-color: var(--vit-surface) !important;
        border: 1px solid var(--vit-border) !important;
        color: var(--vit-primary) !important;
    }}

    /* ── Tab list background and panel ── */
    [data-baseweb="tab-list"] {{
        background-color: var(--vit-surface) !important;
        border-radius: 8px !important;
        gap: 2px !important;
        padding: 3px !important;
    }}
    [data-baseweb="tab"] {{ background: transparent !important; }}
    [data-baseweb="tab"][aria-selected="true"] {{
        background: var(--vit-input) !important;
    }}
    [data-baseweb="tab-panel"] {{ background: transparent !important; }}
    [data-baseweb="tab-border"] {{ display: none !important; }}

    /* ── Selectbox / multiselect open dropdown ── */
    [data-baseweb="popover"] [data-baseweb="menu"],
    [data-baseweb="popover"] ul {{
        background-color: var(--vit-surface) !important;
        border: 1px solid var(--vit-border) !important;
    }}
    [data-baseweb="option"] {{
        background-color: var(--vit-surface) !important;
        color: var(--vit-text) !important;
    }}
    [data-baseweb="option"]:hover,
    [data-baseweb="option"][aria-selected="true"] {{
        background-color: var(--vit-input) !important;
    }}

    /* ── Slider track & thumb ── */
    [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {{
        background: var(--vit-primary) !important;
        border-color: var(--vit-primary) !important;
    }}
    [data-testid="stSlider"] p {{ color: var(--vit-muted) !important; }}

    /* ── Markdown containers ── */
    [data-testid="stMarkdownContainer"] p {{ color: var(--vit-text); }}
    [data-testid="stMarkdownContainer"] li {{ color: var(--vit-text); }}

    /* ── Dataframe / table ── */
    [data-testid="stDataFrame"] iframe {{ filter: none; }}
    [data-testid="stDataFrameGlideDataEditor"] {{
        background: var(--vit-surface) !important;
        color: var(--vit-text) !important;
    }}

    /* ── Toast notifications ── */
    [data-testid="stToast"] {{
        background-color: var(--vit-surface) !important;
        border: 1px solid var(--vit-border) !important;
        color: var(--vit-text) !important;
    }}
    [data-testid="stToast"] * {{ color: var(--vit-text) !important; }}

    /* ── Horizontal rule ── */
    hr {{ border-color: var(--vit-border) !important; }}

    /* ── Scrollbars ── */
    * {{
        scrollbar-width: thin;
        scrollbar-color: var(--vit-border) transparent;
    }}
    ::-webkit-scrollbar {{ width: 5px; height: 5px; }}
    ::-webkit-scrollbar-track {{ background: transparent; }}
    ::-webkit-scrollbar-thumb {{ background: var(--vit-border); border-radius: 4px; }}
    ::-webkit-scrollbar-thumb:hover {{ background: var(--vit-soft); }}

    /* ── Category overview bar ── */
    .cat-overview {{
        display: flex;
        background: var(--vit-surface);
        border: 1px solid var(--vit-border);
        border-radius: 8px;
        overflow: hidden;
        margin-bottom: 1.5rem;
    }}
    .cat-pill {{
        flex: 1;
        padding: 0.9rem 0.75rem 0.8rem;
        border-right: 1px solid var(--vit-border);
        display: flex;
        flex-direction: column;
        align-items: center;
        text-align: center;
        gap: 0.2rem;
    }}
    .cat-pill:last-child {{ border-right: none; }}
    .cat-pill-icon {{ display: none; }}
    .cat-pill-count {{
        font-size: 1.55rem;
        font-weight: 700;
        line-height: 1;
        letter-spacing: -0.03em;
    }}
    .cat-pill-label {{
        font-size: 0.64rem;
        color: var(--vit-muted);
        text-transform: uppercase;
        letter-spacing: 0.07em;
        font-weight: 600;
    }}

    /* ── Empty state ── */
    .empty-state {{
        padding: 1.5rem;
        background: transparent;
        border: 1px dashed var(--vit-border);
        border-radius: 8px;
        color: var(--vit-muted);
        font-size: 0.83rem;
        line-height: 1.6;
        margin-bottom: 0.9rem;
        text-align: center;
    }}
    .empty-state strong {{
        display: block;
        color: var(--vit-text);
        font-weight: 600;
        font-size: 0.88rem;
        margin-bottom: 0.3rem;
    }}
    .empty-state-icon,
    .empty-state-title,
    .empty-state-sub {{ display: none; }}

    /* ── Keyframe animations ─────────────────────────────────────── */
    @keyframes vit-fade-up {{
        from {{ opacity: 0; transform: translateY(10px); }}
        to   {{ opacity: 1; transform: translateY(0); }}
    }}
    @keyframes vit-fade-in {{
        from {{ opacity: 0; }}
        to   {{ opacity: 1; }}
    }}
    @keyframes vit-slide-right {{
        from {{ opacity: 0; transform: translateX(-8px); }}
        to   {{ opacity: 1; transform: translateX(0); }}
    }}
    @keyframes vit-bar-grow {{
        from {{ clip-path: inset(0 100% 0 0 round 3px); }}
        to   {{ clip-path: inset(0 0% 0 0 round 3px); }}
    }}
    @keyframes vit-scale-in {{
        from {{ opacity: 0; transform: scale(0.88); }}
        to   {{ opacity: 1; transform: scale(1); }}
    }}
    @keyframes vit-pulse-border {{
        0%, 100% {{ box-shadow: 0 0 0 0 var(--vit-primary)00; }}
        50%       {{ box-shadow: 0 0 0 3px var(--vit-primary)22; }}
    }}

    /* ── Apply animations ────────────────────────────────────────── */
    .vit-header    {{ animation: vit-fade-up 0.4s ease both; }}
    .info-strip    {{ animation: vit-fade-in 0.5s ease both; animation-delay: 0.1s; }}
    .metric-grid   {{ animation: vit-fade-up 0.35s ease both; animation-delay: 0.05s; }}
    .cat-overview  {{ animation: vit-fade-in 0.4s ease both; animation-delay: 0.08s; }}
    .result-card-wrap,
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card) {{
        animation: vit-fade-up 0.28s ease both;
    }}
    .context-banner {{ animation: vit-fade-in 0.3s ease both; }}
    .empty-state   {{ animation: vit-fade-in 0.3s ease both; }}
    .section-heading {{ animation: vit-slide-right 0.22s ease both; }}
    .report-card   {{ animation: vit-fade-up 0.2s ease both; }}

    /* Category pill counts pop in with a slight bounce */
    .cat-pill-count {{
        animation: vit-scale-in 0.35s cubic-bezier(0.34, 1.56, 0.64, 1) both;
    }}
    .cat-overview .cat-pill:nth-child(1) .cat-pill-count {{ animation-delay: 0.06s; }}
    .cat-overview .cat-pill:nth-child(2) .cat-pill-count {{ animation-delay: 0.12s; }}
    .cat-overview .cat-pill:nth-child(3) .cat-pill-count {{ animation-delay: 0.18s; }}
    .cat-overview .cat-pill:nth-child(4) .cat-pill-count {{ animation-delay: 0.24s; }}

    /* Probability bar — reveal left to right */
    .prob-bar-fill {{
        animation: vit-bar-grow 0.7s cubic-bezier(0.22, 1, 0.36, 1) both;
        animation-delay: 0.15s;
    }}

    /* Respect system reduced-motion preference */
    @media (prefers-reduced-motion: reduce) {{
        *, *::before, *::after {{
            animation-duration: 0.01ms !important;
            transition-duration: 0.01ms !important;
        }}
    }}

    /* ── Dark mode: deeper segmented control fix ─────────────────── */
    /* Target every possible DOM path Streamlit 1.5x might use */
    [data-testid="stSegmentedControl"] > div > div,
    [data-testid="stSegmentedControl"] > div > div > div {{
        background-color: var(--vit-input) !important;
        border-color: var(--vit-border) !important;
    }}
    [data-testid="stSegmentedControl"] label span,
    [data-testid="stSegmentedControl"] button span {{
        color: inherit !important;
    }}

    /* ── Result card polish ───────────────────────────────────────── */
    /* Badge glow on hover for reach/dream cards */
    .result-card-wrap.dream:hover {{
        border-left-color: var(--vit-dream-color) !important;
        box-shadow: var(--vit-hover-dream), var(--vit-shadow);
    }}
    .result-card-wrap.safe:hover {{
        border-left-color: var(--vit-safe-color) !important;
        box-shadow: var(--vit-hover-safe), var(--vit-shadow);
    }}
    .result-card-wrap.moderate:hover {{
        border-left-color: var(--vit-moderate-color) !important;
        box-shadow: var(--vit-hover-moderate), var(--vit-shadow);
    }}
    .result-card-wrap.unlikely:hover {{
        border-left-color: var(--vit-soft) !important;
        box-shadow: var(--vit-hover-unlikely), var(--vit-shadow);
    }}

    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--dream):hover {{
        border-left-color: var(--vit-dream-color) !important;
        box-shadow: var(--vit-hover-dream), var(--vit-shadow);
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--safe):hover {{
        border-left-color: var(--vit-safe-color) !important;
        box-shadow: var(--vit-hover-safe), var(--vit-shadow);
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--moderate):hover {{
        border-left-color: var(--vit-moderate-color) !important;
        box-shadow: var(--vit-hover-moderate), var(--vit-shadow);
    }}
    [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card--unlikely):hover {{
        border-left-color: var(--vit-soft) !important;
        box-shadow: var(--vit-hover-unlikely), var(--vit-shadow);
    }}

    /* Probability number — tighter letter spacing for big digits */
    .prob-number {{
        letter-spacing: -0.04em;
        font-variant-numeric: tabular-nums;
    }}

    /* Chip row slight gap increase for breathing room */
    .chip-row {{ gap: 0.6rem; }}

    /* ── Dark mode: sidebar improvements ─────────────────────────── */
    [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h3 {{
        font-size: 0.78rem !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        color: var(--vit-soft) !important;
        margin: 1.1rem 0 0.5rem !important;
    }}

    /* ── Cat-overview divider line ────────────────────────────────── */
    .cat-pill {{
        position: relative;
    }}

    /* ── Admin stat cards ─────────────────────────────────────────── */
    .admin-stat-card {{
        transition: transform 0.18s, box-shadow 0.18s;
    }}
    .admin-stat-card:hover {{
        transform: translateY(-2px);
        box-shadow: var(--vit-stat-card-hover);
    }}

    /* ── Stagger result rows inside each section ─────────────────── */
    /* Works on result-rows that are siblings or near-siblings */
    [data-testid="stVerticalBlock"] .result-card-wrap,
    [data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card) {{
        animation-delay: 0.04s;
    }}

    /* ── Rank display in sidebar ──────────────────────────────────── */
    .rank-big {{
        font-variant-numeric: tabular-nums;
        letter-spacing: -0.03em;
    }}

    /* ── Responsive ── */
    @media (max-width: 900px) {{
        [data-testid="stMainBlockContainer"] {{ padding: 1.25rem 1rem; }}
        .metric-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .result-row {{ grid-template-columns: 1fr; }}
        [data-testid="stMainBlockContainer"] [data-testid="stHorizontalBlock"]:has(span.vit-pred-card) {{
            flex-direction: column !important;
        }}
        .prob-panel {{
            align-items: flex-start;
            border-left: none;
            border-top: 1px solid var(--vit-border);
            padding-left: 0;
            padding-top: 1rem;
        }}
        .prob-panel.prob-panel--column {{
            align-items: flex-start;
            border-top: 1px solid var(--vit-border);
            padding-top: 0.85rem;
            margin-top: 0.25rem;
        }}
        .prob-bar-bg {{ width: 100%; }}
        .prob-label, .score-label, .cutoff-note {{ text-align: left; }}
        .report-type-grid {{ grid-template-columns: 1fr 1fr; }}
        .admin-stat-grid {{ grid-template-columns: repeat(2, 1fr); }}
        .admin-report-row {{ grid-template-columns: 1fr; }}
    }}

</style>
""",
    unsafe_allow_html=True,
)

# =====================================================
# PAGE HEADER
# =====================================================

st.markdown(
    """
<div class="vit-header">
    <div class="vit-header-icon">🎓</div>
    <div>
        <h1>VIT Counselling Predictor</h1>
        <p>Powered by real student data &nbsp;·&nbsp; Percentile-calibrated admission probability</p>
    </div>
</div>
<div class="info-strip">
    ℹ️ Enter your VITEEE rank on the left, apply filters, and click <strong>Get Recommendations</strong>
    to see your personalised predictions. The predictor uses a <strong>90th percentile cutoff model</strong>
    so outlier ranks don't inflate estimates.
</div>
""",
    unsafe_allow_html=True,
)
st.markdown(
    f"""
<div style="
    background: {theme["dream_bg"]};
    border: 1px solid {theme["dream_border"]};
    border-left: 5px solid {theme["dream_color"]};
    border-radius: 10px;
    padding: 0.85rem 1.1rem;
    font-size: 0.85rem;
    color: {theme["dream_text"]};
    margin-bottom: 1.5rem;
    line-height: 1.6;
">
    ⚠️ <strong>Disclaimer:</strong> This tool is <u>unofficial</u> and not affiliated with VIT or any
    official counselling authority. All predictions are based on historical data and statistical models
    and <strong>may not reflect actual results</strong>. Always verify with official VIT counselling
    resources before making any final decisions. Use at your own discretion.
</div>
""",
    unsafe_allow_html=True,
)

# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.markdown(
    f"""
<div style="
    background:linear-gradient(135deg,{theme["primary"]}18,{theme["primary_dark"]}0d);
    border:1px solid {theme["primary"]}30;
    border-radius:12px;
    padding:1rem 1rem 0.9rem;
    margin-bottom:1.1rem;
    display:flex;align-items:center;gap:0.85rem;
">
    <div style="
        width:40px;height:40px;border-radius:10px;flex-shrink:0;
        background:linear-gradient(135deg,{theme["primary"]},{theme["primary_dark"]});
        display:flex;align-items:center;justify-content:center;font-size:1.3rem;
        box-shadow:0 3px 10px {theme["primary"]}40;
    ">🎓</div>
    <div>
        <div style="font-size:0.88rem;font-weight:800;color:{theme["text"]};letter-spacing:-0.01em;line-height:1.2;">VIT Predictor</div>
        <div style="font-size:0.7rem;color:{theme["muted"]};margin-top:1px;">Admission probability tool</div>
    </div>
</div>
""",
    unsafe_allow_html=True,
)
st.sidebar.markdown("### ⚙️ Settings")

rank = st.sidebar.number_input(
    "Your VITEEE rank",
    min_value=1,
    max_value=250000,
    step=1,
    value=5000,
    help="Enter your VITEEE counselling rank (up to 2.5 lakh)",
)
st.sidebar.markdown(
    f'<div class="rank-big">{rank:,}</div>'
    f'<div style="font-size:0.8rem;color:var(--vit-muted);margin-bottom:0.85rem;">rank entered</div>',
    unsafe_allow_html=True,
)

sort_option = st.sidebar.selectbox(
    "Sort results by",
    [
        "Recommended",
        "Probability",
        "Fee Category",
        "Confidence Level",
        "Number of Responses",
        "Closing Rank",
    ],
)
sort_mapping = {
    "Recommended": "recommended",
    "Probability": "probability",
    "Fee Category": "fee",
    "Confidence Level": "confidence",
    "Number of Responses": "responses",
    "Closing Rank": "closing_rank",
}

prob_order = "desc"
if sort_option == "Probability":
    prob_order = st.sidebar.radio(
        "Order",
        ["High to Low (default)", "Low to High (riskier first)"],
        index=0,
        help="Choose 'Low to High' to see riskier options first.",
    )

results_limit = st.sidebar.slider(
    "Max results per category", min_value=5, max_value=30, value=10, step=5
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 🔍 Filters")

branch_filter = st.sidebar.segmented_control(
    "Quick branch filter", ["All", "CSE", "ECE+EEE"], default="All", key="branch_filter"
)

cse_programs = [
    "CSE Core",
    "CSE AIML",
    "CSE DS",
    "CSE Cybersecurity",
    "CSE Business Systems",
    "CSE Robotics",
    "CSE IoT",
    "CSE CPS",
]
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
    st.link_button(
        "📋 Submit 2025", "https://forms.gle/VG28i72zpKetFA4W6", width="stretch"
    )
with col2:
    st.info("Share your rank & allotment", icon="ℹ️")

st.sidebar.markdown("---")

predict_button = st.sidebar.button(
    "🚀 Get Recommendations", width="stretch", type="primary", key="predict_btn"
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
        f'<div class="prob-bar-fill" style="width:{min(prob, 100):.1f}%;background:{c};"></div>'
        f"</div>"
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


def make_card_key(r):
    return f"{r['campus']}_{r['branch']}_{r['fee']}".replace(" ", "_")


def result_card_parts(r, rank, kind, *, prob_extra_class=""):
    """Left column (details) + probability panel HTML. Use prob_extra_class for column layout variant."""
    diff = r["rank_difference"]
    sign = "+" if diff >= 0 else "−"
    margin_label = f"{sign}{abs(diff):,}"
    margin_sub = "buffer ✓" if diff >= 0 else "shortfall ✗"

    badge_map = {
        "safe": "badge-safe",
        "moderate": "badge-moderate",
        "dream": "badge-dream",
        "unlikely": "badge-unlikely",
    }
    badge_text = {
        "safe": "Safe ✓",
        "moderate": "Moderate",
        "dream": "Reach",
        "unlikely": "Very Unlikely",
    }
    badge_html = f'<span class="badge {badge_map[kind]}">{badge_text[kind]}</span>'

    if r.get("data_insufficient"):
        insuff_badge = (
            '<span class="badge badge-insufficient">'
            "⚠ Data Insufficient"
            "</span>"
        )
    else:
        insuff_badge = ""

    conf_label = confidence_clean(r["confidence"])
    conf_class = chip_class_from_confidence(r["confidence_pct"])
    buf_class = chip_class_from_buffer(diff)

    if r.get("data_insufficient"):
        orig_prob = r.get("original_probability", r["probability"])
        dom_fee = r.get("dominant_fee", "a cheaper category")
        reason = (
            f"<strong>Data Insufficient</strong> — "
            f"Fee Category <strong>{dom_fee}</strong> of the same branch/campus already shows "
            f"<strong>{r['probability']:.0f}%</strong> probability (higher than this category's "
            f"raw <strong>{orig_prob:.0f}%</strong>). "
            f"Probability shown here is adjusted to match — prefer Cat {dom_fee} if possible. "
            f"Submit more data to improve this estimate."
        )
    else:
        reason = recommendation_reason(r)

    branch = escape(r["branch"])
    campus = escape(r["campus"])
    sd_val = r.get("std_dev", 0)

    if sd_val > 1500:
        spread_chip = (
            '<div class="chip warn">'
            '<span class="chip-label">Spread</span>'
            f'<span class="chip-value">&#177;{sd_val:,}</span>'
            '<span class="chip-sub">rank std dev</span>'
            "</div>"
        )
    else:
        spread_chip = ""

    if r.get("data_insufficient"):
        orig_prob = r.get("original_probability", r["probability"])
        orig_chip = (
            '<div class="chip warn">'
            '<span class="chip-label">Raw Prob</span>'
            f'<span class="chip-value">{orig_prob:.0f}%</span>'
            '<span class="chip-sub">before adjust</span>'
            "</div>"
        )
    else:
        orig_chip = ""

    true_max = r.get("true_max", r["closing_rank"])
    prob_bar_html = prob_bar(r["probability"], kind)
    badge_label = badge_text[kind]

    prob_classes = "prob-panel"
    if prob_extra_class:
        prob_classes += f" {prob_extra_class.strip()}"

    left_html = (
        f'<div style="min-width:0;">'
        f'<div class="result-topline">'
        f'<span class="result-branch">{branch}</span>'
        f"{badge_html}"
        f"{insuff_badge}"
        f"</div>"
        f'<div class="chip-row">'
        f'<div class="chip"><span class="chip-label">Campus</span><span class="chip-value">{campus}</span></div>'
        f'<div class="chip"><span class="chip-label">Fee Cat.</span><span class="chip-value">{r["fee"]}</span></div>'
        f'<div class="chip"><span class="chip-label">Cutoff Rank</span><span class="chip-value">{r["closing_rank"]:,}</span><span class="chip-sub">90th pct &#183; true max {true_max:,}</span></div>'
        f'<div class="chip {buf_class}"><span class="chip-label">Rank Margin</span><span class="chip-value">{margin_label}</span><span class="chip-sub">{margin_sub}</span></div>'
        f'<div class="chip {conf_class}"><span class="chip-label">Confidence</span><span class="chip-value">{conf_label}</span><span class="chip-sub">{r["responses"]} responses</span></div>'
        f"{orig_chip}"
        f"{spread_chip}"
        f"</div>"
        f'<div class="result-note">{reason}</div>'
        f"</div>"
    )

    prob_html = (
        f'<div class="{prob_classes}">'
        f'<div class="prob-number {kind}">{r["probability"]:.0f}%</div>'
        f'<div class="prob-label">{badge_label} chance</div>'
        f"{prob_bar_html}"
        f'<div class="cutoff-note">cutoff {r["closing_rank"]:,}</div>'
        f'<div class="score-label">score {r["recommendation_score"]:.1f}</div>'
        f"</div>"
    )

    return left_html, prob_html


def result_row_html(r, rank, kind):
    """Single HTML row for “already reported” cards (classic two-column grid inside one wrap)."""
    left_html, prob_html = result_card_parts(r, rank, kind)
    return f'<div class="result-row">{left_html}{prob_html}</div>'


def wrap_result_card(inner_html, kind, *, trailing_html=""):
    classes = f"result-card-wrap {kind}"
    return f'<div class="{classes}">{inner_html}{trailing_html}</div>'


REPORT_TYPES = [
    {
        "key": "wrong_cutoff",
        "icon": "📊",
        "label": "Wrong cutoff",
        "hint": "Cutoff rank seems incorrect based on your actual allotment.",
    },
    {
        "key": "got_allotted",
        "icon": "✅",
        "label": "Got allotted",
        "hint": "You were allotted this branch/campus at your rank.",
    },
    {
        "key": "not_allotted",
        "icon": "❌",
        "label": "Not allotted",
        "hint": "You did NOT get this despite it showing Safe/Moderate.",
    },
    {
        "key": "prob_high",
        "icon": "📈",
        "label": "Prob too high",
        "hint": "Admission probability appears inflated.",
    },
    {
        "key": "prob_low",
        "icon": "📉",
        "label": "Prob too low",
        "hint": "Admission probability appears underestimated.",
    },
    {
        "key": "other",
        "icon": "💬",
        "label": "Other",
        "hint": "Something else is wrong with this prediction.",
    },
]


def render_result_with_report(r, rank, kind):
    card_key = make_card_key(r)

    # Already submitted — success sits inside the same card chrome as the prediction
    if st.session_state.report_submitted.get(card_key):
        thanks_html = (
            '<div class="report-success report-success--embedded">'
            "✅ Thanks for your report — it helps improve the model for everyone!"
            "</div>"
        )
        st.markdown(
            wrap_result_card(
                result_row_html(r, rank, kind), kind, trailing_html=thanks_html
            ),
            unsafe_allow_html=True,
        )
        return

    is_open = st.session_state.report_open.get(card_key, False)

    left_html, prob_html = result_card_parts(
        r, rank, kind, prob_extra_class="prob-panel--column"
    )
    marker = f'<span class="vit-pred-card vit-pred-card--{kind}" aria-hidden="true"></span>'
    col_main, col_prob = st.columns([3.55, 1])
    with col_main:
        st.markdown(
            marker + f'<div class="vit-pred-col-main">{left_html}</div>',
            unsafe_allow_html=True,
        )
    with col_prob:
        st.markdown(
            f'<div class="vit-pred-col-side">{prob_html}</div>',
            unsafe_allow_html=True,
        )
        btn_label = "🚩 Hide" if is_open else "🚩 Report"
        if st.button(
            btn_label,
            key=f"report_btn_{card_key}",
            help="Flag this prediction as inaccurate or add real-world data",
            use_container_width=True,
        ):
            st.session_state.report_open[card_key] = not is_open
            st.rerun()

    if is_open:
        branch_esc = escape(r["branch"])
        campus_esc = escape(r["campus"])
        st.markdown(
            f'<div class="report-card">'
            f'<div class="report-card-header">'
            f'<div class="report-card-title">🚩 Report prediction'
            f'<span class="report-card-sub">— {branch_esc} · {campus_esc} · Fee Cat {r["fee"]}</span>'
            f"</div>"
            f"</div>"
            f'<div class="report-card-body">',
            unsafe_allow_html=True,
        )

        if st.session_state.get(f"report_save_err_{card_key}"):
            st.error(
                "Last report submission did not save. Please try submitting again."
            )

        # Issue type selector
        st.markdown(
            '<div style="font-size:0.82rem;font-weight:700;color:var(--vit-text);margin-bottom:0.5rem;">What\'s wrong with this prediction?</div>',
            unsafe_allow_html=True,
        )
        type_cols = st.columns(3)
        selected_type = st.session_state.report_type.get(card_key, None)
        for i, rtype in enumerate(REPORT_TYPES):
            with type_cols[i % 3]:
                is_selected = selected_type == rtype["key"]
                btn_style = "primary" if is_selected else "secondary"
                if st.button(
                    f"{rtype['icon']} {rtype['label']}",
                    key=f"rtype_{card_key}_{rtype['key']}",
                    type=btn_style,
                    use_container_width=True,
                ):
                    st.session_state.report_type[card_key] = rtype["key"]
                    st.rerun()

        # Show hint for selected type
        if selected_type:
            matched = next(
                (rt for rt in REPORT_TYPES if rt["key"] == selected_type), None
            )
            if matched:
                st.markdown(
                    f'<div class="report-hint">💡 {matched["hint"]}</div>',
                    unsafe_allow_html=True,
                )

        # Free-text reason
        reason_text = st.text_area(
            "Additional details *(optional)*",
            value=st.session_state.report_text.get(card_key, ""),
            placeholder="e.g. Got allotted CSE Core at Vellore with rank 8,200 — cutoff shown is 7,000 which seems low…",
            key=f"report_text_{card_key}",
            height=80,
        )

        col_submit, col_cancel, col_pad2 = st.columns([1.2, 1, 4])
        with col_submit:
            submit_disabled = not selected_type
            if st.button(
                "✅ Submit Report",
                key=f"report_submit_{card_key}",
                type="primary",
                disabled=submit_disabled,
            ):
                st.session_state.report_text[card_key] = reason_text
                ok = submit_report(
                    user_rank=rank,
                    campus=r["campus"],
                    branch=r["branch"],
                    fee=r["fee"],
                    probability=r["probability"],
                    chance=r["chance"],
                    report_type=selected_type,  # ← separate column in DB
                    reason_text=reason_text,  # ← clean, no [tag] prefix
                )
                if ok:
                    st.session_state.report_submitted[card_key] = True
                    st.session_state.report_open[card_key] = False
                    st.session_state.pop(f"report_save_err_{card_key}", None)
                    st.rerun()
                else:
                    st.session_state.report_submitted[card_key] = False
                    st.session_state.report_open[card_key] = True
                    st.session_state[f"report_save_err_{card_key}"] = True
                    st.error(
                        "Report could not be saved. Please try again or contact the admin."
                    )
        with col_cancel:
            if st.button("✖ Cancel", key=f"report_cancel_{card_key}"):
                st.session_state.report_open[card_key] = False
                st.rerun()

        if not selected_type:
            st.caption("⬆️ Please select an issue type before submitting.")

        st.markdown(
            '<div class="report-footer">Reports are anonymous. '
            "Include your actual rank and allotted branch/campus if known — "
            "it helps the model improve for everyone.</div>"
            "</div></div>",
            unsafe_allow_html=True,
        )


def section_header(icon, title, count):
    st.markdown(
        f'<div class="section-heading">{icon} {title} &nbsp;·&nbsp; {count} option{"s" if count != 1 else ""}</div>',
        unsafe_allow_html=True,
    )


# =====================================================
# RESULTS
# =====================================================

# ── Step 1: Compute results only when the button is clicked ─────────────────
if predict_button:
    if sort_option == "Probability":
        _sort = (
            "probability_asc"
            if prob_order == "Low to High (riskier first)"
            else "probability"
        )
    else:
        _sort = sort_mapping[sort_option]

    _all_results = recommend(rank, sort_by=_sort)
    _fees_int = [int(f) for f in selected_fees]
    _filtered = [
        r
        for r in _all_results
        if r["campus"] in selected_campuses
        and r["branch"] in selected_branches
        and r["fee"] in _fees_int
    ]
    # Persist results so they survive reruns triggered by report-panel buttons
    st.session_state["_pred_rank"] = rank
    st.session_state["_pred_results"] = _filtered
    st.session_state["_pred_ready"] = True

# ── Step 2: Render results on EVERY rerun (report panel stays interactive) ──
if st.session_state.get("_pred_ready"):
    _rank = st.session_state["_pred_rank"]
    filtered_results = st.session_state["_pred_results"]

    if not filtered_results:
        st.markdown(
            '<div class="context-banner dream">'
            "No options match your filters. Try selecting more campuses, branches, or fee categories."
            "</div>",
            unsafe_allow_html=True,
        )
    else:
        rank_stats = get_rank_statistics(_rank)
        safe_list = [r for r in filtered_results if r["chance"] == "Safe"]
        moderate_list = [r for r in filtered_results if r["chance"] == "Moderate"]
        dream_list = [r for r in filtered_results if r["chance"] == "Dream"]
        unlikely_list = [r for r in filtered_results if r["chance"] == "Very Unlikely"]
        avg_prob = sum(r["probability"] for r in filtered_results) / len(
            filtered_results
        )

        st.markdown(
            f"""
        <div class="metric-grid">
            <div class="metric-card">
                <div class="metric-card-label">Your rank</div>
                <div class="metric-card-value">{_rank:,}</div>
                <div class="metric-card-sub">Top {rank_stats["percentile"]:.1f}% of candidates</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Total options</div>
                <div class="metric-card-value">{len(filtered_results)}</div>
                <div class="metric-card-sub">of {rank_stats["total_options"]} overall</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Reach options</div>
                <div class="metric-card-value">{len(dream_list)}</div>
                <div class="metric-card-sub">{"High-risk, high-reward" if dream_list else "None in current filters"}</div>
            </div>
            <div class="metric-card">
                <div class="metric-card-label">Avg probability</div>
                <div class="metric-card-value">{avg_prob:.1f}%</div>
                <div class="metric-card-sub">across all filtered options</div>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        # ── Category overview bar (always visible) ─────────────────────────
        sc = theme["safe_color"]
        mc = theme["moderate_color"]
        dc = theme["dream_color"]
        uc = theme["muted"]
        st.markdown(
            f"""
            <div class="cat-overview">
              <div class="cat-pill" style="border-top:3px solid {sc};">
                <span class="cat-pill-icon">✅</span>
                <span class="cat-pill-count" style="color:{sc};">{len(safe_list)}</span>
                <span class="cat-pill-label" style="color:{sc};">Primary</span>
              </div>
              <div class="cat-pill" style="border-top:3px solid {mc};">
                <span class="cat-pill-icon">⚡</span>
                <span class="cat-pill-count" style="color:{mc};">{len(moderate_list)}</span>
                <span class="cat-pill-label" style="color:{mc};">Backup</span>
              </div>
              <div class="cat-pill" style="border-top:3px solid {dc};">
                <span class="cat-pill-icon">🔥</span>
                <span class="cat-pill-count" style="color:{dc};">{len(dream_list)}</span>
                <span class="cat-pill-label" style="color:{dc};">Reach</span>
              </div>
              <div class="cat-pill" style="border-top:3px solid {uc};">
                <span class="cat-pill-icon">⛔</span>
                <span class="cat-pill-count" style="color:{uc};">{len(unlikely_list)}</span>
                <span class="cat-pill-label" style="color:{uc};">Skip</span>
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # ── 🔥 Reach / Dream (always shown first) ──────────────────────────
        section_header("🔥", "Reach picks — possible but risky", len(dream_list))
        if dream_list:
            st.markdown(
                '<div class="context-banner dream">Outside or near the observed cutoff — possible but a stretch. Add these to aim high, but always pair with safer backups.</div>',
                unsafe_allow_html=True,
            )
            for r in dream_list[:results_limit]:
                render_result_with_report(r, _rank, "dream")
        else:
            st.markdown(
                '<div class="empty-state">'
                "<strong>No reach options</strong><br>"
                "Your rank is safely within cutoffs for all filtered programs — nothing is a stretch pick!"
                "</div>",
                unsafe_allow_html=True,
            )

        # ── ⚡ Backup / Moderate (always shown second) ───────────────────────
        section_header("⚡", "Backup picks — possible but tighter", len(moderate_list))
        if moderate_list:
            st.markdown(
                '<div class="context-banner moderate">These are within reach but have a narrow buffer, high spread, or limited data. Good backups.</div>',
                unsafe_allow_html=True,
            )
            for r in moderate_list[:results_limit]:
                render_result_with_report(r, _rank, "moderate")
        else:
            st.markdown(
                '<div class="empty-state">'
                "<strong>No backup options</strong><br>"
                "Either your rank is very strong (everything is already Primary!), or try expanding your filters."
                "</div>",
                unsafe_allow_html=True,
            )

        # ── ✅ Primary / Safe (always shown third) ──────────────────────────
        section_header("✅", "Primary picks — strong rank fit", len(safe_list))
        if safe_list:
            st.markdown(
                '<div class="context-banner safe">Your rank sits comfortably inside these cutoffs. Prioritise by campus preference and fee category.</div>',
                unsafe_allow_html=True,
            )
            for r in safe_list[:results_limit]:
                render_result_with_report(r, _rank, "safe")
        else:
            st.markdown(
                '<div class="empty-state">'
                "<strong>No primary picks for this rank</strong><br>"
                "Your rank may be outside the cutoffs for the selected programs. Try expanding campus or branch filters."
                "</div>",
                unsafe_allow_html=True,
            )

        # ── ⛔ Impossible / Unlikely (always shown last) ─────────────────────
        section_header("⛔", "Impossible — far outside cutoff", len(unlikely_list))
        if unlikely_list:
            st.markdown(
                '<div class="context-banner dream">These are well outside the observed cutoff. Listed for awareness only — not worth applying.</div>',
                unsafe_allow_html=True,
            )
            _show_unlikely = unlikely_list[: min(results_limit, 5)]
            for r in _show_unlikely:
                render_result_with_report(r, _rank, "unlikely")
            if len(unlikely_list) > len(_show_unlikely):
                st.caption(
                    f"Showing {len(_show_unlikely)} of {len(unlikely_list)} — expand filters or raise the limit to see more."
                )
        else:
            st.markdown(
                '<div class="empty-state">'
                "<strong>Nothing impossible here</strong><br>"
                "No programs are well outside your reach for the current filters."
                "</div>",
                unsafe_allow_html=True,
            )

# =====================================================
# DATASET ANALYTICS
# =====================================================

st.markdown("---")
st.markdown(
    '<div class="section-heading">📊 Dataset statistics</div>', unsafe_allow_html=True
)

col1, col2, col3, col4 = st.columns(4)
if master_df.empty:
    with col1:
        st.metric("Total responses", 0)
    with col2:
        st.metric("Best rank", "—")
    with col3:
        st.metric("Worst rank", "—")
    with col4:
        st.metric("Unique variations", 0)
else:
    with col1:
        st.metric("Total responses", len(master_df))
    with col2:
        st.metric("Best rank", f"{int(master_df['Rank'].min()):,}")
    with col3:
        st.metric("Worst rank", f"{int(master_df['Rank'].max()):,}")
    with col4:
        st.metric(
            "Unique variations",
            len(master_df[["Campus", "Branch", "Fee"]].drop_duplicates()),
        )

CHART_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter, Arial, sans-serif", size=13, color=theme["text"]),
    title=dict(font=dict(size=17, color=theme["text"]), x=0.02, xanchor="left"),
    margin=dict(t=58, b=48, l=20, r=24),
    height=430,
    hoverlabel=dict(
        bgcolor=theme["hover_bg"], font_size=13, font_color=theme["hover_text"]
    ),
)


def readable_count_series(series, limit=12):
    counts = series.value_counts()
    if len(counts) <= limit:
        return counts
    visible = counts.head(limit - 1)
    visible.loc["Other"] = counts.iloc[limit - 1 :].sum()
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
        fig.update_traces(
            marker_line_width=0,
            text=branch_counts.values,
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(
            values=branch_counts.values,
            names=branch_counts.index,
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
            x=campus_counts.index,
            y=campus_counts.values,
            labels={"x": "Campus", "y": "Responses"},
            title="Responses by campus",
            color=campus_counts.values,
            color_continuous_scale=["#bae6fd", "#0284c7", "#0c4a6e"],
        )
        fig.update_layout(coloraxis_showscale=False)
        style_chart(fig)
        fig.update_traces(
            marker_line_width=0,
            text=campus_counts.values,
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(
            values=campus_counts.values,
            names=campus_counts.index,
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
            x=fee_labels,
            y=fee_counts.values,
            labels={"x": "Fee category", "y": "Students"},
            title="Students by fee category",
            color=fee_counts.values,
            color_continuous_scale=["#bbf7d0", "#16a34a", "#14532d"],
        )
        fig.update_layout(coloraxis_showscale=False)
        style_chart(fig)
        fig.update_traces(
            marker_line_width=0,
            text=fee_counts.values,
            textposition="outside",
            cliponaxis=False,
        )
        st.plotly_chart(fig, width="stretch")
    with c2:
        fig = px.pie(
            values=fee_counts.values,
            names=fee_labels,
            title="Share by fee category",
            color_discrete_sequence=px.colors.qualitative.Pastel,
        )
        style_pie(fig)
        st.plotly_chart(fig, width="stretch")

with tab4:
    c1, c2 = st.columns([0.7, 0.3])
    with c1:
        search_branch = st.selectbox(
            "Filter by branch", ["All"] + sorted(master_df["Branch"].unique().tolist())
        )
    with c2:
        display_count = st.slider(
            "Rows to show", min_value=10, max_value=100, value=20, step=10
        )
    display_df = (
        master_df
        if search_branch == "All"
        else master_df[master_df["Branch"] == search_branch]
    )
    st.dataframe(
        display_df.head(display_count),
        width="stretch",
        height=400,
        column_config={
            "Rank": st.column_config.NumberColumn(format="%d"),
            "Fee": st.column_config.NumberColumn(format="Category %d"),
        },
    )
    st.caption(
        f"Showing {min(display_count, len(display_df)):,} of {len(display_df):,} records"
    )


# =====================================================
# ADMIN PANEL  (access via ?admin=1 — no link shown)
# =====================================================

query_params = st.query_params
if query_params.get("admin") == "1":
    st.markdown("---")

    # ── Auth ─────────────────────────────────────────────────────────────
    try:
        _has_password_secret = "admin_password" in st.secrets
    except Exception:
        _has_password_secret = False

    if "admin_authed" not in st.session_state:
        st.session_state.admin_authed = not _has_password_secret

    if not st.session_state.admin_authed:
        # ── Login card ────────────────────────────────────────────────────
        st.markdown(
            """
        <div style="max-width:420px;margin:3rem auto 0;">
            <div style="
                background:linear-gradient(135deg,#1e1b4b,#312e81);
                border-radius:14px 14px 0 0;
                padding:1.5rem 2rem 1.2rem;
                text-align:center;">
                <div style="font-size:2.5rem;margin-bottom:0.4rem;">🔐</div>
                <div style="font-size:1.25rem;font-weight:800;color:#ffffff;">Admin Login</div>
                <div style="font-size:0.85rem;color:rgba(255,255,255,0.65);margin-top:0.2rem;">
                    VIT Counselling Predictor — restricted area
                </div>
            </div>
        """,
            unsafe_allow_html=True,
        )
        with st.container():
            pw = st.text_input(
                "Password",
                type="password",
                key="admin_pw",
                placeholder="Enter admin password…",
            )
            if st.button(
                "🔓 Login", type="primary", key="admin_login", use_container_width=True
            ):
                correct = st.secrets.get("admin_password", "")
                if pw == correct:
                    st.session_state.admin_authed = True
                    st.rerun()
                else:
                    st.error("❌ Incorrect password. Try again.")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        # ── Admin Dashboard ───────────────────────────────────────────────
        st.markdown(
            """
        <div class="admin-header">
            <div class="admin-header-icon">🔐</div>
            <div>
                <h2>Admin Dashboard</h2>
                <p>Reported predictions — user-submitted accuracy flags</p>
            </div>
        </div>
        """,
            unsafe_allow_html=True,
        )

        col_refresh, col_logout, col_pad = st.columns([1, 1, 6])
        with col_refresh:
            if st.button("🔄 Refresh", key="admin_refresh"):
                st.rerun()
        with col_logout:
            if st.button("🔒 Logout", key="admin_logout"):
                st.session_state.admin_authed = False
                st.rerun()

        with st.spinner("Loading reports…"):
            reports_df = get_reports()

        if reports_df is None:
            st.error(
                "Failed to load reports — check Supabase reports table connection."
            )
        elif reports_df.empty:
            st.info("📭 No reports submitted yet.")
        else:
            total = len(reports_df)
            with_reason = int(
                (reports_df.get("Reason", pd.Series()) != "(no reason given)").sum()
            )
            unique_comb = (
                reports_df[["Campus", "Branch"]].drop_duplicates().__len__()
                if "Campus" in reports_df.columns
                else 0
            )

            # Sort most recent first
            try:
                reports_df = reports_df.sort_values("Timestamp", ascending=False)
            except Exception:
                pass

            # ── Stat cards ────────────────────────────────────────────────
            st.markdown(
                f"""
            <div class="admin-stat-grid">
                <div class="admin-stat-card">
                    <div class="admin-stat-label">Total reports</div>
                    <div class="admin-stat-value">{total}</div>
                    <div class="admin-stat-sub">all time</div>
                </div>
                <div class="admin-stat-card">
                    <div class="admin-stat-label">With details</div>
                    <div class="admin-stat-value">{with_reason}</div>
                    <div class="admin-stat-sub">have reason text</div>
                </div>
                <div class="admin-stat-card">
                    <div class="admin-stat-label">Without details</div>
                    <div class="admin-stat-value">{total - with_reason}</div>
                    <div class="admin-stat-sub">type-only reports</div>
                </div>
                <div class="admin-stat-card">
                    <div class="admin-stat-label">Unique combos</div>
                    <div class="admin-stat-value">{unique_comb}</div>
                    <div class="admin-stat-sub">branch × campus pairs</div>
                </div>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # ── Charts row ────────────────────────────────────────────────
            if (
                "Predicted Chance" in reports_df.columns
                or "Campus" in reports_df.columns
            ):
                chart_tab1, chart_tab2 = st.tabs(["By Predicted Chance", "By Campus"])

                with chart_tab1:
                    if "Predicted Chance" in reports_df.columns:
                        chance_counts = reports_df["Predicted Chance"].value_counts()
                        chance_colors = {
                            "Safe": theme["safe_color"],
                            "Moderate": theme["moderate_color"],
                            "Dream": theme["dream_color"],
                            "Very Unlikely": theme["soft"],
                        }
                        colors_list = [
                            chance_colors.get(c, "#94a3b8") for c in chance_counts.index
                        ]
                        fig = go.Figure(
                            go.Bar(
                                x=chance_counts.index.tolist(),
                                y=chance_counts.values.tolist(),
                                marker_color=colors_list,
                                text=chance_counts.values.tolist(),
                                textposition="outside",
                            )
                        )
                        fig.update_layout(
                            **CHART_THEME,
                            title_text="Reports by predicted chance category",
                            showlegend=False,
                            xaxis=dict(
                                tickfont=dict(color=theme["muted"]),
                                gridcolor=theme["grid"],
                            ),
                            yaxis=dict(
                                tickfont=dict(color=theme["muted"]),
                                gridcolor=theme["grid"],
                            ),
                        )
                        fig.update_layout(height=300)
                        st.plotly_chart(fig, width="stretch")

                with chart_tab2:
                    if "Campus" in reports_df.columns:
                        campus_counts_r = reports_df["Campus"].value_counts()
                        fig2 = px.pie(
                            values=campus_counts_r.values,
                            names=campus_counts_r.index,
                            title="Reports by campus",
                            color_discrete_sequence=px.colors.qualitative.Bold,
                        )
                        style_pie(fig2)
                        fig2.update_layout(height=300)
                        st.plotly_chart(fig2, width="stretch")

            # ── Filters ───────────────────────────────────────────────────
            st.markdown(
                '<div class="section-heading">🔍 Filter reports</div>',
                unsafe_allow_html=True,
            )
            fc1, fc2, fc3 = st.columns(3)
            with fc1:
                filter_chance = st.multiselect(
                    "Predicted chance",
                    options=["Safe", "Moderate", "Dream", "Very Unlikely"],
                    default=[],
                    key="admin_filter_chance",
                )
            with fc2:
                filter_campus = st.multiselect(
                    "Campus",
                    options=sorted(reports_df["Campus"].unique().tolist())
                    if "Campus" in reports_df.columns
                    else [],
                    default=[],
                    key="admin_filter_campus",
                )
            with fc3:
                filter_branch = st.multiselect(
                    "Branch",
                    options=sorted(reports_df["Branch"].unique().tolist())
                    if "Branch" in reports_df.columns
                    else [],
                    default=[],
                    key="admin_filter_branch",
                )

            display_reports = reports_df.copy()
            if filter_chance:
                display_reports = display_reports[
                    display_reports["Predicted Chance"].isin(filter_chance)
                ]
            if filter_campus:
                display_reports = display_reports[
                    display_reports["Campus"].isin(filter_campus)
                ]
            if filter_branch:
                display_reports = display_reports[
                    display_reports["Branch"].isin(filter_branch)
                ]

            st.markdown(
                f'<div class="section-heading">📋 Reports &nbsp;·&nbsp; {len(display_reports)} of {total}</div>',
                unsafe_allow_html=True,
            )

            # ── Report cards ──────────────────────────────────────────────
            view_mode = st.segmented_control(
                "View as", ["Cards", "Table"], default="Cards", key="admin_view_mode"
            )

            if view_mode == "Cards":
                for _, row in display_reports.iterrows():
                    report_id = row.get("id", "")
                    chance_val = row.get("Predicted Chance", "—")
                    chance_color_map = {
                        "Safe": theme["safe_color"],
                        "Moderate": theme["moderate_color"],
                        "Dream": theme["dream_color"],
                        "Very Unlikely": theme["soft"],
                    }
                    cc = chance_color_map.get(chance_val, theme["soft"])

                    reason_raw = str(row.get("Reason", ""))
                    is_no_reason = reason_raw in ("(no reason given)", "", "nan")
                    reason_class = "no-reason" if is_no_reason else ""
                    reason_display = (
                        "No details provided." if is_no_reason else escape(reason_raw)
                    )

                    rtype_raw = str(row.get("Report Type", "other") or "other")
                    rtype_meta = REPORT_TYPE_META.get(
                        rtype_raw, {"label": rtype_raw, "color": "#64748b"}
                    )
                    report_type_badge = (
                        f'<span style="'
                        f"font-size:0.72rem;font-weight:700;"
                        f"padding:3px 10px;border-radius:99px;"
                        f"background:{rtype_meta['color']}22;"
                        f"color:{rtype_meta['color']};"
                        f'border:1px solid {rtype_meta["color"]}55;">'
                        f"{escape(str(rtype_meta['label']))}"
                        f"</span>"
                    )

                    ts = str(row.get("Timestamp", ""))[:16]

                    st.markdown(
                        f"""
                    <div style="
                        background:var(--vit-surface);
                        border:1px solid var(--vit-border);
                        border-left:5px solid {cc};
                        border-radius:10px;
                        padding:1rem 1.25rem;
                        margin-bottom:0.6rem;
                        box-shadow:var(--vit-shadow);
                    ">
                        <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;margin-bottom:0.7rem;">
                            <div>
                                <span style="font-size:1rem;font-weight:800;color:var(--vit-text);">
                                    {escape(str(row.get("Branch", "—")))}
                                </span>
                                <span style="font-size:0.82rem;color:var(--vit-muted);margin-left:0.5rem;">
                                    {escape(str(row.get("Campus", "—")))} · Fee Cat {row.get("Fee Category", "—")}
                                </span>
                            </div>
                            <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
                                <span style="
                                    font-size:0.72rem;font-weight:700;
                                    padding:3px 10px;border-radius:99px;
                                    background:{cc}22;color:{cc};
                                    border:1px solid {cc}55;
                                ">{chance_val}</span>
                                <!-- Report Type badge -->
                                {report_type_badge}
                                <span style="font-size:0.75rem;color:var(--vit-muted);">
                                    Prob: {row.get("Predicted Probability (%)", "—")}%
                                </span>
                                <span style="font-size:0.75rem;color:var(--vit-muted);">
                                    Rank: {row.get("User Rank", "—"):,}
                                </span>
                                <span style="font-size:0.72rem;color:var(--vit-soft);">{ts}</span>
                            </div>
                        </div>
                        <div class="admin-report-reason {reason_class}">{reason_display}</div>
                    </div>
                    """,
                        unsafe_allow_html=True,
                    )

                    # ── Delete button / inline confirmation ────────────────
                    is_pending = report_id != "" and str(
                        st.session_state["_admin_delete_pending"]
                    ) == str(report_id)
                    if is_pending:
                        st.markdown(
                            '<div style="font-size:0.82rem;color:#ef4444;font-weight:600;'
                            'margin:-0.3rem 0 0.4rem 0.2rem;">'
                            "⚠️ Delete this report? This cannot be undone."
                            "</div>",
                            unsafe_allow_html=True,
                        )
                        col_yes, col_no, col_pad = st.columns([1, 1, 7])
                        with col_yes:
                            if st.button(
                                "🗑️ Yes, delete",
                                key=f"del_confirm_{report_id}",
                                type="primary",
                                use_container_width=True,
                            ):
                                ok = db.delete_report(report_id)
                                st.session_state["_admin_delete_pending"] = None
                                if ok:
                                    st.toast("Report deleted.", icon="✅")
                                else:
                                    st.toast(
                                        "Could not delete report — check console.",
                                        icon="❌",
                                    )
                                st.rerun()
                        with col_no:
                            if st.button(
                                "✖ Cancel",
                                key=f"del_cancel_{report_id}",
                                use_container_width=True,
                            ):
                                st.session_state["_admin_delete_pending"] = None
                                st.rerun()
                    else:
                        col_del, col_pad = st.columns([1, 9])
                        with col_del:
                            if st.button(
                                "🗑️ Remove",
                                key=f"del_btn_{report_id}",
                                help="Remove this report from the database",
                                use_container_width=True,
                            ):
                                st.session_state["_admin_delete_pending"] = report_id
                                st.rerun()

                    st.markdown(
                        '<div style="margin-bottom:0.5rem;"></div>',
                        unsafe_allow_html=True,
                    )
            else:
                st.dataframe(
                    display_reports,
                    use_container_width=True,
                    height=500,
                    column_config={
                        "Predicted Probability (%)": st.column_config.NumberColumn(
                            format="%.1f%%"
                        ),
                        "User Rank": st.column_config.NumberColumn(format="%d"),
                        "Fee Category": st.column_config.NumberColumn(
                            format="Category %d"
                        ),
                    },
                )
            st.caption(f"Showing {len(display_reports):,} of {total:,} reports")

            # CSV download
            csv = display_reports.to_csv(index=False).encode("utf-8")
            st.download_button(
                "⬇️ Download as CSV",
                data=csv,
                file_name="vit_prediction_reports.csv",
                mime="text/csv",
                key="admin_csv_download",
            )

# =====================================================
# FOOTER
# =====================================================

st.markdown("---")

c1, c2, c3 = st.columns(3)
_card = (
    "background:{bg};border:1px solid {border};border-left:3px solid {accent};"
    "border-radius:10px;padding:0.9rem 1.1rem;display:flex;align-items:center;"
    "gap:0.85rem;box-shadow:{shadow};"
)
with c1:
    st.markdown(
        f'<div style="{_card.format(bg=theme["surface"], border=theme["border"], accent=theme["primary"], shadow=theme["shadow"])}">'
        f'<span style="font-size:1.4rem;flex-shrink:0;">📊</span>'
        f'<div><div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:{theme["muted"]}">Data updated</div>'
        f'<div style="font-size:0.92rem;font-weight:700;color:{theme["text"]};margin-top:2px;">{pd.Timestamp.now().strftime("%Y-%m-%d")}</div></div></div>',
        unsafe_allow_html=True,
    )
with c2:
    st.markdown(
        f'<div style="{_card.format(bg=theme["surface"], border=theme["border"], accent=theme["safe_color"], shadow=theme["shadow"])}">'
        f'<span style="font-size:1.4rem;flex-shrink:0;">📌</span>'
        f'<div><div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:{theme["muted"]}">Student records</div>'
        f'<div style="font-size:0.92rem;font-weight:700;color:{theme["text"]};margin-top:2px;">{len(master_df):,}</div></div></div>',
        unsafe_allow_html=True,
    )
with c3:
    st.markdown(
        f'<div style="{_card.format(bg=theme["surface"], border=theme["border"], accent=theme["moderate_color"], shadow=theme["shadow"])}">'
        f'<span style="font-size:1.4rem;flex-shrink:0;">🔄</span>'
        f'<div><div style="font-size:0.68rem;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:{theme["muted"]}">Model quality</div>'
        f'<div style="font-size:0.92rem;font-weight:700;color:{theme["text"]};margin-top:2px;">Improves with data</div></div></div>',
        unsafe_allow_html=True,
    )

st.markdown(
    """
<div class="footer-note" style="font-size:0.84rem;margin-top:1rem;line-height:1.8;">
<strong>How to read the results</strong><br>
<b>Reach (15–40%)</b> — Shown first. Outside or near the cutoff — aim high but pair with backups.<br>
<b>Moderate (40–75%)</b> — Possible but not guaranteed. Use as backups.<br>
<b>Safe (75%+)</b> — Very likely to get a seat. These are your strongest options.<br><br>
<strong>About the model</strong><br>
Closing ranks use the <strong>90th percentile</strong> of observed data (not the maximum) so a single outlier doesn't inflate the cutoff. Standard deviation of observed ranks is factored in — options with volatile historical cutoffs receive lower probabilities. Both the historical Excel dataset and live Google Form responses are merged and deduplicated before analysis.<br><br>
<strong style="color:#e11d48;">Disclaimer</strong>: <em>This tool is <u>unofficial</u> and not affiliated with VIT or any official counselling authority. All predictions are based on historical data and statistical models, and may not reflect actual results. The recommendations are for informational purposes only and are not perfect or guaranteed. Always verify with official VIT counselling resources before making any final decisions. Use at your own discretion.</em>
</div>
""",
    unsafe_allow_html=True,
)
