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
from pathlib import Path

import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials

import database as db

DEFAULT_DATA_YEAR = db.DEFAULT_DATA_YEAR
DATA_SHARE_FORM_URL = "https://forms.gle/VG28i72zpKetFA4W6"


def _parse_years(value) -> list[int]:
    """Accept Streamlit secrets as a list or comma-separated string."""
    if value is None:
        return []
    if isinstance(value, str):
        raw_years = re.split(r"[, ]+", value.strip())
    else:
        raw_years = value

    years: list[int] = []
    for raw_year in raw_years:
        if raw_year in (None, ""):
            continue
        try:
            years.append(int(raw_year))
        except (TypeError, ValueError):
            continue
    return years


def _active_data_year() -> int:
    """Year used by the public predictor unless Streamlit secrets override it."""
    try:
        return int(st.secrets.get("active_data_year", DEFAULT_DATA_YEAR))
    except Exception:
        return DEFAULT_DATA_YEAR


ACTIVE_DATA_YEAR = _active_data_year()


def configured_data_years() -> list[int]:
    """
    Years intentionally exposed to admin controls.

    To add the next junior batch later, add this to Streamlit secrets:
        active_data_year = 2026
        available_data_years = "2025,2026"
    """
    years = {DEFAULT_DATA_YEAR, ACTIVE_DATA_YEAR}
    try:
        years.update(_parse_years(st.secrets.get("available_data_years")))
    except Exception:
        pass
    years.update(_available_historical_years())
    return sorted(years)


def data_share_form_url(data_year: int = ACTIVE_DATA_YEAR) -> str:
    """
    Return the form URL for the active public batch.

    Optional secrets:
        data_share_form_url = "https://forms.gle/..."

        [data_share_form_urls]
        2025 = "https://forms.gle/..."
        2026 = "https://forms.gle/..."
    """
    try:
        urls = st.secrets.get("data_share_form_urls", {})
        if str(int(data_year)) in urls:
            return str(urls[str(int(data_year))])
    except Exception:
        pass
    try:
        return str(st.secrets.get("data_share_form_url", DATA_SHARE_FORM_URL))
    except Exception:
        return DATA_SHARE_FORM_URL


def _historical_file_for_year(data_year: int) -> Path:
    matches = sorted(Path("data").glob(f"*{int(data_year)}*.xlsx"))
    if matches:
        return matches[0]
    if int(data_year) == DEFAULT_DATA_YEAR:
        return Path("data/VIT Counselling Data ( 2025 ).xlsx")
    raise FileNotFoundError(f"No historical Excel file found in data/ for {data_year}")


def _empty_historical_df(data_year: int) -> pd.DataFrame:
    return pd.DataFrame(
        columns=["Rank", "Campus", "Branch", "Fee", "source", "data_year"]
    ).astype(
        {
            "Rank": "int64",
            "Campus": "object",
            "Branch": "object",
            "Fee": "int64",
            "source": "object",
            "data_year": "int64",
        }
    )


def _available_historical_years() -> list[int]:
    years = set()
    for path in Path("data").glob("*.xlsx"):
        match = re.search(r"(20\d{2})", path.name)
        if match:
            years.add(int(match.group(1)))
    return sorted(years) or [DEFAULT_DATA_YEAR]

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
        "cse core": "CSE Core",
        "cs core": "CSE Core",
        "csecore": "CSE Core",
        "b tech cse": "CSE Core",
        "btech cse": "CSE Core",
        "computer science": "CSE Core",
        "computer science engineering": "CSE Core",
        "cse cs": "CSE Core",  # typo variant
        "cse spec unspecified": "CSE Core",
        # AIML
        "cse aiml": "CSE AIML",
        "cse ai ml": "CSE AIML",
        "cse ai ml": "CSE AIML",
        "cse ai ml": "CSE AIML",
        "cse ai ml": "CSE AIML",
        "aiml": "CSE AIML",
        "ai ml": "CSE AIML",
        "artificial intelligence and machine learning": "CSE AIML",
        "cse artificial intelligence and machine learning": "CSE AIML",
        # Data Science
        "cse ds": "CSE DS",
        "cse data science": "CSE DS",
        "data science": "CSE DS",
        "ds": "CSE DS",
        # Cybersecurity
        "cse cybersecurity": "CSE Cybersecurity",
        "cybersecurity": "CSE Cybersecurity",
        "cse cyber": "CSE Cybersecurity",
        "cse cyber security": "CSE Cybersecurity",
        "cse cybersec": "CSE Cybersecurity",
        "cyber security": "CSE Cybersecurity",
        # Business Systems
        "cse business systems": "CSE Business Systems",
        "cse bs": "CSE Business Systems",
        "csbs": "CSE Business Systems",
        "cs business systems": "CSE Business Systems",
        # Robotics
        "cse ai robo": "CSE Robotics",
        "robotics": "CSE Robotics",
        "cse robotics": "CSE Robotics",
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
        "electronics and communication engineering": "ECE Core",
        "ecm": "ECM",
        "ecse": "ECSE",
        "electronics and computer engineering": "ECSE",
        # IT
        "it": "IT Core",
        "it core": "IT Core",
        "information technology": "IT Core",
        # Mechanical
        "mechanical": "Mechanical",
        "mech": "Mechanical",
        "mech core": "Mechanical",
        "mechanical core": "Mechanical",
        "mechanical engineering": "Mechanical",
        "mechanical ev": "Mechanical EV",
        "mech ev": "Mechanical EV",
        "mechanical engineering smart manufacturing": "Mechanical EV",
        # Mechatronics
        "mechatronics": "Mechatronics",
        # Civil
        "civil": "Civil",
        "civil engineering": "Civil",
        # Electrical
        "electrical": "Electrical",
        "eee": "Electrical",
        "eie": "Electrical",
        "ee vlsi design and technology": "Electrical VLSI",
        "electronics engineering vlsi design and technology": "Electrical VLSI",
        "ee vlsi": "Electrical VLSI",
        "ee vlsi ": "Electrical VLSI",
        "ee  vlsi ": "Electrical VLSI",
        # Chemical
        "chemical": "Chemical",
        # Biotech
        "biotechnology": "Biotechnology",
        "biotech": "Biotechnology",
        "bio technology": "Biotechnology",
    }

    if branch in mapping:
        return mapping[branch]
    if branch_key in mapping:
        return mapping[branch_key]

    # Smart pattern matching for common variants
    if "vlsi" in tokens:
        return "Electrical VLSI"
    if tokens & {"aiml", "artificial", "machine"} and tokens & {
        "intelligence",
        "learning",
        "aiml",
    }:
        return "CSE AIML"
    if (
        "cybersecurity" in branch_key
        or "cyber security" in branch_key
        or "cybersec" in branch_key
    ):
        return "CSE Cybersecurity"
    if (tokens & {"cse", "cs", "computer"}) or "computer science" in branch_key:
        if tokens & {"core", "science"}:
            return "CSE Core"

    return None  # unknown — caller should reject this row


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


# ── Whitelists — only these canonical names are accepted from form responses ──
# Any branch/campus that normalize_branch / normalize_campus does not map to
# one of these values is silently dropped before the Supabase upsert.

VALID_CAMPUSES: set[str] = {
    "Vellore",
    "Chennai",
    "Bhopal",
    "Amaravati",
}

VALID_BRANCHES: set[str] = {
    # CSE family
    "CSE Core",
    "CSE AIML",
    "CSE DS",
    "CSE Cybersecurity",
    "CSE Business Systems",
    "CSE Robotics",
    "CSE IoT",
    "CSE CPS",
    # ECE / Electronics
    "ECE Core",
    "ECM",
    "ECSE",
    # IT
    "IT Core",
    # Electrical
    "Electrical",
    "Electrical VLSI",
    # Mechanical
    "Mechanical",
    "Mechanical EV",
    "Mechatronics",
    # Others
    "Civil",
    "Chemical",
    "Biotechnology",
}


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
    total = 0
    for data_year in _available_historical_years():
        print(f"[load] 🌱 Syncing {data_year} Excel → Supabase (idempotent upsert) …")
        records = _build_historical_records(data_year)
        ok = db.upsert_records(records)
        n = len(records) if ok else 0
        total += n
        print(f"[load] ✅ {data_year} Excel → Supabase sync complete: {n:,} rows upserted")
    return total


def _load_historical_df(data_year: int) -> pd.DataFrame:
    """Load and normalise one year's historical Excel file."""
    try:
        hist = pd.read_excel(_historical_file_for_year(data_year))
    except FileNotFoundError:
        print(f"[load] ⚠ No historical Excel file found for {data_year}; using DB/form rows only")
        return _empty_historical_df(data_year)
    hist.columns = ["Rank", "Campus", "Branch", "Fee"]
    hist = hist.dropna()
    hist["Rank"] = hist["Rank"].astype(int)
    hist["Fee"] = hist["Fee"].astype(int)
    hist["Branch"] = hist["Branch"].apply(normalize_branch)
    hist["Campus"] = hist["Campus"].apply(normalize_campus)
    hist = hist.dropna(subset=["Branch", "Campus"])
    hist = hist.drop_duplicates(subset=["Rank", "Campus", "Branch", "Fee"])
    hist["source"] = "historical"
    hist["data_year"] = int(data_year)
    return hist


def _build_historical_records(data_year: int) -> list[dict]:
    hist = _load_historical_df(data_year)
    return [
        {
            "rank": int(row["Rank"]),
            "campus": row["Campus"],
            "branch": row["Branch"],
            "fee": int(row["Fee"]),
            "source": "historical",
            "data_year": int(data_year),
        }
        for _, row in hist.iterrows()
    ]


# =====================================================
# SYNC GOOGLE FORM RESPONSES  (safe to re-run)
# =====================================================


def _sync_form_responses(data_year: int = ACTIVE_DATA_YEAR) -> int:
    """
    Pull latest Google Form responses and upsert into Supabase.
    Returns the number of valid rows sent.
    """
    try:
        records = _build_form_records(data_year)
        if records:
            db.upsert_records(records)
        print(f"[load] 🔄 Synced {len(records)} valid form responses")
        return len(records)
    except Exception as exc:
        print(f"[load] _sync_form_responses error: {exc}")
        return 0


def _build_form_records(data_year: int = ACTIVE_DATA_YEAR) -> list[dict]:
    """Read Google Form responses and return validated Supabase records."""
    sheet = _gs_client.open_by_url(SPREADSHEET_URL).sheet1
    raw = sheet.get_all_records()
    if not raw:
        return []

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
            return []
    df = df[["Rank", "Campus", "Branch", "Fee"]].copy()

    df["Rank"] = pd.to_numeric(df["Rank"], errors="coerce")
    df["Fee"] = df["Fee"].astype(str).str.extract(r"(\d+)", expand=False)
    df["Fee"] = pd.to_numeric(df["Fee"], errors="coerce")
    df = df.dropna()
    df["Rank"] = df["Rank"].astype(int)
    df["Fee"] = df["Fee"].astype(int)
    df["Branch"] = df["Branch"].apply(normalize_branch)
    df["Campus"] = df["Campus"].apply(normalize_campus)

    # Strict whitelist: drop any row with an unrecognised branch or campus.
    before = len(df)
    df = df[
        df["Branch"].isin(VALID_BRANCHES)
        & df["Campus"].isin(VALID_CAMPUSES)
        & df["Fee"].apply(_valid_fee)
        & df["Rank"].apply(_valid_rank)
    ]
    dropped = before - len(df)
    if dropped:
        print(f"[load] ⚠ Dropped {dropped} form rows with invalid branch/campus/fee/rank")

    df = df.drop_duplicates(subset=["Rank", "Campus", "Branch", "Fee"])
    return [
        {
            "rank": int(row["Rank"]),
            "campus": row["Campus"],
            "branch": row["Branch"],
            "fee": int(row["Fee"]),
            "source": "form",
            "data_year": int(data_year),
        }
        for _, row in df.iterrows()
    ]


# =====================================================
# BUILD MASTER DF  (runs at import time)
# =====================================================

_seed_historical()
_sync_form_responses()

_hist = _load_historical_df(ACTIVE_DATA_YEAR)

_sb = db.fetch_all_records()
if "data_year" in _sb.columns:
    _sb = _sb[_sb["data_year"] == ACTIVE_DATA_YEAR]

master_df = (
    pd.concat([_hist, _sb], ignore_index=True)
    .drop_duplicates(subset=["Rank", "Campus", "Branch", "Fee", "data_year"], keep="first")
    .sort_values("Rank")
    .reset_index(drop=True)
)

print(
    f"[load] ✅ master_df {ACTIVE_DATA_YEAR}: {len(master_df):,} rows "
    f"({len(_hist):,} Excel + {len(_sb):,} Supabase)"
)

# Safety fallback: if Supabase returned nothing, load directly from Excel
# so the app stays functional while the DB connection is investigated
if master_df.empty:
    print("[load] ⚠ Supabase returned empty — falling back to Excel")
    _fb = _load_historical_df(ACTIVE_DATA_YEAR)
    master_df = _fb.sort_values("Rank").reset_index(drop=True)

print(
    f"[load] ✅ master_df {ACTIVE_DATA_YEAR}: {len(master_df):,} rows | "
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


def refresh_from_sources(data_year: int = ACTIVE_DATA_YEAR) -> dict:
    """
    ADMIN ONLY: Refresh one data year by:
    1. Delete existing counselling records for that year
    2. Reload that year's Excel file (historical data)
    3. Reload Google Sheets form responses tagged to that year
    
    Returns dict with results: {
        'success': bool,
        'records_loaded': int,
        'form_responses': int,
        'error': str (if any)
    }
    """
    try:
        data_year = int(data_year)
        print(f"[load] 🔄 Starting {data_year} data refresh from sources...")
        
        # Step 1: Delete existing records for this year only.
        print(f"[load] Step 1: Clearing existing {data_year} records...")
        db.delete_records_by_year(data_year)
        print(f"[load] ✅ Existing {data_year} records cleared")
        
        # Step 2: Load historical data from Excel
        print("[load] Step 2: Loading historical data from Excel...")
        records = _build_historical_records(data_year)
        
        if records:
            ok = db.upsert_records(records)
            records_loaded = len(records) if ok else 0
        else:
            records_loaded = 0
        
        print(f"[load] ✅ Loaded {records_loaded} historical records")
        
        # Step 3: Load form responses from Google Sheets
        print("[load] Step 3: Loading form responses from Google Sheets...")
        form_records = _build_form_records(data_year)
        if form_records:
            ok = db.upsert_records(form_records)
            form_responses = len(form_records) if ok else 0
        else:
            form_responses = 0
        print(f"[load] ✅ Loaded {form_responses} form responses")
        
        # Success!
        total = records_loaded + form_responses
        print(f"[load] 🎉 Data refresh complete! Loaded {total} total records")
        
        return {
            "success": True,
            "data_year": data_year,
            "records_loaded": records_loaded,
            "form_responses": form_responses,
            "total": total,
            "error": None
        }
        
    except Exception as e:
        error_msg = f"Data refresh failed: {str(e)}"
        print(f"[load] ❌ {error_msg}")
        return {
            "success": False,
            "data_year": data_year if "data_year" in locals() else ACTIVE_DATA_YEAR,
            "records_loaded": 0,
            "form_responses": 0,
            "total": 0,
            "error": error_msg
        }


def refresh_form_responses_only(data_year: int = ACTIVE_DATA_YEAR) -> dict:
    """
    ADMIN ONLY: Refresh just Google Form records.

    Historical Excel rows and user reports are preserved. Existing rows with
    source='form' are cleared before the latest valid form responses are loaded.
    """
    try:
        data_year = int(data_year)
        print(f"[load] 🔄 Starting {data_year} form-only refresh...")
        existing_sources = db.get_source_counts(data_year)
        previous_form_records = existing_sources.get("form", 0)

        records = _build_form_records(data_year)
        if not db.delete_records_by_source("form", data_year):
            return {
                "success": False,
                "data_year": data_year,
                "previous_form_records": previous_form_records,
                "form_responses": 0,
                "error": "Could not clear existing form records",
            }

        ok = db.upsert_records(records) if records else True
        if not ok:
            return {
                "success": False,
                "data_year": data_year,
                "previous_form_records": previous_form_records,
                "form_responses": 0,
                "error": "Could not insert refreshed form records",
            }

        print(f"[load] ✅ Form-only refresh complete: {len(records)} rows")
        return {
            "success": True,
            "data_year": data_year,
            "previous_form_records": previous_form_records,
            "form_responses": len(records),
            "error": None,
        }

    except Exception as e:
        error_msg = f"Form refresh failed: {str(e)}"
        print(f"[load] ❌ {error_msg}")
        return {
            "success": False,
            "data_year": data_year if "data_year" in locals() else ACTIVE_DATA_YEAR,
            "previous_form_records": 0,
            "form_responses": 0,
            "error": error_msg,
        }
