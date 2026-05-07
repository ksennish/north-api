import gspread
from google.oauth2.service_account import Credentials
import os, json
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_sheet(tab_name):
    sa_json = os.getenv("SERVICE_ACCOUNT_JSON")
    if sa_json:
        creds = Credentials.from_service_account_info(json.loads(sa_json), scopes=SCOPES)
    else:
        creds = Credentials.from_service_account_file("service_account.json", scopes=SCOPES)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(os.getenv("SPREADSHEET_ID"))
    return sheet.worksheet(tab_name)

def get_all_rows(tab_name):
    return get_sheet(tab_name).get_all_records()
