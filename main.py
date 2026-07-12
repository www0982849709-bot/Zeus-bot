import os
import json
from fastapi import FastAPI, HTTPException
import gspread
from google.oauth2.service_account import Credentials
import requests
from apscheduler.schedulers.background import BackgroundScheduler
from contextlib import asynccontextmanager

# إعدادات جوجل شيت والصلاحيات
SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

def get_gc():
    creds_json_string = os.getenv("GOOGLE_CREDENTIALS")
    if not creds_json_string or not creds_json_string.strip():
        raise HTTPException(status_code=500, detail="متغير البيئة GOOGLE_CREDENTIALS غير موجود أو فارغ")
    try:
        creds_dict = json.loads(creds_json_string.strip())
        creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
        return gspread.authorize(creds)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في تحليل JSON أو الاعتمادات: {type(e).__name__} - {str(e)}")

# الثوابت الخاصة بالاتصال بالمنصة الخارجية وجوجل شيت
SPREADSHEET_ID = "1pDpFcMxRMJQkOTnx9rAlDtoRD-OjPeNddNafUf2iayQ"
API_BASE_URL = "https://apisyria.com/api/v1"
API_KEY = "9643d2da874acdf7a7f9219e41e3f19266a5ce3459c3834b4ed4ed61147e2594"
GSM_NUMBER = "0984519477"

def get_sheet():
    try:
        gc = get_gc()
        spreadsheet = gc.open_by_key(SPREADSHEET_ID)
        return spreadsheet.sheet1
    except Exception as e:
        error_msg = f"{type(e).__name__}: {str(e)}"
        if not str(e):
            error_msg = f"{type(e).__name__} (تأكد من مشاركة الشيت مع الـ client_email وصلاحية المحرر)"
        raise HTTPException(status_code=500, detail=f"خطأ في الاتصال بجوجل شيت: {error_msg}")

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
        raise Exception(f"خطأ من الخادم الخارجي [{response.status_code}]: {response.text}")
    
    try:
        result = response.json()
    except json.JSONDecodeError:
        raise Exception(f"استجابة غير صالحة من السيرفر: {response.text}")
    
    if not result.get("success", False):
        return 0
    
    items = result.get("data", {}).get("items", [])
    sheet = get_sheet()
    
    added_count = 0
    for tx in items:
        sheet.append_row([
            str(tx.get("transaction_no")),
            str(tx.get("date")),
            str(tx.get("from")),
            str(tx.get("to")),
            str(tx.get("amount"))
        ])
        added_count += 1
        
    return added_count

# دالة الجدولة التي تعمل في الخلفية
def background_sync_job():
    try:
        count = fetch_and_sync_transactions()
        print(f"المزامنة التلقائية نجحت.
        
