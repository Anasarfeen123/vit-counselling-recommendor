import pandas as pd

file = "VIT Counselling Data ( 2025 ).xlsx"

df = pd.read_excel(file)

# Remove fully empty rows
df = df.dropna(how="all")

# Remove fully empty columns
df = df.dropna(axis=1, how="all")

# Rename columns properly
df.columns = ["Rank", "Campus", "Branch", "Fee"]

# Remove rows with missing values
df = df.dropna()

# Convert rank/fee to int
df["Rank"] = df["Rank"].astype(int)
df["Fee"] = df["Fee"].astype(int)

# print(df.head())

cutoffs = {}

for _, row in df.iterrows():
    key = (row["Campus"], row["Branch"], row["Fee"])

    rank = row["Rank"]

    # store maximum rank (closing rank)
    if key not in cutoffs:
        cutoffs[key] = rank

    else:
        cutoffs[key] = max(cutoffs[key], rank)

if __name__ == "__main__":
    for key, cutoff in cutoffs.items():
        print(f"{key}: {cutoff}")
