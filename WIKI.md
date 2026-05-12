# VIT Counselling Predictor Wiki

This wiki is for future maintainers who want to understand, run, update, and extend the VIT Counselling Predictor without rediscovering the whole system from scratch.

## 1. Mental Model

The project has four main layers:

```text
Data sources
  -> load_data.py
  -> recommender.py
  -> app.py / admin_app.py
  -> Supabase persistence through database.py
```

The public app reads merged data, computes cutoffs, and shows recommendations. The admin app manages the data behind those recommendations.

## 2. Main Files

### `app.py`

Public Streamlit app for students.

Responsibilities:

- Rank input and filters.
- Recommendation rendering.
- Chance categories.
- Report submission UI.
- Dataset analytics.
- Public theme and layout.

Touch this when changing the student-facing experience.

### `admin_app.py`

Admin Streamlit app.

Responsibilities:

- Password gate.
- Dashboard metrics.
- Record CRUD.
- Report management.
- Bulk import/export.
- Data Quality Center.
- Refresh controls.
- Admin styling.

Touch this when changing internal data workflows.

### `recommender.py`

Recommendation logic.

Responsibilities:

- Probability calculation.
- Chance bucket mapping.
- Branch/campus/fee scoring.
- Sorting.
- Fee-category cutoff order issue flags.

Important invariant:

For the same `campus + branch + data_year`, higher fee categories should not have lower cutoff ranks than lower fee categories. If Cat 4 cutoff is lower than Cat 3, mark the affected categories as a data issue instead of trusting either side.

### `load_data.py`

Data loading and cutoff building.

Responsibilities:

- Load historical Excel.
- Load Google Form responses.
- Fetch Supabase records.
- Merge and deduplicate.
- Build `cutoffs`.
- Refresh one year or form-only rows.

### `database.py`

Supabase helper layer.

Responsibilities:

- Fetch records/reports.
- Upsert records.
- Insert/delete reports.
- Delete records by source/year/exact key.
- Backward compatibility for older schemas.

## 3. Data Flow

### Startup

1. `load_data.py` reads active year settings.
2. Historical Excel rows are normalized.
3. Google Form rows are normalized.
4. Supabase rows are fetched.
5. Rows are merged and deduplicated by:

```text
Rank, Campus, Branch, Fee, data_year
```

6. Cutoffs are built per:

```text
Campus, Branch, Fee
```

7. `recommender.py` uses those cutoffs to build recommendations.

## 4. Cutoff Model

For every campus, branch, and fee category:

- `closing_rank`: 90th percentile rank.
- `true_max`: maximum observed rank.
- `std_dev`: rank spread.
- `responses`: number of rows in that group.

Why 90th percentile?

A single very high rank can be an outlier. The 90th percentile gives a more stable cutoff estimate while still reflecting real observed data.

## 5. Data Quality Rules

The admin app audits:

- Invalid rank: blank, non-numeric, less than 1, or greater than 250,000.
- Invalid fee: not 1 through 5.
- Missing campus, branch, or source.
- Duplicate natural keys.
- Low sample size per option.
- Fee cutoff order conflicts.

The Data Quality Center is informational. It does not automatically delete or mutate records.

## 6. Adding A New Counselling Year

1. Run the migration in `supabase_data_year_migration.sql` if it has not already been run.
2. Add the new Excel file to `data/` with the year in the filename.

Example:

```text
data/VIT Counselling Data ( 2026 ).xlsx
```

3. Update Streamlit secrets.

```toml
active_data_year = 2026
available_data_years = "2025,2026"

[data_share_form_urls]
2025 = "https://forms.gle/old-form"
2026 = "https://forms.gle/new-form"
```

4. Open the admin app.
5. Use Data Refresh for the selected year.
6. Check Data Quality Center before announcing the new year.

More detail: [NEXT_YEAR_SETUP.md](NEXT_YEAR_SETUP.md).

## 7. Admin Safe Operations

### Form-only refresh

Use when new Google Form responses should appear.

Effect:

- Deletes only `source = form` rows for the selected year.
- Reloads Google Form rows.
- Preserves historical rows.
- Preserves reports.

### Full source refresh

Use when rebuilding one selected year.

Effect:

- Deletes records for that year.
- Reloads that year's Excel rows.
- Reloads that year's Google Form rows.
- Preserves reports.

Before running destructive operations:

1. Export records.
2. Export reports.
3. Confirm selected year.
4. Run refresh.
5. Check Data Quality Center.

## 8. Local Development

Install:

```bash
pip install -r requirements.txt
```

Run public app:

```bash
streamlit run app.py
```

Run admin app:

```bash
streamlit run admin_app.py --server.port 8502
```

Compile check:

```bash
python -m py_compile app.py admin_app.py load_data.py recommender.py database.py
```

## 9. Secrets

Never commit `.streamlit/secrets.toml`.

Required:

- Supabase URL.
- Supabase service role key.
- Google service account credentials.
- Admin password.

Recommended:

- `active_data_year`
- `available_data_years`
- `data_share_form_url` or `[data_share_form_urls]`

## 10. Common Changes

### Change probability behavior

Edit:

```text
recommender.py
```

Look at:

- `calculate_probability`
- `get_chance_category`
- `calculate_recommendation_score`

Then test several ranks manually.

### Add a new branch alias

Edit normalization in:

```text
load_data.py
```

Search for branch mapping dictionaries.

### Change public UI

Edit:

```text
app.py
```

Keep cards responsive and verify mobile layouts.

### Change admin UI

Edit:

```text
admin_app.py
```

Avoid adding destructive actions without confirmation.

### Add database behavior

Edit:

```text
database.py
```

Keep backward compatibility where possible because deployed Supabase schemas may lag behind local code.

## 11. Troubleshooting

### Streamlit says a module is missing

Run:

```bash
pip install -r requirements.txt
```

### Supabase upsert fails

Check the unique constraint. The current expected conflict key is:

```text
rank,campus,branch,fee,data_year
```

Run the migration if needed.

### Admin year dropdown is wrong

Check:

- `active_data_year`
- `available_data_years`
- Supabase `data_year` values
- Excel filenames in `data/`

### Google Form refresh fails

Check:

- Google service account credentials.
- Sheet sharing permissions.
- Form column names.
- Rank, campus, branch, and fee normalization.

## 12. Release Checklist

Before deploying:

1. Run compile check.
2. Open public app.
3. Open admin app.
4. Test one rank.
5. Test Data Quality Center.
6. Export records and reports.
7. Confirm secrets on Streamlit Cloud.
8. Confirm `active_data_year`.
9. Confirm data-sharing form link.

## 13. Ownership And Credits

Project credits:

- Anas Arfeen
- Daksh Sablok

Keep credits visible in `README.md` and any future public-facing documentation.
