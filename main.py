from fastapi import FastAPI, HTTPException
import gspread
from google.oauth2.service_account import Credentials
import requests
import os
import json

app = FastAPI()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

# قراءة مفتاح الـ JSON من متغير البيئة بطريقة آمنة
creds_json_string = os.getenv("GOOGLE_CREDENTIALS_JSON")

if creds_json_string:
    # تنظيف النص وقراءته كـ JSON
    creds_dict = json.loads(creds_json_string.strip())
else:
    # قاموس افتراضي أو إيقاف في حال عدم وجوده
    raise Exception("متغير البيئة GOOGLE_CREDENTIALS_JSON غير موجود في المنصة")

creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
gc = gspread.authorize(creds)

SPREADSHEET_ID = "1pDpFcMxRMJQkOTnx9rAIDtoRD-OjPeNddNafUf2iayQ"
API_BASE_URL = "https://apisyria.com/api/v1"
API_KEY = "9643d2da874acdf7a7f9219e41e3f19266a5ce3459c3834b4ed4ed61147e2594"
GSM_NUMBER = "86623398"

def get_sheet():
    try:
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        return spreadsheet.sheet1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الاتصال بجوجل شيت: {str(e)}")
        
def fetch_and_sync_transactions():
    headers = {
        "X-Api-Key": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "resource": "syriatel",
        "action": "history",
        "gsm": GSM_NUMBER,
        "period": "7"
    }
    response = requests.get(API_BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception("فشل الاتصال بخدمة API")
    
    result = response.json()
    if not result.get("success"):
        return 0
    
    items = result.get("data", {}).get("items", [])
    sheet = get_sheet()
    
    added_count = 0
    for tx in items:
        tx_no = tx.get("transaction_no")
        date = tx.get("date")
        sender = tx.get("from")
        receiver = tx.get("to")
        amount = tx.get("amount")
        
        sheet.append_row([str(tx_no), str(date), str(sender), str(receiver), str(amount)])
        added_count += 1
        
    return added_count

@app.get("/sync-payments")
def sync_payments():
    try:
        count = fetch_and_sync_transactions()
        return {
            "status": "success",
            "message": f"تمت مزامنة {count} عملية بنجاح إلى جوجل شيت"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def home():
    return {"status": "online", "message": "سيرفر السكريبت يعمل بنجاح"}
    
