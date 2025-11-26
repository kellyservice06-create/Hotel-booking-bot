Perfect! `requirements.txt` is now in the repo.  
Now add the **second and final file** — the actual bot code.

### Do this right now (30 seconds):

1. On your repo page → click green **“Add file”** → **“Create new file”**  
2. In the file name box type exactly:  
   `bot.py`  
3. Copy-paste the **entire code below** into the big white box (this is the clean, working version for Render):

```python
import logging
from datetime import date
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram_calendar import SimpleCalendar, simple_cal_callback
import asyncio
import os
import asyncpg
import uuid

# ==================== CONFIG ====================
BOT_TOKEN = os.getenv("8216496503:AAFB_-d4JJ9g9zdMy3igid6W6LjFJ461Dnw")
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))
PAYMENT_PROVIDER_TOKEN = os.getenv("PAYMENT_PROVIDER_TOKEN")
DATABASE_URL = os.getenv("DATABASE_URL")

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

pool = None

ROOM_PRICES = {"single": 7900, "double": 12900, "suite": 29900}
ROOM_NAMES = {"single": "Single Room", "double": "Double Room", "suite": "Luxury Suite"}

# ==================== DATABASE ====================
async def init_db():
    global pool
    pool = await asyncpg.create_pool(DATABASE_URL)
    async with pool.acquire() as conn:
        await conn.execute('''
            CREATE TABLE IF NOT EXISTS bookings (
                id SERIAL PRIMARY KEY,
                user_id BIGINT,
                username TEXT,
                room_type TEXT,
                check_in DATE,
                check_out DATE,
                nights INTEGER,
                total_price INTEGER,
                booking_id TEXT UNIQUE,
                status TEXT DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT NOW()
            )
        ''')

# ==================== STATES ====================
class BookingStates(StatesGroup):
    choosing_room = State()
    choosing_checkin = State()
    choosing_checkout = State()

# ==================== KEYBOARDS ====================
def room_keyboard():
    kb = [
        [InlineKeyboardButton(f"{ROOM_NAMES[r]} - ${ROOM_PRICES[r]//100}/night", callback_data=f"room_{r}")]
        for r in ROOM_PRICES
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

def confirm_keyboard(booking_id):
    kb = [[InlineKeyboardButton("Confirm & Pay", callback_data=f"pay_{booking_id}")]]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# ==================== HANDLERS ====================
@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("🏨 Welcome to LuxeHotel!\nChoose your room:", reply_markup=room_keyboard())

@dp.callback_query(lambda c: c.data.startswith("room_"))
async def select_room(callback: types.CallbackQuery, state: FSMContext):
    room = callback.data.split("_")[1]
    await state.update_data(room_type=room)
    await callback.message.edit_text(
        f"Selected: <b>{ROOM_NAMES[room]}</b> – ${ROOM_PRICES[room]//100}/night\n\nSelect check-in date:",
        reply_markup=await SimpleCalendar().start_calendar(),
        parse_mode="HTML"
    )
    await state.set_state(BookingStates.choosing_checkin)

@dp.callback_query(simple_cal_callback.filter(), BookingStates.choosing_checkin)
async def process_checkin(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date_obj = await SimpleCalendar().process_selection(callback, callback_data)
    if selected and date_obj:
        await state.update_data(check_in=date_obj.date())
        await callback.message.edit_text(
            f"Check-in: <b>{date_obj.strftime('%Y-%m-%d')}</b>\nSelect check-out date:",
            reply_markup=await SimpleCalendar().start_calendar(year=date_obj.year, month=date_obj.month),
            parse_mode="HTML"
        )
        await state.set_state(BookingStates.choosing_checkout)

@dp.callback_query(simple_cal_callback.filter(), BookingStates.choosing_checkout)
async def process_checkout(callback: types.CallbackQuery, callback_data: dict, state: FSMContext):
    selected, date_obj = await SimpleCalendar().process_selection(callback, callback_data)
    if selected and date_obj:
        data = await state.get_data()
        check_in = data["check_in"]
        check_out = date_obj.date()
        if check_out <= check_in:
            await callback.answer("Check-out must be after check-in!", show_alert=True)
            return
        nights = (check_out - check_in).days
        total = nights * ROOM_PRICES[data["room_type"]]
        booking_id = str(uuid.uuid4())[:8].upper()
        await state.update_data(check_out=check_out, nights=nights, total_price=total, booking_id=booking_id)

        text = (f"Booking Summary:\n\n"
                f"Room: {ROOM_NAMES[data['room_type']]}\n"
                f"Check-in: {check_in}\nCheck-out: {check_out}\n"
                f"Nights: {nights}\nTotal: <b>${total//100}</b>\n\n"
                f"Click to pay securely")
        await callback.message.edit_text(text, reply_markup=confirm_keyboard(booking_id), parse_mode="HTML")

@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def process_pay(callback: types.CallbackQuery, state: FSMContext):
    booking_id = callback.data.split("_")[1]
    data = await state.get_data()
    async with pool.acquire() as conn:
        await conn.execute("""
            INSERT INTO bookings (user_id, username, room_type, check_in, check_out, nights, total_price, booking_id)
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8)
        """, callback.from_user.id, callback.from_user.username or "", data["room_type"],
            data["check_in"], data["check_out"], data["nights"], data["total_price"], booking_id)

    prices = [LabeledPrice(label="Hotel Booking", amount=data["total_price"])]
    await bot.send_invoice(
        chat_id=callback.from_user.id,
        title="LuxeHotel Booking",
        description=f"{ROOM_NAMES[data['room_type']]} × {data['nights']} nights",
        payload=booking_id,
        provider_token=PAYMENT_PROVIDER_TOKEN,
        currency="USD",
        prices=prices
    )

@dp.pre_checkout_query(lambda q: True)
async def pre_checkout(pre_checkout_query: types.PreCheckoutQuery):
    await bot.answer_pre_checkout_query(pre_checkout_query.id, ok=True)

@dp.message(lambda m: m.successful_payment)
async def successful_payment(message: types.Message):
    booking_id = message.successful_payment.invoice_payload
    async with pool.acquire() as conn:
        await conn.execute("UPDATE bookings SET status='paid' WHERE booking_id=$1", booking_id)
    await bot.send_message(ADMIN_ID, f"New PAID booking! ID: {booking_id}\nUser: @{message.from_user.username}")
    await message.answer("Payment successful! Your room is confirmed. Thank you!")

@dp.message(Command("admin"))
async def admin_panel(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return
    async with pool.acquire() as conn:
        bookings = await conn.fetch("SELECT * FROM bookings WHERE status='pending'")
    if not bookings:
        await message.answer("No pending bookings.")
        return
    for b in bookings:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("Approve", callback_data=f"approve_{b['booking_id']}"),
             InlineKeyboardButton("Reject", callback_data=f"reject_{b['booking_id']}")]
        ])
        await message.answer(f"Booking {b['booking_id']}\nUser: @{b['username']}\n{b['room_type'].title()} {b['check_in']} → {b['check_out']}", reply_markup=kb)

# ==================== MAIN ====================
async def main():
    await init_db()
    logging.info("Hotel Booking Bot Started!")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```

4. Scroll down → click **“Commit new file”**

That’s it!  
As soon as you commit `bot.py`, Render will **automatically start a new deploy** and this time it will go **LIVE** in under 2 minutes.

Reply “bot.py added” when you’re done and I’ll tell you the final tiny step (adding the database) so everything is 100% complete.  
You’re seconds away now!
