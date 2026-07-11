from fastapi import FastAPI, HTTPException
import gspread
from google.oauth2.service_account import Credentials
import requests

app = FastAPI()
import os
import json

# إعداد الصلاحيات للاتصال بجوجل شيت عبر متغير البيئة في Railway
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

creds_json = os.getenv("GOOGLE_CREDENTIALS_JSON")
if creds_json:
    creds_info = json.loads(creds_json)
    creds = Credentials.from_service_account_info(creds_info, scopes=SCOPES)
else:
    creds = Credentials.from_service_account_file("credentials.json", scopes=SCOPES)

gc = gspread.authorize(creds)

SPREADSHEET_NAME = "mydata"  # استبدل هذا باسم الشيت الخاص بك

# إعدادات API Syria (يمكنك وضعها هنا أو كمتغيرات بيئة)
API_BASE_URL = "https://apisyria.com/api/v1"
API_KEY = "9643d2da874acdf7a7f9219e41e3f19266a5ce3459c3834b4ed4ed61147e2594"       # ضع مفتاح الـ API الخاص بك هنا
GSM_NUMBER = "86623398"          # ضع رقم الموبايل أو كود الكاش هنا

def get_sheet():
    try:
        spreadsheet = gc.open(SPREADSHEET_NAME)
        return spreadsheet.sheet1
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"فشل الاتصال بملف جوجل شيت: {str(e)}")

# دالة لجلب العمليات الواردة من Syriatel Cash وتخزينها في جوجل شيت
def fetch_and_sync_transactions():
    headers = {
        "X-Api-Key": API_KEY,
        "Accept": "application/json"
    }
    params = {
        "resource": "syriatel",
        "action": "history",
        "gsm": GSM_NUMBER,
        "period": "7"  # جلب آخر 7 أيام
    }
    
    response = requests.get(API_BASE_URL, headers=headers, params=params)
    if response.status_code != 200:
        raise Exception("فشل الاتصال بخدمة API Syria")
        
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
        
        # يمكنك إضافة فحص بسيط للتأكد من عدم تكرار العملية قبل إضافتها
        # لإضافة البيانات للجدول: [رقم العملية، التاريخ، المرسل، المستلم، المبلغ]
        sheet.append_row([str(tx_no), str(date), str(sender), str(receiver), str(amount)])
        added_count += 1
        
    return added_count

@app.get("/sync-payments")
def sync_payments():
    try:
        count = fetch_and_sync_transactions()
        return {
            "status": "success", 
            "message": f"تمت مزامنة وإضافة {count} عملية جديدة إلى جوجل شيت بنجاح"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/")
def home():
    return {"status": "online", "message": "سيرفر السيريتل كاش وربط الـ API يعمل بنجاح"}
        
