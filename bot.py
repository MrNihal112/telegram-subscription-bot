import os
import sqlite3
from datetime import datetime, timedelta, timezone

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise RuntimeError("BOT_TOKEN is not configured")

bot = Bot(token=TOKEN)
dp = Dispatcher()

db = sqlite3.connect("subscriptions.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS subscriptions (
    telegram_id INTEGER PRIMARY KEY,
    plan TEXT NOT NULL,
    started_at TEXT NOT NULL,
    expires_at TEXT NOT NULL
)
""")
db.commit()


PLANS = {
    "1":  {"name": "1 Day",  "price": 49,  "days": 1},
    "7":  {"name": "7 Days", "price": 149, "days": 7},
    "15": {"name": "15 Days", "price": 249, "days": 15},
    "30": {"name": "30 Days", "price": 399, "days": 30},
}


def main_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🛒 Purchase", callback_data="purchase")],
            [InlineKeyboardButton(text="👤 My Subscription", callback_data="status")]
        ]
    )


def plans_menu():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🟢 1 Day — ₹49", callback_data="plan_1")],
            [InlineKeyboardButton(text="🔵 7 Days — ₹149", callback_data="plan_7")],
            [InlineKeyboardButton(text="🟣 15 Days — ₹249", callback_data="plan_15")],
            [InlineKeyboardButton(text="🟠 30 Days — ₹399", callback_data="plan_30")],
            [InlineKeyboardButton(text="🔙 Back", callback_data="back")]
        ]
    )


@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "👋 Welcome!\n\n"
        "Choose an option below:",
        reply_markup=main_menu()
    )


@dp.callback_query(lambda c: c.data == "purchase")
async def purchase(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "🛒 Choose your subscription:",
        reply_markup=plans_menu()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("plan_"))
async def select_plan(callback: types.CallbackQuery):
    plan_id = callback.data.replace("plan_", "")
    plan = PLANS[plan_id]

    await callback.message.edit_text(
        f"📦 {plan['name']}\n"
        f"💰 Price: ₹{plan['price']}\n\n"
        f"Validity: {plan['days']} day(s)\n\n"
        "Payment integration will be connected here.",
        reply_markup=InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(
                    text=f"💳 Pay ₹{plan['price']}",
                    callback_data=f"pay_{plan_id}"
                )],
                [InlineKeyboardButton(
                    text="🔙 Back",
                    callback_data="purchase"
                )]
            ]
        )
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data.startswith("pay_"))
async def payment(callback: types.CallbackQuery):
    plan_id = callback.data.replace("pay_", "")
    plan = PLANS[plan_id]

    await callback.message.edit_text(
        f"💳 Payment\n\n"
        f"Plan: {plan['name']}\n"
        f"Amount: ₹{plan['price']}\n\n"
        "Payment gateway/QR will be connected here."
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "status")
async def subscription_status(callback: types.CallbackQuery):
    telegram_id = callback.from_user.id

    cursor.execute(
        "SELECT plan, started_at, expires_at FROM subscriptions WHERE telegram_id = ?",
        (telegram_id,)
    )

    row = cursor.fetchone()

    if not row:
        text = (
            "👤 My Subscription\n\n"
            "❌ No active subscription found."
        )
    else:
        plan, started_at, expires_at = row

        expiry = datetime.fromisoformat(expires_at)
        now = datetime.now(timezone.utc)

        if expiry > now:
            text = (
                "👤 My Subscription\n\n"
                f"📦 Plan: {plan}\n"
                f"📅 Started: {started_at}\n"
                f"⏳ Expires: {expires_at}\n"
                "✅ Status: Active"
            )
        else:
            text = (
                "👤 My Subscription\n\n"
                f"📦 Plan: {plan}\n"
                f"⏳ Expired: {expires_at}\n"
                "❌ Status: Expired"
            )

    await callback.message.edit_text(
        text,
        reply_markup=main_menu()
    )
    await callback.answer()


@dp.callback_query(lambda c: c.data == "back")
async def back(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👋 Welcome!\n\nChoose an option below:",
        reply_markup=main_menu()
    )
    await callback.answer()


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
