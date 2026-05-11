"""
load_data.py — Data loading, normalisation and cutoff computation.

Storage flow
------------
1. On first start: seed Excel → Supabase  (idempotent, runs once via cache)
2. On every start : sync Google Form responses → Supabase  (upsert, safe to re-run)
3. master_df      : built from Supabase (single source of truth)
4. cutoffs        : 90th-percentile closing rank + true_max + std_dev per group

Public API (imported by app.py / recommender.py)
-------------------------------------------------
  master_df          — pd.DataFrame  (Rank, Campus, Branch, Fee, source)
  cutoffs            — dict  {(campus, branch, fee): {closing_rank, true_max, std_dev, responses}}
  submit_report(...) — bool
  get_reports()      — pd.DataFrame | None
"""

import re
import statistics
from collections import defaultdict

import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

import database as db

# =====================================================
# GOOGLE SHEETS CONNECTION  (form-response ingestion)
# =====================================================

_SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

try:
    _creds = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), _SCOPE
    )
    print("[load] ✅ Google auth via Streamlit secrets")
except Exception:
    _creds = ServiceAccountCredentials.from_json_keyfile_name(
        "credentials.json", _SCOPE
    )
    print("[load] ✅ Google auth via credentials.json")

_gs_client = gspread.authorize(_creds)

SPREADSHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1IOKcDcfUXporFN4VAqh6G1SYuGpCxZo5iCnraVePVsY/edit?usp=sharing"
)

# =====================================================
# BRANCH NORMALISATION
# =====================================================


def normalize_branch(branch: str) -> str:
    branch = str(branch).lower().strip()
    branch = " ".join(branch.split())
    branch_key = re.sub(r"[^a-z0-9]+", " ", branch).strip()
    tokens = set(branch_key.split())

    mapping = {
        # CSE Core
        "cse": "CSE Core",
        "cs": "CSE Core",
        "core": "CSE Core",
        "cse core": "CSE Core",
        "cs core": "CSE Core",
        "csecore": "CSE Core",
        "b tech cse": "CSE Core",
        "btech cse": "CSE Core",
        "computer science": "CSE Core",
        "computer science engineering": "CSE Core",
        # AIML
        "cse aiml": "CSE AIML",
        "cse ai ml": "CSE AIML",
        "cse ai/ml": "CSE AIML",
        "cse ai & ml": "CSE AIML",
        "cse ai&ml": "CSE AIML",
        "aiml": "CSE AIML",
        "ai ml": "CSE AIML",
        "artificial intelligence and machine learning": "CSE AIML",
        # Data Science
        "cse ds": "CSE DS",
        "cse data science": "CSE DS",
        "data science": "CSE DS",
        "ds": "CSE DS",
        # Cybersecurity
        "cse cybersecurity": "CSE Cybersecurity",
        "cybersecurity": "CSE Cybersecurity",
        "cse cyber": "CSE Cybersecurity",
        # Business Systems
        "cse business systems": "CSE Business Systems",
        "cse bs": "CSE Business Systems",
        # Robotics
        "cse ai robo": "CSE Robotics",
        "robotics": "CSE Robotics",
        # IoT
        "cse iot": "CSE IoT",
        "iot": "CSE IoT",
        # CPS
        "cse cps": "CSE CPS",
        "cps": "CSE CPS",
        # ECE
        "ece": "ECE Core",
        "ece core": "ECE Core",
        "electronics and communication": "ECE Core",
        "ecm": "ECM",
        # IT
        "it": "IT Core",
        "it core": "IT Core",
        "information technology": "IT Core",
        # Mechanical
        "mechanical": "Mechanical",
        "me": "Mechanical",
        "mech": "Mechanical",
        "mechanical ev": "Mechanical EV",
        # Mechatronics
        "mechatronics": "Mechatronics",
        # Civil
        "civil": "Civil",
        "ce": "Civil",
        # Electrical
        "electrical": "Electrical",
        "eee": "Electrical",
        "ee": "Electrical",
        "ee vlsi design and technology": "Electrical VLSI",
        # Chemical
        "chemical": "Chemical",
        # Biotech
        "biotechnology": "Biotechnology",
    }

    if branch in mapping:
        return mapping[branch]
    if branch_key in mapping:
        return mapping[branch_key]

    # Smart CSE detection
    if (tokens & {"cse", "cs", "computer"}) or "computer science" in branch_key:
        if tokens & {"core", "science"}:
            return "CSE Core"

    return branch.title()


# =====================================================
# CAMPUS NORMALISATION
# =====================================================


def normalize_campus(campus: str) -> str:
    campus = str(campus).lower().strip()
    mapping = {
        "vellore": "Vellore",
        "vit vellore": "Vellore",
        "chennai": "Chennai",
        "vit chennai": "Chennai",
        "vtc": "Chennai",
        "bhopal": "Bhopal",
        "vit bhopal": "Bhopal",
        "amaravati": "Amaravati",
        "ap": "Amaravati",
        "vit amaravati": "Amaravati",
    }
    return mapping.get(campus, campus.title())


# =====================================================
# VALIDATION HELPERS
# =====================================================


def _valid_fee(fee) -> bool:
    try:
        return 1 <= int(fee) <= 5
    except (TypeError, ValueError):
        return False


def _valid_rank(rank) -> bool:
    try:
        return 1 <= int(rank) <= 250_000
    except (TypeError, ValueError):
        return False


# =====================================================
# SEED HISTORICAL DATA  (idempotent, runs once)
# =====================================================


@st.cache_resource(show_spinner=False)
def _seed_historical() -> int:
    """
    Sync every row from the local Excel file into Supabase via idempotent upsert.

    The upsert uses ON CONFLICT (rank, campus, branch, fee) DO NOTHING, so
    re-running this is completely safe — existing rows are untouched and only
    genuinely new rows are inserted.  The @st.cache_resource guard means this
    runs exactly once per server process, which is the right cadence.

    Previously this function was skipped when Supabase already had >100 rows,
    which meant new rows added to the Excel file were never pushed to Supabase.
    That guard has been removed.
    """
    print("[load] 🌱 Syncing Excel → Supabase (idempotent upsert) …")
    hist = pd.read_excel("data/VIT Counselling Data ( 2025 ).xlsx")
    hist.columns = ["Rank", "Campus", "Branch", "Fee"]
    hist = hist.dropna()
    hist["Rank"] = hist["Rank"].astype(int)
    hist["Fee"] = hist["Fee"].astype(int)
    hist["Branch"] = hist["Branch"].apply(normalize_branch)
    hist["Campus"] = hist["Campus"].apply(normalize_campus)
    hist = hist.drop_duplicates(subset=["Rank", "Campus", "Branch", "Fee"])

    records = [
        {
            "rank": int(row["Rank"]),
            "campus": row["Campus"],
            "branch": row["Branch"],
            "fee": int(row["Fee"]),
            "source": "historical",
        }
        for _, row in hist.iterrows()
    ]
    ok = db.upsert_records(records)
    n = len(records) if ok else 0
    print(f"[load] ✅ Excel → Supabase sync complete: {n:,} rows upserted")
    return n


# =====================================================
# SYNC GOOGLE FORM RESPONSES  (safe to re-run)
# =====================================================


def _sync_form_responses() -> int:
    """
    Pull latest Google Form responses and upsert into Supabase.
    Returns the number of valid rows sent.
    """
    try:
        sheet = _gs_client.open_by_url(SPREADSHEET_URL).sheet1
        raw = sheet.get_all_records()
        if not raw:
            return 0

        df = pd.DataFrame(raw).rename(
            columns={
                "VITEEE Rank": "Rank",
                "Campus": "Campus",
                "Branch": "Branch",
                "Fee Category": "Fee",
            }
        )

        # Keep only the four needed columns (extra form fields ignored)
        for col in ["Rank", "Campus", "Branch", "Fee"]:
            if col not in df.columns:
                print(f"[load] ⚠ Column '{col}' missing from form sheet")
                return 0
        df = df[["Rank", "Campus", "Branch", "Fee"]].copy()

        df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
        df["Fee"] = df["Fee"].astype(str).str.extract(r"(\d+)", expand=False)
        df["Fee"] = pd.to_numeric(df["Fee"], errors="coerce")
        df = df.dropna()
        df["Rank"] = df["Rank"].astype(int)
        df["Fee"] = df["Fee"].astype(int)
        df["Branch"] = df["Branch"].apply(normalize_branch)
        df["Campus"] = df["Campus"].apply(normalize_campus)
        df = df[df["Fee"].apply(_valid_fee) & df["Rank"].apply(_valid_rank)]
        df = df.drop_duplicates(subset=["Rank", "Campus", "Branch", "Fee"])

        records = [
            {
                "rank": int(row["Rank"]),
                "campus": row["Campus"],
                "branch": row["Branch"],
                "fee": int(row["Fee"]),
                "source": "form",
            }
            for _, row in df.iterrows()
        ]
        if records:
            db.upsert_records(records)
        print(f"[load] 🔄 Synced {len(records)} form responses")
        return len(records)
    except Exception as exc:
        print(f"[load] _sync_form_responses error: {exc}")
        return 0


# =====================================================
# BUILD MASTER DF  (runs at import time)
# =====================================================

_seed_historical()
_sync_form_responses()

_hist = pd.read_excel("data/VIT Counselling Data ( 2025 ).xlsx")
_hist.columns = ["Rank", "Campus", "Branch", "Fee"]
_hist = _hist.dropna()
_hist["Rank"] = _hist["Rank"].astype(int)
_hist["Fee"] = _hist["Fee"].astype(int)
_hist["Branch"] = _hist["Branch"].apply(normalize_branch)
_hist["Campus"] = _hist["Campus"].apply(normalize_campus)
_hist["source"] = "historical"

_sb = db.fetch_all_records()

master_df = (
    pd.concat([_hist, _sb], ignore_index=True)
    .drop_duplicates(subset=["Rank", "Campus", "Branch", "Fee"], keep="first")
    .sort_values("Rank")
    .reset_index(drop=True)
)

print(
    f"[load] ✅ master_df: {len(master_df):,} rows ({len(_hist):,} Excel + {len(_sb):,} Supabase)"
)

# Safety fallback: if Supabase returned nothing, load directly from Excel
# so the app stays functional while the DB connection is investigated
if master_df.empty:
    print("[load] ⚠ Supabase returned empty — falling back to Excel")
    _fb = pd.read_excel("data/VIT Counselling Data ( 2025 ).xlsx")
    _fb.columns = ["Rank", "Campus", "Branch", "Fee"]
    _fb = _fb.dropna()
    _fb["Rank"] = _fb["Rank"].astype(int)
    _fb["Fee"] = _fb["Fee"].astype(int)
    _fb["Branch"] = _fb["Branch"].apply(normalize_branch)
    _fb["Campus"] = _fb["Campus"].apply(normalize_campus)
    master_df = _fb.sort_values("Rank").reset_index(drop=True)

print(
    f"[load] ✅ master_df: {len(master_df):,} rows | "
    f"{master_df['Campus'].nunique()} campuses | "
    f"{master_df['Branch'].nunique()} branches"
)

# =====================================================
# BUILD CUTOFFS  (90th-pct + true_max + std_dev)
# =====================================================
#
# closing_rank = 90th-percentile rank for the group
#                (single outlier at the max doesn't inflate the cutoff)
# true_max     = actual maximum rank observed (shown as context in UI)
# std_dev      = standard deviation of observed ranks (volatility signal)
# responses    = total data points for confidence scoring
# =====================================================

_groups: dict[tuple, list[int]] = defaultdict(list)
for _, _row in master_df.iterrows():
    _key = (_row["Campus"], _row["Branch"], _row["Fee"])
    _groups[_key].append(int(_row["Rank"]))

cutoffs: dict[tuple, dict] = {}
for _key, _ranks in _groups.items():
    _n = len(_ranks)
    _srt = sorted(_ranks)
    # 90th-percentile index (clamp to last element)
    _p90_idx = min(int(_n * 0.9), _n - 1)
    cutoffs[_key] = {
        "closing_rank": _srt[_p90_idx],
        "true_max": _srt[-1],
        "std_dev": int(statistics.stdev(_srt)) if _n >= 2 else 0,
        "responses": _n,
    }

print(
    f"[load] ✅ cutoffs: {len(cutoffs)} group entries (90th-pct + true_max + std_dev)"
)

# =====================================================
# PUBLIC API  (called by app.py)
# =====================================================


def submit_report(
    user_rank,
    campus,
    branch,
    fee,
    probability,
    chance,
    report_type,  # ← now a separate param (not buried in reason_text)
    reason_text="",
) -> bool:
    """Persist one user prediction report to Supabase."""
    return db.insert_report(
        user_rank=user_rank,
        campus=campus,
        branch=branch,
        fee=fee,
        probability=probability,
        chance=chance,
        report_type=report_type,
        reason_text=reason_text,
    )


def get_reports():
    """Fetch all reports from Supabase for the admin panel."""
    return db.fetch_reports()


def delete_report(report_id: int) -> bool:
    """Delete a report by ID from Supabase."""
    return db.delete_report(report_id)
