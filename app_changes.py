"""
app_changes.py
==============
Two surgical patches needed in app.py after the Supabase migration.
Copy-paste the NEW blocks to replace the OLD blocks shown below.
"""


# ══════════════════════════════════════════════════════════════════════
# PATCH 2  — Admin panel report cards  (~line 490 in your app.py)
# Add a "Report Type" badge next to the predicted-chance badge
# ══════════════════════════════════════════════════════════════════════

OLD_2 = """
                        <div style="display:flex;gap:0.5rem;align-items:center;flex-wrap:wrap;">
                                <span style="
                                    font-size:0.72rem;font-weight:700;
                                    padding:3px 10px;border-radius:99px;
                                    background:{cc}22;color:{cc};
                                    border:1px solid {cc}55;
                                ">{chance_val}</span>
                                <span style="font-size:0.75rem;color:var(--vit-muted);">
                                    Prob: {row.get("Predicted Probability (%)","—")}%
                                </span>
                                <span style="font-size:0.75rem;color:var(--vit-muted);">
                                    Rank: {row.get("User Rank","—"):,}
                                </span>
                                <span style="font-size:0.72rem;color:var(--vit-soft);">{ts}</span>
                            </div>
"""

# Build this helper map once (add near the top of the admin-authed block):
REPORT_TYPE_META = {
    "wrong_cutoff": {"label": "Wrong cutoff",  "color": "#f59e0b"},
    "got_allotted": {"label": "Got allotted",  "color": "#10b981"},
    "not_allotted": {"label": "Not allotted",  "color": "#ef4444"},
    "prob_high":    {"label": "Prob too high", "color": "#6366f1"},
    "prob_low":     {"label": "Prob too low",  "color": "#ec4899"},
    "other":        {"label": "Other",         "color": "#64748b"},
}

NEW_2 = """
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
                                    Prob: {row.get("Predicted Probability (%)","—")}%
                                </span>
                                <span style="font-size:0.75rem;color:var(--vit-muted);">
                                    Rank: {row.get("User Rank","—"):,}
                                </span>
                                <span style="font-size:0.72rem;color:var(--vit-soft);">{ts}</span>
                            </div>
"""

# And before the st.markdown(...) call in the admin card loop, add:
REPORT_TYPE_BADGE_CODE = """
                    rtype_raw  = str(row.get("Report Type", "other"))
                    rtype_meta = REPORT_TYPE_META.get(rtype_raw, {"label": rtype_raw, "color": "#64748b"})
                    report_type_badge = (
                        f'<span style="'
                        f'font-size:0.72rem;font-weight:700;'
                        f'padding:3px 10px;border-radius:99px;'
                        f'background:{rtype_meta[\"color\"]}22;'
                        f'color:{rtype_meta[\"color\"]};'
                        f'border:1px solid {rtype_meta[\"color\"]}55;">'
                        f'{rtype_meta[\"label\"]}'
                        f'</span>'
                    )
"""
