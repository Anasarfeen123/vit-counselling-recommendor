import streamlit as st
import gspread
import pandas as pd
import re

from oauth2client.service_account import (
    ServiceAccountCredentials
)

# =====================================================
# GOOGLE SHEETS CONNECTION
# =====================================================

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

# =====================================================
# TRY STREAMLIT SECRETS FIRST
# =====================================================

try:

    creds_dict = dict(
        st.secrets["gcp_service_account"]
    )

    creds = (
        ServiceAccountCredentials
        .from_json_keyfile_dict(
            creds_dict,
            scope
        )
    )

    print("✅ Using Streamlit secrets")

# =====================================================
# FALLBACK TO LOCAL credentials.json
# =====================================================

except Exception:

    creds = (
        ServiceAccountCredentials
        .from_json_keyfile_name(
            "credentials.json",
            scope
        )
    )

    print("✅ Using local credentials.json")

# =====================================================
# AUTHORIZE
# =====================================================

client = gspread.authorize(creds)

sheet = client.open_by_url(
    "https://docs.google.com/spreadsheets/d/1IOKcDcfUXporFN4VAqh6G1SYuGpCxZo5iCnraVePVsY/edit?usp=sharing"
).sheet1

# =====================================================
# LOAD LIVE GOOGLE FORM DATA
# =====================================================

live_data = sheet.get_all_records()

live_df = pd.DataFrame(live_data)

# =====================================================
# RENAME COLUMNS
# =====================================================

live_df = live_df.rename(
    columns={
        "VITEEE Rank": "Rank",
        "Campus": "Campus",
        "Branch": "Branch",
        "Fee Category": "Fee",
    }
)

# Keep only useful columns
live_df = live_df[
    [
        "Rank",
        "Campus",
        "Branch",
        "Fee"
    ]
]

# =====================================================
# CLEAN RANK
# =====================================================

live_df["Rank"] = pd.to_numeric(
    live_df["Rank"],
    errors="coerce"
)

# =====================================================
# CLEAN FEE CATEGORY
# =====================================================

live_df["Fee"] = (
    live_df["Fee"]
    .astype(str)
    .str.extract(r"(\d+)")
)

live_df["Fee"] = pd.to_numeric(
    live_df["Fee"],
    errors="coerce"
)

# Remove invalid rows
live_df = live_df.dropna()

# Convert to int
live_df["Rank"] = live_df["Rank"].astype(int)

live_df["Fee"] = live_df["Fee"].astype(int)

# =====================================================
# NORMALIZE BRANCHES
# =====================================================

def normalize_branch(branch):

    branch = str(branch).lower().strip()

    # Remove extra spaces
    branch = " ".join(branch.split())

    # Remove special chars
    branch_key = re.sub(
        r"[^a-z0-9]+",
        " ",
        branch
    )

    branch_key = " ".join(
        branch_key.split()
    )

    tokens = set(
        branch_key.split()
    )

    mapping = {

        # =================================================
        # CSE CORE
        # =================================================

        "cse": "CSE Core",
        "cs": "CSE Core",
        "core": "CSE Core",
        "cse core": "CSE Core",
        "cs core": "CSE Core",
        "csecore": "CSE Core",
        "b tech cse": "CSE Core",
        "btech cse": "CSE Core",
        "computer science": "CSE Core",
        "computer science engineering": "CSE Core",

        # =================================================
        # AIML
        # =================================================

        "cse aiml": "CSE AIML",
        "cse ai ml": "CSE AIML",
        "cse ai/ml": "CSE AIML",
        "cse ai & ml": "CSE AIML",
        "cse ai&ml": "CSE AIML",
        "aiml": "CSE AIML",
        "ai ml": "CSE AIML",
        "artificial intelligence and machine learning":
            "CSE AIML",

        # =================================================
        # DATA SCIENCE
        # =================================================

        "cse ds": "CSE DS",
        "cse data science": "CSE DS",
        "data science": "CSE DS",
        "ds": "CSE DS",

        # =================================================
        # CYBERSECURITY
        # =================================================

        "cse cybersecurity": "CSE Cybersecurity",
        "cybersecurity": "CSE Cybersecurity",
        "cse cyber": "CSE Cybersecurity",

        # =================================================
        # BUSINESS SYSTEMS
        # =================================================

        "cse business systems": "CSE Business Systems",
        "cse bs": "CSE Business Systems",

        # =================================================
        # ROBOTICS
        # =================================================

        "cse ai robo": "CSE Robotics",
        "robotics": "CSE Robotics",

        # =================================================
        # IOT
        # =================================================

        "cse iot": "CSE IoT",
        "iot": "CSE IoT",

        # =================================================
        # CPS
        # =================================================

        "cse cps": "CSE CPS",
        "cps": "CSE CPS",

        # =================================================
        # ECE
        # =================================================

        "ece": "ECE Core",
        "ece core": "ECE Core",
        "electronics and communication":
            "ECE Core",
        "ecm": "ECM",

        # =================================================
        # IT
        # =================================================

        "it": "IT Core",
        "it core": "IT Core",
        "information technology":
            "IT Core",

        # =================================================
        # MECHANICAL
        # =================================================

        "mechanical": "Mechanical",
        "me": "Mechanical",
        "mech": "Mechanical",
        "mechanical ev": "Mechanical EV",

        # =================================================
        # MECHATRONICS
        # =================================================

        "mechatronics": "Mechatronics",

        # =================================================
        # CIVIL
        # =================================================

        "civil": "Civil",
        "ce": "Civil",

        # =================================================
        # ELECTRICAL
        # =================================================

        "electrical": "Electrical",
        "eee": "Electrical",
        "ee": "Electrical",
        "ee vlsi design and technology":
            "Electrical VLSI",

        # =================================================
        # CHEMICAL
        # =================================================

        "chemical": "Chemical",

        # =================================================
        # BIOTECH
        # =================================================

        "biotechnology": "Biotechnology",
    }

    # Exact matches
    if branch in mapping:
        return mapping[branch]

    if branch_key in mapping:
        return mapping[branch_key]

    # Smart CSE detection
    cse_tokens = {
        "cse",
        "cs",
        "computer"
    }

    core_tokens = {
        "core",
        "science"
    }

    has_cse_signal = (
        bool(tokens & cse_tokens)
        or "computer science" in branch_key
    )

    has_core_signal = bool(
        tokens & core_tokens
    )

    if has_cse_signal and has_core_signal:
        return "CSE Core"

    return branch.title()


live_df["Branch"] = live_df[
    "Branch"
].apply(normalize_branch)

# =====================================================
# NORMALIZE CAMPUS
# =====================================================

def normalize_campus(campus):

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

    return mapping.get(
        campus,
        campus.title()
    )


live_df["Campus"] = live_df[
    "Campus"
].apply(normalize_campus)

# =====================================================
# VALIDATION
# =====================================================

def validate_fee_category(fee):

    if pd.isna(fee):
        return False

    fee_int = int(fee)

    return 1 <= fee_int <= 5


def validate_rank(rank):

    if pd.isna(rank):
        return False

    return 1 <= int(rank) <= 250000


live_df = live_df[
    live_df["Fee"].apply(
        validate_fee_category
    )
]

live_df = live_df[
    live_df["Rank"].apply(
        validate_rank
    )
]

# =====================================================
# LOAD HISTORICAL DATASET
# =====================================================

historical_df = pd.read_excel(
    "data/VIT Counselling Data ( 2025 ).xlsx"
)

historical_df.columns = [
    "Rank",
    "Campus",
    "Branch",
    "Fee"
]

historical_df = historical_df.dropna()

historical_df["Rank"] = (
    historical_df["Rank"]
    .astype(int)
)

historical_df["Fee"] = (
    historical_df["Fee"]
    .astype(int)
)

historical_df["Branch"] = (
    historical_df["Branch"]
    .apply(normalize_branch)
)

historical_df["Campus"] = (
    historical_df["Campus"]
    .apply(normalize_campus)
)

# =====================================================
# MERGE DATASETS
# =====================================================

master_df = pd.concat(
    [
        historical_df,
        live_df
    ],
    ignore_index=True
)

master_df = (
    master_df
    .drop_duplicates(
        subset=[
            "Rank",
            "Campus",
            "Branch",
            "Fee"
        ],
        keep="first"
    )
)

master_df = (
    master_df
    .sort_values(by="Rank")
    .reset_index(drop=True)
)

# =====================================================
# DATA QUALITY REPORT
# =====================================================

print(
    f"✅ Total records loaded: {len(master_df)}"
)

print(
    f"📊 Unique combinations: "
    f"{len(master_df[['Campus', 'Branch', 'Fee']].drop_duplicates())}"
)

print(
    f"🏫 Campuses: "
    f"{', '.join(sorted(master_df['Campus'].unique()))}"
)

print(
    f"📚 Branches: "
    f"{len(master_df['Branch'].unique())}"
)

# =====================================================
# GENERATE CUTOFF DATABASE
# =====================================================

cutoffs = {}

for _, row in master_df.iterrows():

    key = (
        row["Campus"],
        row["Branch"],
        row["Fee"]
    )

    rank = row["Rank"]

    if key not in cutoffs:

        cutoffs[key] = {

            "closing_rank": rank,

            "responses": 1
        }

    else:

        cutoffs[key]["closing_rank"] = max(
            cutoffs[key]["closing_rank"],
            rank
        )

        cutoffs[key]["responses"] += 1