from load_data import cutoffs
import statistics

# cutoffs is a dict keyed by (campus, branch, fee) — built in load_data.py
# from the historical Excel + live Google Form responses merged together


# how confident are we in the data for a given branch/campus/fee combo?
# basically just bucketing by how many people submitted data for it
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


# same idea but returns a number (0-100) so the UI can draw a progress bar
# interpolates between breakpoints instead of hard steps — so going from
# 5 to 6 responses doesn't cause a sudden 20pt jump on the bar
def get_confidence_percentage(responses):
    # each tuple is (min_responses, percentage_at_that_point)
    breakpoints = [(0, 20), (3, 40), (6, 60), (12, 75), (20, 85), (30, 95)]

    # find which two breakpoints we're between and lerp
    for i in range(len(breakpoints) - 1):
        lo_r, lo_pct = breakpoints[i]
        hi_r, hi_pct = breakpoints[i + 1]
        if responses <= hi_r:
            if hi_r == lo_r:
                return lo_pct
            t = (responses - lo_r) / (hi_r - lo_r)
            return round(lo_pct + t * (hi_pct - lo_pct), 1)

    return 95   # capped at 95 — we never claim 100% confidence


def calculate_probability(user_rank, closing_rank, responses, std_dev=0):
    # closing_rank here is the 90th-percentile rank from historical data,
    # not the actual max — so one outlier doesn't tank everyone else's prob

    rank_buffer = closing_rank - user_rank
    # positive = user is better than the cutoff (good)
    # negative = user is worse than the cutoff (bad)

    # buffer_ratio lets us handle absolute and relative rank gaps consistently.
    # a rank_buffer of 5000 means a lot more for a 10k cutoff than for a 100k cutoff
    buffer_ratio = rank_buffer / closing_rank if closing_rank else -1

    if rank_buffer >= 0:
        # user is inside the cutoff — figure out how comfortable the margin is
        if rank_buffer >= 25000 or buffer_ratio >= 0.65:
            base_prob = 94   # massive cushion, almost certain
        elif rank_buffer >= 10000 or buffer_ratio >= 0.45:
            base_prob = 88
        elif rank_buffer >= 5000 or buffer_ratio >= 0.25:
            base_prob = 80
        elif rank_buffer >= 2000 or buffer_ratio >= 0.12:
            base_prob = 70
        elif rank_buffer >= 500 or buffer_ratio >= 0.04:
            base_prob = 58   # inside but barely
        else:
            base_prob = 46   # right on the edge — could go either way
    elif rank_buffer >= -500:
        base_prob = 35   # just missed the cutoff, still worth listing as backup
    elif rank_buffer >= -2000:
        base_prob = 25
    elif rank_buffer >= -5000:
        base_prob = 15
    else:
        base_prob = 8    # way outside, not realistic

    # less data = less reliable cutoff = knock the probability down a bit
    # this penalty is small on purpose — rank buffer still drives the number
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

    # if the rank buffer is already very safe, cap the penalty — don't punish
    # a clear safe pick just because not many people submitted data for it
    if rank_buffer >= 5000 or buffer_ratio >= 0.25:
        uncertainty_penalty = min(uncertainty_penalty, 3)

    # std_dev penalty — if a branch has had wildly different cutoffs across years,
    # the cutoff we have is less trustworthy, so we shave the probability a bit.
    # volatility is the std_dev as a fraction of the closing rank, so it scales
    # correctly regardless of whether the cutoff is 5k or 80k.
    # max penalty is 6 points — enough to notice but won't flip a Safe to a Dream.
    volatility = std_dev / closing_rank if closing_rank else 0
    if volatility >= 0.35:
        base_prob -= 6
    elif volatility >= 0.20:
        base_prob -= 4
    elif volatility >= 0.10:
        base_prob -= 2
    # under 0.10 = pretty stable, no penalty

    return round(max(1, min(98, base_prob - uncertainty_penalty)), 1)


# buckets the probability into a human-readable category shown in the UI
def get_chance_category(probability):
    if probability >= 75:
        return "Safe"
    elif probability >= 40:
        return "Moderate"
    elif probability >= 15:
        return "Dream"
    else:
        return "Very Unlikely"


# hex colors for each category — matched to the CSS variables in app.py
def get_chance_color(chance):
    return {
        "Safe": "#10b981",
        "Moderate": "#f59e0b",
        "Dream": "#ef4444",
        "Very Unlikely": "#6b7280",
    }.get(chance, "#95a5a6")


# emoji shown next to the probability number on each result card
def get_emoji_for_probability(probability):
    if probability >= 85: return "✅"
    elif probability >= 70: return "👍"
    elif probability >= 50: return "⚡"
    elif probability >= 25: return "🔥"
    else: return "💭"


# branch ordering — lower number = higher demand / more competitive
# this order was decided based on general VIT counselling trends, not hardcoded rules
# changing this will affect how results are sorted in "Recommended" mode
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

# multiplier applied when converting priority rank → bonus score
# kept intentionally small so branch preference doesn't override probability
BRANCH_SCORE_WEIGHT = 3


def get_branch_priority(branch):
    # returns 99 for anything not in the map (unknown branch)
    return BRANCH_PRIORITY_MAP.get(str(branch).lower(), 99)


def get_branch_bonus(branch):
    priority = get_branch_priority(branch)
    if priority == 99:
        return -10   # unknown branch gets penalised in scoring

    # flip the priority so lower priority number = higher bonus
    # e.g. CSE Core (priority 0) gets max bonus, Biotech gets 0
    max_priority = max(BRANCH_PRIORITY_MAP.values())
    return (max_priority - priority) * BRANCH_SCORE_WEIGHT


# campus tiers used for sorting — Vellore first, Bhopal last
# separate from campus_bonus because sort and score are different things
CAMPUS_TIERS = {
    "Vellore":   0,
    "Chennai":   1,
    "Amaravati": 3,
    "Ap":        3,    # Ap and Amaravati are the same campus
    "Bhopal":    5,
}

# additive bonuses added to the recommendation score
# these reflect general student preference, not any official ranking
CAMPUS_BONUSES = {
    "Vellore":   10,
    "Chennai":    4,
    "Amaravati": -3,
    "Ap":        -3,
    "Bhopal":    -10,
}


def get_campus_tier(campus):
    return CAMPUS_TIERS.get(campus, 9)   # 9 = unknown campus, sorts to bottom


def get_campus_priority(campus):
    # used as a tiebreaker in the sort — only Vellore/Chennai get preferential treatment
    return {"Vellore": 0, "Chennai": 1}.get(campus, 10)


def get_campus_bonus(campus):
    return CAMPUS_BONUSES.get(campus, -15)   # -15 for anything not in the map


# fee categories are integers 1–5, lower = cheaper
# so fee_priority is just the fee number itself — lower number sorts first
FEE_SCORE_WEIGHT = 2


def get_fee_priority(fee):
    try:
        return int(fee)
    except (TypeError, ValueError):
        return 99   # garbage value in data, push to the end


def get_fee_bonus(fee):
    priority = get_fee_priority(fee)
    if priority == 99:
        return 0    # don't penalise, just don't reward

    # cheaper fee = higher bonus, so category 1 gets the most
    max_fee = 5
    return max(0, max_fee - priority) * FEE_SCORE_WEIGHT


# combines probability with branch/campus/fee preferences into one number.
# the key fix here is scaling the bonuses down so probability stays dominant.
# old version just added raw bonuses, so branch_bonus (up to 48) could easily
# swamp the probability signal and push low-prob CSE above high-prob ECE.
# now bonuses are dampened — they break ties but can't flip rankings.
def calculate_recommendation_score(probability, responses, fee, campus, branch):
    branch_bonus = get_branch_bonus(branch)
    campus_bonus = get_campus_bonus(campus)
    fee_bonus    = get_fee_bonus(fee)

    # small nudge for options with more data — not enough to flip rankings,
    # just enough to break ties between equally probable options
    confidence_bonus = min(responses, 20) * 0.35

    # branch and campus bonuses are scaled down by 0.3 / 0.5 so they
    # inform the score without overriding it — probability is still king
    return round(
        probability
        + (branch_bonus * 0.3)
        + (campus_bonus * 0.5)
        + fee_bonus
        + confidence_bonus,
        2
    )


# maps chance category to a sort integer so Dream shows up before Safe
# (we deliberately show riskier options first — they're more interesting)
def get_chance_priority(chance):
    return {"Dream": 0, "Moderate": 1, "Safe": 2, "Very Unlikely": 3}.get(chance, 9)


def flag_dominated_fee_categories(recommendations):
    # Higher fee categories should have cutoffs that are at least as high as
    # lower fee categories for the same campus+branch. Example: Cat 4 should
    # not have a lower cutoff rank than Cat 3. If that happens, both sides are
    # marked as a data issue because we cannot safely know which cutoff is bad.
    # Nothing gets deleted or overwritten; the UI shows the warning in context.

    from collections import defaultdict
    groups = defaultdict(list)
    for r in recommendations:
        groups[(r["campus"], r["branch"])].append(r)

    result = []
    for (campus, branch), rows in groups.items():
        rows_by_fee = sorted(rows, key=lambda x: x["fee_priority"])

        for row in rows_by_fee:
            row["data_insufficient"] = False
            row["dominant_fee"] = None
            row["data_issue_type"] = None
            row["category_cutoff_issues"] = []

        previous_rows = []

        for row in rows_by_fee:
            cutoff = row["closing_rank"]
            conflicting_lower_rows = [
                lower_row
                for lower_row in previous_rows
                if lower_row["closing_rank"] > cutoff
            ]

            if conflicting_lower_rows:
                row["data_insufficient"] = True
                row["data_issue_type"] = "category_cutoff_order"

            for lower_row in conflicting_lower_rows:
                lower_row["data_insufficient"] = True
                lower_row["data_issue_type"] = "category_cutoff_order"

                lower_issue = {
                    "fee": row["fee"],
                    "cutoff": cutoff,
                    "relationship": "higher",
                }
                higher_issue = {
                    "fee": lower_row["fee"],
                    "cutoff": lower_row["closing_rank"],
                    "relationship": "lower",
                }

                if lower_issue not in lower_row["category_cutoff_issues"]:
                    lower_row["category_cutoff_issues"].append(lower_issue)
                if higher_issue not in row["category_cutoff_issues"]:
                    row["category_cutoff_issues"].append(higher_issue)

            previous_rows.append(row)

        for row in rows_by_fee:
            if row.get("category_cutoff_issues"):
                row["category_cutoff_issues"].sort(
                    key=lambda issue: get_fee_priority(issue["fee"])
                )
            result.append(row)

    return result


def recommend(user_rank, sort_by="recommended"):
    # main entry point — takes a rank and returns a sorted list of dicts,
    # one per (campus, branch, fee) combination we have data for

    recommendations = []

    for key, data in cutoffs.items():
        campus, branch, fee = key
        closing_rank = data["closing_rank"]
        true_max     = data.get("true_max", closing_rank)   # actual max rank seen in data
        std_dev      = data.get("std_dev", 0)               # spread of historical ranks
        responses    = data["responses"]

        # pass std_dev in so the volatility penalty kicks in
        probability          = calculate_probability(user_rank, closing_rank, responses, std_dev)
        rank_difference      = closing_rank - user_rank      # positive = user has cushion
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
            "true_max":             true_max,
            "std_dev":              std_dev,
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
            # these two get overwritten by flag_dominated_fee_categories below
            "data_insufficient":    False,
            "dominant_fee":         None,
        })

    # fix fee-category inconsistencies before sorting
    recommendations = flag_dominated_fee_categories(recommendations)

    # each sort key is a tuple — Python sorts tuples left-to-right,
    # so the first element has highest priority, last is just a tiebreaker
    sort_keys = {
        # "recommended" tries to balance all factors: campus > chance bucket > fee > branch > prob
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
        # pure probability sort — still groups by campus first
        "probability": lambda x: (
            x["campus_tier"],
            -x["probability"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["responses"],
        ),
        # ascending probability — useful for seeing riskier options first
        "probability_asc": lambda x: (
            x["campus_tier"],
            x["probability"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["responses"],
        ),
        # sort by how trustworthy the data is (number of responses)
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
        # sort by the raw cutoff rank value (higher cutoff = more competitive)
        "closing_rank": lambda x: (
            x["campus_tier"],
            -x["closing_rank"],
            x["branch_priority"],
            x["fee_priority"],
            x["campus_priority"],
            -x["probability"],
        ),
        # sort cheapest fee first — ignores campus tier on purpose
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


# splits results into the four chance buckets — used by the UI tab view
# MAX_RESULTS caps how many show per section so the page doesn't get too long
def get_recommendations_by_category(recommendations):
    MAX_RESULTS = 20
    return {
        "Safe":          [r for r in recommendations if r["chance"] == "Safe"][:MAX_RESULTS],
        "Moderate":      [r for r in recommendations if r["chance"] == "Moderate"][:MAX_RESULTS],
        "Dream":         [r for r in recommendations if r["chance"] == "Dream"][:MAX_RESULTS],
        "Very Unlikely": [r for r in recommendations if r["chance"] == "Very Unlikely"][:MAX_RESULTS],
    }


# quick summary stats shown in the sidebar after running recommendations
def get_rank_statistics(user_rank):
    all_closing_ranks = [data["closing_rank"] for data in cutoffs.values()]
    better = len([r for r in all_closing_ranks if r > user_rank])   # cutoffs the user beats
    worse  = len([r for r in all_closing_ranks if r < user_rank])   # cutoffs the user misses
    total  = len(all_closing_ranks)
    return {
        "total_options":  total,
        "better_options": better,
        "worse_options":  worse,
        # what percentile is the user in relative to all observed cutoffs
        "percentile":     round((worse / total * 100) if total > 0 else 0, 1),
    }
