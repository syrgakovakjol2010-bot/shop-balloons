import asyncio
import json
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import WebAppInfo, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton

# --- НАСТРОЙКИ ---
TOKEN = "7748837798:AAEaG7rEddj5NiFtN8lF_sPReV0uab51HcY"
# Добавил нового админа в список
ADMIN_IDS = [5874406282, 5385396977, 6593284203]
# Ссылка на сайт (Витрину)
WEBAPP_URL = "https://syrgakovakjol2010-bot.github.io/shop-balloons/" 

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Функция для разделения тысяч пробелами
def format_price(value):
    try:
        return f"{int(value):,}".replace(",", " ")
    except:
        return value

# 1. ЗАПУСК БОТА
@dp.message(CommandStart())
async def start(message: types.Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🎈 Заказать баллоны", web_app=WebAppInfo(url=WEBAPP_URL))]],
        resize_keyboard=True
    )
    if message.from_user.id in ADMIN_IDS:
        await message.answer("Админ-панель активна. Ждем заказов!", reply_markup=kb)
    else:
        await message.answer("Привет! Нажми кнопку ниже, чтобы открыть магазин:", reply_markup=kb)

# 2. ПОЛУЧЕНИЕ ЗАКАЗА
@dp.message(F.content_type == types.ContentType.WEB_APP_DATA)
async def process_order(message: types.Message):
    data = json.loads(message.web_app_data.data)
    
    cart_text = ""
    for item in data.get('items'):
        cart_text += f"▫️ {item['name']} x {item['count']} шт.\n"

    total_pretty = format_price(data.get('total'))

    order_text = (
        f"🚨 <b>НОВЫЙ ЗАКАЗ!</b>\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🛒 <b>Корзина:</b>\n{cart_text}\n"
        f"💰 <b>Сумма:</b> {total_pretty} сом\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"🏙 <b>Город:</b> {data.get('city')}\n"
        f"🏠 <b>Адрес:</b> {data.get('address')}\n"
        f"🚪 <b>Кв/Этаж:</b> {data.get('kv')}\n"
        f"📞 <b>Телефон:</b> <code>{data.get('phone')}</code>\n"
        f"🚀 <b>Срочность:</b> {data.get('urgency')}\n"
        f"💳 <b>Оплата:</b> {data.get('payment')}\n"
        f"➖➖➖➖➖➖➖➖\n"
        f"👤 Клиент: @{message.from_user.username}"
    )

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📦 Взять в сборку", callback_data=f"step_assemble_{message.from_user.id}")]
    ])

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, order_text, parse_mode="HTML", reply_markup=kb)
        except:
            pass
            
    await message.answer("✅ <b>Ваш заказ принят!</b>\nОжидайте подтверждения.", parse_mode="HTML")

# --- СТАТУСЫ ---
@dp.callback_query(F.data.startswith("step_assemble_"))
async def step_assemble(callback: types.CallbackQuery):
    client_id = int(callback.data.split("_")[2])
    try:
        await bot.send_message(client_id, "⚙️ <b>Статус: Заказ собирается</b>\nМы готовим ваши баллоны.", parse_mode="HTML")
    except:
        pass
    new_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="🚚 Отправить курьера", callback_data=f"step_transit_{client_id}")]])
    await callback.message.edit_reply_markup(reply_markup=new_kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("step_transit_"))
async def step_transit(callback: types.CallbackQuery):
    client_id = int(callback.data.split("_")[2])
    try:
        await bot.send_message(client_id, "🚚 <b>Курьер выехал!</b>\nСкоро будем у вас. Держите телефон рядом.", parse_mode="HTML")
    except:
        pass
    new_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="📍 Курьер прибыл", callback_data=f"step_arrived_{client_id}")]])
    await callback.message.edit_reply_markup(reply_markup=new_kb)
    await callback.answer()

@dp.callback_query(F.data.startswith("step_arrived_"))
async def step_arrived(callback: types.CallbackQuery):
    client_id = int(callback.data.split("_")[2])
    client_kb = InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text="✅ Я получил заказ", callback_data=f"client_confirm_{client_id}")]])
    try:
        await bot.send_message(client_id, "📍 <b>Курьер прибыл!</b>\nВыходите к курьеру.\nНажмите кнопку, когда заберете заказ:", parse_mode="HTML", reply_markup=client_kb)
    except:
        pass
    await callback.message.edit_text(callback.message.text + "\n\n⏳ <i>Ждем клиента...</i>", parse_mode="HTML", reply_markup=None)
    await callback.answer()

@dp.callback_query(F.data.startswith("client_confirm_"))
async def client_confirm(callback: types.CallbackQuery):
    await callback.message.edit_text("✅ <b>Спасибо за заказ!</b>\nЖдем вас снова! 🎉", parse_mode="HTML", reply_markup=None)
    client_name = callback.from_user.full_name
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, f"✅ <b>Заказ успешно закрыт!</b>\nКлиент {client_name} подтвердил получение.", parse_mode="HTML")
        except:
            pass

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
