from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
import asyncio
import random
from datetime import datetime, timedelta
import json
import os

# Замените на ваш токен от BotFather
TOKEN = '7682840058:AAGqMGgkFul-BsCwaR80R1cOR2hHUV8RK_U'

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Структура для хранения данных пользователей
users_data = {}

# Промокоды и их параметры
promo_codes = {
    '2134eg': {'stars': 15, 'activations': 30, 'used': 0},
    '230km': {'stars': 5, 'activations': 50, 'used': 0},
    'starsss2': {'stars': 15, 'activations': 52, 'used': 0}
}

# Путь к файлу для сохранения данных
DATA_FILE = 'users_data.json'

# Загрузка данных из файла
def load_data():
    global users_data, promo_codes
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            users_data = data.get('users', {})
            promo_codes = data.get('promos', promo_codes)

# Сохранение данных в файл
def save_data():
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump({
            'users': users_data,
            'promos': promo_codes
        }, f, ensure_ascii=False, indent=2)

# Создание клавиатуры главного меню
def get_main_keyboard():
    main_menu = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text="⭐ Заработать звезды"),
                KeyboardButton(text="👤 Профиль")
            ],
            [
                KeyboardButton(text="Ⓜ️ Промкод"),
                KeyboardButton(text="🎁 Ежедневный бонус")
            ],
            [
                KeyboardButton(text="📣 Реф ссылка"),
                KeyboardButton(text="➡️ Вывести звезды")
            ]
        ],
        resize_keyboard=True
    )
    return main_menu

# Инициализация данных пользователя
def init_user(user_id, username):
    if str(user_id) not in users_data:
        users_data[str(user_id)] = {
            'username': username,
            'balance': 0,
            'referrals': 0,
            'clicks_today': 0,
            'last_click_date': '',
            'last_bonus_date': '',
            'used_promos': [],
            'referred_by': None
        }
        save_data()

# Обработчик команды /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = str(message.from_user.id)
    username = message.from_user.username or str(user_id)
    
    # Проверяем, не зарегистрирован ли уже пользователь
    is_new_user = user_id not in users_data
    
    init_user(user_id, username)
    
    # Проверяем наличие реферальной ссылки
    args = message.text.split()
    if len(args) > 1 and is_new_user:
        ref_id = args[1]
        if ref_id != user_id and ref_id in users_data and users_data[user_id]['referred_by'] is None:
            users_data[user_id]['referred_by'] = ref_id
            users_data[ref_id]['referrals'] += 1
            users_data[ref_id]['balance'] += 2
            save_data()
            try:
                await bot.send_message(
                    ref_id,
                    f"📲 По твоей реферальной ссылке зарегистрировался\n@{username}\n\nНа твой баланс зачислено 2 ⭐️"
                )
            except Exception as e:
                print(f"Ошибка отправки уведомления рефереру: {e}")
    
    await message.answer(
        "👋 Добро пожаловать! \n\nВыберите действие в меню ниже:",
        reply_markup=get_main_keyboard()
    )

# Обработчик для кнопки "Заработать звезды"
@dp.message(lambda message: message.text == "⭐ Заработать звезды")
async def earn_stars(message: types.Message):
    user_id = str(message.from_user.id)
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    if users_data[user_id]['last_click_date'] != current_date:
        users_data[user_id]['clicks_today'] = 0
        users_data[user_id]['last_click_date'] = current_date
    
    if users_data[user_id]['clicks_today'] < 10:
        users_data[user_id]['balance'] += 0.2
        users_data[user_id]['clicks_today'] += 1
        save_data()
        await message.answer(
            f"✅ Вы заработали 0.2 ⭐️!\n"
            f"Осталось кликов сегодня: {10 - users_data[user_id]['clicks_today']}"
        )
    else:
        await message.answer("❌ Вы исчерпали дневной лимит кликов. Приходите завтра!")

# Обработчик для кнопки "Профиль"
@dp.message(lambda message: message.text == "👤 Профиль")
async def profile(message: types.Message):
    user_id = str(message.from_user.id)
    user_data = users_data[user_id]
    await message.answer(
        f"👤 Пользователь @{user_data['username']}\n\n"
        f"📊 Приглашено друзей за все время: {user_data['referrals']}\n\n"
        f"🏦 Баланс: {user_data['balance']} ⭐️"
    )

# Обработчик для кнопки "Ежедневный бонус"
@dp.message(lambda message: message.text == "🎁 Ежедневный бонус")
async def daily_bonus(message: types.Message):
    user_id = str(message.from_user.id)
    current_date = datetime.now().strftime('%Y-%m-%d')
    
    if users_data[user_id].get('last_bonus_date') != current_date:
        bonus = random.randint(2, 15)
        users_data[user_id]['balance'] += bonus
        users_data[user_id]['last_bonus_date'] = current_date
        save_data()
        await message.answer(
            f"🎁 Поздравляем!\n"
            f"Вы получили ежедневный бонус: {bonus} ⭐️\n"
            f"Приходите завтра за новым бонусом!"
        )
    else:
        next_bonus = datetime.now() + timedelta(days=1)
        next_bonus = next_bonus.replace(hour=0, minute=0, second=0, microsecond=0)
        hours_left = (next_bonus - datetime.now()).seconds // 3600
        minutes_left = ((next_bonus - datetime.now()).seconds % 3600) // 60
        
        await message.answer(
            f"⏳ Вы уже получили сегодняшний бонус!\n"
            f"Следующий бонус будет доступен через: {hours_left}ч {minutes_left}мин"
        )

# Обработчик для кнопки "Реф ссылка"
@dp.message(lambda message: message.text == "📣 Реф ссылка")
async def ref_link(message: types.Message):
    user_id = str(message.from_user.id)
    bot_info = await bot.get_me()
    bot_username = bot_info.username
    ref_link = f"https://t.me/{bot_username}?start={user_id}"
    
    await message.answer(
        f"🔗 Ваша реферальная ссылка:\n"
        f"{ref_link}\n\n"
        f"📊 Статистика рефералов:\n"
        f"👥 Приглашено: {users_data[user_id]['referrals']} чел.\n"
        f"💰 Заработано на рефералах: {users_data[user_id]['referrals'] * 2} ⭐️\n\n"
        f"ℹ️ За каждого приглашенного друга вы получаете 2 ⭐️"
    )

# Обработчик для кнопки "Вывести звезды"
@dp.message(lambda message: message.text == "➡️ Вывести звезды")
async def withdraw_stars(message: types.Message):
    user_id = str(message.from_user.id)
    balance = users_data[user_id]['balance']
    
    await message.answer(
        f"💫 Ваш текущный баланс: {balance} ⭐️\n\n"
        f"⚠️ Вывод звезд временно недоступен\n"
        f"📢 Следите за обновлениями в нашем канале: https://t.me/slavik_stars"
    )

# Загрузка данных при запуске
load_data()

# Функция запуска бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())