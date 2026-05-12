# 🔄 Data Refresh / Reset Guide

## Overview

The **Data Refresh** feature allows admins to safely reset and reload all data in the VIT Counselling Predictor. This is useful for:

- 🔄 Starting fresh with new test data
- 🗑️ Cleaning up corrupted data
- 📋 Reloading data from updated sources
- 🧪 Testing with sample datasets
- 🎯 Periodic data resets for maintenance

## ⚠️ Important - This Action Cannot Be Undone!

**All data will be permanently deleted.** Make sure to:
1. ✅ Export backups first
2. ✅ Confirm the action twice before proceeding
3. ✅ Prepare your fresh data file

---

## 🚀 How to Use

### Step 1: Access Advanced Options
1. Open Admin Dashboard: `streamlit run admin_app.py`
2. Go to **Settings** tab
3. Check the box: **"Show Advanced Options"**

### Step 2: Choose Your Reset Option

You have 3 options:

#### 🗑️ Option A: Delete All Records Only
```
Click: "🗑️ DELETE ALL RECORDS"
↓
Confirm: "✅ YES, DELETE ALL RECORDS"
↓
✅ All counselling records deleted
```

**Result:** Removes all records but keeps reports.

---

#### 📋 Option B: Delete All Reports Only
```
Click: "📋 DELETE ALL REPORTS"
↓
Confirm: "✅ YES, DELETE ALL REPORTS"
↓
✅ All user reports deleted
```

**Result:** Removes all feedback but keeps records.

---

#### 🔄 Option C: Refresh All Data (Recommended)
This is the **most comprehensive** option:

1. Click: **"🔄 REFRESH WITH THIS DATA"**
2. Upload CSV file with fresh records
3. Preview the data
4. Confirm: **"✅ YES, REFRESH DATA"**
5. All old data deleted + new data loaded

**Result:** Complete fresh restart with new records.

---

## 📊 CSV Format for Refresh

The CSV file must have these columns:

```csv
rank,campus,branch,fee,source
1,VIT Vellore,CSE Core,1,historical
2,VIT Vellore,CSE Core,1,historical
3,VIT Chennai,ECE,2,form
5,VIT Vellore,CSE Core,2,historical
7,VIT Chennai,CSE Core,1,historical
```

**Required columns:**
- `rank` - Student rank (integer)
- `campus` - Campus name (text)
- `branch` - Branch/program (text)
- `fee` - Fee category 1-5 (integer)
- `source` - Data source: "historical" or "form" (text)

---

## 🎯 Step-by-Step Example

### Example Scenario: Clean Reset with Test Data

#### Step 1: Prepare Test Data
Create file: `fresh_test_data.csv`

```csv
rank,campus,branch,fee,source
1,VIT Vellore,CSE Core,1,historical
2,VIT Vellore,CSE Core,1,historical
3,VIT Vellore,CSE Core,1,historical
10,VIT Chennai,ECE,2,historical
20,VIT Pune,IT,3,historical
50,VIT Amravati,CSE,2,form
```

#### Step 2: Backup Current Data
1. Go to **Bulk Export** tab
2. Download current records as Excel
3. Download current reports as Excel
4. Save to safe location

#### Step 3: Execute Refresh
1. Go to **Settings** → **Advanced Options**
2. Scroll to **🔄 REFRESH ALL DATA**
3. Click **"Choose CSV file"**
4. Select: `fresh_test_data.csv`
5. Preview the 6 records
6. Click: **"🔄 REFRESH WITH THIS DATA"**
7. Confirm: **"✅ YES, REFRESH DATA"**
8. ✅ Done! Database now has 6 records

---

## 🔐 Safety Features

### Double Confirmation
Every destructive action requires 2-step confirmation:
1. Click the initial button
2. Click confirm button

### Preview Before Refresh
See data preview before final refresh

### Detailed Feedback
Get success/error messages for all actions

---

## ⏮️ If Something Goes Wrong

### Oops! I deleted the wrong data
1. Check if you have a backup (exported Excel file)
2. Re-import using **Bulk Import** tab
3. Upload your backup file

### The refresh failed
1. Check CSV format matches requirements
2. Verify all columns are spelled correctly
3. Ensure no special characters cause issues
4. Try again with smaller dataset

### Need help
1. Check the CSV format example above
2. Verify file encoding is UTF-8
3. Ensure no empty rows in CSV

---

## 📝 Common Use Cases

### Use Case 1: Weekly Reset with Fresh Data
```
Monday morning:
1. Export backup of last week
2. Prepare new fresh dataset
3. Refresh database with new data
4. Announce fresh dataset to users
```

### Use Case 2: Remove All User Reports
```
Monthly cleanup:
1. Settings → Advanced Options
2. Delete All Reports
3. Keep records intact
4. User feedback starts fresh
```

### Use Case 3: Test with Sample Data
```
Testing new features:
1. Prepare sample_test_data.csv
2. Refresh with test data
3. Test admin/student features
4. Refresh back to production data
```

### Use Case 4: Recover from Data Corruption
```
If data gets corrupted:
1. Export current (bad) data
2. Restore from recent backup
3. Re-import via Bulk Import
```

---

## ✅ Backup Strategy

### Before Every Refresh:
```
1. Go to: Bulk Export
2. Click: Download Records as Excel
   → Saves: counselling_records_[timestamp].xlsx
3. Click: Download Reports as Excel
   → Saves: reports_[timestamp].xlsx
4. Store in: /backups/ folder locally
5. Then: Proceed with refresh
```

### Automated Backups (Optional):
```bash
# Run monthly backup
python backup_script.py

# Saves all data with timestamp
```

---

## 🚀 Database Functions

The underlying database functions are:

```python
# Delete all records
db.delete_all_records()  # Returns True on success

# Delete all reports  
db.delete_all_reports()  # Returns True on success

# Refresh all data
db.refresh_all_data(records_list)  # Returns True on success
```

**They're located in:** `database.py`

---

## 📊 Before & After Example

### Before Refresh
```
Records: 1,245
Reports: 89
Campuses: 4
```

### After Refresh (with 20 records)
```
Records: 20
Reports: 0
Campuses: 2
```

---

## 🎯 Tips & Best Practices

✅ **DO:**
- Always backup before refresh
- Test on small dataset first
- Keep backup files organized with dates
- Verify CSV format matches requirements
- Document reason for each refresh

❌ **DON'T:**
- Refresh without backup
- Refresh with incomplete CSVs
- Refresh during student usage times
- Delete data multiple times in quick succession
- Skip the confirmation steps

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| CSV upload fails | Verify encoding is UTF-8, check column names |
| Confirms button doesn't work | Refresh page, retry process |
| Data not showing after refresh | Check import completed, clear cache in Settings |
| Wrong data was deleted | Restore from backup file using Bulk Import |
| Refresh shows 0 records | CSV was empty or parsing failed, check file |

---

## 📞 Support

If you encounter issues:

1. Check this guide
2. Verify CSV format
3. Try with smaller dataset
4. Check browser console for errors
5. Restart admin_app.py

---

## Summary

| Feature | Details |
|---------|---------|
| **Access** | Settings → Advanced Options |
| **Destructive?** | Yes, requires confirmation |
| **Backupable?** | Yes, use Bulk Export first |
| **Reversible?** | Only with backup restore |
| **Time** | < 5 seconds typically |
| **Recommended Frequency** | As needed for maintenance |

---

## 🎊 You're Ready!

You now have full control to reset and refresh your database whenever needed.

**Remember:** Always backup first! 💾

Happy administrating! 🚀
