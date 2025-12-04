import telebot
from telebot import types
import os

TOKEN = os.getenv("8216496503:AAHXjvxHrYBhJsTWIUi7z2pumlm2dCKotWU")
bot = telebot.TeleBot(TOKEN)

ROOMS = {
    "single": {"name": "Single Room", "price": "₦25,000/night", "emoji": "Single Bed"},
    "double": {"name": "Double Room", "price": "₦40,000/night", "emoji": "Double Bed"},
    "suite":  {"name": "Luxury Suite", "price": "₦80,000/night", "emoji": "Crown"}
}

@bot.message_handler(commands=['start'])
def start(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(types.KeyboardButton("Make a Booking"))
    bot.send_message(message.chat.id,
                     "*Welcome to My Hotel Bot*\n\nTap the button to book a room",
                     reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Make a Booking")
def book_room(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for k, v in ROOMS.items():
        markup.add(types.InlineKeyboardButton(f"{v['emoji']} {v['name']} – {v['price']}", callback_data=f"room_{k}"))
    bot.send_message(message.chat.id, "Choose room type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda c: True)
def callback(c):
    if c.data.startswith("room_"):
        bot.answer_callback_query(c.id)
        bot.send_message(c.message.chat.id, "Send your full name:")
        bot.register_next_step_handler(c.message, lambda m: bot.send_message(m.chat.id, f"Thanks {m.text}! Booking flow coming soon"))
    # you’ll get full flow once this runs

print("Bot started successfully!")
bot.infinity_polling()
