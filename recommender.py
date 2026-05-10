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
        uncertainty_penalty = 7

    # Large buffer stays safe even with small sample
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
# Reflects real-world preference and placement value:
#   CSE Core > AIML > DS > Cybersecurity > Business Systems
#   > Robotics > IoT > CPS > IT > ECE > ECM > others
# Lower number = higher priority (better branch)
# =====================================================

BRANCH_PRIORITY_MAP = {
    # ── CSE family ──────────────────────────────────
    "cse core":             0,
    "cse aiml":             1,
    "cse ds":               2,
    "cse cybersecurity":    3,
    "cse business systems": 4,
    "cse robotics":         5,
    "cse iot":              6,
    "cse cps":              7,

    # ── IT ──────────────────────────────────────────
    "it core":              8,

    # ── ECE family ──────────────────────────────────
    "ece core":             9,
    "ecm":                  10,
    "ecse":                 10,

    # ── EEE ─────────────────────────────────────────
    "electrical":           11,
    "electrical vlsi":      11,

    # ── Mechanical family ───────────────────────────
    "mechatronics":         12,
    "mechanical":           13,
    "mechanical ev":        13,

    # ── Others ──────────────────────────────────────
    "civil":                14,
    "chemical":             15,
    "biotechnology":        16,
}

# How many score points a branch priority step is worth.
# Keeps branch preference meaningful without completely overriding probability.
BRANCH_SCORE_WEIGHT = 3   # points per priority step


def get_branch_priority(branch):
    """Return numeric priority (lower = better). Unknown branches go last."""
    return BRANCH_PRIORITY_MAP.get(str(branch).lower(), 99)


def get_branch_bonus(branch):
    """
    Score bonus based on branch desirability.
    CSE Core gets the full 48 pts, each step down loses BRANCH_SCORE_WEIGHT.
    """
    priority = get_branch_priority(branch)
    if priority == 99:
        return -10   # unknown / niche branch
    max_priority = max(BRANCH_PRIORITY_MAP.values())  # 16
    return (max_priority - priority) * BRANCH_SCORE_WEIGHT


# =====================================================
# CAMPUS PRIORITY
# Vellore and Chennai are Tier-0 (roughly equal).
# AP and Bhopal are deprioritised.
# =====================================================

CAMPUS_TIERS = {
    "Vellore":   0,
    "Chennai":   0,
    "Amaravati": 1,
    "Ap":        1,
    "Bhopal":    2,
}

CAMPUS_BONUSES = {
    "Vellore":   6,
    "Chennai":   5,
    "Amaravati": -3,
    "Ap":        -3,
    "Bhopal":    -10,
}


def get_campus_tier(campus):
    return CAMPUS_TIERS.get(campus, 9)


def get_campus_priority(campus):
    """Tiebreaker within same tier: Vellore slightly ahead of Chennai."""
    return {"Vellore": 0, "Chennai": 1}.get(campus, 10)


def get_campus_bonus(campus):
    return CAMPUS_BONUSES.get(campus, -15)


# =====================================================
# FEE PRIORITY
# Lower fee category = cheaper = better by default.
# BUT: the scoring weight is kept small so a much
# better branch can still outrank a lower-fee option.
# =====================================================

FEE_SCORE_WEIGHT = 2   # points per category step saved

def get_fee_priority(fee):
    try:
        return int(fee)
    except (TypeError, ValueError):
        return 99


def get_fee_bonus(fee):
    """
    Cheap fee gives a small bonus.
    Cat 1 → +8 pts, Cat 5 → 0 pts.
    Deliberately smaller than branch bonus so
    "Cat 3 Core" can still beat "Cat 1 IoT".
    """
    priority = get_fee_priority(fee)
    if priority == 99:
        return 0
    max_fee = 5
    return max(0, max_fee - priority) * FEE_SCORE_WEIGHT


# =====================================================
# RECOMMENDATION SCORE
#
# Formula (all additive):
#   probability          (0–98,  primary driver)
#   + branch_bonus       (0–48,  prestige/placement)
#   + campus_bonus       (-15–6, campus quality)
#   + fee_bonus          (0–8,   affordability nudge)
#   + confidence_bonus   (0–7,   data quality nudge)
#
# Branch weight > fee weight means:
#   CSE Core Cat-3 will usually beat CSE IoT Cat-1
#   when probability is similar.
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
    return {"Safe": 0, "Moderate": 1, "Dream": 2, "Very Unlikely": 3}.get(chance, 9)


# =====================================================
# MAIN RECOMMENDER
# =====================================================

def recommend(user_rank, sort_by="recommended"):
    """
    Generate ranked recommendations for a given VITEEE rank.

    Default "recommended" sort:
      1. Chance category (Safe → Moderate → Dream → Unlikely)
      2. Campus tier
      3. Branch priority  ← AIML before IoT, etc.
      4. Fee priority     ← cheaper preferred when branch is equal
      5. Campus tiebreaker (Vellore > Chennai within same tier)
      6. Probability descending
      7. Responses descending (more data = more reliable)
      8. Recommendation score descending
      9. Branch name (alphabetic stability)
    """
    recommendations = []

    for key, data in cutoffs.items():
        campus, branch, fee = key
        closing_rank = data["closing_rank"]
        responses    = data["responses"]

        probability         = calculate_probability(user_rank, closing_rank, responses)
        rank_difference     = closing_rank - user_rank
        chance              = get_chance_category(probability)
        confidence          = get_confidence(responses)
        confidence_pct      = get_confidence_percentage(responses)
        campus_tier         = get_campus_tier(campus)
        campus_priority     = get_campus_priority(campus)
        branch_priority     = get_branch_priority(branch)
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
        })

    # ── Sort keys ──────────────────────────────────────────────────────────

    sort_keys = {
        "recommended": lambda x: (
            get_chance_priority(x["chance"]),   # Safe first
            x["campus_tier"],                   # Vellore/Chennai before AP/Bhopal
            x["branch_priority"],               # CSE Core > AIML > IoT etc.
            x["fee_priority"],                  # cheaper when branch is equal
            x["campus_priority"],               # Vellore > Chennai tiebreak
            -x["probability"],                  # higher prob first
            -x["responses"],                    # more data first
            -x["recommendation_score"],
            x["branch"],                        # alphabetic stability
        ),
        "probability": lambda x: (
            -x["probability"],
            x["campus_tier"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["responses"],
        ),
        "confidence": lambda x: (
            -x["confidence_pct"],
            x["campus_tier"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        "responses": lambda x: (
            -x["responses"],
            x["campus_tier"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        "closing_rank": lambda x: (
            -x["closing_rank"],
            x["campus_tier"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        "fee": lambda x: (
            x["fee_priority"],          # cheapest first
            x["campus_tier"],
            x["branch_priority"],       # within same fee, better branch first
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
    return {
        "Safe":          [r for r in recommendations if r["chance"] == "Safe"],
        "Moderate":      [r for r in recommendations if r["chance"] == "Moderate"],
        "Dream":         [r for r in recommendations if r["chance"] == "Dream"],
        "Very Unlikely": [r for r in recommendations if r["chance"] == "Very Unlikely"],
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