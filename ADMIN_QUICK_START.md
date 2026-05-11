# Quick Start - Admin Dashboard

## 🚀 Setup (5 minutes)

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Configure Secrets
Edit `.streamlit/secrets.toml`:
```toml
[supabase]
url = "https://<your-project-ref>.supabase.co"
key = "<your service_role key>"

[gcp_service_account]
type = "service_account"
# ... your GCP credentials

# Change this password!
admin_password = "change_me_to_strong_password"
```

### Step 3: Run Admin App
```bash
# Option A: Direct
streamlit run admin_app.py

# Option B: Interactive menu (if you have run_app.sh executable)
bash run_app.sh
# Then select: 2) Admin Dashboard
```

### Step 4: Login
- Navigate to http://localhost:8501
- Enter your admin password
- Access dashboard

---

## 📋 Example CSV Files for Bulk Import

### Records Import (records.csv)
Save this file and import via Dashboard → Bulk Import → Records:

```csv
rank,campus,branch,fee,source
1,VIT Vellore,CSE Core,1,historical
2,VIT Vellore,CSE Core,1,historical
3,VIT Vellore,CSE Core,1,historical
5,VIT Vellore,CSE Core,2,historical
7,VIT Vellore,CSE Core,2,historical
10,VIT Chennai,CSE Core,1,historical
15,VIT Chennai,CSE Core,1,historical
20,VIT Pune,ECE,2,historical
25,VIT Amravati,IT,3,form
```

### Reports Import (reports.csv)
Save this file and import via Dashboard → Bulk Import → Reports:

```csv
user_rank,campus,branch,fee_category,predicted_probability,predicted_chance,report_type,reason_text
1,VIT Vellore,CSE Core,1,95.5,Safe,wrong_cutoff,Cutoff was higher than expected
5,VIT Vellore,CSE Core,2,78.3,Moderate,prob_high,Probability was inflated
10,VIT Chennai,CSE Core,1,92.1,Safe,got_allotted,Successfully allotted
15,VIT Chennai,CSE Core,1,60.5,Dream,prob_low,Got allotted despite low probability
20,VIT Pune,ECE,2,75.0,Moderate,not_allotted,Did not get allotted
25,VIT Amravati,IT,3,45.0,Very Unlikely,other,General feedback
```

---

## 🎯 First Steps

1. **Review Dashboard**: See current records and reports
2. **Check Analytics**: Understand data distribution
3. **Try Export**: Export data to see CSV format
4. **Try Import**: Import sample data from examples above
5. **Test Edit**: Modify a record and verify
6. **Check Reports**: View and delete sample reports if needed

---

## 💡 Tips

### 📊 Data Validation Before Import
- Rank should be positive integers
- Campus must match: VIT Vellore, VIT Chennai, VIT Pune, VIT Amravati
- Fee should be 1-5
- Predicted Chance: Safe, Moderate, Dream, Very Unlikely
- Report Type: wrong_cutoff, got_allotted, not_allotted, prob_high, prob_low, other

### 🔒 Security
- Change admin_password from default
- Never share credentials.json
- Keep secrets.toml in .gitignore

### 🎓 Running Both Apps
You can run both simultaneously on different ports:

**Terminal 1 (Main App):**
```bash
streamlit run app.py --server.port 8501
```

**Terminal 2 (Admin App):**
```bash
streamlit run admin_app.py --server.port 8502
```

Then access:
- Main App: http://localhost:8501
- Admin App: http://localhost:8502

---

## ❓ Common Questions

**Q: Can I delete records?**
A: The delete function requires additional DB permissions. Contact your database administrator.

**Q: How do I backup data?**
A: Use "Bulk Export" to download all records and reports as Excel files.

**Q: What if I forget the admin password?**
A: Edit `.streamlit/secrets.toml` and change the `admin_password` value.

**Q: Can I import data from my old system?**
A: Yes! Format it as CSV with the required columns and use "Bulk Import".

**Q: How many records can I import at once?**
A: Theoretically unlimited, but recommend batching in groups of 1000+ for performance.

---

## 📞 Support

If you encounter issues:

1. Check [ADMIN_GUIDE.md](ADMIN_GUIDE.md) for detailed documentation
2. Clear cache: Settings → Advanced Options → Clear Cache
3. Restart the app: `streamlit run admin_app.py`
4. Check secrets: Verify `.streamlit/secrets.toml` format
5. Verify database: Check Supabase dashboard connection

---

## 🎊 You're All Set!

You now have a powerful admin dashboard to manage all your VIT Counselling Predictor data.

**Key Features:**
- ✅ Full CRUD operations
- ✅ Bulk import/export
- ✅ Analytics & insights
- ✅ Report management
- ✅ Secure authentication

Happy managing! 🚀
