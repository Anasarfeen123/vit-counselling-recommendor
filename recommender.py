from load_data import cutoffs
import statistics

# =====================================================
# CONFIDENCE SCORE
# =====================================================

def get_confidence(responses):
    if responses >= 20:
        return "Very High 🟢"
    elif responses >= 12:
        return "High 🟢"
    elif responses >= 6:
        return "Medium 🟡"
    elif responses >= 3:
        return "Low 🔴"
    return "Very Low 🔴"


def get_confidence_percentage(responses):
    if responses >= 30:
        return 95
    elif responses >= 20:
        return 85
    elif responses >= 12:
        return 75
    elif responses >= 6:
        return 60
    elif responses >= 3:
        return 40
    else:
        return 20


def calculate_probability(user_rank, closing_rank, responses):
    """
    Probability of admission based on rank buffer and data confidence.
    Rank buffer is the primary signal; response count adjusts uncertainty only.
    """
    rank_buffer = closing_rank - user_rank
    buffer_ratio = rank_buffer / closing_rank if closing_rank else -1

    if rank_buffer >= 0:
        if rank_buffer >= 25000 or buffer_ratio >= 0.65:
            base_prob = 94
        elif rank_buffer >= 10000 or buffer_ratio >= 0.45:
            base_prob = 88
        elif rank_buffer >= 5000 or buffer_ratio >= 0.25:
            base_prob = 80
        elif rank_buffer >= 2000 or buffer_ratio >= 0.12:
            base_prob = 70
        elif rank_buffer >= 500 or buffer_ratio >= 0.04:
            base_prob = 58
        else:
            base_prob = 46
    elif rank_buffer >= -500:
        base_prob = 35
    elif rank_buffer >= -2000:
        base_prob = 25
    elif rank_buffer >= -5000:
        base_prob = 15
    else:
        base_prob = 8

    if responses >= 12:
        uncertainty_penalty = 0
    elif responses >= 6:
        uncertainty_penalty = 2
    elif responses >= 3:
        uncertainty_penalty = 3
    elif responses == 2:
        uncertainty_penalty = 5
    else:
        uncertainty_penalty = 6

    if rank_buffer >= 5000 or buffer_ratio >= 0.25:
        uncertainty_penalty = min(uncertainty_penalty, 3)

    return round(max(1, min(98, base_prob - uncertainty_penalty)), 1)


# =====================================================
# CHANCE CLASSIFICATION
# =====================================================

def get_chance_category(probability):
    if probability >= 75:
        return "Safe"
    elif probability >= 40:
        return "Moderate"
    elif probability >= 15:
        return "Dream"
    else:
        return "Very Unlikely"


def get_chance_color(chance):
    return {
        "Safe": "#10b981",
        "Moderate": "#f59e0b",
        "Dream": "#ef4444",
        "Very Unlikely": "#6b7280",
    }.get(chance, "#95a5a6")


def get_emoji_for_probability(probability):
    if probability >= 85: return "✅"
    elif probability >= 70: return "👍"
    elif probability >= 50: return "⚡"
    elif probability >= 25: return "🔥"
    else: return "💭"


# =====================================================
# BRANCH PRIORITY
# =====================================================

BRANCH_PRIORITY_MAP = {
    "cse core":             0,
    "cse aiml":             1,
    "cse ds":               2,
    "cse cybersecurity":    3,
    "cse business systems": 4,
    "cse robotics":         5,
    "cse iot":              6,
    "cse cps":              7,
    "it core":              8,
    "ece core":             9,
    "ecm":                  10,
    "ecse":                 10,
    "electrical":           11,
    "electrical vlsi":      11,
    "mechatronics":         12,
    "mechanical":           13,
    "mechanical ev":        13,
    "civil":                14,
    "chemical":             15,
    "biotechnology":        16,
}

BRANCH_SCORE_WEIGHT = 3


def get_branch_priority(branch):
    return BRANCH_PRIORITY_MAP.get(str(branch).lower(), 99)


def get_branch_bonus(branch):
    priority = get_branch_priority(branch)
    if priority == 99:
        return -10
    max_priority = max(BRANCH_PRIORITY_MAP.values())
    return (max_priority - priority) * BRANCH_SCORE_WEIGHT


# =====================================================
# CAMPUS PRIORITY
# =====================================================

CAMPUS_TIERS = {
    "Vellore":   0,
    "Chennai":   1,
    "Amaravati": 3,
    "Ap":        3,
    "Bhopal":    5,
}

CAMPUS_BONUSES = {
    "Vellore":   10,
    "Chennai":    4,
    "Amaravati": -3,
    "Ap":        -3,
    "Bhopal":    -10,
}


def get_campus_tier(campus):
    return CAMPUS_TIERS.get(campus, 9)


def get_campus_priority(campus):
    return {"Vellore": 0, "Chennai": 1}.get(campus, 10)


def get_campus_bonus(campus):
    return CAMPUS_BONUSES.get(campus, -15)


# =====================================================
# FEE PRIORITY
# =====================================================

FEE_SCORE_WEIGHT = 2


def get_fee_priority(fee):
    try:
        return int(fee)
    except (TypeError, ValueError):
        return 99


def get_fee_bonus(fee):
    priority = get_fee_priority(fee)
    if priority == 99:
        return 0
    max_fee = 5
    return max(0, max_fee - priority) * FEE_SCORE_WEIGHT


# =====================================================
# RECOMMENDATION SCORE
# =====================================================

def calculate_recommendation_score(probability, responses, fee, campus, branch):
    branch_bonus     = get_branch_bonus(branch)
    campus_bonus     = get_campus_bonus(campus)
    fee_bonus        = get_fee_bonus(fee)
    confidence_bonus = min(responses, 20) * 0.35

    return round(
        probability + branch_bonus + campus_bonus + fee_bonus + confidence_bonus,
        2
    )


# =====================================================
# CHANCE PRIORITY (for sort order)
# =====================================================

def get_chance_priority(chance):
    return {"Dream": 0, "Moderate": 1, "Safe": 2, "Very Unlikely": 3}.get(chance, 9)


# =====================================================
# FEE-CATEGORY DOMINANCE FLAGGING
#
# For each (campus, branch) group, sort by fee ascending.
# Track the best probability seen so far among cheaper
# categories. If a more-expensive row has a LOWER
# probability than a cheaper one, it is "dominated":
#
#   → probability is overridden to match the dominant
#     (cheaper) option so it lands in the same chance
#     bucket, not a misleadingly lower one.
#   → data_insufficient = True  (UI shows a badge)
#   → dominant_fee records which cheaper cat dominates
#   → original_probability / original_closing_rank
#     are preserved so the UI can show them as a note.
#
# A row with HIGHER probability than all cheaper options
# is NOT dominated — it genuinely adds information.
# =====================================================

def flag_dominated_fee_categories(recommendations):
    """
    Mark dominated fee categories in-place; nothing is removed.

    A row is dominated when a cheaper fee category for the
    same (campus, branch) already achieves >= probability.
    Dominated rows get their probability/chance corrected to
    the dominant value and are flagged with data_insufficient=True.
    """
    from collections import defaultdict
    groups = defaultdict(list)
    for r in recommendations:
        groups[(r["campus"], r["branch"])].append(r)

    result = []
    for (campus, branch), rows in groups.items():
        # Sort cheapest first so we can do a single forward pass
        rows_by_fee = sorted(rows, key=lambda x: x["fee_priority"])

        best_prob = -1
        best_fee  = None

        for row in rows_by_fee:
            if row["probability"] >= best_prob:
                # Not dominated — this row is the new best for this campus+branch
                row["data_insufficient"]   = False
                row["dominant_fee"]        = None
                best_prob = row["probability"]
                best_fee  = row["fee"]
            else:
                # Dominated: a cheaper cat already beats this probability.
                # Store the original values for display, then override.
                row["data_insufficient"]      = True
                row["dominant_fee"]           = best_fee
                row["original_probability"]   = row["probability"]
                row["original_closing_rank"]  = row["closing_rank"]
                # Override so the card shows the same chance as the dominant cat
                row["probability"]            = best_prob
                row["chance"]                 = get_chance_category(best_prob)
                row["color"]                  = get_chance_color(row["chance"])
                row["emoji"]                  = get_emoji_for_probability(best_prob)
                row["recommendation_score"]   = calculate_recommendation_score(
                    best_prob, row["responses"], row["fee"], campus, branch
                )

            result.append(row)

    return result


# =====================================================
# MAIN RECOMMENDER
# =====================================================

def recommend(user_rank, sort_by="recommended"):
    """
    Generate ranked recommendations for a given VITEEE rank.
    Fee categories dominated by a cheaper option are shown
    with matched probability and flagged as data_insufficient.
    """
    recommendations = []

    for key, data in cutoffs.items():
        campus, branch, fee = key
        closing_rank = data["closing_rank"]
        responses    = data["responses"]

        probability          = calculate_probability(user_rank, closing_rank, responses)
        rank_difference      = closing_rank - user_rank
        chance               = get_chance_category(probability)
        confidence           = get_confidence(responses)
        confidence_pct       = get_confidence_percentage(responses)
        campus_tier          = get_campus_tier(campus)
        campus_priority      = get_campus_priority(campus)
        branch_priority      = get_branch_priority(branch)
        recommendation_score = calculate_recommendation_score(
            probability, responses, fee, campus, branch
        )

        recommendations.append({
            "campus":               campus,
            "branch":               branch,
            "fee":                  fee,
            "closing_rank":         closing_rank,
            "rank_difference":      rank_difference,
            "responses":            responses,
            "confidence":           confidence,
            "confidence_pct":       confidence_pct,
            "chance":               chance,
            "probability":          probability,
            "recommendation_score": recommendation_score,
            "fee_priority":         get_fee_priority(fee),
            "campus_tier":          campus_tier,
            "campus_priority":      campus_priority,
            "branch_priority":      branch_priority,
            "emoji":                get_emoji_for_probability(probability),
            "color":                get_chance_color(chance),
            # defaults — overwritten by flag_dominated_fee_categories
            "data_insufficient":    False,
            "dominant_fee":         None,
        })

    # ── Flag dominated fee categories ──────────────────────────────────────
    recommendations = flag_dominated_fee_categories(recommendations)

    # ── Sort keys ──────────────────────────────────────────────────────────
    sort_keys = {
        "recommended": lambda x: (
            x["campus_tier"],
            get_chance_priority(x["chance"]),
            x["fee_priority"],
            x["branch_priority"],
            x["campus_priority"],
            -x["probability"],
            -x["responses"],
            -x["recommendation_score"],
            x["branch"],
        ),
        "probability": lambda x: (
            x["campus_tier"],
            -x["probability"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["responses"],
        ),
        "probability_asc": lambda x: (
            x["campus_tier"],
            x["probability"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["responses"],
        ),
        "confidence": lambda x: (
            x["campus_tier"],
            -x["confidence_pct"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        "responses": lambda x: (
            x["campus_tier"],
            -x["responses"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        "closing_rank": lambda x: (
            x["campus_tier"],
            -x["closing_rank"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        "fee": lambda x: (
            x["fee_priority"],
            x["campus_tier"],
            x["branch_priority"],
            x["campus_priority"],
            -x["probability"],
            -x["responses"],
        ),
    }

    recommendations.sort(key=sort_keys.get(sort_by, sort_keys["recommended"]))
    return recommendations


# =====================================================
# HELPERS
# =====================================================

def get_recommendations_by_category(recommendations):
    MAX_RESULTS = 20
    return {
        "Safe":          [r for r in recommendations if r["chance"] == "Safe"][:MAX_RESULTS],
        "Moderate":      [r for r in recommendations if r["chance"] == "Moderate"][:MAX_RESULTS],
        "Dream":         [r for r in recommendations if r["chance"] == "Dream"][:MAX_RESULTS],
        "Very Unlikely": [r for r in recommendations if r["chance"] == "Very Unlikely"][:MAX_RESULTS],
    }


def get_rank_statistics(user_rank):
    all_closing_ranks = [data["closing_rank"] for data in cutoffs.values()]
    better = len([r for r in all_closing_ranks if r > user_rank])
    worse  = len([r for r in all_closing_ranks if r < user_rank])
    total  = len(all_closing_ranks)
    return {
        "total_options":  total,
        "better_options": better,
        "worse_options":  worse,
        "percentile":     round((worse / total * 100) if total > 0 else 0, 1),
    }