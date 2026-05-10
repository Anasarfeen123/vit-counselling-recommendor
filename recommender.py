from load_data import cutoffs
import statistics

# =====================================================
# CONFIDENCE SCORE (IMPROVED)
# =====================================================


def get_confidence(responses):
    """Get confidence level based on number of responses - improved thresholds"""
    
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
    """Get confidence as percentage - improved calculation"""
    # Logarithmic scale for better accuracy
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
    Calculate probability of getting a seat.

    Rank buffer is the primary signal. Response count should describe how
    confident we are in the estimate, not crush an otherwise strong option.
    
    Args:
        user_rank: Student's rank
        closing_rank: Closing rank for that option
        responses: Number of data points
    
    Returns:
        Probability percentage (0-100)
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
        uncertainty_penalty = 4
    elif responses == 2:
        uncertainty_penalty = 6
    else:
        uncertainty_penalty = 8

    # A very large buffer should stay safe even if the sample size is tiny.
    if rank_buffer >= 5000 or buffer_ratio >= 0.25:
        uncertainty_penalty = min(uncertainty_penalty, 3)

    probability = max(1, min(98, base_prob - uncertainty_penalty))
    return round(probability, 1)


# =====================================================
# CHANCE CLASSIFICATION
# =====================================================

def get_chance_category(probability):
    """Classify chance based on probability"""
    if probability >= 75:
        return "Safe"
    elif probability >= 40:
        return "Moderate"
    elif probability >= 15:
        return "Dream"
    else:
        return "Very Unlikely"


def get_chance_color(chance):
    """Return color based on chance category"""
    colors = {
        "Safe": "#10b981",
        "Moderate": "#f59e0b",
        "Dream": "#ef4444",
        "Very Unlikely": "#6b7280",
    }
    return colors.get(chance, "#95a5a6")


def get_emoji_for_probability(probability):
    """Get emoji based on probability"""
    if probability >= 85:
        return "✅"
    elif probability >= 70:
        return "👍"
    elif probability >= 50:
        return "⚡"
    elif probability >= 25:
        return "🔥"
    else:
        return "💭"


# =====================================================
# RECOMMENDATION RANKING
# =====================================================

def get_fee_priority(fee):
    """Lower fee categories are better and should rank earlier."""
    try:
        return int(fee)
    except (TypeError, ValueError):
        return 99


def get_campus_priority(campus):
    """Small preference inside a campus tier."""
    priorities = {
        "Vellore": 0,
        "Chennai": 1,
        "Ap": 10,
        "Bhopal": 20,
    }
    return priorities.get(campus, 99)


def get_campus_tier(campus):
    """
    Campus desirability buckets.

    Vellore and Chennai are comparable, so fee/branch can reorder them.
    AP and Bhopal are intentionally pushed to lower tiers.
    """
    tiers = {
        "Vellore": 0,
        "Chennai": 0,
        "Ap": 1,
        "Bhopal": 2,
    }
    return tiers.get(campus, 9)


def get_campus_bonus(campus):
    """Score bonus used for display/ranking within close calls."""
    bonuses = {
        "Vellore": 8,
        "Chennai": 7,
        "Ap": -4,
        "Bhopal": -12,
    }
    return bonuses.get(campus, -16)


def get_branch_priority(branch):
    """Prefer CSE Core first, then other CSE-related branches."""
    branch_key = str(branch).lower()

    if branch_key == "cse core":
        return 0
    if branch_key in {"it", "ece", "ecm", "ecse"}:
        return 2
    if "cse" in branch_key or branch_key in {"csbs"}:
        return 1
    return 3


def calculate_recommendation_score(probability, responses, fee, campus, branch):
    """
    Balanced score for default ranking.

    Probability still matters most, but campus preference, CSE Core preference,
    and cheaper fee categories influence options that are close.
    """
    fee_priority = get_fee_priority(fee)
    campus_bonus = get_campus_bonus(campus)
    branch_bonus = max(0, 4 - get_branch_priority(branch)) * 4
    affordability_bonus = max(0, 6 - fee_priority) * 4
    confidence_bonus = min(responses, 20) * 0.35
    return round(probability + campus_bonus + branch_bonus + affordability_bonus + confidence_bonus, 2)


def get_chance_priority(chance):
    """Keep safer categories ahead when using the recommended sort."""
    priorities = {
        "Safe": 0,
        "Moderate": 1,
        "Dream": 2,
        "Very Unlikely": 3,
    }
    return priorities.get(chance, 9)


# =====================================================
# MAIN RECOMMENDER (IMPROVED)
# =====================================================


def recommend(user_rank, sort_by="recommended"):
    """
    Generate recommendations based on user rank using improved algorithm
    
    Args:
        user_rank: Student's VITEEE rank
        sort_by: How to sort results
            ("recommended", "probability", "confidence", "responses", "closing_rank", "fee")
    
    Returns:
        List of recommendation dictionaries sorted by specified criteria
    """

    recommendations = []

    for key, data in cutoffs.items():
        campus, branch, fee = key
        closing_rank = data["closing_rank"]
        responses = data["responses"]

        # =============================================
        # CALCULATE PROBABILITY & SCORE
        # =============================================

        probability = calculate_probability(user_rank, closing_rank, responses)
        rank_difference = closing_rank - user_rank
        
        chance = get_chance_category(probability)
        confidence = get_confidence(responses)
        confidence_pct = get_confidence_percentage(responses)
        campus_tier = get_campus_tier(campus)
        campus_priority = get_campus_priority(campus)
        branch_priority = get_branch_priority(branch)
        recommendation_score = calculate_recommendation_score(probability, responses, fee, campus, branch)
        
        # =============================================
        # SAVE RESULT
        # =============================================

        recommendations.append(
            {
                "campus": campus,
                "branch": branch,
                "fee": fee,
                "closing_rank": closing_rank,
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
            }
        )

    # =============================================
    # SORT RESULTS
    # =============================================

    def common_tiebreakers(x):
        return (
            x["campus_tier"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
            -x["responses"],
            x["campus"],
            x["branch"],
        )

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
        "probability": lambda x: (-x["probability"], x["campus_tier"], x["branch_priority"], x["fee_priority"], x["campus_priority"], -x["responses"]),
        "confidence": lambda x: (-x["confidence_pct"], x["campus_tier"], x["branch_priority"], x["fee_priority"], x["campus_priority"], -x["probability"]),
        "responses": lambda x: (-x["responses"], x["campus_tier"], x["branch_priority"], x["fee_priority"], x["campus_priority"], -x["probability"]),
        "closing_rank": lambda x: (-x["closing_rank"], x["campus_tier"], x["branch_priority"], x["fee_priority"], x["campus_priority"], -x["probability"]),
        "fee": lambda x: (x["fee_priority"], x["campus_tier"], x["branch_priority"], x["campus_priority"], -x["probability"], -x["responses"]),
    }

    recommendations.sort(key=sort_keys.get(sort_by, sort_keys["recommended"]))

    return recommendations


def get_recommendations_by_category(recommendations):
    """Group recommendations by chance category"""
    categorized = {
        "Safe": [r for r in recommendations if r["chance"] == "Safe"],
        "Moderate": [r for r in recommendations if r["chance"] == "Moderate"],
        "Dream": [r for r in recommendations if r["chance"] == "Dream"],
        "Very Unlikely": [r for r in recommendations if r["chance"] == "Very Unlikely"],
    }
    return categorized


def get_rank_statistics(user_rank):
    """Get statistics about rank relative to all closing ranks"""
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
