import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Buat scope dan koneksi
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# URL spreadsheet
sheet_url = "https://docs.google.com/spreadsheets/d/1oWjMfSLm-L_3bgpop7YtUVTCgnTrdKYcmIivq-uXMzg/edit?usp=sharing"

# Ambil sheet
spreadsheet = client.open_by_url(sheet_url)
sheet = spreadsheet.sheet1

# Uji baca
print("Isi sel A1:", sheet.acell("A1").value)
