import os
import uvicorn
from fastapi import FastAPI, Request
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# قراءة المتغيرات السرية من بيئة السيرفر
TOKEN = os.getenv("TOKEN")
app = FastAPI()
bot = Bot(token=TOKEN)

# --- 1. دوال بوت تيليجرام الأساسية التي برمجناها سابقاً ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أهلاً بك في بوت ZEUS ROBERT لخدمات الـ iChancey ⚡")

# (يمكنك إضافة بقية دوال الأزرار والقوائم هنا)

# --- 2. مستقبل إشعارات الدفع (Webhook) من سيريتل كاش ---
@app.post("/api/syriatel/callback")
async def syriatel_callback(request: Request):
    data = await request.json()
    
    # البيانات الواردة من سيريتل كاش حسب توثيقهم
    transaction_id = data.get("transaction_id")
    amount = data.get("amount")
    status = data.get("status")
    user_telegram_id = data.get("user_id")  # الآيدي الذي أرسلته عند طلب الشحن

    if status == "SUCCESS" and user_telegram_id:
        # إرسال رسالة تهنئة وشحن الرصيد للمستخدم فوراً
text = f"✅ **تم شحن رصيدك بنجاح!**\n\n💰 المبلغ: `{amount}` ليرة سورية\n🔖 رقم العملية: `{transaction_id}`"
        await bot.send_message(chat_id=int(user_telegram_id), text=text, parse_mode="Markdown")
        return {"status": "success"}
        
    return {"status": "ignored"}

# تشغيل الخادم
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)
