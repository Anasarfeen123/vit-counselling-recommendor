# VIT Counselling Predictor

An unofficial Streamlit app that helps students explore VIT counselling options using historical allotment data, live form submissions, and a probability model based on observed cutoff ranks.

The project includes two apps:

- `app.py`: public recommendation app for students.
- `admin_app.py`: password-protected admin dashboard for records, reports, imports, exports, refreshes, and data quality checks.

## Credits

Created and maintained by:

- **Anas Arfeen**
- **Daksh Sablok**

This project is community-built and unofficial. It is not affiliated with VIT or any official counselling authority.

## What It Does

- Accepts a VITEEE rank and returns grouped recommendations.
- Shows options as Reach, Backup, Primary, or Skip based on calculated probability.
- Uses 90th-percentile closing rank instead of raw maximum rank, so one outlier does not dominate the cutoff.
- Factors in response count and rank spread to show confidence.
- Flags suspicious data, including fee-category cutoff order conflicts.
- Lets users submit feedback when a prediction or cutoff looks wrong.
- Gives admins tools to manage records, reports, imports, exports, refreshes, and quality audits.

## Tech Stack

- Python
- Streamlit
- Supabase/PostgreSQL
- Pandas
- Plotly
- Google Sheets ingestion through `gspread`

## Repository Map

```text
app.py                         Public student recommendation app
admin_app.py                   Admin dashboard
recommender.py                 Probability, scoring, sorting, and data issue flags
load_data.py                   Excel, Google Form, Supabase loading and cutoff building
database.py                    Supabase persistence helpers
supabase_data_year_migration.sql
                               Migration for year-separated records
data/                          Example and historical data files
README.md                      Project overview
WIKI.md                        Future maintainer guide
CONTRIBUTING.md                Contribution guide
```

## Setup

1. Create and activate a virtual environment.

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies.

```bash
pip install -r requirements.txt
```

3. Create `.streamlit/secrets.toml`.

```toml
[supabase]
url = "https://your-project.supabase.co"
key = "your-service-role-key"

[gcp_service_account]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."

admin_password = "change_this_password"
active_data_year = 2025
available_data_years = "2025"
data_share_form_url = "https://forms.gle/your-form"
```

4. Run the public app.

```bash
streamlit run app.py
```

5. Run the admin app.

```bash
streamlit run admin_app.py --server.port 8502
```

You can also use:

```bash
bash run_app.sh
```

## Database Setup

The app expects two Supabase tables:

- `counselling_records`
- `reports`

For multi-year data, run:

```sql
-- See the full file:
-- supabase_data_year_migration.sql
```

The important unique key for records is:

```text
rank, campus, branch, fee, data_year
```

## Data Format

Records import CSV:

```csv
rank,campus,branch,fee,source,data_year
1200,Vellore,CSE Core,1,historical,2025
8400,Chennai,ECE Core,2,form,2025
```

Reports import CSV:

```csv
user_rank,campus,branch,fee_category,predicted_probability,predicted_chance,report_type,reason_text
8200,Vellore,CSE Core,1,74.5,Moderate,wrong_cutoff,Cutoff looked too low
```

## Admin Workflow

Use the admin dashboard to:

- View and filter records.
- Add or edit individual records.
- Delete one exact record after confirmation.
- Import records and preview quality issues.
- Export records and reports.
- Audit data quality.
- Refresh only Google Form rows.
- Rebuild one selected data year from source files.

Read [WIKI.md](WIKI.md) for a full maintainer guide.

## Contributing

Contributions are welcome, especially:

- Better data cleaning rules.
- UI polish that keeps the app usable on mobile.
- Admin workflow improvements.
- Safer refresh/import/export flows.
- Documentation updates.
- Bug reports with screenshots and exact steps.

Start with [CONTRIBUTING.md](CONTRIBUTING.md).

## Important Disclaimer

This tool is unofficial and informational. Predictions are based on available historical and submitted data. They may be incomplete, wrong, or different from official counselling outcomes. Students should always verify final decisions with official VIT counselling resources.
