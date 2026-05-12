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

DEFAULT_DATA_YEAR = 2025

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
    Conflict resolution key: (rank, campus, branch, fee, data_year).

    Each record dict must have keys: rank, campus, branch, fee, source.
    data_year is optional and defaults to 2025 for legacy/current data.
    Returns True on success, False on any error.
    """
    if not records:
        return True
    try:
        sb = get_supabase()
        chunk_size = 500
        for i in range(0, len(records), chunk_size):
            chunk = [
                {
                    **record,
                    "data_year": int(record.get("data_year", DEFAULT_DATA_YEAR)),
                }
                for record in records[i : i + chunk_size]
            ]
            sb.table("counselling_records").upsert(
                chunk,
                on_conflict="rank,campus,branch,fee,data_year",
            ).execute()
        return True
    except Exception as exc:
        # Backward compatibility while the deployed Supabase table still has
        # the original 2025-only schema without data_year.
        if all(int(record.get("data_year", DEFAULT_DATA_YEAR)) == DEFAULT_DATA_YEAR for record in records):
            try:
                sb = get_supabase()
                chunk_size = 500
                for i in range(0, len(records), chunk_size):
                    legacy_chunk = []
                    for record in records[i : i + chunk_size]:
                        legacy_record = dict(record)
                        legacy_record.pop("data_year", None)
                        legacy_chunk.append(legacy_record)
                    sb.table("counselling_records").upsert(
                        legacy_chunk,
                        on_conflict="rank,campus,branch,fee",
                    ).execute()
                return True
            except Exception as legacy_exc:
                print(f"[db] upsert_records legacy error: {legacy_exc}")

        print(f"[db] upsert_records error: {exc}")
        return False


def fetch_all_records() -> pd.DataFrame:
    """
    Fetch every row from counselling_records with pagination.

    Returns a DataFrame with columns:
        Rank (int), Campus (str), Branch (str), Fee (int), source (str),
        data_year (int)
    Returns an empty DataFrame on error.
    """
    try:
        sb = get_supabase()
        rows: list[dict] = []
        offset = 0
        page_size = 1000
        select_cols = "rank,campus,branch,fee,source,data_year"

        while True:
            try:
                resp = (
                    sb.table("counselling_records")
                    .select(select_cols)
                    .range(offset, offset + page_size - 1)
                    .execute()
                )
            except Exception:
                select_cols = "rank,campus,branch,fee,source"
                resp = (
                    sb.table("counselling_records")
                    .select(select_cols)
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
            return pd.DataFrame(
                columns=["Rank", "Campus", "Branch", "Fee", "source", "data_year"]
            )

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
        if "data_year" not in df.columns:
            df["data_year"] = DEFAULT_DATA_YEAR
        df["data_year"] = df["data_year"].fillna(DEFAULT_DATA_YEAR).astype(int)
        return df

    except Exception as exc:
        print(f"[db] fetch_all_records error: {exc}")
        return pd.DataFrame(
            columns=["Rank", "Campus", "Branch", "Fee", "source", "data_year"]
        )


def get_source_counts(data_year: int | None = None) -> dict[str, int]:
    """Return {'historical': N, 'form': M} counts for the data quality display."""
    try:
        df = fetch_all_records()
        if data_year is not None and "data_year" in df.columns:
            df = df[df["data_year"] == int(data_year)]
        if df.empty or "source" not in df.columns:
            return {}
        return df["source"].value_counts().to_dict()
    except Exception:
        return {}


def get_available_data_years() -> list[int]:
    """Return all data years found in counselling_records, defaulting to 2025."""
    try:
        df = fetch_all_records()
        if df.empty or "data_year" not in df.columns:
            return [DEFAULT_DATA_YEAR]
        years = sorted(df["data_year"].dropna().astype(int).unique().tolist())
        return years or [DEFAULT_DATA_YEAR]
    except Exception:
        return [DEFAULT_DATA_YEAR]


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


def delete_all_records() -> bool:
    """
    Delete ALL records from counselling_records table.
    ⚠️ WARNING: This action cannot be undone!
    Returns True on success, False on any error.
    """
    try:
        get_supabase().table("counselling_records").delete().neq("id", -1).execute()
        return True
    except Exception as exc:
        print(f"[db] delete_all_records error: {exc}")
        return False


def delete_records_by_source(source: str, data_year: int | None = None) -> bool:
    """
    Delete counselling_records rows for one source, for example 'form'.
    Returns True on success, False on any error.
    """
    try:
        query = get_supabase().table("counselling_records").delete().eq(
            "source", str(source)
        )
        if data_year is not None:
            try:
                query = query.eq("data_year", int(data_year))
            except Exception:
                pass
        query.execute()
        return True
    except Exception as exc:
        if data_year == DEFAULT_DATA_YEAR:
            try:
                get_supabase().table("counselling_records").delete().eq(
                    "source", str(source)
                ).execute()
                return True
            except Exception:
                pass
        print(f"[db] delete_records_by_source error: {exc}")
        return False


def delete_records_by_year(data_year: int) -> bool:
    """
    Delete counselling_records rows for one data year.
    Returns True on success, False on any error.
    """
    try:
        get_supabase().table("counselling_records").delete().eq(
            "data_year", int(data_year)
        ).execute()
        return True
    except Exception as exc:
        if int(data_year) == DEFAULT_DATA_YEAR:
            return delete_all_records()
        print(f"[db] delete_records_by_year error: {exc}")
        return False


def delete_record(
    *,
    rank: int,
    campus: str,
    branch: str,
    fee: int,
    data_year: int | None = None,
) -> bool:
    """
    Delete one counselling record by its natural key.

    data_year is included when available so the admin UI can safely distinguish
    the same rank/campus/branch/fee across counselling years.
    """
    try:
        query = (
            get_supabase()
            .table("counselling_records")
            .delete()
            .eq("rank", int(rank))
            .eq("campus", str(campus))
            .eq("branch", str(branch))
            .eq("fee", int(fee))
        )
        if data_year is not None:
            query = query.eq("data_year", int(data_year))
        query.execute()
        return True
    except Exception as exc:
        if data_year == DEFAULT_DATA_YEAR:
            try:
                (
                    get_supabase()
                    .table("counselling_records")
                    .delete()
                    .eq("rank", int(rank))
                    .eq("campus", str(campus))
                    .eq("branch", str(branch))
                    .eq("fee", int(fee))
                    .execute()
                )
                return True
            except Exception:
                pass
        print(f"[db] delete_record error: {exc}")
        return False


def delete_all_reports() -> bool:
    """
    Delete ALL reports from reports table.
    ⚠️ WARNING: This action cannot be undone!
    Returns True on success, False on any error.
    """
    try:
        get_supabase().table("reports").delete().neq("id", -1).execute()
        return True
    except Exception as exc:
        print(f"[db] delete_all_reports error: {exc}")
        return False


def refresh_all_data(records: list[dict]) -> bool:
    """
    Delete all existing data and reload with fresh records.
    ⚠️ WARNING: This action cannot be undone!
    Returns True on success, False on any error.
    """
    try:
        # Delete all reports first
        get_supabase().table("reports").delete().neq("id", -1).execute()
        # Delete all records
        get_supabase().table("counselling_records").delete().neq("id", -1).execute()
        
        # Re-insert fresh records
        if records:
            chunk_size = 500
            for i in range(0, len(records), chunk_size):
                get_supabase().table("counselling_records").insert(
                    records[i : i + chunk_size]
                ).execute()
        
        return True
    except Exception as exc:
        print(f"[db] refresh_all_data error: {exc}")
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
