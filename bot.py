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
                     "*Welcome to My Hotel Bot*\n\nPress the button to book a room",
                     reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Make a Booking")
def book_room(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    for key, room in ROOMS.items():
        markup.add(types.InlineKeyboardButton(
            f"{room['emoji']} {room['name']} – {room['price']}",
            callback_data=f"room_{key}"))
    bot.send_message(message.chat.id, "Choose your room type:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("room_"))
def get_name(call):
    room_key = call.data.split("_")[1]
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Please send your full name:")
    bot.register_next_step_handler(call.message, get_phone, room_key)

def get_phone(message, room_key):
    name = message.text.strip()
    bot.send_message(message.chat.id, "Send your phone number (e.g. +2348012345678):")
    bot.register_next_step_handler(message, get_dates, room_key, name)

def get_dates(message, room_key, name):
    phone = message.text.strip()
    bot.send_message(message.chat.id, "Check-in date (e.g. 10 Dec 2025):")
    bot.register_next_step_handler(message, get_checkout, room_key, name, phone)

def get_checkout(message, room_key, name, phone):
    check_in = message.text.strip()
    bot.send_message(message.chat.id, "Check-out date (e.g. 15 Dec 2025):")
    bot.register_next_step_handler(message, confirm_booking, room_key, name, phone, check_in)

def confirm_booking(message, room_key, name, phone, check_in):
    check_out = message.text.strip()
    room = ROOMS[room_key]
    text = f"""*Booking Summary*

Name: {name}
Phone: {phone}
Room: {room['emoji']} {room['name']}
Price: {room['price']}
Check-in: {check_in}
Check-out: {check_out}

Correct?"""
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("Yes, confirm", callback_data=f"confirm_{room_key}"),
        types.InlineKeyboardButton("Cancel", callback_data="cancel")
    )
    bot.send_message(message.chat.id, text, reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_"))
def confirmed(call):
    bot.edit_message_text("Booking confirmed! We will contact you soon", call.message.chat.id, call.message.id)

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def cancelled(call):
    bot.edit_message_text("Booking cancelled.", call.message.chat.id, call.message.id)

print("Bot is starting...")
bot.infinity_polling()
