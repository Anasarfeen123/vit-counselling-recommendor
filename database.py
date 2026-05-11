"""
database.py — Supabase persistence layer for VIT Counselling Predictor.

Tables
------
counselling_records  : all student allotment data (historical + live form)
reports              : user-submitted prediction accuracy flags (with type tag)

Usage
-----
Add to .streamlit/secrets.toml (or Streamlit Cloud secrets):

    [supabase]
    url  = "https://<project-ref>.supabase.co"
    key  = "<service_role key>"          # use service_role, NOT anon
"""

from __future__ import annotations

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timezone
from typing import Optional


# ── Singleton client ─────────────────────────────────────────────────────────

@st.cache_resource(show_spinner=False)
def get_supabase() -> Client:
    """Return a single Supabase client shared across all Streamlit sessions."""
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    return create_client(url, key)


# ── counselling_records ──────────────────────────────────────────────────────

def count_records() -> int:
    """
    Fast HEAD-count of rows in counselling_records.
    Returns 0 on error.
    """
    try:
        resp = (
            get_supabase()
            .table("counselling_records")
            .select("id", count="exact")
            .limit(1)
            .execute()
        )
        return resp.count or 0
    except Exception as exc:
        print(f"[db] count_records error: {exc}")
        return 0


def upsert_records(records: list[dict]) -> bool:
    """
    Bulk-upsert counselling records.
    Conflict resolution key: (rank, campus, branch, fee) — do nothing on conflict.

    Each record dict must have keys: rank, campus, branch, fee, source.
    Returns True on success, False on any error.
    """
    if not records:
        return True
    try:
        sb         = get_supabase()
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            sb.table("counselling_records").upsert(
                records[i : i + chunk_size],
                on_conflict="rank,campus,branch,fee",
            ).execute()
        return True
    except Exception as exc:
        print(f"[db] upsert_records error: {exc}")
        return False


def fetch_all_records() -> pd.DataFrame:
    """
    Fetch every row from counselling_records with pagination.

    Returns a DataFrame with columns:
        Rank (int), Campus (str), Branch (str), Fee (int), source (str)
    Returns an empty DataFrame on error.
    """
    try:
        sb        = get_supabase()
        rows: list[dict] = []
        offset    = 0
        page_size = 1000

        while True:
            resp = (
                sb.table("counselling_records")
                .select("rank,campus,branch,fee,source")
                .range(offset, offset + page_size - 1)
                .execute()
            )
            if not resp.data:
                break
            rows.extend(resp.data)
            if len(resp.data) < page_size:
                break
            offset += page_size

        if not rows:
            return pd.DataFrame(columns=["Rank", "Campus", "Branch", "Fee", "source"])

        df = (
            pd.DataFrame(rows)
            .rename(columns={
                "rank":   "Rank",
                "campus": "Campus",
                "branch": "Branch",
                "fee":    "Fee",
            })
        )
        df["Rank"] = df["Rank"].astype(int)
        df["Fee"]  = df["Fee"].astype(int)
        return df

    except Exception as exc:
        print(f"[db] fetch_all_records error: {exc}")
        return pd.DataFrame(columns=["Rank", "Campus", "Branch", "Fee", "source"])


def get_source_counts() -> dict[str, int]:
    """Return {'historical': N, 'form': M} counts for the data quality display."""
    try:
        df = fetch_all_records()
        if df.empty or "source" not in df.columns:
            return {}
        return df["source"].value_counts().to_dict()
    except Exception:
        return {}


# ── reports ──────────────────────────────────────────────────────────────────

def insert_report(
    *,
    user_rank: int,
    campus: str,
    branch: str,
    fee: int,
    probability: float,
    chance: str,
    report_type: str,
    reason_text: str = "",
) -> bool:
    """
    Insert one user-submitted prediction report.

    report_type must be one of:
        'wrong_cutoff' | 'got_allotted' | 'not_allotted' |
        'prob_high'    | 'prob_low'     | 'other'

    Returns True on success, False on any error.
    """
    try:
        get_supabase().table("reports").insert({
            "user_rank":             int(user_rank),
            "campus":                str(campus),
            "branch":                str(branch),
            "fee_category":          int(fee),
            "predicted_probability": round(float(probability), 1),
            "predicted_chance":      str(chance),
            "report_type":           str(report_type),
            "reason_text":           str(reason_text).strip() or None,
            "created_at":            datetime.now(timezone.utc).isoformat(),
        }).execute()
        return True
    except Exception as exc:
        print(f"[db] insert_report error: {exc}")
        return False


def fetch_reports() -> Optional[pd.DataFrame]:
    """
    Fetch all reports ordered by most recent first.

    Returns a DataFrame with admin-panel-friendly column names:
        id, Timestamp, User Rank, Campus, Branch, Fee Category,
        Predicted Probability (%), Predicted Chance, Report Type, Reason

    Returns None on connection/query error (caller shows an error banner).
    Returns an empty DataFrame when the table has no rows.
    """
    _empty_cols = [
        "id", "Timestamp", "User Rank", "Campus", "Branch",
        "Fee Category", "Predicted Probability (%)",
        "Predicted Chance", "Report Type", "Reason",
    ]
    try:
        resp = (
            get_supabase()
            .table("reports")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        if not resp.data:
            return pd.DataFrame(columns=_empty_cols)

        df = pd.DataFrame(resp.data).rename(columns={
            "user_rank":             "User Rank",
            "campus":                "Campus",
            "branch":                "Branch",
            "fee_category":          "Fee Category",
            "predicted_probability": "Predicted Probability (%)",
            "predicted_chance":      "Predicted Chance",
            "report_type":           "Report Type",
            "reason_text":           "Reason",
            "created_at":            "Timestamp",
        })
        # Fill missing reason with placeholder
        if "Reason" in df.columns:
            df["Reason"] = df["Reason"].fillna("(no reason given)")
        return df

    except Exception as exc:
        print(f"[db] fetch_reports error: {exc}")
        return None
