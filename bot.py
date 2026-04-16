import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import os
import time

# ==========================================
# 1. BOT SETTINGS
# ==========================================
# Aapka asli Token yahan set ho gaya hai
BOT_TOKEN = "8665786518:AAHzrG19WCAu-AuTt1LZBeqm446eoV0n-zs"
bot = telebot.TeleBot(BOT_TOKEN)

# Aapka Secret Code (Jo user ko denge Paid Course ke liye)
SECRET_CODE = "dkstudio"

# Jin users ne code daal diya hai, unka data yahan save rahega
unlocked_users = set()

# Aapke Chapters aur Questions yahan hain
courses_data = {
    "chap_1": {
        "title": "Chapter 1: BPSC AEDO F.L.T. 16 (FREE DEMO 🟢)",
        "is_free": True,
        "questions": [
            {
                "q": "Begum Khaleda Zia kitni baar Bangladesh ki PM rahi?",
                "options": ["3 Baar", "5 Baar", "2 Baar", "Inme se koi nahi"],
                "ans": 0,
                "expl": "Sahi Jawab: 3 Baar. (1991–1996, 1996, 2001–2006)\n@GKGSCOMPLETEPYQREVISION_bot"
            },
            {
                "q": "Bihar ka pehla vidyut sangrahalaya (power museum) kahan banega?",
                "options": ["Karbighhia", "Pataliputra", "Digha", "Gaya"],
                "ans": 0,
                "expl": "Sahi Jawab: Karbighhia thermal power station complex me.\n@GKGSCOMPLETEPYQREVISION_bot"
            }
        ]
    },
    "chap_2": {
        "title": "Chapter 2: K-4 Missile & Current Affairs (PAID 🔴)",
        "is_free": False,
        "questions": [
            {
                "q": "K-4 missile ki maar-kshamta (range) kitni hai?",
                "options": ["1500 km", "3500 km se adhik", "5000 km", "2000 km"],
                "ans": 1,
                "expl": "Sahi Jawab: 3500 km se adhik. Ye ek submarine-launched ballistic missile (SLBM) hai.\n@GKGSCOMPLETEPYQREVISION_bot"
            },
            {
                "q": "Haal hi me kis desh ne Somaliland ko swatantra rashtra ki manyata di?",
                "options": ["Syria", "India", "Somalia", "Israel"],
                "ans": 3,
                "expl": "Sahi Jawab: Israel.\n@GKGSCOMPLETEPYQREVISION_bot"
            }
        ]
    }
}

user_state = {}

# ==========================================
# 2. DUMMY WEB SERVER (Render ke liye zaruri hai taki error na aaye)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "BPSC Bot is running 24/7 successfully! 🔥 (Powered by GitHub & Render)"

# ==========================================
# 3. BOT KA LOGIC
# ==========================================
@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    welcome_text = (
        "📚 *BPSC Complete PYQ Course me aapka swagat hai!*\n\n"
        "🌟 *Naye users ke liye FREE DEMO uplabdh hai!* Niche 'Chapter 1' par click karke test try karein.\n\n"
        "*(Note: Paid chapters ko unlock karne ke liye apna 'Access Code' yahan chat me type karke bhejein)*"
    )
    markup = InlineKeyboardMarkup(row_width=1)
    for chap_id, chap_info in courses_data.items():
        icon = "🟢" if chap_info['is_free'] else ("📖" if chat_id in unlocked_users else "🔒")
        btn = InlineKeyboardButton(f"{icon} {chap_info['title']}", callback_data=f"start_{chap_id}")
        markup.add(btn)
    bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_messages(message):
    chat_id = message.chat.id
    user_text = message.text.strip().lower()
    
    if user_text == SECRET_CODE.lower():
        unlocked_users.add(chat_id)
        success_msg = "🎉 *Badhai ho!*\n\nAapka Access Code sahi hai aur *Pura Course UNLOCK* ho gaya hai! ✅\n\nKripya wapas /start type karein aur apne saare premium chapters padhna shuru karein."
        bot.send_message(chat_id, success_msg, parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ *Invalid Code!*\nAgar aapko Premium Course ka Access Code chahiye, toh kripya Admin se sampark karein.", parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: True)
def handle_query(call):
    chat_id = call.message.chat.id
    if call.data.startswith("start_"):
        chap_id = call.data.split("start_")[1]
        chap_info = courses_data[chap_id]
        
        # Check karna ki chapter paid toh nahi
        if not chap_info["is_free"] and chat_id not in unlocked_users:
            lock_msg = "🔒 *Ye Chapter PAID hai!*\n\nIse access karne ke liye apna Access Code chat me type karke bhejein.\n👉 *(Course kharidne ke liye admin se baat karein)*"
            bot.send_message(chat_id, lock_msg, parse_mode="Markdown")
            return
            
        user_state[chat_id] = {"current_chap": chap_id, "current_q": 0, "score": 0}
        send_question(chat_id)
        
    elif call.data.startswith("ans_"):
        selected_opt = int(call.data.split("_")[1])
        state = user_state.get(chat_id)
        
        if not state:
            bot.send_message(chat_id, "⏳ Test expire ho gaya. Kripya /start type karke wapas shuru karein.")
            return
            
        chap_id = state["current_chap"]
        current_q_index = state["current_q"]
        q_data = courses_data[chap_id]["questions"][current_q_index]
        
        # Jawab check karna
        if selected_opt == q_data["ans"]:
            state["score"] += 1
            bot.send_message(chat_id, "✅ *Sahi Jawab!*\n\n" + q_data["expl"], parse_mode="Markdown")
        else:
            bot.send_message(chat_id, "❌ *Galat Jawab!*\n\n" + q_data["expl"], parse_mode="Markdown")
        
        # Agla sawal
        state["current_q"] += 1
        if state["current_q"] < len(courses_data[chap_id]["questions"]):
            # Thoda delay dalte hain taki Telegram block na kare
            time.sleep(1)
            send_question(chat_id)
        else:
            show_result(chat_id)

def send_question(chat_id):
    state = user_state[chat_id]
    chap_id = state["current_chap"]
    q_index = state["current_q"]
    q_data = courses_data[chap_id]["questions"][q_index]
    
    markup = InlineKeyboardMarkup(row_width=1)
    for i, opt in enumerate(q_data["options"]):
        btn = InlineKeyboardButton(opt, callback_data=f"ans_{i}")
        markup.add(btn)
        
    chap_title = courses_data[chap_id]["title"]
    bot.send_message(chat_id, f"*{chap_title}*\n\n👉 Q{q_index + 1}: {q_data['q']}", reply_markup=markup, parse_mode="Markdown")

def show_result(chat_id):
    state = user_state[chat_id]
    score = state["score"]
    chap_id = state["current_chap"]
    total = len(courses_data[chap_id]["questions"])
    is_free = courses_data[chap_id]["is_free"]
    
    result_text = f"🎉 *TEST COMPLETED!* 🎉\n\n📝 Aapka Score: *{score} / {total}*\n\n"
    
    # Marketing Flow
    if is_free and chat_id not in unlocked_users:
        result_text += "💡 *Kaisa laga Demo Test?*\n\nPremium chapters (PAID 🔴) padhne ke liye apna *Access Code* (Jaise: dkstudio) yahan chat me bhejein.\n\n@GKGSCOMPLETEPYQREVISION_bot"
    else:
        result_text += "Dusra Chapter padhne ke liye wapas /start bhejein.\n\n@GKGSCOMPLETEPYQREVISION_bot"
        
    bot.send_message(chat_id, result_text, parse_mode="Markdown")

# ==========================================
# 4. STARTING THE SERVER & BOT
# ==========================================
def run_bot():
    print("Bot shuru ho gaya hai! Telegram par check karein...")
    # Polling me auto-retry lagaya hai taki server band na ho
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print("Error aaya:", e)
            time.sleep(5)

if __name__ == "__main__":
    # Bot ko background thread me chalayenge
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Web server ko main thread me chalayenge (Render ko yahi chahiye)
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
