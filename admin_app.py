"""
admin_app.py — Admin Dashboard for VIT Counselling Predictor

Full CRUD operations for:
  • counselling_records (student data)
  • reports (feedback data)
  • Bulk imports/exports
  • Statistics & analytics
  • Data validation & integrity checks

Run with:
  streamlit run admin_app.py
"""

from datetime import datetime
from html import escape
import io
import pandas as pd
import plotly.express as px
import streamlit as st
from streamlit_option_menu import option_menu
import database as db
import load_data

# =====================================================
# PAGE CONFIG
# =====================================================

st.set_page_config(
    page_title="VIT Admin Dashboard",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# =====================================================
# ADMIN AUTHENTICATION
# =====================================================

def pie_chart_from_counts(counts: pd.Series, title: str) -> None:
    """Render a pie chart from a value_counts Series."""
    chart_df = counts.rename_axis("Category").reset_index(name="Count")
    fig = px.pie(chart_df, values="Count", names="Category", title=title)
    fig.update_traces(textposition="inside", textinfo="percent+label")
    fig.update_layout(margin=dict(l=10, r=10, t=50, b=10), height=360)
    st.plotly_chart(fig, use_container_width=True)


def _metric_card(label: str, value, sub: str = "", accent: str = "#2563eb") -> str:
    label_html = escape(str(label))
    value_html = escape(str(value))
    sub_html = escape(str(sub))
    accent_html = escape(str(accent), quote=True)
    return (
        f'<div class="admin-metric-card" style="--accent:{accent_html};">'
        f'<div class="admin-metric-label">{label_html}</div>'
        f'<div class="admin-metric-value">{value_html}</div>'
        f'<div class="admin-metric-sub">{sub_html}</div>'
        f"</div>"
    )


def render_metric_grid(cards: list[str]) -> None:
    st.markdown(
        f'<div class="admin-metric-grid">{"".join(cards)}</div>',
        unsafe_allow_html=True,
    )


def section_title(title: str, subtitle: str = "") -> None:
    st.markdown(
        f"""
        <div class="admin-section-title">
            <h2>{escape(title)}</h2>
            <p>{escape(subtitle)}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _empty_issue_frame() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "severity",
            "issue",
            "data_year",
            "campus",
            "branch",
            "fee",
            "rank",
            "details",
        ]
    )


def calculate_cutoff_order_issues(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return _empty_issue_frame()

    required = {"Rank", "Campus", "Branch", "Fee", "data_year"}
    if not required.issubset(records.columns):
        return _empty_issue_frame()

    rows = []
    clean = records.dropna(subset=["Rank", "Campus", "Branch", "Fee", "data_year"]).copy()
    if clean.empty:
        return _empty_issue_frame()

    clean["Rank"] = pd.to_numeric(clean["Rank"], errors="coerce")
    clean["Fee"] = pd.to_numeric(clean["Fee"], errors="coerce")
    clean["data_year"] = pd.to_numeric(clean["data_year"], errors="coerce")
    clean = clean.dropna(subset=["Rank", "Fee", "data_year"])

    grouped = (
        clean.groupby(["data_year", "Campus", "Branch", "Fee"])["Rank"]
        .agg(
            responses="count",
            closing_rank=lambda s: int(sorted(s.astype(int))[min(int(len(s) * 0.9), len(s) - 1)]),
        )
        .reset_index()
        .sort_values(["data_year", "Campus", "Branch", "Fee"])
    )

    for (year, campus, branch), group in grouped.groupby(["data_year", "Campus", "Branch"]):
        previous = []
        for _, current in group.sort_values("Fee").iterrows():
            for lower in previous:
                if int(lower["closing_rank"]) > int(current["closing_rank"]):
                    rows.append(
                        {
                            "severity": "High",
                            "issue": "Fee cutoff order conflict",
                            "data_year": int(year),
                            "campus": campus,
                            "branch": branch,
                            "fee": int(current["Fee"]),
                            "rank": "",
                            "details": (
                                f"Cat {int(current['Fee'])} cutoff {int(current['closing_rank']):,} "
                                f"is lower than Cat {int(lower['Fee'])} cutoff {int(lower['closing_rank']):,}."
                            ),
                        }
                    )
            previous.append(current)

    return pd.DataFrame(rows) if rows else _empty_issue_frame()


def build_data_quality_report(records: pd.DataFrame) -> pd.DataFrame:
    if records.empty:
        return _empty_issue_frame()

    df = records.copy()
    if "data_year" not in df.columns:
        df["data_year"] = db.DEFAULT_DATA_YEAR

    issues = []

    rank_num = pd.to_numeric(df.get("Rank"), errors="coerce")
    fee_num = pd.to_numeric(df.get("Fee"), errors="coerce")

    invalid_rank = df[rank_num.isna() | (rank_num < 1) | (rank_num > 250000)]
    for _, row in invalid_rank.iterrows():
        issues.append(
            {
                "severity": "High",
                "issue": "Invalid rank",
                "data_year": row.get("data_year", ""),
                "campus": row.get("Campus", ""),
                "branch": row.get("Branch", ""),
                "fee": row.get("Fee", ""),
                "rank": row.get("Rank", ""),
                "details": "Rank must be between 1 and 250,000.",
            }
        )

    invalid_fee = df[fee_num.isna() | ~fee_num.isin([1, 2, 3, 4, 5])]
    for _, row in invalid_fee.iterrows():
        issues.append(
            {
                "severity": "High",
                "issue": "Invalid fee category",
                "data_year": row.get("data_year", ""),
                "campus": row.get("Campus", ""),
                "branch": row.get("Branch", ""),
                "fee": row.get("Fee", ""),
                "rank": row.get("Rank", ""),
                "details": "Fee category must be 1, 2, 3, 4, or 5.",
            }
        )

    for col in ["Campus", "Branch", "source"]:
        if col in df.columns:
            missing = df[df[col].isna() | (df[col].astype(str).str.strip() == "")]
            for _, row in missing.iterrows():
                issues.append(
                    {
                        "severity": "Medium",
                        "issue": f"Missing {col}",
                        "data_year": row.get("data_year", ""),
                        "campus": row.get("Campus", ""),
                        "branch": row.get("Branch", ""),
                        "fee": row.get("Fee", ""),
                        "rank": row.get("Rank", ""),
                        "details": f"{col} is blank.",
                    }
                )

    key_cols = ["Rank", "Campus", "Branch", "Fee", "data_year"]
    if set(key_cols).issubset(df.columns):
        duplicate_rows = df[df.duplicated(subset=key_cols, keep=False)]
        for _, row in duplicate_rows.iterrows():
            issues.append(
                {
                    "severity": "Medium",
                    "issue": "Duplicate natural key",
                    "data_year": row.get("data_year", ""),
                    "campus": row.get("Campus", ""),
                    "branch": row.get("Branch", ""),
                    "fee": row.get("Fee", ""),
                    "rank": row.get("Rank", ""),
                    "details": "Same rank/campus/branch/fee/year appears more than once.",
                }
            )

    if set(["Campus", "Branch", "Fee", "data_year"]).issubset(df.columns):
        low_sample = (
            df.groupby(["data_year", "Campus", "Branch", "Fee"])
            .size()
            .reset_index(name="responses")
        )
        low_sample = low_sample[low_sample["responses"] < 3]
        for _, row in low_sample.iterrows():
            issues.append(
                {
                    "severity": "Low",
                    "issue": "Low sample size",
                    "data_year": int(row["data_year"]),
                    "campus": row["Campus"],
                    "branch": row["Branch"],
                    "fee": int(row["Fee"]),
                    "rank": "",
                    "details": f"Only {int(row['responses'])} response(s) for this option.",
                }
            )

    cutoff_issues = calculate_cutoff_order_issues(df)
    if not cutoff_issues.empty:
        issues.extend(cutoff_issues.to_dict("records"))

    return pd.DataFrame(issues) if issues else _empty_issue_frame()


def normalize_uploaded_records_for_audit(df: pd.DataFrame) -> pd.DataFrame:
    """Map import-template column names to the display names used by audits."""
    return df.rename(
        columns={
            "rank": "Rank",
            "campus": "Campus",
            "branch": "Branch",
            "fee": "Fee",
        }
    )

def check_admin_password():
    """Simple admin authentication."""
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    if not st.session_state.admin_authenticated:
        st.warning("⛔ Admin Access Required")
        password = st.text_input(
            "Enter admin password:",
            type="password",
            key="admin_password_input"
        )
        
        admin_password = st.secrets.get("admin_password", "admin123")
        
        if st.button("Login"):
            if password == admin_password:
                st.session_state.admin_authenticated = True
                st.success("✅ Authenticated!")
                st.rerun()
            else:
                st.error("❌ Incorrect password")
        st.stop()

# =====================================================
# SIDEBAR STYLING & NAVIGATION
# =====================================================

st.markdown("""
    <style>
        :root {
            --admin-bg: #eef2f7;
            --admin-surface: #ffffff;
            --admin-surface-2: #f8fafc;
            --admin-text: #0f172a;
            --admin-muted: #64748b;
            --admin-border: #dbe3ee;
            --admin-primary: #2563eb;
            --admin-primary-dark: #1d4ed8;
            --admin-success: #16a34a;
            --admin-warn: #d97706;
            --admin-risk: #dc2626;
            --admin-shadow: 0 12px 34px rgba(15,23,42,0.08);
        }
        @keyframes admin-rise {
            from { opacity: 0; transform: translateY(10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        @keyframes admin-sheen {
            from { transform: translateX(-130%) skewX(-18deg); opacity: 0; }
            30% { opacity: .65; }
            to { transform: translateX(230%) skewX(-18deg); opacity: 0; }
        }
        @keyframes admin-pulse {
            0%, 100% { box-shadow: 0 0 0 0 rgba(37,99,235,0); }
            50% { box-shadow: 0 0 0 5px rgba(37,99,235,0.14); }
        }
        .stApp {
            background:
                linear-gradient(90deg, rgba(148,163,184,0.11) 1px, transparent 1px),
                linear-gradient(180deg, rgba(148,163,184,0.09) 1px, transparent 1px),
                var(--admin-bg);
            background-size: 44px 44px;
            color: var(--admin-text);
        }
        [data-testid="stMainBlockContainer"] {
            max-width: 1520px;
            padding-top: 1.4rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: #0f172a;
            border-right: 1px solid rgba(255,255,255,0.08);
        }
        [data-testid="stSidebar"] * {
            color: #f9fafb;
        }
        [data-testid="stSidebar"] .stMetric {
            background: rgba(255,255,255,0.08);
            border: 1px solid rgba(255,255,255,0.12);
            border-radius: 8px;
            padding: 12px;
        }
        div[data-testid="stMetric"] {
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 12px;
            padding: 16px;
            box-shadow: var(--admin-shadow);
            animation: admin-rise .28s ease both;
        }
        div[data-testid="stMetric"] label {
            color: var(--admin-muted);
        }
        .admin-hero {
            position: relative;
            overflow: hidden;
            background:
                linear-gradient(135deg, rgba(37,99,235,0.34), transparent 42%),
                linear-gradient(135deg, #0f172a 0%, #172033 55%, #243449 100%);
            border-radius: 14px;
            padding: 28px;
            color: #ffffff;
            margin-bottom: 20px;
            border: 1px solid rgba(255,255,255,0.08);
            box-shadow: 0 18px 46px rgba(15,23,42,0.22);
            animation: admin-rise .35s ease both;
        }
        .admin-hero:after {
            content: "";
            position: absolute;
            top: 0;
            bottom: 0;
            width: 34%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.16), transparent);
            animation: admin-sheen 5.5s ease-in-out .8s infinite;
            pointer-events: none;
        }
        .admin-hero h1 {
            margin: 0;
            font-size: 34px;
            line-height: 1.1;
            letter-spacing: 0;
        }
        .admin-hero p {
            margin: 10px 0 0;
            color: #cbd5e1;
            font-size: 15px;
        }
        .admin-panel {
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 12px;
            padding: 18px;
            box-shadow: var(--admin-shadow);
            margin-bottom: 18px;
            animation: admin-rise .28s ease both;
        }
        .admin-panel h3 {
            margin: 0 0 8px;
            font-size: 18px;
            color: var(--admin-text);
        }
        .admin-muted {
            color: var(--admin-muted);
            font-size: 14px;
            margin: 0;
        }
        .admin-kicker {
            color: #94a3b8;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: .08em;
            text-transform: uppercase;
            margin-bottom: 8px;
        }
        .sidebar-title {
            background: linear-gradient(135deg, rgba(37,99,235,0.22), rgba(14,165,233,0.10));
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 12px;
            padding: 14px;
            font-size: 16px;
            font-weight: 800;
            color: #ffffff;
            margin-bottom: 16px;
        }
        .section-header {
            font-size: 16px;
            font-weight: bold;
            color: #e5e7eb;
            margin-top: 20px;
            margin-bottom: 10px;
        }
        .metric-card {
            background: var(--admin-surface);
            padding: 20px;
            border-radius: 12px;
            color: var(--admin-text);
            margin: 10px 0;
            border: 1px solid var(--admin-border);
        }
        .metric-value {
            font-size: 24px;
            font-weight: bold;
        }
        .metric-label {
            font-size: 12px;
            opacity: 0.9;
            margin-top: 5px;
        }
        .success-box {
            background-color: #f0fdf4;
            padding: 15px;
            border-left: 4px solid #16a34a;
            border-radius: 8px;
            margin: 10px 0;
        }
        .warning-box {
            background-color: #fefce8;
            padding: 15px;
            border-left: 4px solid #eab308;
            border-radius: 8px;
            margin: 10px 0;
        }
        .error-box {
            background-color: #fef2f2;
            padding: 15px;
            border-left: 4px solid #dc2626;
            border-radius: 8px;
            margin: 10px 0;
        }
        .stButton > button, .stDownloadButton > button {
            border-radius: 8px;
            font-weight: 700;
            min-height: 2.55rem;
            transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
        }
        .stButton > button:hover, .stDownloadButton > button:hover {
            transform: translateY(-1px);
            box-shadow: 0 10px 22px rgba(15,23,42,0.12);
        }
        button[kind="primary"]:hover {
            animation: admin-pulse 1.1s ease-in-out infinite;
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 12px;
            padding: 4px;
            box-shadow: var(--admin-shadow);
        }
        .stTabs [data-baseweb="tab"] {
            background: transparent;
            border: 1px solid transparent;
            border-radius: 8px;
            padding: 8px 14px;
            font-weight: 700;
        }
        .stTabs [aria-selected="true"] {
            background: var(--admin-surface-2) !important;
            color: var(--admin-primary) !important;
            border-color: var(--admin-border);
        }
        .admin-metric-grid {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 14px;
            margin: 0 0 20px;
        }
        .admin-metric-card {
            position: relative;
            overflow: hidden;
            background: var(--admin-surface);
            border: 1px solid var(--admin-border);
            border-radius: 12px;
            padding: 18px;
            box-shadow: var(--admin-shadow);
            animation: admin-rise .3s ease both;
            transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;
        }
        .admin-metric-card:before {
            content: "";
            position: absolute;
            inset: 0 0 auto;
            height: 3px;
            background: var(--accent, var(--admin-primary));
        }
        .admin-metric-card:hover {
            transform: translateY(-2px);
            border-color: color-mix(in srgb, var(--accent, var(--admin-primary)) 36%, var(--admin-border));
            box-shadow: 0 16px 38px rgba(15,23,42,0.13);
        }
        .admin-metric-label {
            color: var(--admin-muted);
            text-transform: uppercase;
            font-size: 12px;
            font-weight: 800;
            letter-spacing: 0;
        }
        .admin-metric-value {
            color: var(--admin-text);
            font-size: 30px;
            font-weight: 850;
            line-height: 1;
            margin: 9px 0 5px;
            letter-spacing: 0;
            font-variant-numeric: tabular-nums;
        }
        .admin-metric-sub {
            color: var(--admin-muted);
            font-size: 13px;
            min-height: 18px;
        }
        .admin-section-title {
            margin: 8px 0 16px;
        }
        .admin-section-title h2 {
            margin: 0;
            color: var(--admin-text);
            font-size: 24px;
            letter-spacing: 0;
        }
        .admin-section-title p {
            margin: 5px 0 0;
            color: var(--admin-muted);
            font-size: 14px;
        }
        .issue-high, .issue-medium, .issue-low {
            display: inline-flex;
            align-items: center;
            border-radius: 999px;
            padding: 2px 9px;
            font-size: 12px;
            font-weight: 800;
        }
        .issue-high { background: #fee2e2; color: #991b1b; }
        .issue-medium { background: #fef3c7; color: #92400e; }
        .issue-low { background: #dbeafe; color: #1e40af; }
        [data-testid="stDataFrame"] {
            border-radius: 12px;
            overflow: hidden;
            box-shadow: var(--admin-shadow);
        }
        [data-testid="stAlert"] {
            border-radius: 12px;
        }
        @media (max-width: 900px) {
            .admin-metric-grid {
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }
        }
        @media (max-width: 560px) {
            .admin-metric-grid {
                grid-template-columns: 1fr;
            }
            .admin-hero h1 {
                font-size: 26px;
            }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *:before, *:after {
                animation-duration: .01ms !important;
                transition-duration: .01ms !important;
            }
            .admin-hero:after {
                display: none;
            }
        }
    </style>
""", unsafe_allow_html=True)


def admin_hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="admin-hero">
            <div class="admin-kicker">Admin Console</div>
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def admin_panel(title: str, body: str) -> None:
    st.markdown(
        f"""
        <div class="admin-panel">
            <h3>{title}</h3>
            <p class="admin-muted">{body}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def data_year_options() -> list[int]:
    years = set(db.get_available_data_years())
    configured_data_years = getattr(load_data, "configured_data_years", None)
    if callable(configured_data_years):
        years.update(configured_data_years())
    else:
        years.add(getattr(load_data, "ACTIVE_DATA_YEAR", db.DEFAULT_DATA_YEAR))
        years.add(db.DEFAULT_DATA_YEAR)
    return sorted(years)


def selected_admin_year(key: str = "admin_data_year") -> int:
    options = data_year_options()
    default_index = options.index(db.DEFAULT_DATA_YEAR) if db.DEFAULT_DATA_YEAR in options else 0
    return int(
        st.selectbox(
            "Data Year",
            options,
            index=default_index,
            key=key,
            help="2025 is the current dataset. Keep 2026 separate when you add it later.",
        )
    )

# =====================================================
# MAIN APP
# =====================================================

if __name__ == "__main__":
    check_admin_password()

    # Sidebar header
    with st.sidebar:
        st.markdown('<div class="sidebar-title">🛡️ ADMIN DASHBOARD</div>', 
                    unsafe_allow_html=True)
        
        # Quick stats
        st.markdown('<div class="section-header">📊 Quick Stats</div>', 
                    unsafe_allow_html=True)
        
        try:
            record_count = db.count_records()
            report_count = len(db.fetch_all_reports()) if db.fetch_all_reports() is not None else 0
            sources = db.get_source_counts()
            years = db.get_available_data_years()
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("📚 Records", record_count)
            with col2:
                st.metric("📋 Reports", report_count)
            
            if sources:
                st.caption(f"Sources: Historical={sources.get('historical', 0)}, Form={sources.get('form', 0)}")
            st.caption(f"Years: {', '.join(str(year) for year in years)}")
        except Exception as e:
            st.error(f"Error loading stats: {str(e)}")

        st.divider()
        
        # Navigation menu
        selected_menu = option_menu(
            "Navigation",
            ["Dashboard", "Records", "Reports", "Data Quality", "Bulk Import", "Bulk Export", "Analytics", "Data Refresh", "Settings"],
            icons=["speedometer2", "table", "chat-left-text", "shield-check", "upload", "download", "bar-chart", "arrow-clockwise", "gear"],
            menu_icon="menu-button-wide",
            default_index=0,
        )

    # ════════════════════════════════════════════════════════════════════
    # DASHBOARD TAB
    # ════════════════════════════════════════════════════════════════════
    
    if selected_menu == "Dashboard":
        admin_hero(
            "VIT Admin Dashboard",
            "Monitor counselling records, user reports, imports, exports, and refresh jobs from one place.",
        )

        if st.session_state.get("last_form_refresh_result"):
            result = st.session_state.pop("last_form_refresh_result")
            st.success(
                f"Form data refreshed: {result['form_responses']} rows loaded "
                f"(previously {result['previous_form_records']})."
            )
        
        try:
            record_count = db.count_records()
            reports_df = db.fetch_all_reports()
            report_count = len(reports_df) if reports_df is not None else 0
            all_records = db.fetch_all_records()
            active_records = (
                all_records[all_records["data_year"] == load_data.ACTIVE_DATA_YEAR]
                if "data_year" in all_records.columns
                else all_records
            )
            sources = db.get_source_counts()
            quality = build_data_quality_report(all_records)
            high_issues = len(quality[quality["severity"] == "High"]) if not quality.empty else 0

            render_metric_grid(
                [
                    _metric_card("Total records", f"{record_count:,}", "all counselling rows", "#2563eb"),
                    _metric_card("User reports", f"{report_count:,}", "prediction feedback", "#7c3aed"),
                    _metric_card(
                        f"{load_data.ACTIVE_DATA_YEAR} unique ranks",
                        f"{len(active_records['Rank'].unique()):,}" if not active_records.empty else "0",
                        "active year coverage",
                        "#16a34a",
                    ),
                    _metric_card(
                        "Data issues",
                        f"{len(quality):,}",
                        f"{high_issues:,} high severity",
                        "#dc2626" if high_issues else "#16a34a",
                    ),
                ]
            )
        
        except Exception as e:
            st.error(f"Error loading dashboard metrics: {str(e)}")
        
        st.divider()

        admin_panel(
            "Quick Admin Actions",
            "Use the form-only refresh when new Google Form responses should appear without resetting historical data or reports.",
        )

        action_col1, action_col2, action_col3 = st.columns([1, 1, 2])
        with action_col1:
            dashboard_refresh_year = selected_admin_year("dashboard_refresh_year")
            if st.button("Refresh Form Data", type="primary", use_container_width=True, key="dashboard_form_refresh"):
                st.session_state.confirm_form_refresh = True
        with action_col2:
            if st.button("Clear Streamlit Cache", use_container_width=True, key="dashboard_clear_cache"):
                st.cache_resource.clear()
                st.success("Cache cleared. Refresh the page if old data is still visible.")
        with action_col3:
            st.info("Form refresh replaces only rows where source = 'form' for the selected year. Historical rows and reports stay intact.")

        if st.session_state.get("confirm_form_refresh"):
            st.warning("Refresh only Google Form data? Existing form-sourced rows will be replaced with the latest valid sheet rows.")
            confirm_col, cancel_col = st.columns(2)
            with confirm_col:
                if st.button("Yes, Refresh Form Rows", type="primary", use_container_width=True, key="dashboard_confirm_form_refresh"):
                    with st.spinner("Refreshing Google Form data..."):
                        result = load_data.refresh_form_responses_only(dashboard_refresh_year)
                    if result["success"]:
                        st.session_state.last_form_refresh_result = result
                        st.session_state.confirm_form_refresh = False
                        st.cache_resource.clear()
                        st.rerun()
                    else:
                        st.error(f"Form refresh failed: {result['error']}")
            with cancel_col:
                if st.button("Cancel", use_container_width=True, key="dashboard_cancel_form_refresh"):
                    st.session_state.confirm_form_refresh = False
                    st.rerun()
        
        # Recent records
        st.subheader("📊 Recent Records")
        try:
            all_records = db.fetch_all_records()
            if not all_records.empty:
                st.dataframe(all_records.tail(10), use_container_width=True, hide_index=True)
            else:
                st.info("No records found")
        except Exception as e:
            st.error(f"Error loading records: {str(e)}")
        
        # Recent reports
        st.subheader("📋 Recent Reports")
        try:
            reports = db.fetch_all_reports()
            if reports is not None and not reports.empty:
                st.dataframe(reports.tail(10), use_container_width=True, hide_index=True)
            else:
                st.info("No reports found")
        except Exception as e:
            st.error(f"Error loading reports: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # RECORDS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Records":
        st.title("📚 Manage Counselling Records")
        
        record_tabs = st.tabs(["View & Filter", "Add New Record", "Edit Record", "Delete Record"])
        
        with record_tabs[0]:  # VIEW & FILTER
            st.subheader("View & Filter Records")
            
            try:
                all_records = db.fetch_all_records()
                
                if not all_records.empty:
                    col1, col2, col3, col4, col5 = st.columns(5)
                    
                    with col1:
                        rank_filter = st.text_input("Filter by Rank (optional)")
                    with col2:
                        campus_filter = st.selectbox(
                            "Filter by Campus",
                            ["All"] + sorted(all_records['Campus'].unique().tolist()),
                            key="campus_view"
                        )
                    with col3:
                        branch_filter = st.selectbox(
                            "Filter by Branch",
                            ["All"] + sorted(all_records['Branch'].unique().tolist()),
                            key="branch_view"
                        )
                    with col4:
                        source_filter = st.selectbox(
                            "Filter by Source",
                            ["All"] + sorted(all_records['source'].unique().tolist()),
                            key="source_view"
                        )
                    with col5:
                        year_filter = st.selectbox(
                            "Filter by Year",
                            ["All"] + sorted(all_records["data_year"].dropna().astype(int).unique().tolist()),
                            key="year_view",
                        )
                    
                    # Apply filters
                    filtered = all_records.copy()
                    
                    if rank_filter:
                        filtered = filtered[filtered['Rank'].astype(str).str.contains(rank_filter, case=False, na=False)]
                    
                    if campus_filter != "All":
                        filtered = filtered[filtered['Campus'] == campus_filter]
                    
                    if branch_filter != "All":
                        filtered = filtered[filtered['Branch'] == branch_filter]
                    
                    if source_filter != "All":
                        filtered = filtered[filtered['source'] == source_filter]

                    if year_filter != "All":
                        filtered = filtered[filtered["data_year"] == int(year_filter)]
                    
                    st.success(f"✅ Showing {len(filtered)} records")
                    st.dataframe(filtered, use_container_width=True, hide_index=True)
                    
                else:
                    st.warning("No records found in database")
            
            except Exception as e:
                st.error(f"Error loading records: {str(e)}")
        
        with record_tabs[1]:  # ADD NEW
            st.subheader("➕ Add New Record")
            
            col1, col2 = st.columns(2)
            
            with col1:
                rank = st.number_input("Rank", min_value=1, step=1)
                campus = st.selectbox(
                    "Campus",
                    ["VIT Chennai", "VIT Vellore", "VIT Pune", "VIT Amravati"],
                    key="campus_add"
                )
            
            with col2:
                branch = st.text_input("Branch (e.g., CSE Core)")
                fee = st.selectbox(
                    "Fee Category",
                    [1, 2, 3, 4, 5],
                    key="fee_add"
                )
            
            source = st.selectbox("Source", ["historical", "form"], key="source_add")
            data_year = st.selectbox("Data Year", data_year_options(), index=data_year_options().index(db.DEFAULT_DATA_YEAR), key="year_add")
            
            if st.button("➕ Add Record", type="primary", use_container_width=True):
                try:
                    success = db.upsert_records([{
                        "rank": int(rank),
                        "campus": campus,
                        "branch": branch,
                        "fee": int(fee),
                        "source": source,
                        "data_year": int(data_year),
                    }])
                    
                    if success:
                        st.success(f"✅ Record added: Rank {rank} - {campus} - {branch}")
                    else:
                        st.error("❌ Failed to add record")
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with record_tabs[2]:  # EDIT RECORD
            st.subheader("✏️ Edit Record")
            
            try:
                all_records = db.fetch_all_records()
                
                if not all_records.empty:
                    edit_year = st.selectbox(
                        "Edit Year",
                        sorted(all_records["data_year"].dropna().astype(int).unique().tolist()),
                        key="edit_year",
                    )
                    editable_records = all_records[all_records["data_year"] == int(edit_year)].reset_index(drop=True)
                    selected_idx = st.selectbox(
                        "Select Record",
                        range(len(editable_records)),
                        format_func=lambda i: (
                            f"{editable_records.iloc[i]['Rank']} | "
                            f"{editable_records.iloc[i]['Campus']} | "
                            f"{editable_records.iloc[i]['Branch']} | "
                            f"Fee {editable_records.iloc[i]['Fee']}"
                        ),
                        key="edit_record_idx",
                    )
                    
                    record = editable_records.iloc[selected_idx]
                    
                    st.write("**Current Record:**")
                    st.json({
                        "Rank": int(record['Rank']),
                        "Campus": record['Campus'],
                        "Branch": record['Branch'],
                        "Fee": int(record['Fee']),
                        "Source": record['source'],
                        "Data Year": int(record["data_year"]),
                    })
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        campus_options = sorted(set(all_records["Campus"].dropna().tolist()) | {"Vellore", "Chennai", "Bhopal", "Amaravati"})
                        new_campus = st.selectbox(
                            "Update Campus",
                            campus_options,
                            index=campus_options.index(record["Campus"]) if record["Campus"] in campus_options else 0,
                            key="edit_campus"
                        )
                        new_branch = st.text_input("Update Branch", value=record['Branch'])
                    
                    with col2:
                        new_fee = st.selectbox(
                            "Update Fee",
                            [1, 2, 3, 4, 5],
                            index=[1, 2, 3, 4, 5].index(int(record['Fee'])),
                            key="edit_fee"
                        )
                        new_source = st.selectbox(
                            "Update Source",
                            ["historical", "form"],
                            index=["historical", "form"].index(record['source']),
                            key="edit_source"
                        )
                        new_data_year = st.selectbox(
                            "Update Data Year",
                            data_year_options(),
                            index=data_year_options().index(int(record["data_year"])) if int(record["data_year"]) in data_year_options() else 0,
                            key="edit_data_year",
                        )
                    
                    if st.button("✅ Update Record", type="primary", use_container_width=True):
                        try:
                            success = db.upsert_records([{
                                "rank": int(record["Rank"]),
                                "campus": new_campus,
                                "branch": new_branch,
                                "fee": int(new_fee),
                                "source": new_source,
                                "data_year": int(new_data_year),
                            }])
                            
                            if success:
                                st.success("✅ Record updated successfully!")
                            else:
                                st.error("❌ Failed to update record")
                        except Exception as e:
                            st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("No records found")
            
            except Exception as e:
                st.error(f"Error loading records: {str(e)}")
        
        with record_tabs[3]:  # DELETE RECORD
            st.subheader("🗑️ Delete Record")
            st.warning("⚠️ This action cannot be undone!")
            
            try:
                all_records = db.fetch_all_records()
                
                if not all_records.empty:
                    delete_year = st.selectbox(
                        "Delete Year",
                        sorted(all_records["data_year"].dropna().astype(int).unique().tolist()),
                        key="delete_year",
                    )
                    delete_records = all_records[all_records["data_year"] == int(delete_year)].reset_index(drop=True)
                    selected_idx = st.selectbox(
                        "Select Record to Delete",
                        range(len(delete_records)),
                        format_func=lambda i: (
                            f"{delete_records.iloc[i]['Rank']} | "
                            f"{delete_records.iloc[i]['Campus']} | "
                            f"{delete_records.iloc[i]['Branch']} | "
                            f"Fee {delete_records.iloc[i]['Fee']} | "
                            f"{delete_records.iloc[i].get('source', 'unknown')}"
                        ),
                        key="delete_record_idx",
                    )
                    
                    record = delete_records.iloc[selected_idx]
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.json({
                            "Rank": int(record['Rank']),
                            "Campus": record['Campus'],
                            "Branch": record['Branch'],
                            "Fee": int(record['Fee']),
                            "Source": record.get("source", ""),
                            "Data Year": int(record.get("data_year", db.DEFAULT_DATA_YEAR)),
                        })
                    
                    with col2:
                        confirm_text = st.text_input(
                            "Type DELETE to confirm",
                            key="delete_record_confirm_text",
                        )
                        if st.button("🗑️ DELETE THIS RECORD", type="secondary", use_container_width=True):
                            try:
                                if confirm_text.strip().upper() != "DELETE":
                                    st.warning("Type DELETE before removing this record.")
                                else:
                                    success = db.delete_record(
                                        rank=int(record["Rank"]),
                                        campus=str(record["Campus"]),
                                        branch=str(record["Branch"]),
                                        fee=int(record["Fee"]),
                                        data_year=int(record.get("data_year", db.DEFAULT_DATA_YEAR)),
                                    )
                                    if success:
                                        st.success("✅ Record deleted successfully.")
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete record.")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                else:
                    st.warning("No records found")
            
            except Exception as e:
                st.error(f"Error loading records: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # REPORTS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Reports":
        st.title("📋 Manage User Reports")
        
        report_tabs = st.tabs(["View Reports", "Report Analytics", "Delete Report"])
        
        with report_tabs[0]:  # VIEW REPORTS
            st.subheader("View All Reports")
            
            try:
                reports = db.fetch_all_reports()
                
                if reports is not None and not reports.empty:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        report_type_filter = st.selectbox(
                            "Filter by Report Type",
                            ["All"] + (reports['Report Type'].unique().tolist() if 'Report Type' in reports.columns else [])
                        )
                    
                    with col2:
                        chance_filter = st.selectbox(
                            "Filter by Predicted Chance",
                            ["All"] + (reports['Predicted Chance'].unique().tolist() if 'Predicted Chance' in reports.columns else [])
                        )
                    
                    with col3:
                        campus_filter = st.selectbox(
                            "Filter by Campus",
                            ["All"] + (reports['Campus'].unique().tolist() if 'Campus' in reports.columns else []),
                            key="reports_campus"
                        )
                    
                    filtered_reports = reports.copy()
                    
                    if report_type_filter != "All" and 'Report Type' in reports.columns:
                        filtered_reports = filtered_reports[filtered_reports['Report Type'] == report_type_filter]
                    
                    if chance_filter != "All" and 'Predicted Chance' in reports.columns:
                        filtered_reports = filtered_reports[filtered_reports['Predicted Chance'] == chance_filter]
                    
                    if campus_filter != "All" and 'Campus' in reports.columns:
                        filtered_reports = filtered_reports[filtered_reports['Campus'] == campus_filter]
                    
                    st.success(f"✅ Showing {len(filtered_reports)} reports")
                    st.dataframe(filtered_reports, use_container_width=True, hide_index=True)
                
                else:
                    st.info("No reports found")
            
            except Exception as e:
                st.error(f"Error loading reports: {str(e)}")
        
        with report_tabs[1]:  # ANALYTICS
            st.subheader("📊 Report Analytics")
            
            try:
                reports = db.fetch_all_reports()
                
                if reports is not None and not reports.empty:
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        if 'Report Type' in reports.columns:
                            st.metric("📌 Report Types", reports['Report Type'].nunique())
                    
                    with col2:
                        st.metric("📋 Total Reports", len(reports))
                    
                    with col3:
                        if 'Timestamp' in reports.columns or 'created_at' in reports.columns:
                            st.metric("📅 Date Range", "See below")
                    
                    st.divider()
                    
                    # Report type distribution
                    if 'Report Type' in reports.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Reports by Type")
                            report_type_counts = reports['Report Type'].value_counts()
                            st.bar_chart(report_type_counts)
                        
                        with col2:
                            st.subheader("Distribution")
                            st.dataframe(report_type_counts, use_container_width=True)
                    
                    # Chance distribution
                    if 'Predicted Chance' in reports.columns:
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.subheader("Reports by Predicted Chance")
                            chance_counts = reports['Predicted Chance'].value_counts()
                            pie_chart_from_counts(chance_counts, "Reports by Predicted Chance")
                        
                        with col2:
                            st.subheader("Distribution")
                            st.dataframe(chance_counts, use_container_width=True)
                    
                    # Campus wise reports
                    if 'Campus' in reports.columns:
                        st.subheader("Reports by Campus")
                        campus_counts = reports['Campus'].value_counts()
                        st.bar_chart(campus_counts)
                
                else:
                    st.info("No reports to analyze")
            
            except Exception as e:
                st.error(f"Error loading analytics: {str(e)}")
        
        with report_tabs[2]:  # DELETE REPORT
            st.subheader("🗑️ Delete Report")
            st.warning("⚠️ This action cannot be undone!")
            
            try:
                reports = db.fetch_all_reports()
                
                if reports is not None and not reports.empty:
                    # Create a display string for selection
                    report_options = []
                    report_ids = []
                    
                    for idx, row in reports.iterrows():
                        label = f"ID: {row.get('id', 'N/A')} | Rank: {row.get('User Rank', 'N/A')} | Type: {row.get('Report Type', 'N/A')}"
                        report_options.append(label)
                        report_ids.append(row.get('id'))
                    
                    selected_idx = st.selectbox(
                        "Select Report to Delete",
                        range(len(report_options)),
                        format_func=lambda i: report_options[i]
                    )
                    
                    selected_report_id = report_ids[selected_idx]
                    selected_report = reports.iloc[selected_idx]
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.json(selected_report.to_dict())
                    
                    with col2:
                        if st.button("🗑️ DELETE THIS REPORT", type="secondary", use_container_width=True):
                            try:
                                success = db.delete_report(selected_report_id)
                                
                                if success:
                                    st.success(f"✅ Report {selected_report_id} deleted successfully!")
                                    st.rerun()
                                else:
                                    st.error(f"❌ Failed to delete report")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                else:
                    st.warning("No reports found")
            
            except Exception as e:
                st.error(f"Error loading reports: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # DATA QUALITY TAB
    # ════════════════════════════════════════════════════════════════════

    elif selected_menu == "Data Quality":
        admin_hero(
            "Data Quality Center",
            "Audit records for invalid values, duplicate keys, thin samples, and fee-category cutoff order conflicts.",
        )

        try:
            all_records = db.fetch_all_records()
            if all_records.empty:
                st.warning("No records available to audit.")
            else:
                year_options = ["All"] + sorted(
                    all_records["data_year"].dropna().astype(int).unique().tolist()
                    if "data_year" in all_records.columns
                    else [db.DEFAULT_DATA_YEAR]
                )
                filter_col1, filter_col2, filter_col3 = st.columns(3)
                with filter_col1:
                    audit_year = st.selectbox("Audit year", year_options, key="quality_year")
                with filter_col2:
                    audit_campus = st.selectbox(
                        "Campus",
                        ["All"] + sorted(all_records["Campus"].dropna().unique().tolist()),
                        key="quality_campus",
                    )
                with filter_col3:
                    audit_severity = st.selectbox(
                        "Severity",
                        ["All", "High", "Medium", "Low"],
                        key="quality_severity",
                    )

                scoped_records = all_records.copy()
                if audit_year != "All" and "data_year" in scoped_records.columns:
                    scoped_records = scoped_records[scoped_records["data_year"] == int(audit_year)]
                if audit_campus != "All":
                    scoped_records = scoped_records[scoped_records["Campus"] == audit_campus]

                issues = build_data_quality_report(scoped_records)
                if audit_severity != "All" and not issues.empty:
                    issues = issues[issues["severity"] == audit_severity]

                high_count = len(issues[issues["severity"] == "High"]) if not issues.empty else 0
                medium_count = len(issues[issues["severity"] == "Medium"]) if not issues.empty else 0
                low_count = len(issues[issues["severity"] == "Low"]) if not issues.empty else 0
                conflict_count = (
                    len(issues[issues["issue"] == "Fee cutoff order conflict"])
                    if not issues.empty
                    else 0
                )

                render_metric_grid(
                    [
                        _metric_card("High severity", f"{high_count:,}", "fix first", "#dc2626"),
                        _metric_card("Medium severity", f"{medium_count:,}", "review soon", "#d97706"),
                        _metric_card("Low severity", f"{low_count:,}", "data confidence", "#2563eb"),
                        _metric_card("Cutoff conflicts", f"{conflict_count:,}", "fee order issues", "#7c3aed"),
                    ]
                )

                if issues.empty:
                    st.success("✅ No data quality issues found for the selected scope.")
                else:
                    issue_tabs = st.tabs(["Issues", "Summary", "Export"])

                    with issue_tabs[0]:
                        st.dataframe(
                            issues.sort_values(["severity", "issue", "data_year"]),
                            use_container_width=True,
                            hide_index=True,
                        )

                    with issue_tabs[1]:
                        col_a, col_b = st.columns(2)
                        with col_a:
                            st.subheader("Issues by type")
                            type_counts = issues["issue"].value_counts()
                            st.bar_chart(type_counts)
                            st.dataframe(type_counts.reset_index(name="count"), use_container_width=True, hide_index=True)
                        with col_b:
                            st.subheader("Issues by branch")
                            branch_counts = (
                                issues[issues["branch"].astype(str).str.len() > 0]["branch"]
                                .value_counts()
                                .head(15)
                            )
                            if not branch_counts.empty:
                                st.bar_chart(branch_counts)
                                st.dataframe(branch_counts.reset_index(name="count"), use_container_width=True, hide_index=True)
                            else:
                                st.info("No branch-specific issues in this scope.")

                    with issue_tabs[2]:
                        st.download_button(
                            "Download issue report CSV",
                            data=issues.to_csv(index=False),
                            file_name=f"data_quality_issues_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            type="primary",
                            use_container_width=True,
                        )
                        st.info("Use this report to fix records in Supabase or through the Records tab.")

        except Exception as e:
            st.error(f"Error running data quality audit: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # BULK IMPORT TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Bulk Import":
        st.title("📥 Bulk Import Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Import Records")
            st.info("""
            Upload a CSV file with columns:
            - `rank` (integer)
            - `campus` (text)
            - `branch` (text)
            - `fee` (integer: 1-5)
            - `source` (text: 'historical' or 'form')
            - `data_year` (optional, defaults to the current active year)
            """)
            
            records_file = st.file_uploader(
                "Choose CSV file for records",
                type="csv",
                key="records_import"
            )
            
            if records_file:
                try:
                    df = pd.read_csv(records_file)
                    st.dataframe(df.head(10), use_container_width=True)
                    audit_df = normalize_uploaded_records_for_audit(df.copy())
                    if "data_year" not in audit_df.columns:
                        audit_df["data_year"] = load_data.ACTIVE_DATA_YEAR
                    import_issues = build_data_quality_report(audit_df)
                    
                    col_a, col_b, col_c = st.columns(3)
                    with col_a:
                        st.success(f"✅ {len(df)} rows ready to import")
                    with col_b:
                        if import_issues.empty:
                            st.success("✅ No obvious quality issues")
                        else:
                            st.warning(f"⚠️ {len(import_issues)} issue(s) found")
                    
                    with col_c:
                        if st.button("📥 Import Records", type="primary", use_container_width=True, key="import_records_btn"):
                            try:
                                if "data_year" not in df.columns:
                                    df["data_year"] = load_data.ACTIVE_DATA_YEAR
                                records = df.to_dict('records')
                                success = db.upsert_records(records)
                                
                                if success:
                                    st.success(f"✅ Successfully imported {len(records)} records!")
                                else:
                                    st.error("❌ Failed to import records")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")

                    if not import_issues.empty:
                        with st.expander("Review import issues before importing"):
                            st.dataframe(import_issues, use_container_width=True, hide_index=True)
                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        with col2:
            st.subheader("📋 Import Reports")
            st.info("""
            Upload a CSV/Excel file with columns:
            - `user_rank` (integer)
            - `campus` (text)
            - `branch` (text)
            - `fee_category` (integer)
            - `predicted_probability` (float)
            - `predicted_chance` (text)
            - `report_type` (text)
            - `reason_text` (text, optional)
            """)
            
            reports_file = st.file_uploader(
                "Choose CSV/Excel file for reports",
                type=["csv", "xlsx"],
                key="reports_import"
            )
            
            if reports_file:
                try:
                    if reports_file.name.endswith('.xlsx'):
                        df = pd.read_excel(reports_file)
                    else:
                        df = pd.read_csv(reports_file)
                    
                    st.dataframe(df.head(10), use_container_width=True)
                    
                    col_a, col_b = st.columns(2)
                    with col_a:
                        st.success(f"✅ {len(df)} rows ready to import")
                    
                    with col_b:
                        if st.button("📥 Import Reports", type="primary", use_container_width=True, key="import_reports_btn"):
                            try:
                                imported = 0
                                for _, row in df.iterrows():
                                    success = db.insert_report(
                                        user_rank=int(row['user_rank']),
                                        campus=str(row['campus']),
                                        branch=str(row['branch']),
                                        fee=int(row['fee_category']),
                                        probability=float(row['predicted_probability']),
                                        chance=str(row['predicted_chance']),
                                        report_type=str(row['report_type']),
                                        reason_text=str(row.get('reason_text', ''))
                                    )
                                    if success:
                                        imported += 1
                                
                                st.success(f"✅ Successfully imported {imported}/{len(df)} reports!")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # BULK EXPORT TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Bulk Export":
        st.title("📤 Bulk Export Data")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Records")
            
            if st.button("📤 Download Records as CSV", type="primary", use_container_width=True):
                try:
                    records = db.fetch_all_records()
                    
                    if not records.empty:
                        csv_data = records.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Click to Download Records.csv",
                            data=csv_data,
                            file_name=f"counselling_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(records)} records ready for download")
                    else:
                        st.warning("No records to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.button("📊 Download Records as Excel", type="primary", use_container_width=True):
                try:
                    records = db.fetch_all_records()
                    
                    if not records.empty:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            records.to_excel(writer, sheet_name='Records', index=False)
                        
                        buffer.seek(0)
                        st.download_button(
                            label="📥 Click to Download Records.xlsx",
                            data=buffer.getvalue(),
                            file_name=f"counselling_records_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(records)} records ready for download")
                    else:
                        st.warning("No records to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
        
        with col2:
            st.subheader("📋 Export Reports")
            
            if st.button("📤 Download Reports as CSV", type="primary", use_container_width=True):
                try:
                    reports = db.fetch_all_reports()
                    
                    if reports is not None and not reports.empty:
                        csv_data = reports.to_csv(index=False)
                        
                        st.download_button(
                            label="📥 Click to Download Reports.csv",
                            data=csv_data,
                            file_name=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(reports)} reports ready for download")
                    else:
                        st.warning("No reports to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
            
            if st.button("📊 Download Reports as Excel", type="primary", use_container_width=True):
                try:
                    reports = db.fetch_all_reports()
                    
                    if reports is not None and not reports.empty:
                        buffer = io.BytesIO()
                        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                            reports.to_excel(writer, sheet_name='Reports', index=False)
                        
                        buffer.seek(0)
                        st.download_button(
                            label="📥 Click to Download Reports.xlsx",
                            data=buffer.getvalue(),
                            file_name=f"reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True
                        )
                        st.success(f"✅ {len(reports)} reports ready for download")
                    else:
                        st.warning("No reports to export")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # ANALYTICS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Analytics":
        st.title("📊 Analytics Dashboard")
        
        try:
            all_records = db.fetch_all_records()
            
            if not all_records.empty:
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("📚 Total Records", len(all_records))
                
                with col2:
                    st.metric("🏛️ Campuses", all_records['Campus'].nunique())
                
                with col3:
                    st.metric("🎓 Branches", all_records['Branch'].nunique())
                
                with col4:
                    st.metric("💰 Fee Categories", all_records['Fee'].nunique())
                
                st.divider()
                
                # Records by Campus
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Records by Campus")
                    campus_counts = all_records['Campus'].value_counts()
                    st.bar_chart(campus_counts)
                
                with col2:
                    st.subheader("Records by Branch")
                    branch_counts = all_records['Branch'].value_counts().head(10)
                    st.bar_chart(branch_counts)
                
                st.divider()
                
                # Record ranks distribution
                st.subheader("Rank Distribution")
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Min Rank", int(all_records['Rank'].min()))
                    st.metric("Max Rank", int(all_records['Rank'].max()))
                
                with col2:
                    st.metric("Avg Rank", int(all_records['Rank'].mean()))
                    st.metric("Median Rank", int(all_records['Rank'].median()))
                
                st.divider()
                
                # Source distribution
                col1, col2 = st.columns(2)
                
                with col1:
                    st.subheader("Records by Source")
                    source_counts = all_records['source'].value_counts()
                    pie_chart_from_counts(source_counts, "Records by Source")
                
                with col2:
                    st.subheader("Distribution Table")
                    st.dataframe(source_counts, use_container_width=True)
                
            else:
                st.warning("No records to analyze")
        
        except Exception as e:
            st.error(f"Error loading analytics: {str(e)}")

    # ════════════════════════════════════════════════════════════════════
    # DATA REFRESH TAB
    # ════════════════════════════════════════════════════════════════════

    elif selected_menu == "Data Refresh":
        admin_hero(
            "Data Refresh",
            "Refresh live form rows independently, or run a full source rebuild when you need a complete reset.",
        )

        if st.session_state.get("last_form_refresh_result"):
            result = st.session_state.pop("last_form_refresh_result")
            st.success(
                f"Form data refreshed: {result['form_responses']} rows loaded "
                f"(previously {result['previous_form_records']})."
            )

        if st.session_state.get("last_full_refresh_result"):
            result = st.session_state.pop("last_full_refresh_result")
            st.success(
                f"Full refresh complete: {result['records_loaded']} historical rows, "
                f"{result['form_responses']} form rows, {result['total']} total."
            )

        try:
            sources = db.get_source_counts()
            reports_df = db.fetch_all_reports()
            report_count = len(reports_df) if reports_df is not None else 0
            refresh_year = selected_admin_year("refresh_page_year")
            year_sources = db.get_source_counts(refresh_year)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(f"{refresh_year} Historical Rows", year_sources.get("historical", 0))
            with col2:
                st.metric(f"{refresh_year} Form Rows", year_sources.get("form", 0))
            with col3:
                st.metric("All Reports", report_count)
        except Exception as e:
            st.error(f"Error loading refresh stats: {str(e)}")
            refresh_year = db.DEFAULT_DATA_YEAR

        st.divider()

        form_col, full_col = st.columns(2)

        with form_col:
            admin_panel(
                "Refresh Form Data Only",
                "Replaces rows imported from Google Forms for the selected year while preserving historical Excel records and user reports.",
            )
            if st.button("Refresh Form Data Only", type="primary", use_container_width=True, key="refresh_form_only"):
                st.session_state.confirm_form_refresh = True

            if st.session_state.get("confirm_form_refresh"):
                st.warning("This will delete existing source='form' rows and reload the latest valid Google Sheet responses.")
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("Confirm Form Refresh", type="primary", use_container_width=True, key="confirm_refresh_form_only"):
                        with st.spinner("Refreshing Google Form rows..."):
                            result = load_data.refresh_form_responses_only(refresh_year)
                        if result["success"]:
                            st.session_state.last_form_refresh_result = result
                            st.session_state.confirm_form_refresh = False
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.error(f"Form refresh failed: {result['error']}")
                with cancel_col:
                    if st.button("Cancel", use_container_width=True, key="cancel_refresh_form_only"):
                        st.session_state.confirm_form_refresh = False
                        st.rerun()

        with full_col:
            admin_panel(
                "Full Source Refresh",
                "Deletes records for the selected year, then reloads that year's historical Excel data and Google Form responses.",
            )
            st.error("Use this only when you intentionally want to rebuild the selected year.")
            if st.button("Full Refresh From Sources", use_container_width=True, key="refresh_all_sources"):
                st.session_state.confirm_refresh = True

            if st.session_state.get("confirm_refresh"):
                st.warning(f"This deletes current {refresh_year} records before reloading sources.")
                confirm_col, cancel_col = st.columns(2)
                with confirm_col:
                    if st.button("Confirm Full Refresh", type="secondary", use_container_width=True, key="confirm_refresh_all_sources"):
                        with st.spinner("Refreshing all source data..."):
                            result = load_data.refresh_from_sources(refresh_year)
                        if result["success"]:
                            st.session_state.last_full_refresh_result = result
                            st.session_state.confirm_refresh = False
                            st.cache_resource.clear()
                            st.rerun()
                        else:
                            st.error(f"Full refresh failed: {result['error']}")
                with cancel_col:
                    if st.button("Cancel", use_container_width=True, key="cancel_refresh_all_sources"):
                        st.session_state.confirm_refresh = False
                        st.rerun()

    # ════════════════════════════════════════════════════════════════════
    # SETTINGS TAB
    # ════════════════════════════════════════════════════════════════════
    
    elif selected_menu == "Settings":
        st.title("⚙️ Admin Settings")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🔐 Security")
            
            if st.button("🔓 Logout"):
                st.session_state.admin_authenticated = False
                st.success("✅ Logged out successfully")
                st.rerun()
            
            st.divider()
            
            st.subheader("📊 Database Info")
            
            try:
                record_count = db.count_records()
                reports_df = db.fetch_all_reports()
                report_count = len(reports_df) if reports_df is not None else 0
                
                st.json({
                    "Total Records": record_count,
                    "Total Reports": report_count,
                    "Database Status": "✅ Connected"
                })
            except Exception as e:
                st.error(f"❌ Connection Error: {str(e)}")
        
        with col2:
            st.subheader("📝 About")
            
            st.markdown("""
            **VIT Admin Dashboard**
            
            • Manage counselling data
            • Handle user reports
            • Import/Export functionality
            • Analytics & insights
            
            **Version:** 1.0
            **Last Updated:** May 2026
            """)
            
            st.divider()
            
            if st.checkbox("Show Advanced Options"):
                st.warning("⚠️ Advanced Options")
                
                if st.button("🔄 Clear Cache"):
                    st.cache_resource.clear()
                    st.success("✅ Cache cleared")
                
                if st.button("🐛 Show Debug Info"):
                    st.json({
                        "Session State": dict(st.session_state),
                        "User": "Admin",
                        "Timestamp": datetime.now().isoformat()
                    })
                
                st.divider()
                
                st.subheader("🗑️ Data Refresh / Reset")
                st.error("⚠️ DANGER ZONE - These actions cannot be undone!")
                
                col_refresh1, col_refresh2 = st.columns(2)
                
                with col_refresh1:
                    if st.button("🗑️ DELETE ALL RECORDS", type="secondary", use_container_width=True):
                        st.session_state.confirm_delete_records = True
                    
                    if st.session_state.get("confirm_delete_records"):
                        st.warning("⚠️ Are you absolutely sure? This will delete ALL counselling records!")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ YES, DELETE ALL RECORDS", type="secondary", use_container_width=True):
                                try:
                                    success = db.delete_all_records()
                                    if success:
                                        st.success("✅ All records deleted successfully!")
                                        st.session_state.confirm_delete_records = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete records")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        
                        with col_b:
                            if st.button("❌ CANCEL", use_container_width=True):
                                st.session_state.confirm_delete_records = False
                                st.rerun()
                
                with col_refresh2:
                    if st.button("📋 DELETE ALL REPORTS", type="secondary", use_container_width=True):
                        st.session_state.confirm_delete_reports = True
                    
                    if st.session_state.get("confirm_delete_reports"):
                        st.warning("⚠️ Are you absolutely sure? This will delete ALL user reports!")
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("✅ YES, DELETE ALL REPORTS", type="secondary", use_container_width=True):
                                try:
                                    success = db.delete_all_reports()
                                    if success:
                                        st.success("✅ All reports deleted successfully!")
                                        st.session_state.confirm_delete_reports = False
                                        st.rerun()
                                    else:
                                        st.error("❌ Failed to delete reports")
                                except Exception as e:
                                    st.error(f"❌ Error: {str(e)}")
                        
                        with col_b:
                            if st.button("❌ CANCEL", use_container_width=True):
                                st.session_state.confirm_delete_reports = False
                                st.rerun()
                
                st.divider()
                
                st.subheader("🔄 REFRESH FROM SOURCES")
                settings_refresh_year = selected_admin_year("settings_refresh_year")
                st.info("📌 Delete selected-year records and reload from Google Sheets + Historical Excel")
                st.markdown("""
                This will:
                - 🗑️ Delete current counselling records for the selected year
                - 📊 Reload that year's historical data from Excel
                - 📋 Reload form responses from Google Sheets for the selected year
                """)
                
                if st.button("🔄 REFRESH NOW", type="secondary", use_container_width=True):
                    st.session_state.confirm_refresh = True
                
                if st.session_state.get("confirm_refresh"):
                    st.error(f"⚠️ WARNING: This will rebuild {settings_refresh_year} counselling records!")
                    col_a, col_b = st.columns(2)
                    
                    with col_a:
                        if st.button("✅ YES, REFRESH FROM SOURCES", type="secondary", use_container_width=True):
                            try:
                                # Show loading spinner
                                with st.spinner("⏳ Refreshing data from sources..."):
                                    result = load_data.refresh_from_sources(settings_refresh_year)
                                
                                if result["success"]:
                                    st.success(f"✅ Data refresh successful!")
                                    st.success(f"📊 Historical records loaded: {result['records_loaded']}")
                                    st.success(f"📋 Form responses loaded: {result['form_responses']}")
                                    st.success(f"📈 Total records: {result['total']}")
                                    st.balloons()
                                    st.session_state.confirm_refresh = False
                                    import time
                                    time.sleep(1)
                                    st.rerun()
                                else:
                                    st.error(f"❌ Refresh failed: {result['error']}")
                            except Exception as e:
                                st.error(f"❌ Error: {str(e)}")
                    
                    with col_b:
                        if st.button("❌ CANCEL", use_container_width=True):
                            st.session_state.confirm_refresh = False
                            st.rerun()
