# Admin Dashboard - VIT Counselling Predictor

## Overview

The **Admin Dashboard** is a separate Streamlit application that gives administrators full control over the VIT Counselling Predictor data. It enables complete CRUD (Create, Read, Update, Delete) operations on counselling records and user reports.

## Features

### 🔐 **Security**
- Admin password protection (configurable via Streamlit secrets)
- Session-based authentication
- Logout functionality

### 📚 **Record Management**
- **View & Filter**: Display records with filters by rank, campus, branch, and source
- **Add Records**: Insert new counselling records
- **Edit Records**: Modify existing records
- **View Statistics**: Analytics on records by campus, branch, rank distribution

### 📋 **Report Management**
- **View Reports**: Browse all user-submitted reports
- **Filter Reports**: Filter by report type, predicted chance, and campus
- **Delete Reports**: Remove invalid or duplicate reports
- **Report Analytics**: Visualize report distribution and statistics

### 📥 **Bulk Import**
- Import counselling records from CSV
- Import user reports from CSV or Excel
- Batch data loading with validation

### 📤 **Bulk Export**
- Export all records as CSV or Excel
- Export all reports as CSV or Excel
- Timestamped backups

### 📊 **Analytics Dashboard**
- Total records and statistics
- Campus and branch distribution charts
- Rank distribution analysis
- Source distribution (historical vs form)
- Report type distribution
- Chance prediction distribution

### ⚙️ **Settings**
- Admin logout
- Database connection status
- Debug information
- Cache management

## Installation

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

The requirements include:
- `streamlit` - Web framework
- `streamlit-option-menu` - Enhanced navigation menu
- `pandas` - Data manipulation
- `openpyxl` - Excel support
- `supabase` - Database client

### 2. Configure Secrets

Add to `.streamlit/secrets.toml` (local) or Streamlit Cloud secrets:

```toml
[supabase]
url = "https://<your-project-ref>.supabase.co"
key = "<your service_role key>"

[gcp_service_account]
type = "service_account"
project_id = "..."
# ... rest of GCP credentials

# Admin password (optional, defaults to "admin123")
admin_password = "your_secure_password_here"
```

## Running the App

### Local Development

```bash
streamlit run admin_app.py
```

This will:
1. Open at `http://localhost:8501`
2. Prompt for admin password
3. Display the admin dashboard

### Streamlit Cloud Deployment

```bash
streamlit run admin_app.py
```

Or set it as the main app in `streamlit.app.py` (if deploying both apps).

## User Guide

### 📊 Dashboard Tab
Main overview with:
- Quick statistics (records, reports, unique ranks, campuses)
- Recent records (last 10)
- Recent reports (last 10)

### 📚 Records Tab

#### View & Filter
1. Select filters (rank, campus, branch, source)
2. Results update in real-time
3. Export filtered results by downloading

#### Add New Record
1. Enter rank (required)
2. Select campus
3. Enter branch name
4. Select fee category (1-5)
5. Choose source (historical or form)
6. Click "Add Record"

#### Edit Record
1. Select record by rank
2. Update any fields
3. Click "Update Record"
4. Changes saved to database

#### Delete Record
- Feature requires database-level permissions
- Contact DB administrator for deletions

### 📋 Reports Tab

#### View Reports
- Browse all submitted reports
- Filter by report type, predicted chance, campus
- View details inline

#### Report Analytics
- Visual breakdown by report type
- Predicted chance distribution (pie chart)
- Campus-wise report counts
- Distribution tables

#### Delete Report
1. Select report from dropdown
2. Review details
3. Click "DELETE THIS REPORT"
4. Action is permanent

### 📥 Bulk Import

#### Import Records CSV Format
```csv
rank,campus,branch,fee,source
1,VIT Vellore,CSE Core,1,historical
2,VIT Vellore,CSE Core,1,historical
3,VIT Chennai,ECE,2,form
```

#### Import Reports CSV/Excel Format
```csv
user_rank,campus,branch,fee_category,predicted_probability,predicted_chance,report_type,reason_text
1,VIT Vellore,CSE Core,1,95.5,Safe,wrong_cutoff,Cutoff was higher than expected
2,VIT Chennai,ECE,2,75.3,Moderate,prob_high,Probability seemed inflated
```

### 📤 Bulk Export

1. Navigate to "Bulk Export"
2. Click format button (CSV or Excel)
3. Download starts automatically
4. File includes timestamp in filename

### 📊 Analytics

View comprehensive statistics:
- Record counts by campus
- Top 10 branches
- Rank statistics (min, max, avg, median)
- Source distribution pie chart

## Data Validation

### Records
- Rank: Integer, > 0
- Campus: Must be valid VIT campus
- Branch: Text field
- Fee: Integer 1-5
- Source: "historical" or "form"

### Reports
- User Rank: Integer
- Campus/Branch: Text
- Fee Category: Integer 1-5
- Predicted Probability: Float (0-100)
- Predicted Chance: Must be "Safe", "Moderate", "Dream", or "Very Unlikely"
- Report Type: Valid type from ["wrong_cutoff", "got_allotted", "not_allotted", "prob_high", "prob_low", "other"]
- Reason: Optional text

## Common Tasks

### Backup All Data
1. Go to "Bulk Export"
2. Export records as Excel
3. Export reports as Excel
4. Save with date for version control

### Clean Up Duplicate Reports
1. Go to "Reports" → "View Reports"
2. Filter by type and review
3. Use "Delete Report" to remove duplicates

### Update Cutoff Data
1. Export current records
2. Update in spreadsheet
3. Delete old records (contact admin)
4. Re-import via "Bulk Import"

### Merge Two Data Sources
1. Export both sources as CSV
2. Combine in spreadsheet
3. Remove duplicates (by rank + campus + branch + fee)
4. Import via "Bulk Import"

## Troubleshooting

### Password Not Working
- Check `.streamlit/secrets.toml` syntax
- Verify `admin_password` value
- Restart Streamlit: `streamlit run admin_app.py --logger.level=debug`

### Records Not Showing
- Verify database connection in secrets
- Check internet connectivity
- Try: "Settings" → "Clear Cache"

### Import Failing
- Verify CSV format matches requirements
- Check column names exactly
- Ensure no special characters in data
- Try smaller file to isolate issue

### Export Not Downloading
- Check browser download permissions
- Try different format (CSV vs Excel)
- Check available disk space

## Security Notes

⚠️ **Important:**
- Always use strong admin password in production
- Change default password from "admin123"
- Use service_role key (never anon key)
- Enable Row-Level Security (RLS) on tables in Supabase
- Restrict Streamlit app to trusted network when possible
- Keep secrets.toml in .gitignore

## Performance Tips

- Clear cache regularly under Settings
- Use filters when viewing large datasets (>10k records)
- Export in batches for analysis
- Archive old reports monthly

## Support & Maintenance

| Issue | Solution |
|-------|----------|
| Slow dashboard | Clear cache, restart app |
| Import errors | Validate CSV format, check column names |
| Missing reports | Verify database RLS policies |
| Authentication loop | Check admin_password in secrets |

## Version History

- **v1.0** (May 2026): Initial release with CRUD, import/export, analytics

## Related Documentation

- [Main App Setup Guide](SETUP.md)
- [Database Schema](schema.sql)
- [Database Functions](database.py)
