# Next-Year Batch Setup

To show recommendations for a new junior batch later, keep records separated by
`data_year` and switch the public app through Streamlit secrets.

Example:

```toml
active_data_year = 2026
available_data_years = "2025,2026"
data_share_form_url = "https://forms.gle/your-new-form"

[data_share_form_urls]
2025 = "https://forms.gle/VG28i72zpKetFA4W6"
2026 = "https://forms.gle/your-new-form"
```

Notes:

- Put the new counselling spreadsheet in `data/` with the year in the filename,
  for example `VIT Counselling Data ( 2026 ).xlsx`.
- If the spreadsheet is not ready yet, the app can still run for that year using
  rows already uploaded/imported into Supabase or collected from the form.
- Admin year dropdowns include years from Supabase, local spreadsheets, and
  `available_data_years`.
