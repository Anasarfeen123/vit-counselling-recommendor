# Documentation Index

## Main Project Docs

- [README.md](README.md) - Project overview, credits, setup, usage, and disclaimer.
- [WIKI.md](WIKI.md) - Future maintainer guide for architecture, data flow, yearly setup, and operations.
- [CONTRIBUTING.md](CONTRIBUTING.md) - How to contribute safely and what to verify before submitting changes.

## Credits

Created and maintained by:

- Anas Arfeen
- Daksh Sablok

---

# Admin Dashboard - Complete Index

## 🎯 Start Here

**First time?** Start with this document, then read:
1. [README.md](README.md) - Project overview and setup
2. [WIKI.md](WIKI.md) - Future maintainer guide
3. [CONTRIBUTING.md](CONTRIBUTING.md) - Contribution workflow
4. [ADMIN_SETUP_COMPLETE.md](ADMIN_SETUP_COMPLETE.md) - 5 min setup overview
5. [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md) - Getting started guide
6. [admin_app.py](admin_app.py) - The application itself

---

## 📚 Documentation Structure

### 🚀 Getting Started (Beginner)
- **[ADMIN_SETUP_COMPLETE.md](ADMIN_SETUP_COMPLETE.md)** ← Start here!
  - What was created
  - Quick start (< 5 min)
  - Configuration steps
  - Common tasks

### 📖 Quick Reference (Intermediate)
- **[ADMIN_QUICK_START.md](ADMIN_QUICK_START.md)**
  - 5-minute setup guide
  - Example CSV files
  - First steps checklist
  - Common questions

### 🔍 Complete Reference (Advanced)
- **[ADMIN_GUIDE.md](ADMIN_GUIDE.md)**
  - Full feature documentation
  - User guide for each tab
  - Data validation rules
  - Troubleshooting matrix

### 🎨 Visual Tour (Visual Learner)
- **[ADMIN_VISUAL_GUIDE.md](ADMIN_VISUAL_GUIDE.md)**
  - ASCII mockups of each screen
  - Feature workflows
  - Example use cases
  - Performance metrics

### 🏗️ Architecture (Developer)
- **[SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)**
  - System architecture diagram
  - Data model explanation
  - Data flow diagrams
  - Deployment options

### Maintainers & Contributors
- **[WIKI.md](WIKI.md)**
  - How the predictor works
  - How to add a new counselling year
  - Data quality rules
  - Release checklist
- **[CONTRIBUTING.md](CONTRIBUTING.md)**
  - Local setup
  - Pull request checklist
  - Data and UI contribution rules

---

## 📂 File Map

### Core Application
```
admin_app.py (41 KB)
├─ Dashboard tab - Overview & statistics
├─ Records tab - CRUD operations for records
├─ Reports tab - Report management & analytics
├─ Bulk Import tab - Batch data loading
├─ Bulk Export tab - Data export (CSV/Excel)
├─ Analytics tab - Charts & insights
└─ Settings tab - Admin panel settings
```

### Documentation
```
README & Guides
├─ ADMIN_SETUP_COMPLETE.md - Complete setup summary
├─ ADMIN_QUICK_START.md - 5-min quick start
├─ ADMIN_GUIDE.md - Full reference manual
├─ ADMIN_VISUAL_GUIDE.md - Visual feature tour
├─ SYSTEM_OVERVIEW.md - Architecture docs
└─ INDEX.md - This file

Updated Files
├─ database.py - Added fetch_all_reports() function
└─ requirements.txt - Added streamlit-option-menu
```

### Example Data
```
Sample Files (Ready to import)
├─ data/example_records.csv - 20 sample records
└─ data/example_reports.csv - 10 sample reports
```

### Utilities
```
Scripts & Tools
└─ run_app.sh - Interactive app switcher
```

---

## 🎯 Feature Quick Links

### 📊 Dashboard Features
| Feature | File | Line | Documentation |
|---------|------|------|---------------|
| Dashboard overview | admin_app.py | ~120 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-dashboard-tab) |
| Records management | admin_app.py | ~280 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-records-tab) |
| Report management | admin_app.py | ~450 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-reports-tab) |
| Bulk import | admin_app.py | ~620 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-bulk-import) |
| Bulk export | admin_app.py | ~750 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-bulk-export) |
| Analytics | admin_app.py | ~860 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-analytics) |
| Settings | admin_app.py | ~940 | [ADMIN_GUIDE.md](ADMIN_GUIDE.md#-settings) |

---

## 🔧 Configuration

### Setup Checklist
```
├─ [ ] Install: pip install streamlit-option-menu
├─ [ ] Configure: Edit .streamlit/secrets.toml
├─ [ ] Add: admin_password value
├─ [ ] Test: streamlit run admin_app.py
├─ [ ] Login: Use password "admin123"
├─ [ ] Verify: All tabs load properly
└─ [ ] Secure: Change password from default
```

### Secrets Configuration
```toml
[supabase]
url = "https://your-project.supabase.co"
key = "your-service-role-key"

[gcp_service_account]
type = "service_account"
# ... existing config ...

# Change this immediately!
admin_password = "change_me_to_strong_password"
```

---

## 🚀 Quick Commands

### Installation
```bash
pip install streamlit-option-menu
pip install -r requirements.txt
```

### Running
```bash
# Run admin app
streamlit run admin_app.py

# Run main app
streamlit run app.py

# Interactive menu
bash run_app.sh
```

### Running Both Simultaneously
```bash
# Terminal 1: Main app on port 8501
streamlit run app.py --server.port 8501

# Terminal 2: Admin app on port 8502
streamlit run admin_app.py --server.port 8502
```

---

## 📊 Data Formats

### Records CSV
```csv
rank,campus,branch,fee,source
1,VIT Vellore,CSE Core,1,historical
2,VIT Chennai,ECE,2,form
```

### Reports CSV
```csv
user_rank,campus,branch,fee_category,predicted_probability,predicted_chance,report_type,reason_text
1,VIT Vellore,CSE Core,1,95.5,Safe,wrong_cutoff,Cutoff was higher
```

---

## ❓ Common Questions

**Q: How do I change the admin password?**
A: Edit `.streamlit/secrets.toml` and change `admin_password` value. Restart the app.

**Q: Can I import large files?**
A: Yes, tested up to 10,000+ records. Batch them for better performance.

**Q: Where are backups stored?**
A: Use "Bulk Export" to download backups. They're stored locally on your device.

**Q: Can I delete records?**
A: Yes, but it requires database-level permissions. Contact your DB administrator.

**Q: How do I run both apps at the same time?**
A: Use different ports: `streamlit run app.py --server.port 8501` and `streamlit run admin_app.py --server.port 8502`

For more FAQs, see:
- [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md#-common-questions)
- [ADMIN_GUIDE.md](ADMIN_GUIDE.md#troubleshooting)

---

## 🎓 Learning Path

### For Users/Admins
1. Read [ADMIN_SETUP_COMPLETE.md](ADMIN_SETUP_COMPLETE.md) - Overview (5 min)
2. Read [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md) - Getting started (10 min)
3. Read [ADMIN_GUIDE.md](ADMIN_GUIDE.md) - Full reference (15 min)
4. Try [admin_app.py](admin_app.py) - Test with example data (10 min)
5. Reference [ADMIN_VISUAL_GUIDE.md](ADMIN_VISUAL_GUIDE.md) - Feature walkthrough (10 min)

### For Developers
1. Read [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md) - Architecture (15 min)
2. Review [admin_app.py](admin_app.py) - Code walkthrough (20 min)
3. Review [database.py](database.py) - CRUD operations (15 min)
4. Check [SETUP.md](SETUP.md) - System setup (15 min)

---

## 📈 What's New (v2.0)

### Added Features
✨ Separate admin application  
✨ Password-protected access  
✨ Full CRUD capabilities  
✨ Bulk import/export  
✨ Analytics dashboard  
✨ Report management  
✨ Data validation  
✨ Secure authentication  

### Modified Files
- `database.py` - Added `fetch_all_reports()` alias
- `requirements.txt` - Added `streamlit-option-menu`

### New Files
- `admin_app.py` - Main admin application
- `ADMIN_SETUP_COMPLETE.md` - Setup summary
- `ADMIN_QUICK_START.md` - Quick start guide
- `ADMIN_GUIDE.md` - Full documentation
- `ADMIN_VISUAL_GUIDE.md` - Visual tour
- `SYSTEM_OVERVIEW.md` - Architecture docs
- `INDEX.md` - This file
- `run_app.sh` - App switcher
- `data/example_records.csv` - Sample data
- `data/example_reports.csv` - Sample data

---

## 🔐 Security Best Practices

✅ Change admin password from `admin123`  
✅ Keep `.streamlit/secrets.toml` in `.gitignore`  
✅ Never commit credentials to GitHub  
✅ Use service_role key only  
✅ Enable Row-Level Security in Supabase  
✅ Restrict admin app to trusted network  
✅ Audit admin actions regularly  

---

## 📞 Support & Help

### For Setup Issues
→ See [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md#-setup-5-minutes)

### For Feature Questions
→ See [ADMIN_GUIDE.md](ADMIN_GUIDE.md)

### For Visual Examples
→ See [ADMIN_VISUAL_GUIDE.md](ADMIN_VISUAL_GUIDE.md)

### For Architecture Questions
→ See [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)

### For Troubleshooting
→ See [ADMIN_GUIDE.md#troubleshooting](ADMIN_GUIDE.md#troubleshooting)

---

## 🎊 You're All Set!

You now have:
✅ Complete admin dashboard  
✅ Full data management  
✅ Professional analytics  
✅ Comprehensive documentation  
✅ Ready-to-use examples  

**Next step:**
```bash
pip install streamlit-option-menu
streamlit run admin_app.py
```

**Default password:** `admin123` (change it!)

---

## 📝 File Map Summary

```
VIT Recommendation/
├── admin_app.py .................. Main admin application ⭐
├── ADMIN_SETUP_COMPLETE.md ....... Setup summary ⭐
├── ADMIN_QUICK_START.md .......... Quick start guide ⭐
├── ADMIN_GUIDE.md ................ Full documentation ⭐
├── ADMIN_VISUAL_GUIDE.md ......... Visual tour ⭐
├── SYSTEM_OVERVIEW.md ............ Architecture ⭐
├── INDEX.md ...................... This file ⭐
├── run_app.sh .................... App switcher ⭐
├── requirements.txt .............. Updated with streamlit-option-menu
├── database.py ................... Updated with fetch_all_reports()
│
├── data/
│   ├── example_records.csv ....... Sample data ⭐
│   └── example_reports.csv ....... Sample data ⭐
│
├── app.py ........................ Existing student app
├── load_data.py .................. Existing data loading
├── recommender.py ................ Existing recommendation engine
└── ... (other existing files)

⭐ = NEW or MODIFIED
```

---

## 🎯 30-Second Summary

**What:** Separate admin dashboard for VIT Counselling Predictor  
**How:** Streamlit application with password protection  
**Features:** CRUD, bulk import/export, analytics, security  
**Setup:** 5 minutes  
**Start:** `streamlit run admin_app.py`  
**Docs:** Read [ADMIN_SETUP_COMPLETE.md](ADMIN_SETUP_COMPLETE.md)  

---

## 📞 Questions?

1. **Quick setup?** → [ADMIN_QUICK_START.md](ADMIN_QUICK_START.md)
2. **How do I...?** → [ADMIN_GUIDE.md](ADMIN_GUIDE.md)
3. **Visual guide?** → [ADMIN_VISUAL_GUIDE.md](ADMIN_VISUAL_GUIDE.md)
4. **Architecture?** → [SYSTEM_OVERVIEW.md](SYSTEM_OVERVIEW.md)
5. **Setup complete?** → [ADMIN_SETUP_COMPLETE.md](ADMIN_SETUP_COMPLETE.md)

Happy administrating! 🚀
