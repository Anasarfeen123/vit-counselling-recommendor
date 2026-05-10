from load_data import master_df
import statistics
import math

# =====================================================
# BUILD CUTOFF DATABASE (PERCENTILE-BASED)
# Replaces naive max() with 90th-percentile closing rank
# so a single outlier doesn't inflate the cutoff.
# We also store std_dev so the probability function can
# penalise uncertain options properly.
# =====================================================

def build_cutoffs(df):
    cutoffs = {}
    for (campus, branch, fee), group in df.groupby(["Campus", "Branch", "Fee"]):
        ranks = sorted(group["Rank"].tolist())
        n = len(ranks)

        # 90th-percentile closing rank (robust to outliers)
        p90_idx = min(int(math.ceil(0.90 * n)) - 1, n - 1)
        closing_rank = ranks[p90_idx]

        # True maximum (for display purposes)
        true_max = ranks[-1]

        # Spread of observed ranks
        std_dev = statistics.stdev(ranks) if n >= 2 else 0

        cutoffs[(campus, branch, fee)] = {
            "closing_rank": closing_rank,
            "true_max": true_max,
            "std_dev": std_dev,
            "responses": n,
            "min_rank": ranks[0],
            "median_rank": statistics.median(ranks),
        }
    return cutoffs


cutoffs = build_cutoffs(master_df)


# =====================================================
# CONFIDENCE
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
    return 20


# =====================================================
# PROBABILITY (IMPROVED)
# Uses:
#   1. Rank buffer as fraction of closing rank (scale-invariant)
#   2. Standard deviation penalty (high spread = more uncertainty)
#   3. Small confidence penalty for thin data
# =====================================================

def calculate_probability(user_rank, closing_rank, responses, std_dev=0):
    """
    Calculate probability of getting a seat.

    Args:
        user_rank:     Student's VITEEE rank
        closing_rank:  90th-percentile closing rank for this option
        responses:     Number of data points
        std_dev:       Standard deviation of observed ranks

    Returns:
        Probability percentage (0-100)
    """
    rank_buffer = closing_rank - user_rank
    buffer_ratio = rank_buffer / closing_rank if closing_rank else -1

    # ── Base probability from rank buffer ──────────────────────
    if rank_buffer >= 0:
        if rank_buffer >= 20000 or buffer_ratio >= 0.60:
            base_prob = 92
        elif rank_buffer >= 10000 or buffer_ratio >= 0.40:
            base_prob = 85
        elif rank_buffer >= 5000 or buffer_ratio >= 0.22:
            base_prob = 76
        elif rank_buffer >= 2000 or buffer_ratio >= 0.10:
            base_prob = 64
        elif rank_buffer >= 800 or buffer_ratio >= 0.04:
            base_prob = 54
        elif rank_buffer >= 200 or buffer_ratio >= 0.01:
            base_prob = 44
        else:
            base_prob = 38          # very slim positive buffer
    elif rank_buffer >= -500:
        base_prob = 30
    elif rank_buffer >= -2000:
        base_prob = 20
    elif rank_buffer >= -5000:
        base_prob = 12
    else:
        base_prob = 6

    # ── Standard-deviation penalty ─────────────────────────────
    # High spread means the cutoff swings a lot year-to-year.
    # Normalise SD relative to closing rank so a 1000-rank SD on
    # a 50k program is treated differently from the same SD on
    # a 5k program.
    if closing_rank > 0 and std_dev > 0:
        cv = std_dev / closing_rank          # coefficient of variation
        if cv >= 0.25:
            sd_penalty = 14
        elif cv >= 0.15:
            sd_penalty = 9
        elif cv >= 0.08:
            sd_penalty = 5
        elif cv >= 0.04:
            sd_penalty = 2
        else:
            sd_penalty = 0
        # Cap penalty for already-very-safe options
        if rank_buffer >= 10000 or buffer_ratio >= 0.40:
            sd_penalty = min(sd_penalty, 4)
    else:
        sd_penalty = 0

    # ── Thin-data penalty ──────────────────────────────────────
    if responses >= 12:
        data_penalty = 0
    elif responses >= 6:
        data_penalty = 2
    elif responses >= 3:
        data_penalty = 5
    elif responses == 2:
        data_penalty = 8
    else:
        data_penalty = 11

    # Large buffers stay safe regardless of sample size
    if rank_buffer >= 8000 or buffer_ratio >= 0.35:
        data_penalty = min(data_penalty, 3)

    probability = max(2, min(97, base_prob - sd_penalty - data_penalty))
    return round(probability, 1)


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
    return "Very Unlikely"


def get_chance_color(chance):
    colors = {
        "Safe": "#10b981",
        "Moderate": "#f59e0b",
        "Dream": "#ef4444",
        "Very Unlikely": "#6b7280",
    }
    return colors.get(chance, "#95a5a6")


def get_emoji_for_probability(probability):
    if probability >= 85:
        return "✅"
    elif probability >= 70:
        return "👍"
    elif probability >= 50:
        return "⚡"
    elif probability >= 25:
        return "🔥"
    return "💭"


# =====================================================
# RECOMMENDATION SCORING
# =====================================================

def get_fee_priority(fee):
    try:
        return int(fee)
    except (TypeError, ValueError):
        return 99


def get_campus_priority(campus):
    # Keys must match normalize_campus() output — "Amaravati", not "Ap"
    priorities = {"Vellore": 0, "Chennai": 1, "Amaravati": 10, "Bhopal": 20}
    return priorities.get(campus, 99)


def get_campus_tier(campus):
    # Keys must match normalize_campus() output — "Amaravati", not "Ap"
    tiers = {"Vellore": 0, "Chennai": 0, "Amaravati": 1, "Bhopal": 2}
    return tiers.get(campus, 9)


def get_campus_bonus(campus):
    # Keys must match normalize_campus() output — "Amaravati", not "Ap"
    bonuses = {"Vellore": 8, "Chennai": 7, "Amaravati": -4, "Bhopal": -12}
    return bonuses.get(campus, -16)


def get_branch_priority(branch):
    branch_key = str(branch).lower()
    if branch_key == "cse core":
        return 0
    if "cse" in branch_key or branch_key in {"csbs"}:
        return 1
    if branch_key in {"it", "it core", "ece core", "ecm", "ecse"}:
        return 2
    return 3


def calculate_recommendation_score(probability, responses, fee, campus, branch):
    fee_priority = get_fee_priority(fee)
    campus_bonus = get_campus_bonus(campus)
    branch_bonus = max(0, 4 - get_branch_priority(branch)) * 4
    affordability_bonus = max(0, 6 - fee_priority) * 4
    confidence_bonus = min(responses, 20) * 0.35
    return round(probability + campus_bonus + branch_bonus + affordability_bonus + confidence_bonus, 2)


def get_chance_priority(chance):
    priorities = {"Safe": 0, "Moderate": 1, "Dream": 2, "Very Unlikely": 3}
    return priorities.get(chance, 9)


# =====================================================
# MAIN RECOMMENDER
# =====================================================

def recommend(user_rank, sort_by="recommended"):
    recommendations = []

    for key, data in cutoffs.items():
        campus, branch, fee = key
        closing_rank = data["closing_rank"]
        responses = data["responses"]
        std_dev = data["std_dev"]
        true_max = data["true_max"]

        probability = calculate_probability(user_rank, closing_rank, responses, std_dev)
        rank_difference = closing_rank - user_rank

        chance = get_chance_category(probability)
        confidence = get_confidence(responses)
        confidence_pct = get_confidence_percentage(responses)
        campus_tier = get_campus_tier(campus)
        campus_priority = get_campus_priority(campus)
        branch_priority = get_branch_priority(branch)
        recommendation_score = calculate_recommendation_score(
            probability, responses, fee, campus, branch
        )

        recommendations.append({
            "campus": campus,
            "branch": branch,
            "fee": fee,
            "closing_rank": closing_rank,
            "true_max": true_max,
            "std_dev": round(std_dev),
            "rank_difference": rank_difference,
            "responses": responses,
            "confidence": confidence,
            "confidence_pct": confidence_pct,
            "chance": chance,
            "probability": probability,
            "recommendation_score": recommendation_score,
            "fee_priority": get_fee_priority(fee),
            "campus_tier": campus_tier,
            "campus_priority": campus_priority,
            "branch_priority": branch_priority,
            "emoji": get_emoji_for_probability(probability),
            "color": get_chance_color(chance),
        })

    sort_keys = {
        "recommended": lambda x: (
            get_chance_priority(x["chance"]),
            x["campus_tier"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
            -x["responses"],
            -x["recommendation_score"],
            x["branch"],
        ),
        "probability": lambda x: (
            -x["probability"], x["campus_tier"], x["branch_priority"],
            x["fee_priority"], x["campus_priority"], -x["responses"]
        ),
        "confidence": lambda x: (
            -x["confidence_pct"], x["campus_tier"], x["branch_priority"],
            x["fee_priority"], x["campus_priority"], -x["probability"]
        ),
        "responses": lambda x: (
            -x["responses"], x["campus_tier"], x["branch_priority"],
            x["fee_priority"], x["campus_priority"], -x["probability"]
        ),
        "closing_rank": lambda x: (
            -x["closing_rank"], x["campus_tier"], x["branch_priority"],
            x["fee_priority"], x["campus_priority"], -x["probability"]
        ),
        "fee": lambda x: (
            x["fee_priority"], x["campus_tier"], x["branch_priority"],
            x["campus_priority"], -x["probability"], -x["responses"]
        ),
    }

    recommendations.sort(key=sort_keys.get(sort_by, sort_keys["recommended"]))
    return recommendations


def get_recommendations_by_category(recommendations):
    return {
        "Safe": [r for r in recommendations if r["chance"] == "Safe"],
        "Moderate": [r for r in recommendations if r["chance"] == "Moderate"],
        "Dream": [r for r in recommendations if r["chance"] == "Dream"],
        "Very Unlikely": [r for r in recommendations if r["chance"] == "Very Unlikely"],
    }


def get_rank_statistics(user_rank):
    all_closing_ranks = [data["closing_rank"] for data in cutoffs.values()]
    better_ranks = len([r for r in all_closing_ranks if r > user_rank])
    worse_ranks = len([r for r in all_closing_ranks if r < user_rank])
    total_ranks = len(all_closing_ranks)
    return {
        "total_options": total_ranks,
        "better_options": better_ranks,
        "worse_options": worse_ranks,
        "percentile": round((worse_ranks / total_ranks * 100) if total_ranks > 0 else 0, 1),
    }