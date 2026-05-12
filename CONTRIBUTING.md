# Contributing

Thanks for helping improve the VIT Counselling Predictor. This project handles student-facing predictions, so contributions should be careful, explainable, and easy to review.

## Project Maintainers

Credit and maintainership should remain visible for:

- Anas Arfeen
- Daksh Sablok

## What You Can Contribute

Good contributions include:

- Fixing bugs in recommendations or data loading.
- Improving cutoff and confidence logic.
- Improving mobile or dark-mode UI.
- Improving admin workflows.
- Adding safer data validation.
- Improving docs and setup guides.
- Adding tests or small verification scripts.
- Cleaning up confusing code without changing behavior.

Avoid:

- Hardcoding private credentials.
- Removing credits.
- Replacing the model with opaque logic that cannot be explained.
- Adding destructive admin actions without confirmation.
- Mixing large refactors with behavior changes.

## Local Setup

1. Fork or clone the repository.

```bash
git clone <repo-url>
cd "VIT Recommendation"
```

2. Create a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

3. Install dependencies.

```bash
pip install -r requirements.txt
```

4. Add local secrets.

Create:

```text
.streamlit/secrets.toml
```

Never commit this file.

5. Run the app.

```bash
streamlit run app.py
```

6. Run the admin app.

```bash
streamlit run admin_app.py --server.port 8502
```

## Branch Naming

Use descriptive branches:

```text
fix/cutoff-order-warning
feature/admin-quality-export
docs/wiki-maintainer-guide
ui/public-dark-mode
```

## Before You Submit Changes

Run:

```bash
python -m py_compile app.py admin_app.py load_data.py recommender.py database.py
```

If your change touches docs only, still check links and formatting.

If your change touches data logic, manually verify:

- One low rank.
- One middle rank.
- One high rank.
- At least two campuses.
- At least two fee categories for the same branch.
- A known data-quality conflict if available.

If your change touches admin features, manually verify:

- Dashboard loads.
- Records tab loads.
- Reports tab loads.
- Data Quality Center loads.
- Bulk import preview works.
- Destructive actions require confirmation.

## Pull Request Checklist

Include:

- What changed.
- Why it changed.
- Screenshots for UI changes.
- Any migration needed.
- Any new secrets needed.
- Verification steps you ran.

Example:

```markdown
## Summary
- Added quality warning for fee-category cutoff conflicts.
- Updated admin Data Quality Center.

## Verification
- Ran `python -m py_compile ...`
- Tested rank 5000 and 50000 locally.
- Checked admin Data Quality page.
```

## Data Rules

Records should use:

```csv
rank,campus,branch,fee,source,data_year
```

Expected values:

- `rank`: integer from 1 to 250000.
- `campus`: normalized campus name.
- `branch`: normalized branch/program name.
- `fee`: integer from 1 to 5.
- `source`: `historical` or `form`.
- `data_year`: counselling year, for example `2025`.

Do not mix years under the old unique key. Use:

```text
rank,campus,branch,fee,data_year
```

## UI Guidelines

- Keep the public app simple for students.
- Keep admin pages dense but readable.
- Do not hide important warnings.
- Make destructive actions explicit and confirmation-gated.
- Check mobile layouts for public UI changes.
- Keep dark mode readable.

## Security

Never commit:

- Supabase service role keys.
- Google service account JSON.
- `.streamlit/secrets.toml`.
- Raw private form data that should not be public.

Use environment-specific secrets in Streamlit Cloud.

## Documentation

When changing behavior, update at least one of:

- `README.md`
- `WIKI.md`
- `ADMIN_GUIDE.md`
- `DATA_REFRESH_GUIDE.md`
- `NEXT_YEAR_SETUP.md`

Docs are part of the product. If future maintainers cannot understand the change, the change is not finished.
