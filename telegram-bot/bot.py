import os
import json
import time
import random
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.types import BotCommand, BotCommandScopeDefault
from aiogram.dispatcher.filters import Command

USER_DATA_FILE = "/data/users_data.json"
CLAN_DATA_FILE = "/data/clans.json"
TOKEN = os.getenv("TOKEN")
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users_data = {}
clans = {}
SEASON_END = datetime(2025, 8, 15).timestamp()

def load_data():
    global users_data, clans
    if os.path.exists(USER_DATA_FILE):
        try:
            with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)
                users_data = {int(user_id): data for user_id, data in loaded_data.items()}
                for user_id, data in users_data.items():
                    data.setdefault("autoclicker", False)
                    data.setdefault("autoclicker_level", 0)
                    data.setdefault("case_bonus", 0)
                    data.setdefault("achievements", {
                        "clicker_novice": 0,
                        "case_master": 0,
                        "rich": 0,
                        "clan_hero": 0,
                        "lottery_magnate": 0,
                        "referral_leader": 0
                    })
                    data.setdefault("referrals", 0)
                    data.setdefault("daily_tasks", {
                        "clicks": 0,
                        "cases": 0,
                        "upgrade": 0,
                        "referral": 0,
                        "clan_clicks": 0,
                        "last_reset": 0
                    })
                    data.setdefault("daily_clicks", 0)
                    data.setdefault("clan_id", None)
                    data.setdefault("last_promo", 0)
                    data.setdefault("last_click_time", 0)
                    data.setdefault("last_lottery", 0)
                    data.setdefault("coins", 0)
                    data.setdefault("tag", None)
                    data.setdefault("click_booster", 0)
                    data.setdefault("last_message_text", "")
                    data.setdefault("last_reply_markup", None)
                    data.setdefault("clan_clicks_contributed", 0)
                    data.setdefault("cases_opened", 0)
                    data.setdefault("lottery_wins", 0)
                print(f"Данные пользователей загружены из {USER_DATA_FILE}. Пользователей: {len(users_data)}")
                save_data()
        except Exception as e:
            print(f"Ошибка при загрузке данных пользователей: {str(e)}")
            users_data = {}
    else:
        print(f"Файл {USER_DATA_FILE} не найден, начинаем с пустыми данными.")
        users_data = {}
        save_data()

    if os.path.exists(CLAN_DATA_FILE):
        try:
            with open(CLAN_DATA_FILE, "r", encoding="utf-8") as f:
                clans = json.load(f)
                for clan_id in clans:
                    clans[clan_id].setdefault("clan_clicks", 0)
                    clans[clan_id].setdefault("clan_tag", None)
                    clans[clan_id].setdefault("clan_booster", 0)
                    clans[clan_id].setdefault("clan_autoclicker", 0)
                print(f"Данные кланов загружены из {CLAN_DATA_FILE}. Кланов: {len(clans)}")
                save_data()
        except Exception as e:
            print(f"Ошибка при загрузке данных кланов: {str(e)}")
            clans = {}
    else:
        print(f"Файл {CLAN_DATA_FILE} не найден, начинаем с пустыми данными.")
        clans = {}
        save_data()

def save_data():
    try:ееЕ
        os.makedirs("/data", exist_ok=True)
        with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
        with open(CLAN_DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(clans, f, ensure_ascii=False, indent=4)
        print(f"Данные сохранены в {USER_DATA_FILE} и {CLAN_DATA_FILE}")
    except Exception as e:
        print(f"Ошибка при сохранении данных: {str(e)}")

def get_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "clicks": 0,
            "username": None,
            "click_multiplier": 1,
            "upgrade_level": 0,
            "last_daily_reward": 0,
            "autoclicker": False,
            "case_bonus": 0,
            "achievements": {"clicker_novice": 0, "case_master": 0, "rich": 0},
            "referrals": 0,
            "daily_tasks": {"clicks": 0, "cases": 0, "upgrade": 0, "last_reset": 0},
            "daily_clicks": 0,
            "clan_id": None,
            "last_promo": 0,
            "last_click_time": 0,
            "last_message_text": "",
            "last_reply_markup": None
        }
        save_data()
    return users_data[user_id]

def get_clan(clan_id):
    if clan_id not in clans:
        clans[clan_id] = {"name": clan_id, "clicks": 0, "members": []}
        save_data()
    return clans[clan_id]

def get_upgrade_cost(user):
    return math.ceil(10 * (1.15 ** user["upgrade_level"]))  # Изменено с 1.5 на 1.15

def get_case_reward(case_type, case_bonus):
    rewards = {
        "common": [100, 500, 1000, 2000],
        "epic": [1000, 2500, 5000, 10000],
        "legendary": [5000, 10000, 25000, 50000]
    }
    weights = {
        "common": [0.40, 0.30, 0.20, 0.10 + case_bonus],
        "epic": [0.40, 0.30, 0.20, 0.10 + case_bonus],
        "legendary": [0.40, 0.30, 0.20, 0.10 + case_bonus]
    }
    return random.choices(rewards[case_type], weights[case_type], k=1)[0]

def get_progress_bar(progress, total, length=10):
    filled = int(length * progress / total)
    return "█" * filled + "□" * (length - filled)

def check_achievements(user):
    achievements = user["achievements"]
    rewards = []
    if achievements["clicker_novice"] < 100 and user["clicks"] >= 100:
        achievements["clicker_novice"] = 100
        user["clicks"] += 500
        rewards.append("🌟 Кликер-новичок: +500 кликов!")
    if achievements["case_master"] < 5 and user.get("cases_opened", 0) >= 5:
        achievements["case_master"] = 5
        user["clicks"] += 1000
        rewards.append("🎁 Мастер кейсов: +1000 кликов!")
    if achievements["rich"] < 5000 and user["clicks"] >= 5000:
        achievements["rich"] = 5000
        user["clicks"] += 2000
        rewards.append("💰 Богач: +2000 кликов!")
    return rewards

def reset_daily_tasks(user):
    current_time = time.time()
    if current_time - user["daily_tasks"]["last_reset"] >= 86400:
        user["daily_tasks"] = {"clicks": 0, "cases": 0, "upgrade": 0, "last_reset": current_time}
        save_data()

def get_main_keyboard(user_id):
    user = get_user(user_id)
    upgrade_cost = get_upgrade_cost(user)
    kb = InlineKeyboardBuilder()
    kb.button(text="🖱️ Клик ⚡", callback_data="click")
    kb.button(text="📊 Статистика 📈", callback_data="stats")
    kb.button(text="🏆 Лидерборд 🥇", callback_data="leaderboard")
    kb.button(text=f"🔧 Улучшение (+{user['upgrade_level'] + 2} за {upgrade_cost} 💎)", callback_data="upgrade")
    kb.button(text="🎁 Кейсы 🎉", callback_data="select_case")
    kb.button(text="🎈 Ежедневный приз 🎁", callback_data="daily_reward")
    kb.button(text="🏬 Магазин 🛒", callback_data="shop")
    kb.button(text="🏅 Достижения 🏆", callback_data="achievements")
    kb.button(text="🔑 Промокоды 🎟️", callback_data="promo")
    kb.button(text="👥 Клан 🤝", callback_data="clan")
    kb.button(text="📈 Активность 🔥", callback_data="activity")
    kb.adjust(2)
    return kb.as_markup()

async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Запустить бота 🚀"),
        BotCommand(command="/stats", description="Посмотреть свои клики 📊"),
        BotCommand(command="/leaderboard", description="Посмотреть рейтинг 🏆"),
        BotCommand(command="/referral", description="Получить реферальную ссылку 🔗"),
        BotCommand(command="/create_clan", description="Создать клан 👥"),
        BotCommand(command="/join_clan", description="Присоединиться к клану 🤝"),
        BotCommand(command="/promo", description="Ввести промокод 🎟️")
    ]
    await bot.set_my_commands(commands)

async def autoclicker_task(user_id):
    user = get_user(user_id)
    while user["autoclicker"]:
        user["clicks"] += 10
        if user["clan_id"]:
            get_clan(user["clan_id"])["clicks"] += 10
        save_data()
        await asyncio.sleep(10)

@dp.message_handler(commands=["start"])
async def start(message: Message):
    args = message.text.split()
    user = get_user(message.from_user.id)
    user["username"] = message.from_user.username or message.from_user.first_name
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        if referrer_id != message.from_user.id and referrer_id in users_data:
            users_data[referrer_id]["referrals"] += 1
            users_data[referrer_id]["clicks"] += 1000
            user["clicks"] += 1000
            save_data()
    save_data()
    user["last_message_text"] = ""
    user["last_reply_markup"] = None
    await message.answer(
        f"👋 Добро пожаловать в кликер! 🎮\n{'🌟 Сезон: двойные клики до 15 августа! 🌟' if time.time() < SEASON_END else ''}",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@dp.message(Command("stats"))
async def stats(message: Message):
    user = get_user(message.from_user.id)
    reset_daily_tasks(user)
    task_progress = user["daily_tasks"]
    achievement_text = (
        f"🏅 Достижения:\n"
        f"🌟 Кликер-новичок: {get_progress_bar(user['achievements']['clicker_novice'], 100)} {user['achievements']['clicker_novice']}/100\n"
        f"🎁 Мастер кейсов: {get_progress_bar(user.get('cases_opened', 0), 5)} {user.get('cases_opened', 0)}/5\n"
        f"💰 Богач: {get_progress_bar(user['clicks'], 5000)} {min(user['clicks'], 5000)}/5000"
    )
    message_text = (
        f"📊 <b>Твоя статистика</b> 📈\n"
        f"💎 Кликов: {user['clicks']}\n"
        f"🔧 Уровень улучшения: {user['upgrade_level']}\n"
        f"🖱️ Кликов за нажатие: +{user['click_multiplier']}\n"
        f"👥 Рефералов: {user['referrals']}\n"
        f"🤝 Клан: {clans[user['clan_id']]['name'] if user['clan_id'] else 'Нет'}\n"
        f"📋 <b>Задания</b>:\n"
        f"✅ Сделать 50 кликов: {task_progress['clicks']}/50 (+500 кликов)\n"
        f"🎁 Открыть 2 кейса: {task_progress['cases']}/2 (+1000 кликов)\n"
        f"🔧 Купить улучшение: {task_progress['upgrade']}/1 (+300 кликов)\n"
        f"{achievement_text}"
    )
    reply_markup = get_main_keyboard(message.from_user.id)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = reply_markup
    save_data()
    await message.answer(message_text, reply_markup=reply_markup)

@dp.message(Command("leaderboard"))
async def leaderboard(message: Message):
    if not users_data:
        await message.answer("📉 Лидерборд пуст, никто ещё не кликал! 😢")
        return
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]["clicks"], reverse=True)
    leaderboard_text = "🏆 <b>Лидерборд (Топ-5)</b> 🥇\n\n"
    for i, (user_id, data) in enumerate(sorted_users[:5], 1):
        leaderboard_text += f"{i}. {data['username'] or 'Аноним'}: {data['clicks']} кликов 💎\n"
    user = get_user(message.from_user.id)
    user["last_message_text"] = leaderboard_text
    user["last_reply_markup"] = None
    save_data()
    await message.answer(leaderboard_text)

@dp.message(Command("referral"))
async def referral(message: Message):
    user_id = message.from_user.id
    await message.answer(f"🔗 <b>Твоя реферальная ссылка</b>: t.me/YourBot?start=ref_{user_id}\nПриглашай друзей и получайте по 1000 кликов! 👥")

@dp.message(Command("create_clan"))
async def create_clan(message: Message):
    user = get_user(message.from_user.id)
    if user["clan_id"]:
        await message.answer("❌ Ты уже в клане! 😕")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажи название клана: /create_clan Название 📝")
        return
    clan_name = args[1]
    if clan_name in clans:
        await message.answer("❌ Клан с таким названием уже существует! 😢")
        return
    clans[clan_name] = {"name": clan_name, "clicks": 0, "members": [message.from_user.id]}
    user["clan_id"] = clan_name
    save_data()
    await message.answer(f"✅ Клан '{clan_name}' создан! 🎉")

@dp.message(Command("join_clan"))
async def join_clan(message: Message):
    user = get_user(message.from_user.id)
    if user["clan_id"]:
        await message.answer("❌ Ты уже в клане! 😕")
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажи название клана: /join_clan Название 📝")
        return
    clan_name = args[1]
    if clan_name not in clans:
        await message.answer("❌ Клан не найден! 😢")
        return
    clans[clan_name]["members"].append(message.from_user.id)
    user["clan_id"] = clan_name
    save_data()
    await message.answer(f"✅ Ты присоединился к клану '{clan_name}'! 🤝")

@dp.message(Command("promo"))
async def promo(message: Message):
    user = get_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажи промокод: /promo код 🎟️")
        return
    promo_code = args[1]
    current_time = time.time()
    cooldown = 86400
    if user["last_promo"] != 0 and (current_time - user["last_promo"]) < cooldown:
        remaining_time = int(cooldown - (current_time - user["last_promo"]))
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        await message.answer(
            f"⏳ Промокод можно использовать через {hours} ч {minutes} мин {seconds} сек! ⏰"
        )
        return
    if promo_code == "241122":
        user["clicks"] += 5000
        if user["clan_id"]:
            get_clan(user["clan_id"])["clicks"] += 5000
        user["last_promo"] = current_time
        rewards = check_achievements(user)
        save_data()
        message_text = f"🎉 Промокод активирован! +5000 кликов! 💎\nВсего кликов: {user['clicks']}"
        if rewards:
            message_text += "\n" + "\n".join(rewards)
        user["last_message_text"] = message_text
        user["last_reply_markup"] = get_main_keyboard(message.from_user.id)
        await message.answer(message_text, reply_markup=user["last_reply_markup"])
    else:
        await message.answer("❌ Неверный промокод! 😢")

@dp.callback_query(lambda c: c.data == "click")
async def handle_click(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    current_time = time.time()
    if current_time - user["last_click_time"] < 0.5:
        await callback_query.answer("⏳ Слишком быстро! Подожди немного. ⏰")
        return
    user["last_click_time"] = current_time
    multiplier = user["click_multiplier"] * (2 if time.time() < SEASON_END else 1)
    if user["clan_id"]:
        multiplier *= 1.1
    user["clicks"] += multiplier
    user["daily_clicks"] += multiplier
    user["daily_tasks"]["clicks"] += 1
    if user["daily_tasks"]["clicks"] >= 50 and user["daily_tasks"]["clicks"] <= 51:
        user["clicks"] += 500
        user["daily_tasks"]["clicks"] = 51
    if user["clan_id"]:
        get_clan(user["clan_id"])["clicks"] += multiplier
    rewards = check_achievements(user)
    save_data()
    message_text = f"🖱️ Клик! Всего кликов: {user['clicks']} 💎"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    if user["daily_tasks"]["clicks"] == 51:
        message_text += "\n🎯 Задание '50 кликов' выполнено! +500 кликов! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "stats")
async def handle_stats(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    reset_daily_tasks(user)
    achievement_text = (
        f"🏅 <b>Достижения</b>:\n"
        f"🌟 Кликер-новичок: {get_progress_bar(user['achievements']['clicker_novice'], 100)} {user['achievements']['clicker_novice']}/100\n"
        f"🎁 Мастер кейсов: {get_progress_bar(user.get('cases_opened', 0), 5)} {user.get('cases_opened', 0)}/5\n"
        f"💰 Богач: {get_progress_bar(user['clicks'], 5000)} {min(user['clicks'], 5000)}/5000"
    )
    message_text = (
        f"📊 <b>Твоя статистика</b> 📈\n"
        f"💎 Кликов: {user['clicks']}\n"
        f"🔧 Уровень улучшения: {user['upgrade_level']}\n"
        f"🖱️ Кликов за нажатие: +{user['click_multiplier']}\n"
        f"👥 Рефералов: {user['referrals']}\n"
        f"🤝 Клан: {clans[user['clan_id']]['name'] if user['clan_id'] else 'Нет'}\n"
        f"📋 <b>Задания</b>:\n"
        f"✅ Сделать 50 кликов: {user['daily_tasks']['clicks']}/50 (+500 кликов)\n"
        f"🎁 Открыть 2 кейса: {user['daily_tasks']['cases']}/2 (+1000 кликов)\n"
        f"🔧 Купить улучшение: {user['daily_tasks']['upgrade']}/1 (+300 кликов)\n"
        f"{achievement_text}"
    )
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "leaderboard")
async def handle_leaderboard(callback_query: CallbackQuery):
    if not users_data:
        message_text = "📉 Лидерборд пуст, никто ещё не кликал! 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        user = get_user(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]["clicks"], reverse=True)
    message_text = "🏆 <b>Лидерборд (Топ-5)</b> 🥇\n\n"
    for i, (user_id, data) in enumerate(sorted_users[:5], 1):
        message_text += f"{i}. {data['username'] or 'Аноним'}: {data['clicks']} кликов 💎\n"
    user = get_user(callback_query.from_user.id)
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "upgrade")
async def handle_upgrade(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    upgrade_cost = get_upgrade_cost(user)
    if user["clicks"] < upgrade_cost:
        message_text = f"❌ Недостаточно кликов! Нужно {upgrade_cost} кликов для улучшения. 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= upgrade_cost
    user["upgrade_level"] += 1
    user["click_multiplier"] = user["upgrade_level"] + 1
    user["daily_tasks"]["upgrade"] += 1
    if user["daily_tasks"]["upgrade"] == 1:
        user["clicks"] += 300
    rewards = check_achievements(user)
    save_data()
    message_text = f"🔧 Улучшение куплено! Теперь ты получаешь +{user['click_multiplier']} кликов за нажатие! 🚀"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    if user["daily_tasks"]["upgrade"] == 1:
        message_text += "\n🎯 Задание 'Купить улучшение' выполнено! +300 кликов! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "select_case")
async def handle_select_case(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    message_text = "🎁 <b>Выбери кейс</b> 🎉:"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="🎁 Обычный кейс (1000 кликов) 🟢", callback_data="case_common")
    reply_markup.button(text="🎁 Эпический кейс (5000 кликов) 🔵", callback_data="case_epic")
    reply_markup.button(text="🎁 Легендарный кейс (20000 кликов) 🟣", callback_data="case_legendary")
    reply_markup.button(text="⬅️ Назад", callback_data="back")
    reply_markup.adjust(1)
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data.startswith("case_"))
async def handle_case(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    case_type = callback_query.data.split("_")[1]
    case_costs = {"common": 1000, "epic": 5000, "legendary": 20000}
    case_cost = case_costs[case_type]
    if user["clicks"] < case_cost:
        message_text = f"❌ Недостаточно кликов! Нужно {case_cost} кликов для кейса. 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= case_cost
    user["cases_opened"] = user.get("cases_opened", 0) + 1
    user["daily_tasks"]["cases"] += 1
    if user["daily_tasks"]["cases"] == 2:
        user["clicks"] += 1000
    reward = get_case_reward(case_type, user["case_bonus"])
    user["clicks"] += reward
    if user["clan_id"]:
        get_clan(user["clan_id"])["clicks"] += reward
    rewards = check_achievements(user)
    save_data()

    # Анимация открытия кейса
    case_emojis = {"common": "🟢", "epic": "🔵", "legendary": "🟣"}
    await callback_query.message.edit_text(f"{case_emojis[case_type]} Открываем {case_type.capitalize()} кейс... 🎁")
    await asyncio.sleep(1)
    await callback_query.message.edit_text(f"{case_emojis[case_type]} Почти готово... ✨")
    await asyncio.sleep(1)
    message_text = f"{case_emojis[case_type]} Кейс {case_type.capitalize()} открыт! 🎉 Ты получил +{reward} кликов! 💎\nВсего кликов: {user['clicks']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    if user["daily_tasks"]["cases"] == 2:
        message_text += "\n🎯 Задание 'Открыть 2 кейса' выполнено! +1000 кликов! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
        user["last_message_text"] = message_text
        user["last_reply_markup"] = reply_markup
        save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "daily_reward")
async def handle_daily_reward(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    current_time = time.time()
    cooldown = 3600
    if user["last_daily_reward"] != 0 and (current_time - user["last_daily_reward"]) < cooldown:
        remaining_time = int(cooldown - (current_time - user["last_daily_reward"]))
        minutes, seconds = divmod(remaining_time, 60)
        message_text = f"⏳ Ежедневный приз будет доступен через {minutes} мин {seconds} сек! ⏰"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] += 500
    if user["clan_id"]:
        get_clan(user["clan_id"])["clicks"] += 500
    user["last_daily_reward"] = current_time
    rewards = check_achievements(user)
    save_data()
    message_text = f"🎈 Ежедневный приз получен! +500 кликов! 💎\nВсего кликов: {user['clicks']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "shop")
async def handle_shop(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    message_text = "🏬 <b>Магазин</b> 🛒:"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="🕰️ Автокликер (5000 кликов) ⚡", callback_data="buy_autoclicker")
    reply_markup.button(text="🎁 Бонус к кейсам +5% (3000 кликов) ✨", callback_data="buy_case_bonus")
    reply_markup.button(text="⬅️ Назад", callback_data="back")
    reply_markup.adjust(1)
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "buy_autoclicker")
async def buy_autoclicker(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user["autoclicker"]:
        message_text = "❌ Автокликер уже куплен! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    if user["clicks"] < 5000:
        message_text = "❌ Недостаточно кликов! Нужно 5000 кликов. 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= 5000
    user["autoclicker"] = True
    asyncio.create_task(autoclicker_task(callback_query.from_user.id))
    save_data()
    message_text = "🕰️ Автокликер куплен! +10 кликов каждые 10 секунд! ⚡"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "buy_case_bonus")
async def buy_case_bonus(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user["case_bonus"] >= 0.05:
        message_text = "❌ Бонус к кейсам уже куплен! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    if user["clicks"] < 3000:
        message_text = "❌ Недостаточно кликов! Нужно 3000 кликов. 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= 3000
    user["case_bonus"] = 0.05
    save_data()
    message_text = "🎁 Бонус к кейсам куплен! +5% к шансу больших наград! ✨"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "achievements")
async def handle_achievements(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    achievement_text = (
        f"🏅 <b>Достижения</b>:\n"
        f"🌟 Кликер-новичок: {get_progress_bar(user['achievements']['clicker_novice'], 100)} {user['achievements']['clicker_novice']}/100\n"
        f"🎁 Мастер кейсов: {get_progress_bar(user.get('cases_opened', 0), 5)} {user.get('cases_opened', 0)}/5\n"
        f"💰 Богач: {get_progress_bar(user['clicks'], 5000)} {min(user['clicks'], 5000)}/5000"
    )
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != achievement_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(achievement_text, reply_markup=reply_markup)
            user["last_message_text"] = achievement_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "promo")
async def handle_promo(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    message_text = "🔑 Введи промокод командой: /promo 241122\n(Доступно раз в 24 часа, даёт 5000 кликов) 🎟️"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "clan")
async def handle_clan(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user["clan_id"]:
        clan = get_clan(user["clan_id"])
        message_text = f"👥 <b>Клан</b>: {clan['name']} 🤝\n💎 Кликов клана: {clan['clicks']}\n👤 Участников: {len(clan['members'])}"
    else:
        message_text = "👥 Ты не в клане! Используй /create_clan или /join_clan. 😢"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "activity")
async def handle_activity(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not users_data:
        message_text = "📉 Лидерборд активности пуст! 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]["daily_clicks"], reverse=True)
    message_text = "📈 <b>Лидерборд активности (Топ-5)</b> 🔥:\n\n"
    for i, (user_id, data) in enumerate(sorted_users[:5], 1):
        message_text += f"{i}. {data['username'] or 'Аноним'}: {data['daily_clicks']} кликов за день 💎\n"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    message_text = "👋 Вернулся в главное меню! 🎮"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

async def reset_daily_clicks():
    while True:
        for user_id in users_data:
            users_data[user_id]["daily_clicks"] = 0
        sorted_users = sorted(users_data.items(), key=lambda x: x[1]["daily_clicks"], reverse=True)
        for i, (user_id, data) in enumerate(sorted_users[:3], 1):
            if i == 1:
                users_data[user_id]["clicks"] += 5000
            elif i == 2:
                users_data[user_id]["clicks"] += 3000
            elif i == 3:
                users_data[user_id]["clicks"] += 1000
        save_data()
        await asyncio.sleep(86400)

def main():
    load_data()
    dp.loop.create_task(set_bot_commands())
    for user_id in users_data:
        if users_data[user_id].get("autoclicker", False):
            dp.loop.create_task(autoclicker_task(user_id))
    for clan_id in clans:
        if clans[clan_id].get("clan_autoclicker", 0) > 0:
            dp.loop.create_task(clan_autoclicker_task(clan_id))
    dp.loop.create_task(reset_daily_clicks())

if name == "__main__":
    main()
    executor.start_polling(dp, skip_updates=True, timeout=30)
