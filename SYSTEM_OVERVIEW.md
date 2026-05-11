# VIT Counselling Predictor - Complete System Overview

## 📋 System Architecture

The VIT Counselling Predictor system consists of two separate Streamlit applications:

```
┌─────────────────────────────────────────────────────┐
│         VIT Counselling Predictor System            │
└─────────────────────────────────────────────────────┘
        │                              │
        │                              │
        ▼                              ▼
   ┌─────────────┐           ┌──────────────────┐
   │  Main App   │           │ Admin Dashboard  │
   │  (app.py)   │           │ (admin_app.py)   │
   └─────────────┘           └──────────────────┘
   For Students:            For Administrators:
   • Predictions            • CRUD Operations
   • Recommendations        • Bulk Import/Export
   • Submit Reports         • Analytics
   • View Chances           • Report Management
        │                              │
        └──────────────┬───────────────┘
                       │
                       ▼
            ┌──────────────────────┐
            │  Supabase Database   │
            │  (PostgreSQL Backend)│
            └──────────────────────┘
                       │
            ┌──────────┴──────────┐
            │                     │
            ▼                     ▼
        ┌────────────────┐  ┌───────────┐
        │counselling_    │  │ reports   │
        │records         │  │           │
        └────────────────┘  └───────────┘
```

## 🎯 Application Features Comparison

| Feature | Main App | Admin App |
|---------|----------|-----------|
| **Purpose** | Student recommendations | Data management |
| **Access** | Public | Password protected |
| **Core Functions** | Predict, recommend | CRUD, analytics |
| **View Records** | ✅ (filtered by input) | ✅ (all records) |
| **Add Records** | ✓ (via form submission) | ✅ (direct + bulk) |
| **Edit Records** | ✗ | ✅ |
| **Delete Reports** | ✗ | ✅ |
| **Export Data** | ✗ | ✅ |
| **Import Data** | ✗ | ✅ |
| **Analytics** | Partial | ✅ (comprehensive) |
| **Authentication** | None | Password |
| **UI Style** | User-friendly | Admin-focused |

## 📚 Data Model

### counselling_records Table
```sql
CREATE TABLE counselling_records (
    id BIGSERIAL PRIMARY KEY,
    rank INTEGER NOT NULL,              -- Student rank (1-∞)
    campus TEXT NOT NULL,               -- VIT campus name
    branch TEXT NOT NULL,               -- Branch/program
    fee INTEGER NOT NULL,               -- Fee category (1-5)
    source TEXT DEFAULT 'historical',   -- 'historical' | 'form'
    created_at TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT uq_record UNIQUE (rank, campus, branch, fee)
);
```

### reports Table
```sql
CREATE TABLE reports (
    id BIGSERIAL PRIMARY KEY,
    user_rank INTEGER NOT NULL,
    campus TEXT NOT NULL,
    branch TEXT NOT NULL,
    fee_category INTEGER NOT NULL,
    predicted_probability NUMERIC(5,1),
    predicted_chance TEXT,              -- Safe | Moderate | Dream | Very Unlikely
    report_type TEXT NOT NULL,          -- See Report Type Categories below
    reason_text TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Report Type Categories
- `wrong_cutoff` - Incorrect cutoff prediction
- `got_allotted` - Successfully allotted (feedback)
- `not_allotted` - Not allotted (feedback)
- `prob_high` - Predicted probability too high
- `prob_low` - Predicted probability too low
- `other` - Other feedback

## 🔄 Data Flow

### 1. Data Ingest Flow
```
┌─────────────┐      ┌──────────────┐      ┌──────────┐
│ Excel Sheet │  →   │ Google Form  │  →   │ Supabase │
│ (historical)│      │ (live input) │      │ Database │
└─────────────┘      └──────────────┘      └──────────┘
                            ↑
                     Synced by load_data.py
                     on app startup
```

### 2. Prediction Flow
```
┌──────────────┐
│ Student Input│  (Rank, Campus, Branch, Fee)
└──────┬───────┘
       │
       ▼
┌──────────────────┐
│ recommender.py   │
│ • Calculate odds │
│ • Filter options │
│ • Rank cutoffs   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ Show Prediction  │
│ Safe/Moderate/   │
│ Dream/Unlikely   │
└──────┬───────────┘
       │
       ▼
┌──────────────────┐
│ User Feedback    │ (Optional: Submit Report)
└──────────────────┘
```

### 3. Admin Data Management Flow
```
┌─────────────────┐
│ Bulk Import CSV │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Validate Data   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Upsert to DB    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Live in App     │
└─────────────────┘
```

## 🚀 Deployment Options

### Option 1: Single Streamlit App (Main Only)
```bash
streamlit run app.py
```
- Simple setup
- No admin interface

### Option 2: Two Separate Apps
```bash
# Terminal 1
streamlit run app.py --server.port 8501

# Terminal 2
streamlit run admin_app.py --server.port 8502
```
- Main App: http://localhost:8501
- Admin App: http://localhost:8502

### Option 3: Multi-page Streamlit App (Advanced)
- Create `pages/` directory
- Split into `admin_page.py` and `student_page.py`
- Add authentication middleware
- Single deployment

### Option 4: Streamlit Cloud Deployment

**Deploy Main App:**
1. Push to GitHub repository
2. Go to https://streamlit.io/cloud
3. Create new app → Select repo → `app.py`
4. Add secrets in Settings → Secrets

**Deploy Admin App (separate):**
1. Create second app in Streamlit Cloud
2. Select same repo → `admin_app.py`
3. Add same secrets
4. Restrict access via OAuth/password

## 📊 Key Metrics & Admin Operations

### Metrics Tracked
- Total records in database
- Records by campus/branch/fee
- Report count and distribution
- Source distribution (historical vs form)
- Rank statistics (min, max, avg, median)

### Admin Operations Available
1. **View**: All records and reports with filters
2. **Create**: Add new records individually or in bulk
3. **Update**: Edit record details (campus, branch, fee, source)
4. **Delete**: Remove reports (record deletion requires DB perms)
5. **Import**: CSV/Excel batch uploads
6. **Export**: CSV/Excel batch downloads
7. **Analyze**: Charts, statistics, distributions
8. **Manage**: Reports filtering, sorting, metadata

## 🔐 Security Considerations

### Current Protections
- Admin password authentication
- Service role key (not anon key)
- Session-based auth state

### Recommended Enhancements
- [ ] Enable Row-Level Security (RLS) in Supabase
- [ ] Add IP whitelisting for admin app
- [ ] Implement audit logging
- [ ] Add rate limiting
- [ ] Use environment variables for secrets
- [ ] Enable database backups
- [ ] Add request logging

### Secrets Management
```toml
# .streamlit/secrets.toml (NEVER commit this!)
[supabase]
url = "..."
key = "..."

[gcp_service_account]
type = "service_account"
# ...

admin_password = "strong_secure_password"
```

## 📂 Project Structure

```
VIT Recommendation/
├── app.py                      # Main student app
├── admin_app.py               # Admin dashboard ⭐ NEW
├── database.py                # Supabase CRUD operations
├── load_data.py               # Data ingestion & validation
├── recommender.py             # Prediction logic
├── preprocessing.py           # Data normalization
├── requirements.txt           # Dependencies
├── schema.sql                 # Database schema
├── SETUP.md                   # Main setup guide
├── ADMIN_GUIDE.md            # Admin documentation ⭐ NEW
├── ADMIN_QUICK_START.md      # Quick start guide ⭐ NEW
├── run_app.sh                # App switcher script ⭐ NEW
├── credentials.json          # Google auth
├── .streamlit/
│   └── secrets.toml         # Secrets (gitignored)
├── data/
│   ├── example_records.csv   # Example data ⭐ NEW
│   ├── example_reports.csv   # Example data ⭐ NEW
│   └── [other data files]
├── assets/
│   └── [images, icons]
└── __pycache__/
```

## 🔧 Common Admin Tasks

### Daily
- [ ] Check recent reports
- [ ] Monitor record additions
- [ ] Review new feedback

### Weekly
- [ ] Export data backup
- [ ] Check analytics trends
- [ ] Validate data quality

### Monthly
- [ ] Archive old reports
- [ ] Review admin logs
- [ ] Update documentation
- [ ] Assess prediction accuracy

### As Needed
- [ ] Import new data
- [ ] Delete erroneous records
- [ ] Update campus/branch information
- [ ] Handle data requests

## 📈 Performance & Optimization

### For Large Datasets (10k+ records)
1. Use filters when viewing
2. Batch imports in groups of 1000+
3. Clear cache regularly
4. Archive old reports monthly
5. Consider database indexing

### Database Optimization (Supabase)
- Already includes indexes on:
  - `campus, branch, fee`
  - `rank`
  - `source`
  - `report_type`
  - `created_at`

## 🐛 Troubleshooting Matrix

| Problem | Likely Cause | Solution |
|---------|-------------|----------|
| Can't login | Wrong password | Check `.streamlit/secrets.toml` |
| No records show | Bad DB connection | Verify Supabase URL & key |
| Import fails | Bad CSV format | Check column names match exactly |
| Slow dashboard | Too many records | Use filters, clear cache |
| Reports not deleting | DB permissions | Check Supabase RLS policies |

## 📞 Support & Maintenance

### Getting Help
1. Check relevant guide:
   - Students: See prompts in main app
   - Admins: Check [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
2. Review [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md) for common tasks
3. Check [SETUP.md](SETUP.md) for system setup

### Reporting Issues
Include:
- Error message (exact text)
- What you were doing
- Browser/software version
- .streamlit/secrets.toml structure (no values!)

## 🎓 Learning Path

### For Developers
1. Read [SETUP.md](SETUP.md) - Understand architecture
2. Review [database.py](database.py) - See CRUD operations
3. Review [admin_app.py](admin_app.py) - Understand UI components
4. Review [recommender.py](recommender.py) - Understand prediction logic

### For Admins
1. Start with [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md) - 5-minute setup
2. Read [ADMIN_GUIDE.md](ADMIN_GUIDE.md) - Complete reference
3. Try example data: `data/example_records.csv` and `data/example_reports.csv`

## 🚀 Next Steps

1. ✅ Set up Supabase backend
2. ✅ Configure secrets
3. ✅ Run main app
4. ✅ **Add admin app** ← You are here!
5. Test both apps
6. Deploy to production
7. Monitor and optimize

## 📝 Version History

- **1.0** (May 2026)
  - Main student prediction app
  - Database backend on Supabase
  
- **2.0** (May 2026)
  - ✨ **NEW**: Admin Dashboard
  - ✨ **NEW**: Bulk import/export
  - ✨ **NEW**: Full data analytics
  - ✨ **NEW**: Report management
  - ✨ **NEW**: Admin authentication

---

**Happy Counselling! 🎓**

For more details, see:
- Student Features: [app.py](app.py)
- Admin Features: [admin_app.py](admin_app.py) & [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
- Setup Help: [SETUP.md](SETUP.md) & [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md)
