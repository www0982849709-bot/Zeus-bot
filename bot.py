from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes, ConversationHandler
from telegram.request import HTTPXRequest
import gspread
import requests
from google.oauth2.service_account import Credentials
from datetime import datetime
import time

TOKEN = "8941277304:AAH_X0KCDmFw3May7Mv6V6VY26eSGJyWrdc"
ADMIN_ID = 7313571887
# --- إعدادات مسار الشحن الجديد ---
TX_NUMBER, AMOUNT = range(2)
WALLET_NUMBERS = "89066504\n66247745\n45562403\n27811785"
MIN_AMOUNT = 200

# --- إعدادات ربط جوجل شيت ---
CREDENTIALS_FILE = "credentials.json"
SHEET_NAME = "mydata"
WEBHOOK_URL = (
    "https://script.google.com/macros/s/AKfycbySVJe7fkZBNkX2iTCoCRLvT-hWxm0zk8_j4mT3emYKnU1-i7IuhagaT13nw7sbAQej/exec"
)

# تعريف client عالمي ليراه كل البوت
creds = Credentials.from_service_account_file(CREDENTIALS_FILE, scopes=[
    "https://www.googleapis.com/auth/spreadsheets", 
    "https://www.googleapis.com/auth/drive"
])
client = gspread.authorize(creds)

def add_transaction_to_sheet(user_id, username, action_type, method, amount, tx_info):
    try:
        sheet = client.open(SHEET_NAME).get_worksheet(1)
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        row_data = [current_time, user_id, f"@{username}" if username else "لا يوجد", action_type, method, amount, tx_info]
        sheet.append_row(row_data)
        return True
    except Exception as e:
        print(f"خطأ أثناء الاتصال بجوجل شيت: {e}")
        return False
def fetch_sms_from_sheet():
    try:
        sheet = client.open(SHEET_NAME).worksheet("SMS")  # أو اسم/رقم ورقة الـ SMS لديك
        return sheet.get_all_values()
    except Exception as e:
        print(f"خطأ أثناء قراءة شيت الـ SMS: {e}")
        return []

def register_user(user_id, username):
    try:
        users_sheet = client.open(SHEET_NAME).worksheet("Users")
        user_list = users_sheet.col_values(1) # جلب العمود الأول (الـ IDs)
        
        if str(user_id) not in user_list:
            current_date = datetime.now().strftime("%Y-%m-%d")
            users_sheet.append_row([str(user_id), f"@{username}" if username else "لا يوجد", "0", current_date])
            print(f"تم تسجيل مستخدم جديد: {username}")
        else:
            print(f"المستخدم {username} مسجل مسبقاً.")
    except Exception as e:
        print(f"خطأ في تسجيل المستخدم: {e}")

async def send_deposit_request(update, context, user_info):
    order_id = "DEP-" + str(user_info['user_id'])
    
    message = (
        f"🔔 **طلب شحن جديد!**\n"
        f"👤 المستخدم: {user_info['user_id']}\n"
        f"💵 المبلغ: {user_info['amount']} ل.س\n"
        f"📞 رقم المحفظة/التحويل: {user_info['phone_number']}\n"
        f"🔗 معرف الطلب: `{order_id}`"
    )
    
    keyboard = [
        [InlineKeyboardButton("✅ قبول", callback_data=f"approve_{order_id}")],
        [InlineKeyboardButton("❌ رفض", callback_data=f"reject_{order_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=message,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def send_withdraw_request(update, context, user_info):
    order_id = "ORD-" + str(user_info['user_id'])
    
    message = (
        f"🆕 **طلب سحب جديد:**\n"
        f"👤 المستخدم: {user_info['user_id']}\n"
        f"💰 المبلغ المطلوب: {user_info['amount']} ل.س\n"
        f"• قيمة الرسوم: {user_info['fees']} ل.س\n"
        f"• المبلغ بعد الخصم: {user_info['net_amount']} ل.س\n"
        f"📞 رقم العميل: {user_info['phone_number']}\n"
        f"📍 الحالة: ⏳ يحتاج مراجعة يدوية\n"
        f"🔗 معرف الطلب: `{order_id}`"
    )

    keyboard = [
        [InlineKeyboardButton("✅ الموافقة", callback_data=f"approve_{order_id}")],
        [InlineKeyboardButton("❌ الرفض", callback_data=f"reject_{order_id}")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await context.bot.send_message(chat_id=ADMIN_ID, text=message, reply_markup=reply_markup, parse_mode='Markdown')

# 1. قائمة الشروط والأحكام
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    user = update.effective_user
    register_user(user.id, user.username)
    
    terms_text = (
        "⚡️ **مرحباً بك في بوت ZEUS ROBERT** ⚡️\n\n"
        "📋 **شروط الخدمة والأحكام:**\n"
        "• نطاق الخدمة: البوت مخصص فقط لإنشاء وإدارة حسابات الشحن والسحب الفوري لخدمة ichancy.\n"
        "• حساب واحد فقط: إنشاء أكثر من حساب لنفس المستخدم يؤدي لحظر الحسابات.\n"
        "• يحق للإدارة إيقاف الدفع أو السحب مؤقتاً عند الاشتباه بالاحتيال.\n\n"
        "⚠️ باستخدامك للبوت، فأنت توافق على هذه الشروط."
    )
    keyboard = [
        [
            InlineKeyboardButton("✅ أوافق على الشروط", callback_data='accept_terms'),
            InlineKeyboardButton("❌ لا أوافق", callback_data='reject_terms')
        ],
        [InlineKeyboardButton("💬 انضم إلى مجموعتنا", url="https://t.me/zeusrobe")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    if update.message:
        await update.message.reply_text(terms_text, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(terms_text, reply_markup=reply_markup, parse_mode="Markdown")

# 2. القائمة الرئيسية
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    keyboard = [
        [InlineKeyboardButton("⚡ ichancy", callback_data='ichancy_menu'), InlineKeyboardButton("🎮 Golden Tree Fun", callback_data='golden_tree')],
        [InlineKeyboardButton("📥 سحب الرصيد", callback_data='withdraw_menu'), InlineKeyboardButton("💰 شحن الرصيد", callback_data='deposit_menu')],
        [InlineKeyboardButton("⏳ طلبات السحب المعلقة", callback_data='pending_withdrawals')],
        [InlineKeyboardButton("🤝 الإحالات", callback_data='referrals'), InlineKeyboardButton("💡 الأسئلة الشائعة", callback_data='faqs')],
        [InlineKeyboardButton("🔔 تواصل معنا", callback_data='contact_us'), InlineKeyboardButton("👨‍💼 التواصل مع الموظفين", callback_data='staff')],
        [InlineKeyboardButton("🎁 استرداد كود", callback_data='redeem_code'), InlineKeyboardButton("🎁 إهداء رصيد", callback_data='gift_balance')],
        [InlineKeyboardButton("🏆 شارك فوزك", callback_data='share_win')]
    ]
    if query.from_user.id == 7313571887:
        keyboard.append([InlineKeyboardButton("⚙️ لوحة الأدمن", callback_data='admin_panel')])

    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = "⚡️ **قائمة تحكم ZEUS ROBERT** ⚡️\n\n👇 اختر من الخيارات أدناه لبدء المعاملة الفورية لـ ichancy:"
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
# دالة عرض لوحة الأدمن الرئيسية
async def show_admin_panel(query_or_message, context):
    admin_keyboard = [
        [
            InlineKeyboardButton("🛠️ حساب الدعم", callback_data='admin_support'),
            InlineKeyboardButton("📢 رسالة جماعية", callback_data='admin_broadcast'),
            InlineKeyboardButton("📈 الإحصائيات", callback_data='admin_stats')
        ],
        [
            InlineKeyboardButton("💳 سحب شام كاش يدوي", callback_data='admin_manual_sham'),
            InlineKeyboardButton("📦 طلبات السحب المعلقة", callback_data='admin_pending_withdraws')
        ],
        [
            InlineKeyboardButton("👥 نسب الإحالات", callback_data='admin_referral_rates'),
            InlineKeyboardButton("⚙️ إدارة النسب", callback_data='admin_manage_rates'),
            InlineKeyboardButton("💱 حديث سعر الصرف", callback_data='admin_exchange_rate')
        ],
        [
            InlineKeyboardButton("🎯 توزيع أرباح الإحالة يدوياً", callback_data='admin_manual_ref_profit'),
            InlineKeyboardButton("🎁 العروض والبونسات", callback_data='admin_bonuses')
        ],
        [
            InlineKeyboardButton("📱 إدارة أرقام سيرياتيل", callback_data='admin_syriatel_mgmt'),
        ],
        [
            InlineKeyboardButton("🔒 إدارة عمليات الإيداع", callback_data='admin_deposits_mgmt'),
        ],
        [
            InlineKeyboardButton("👥 إدارة المستخدمين", callback_data='admin_users_mgmt'),
            InlineKeyboardButton("📄 كل العمليات", callback_data='admin_all_transactions')
        ],
        [
            InlineKeyboardButton("💰 رصيد شام كاش", callback_data='admin_sham_balance')
        ],
        [
            InlineKeyboardButton("🟢 تشغيل/إيقاف الشحن والسحب", callback_data='admin_toggle_financial'),
            InlineKeyboardButton("🔴 تشغيل/إيقاف البوت", callback_data='admin_toggle_bot')
        ],
        [
            InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_main')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(admin_keyboard)
    text = "⚙️ **لوحة الأدمن - التحكم الكامل**\n\nاختر القسم الذي تريد التعامل معه 👇"
    
    if hasattr(query_or_message, 'edit_message_text'):
        await query_or_message.edit_message_text(text, reply_markup=reply_markup, parse_mode="Markdown")
    else:
        await query_or_message.reply_text(text, reply_markup=reply_markup, parse_mode="Markdown")

# 3. معالجة أزرار القوائم
async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    back_to_main = [[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_main')]]
    
    if data == 'accept_terms' or data == 'back_to_main':
        await main_menu(update, context)
    elif data == 'reject_terms':
        await query.edit_message_text("❌ لم توافق على الشروط، لا يمكنك استخدام البوت الحالي.", reply_markup=None)
        
    elif data == 'ichancy_menu':
        ichancy_kb = [
            [InlineKeyboardButton("💵 رصيدي", callback_data='ichancy_balance'), InlineKeyboardButton("👤 حسابي", callback_data='ichancy_account')],
            [InlineKeyboardButton("🔄 تحويل رصيد للموقع", callback_data='transfer_to_site'), InlineKeyboardButton("📲 تحويل للبوت", callback_data='transfer_to_bot')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_main')]
        ]
        await query.edit_message_text("⚡**قائمة إدارة حسابك في ichancy**", reply_markup=InlineKeyboardMarkup(ichancy_kb))
        
    elif data == 'ichancy_account':
        account_info = "📝 **معلومات حساب كاشير ZEUS ROBERT الخاص بك:**\n\n👤 **اسم المستخدم:** `ZR_User_ichancy_bot`\n🔑 **كلمة المرور:** `ZR_Pass_123`\n🟢 **حالة الحساب:** مفعل وجاهز"
        await query.edit_message_text(account_info, reply_markup=InlineKeyboardMarkup(back_to_main), parse_mode="Markdown")

    elif data == 'deposit_menu':
        deposit_keyboard = [
            [InlineKeyboardButton("🇸🇾 Syriatel Cash", callback_data='dep_syriatel'), InlineKeyboardButton("🔹 ShamCash-SYP", callback_data='dep_sham')],
            [InlineKeyboardButton("🔶 Binance (USDT)", callback_data='dep_binance')],
            [InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_main')]
        ]
        await query.edit_message_text("💰 **قائمة شحن الرصيد**\n\nاختر وسيلة الدفع من القائمة أدناه 👇:", reply_markup=InlineKeyboardMarkup(deposit_keyboard), parse_mode="Markdown")

    elif data == 'admin_panel':
        await show_admin_panel(query, context)

    elif data.startswith('dep_'):
        sheet = client.open(SHEET_NAME).worksheet("Payment")
        rows = sheet.get_all_values()
        
        method_name = "غير موجود"
        account_info = "غير متوفر"
        
        for row in rows[1:]:
            if len(row) >= 2 and row[1].strip() == data.strip():
                method_name = row[0]
                account_info = row[2]
                break

        # حفظ بيانات الحالة في ذاكرة البوت قبل طلب السعر
        context.user_data['action_type'] = 'شحن'
        context.user_data['method'] = method_name
        context.user_data['state'] = 'WAITING_FOR_AMOUNT'
                
        timestamp = f"\n\u200b\n{time.time()}" 
        
        # زر العودة للقائمة الرئيسية
        back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data='back_to_main')]])
        
        # إرسال الرسالة المفصلة مع الزر
        await query.edit_message_text(
            text=(f"💰 **اخترت الشحن عبر: {method_name}**\n\n"
                  f"يرجى التحويل إلى الرقم التالي:\n`{account_info}`\n\n"
                  f"قم بكتابة المبلغ الذي قمت بتحويله :"),
            reply_markup=back_btn,
            parse_mode="Markdown"
        )

    # <-- ضع الكود هنا داخل دالة button_click وقبل دالة check_deposit_sms:
    elif data == 'deposit_menu':
        deposit_keyboard = [
            [
                InlineKeyboardButton("🇸🇾 Syriatel Cash", callback_data='dep_syriatel'),
                InlineKeyboardButton(" ShamCash-SYP", callback_data='dep_sham')
            ],
            [
                InlineKeyboardButton("◆ Binance (USDT)", callback_data='dep_binance')
            ],
            [
                InlineKeyboardButton("⬅️ العودة للقائمة الرئيسية", callback_data='back_to_main')
            ]
        ]
        await query.edit_message_text(
            text='💰 **قائمة شحن الرصيد**\n\nاختر وسيلة الدفع التي قمت بالتحويل عبرها لإرسال البيانات:',
            reply_markup=InlineKeyboardMarkup(deposit_keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith('dep_'):
        sheet = client.open(SHEET_NAME).worksheet('Payment')
        rows = sheet.get_all_values()
        
        method_name = "غير موجود"
        account_info = "غير متوفر"
        
        for row in rows[1:]:
            if len(row) >= 2 and row[1].strip() == data.strip():
                method_name = row[0]
                account_info = row[2]
                break
        # حفظ بيانات الحالة في ذاكرة البوت قبل طلب السعر
        context.user_data['action_type'] = 'شحن'
        context.user_data['method'] = method_name
        context.user_data['state'] = 'WAITING_FOR_AMOUNT'
        
        timestamp = f"\n\u200b\n{time.time()}"
        
        await query.edit_message_text(
            text=f"💰 **اختر الشحن عبر:** {method_name}\n\nيرجى التحويل إلى الرقم التالي:\n`{account_info}`\n\nقم بكتابة المبلغ الذي قمت بتحويله :",
            parse_mode="Markdown"
        )

    elif data.startswith('approve_'):
        order_id = data.replace('approve_', '')
        await query.edit_message_text(
            f"**تم قبول الطلب ({order_id})** ✅\nبنجاح.",
            parse_mode="Markdown"
        )
        
    elif data.startswith('reject_'):
        order_id = data.replace('reject_', '')
        await query.edit_message_text(
            f"**تم رفض الطلب ({order_id}).** ❌",
            parse_mode="Markdown"
        )
 
    async def check_deposit_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        # ... باقي الدالة كما هي ...

async def check_deposit_sms(update: Update, context: ContextTypes.DEFAULT_TYPE):
  query = update.callback_query
  if query:
    await query.answer()
    chat_id = query.message.chat_id
  else:
    chat_id = update.effective_chat.id

  await context.bot.send_message(
      chat_id=chat_id, text="⏳ جاري فحص أحدث رسائل التحويل في السجل..."
  )

  rows = fetch_sms_from_sheet()
  if not rows:
    await context.bot.send_message(
        chat_id=chat_id, text="❌ عذراً، لا توجد أي رسائل مسجلة حالياً."
    )
    return

  latest_sms = rows[-1][1]
  sms_time = rows[-1][0]

  await context.bot.send_message(
      chat_id=chat_id,
      text=(
          f"⏰ وقت الوصل: {sms_time}\n"
          f"✉️ محتوى الرسالة:\n<code>{latest_sms}</code>"
      ),
      parse_mode="HTML",
  )


# 4. استقبال النصوص المصلحة بالكامل لضمان عدم التداخل
async def handle_user_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_state = context.user_data.get('state')
    user_text = update.message.text
    user = update.message.from_user
    
    back_btn = InlineKeyboardMarkup([[InlineKeyboardButton("🔙 القائمة الرئيسية", callback_data='back_to_main')]])

    if user_state == 'WAITING_FOR_AMOUNT':
        context.user_data['amount'] = user_text
        context.user_data['state'] = 'WAITING_FOR_TX_INFO'
        
        action = context.user_data.get('action_type', 'شحن')
        if action == 'شحن':
            await update.message.reply_text("🔹 أرسل **رقم التحويل (أو رقم العملية)** لتأكيد العملية:")
        else:
            await update.message.reply_text(" أرسل رقم محفظتك الذي تريد استقبال الأموال عليه:")
        return # ضروري جداً للتوقف وانتظار الرسالة القادمة

    elif user_state == 'WAITING_FOR_TX_INFO':
        amount = context.user_data.get('amount')
        action_type = context.user_data.get('action_type', 'شحن')
        method = context.user_data.get('method', 'غير محدد')
        tx_info = user_text  # رقم العملية المرسل من المستخدم
        
        user_id = user.id
        username = user.username
        req_id = f"DEP-{user_id}"
        
        # فحص رسائل الـ SMS وجلب المطابقة (تخطي الصف الأول للـ Header)
        rows = fetch_sms_from_sheet()
        verified_sms = None
        if rows and len(rows) > 1:
            for row in rows[1:]:
                if len(row) > 1 and tx_info in row[1]:
                    verified_sms = row[1]
                    break
        
        # تجهيز بيانات الطلب للإرسال
        user_info = {
            'user_id': user_id,
            'amount': amount,
            'fees': 0,
            'net_amount': amount,
            'phone_number': tx_info,
            'req_id': req_id
        }
        
        # إضافة المعاملة إلى جوجل شيت (مرة واحدة فقط)
        success = add_transaction_to_sheet(user_id, username, action_type, method, amount, tx_info)
        
        if success:
            if action_type == 'شحن':
                await send_deposit_request(update, context, user_info)
            else:
                await send_withdraw_request(update, context, user_info)
        
        # الرد على المستخدم بناءً على مطابقة الـ SMS من عدمها
        if verified_sms:
            await update.message.reply_text(
                "✅ **تم استلام طلبك بنجاح و إضافة المبلغ إلى رصيدك في البوت!**\n\n"
                "تم استلام طلبك بنجاح، سيتم مراجعته واعتماده فوراً.",
                reply_markup=back_btn,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text(
                "✅ تم استلام طلبك بنجاح، سيتم مراجعته  .",
                reply_markup=back_btn,
                parse_mode="Markdown"
            )
        
        # مسح الذاكرة بعد انتهاء العملية بنجاح
        context.user_data.clear()

def main():
    local_request = HTTPXRequest(connect_timeout=60.0, read_timeout=60.0)
    application = Application.builder().token(TOKEN).request(local_request).build()
    application.add_handler(CommandHandler("check", check_deposit_sms))

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_click))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_user_input))
    print("🚀 بوت ZEUS ROBERT يعمل الآن ومستعد لاستلام المبالغ وأرقام التحويل لشيت جوجل...")
    application.run_polling()

if __name__ == '__main__':
    main()
