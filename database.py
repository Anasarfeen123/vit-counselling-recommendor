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

import re
from datetime import datetime, timezone
from typing import Optional

import pandas as pd
import streamlit as st
from supabase import Client, create_client

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
        sb = get_supabase()
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
        sb = get_supabase()
        rows: list[dict] = []
        offset = 0
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

        df = pd.DataFrame(rows).rename(
            columns={
                "rank": "Rank",
                "campus": "Campus",
                "branch": "Branch",
                "fee": "Fee",
            }
        )
        df["Rank"] = df["Rank"].astype(int)
        df["Fee"] = df["Fee"].astype(int)
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
    clean_reason = str(reason_text).strip()
    payload = {
        "user_rank": int(user_rank),
        "campus": str(campus),
        "branch": str(branch),
        "fee_category": int(fee),
        "predicted_probability": round(float(probability), 1),
        "predicted_chance": str(chance),
        "report_type": str(report_type),
        "reason_text": clean_reason or None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    # Some deployed Supabase projects may still have the first reports schema,
    # before the `report_type` or app-managed `created_at` columns were added.
    # Try the current schema first, then gracefully retry with compatible payloads
    # so user reports are not silently lost during schema drift.
    payload_attempts = [payload]

    legacy_reason = (
        f"[{report_type}] {clean_reason}" if clean_reason else f"[{report_type}]"
    )
    without_report_type = dict(payload)
    without_report_type.pop("report_type", None)
    without_report_type["reason_text"] = legacy_reason
    payload_attempts.append(without_report_type)

    without_created_at = dict(payload)
    without_created_at.pop("created_at", None)
    payload_attempts.append(without_created_at)

    legacy_minimal = dict(without_report_type)
    legacy_minimal.pop("created_at", None)
    payload_attempts.append(legacy_minimal)

    last_exc: Exception | None = None
    for attempt_payload in payload_attempts:
        try:
            get_supabase().table("reports").insert(attempt_payload).execute()
            return True
        except Exception as exc:
            last_exc = exc

    print(f"[db] insert_report error: {last_exc}")
    return False


def delete_report(report_id: int) -> bool:
    """
    Delete a single report row by primary key.
    Returns True on success, False on any error.
    """
    try:
        get_supabase().table("reports").delete().eq("id", int(report_id)).execute()
        return True
    except Exception as exc:
        print(f"[db] delete_report error: {exc}")
        return False


def _first_present(row: pd.Series, candidates: list[str], default=""):
    """Return the first non-empty value from possible column names."""
    for col in candidates:
        if col in row and pd.notna(row[col]) and row[col] != "":
            return row[col]
    return default


def _normalise_report_rows(rows: list[dict]) -> pd.DataFrame:
    """Convert Supabase report rows from current or legacy schemas for admin UI."""
    _empty_cols = [
        "id",
        "Timestamp",
        "User Rank",
        "Campus",
        "Branch",
        "Fee Category",
        "Predicted Probability (%)",
        "Predicted Chance",
        "Report Type",
        "Reason",
    ]
    if not rows:
        return pd.DataFrame(columns=_empty_cols)

    raw = pd.DataFrame(rows)
    normalised_rows: list[dict] = []

    for _, row in raw.iterrows():
        reason = _first_present(
            row, ["reason_text", "reason", "Reason", "details", "Details"], ""
        )
        report_type = _first_present(
            row, ["report_type", "Report Type", "type", "issue_type"], "other"
        )

        # Legacy inserts stored the report type at the start of the reason, e.g.
        # "[wrong_cutoff] cutoff looked too low". Recover it for filtering/cards.
        if (not report_type or report_type == "other") and isinstance(reason, str):
            match = re.match(r"^\[([a-z_]+)\]\s*(.*)$", reason.strip())
            if match:
                report_type = match.group(1)
                reason = match.group(2).strip()

        normalised_rows.append(
            {
                "id": _first_present(row, ["id", "ID"], ""),
                "Timestamp": _first_present(
                    row,
                    [
                        "created_at",
                        "timestamp",
                        "Timestamp",
                        "submitted_at",
                        "Submitted At",
                    ],
                    "",
                ),
                "User Rank": _first_present(
                    row, ["user_rank", "User Rank", "rank", "Rank"], ""
                ),
                "Campus": _first_present(row, ["campus", "Campus"], ""),
                "Branch": _first_present(row, ["branch", "Branch"], ""),
                "Fee Category": _first_present(
                    row, ["fee_category", "Fee Category", "fee", "Fee"], ""
                ),
                "Predicted Probability (%)": _first_present(
                    row,
                    [
                        "predicted_probability",
                        "Predicted Probability (%)",
                        "probability",
                        "Probability",
                    ],
                    "",
                ),
                "Predicted Chance": _first_present(
                    row,
                    ["predicted_chance", "Predicted Chance", "chance", "Chance"],
                    "",
                ),
                "Report Type": report_type or "other",
                "Reason": reason or "(no reason given)",
            }
        )

    df = pd.DataFrame(normalised_rows, columns=_empty_cols)
    df["Reason"] = (
        df["Reason"].replace("", "(no reason given)").fillna("(no reason given)")
    )
    return df


def fetch_reports() -> Optional[pd.DataFrame]:
    """
    Fetch all reports ordered by most recent first.

    Returns a DataFrame with admin-panel-friendly column names:
        id, Timestamp, User Rank, Campus, Branch, Fee Category,
        Predicted Probability (%), Predicted Chance, Report Type, Reason

    Returns None on connection/query error (caller shows an error banner).
    Returns an empty DataFrame when the table has no rows.
    """
    try:
        table = get_supabase().table("reports")
        try:
            resp = table.select("*").order("created_at", desc=True).execute()
        except Exception:
            # Older deployments may not have created_at; fetch without server-side
            # ordering instead of showing an empty dashboard.
            resp = get_supabase().table("reports").select("*").execute()

        rows = resp.data or []
        df = _normalise_report_rows(rows)

        if not df.empty and "Timestamp" in df.columns:
            sort_key = pd.to_datetime(df["Timestamp"], errors="coerce", utc=True)
            df = (
                df.assign(_sort_timestamp=sort_key)
                .sort_values("_sort_timestamp", ascending=False, na_position="last")
                .drop(columns=["_sort_timestamp"])
                .reset_index(drop=True)
            )
        return df

    except Exception as exc:
        print(f"[db] fetch_reports error: {exc}")
        return None


# Alias for admin app compatibility
def fetch_all_reports() -> Optional[pd.DataFrame]:
    """Alias for fetch_reports() — returns all reports in admin-friendly format."""
    return fetch_reports()
