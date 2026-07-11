from fastapi import FastAPI, HTTPException
import gspread
from google.oauth2.service_account import Credentials
import requests

app = FastAPI()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
# بيانات الاعتمادات مباشرة كـ قاموس بايثون لتجنب خطأ الملف والـ JWT
creds_dict = {
  "type": "service_account",
  "project_id": "ichancy-bot-501002",
  "private_key_id": "9a6546e814f113f7bf99ee92af7ed5d46b25ba99",
  "private_key": "-----BEGIN PRIVATE KEY-----\nMIIEvgIBADANBgkqhkiG9w0BAQEFAASCBKgwggSkAgEAAoIBAQCanCt+4UMKWdyK\nq7ypaOE7sUTylW2Bl4ZCPu9z5tt4JWEL8BQ+y/RjmxDcDhPbeOwWUw5Jj2KZDJ6s\nFhnL+mfm1QzGJbS0ubiwFUHR+ESA8sztDt54c+W3ThviauugKBt/1XjFPN5N1rgO\nkp/p1tdiRyx7ag8C1S2MeAKzhKWjD7DMG1KLx2LDtT9Hd+T6XFtAnDPJOiz+MXzt\nwmNXpJSasR1UxVor7b45hsA60UA5WPS4a8eF298ywtgMFGhxbzHXdxL1K1iDliaL\nDPDGMenKdN5yqlgPULr6hUBQtB+p8CTZ/3DFhoiwrr8UXq8UzXSqbV3HjxvjDkUU\nhpZxqFuBAgMBAAECggEAAKRFSfGFZbWZxLmRvuJAjQ7fSmJ0YeVPGVdJhyGeJ5GA\nJZyJePk/umoaV893JaIK2Mzfck62CgyTXAN7d+1CISMhOnFNnrJmodR0wXpWTnKz\nhwhYxAc3HNumIfpvn+qKsq0gIzFtesU5XlYdc8sAedfxx1FZXpmj5sFYwYX7agHV\nAy9ZeImWCJgguelP8sA9N/bnEmjRyl8VsgQpL1nNZV2oVBRHIYQoi2LHXmN2dPRJ\nPIazdBBdYoyS98SxCdjDV5OHiluvF5tNlSINdHiId6rJ17F0cUvxQ1duISL0nXkJ\nlpt9HOGfnY7HjNQoS99nW9UMVJab+hFTJWKANKOTAQKBgQDKgLZafevj97UWx0z3\nplZXJwVYWN0bNbN3AHWt1xQoliC+jofyjjnzkGEVIb/D/KWfR6wqzVEjzNkAScFW\nNl52yCyrcLxFAOpfpPoBi+trRtwdRvYyAFKZrnKqjxiQO9blMfUUHlBHuSvqUN45\nJqVhm8r4e0oInVWaQFkkX/mvrQKBgQDDdHcs3c3ICfdi0RKWrjM4nT1pQ0oOx6sj\nAiQMjM+4GEc/BatTGptDj25etIVlQaX6UrCSltSpmMaIYMNAyG26vYd4kHU9lwE+\n9XnpFoWccXk3Tj9QpTf0y2uNsYcWjmz0slInmVerJjK6x4qyIyUIe22JZ57ldW/+\n3evy4PLFpQKBgCJRzBXsD2V0XsF8h4PVMf7VQyek79wjrsW1UzxiHi1+vA/vkgS+\nq/2mc32kWZ66m8sx13DtmRnLJt/QoC6fSkUxSbjIg2/iZtZM3H4Um5Jz0Ow5UZJJ\n0bXwBcj4NX6EVbhETjfZp1twe4vbpr3i2daAE9cm9fYdzBs3WqQ6i9OFAoGBAL1v\nwR4kMBGEz1fgKXMPjad+hwnh5QJkNZNtvMDJLX5RUaRce0vFity1RJTXxD56nUL8\KBU7yQxDfZCqsDO2zttiXM3WvTsfg16hDzKB2KfjN0gKN8WTDKPfEPQ5LyQGkMWt\nm4Cz18uS7zImul+jPn51GppFazUcWJsePlSd/87dAoGBAJPpJ+7u922U4C66299j\nfqVeCc9RPglJhyEs6GXJxeKG7TjcpOoeRkNKdDvy4C8yA2iVnaMzyZd2uPcfX5y1\nyGuDfob3/CP1o089E/14Xsk3kFFHHnNDKzPLqwFRVgyCBav9JBYy5FRBqk2CTtTn\nPtwFBqaXmvu/Fu0tcfiKfFzF\n-----END PRIVATE KEY-----\n",
  "client_email": "ichancy-manager@ichancy-bot-501002.iam.gserviceaccount.com",
  "client_id": "106763723367019413935",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/ichancy-manager%40ichancy-bot-501002.iam.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}

creds = Credentials.from_service_account_info(creds_dict, scopes=SCOPES)
gc = gspread.authorize(creds)
SPREADSHEET_NAME = "mydata"
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
        
