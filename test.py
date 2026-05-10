import gspread
import pandas as pd
from oauth2client.service_account import ServiceAccountCredentials

scope = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)

client = gspread.authorize(creds)

sheet = client.open("VIT Counselling Data Collection 2025 (Responses)").sheet1

data = sheet.get_all_records()

df = pd.DataFrame(data)

print(df.head())
