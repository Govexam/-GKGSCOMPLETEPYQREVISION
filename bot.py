import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask
import threading
import os
import time

# ==========================================
# 1. BOT SETTINGS
# ==========================================
# Aapka Token aur Secret Code set hai
BOT_TOKEN = "8665786518:AAHzrG19WCAu-AuTt1LZBeqm446eoV0n-zs"
bot = telebot.TeleBot(BOT_TOKEN)

SECRET_CODE = "dkstudio"
unlocked_users = set()

# Quiz Data (Official Polls ke limits: Question < 300 chars, Options < 100 chars)
courses_data = {
    "chap_1": {
        "title": "Chapter 1: BPSC AEDO F.L.T. 16 (FREE DEMO 🟢)",
        "is_free": True,
        "questions": [
            {
                "q": "Begum Khaleda Zia, Bangladesh's first female PM, passed away. How many times did she serve as PM?",
                "options": ["Three times", "Five times", "Twice", "None of these"],
                "ans": 0,
                "expl": "Served 3 terms: 1991–1996, 1996, and 2001–2006. \n\nJoin: @GKGSCOMPLETEPYQREVISION_bot"
            },
            {
                "q": "Indian PM Modi inaugurated 'Sacred Piprahwa Relics' exhibition. These belong to which religion?",
                "options": ["Buddhism", "Jain", "Sikh", "Hindu"],
                "ans": 0,
                "expl": "Piprahwa relics are bone fragments of Lord Buddha, found in UP. \n\nJoin: @GKGSCOMPLETEPYQREVISION_bot"
            }
        ]
    },
    "chap_2": {
        "title": "Chapter 2: K-4 Missile & Defense (PAID 🔴)",
        "is_free": False,
        "questions": [
            {
                "q": "Identify the correct statement about 'K-4' missile:\nI. Range > 3500 km\nII. Nuclear-capable SLBM\nIII. Developed with Russia",
                "options": ["Only I", "I and II", "Only III", "All of the above"],
                "ans": 1,
                "expl": "K-4 is indigenously developed by India's DRDO, not with Russia. \n\nJoin: @GKGSCOMPLETEPYQREVISION_bot"
            },
            {
                "q": "Which country recently became the first to formally recognize Somaliland as an independent nation?",
                "options": ["Syria", "India", "Somalia", "Israel"],
                "ans": 3,
                "expl": "Israel is noted for specific diplomatic recognition in current affairs context. \n\nJoin: @GKGSCOMPLETEPYQREVISION_bot"
            }
        ]
    }
}

# User progress track karne ke liye
user_quiz_state = {}

# ==========================================
# 2. DUMMY WEB SERVER (For Render 24/7)
# ==========================================
app = Flask(__name__)

@app.route('/')
def home():
    return "Official Quiz Bot is Live & Running! 🎉"

# ==========================================
# 3. BOT LOGIC (OFFICIAL QUIZ MODE)
# ==========================================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    chat_id = message.chat.id
    
    # Reset user state on start
    if chat_id in user_quiz_state:
        del user_quiz_state[chat_id]

    welcome_text = (
        "🤖 *Welcome to Official BPSC Quiz Bot!*\n\n"
        "Yahan aapko asli Telegram Quiz experience milega (Fawara animation ke saath).\n\n"
        "🟢 *Chapter 1* bilkul FREE hai.\n"
        "🔒 *Paid Chapters* unlock karne ke liye apna Access Code bhejein (Example: `dkstudio`)."
    )
    
    markup = InlineKeyboardMarkup(row_width=1)
    for chap_id, chap_info in courses_data.items():
        icon = "🟢" if chap_info['is_free'] else ("📖" if chat_id in unlocked_users else "🔒")
        btn = InlineKeyboardButton(f"{icon} {chap_info['title']}", callback_data=f"menu_{chap_id}")
        markup.add(btn)
        
    bot.send_message(chat_id, welcome_text, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    chat_id = message.chat.id
    text = message.text.strip().lower()
    
    if text == SECRET_CODE.lower():
        unlocked_users.add(chat_id)
        bot.send_message(chat_id, "✅ *Success!* Pura course unlock ho gaya hai.\nAb /start dabayein aur paid chapters shuru karein.", parse_mode="Markdown")
    else:
        bot.send_message(chat_id, "❌ *Invalid Code!* Sahi code type karein ya Admin se sampark karein.")

@bot.callback_query_handler(func=lambda call: call.data.startswith("menu_"))
def handle_menu(call):
    chat_id = call.message.chat.id
    chap_id = call.data.split("_")[1]
    
    # Check Access
    if not courses_data[chap_id]["is_free"] and chat_id not in unlocked_users:
        bot.send_message(chat_id, "🔒 *Chapter Locked!*\nIse access karne ke liye Access Code bhejein.", parse_mode="Markdown")
        return

    # Start Quiz State
    user_quiz_state[chat_id] = {"chap": chap_id, "q_idx": 0}
    bot.send_message(chat_id, f"🚀 *Starting {courses_data[chap_id]['title']}...*", parse_mode="Markdown")
    send_next_poll(chat_id)

def send_next_poll(chat_id):
    state = user_quiz_state.get(chat_id)
    if not state: return
    
    chap_id = state["chap"]
    q_idx = state["q_idx"]
    questions = courses_data[chap_id]["questions"]
    
    if q_idx < len(questions):
        q = questions[q_idx]
        
        # ASLI TELEGRAM POLL (Quiz Mode)
        # Isse 'Confetti' animation khud aayega
        bot.send_poll(
            chat_id=chat_id,
            question=f"Q{q_idx+1}: {q['q']}",
            options=q["options"],
            type='quiz',
            correct_option_id=q["ans"],
            explanation=q["expl"],
            is_anonymous=False # Progress track karne ke liye false hona chahiye
        )
    else:
        # Result and Demo prompt
        is_free = courses_data[chap_id]["is_free"]
        msg = "🏁 *Quiz Khatam!*"
        if is_free and chat_id not in unlocked_users:
            msg += "\n\nAgar demo pasand aaya toh pura course unlock karne ke liye code `dkstudio` bhejein."
        
        bot.send_message(chat_id, msg + "\n\nJoin: @GKGSCOMPLETEPYQREVISION_bot", parse_mode="Markdown")
        if chat_id in user_quiz_state:
            del user_quiz_state[chat_id]

# User jab poll par click karega, ye trigger hoga
@bot.poll_answer_handler(func=lambda answer: True)
def handle_poll_answer(answer):
    chat_id = answer.user.id
    state = user_quiz_state.get(chat_id)
    
    if state:
        # Agle sawal pe bhejna (1.5 second ka delay taki user result dekh sake)
        state["q_idx"] += 1
        time.sleep(1.5)
        send_next_poll(chat_id)

# ==========================================
# 4. STARTING THE ENGINE
# ==========================================
def run_bot():
    print("Bot is polling in Official Quiz Mode...")
    while True:
        try:
            bot.polling(none_stop=True, interval=0, timeout=20)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == "__main__":
    # Start Bot in Background
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.start()
    
    # Start Web Server for Render
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
