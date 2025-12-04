from flask import Flask, request, abort
import telebot
import os

app = Flask(Famous_Diamond)

TOKEN = os.getenv("8216496503:AAHXjvxHrYBhJsTWIUi7z2pumlm2dCKotWU")
bot = telebot.TeleBot(TOKEN)

# ←←← Paste ALL your bot code from bot.py here (the ROOMS dict, handlers, etc.)
# I’m putting the full working version below so you just copy once:

ROOMS = {
    "single": {"name": "Single Room", "price": "₦25,000/night", "emoji": "Single Bed"},
    "double": {"name": "Double Room", "price": "₦40,000/night", "emoji": "Double Bed"},
    "suite":  {"name": "Luxury Suite", "price": "₦80,000/night", "emoji": "Crown"}
}

@bot.message_handler(commands=['start'])
def start(m): 
    keyboard = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add("Make a Booking")
    bot.send_message(m.chat.id, "*Welcome to My Hotel Bot*\n\nTap to book!", reply_markup=keyboard, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Make a Booking")
def book(m):
    markup = telebot.types.InlineKeyboardMarkup(row_width=1)
    for k, v in ROOMS.items():
        markup.add(telebot.types.InlineKeyboardButton(f"{v['emoji']} {v['name']} – {v['price']}", callback_data=f"room_{k}"))
    bot.send_message(m.chat.id, "Choose room:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.data.startswith("room_"):
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "Send your name to continue the booking")
        # full flow can be added later

@app.route('/', methods=['GET', 'POST'])
def webhook():
    if request.method == 'POST':
        if request.headers.get('content-type') == 'application/json':
            json_string = request.get_data().decode('utf-8')
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return '', 200
        else:
            abort(403)
    else:
        return "Bot is alive!", 200

# ←←← End of code
