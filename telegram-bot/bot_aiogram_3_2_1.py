import asyncio
import math
import json
import os
import random
import time
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command
from aiogram.enums import ParseMode
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest

# Конфигурация
TOKEN = "8065777167:AAFQGwJHGoaXgFkt4DQq7veaMU7IPEWXwHk"  # Замените на ваш токен
USER_DATA_FILE = "users_data.json"
CLAN_DATA_FILE = "clans.json"
SEASON_END = datetime(2025, 8, 15).timestamp()

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Глобальные словари для хранения данных
users_data = {}
clans = {}

# Асинхронный лок для безопасного сохранения данных
save_lock = asyncio.Lock()

# Функции для работы с данными
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
                asyncio.create_task(save_data())  # Асинхронный вызов сохранения
        except Exception as e:
            print(f"Ошибка при загрузке данных пользователей: {str(e)}")
            users_data = {}
    else:
        print(f"Файл {USER_DATA_FILE} не найден, начинаем с пустыми данными.")
    
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
                asyncio.create_task(save_data())  # Асинхронный вызов сохранения
        except Exception as e:
            print(f"Ошибка при загрузке данных кланов: {str(e)}")
            clans = {}
    else:
        print(f"Файл {CLAN_DATA_FILE} не найден, начинаем с пустыми данными.")

async def save_data():
    async with save_lock:
        try:
            # Сериализация данных пользователей
            serializable_users_data = {str(k): v for k, v in users_data.items()}
            for user_id, data in serializable_users_data.items():
                if data.get("last_reply_markup") is not None:
                    data["last_reply_markup"] = None  # Удаляем несериализуемые объекты
            with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(serializable_users_data, f, ensure_ascii=False, indent=4)
            
            # Сериализация данных кланов
            with open(CLAN_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(clans, f, ensure_ascii=False, indent=4)
            
            print(f"Данные сохранены в {USER_DATA_FILE} и {CLAN_DATA_FILE}")
        except PermissionError as e:
            print(f"Ошибка прав доступа при сохранении данных: {str(e)}")
        except OSError as e:
            print(f"Ошибка ввода-вывода при сохранении данных: {str(e)}")
        except TypeError as e:
            print(f"Ошибка сериализации JSON: {str(e)}")
        except Exception as e:
            print(f"Неизвестная ошибка при сохранении данных: {str(e)}")

def get_user(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "clicks": 0,
            "coins": 0,
            "username": None,
            "click_multiplier": 1,
            "upgrade_level": 0,
            "last_daily_reward": 0,
            "autoclicker": False,
            "autoclicker_level": 0,
            "case_bonus": 0,
            "achievements": {
                "clicker_novice": 0,
                "case_master": 0,
                "rich": 0,
                "clan_hero": 0,
                "lottery_magnate": 0,
                "referral_leader": 0
            },
            "referrals": 0,
            "daily_tasks": {
                "clicks": 0,
                "cases": 0,
                "upgrade": 0,
                "referral": 0,
                "clan_clicks": 0,
                "last_reset": 0
            },
            "daily_clicks": 0,
            "clan_id": None,
            "last_promo": 0,
            "last_click_time": 0,
            "last_lottery": 0,
            "tag": None,
            "click_booster": 0,
            "clan_clicks_contributed": 0,
            "cases_opened": 0,
            "lottery_wins": 0,
            "last_message_text": "",
            "last_reply_markup": None
        }
        asyncio.create_task(save_data())  # Асинхронный вызов сохранения
    return users_data[user_id]

def get_clan(clan_id):
    if clan_id not in clans:
        clans[clan_id] = {
            "name": clan_id,
            "clan_clicks": 0,
            "members": [],
            "clan_tag": None,
            "clan_booster": 0,
            "clan_autoclicker": 0
        }
        asyncio.create_task(save_data())  # Асинхронный вызов сохранения
    return clans[clan_id]

def get_upgrade_cost(user):
    return math.ceil(10 * (1.15 ** user["upgrade_level"]))

def get_autoclicker_cost(user):
    return math.ceil(5000 * (1.2 ** user["autoclicker_level"]))

def get_clan_booster_cost(clan):
    return math.ceil(10000 * (1.3 ** (clan["clan_booster"] > time.time() and 1 or 0)))

def get_clan_autoclicker_cost(clan):
    return math.ceil(20000 * (1.5 ** clan["clan_autoclicker"]))

def get_case_reward(case_type, case_bonus):
    rewards = {
        "common": [(100, 1), (500, 2), (1000, 3), (2000, 5)],
        "epic": [(1000, 3), (2500, 5), (5000, 8), (10000, 10)],
        "legendary": [(5000, 5), (10000, 10), (25000, 15), (50000, 20)]
    }
    weights = {
        "common": [0.40, 0.30, 0.20, 0.10 + case_bonus],
        "epic": [0.40, 0.30, 0.20, 0.10 + case_bonus],
        "legendary": [0.40, 0.30, 0.20, 0.10 + case_bonus]
    }
    reward, coins = random.choices(rewards[case_type], weights=weights[case_type], k=1)[0]
    coin_drop = coins if random.random() < 0.5 else 0
    return reward, coin_drop

def get_lottery_reward():
    if random.random() < 0.5:
        return random.randint(2000, 5000), random.randint(2, 5)
    return 0, 0

def get_progress_bar(progress, total, length=10):
    filled = int(length * progress / total)
    return "█" * filled + "□" * (length - filled)

def check_achievements(user):
    achievements = user["achievements"]
    rewards = []
    if achievements["clicker_novice"] < 500 and user["clicks"] >= 500:
        achievements["clicker_novice"] = 500
        user["clicks"] += 1000
        user["coins"] += 5
        rewards.append("🌟 Кликер-новичок: +1000 кликов, +5 монет!")
    if achievements["case_master"] < 10 and user.get("cases_opened", 0) >= 10:
        achievements["case_master"] = 10
        user["clicks"] += 2000
        user["coins"] += 10
        rewards.append("🎁 Мастер кейсов: +2000 кликов, +10 монет!")
    if achievements["rich"] < 10000 and user["clicks"] >= 10000:
        achievements["rich"] = 10000
        user["clicks"] += 5000
        user["coins"] += 20
        rewards.append("💰 Богач: +5000 кликов, +20 монет!")
    if achievements["clan_hero"] < 1000 and user.get("clan_clicks_contributed", 0) >= 1000:
        achievements["clan_hero"] = 1000
        user["clicks"] += 3000
        user["coins"] += 15
        rewards.append("🤝 Клановый герой: +3000 кликов, +15 монет!")
    if achievements["lottery_magnate"] < 5 and user.get("lottery_wins", 0) >= 5:
        achievements["lottery_magnate"] = 5
        user["clicks"] += 4000
        user["coins"] += 20
        rewards.append("🎰 Лотерейный магнат: +4000 кликов, +20 монет!")
    if achievements["referral_leader"] < 3 and user["referrals"] >= 3:
        achievements["referral_leader"] = 3
        user["clicks"] += 3000
        user["coins"] += 15
        rewards.append("👥 Реферальный лидер: +3000 кликов, +15 монет!")
    return rewards

def reset_daily_tasks(user):
    current_time = time.time()
    if current_time - user["daily_tasks"]["last_reset"] >= 86400:
        user["daily_tasks"] = {
            "clicks": 0,
            "cases": 0,
            "upgrade": 0,
            "referral": 0,
            "clan_clicks": 0,
            "last_reset": current_time
        }
        user["daily_clicks"] = 0
        asyncio.create_task(save_data())  # Асинхронный вызов сохранения

def check_resources(user, clicks_needed=0, coins_needed=0, clan_clicks_needed=0):
    missing = []
    if clicks_needed > 0 and user["clicks"] < clicks_needed:
        missing.append(f"{clicks_needed} кликов, у тебя {user['clicks']}. Заработай ещё {clicks_needed - user['clicks']}!")
    if coins_needed > 0 and user["coins"] < coins_needed:
        missing.append(f"{coins_needed} монет, у тебя {user['coins']}. Заработай ещё {coins_needed - user['coins']}!")
    if clan_clicks_needed > 0 and user["clan_id"]:
        clan = get_clan(user["clan_id"])
        if clan["clan_clicks"] < clan_clicks_needed:
            missing.append(f"{clan_clicks_needed} клановых кликов, у клана {clan['clan_clicks']}. Заработай ещё {clan_clicks_needed - clan['clan_clicks']}!")
    return missing

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
    kb.button(text="🎰 Лотерея 🍀", callback_data="lottery")
    kb.button(text="📜 Описание игры ℹ️", callback_data="game_info")
    kb.button(text="🏅 Топ кланов 🏆", callback_data="clan_leaderboard")  # Новая кнопка для топа кланов
    kb.adjust(2)
    return kb.as_markup()

async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Запустить бота 🚀"),
        BotCommand(command="/stats", description="Посмотреть свои клики 📊"),
        BotCommand(command="/leaderboard", description="Посмотреть рейтинг игроков 🏆"),
        BotCommand(command="/clan_leaderboard", description="Посмотреть рейтинг кланов 🏅"),
        BotCommand(command="/referral", description="Получить реферальную ссылку 🔗"),
        BotCommand(command="/create_clan", description="Создать клан 👥"),
        BotCommand(command="/join_clan", description="Присоединиться к клану 🤝"),
        BotCommand(command="/promo", description="Ввести промокод 🎟️")
    ]
    await bot.set_my_commands(commands)

async def autoclicker_task(user_id):
    user = get_user(user_id)
    last_save_time = time.time()
    while user["autoclicker"]:
        clicks_per_cycle = 10 + 5 * (user["autoclicker_level"] - 1) if user["autoclicker_level"] > 0 else 0
        click_multiplier = 1.5 if user.get("click_booster", 0) > time.time() else 1.0
        user["clicks"] += clicks_per_cycle * click_multiplier
        user["daily_clicks"] += clicks_per_cycle * click_multiplier
        if user["clan_id"]:
            clan = get_clan(user["clan_id"])
            clan_clicks = clicks_per_cycle * 0.1 * (1.1 if clan["clan_booster"] > time.time() else 1.0)
            clan["clan_clicks"] += clan_clicks
            user["clan_clicks_contributed"] = user.get("clan_clicks_contributed", 0) + clan_clicks
            user["daily_tasks"]["clan_clicks"] += clan_clicks
            if user["daily_tasks"]["clan_clicks"] >= 500 and user["daily_tasks"]["clan_clicks"] <= 501:
                user["clicks"] += 1500
                user["coins"] += 8
                user["daily_tasks"]["clan_clicks"] = 501
        if time.time() - last_save_time >= 30:
            await save_data()
            last_save_time = time.time()
        await asyncio.sleep(10)

async def clan_autoclicker_task(clan_id):
    clan = get_clan(clan_id)
    last_save_time = time.time()
    while clan["clan_autoclicker"] > 0:
        clan["clan_clicks"] += 50 * clan["clan_autoclicker"]
        if time.time() - last_save_time >= 30:
            await save_data()
            last_save_time = time.time()
        await asyncio.sleep(10)

@dp.message(CommandStart())
async def start(message: Message):
    args = message.text.split()
    user = get_user(message.from_user.id)
    user["username"] = message.from_user.username or message.from_user.first_name
    if len(args) > 1 and args[1].startswith("ref_"):
        referrer_id = int(args[1].replace("ref_", ""))
        if referrer_id != message.from_user.id and referrer_id in users_data:
            referrer = get_user(referrer_id)
            referrer["referrals"] += 1
            referrer["daily_tasks"]["referral"] += 1
            referrer["clicks"] += 1000
            referrer["coins"] += 5
            user["clicks"] += 1000
            user["coins"] += 5
            if referrer["daily_tasks"]["referral"] == 1:
                referrer["clicks"] += 1000
                referrer["coins"] += 10
            await save_data()
    user["last_message_text"] = ""
    user["last_reply_markup"] = None
    await save_data()
    await message.answer(
        f"👋 Добро пожаловать в кликер! 🎮\n{'🌟 Сезон: двойные клики до 15 августа! 🌟' if time.time() < SEASON_END else ''}",
        reply_markup=get_main_keyboard(message.from_user.id)
    )

@dp.message(Command("stats"))
async def stats(message: Message):
    user = get_user(message.from_user.id)
    reset_daily_tasks(user)
    achievement_text = (
        f"🏅 <b>Достижения</b>:\n"
        f"🌟 Кликер-новичок: {get_progress_bar(user['achievements']['clicker_novice'], 500)} {user['achievements']['clicker_novice']}/500\n"
        f"🎁 Мастер кейсов: {get_progress_bar(user.get('cases_opened', 0), 10)} {user.get('cases_opened', 0)}/10\n"
        f"💰 Богач: {get_progress_bar(user['clicks'], 10000)} {min(user['clicks'], 10000)}/10000\n"
        f"🤝 Клановый герой: {get_progress_bar(user.get('clan_clicks_contributed', 0), 1000)} {min(user.get('clan_clicks_contributed', 0), 1000)}/1000\n"
        f"🎰 Лотерейный магнат: {get_progress_bar(user.get('lottery_wins', 0), 5)} {user.get('lottery_wins', 0)}/5\n"
        f"👥 Реферальный лидер: {get_progress_bar(user['referrals'], 3)} {user['referrals']}/3"
    )
    message_text = (
        f"📊 <b>Твоя статистика</b> 📈\n"
        f"💎 Кликов: {user['clicks']}\n"
        f"🪙 Монет: {user['coins']}\n"
        f"🔧 Уровень улучшения: {user['upgrade_level']}\n"
        f"🖱️ Кликов за нажатие: +{user['click_multiplier']}\n"
        f"🕰️ Уровень автокликера: {user['autoclicker_level']} (+{10 + 5 * (user['autoclicker_level'] - 1) if user['autoclicker_level'] > 0 else 0} кликов/10 сек)\n"
        f"👥 Рефералов: {user['referrals']}\n"
        f"🤝 Клан: {clans[user['clan_id']]['name'] if user['clan_id'] else 'Нет'}\n"
        f"📋 <b>Задания</b>:\n"
        f"✅ Сделать 100 кликов: {user['daily_tasks']['clicks']}/100 (+1000 кликов, +5 монет)\n"
        f"🎁 Открыть 3 кейса: {user['daily_tasks']['cases']}/3 (+2000 кликов, +10 монет)\n"
        f"🔧 Купить улучшение: {user['daily_tasks']['upgrade']}/1 (+500 кликов, +5 монет)\n"
        f"👥 Пригласить реферала: {user['daily_tasks']['referral']}/1 (+1000 кликов, +10 монет)\n"
        f"🤝 500 клановых кликов: {user['daily_tasks']['clan_clicks']}/500 (+1500 кликов, +8 монет)\n"
        f"{achievement_text}"
    )
    reply_markup = get_main_keyboard(message.from_user.id)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = reply_markup
    await save_data()
    await message.answer(message_text, reply_markup=reply_markup)

@dp.message(Command("leaderboard"))
async def leaderboard(message: Message):
    if not users_data:
        await message.answer("📉 Лидерборд пуст, никто ещё не кликал! 😢")
        return
    sorted_users = sorted(users_data.items(), key=lambda x: x[1]["clicks"], reverse=True)
    leaderboard_text = "🏆 <b>Лидерборд (Топ-5)</b> 🥇\n\n"
    for i, (user_id, data) in enumerate(sorted_users[:5], 1):
        clan_tag = f" ({clans[data['clan_id']]['name']})" if data["clan_id"] else ""
        tag = f" [{data['tag']}]" if data["tag"] else ""
        leaderboard_text += f"{i}. {data['username'] or 'Аноним'}{clan_tag}{tag}: {data['clicks']} кликов 💎\n"
    user = get_user(message.from_user.id)
    user["last_message_text"] = leaderboard_text
    user["last_reply_markup"] = get_main_keyboard(message.from_user.id)
    await save_data()
    await message.answer(leaderboard_text, reply_markup=user["last_reply_markup"])

@dp.message(Command("clan_leaderboard"))
async def clan_leaderboard(message: Message):
    if not clans:
        await message.answer("📉 Лидерборд кланов пуст, ни один клан не создан! 😢")
        return
    sorted_clans = sorted(clans.items(), key=lambda x: x[1]["clan_clicks"], reverse=True)
    leaderboard_text = "🏅 <b>Топ кланов (Топ-5)</b> 🏆\n\n"
    for i, (clan_id, data) in enumerate(sorted_clans[:5], 1):
        tag = f" [{data['clan_tag']}]" if data["clan_tag"] else ""
        members = ", ".join([users_data.get(mid, {}).get("username", "Аноним") for mid in data["members"]])
        leaderboard_text += f"{i}. {data['name']}{tag}: {data['clan_clicks']} клановых кликов 🤝\nУчастники: {members}\n"
    user = get_user(message.from_user.id)
    user["last_message_text"] = leaderboard_text
    user["last_reply_markup"] = get_main_keyboard(message.from_user.id)
    await save_data()
    await message.answer(leaderboard_text, reply_markup=user["last_reply_markup"])

@dp.message(Command("referral"))
async def referral(message: Message):
    user_id = message.from_user.id
    await message.answer(f"🔗 <b>Твоя реферальная ссылка</b>: t.me/kliknetbot?start=ref_{user_id}\nПриглашай друзей и получайте по 1000 кликов и 5 монет! 👥")

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
    clans[clan_name] = {
        "name": clan_name,
        "clan_clicks": 0,
        "members": [message.from_user.id],
        "clan_tag": None,
        "clan_booster": 0,
        "clan_autoclicker": 0
    }
    user["clan_id"] = clan_name
    user["clicks"] = 0  # Сбрасываем клики при создании клана для предотвращения бага
    user["daily_clicks"] = 0
    user["clan_clicks_contributed"] = 0
    await save_data()
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
    await save_data()
    await message.answer(f"✅ Ты присоединился к клану '{clan_name}'! 🤝")

@dp.message(Command("promo"))
async def promo(message: Message):
    user = get_user(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажи промокод: /promo код 🎟️")
        return
    promo_code = args[1].strip()
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
    valid_promos = {
        "241122": (5000, 10, 5000),
        "KLIKNET2025": (10000, 20, 10000),
        "CLANPOWER": (3000, 5, 3000)
    }
    if promo_code not in valid_promos:
        await message.answer("❌ Неверный промокод! 😢")
        return
    clicks, coins, clan_clicks = valid_promos[promo_code]
    user["clicks"] += clicks
    user["coins"] += coins
    if user["clan_id"]:
        get_clan(user["clan_id"])["clan_clicks"] += clan_clicks
    user["last_promo"] = current_time
    rewards = check_achievements(user)
    await save_data()
    message_text = f"🎉 Промокод активирован! +{clicks} кликов, +{coins} монет! 💎🪙\nВсего кликов: {user['clicks']}, монет: {user['coins']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = get_main_keyboard(message.from_user.id)
    await message.answer(message_text, reply_markup=user["last_reply_markup"])

@dp.callback_query(lambda c: c.data == "click")
async def handle_click(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    current_time = time.time()
    if current_time - user["last_click_time"] < 0.5:
        await callback_query.answer("⏳ Слишком быстро! Подожди немного. ⏰")
        return
    user["last_click_time"] = current_time
    multiplier = user["click_multiplier"] * (2 if time.time() < SEASON_END else 1) * (1.5 if user.get("click_booster", 0) > current_time else 1.0)
    if user["clan_id"]:
        multiplier *= 1.1
    user["clicks"] += multiplier
    user["daily_clicks"] += multiplier
    user["daily_tasks"]["clicks"] += 1
    if user["daily_tasks"]["clicks"] >= 100 and user["daily_tasks"]["clicks"] <= 101:
        user["clicks"] += 1000
        user["coins"] += 5
        user["daily_tasks"]["clicks"] = 101
    if user["clan_id"]:
        clan = get_clan(user["clan_id"])
        clan_clicks = multiplier * 0.1 * (1.1 if clan["clan_booster"] > time.time() else 1.0)
        clan["clan_clicks"] += clan_clicks
        user["clan_clicks_contributed"] = user.get("clan_clicks_contributed", 0) + clan_clicks
        user["daily_tasks"]["clan_clicks"] += clan_clicks
        if user["daily_tasks"]["clan_clicks"] >= 500 and user["daily_tasks"]["clan_clicks"] <= 501:
            user["clicks"] += 1500
            user["coins"] += 8
            user["daily_tasks"]["clan_clicks"] = 501
    rewards = check_achievements(user)
    await save_data()
    message_text = f"🖱️ Клик! Всего кликов: {user['clicks']} 💎, монет: {user['coins']} 🪙"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    if user["daily_tasks"]["clicks"] == 101:
        message_text += "\n🎯 Задание '100 кликов' выполнено! +1000 кликов, +5 монет! 🎉"
    if user["daily_tasks"]["clan_clicks"] == 501:
        message_text += "\n🎯 Задание '500 клановых кликов' выполнено! +1500 кликов, +8 монет! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
        f"🌟 Кликер-новичок: {get_progress_bar(user['achievements']['clicker_novice'], 500)} {user['achievements']['clicker_novice']}/500\n"
        f"🎁 Мастер кейсов: {get_progress_bar(user.get('cases_opened', 0), 10)} {user.get('cases_opened', 0)}/10\n"
        f"💰 Богач: {get_progress_bar(user['clicks'], 10000)} {min(user['clicks'], 10000)}/10000\n"
        f"🤝 Клановый герой: {get_progress_bar(user.get('clan_clicks_contributed', 0), 1000)} {min(user.get('clan_clicks_contributed', 0), 1000)}/1000\n"
        f"🎰 Лотерейный магнат: {get_progress_bar(user.get('lottery_wins', 0), 5)} {user.get('lottery_wins', 0)}/5\n"
        f"👥 Реферальный лидер: {get_progress_bar(user['referrals'], 3)} {user['referrals']}/3"
    )
    message_text = (
        f"📊 <b>Твоя статистика</b> 📈\n"
        f"💎 Кликов: {user['clicks']}\n"
        f"🪙 Монет: {user['coins']}\n"
        f"🔧 Уровень улучшения: {user['upgrade_level']}\n"
        f"🖱️ Кликов за нажатие: +{user['click_multiplier']}\n"
        f"🕰️ Уровень автокликера: {user['autoclicker_level']} (+{10 + 5 * (user['autoclicker_level'] - 1) if user['autoclicker_level'] > 0 else 0} кликов/10 сек)\n"
        f"👥 Рефералов: {user['referrals']}\n"
        f"🤝 Клан: {clans[user['clan_id']]['name'] if user['clan_id'] else 'Нет'}\n"
        f"📋 <b>Задания</b>:\n"
        f"✅ Сделать 100 кликов: {user['daily_tasks']['clicks']}/100 (+1000 кликов, +5 монет)\n"
        f"🎁 Открыть 3 кейса: {user['daily_tasks']['cases']}/3 (+2000 кликов, +10 монет)\n"
        f"🔧 Купить улучшение: {user['daily_tasks']['upgrade']}/1 (+500 кликов, +5 монет)\n"
        f"👥 Пригласить реферала: {user['daily_tasks']['referral']}/1 (+1000 кликов, +10 монет)\n"
        f"🤝 500 клановых кликов: {user['daily_tasks']['clan_clicks']}/500 (+1500 кликов, +8 монет)\n"
        f"{achievement_text}"
    )
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
                await save_data()
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
        clan_tag = f" ({clans[data['clan_id']]['name']})" if data["clan_id"] else ""
        tag = f" [{data['tag']}]" if data["tag"] else ""
        message_text += f"{i}. {data['username'] or 'Аноним'}{clan_tag}{tag}: {data['clicks']} кликов 💎\n"
    user = get_user(callback_query.from_user.id)
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "clan_leaderboard")
async def handle_clan_leaderboard(callback_query: CallbackQuery):
    if not clans:
        message_text = "📉 Лидерборд кланов пуст, ни один клан не создан! 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        user = get_user(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    sorted_clans = sorted(clans.items(), key=lambda x: x[1]["clan_clicks"], reverse=True)
    message_text = "🏅 <b>Топ кланов (Топ-5)</b> 🏆\n\n"
    for i, (clan_id, data) in enumerate(sorted_clans[:5], 1):
        tag = f" [{data['clan_tag']}]" if data["clan_tag"] else ""
        members = ", ".join([users_data.get(mid, {}).get("username", "Аноним") for mid in data["members"]])
        message_text += f"{i}. {data['name']}{tag}: {data['clan_clicks']} клановых кликов 🤝\nУчастники: {members}\n"
    user = get_user(callback_query.from_user.id)
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    missing = check_resources(user, clicks_needed=upgrade_cost)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
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
        user["clicks"] += 500
        user["coins"] += 5
    rewards = check_achievements(user)
    await save_data()
    message_text = f"🔧 Улучшение куплено! Теперь ты получаешь +{user['click_multiplier']} кликов за нажатие! 🚀"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    if user["daily_tasks"]["upgrade"] == 1:
        message_text += "\n🎯 Задание 'Купить улучшение' выполнено! +500 кликов, +5 монет! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    reply_markup.button(text="🎁 Эксклюзивный кейс (50 монет) ✨", callback_data="case_exclusive")
    reply_markup.button(text="⬅️ Назад", callback_data="back")
    reply_markup.adjust(1)
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    case_costs = {"common": (1000, 0), "epic": (5000, 0), "legendary": (20000, 0), "exclusive": (0, 50)}
    click_cost, coin_cost = case_costs[case_type]
    missing = check_resources(user, clicks_needed=click_cost, coins_needed=coin_cost)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= click_cost
    user["coins"] -= coin_cost
    user["cases_opened"] = user.get("cases_opened", 0) + 1
    user["daily_tasks"]["cases"] += 1
    if user["daily_tasks"]["cases"] == 3:
        user["clicks"] += 2000
        user["coins"] += 10
    reward, coin_drop = get_case_reward(case_type, user["case_bonus"]) if case_type != "exclusive" else (10000, 20)
    user["clicks"] += reward
    user["coins"] += coin_drop
    if user["clan_id"]:
        clan = get_clan(user["clan_id"])
        clan_clicks = reward * 0.1 * (1.1 if clan["clan_booster"] > time.time() else 1.0)
        clan["clan_clicks"] += clan_clicks
        user["clan_clicks_contributed"] = user.get("clan_clicks_contributed", 0) + clan_clicks
    rewards = check_achievements(user)
    await save_data()

    case_emojis = {"common": "🟢", "epic": "🔵", "legendary": "🟣", "exclusive": "✨"}
    await callback_query.message.edit_text(f"{case_emojis[case_type]} Открываем {case_type.capitalize()} кейс... 🎁")
    await asyncio.sleep(1)
    await callback_query.message.edit_text(f"{case_emojis[case_type]} Почти готово... ✨")
    await asyncio.sleep(1)
    message_text = f"{case_emojis[case_type]} Кейс {case_type.capitalize()} открыт! 🎉 Ты получил +{reward} кликов, +{coin_drop} монет! 💎🪙\nВсего кликов: {user['clicks']}, монет: {user['coins']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    if user["daily_tasks"]["cases"] == 3:
        message_text += "\n🎯 Задание 'Открыть 3 кейса' выполнено! +2000 кликов, +10 монет! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
        user["last_message_text"] = message_text
        user["last_reply_markup"] = reply_markup
        await save_data()
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
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] += 500
    user["coins"] += 5
    if user["clan_id"]:
        clan = get_clan(user["clan_id"])
        clan_clicks = 500 * 0.1 * (1.1 if clan["clan_booster"] > time.time() else 1.0)
        clan["clan_clicks"] += clan_clicks
        user["clan_clicks_contributed"] = user.get("clan_clicks_contributed", 0) + clan_clicks
    user["last_daily_reward"] = current_time
    rewards = check_achievements(user)
    await save_data()
    message_text = f"🎈 Ежедневный приз получен! +500 кликов, +5 монет! 💎🪙\nВсего кликов: {user['clicks']}, монет: {user['coins']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    autoclicker_cost = get_autoclicker_cost(user)
    message_text = "🏬 <b>Магазин</b> 🛒:"
    reply_markup = InlineKeyboardBuilder()
    if not user["autoclicker"]:
        reply_markup.button(text="🕰️ Автокликер (5000 кликов) ⚡", callback_data="buy_autoclicker")
    else:
        reply_markup.button(text=f"🕰️ Улучшить автокликер (+5 кликов/10 сек за {autoclicker_cost} 💎)", callback_data="upgrade_autoclicker")
    reply_markup.button(text="🎁 Бонус к кейсам +5% (3000 кликов) ✨", callback_data="buy_case_bonus")
    reply_markup.button(text="🏷️ Тег 'Богач' (50 монет) 💰", callback_data="buy_tag_rich")
    reply_markup.button(text="🚀 Бустер кликов +50% (30 монет, 1 час) ⚡", callback_data="buy_click_booster")
    reply_markup.button(text="⬅️ Назад", callback_data="back")
    reply_markup.adjust(1)
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    missing = check_resources(user, clicks_needed=5000)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
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
    user["autoclicker_level"] = 1
    asyncio.create_task(autoclicker_task(callback_query.from_user.id))
    await save_data()
    message_text = "🕰️ Автокликер куплен! +10 кликов каждые 10 секунд! ⚡"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "upgrade_autoclicker")
async def upgrade_autoclicker(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    autoclicker_cost = get_autoclicker_cost(user)
    missing = check_resources(user, clicks_needed=autoclicker_cost)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= autoclicker_cost
    user["autoclicker_level"] += 1
    user["daily_tasks"]["upgrade"] += 1
    if user["daily_tasks"]["upgrade"] == 1:
        user["clicks"] += 500
        user["coins"] += 5
    await save_data()
    clicks_per_cycle = 10 + 5 * (user["autoclicker_level"] - 1)
    message_text = f"🕰️ Автокликер улучшен до уровня {user['autoclicker_level']}! Теперь +{clicks_per_cycle} кликов каждые 10 секунд! ⚡"
    if user["daily_tasks"]["upgrade"] == 1:
        message_text += "\n🎯 Задание 'Купить улучшение' выполнено! +500 кликов, +5 монет! 🎉"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    missing = check_resources(user, clicks_needed=3000)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
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
    await save_data()
    message_text = "🎁 Бонус к кейсам куплен! +5% к шансу больших наград! ✨"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "buy_tag_rich")
async def buy_tag_rich(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user["tag"]:
        message_text = "❌ Тег уже куплен! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    missing = check_resources(user, coins_needed=50)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["coins"] -= 50
    user["tag"] = "Богач"
    await save_data()
    message_text = f"🏷️ Тег 'Богач' куплен! Теперь твой ник в лидерборде: @{user['username']} [Богач] 💰"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "buy_click_booster")
async def buy_click_booster(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    current_time = time.time()
    if user.get("click_booster", 0) > current_time:
        remaining_time = int(user["click_booster"] - current_time)
        minutes, seconds = divmod(remaining_time, 60)
        message_text = f"❌ Бустер уже активен! Доступен через {minutes} мин {seconds} сек! ⏰"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    missing = check_resources(user, coins_needed=30)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["coins"] -= 30
    user["click_booster"] = current_time + 3600
    await save_data()
    message_text = "🚀 Бустер кликов +50% куплен! Действует 1 час! ⚡"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "lottery")
async def handle_lottery(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    current_time = time.time()
    cooldown = 3600
    if user["last_lottery"] != 0 and (current_time - user["last_lottery"]) < cooldown:
        remaining_time = int(cooldown - (current_time - user["last_lottery"]))
        minutes, seconds = divmod(remaining_time, 60)
        message_text = f"⏳ Лотерея доступна через {minutes} мин {seconds} сек! ⏰"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    missing = check_resources(user, clicks_needed=1000)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    user["clicks"] -= 1000
    user["last_lottery"] = current_time
    reward, coin_drop = get_lottery_reward()
    if reward > 0:
        user["clicks"] += reward
        user["coins"] += coin_drop
        user["lottery_wins"] = user.get("lottery_wins", 0) + 1
        if user["clan_id"]:
            clan = get_clan(user["clan_id"])
            clan_clicks = reward * 0.1 * (1.1 if clan["clan_booster"] > time.time() else 1.0)
            clan["clan_clicks"] += clan_clicks
            user["clan_clicks_contributed"] = user.get("clan_clicks_contributed", 0) + clan_clicks
    rewards = check_achievements(user)
    await save_data()

    await callback_query.message.edit_text("🎰 Крутим барабан... 🍀")
    await asyncio.sleep(1)
    await callback_query.message.edit_text("🎰 Ещё чуть-чуть... ✨")
    await asyncio.sleep(1)
    message_text = f"🎰 Результат лотереи! {'Ты выиграл +'+str(reward)+' кликов, +'+str(coin_drop)+' монет! 💎🪙' if reward > 0 else 'Увы, ты проиграл. 😢'} Всего кликов: {user['clicks']}, монет: {user['coins']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
        user["last_message_text"] = message_text
        user["last_reply_markup"] = reply_markup
        await save_data()
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
    message_text = (
        f"🏅 <b>Достижения</b>:\n"
        f"🌟 Кликер-новичок: {get_progress_bar(user['achievements']['clicker_novice'], 500)} {user['achievements']['clicker_novice']}/500\n"f"🎁 Мастер кейсов: {get_progress_bar(user.get('cases_opened', 0), 10)} {user.get('cases_opened', 0)}/10\n"
        f"💰 Богач: {get_progress_bar(user['clicks'], 10000)} {min(user['clicks'], 10000)}/10000\n"
        f"🤝 Клановый герой: {get_progress_bar(user.get('clan_clicks_contributed', 0), 1000)} {min(user.get('clan_clicks_contributed', 0), 1000)}/1000\n"
        f"🎰 Лотерейный магнат: {get_progress_bar(user.get('lottery_wins', 0), 5)} {user.get('lottery_wins', 0)}/5\n"
        f"👥 Реферальный лидер: {get_progress_bar(user['referrals'], 3)} {user['referrals']}/3"
    )
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    if not user["clan_id"]:
        message_text = "🤝 <b>Клановое меню</b>:\nТы не в клане! Создай или присоединись к клану. Используй команды /create_clan или /join_clan"
        reply_markup = InlineKeyboardBuilder()
        reply_markup.button(text="Создать клан 📝", callback_data="create_clan")
        reply_markup.button(text="Присоединиться к клану 🔗", callback_data="join_clan")
        reply_markup.button(text="⬅️ Назад", callback_data="back")
        reply_markup.adjust(1)
    else:
        clan = get_clan(user["clan_id"])
        booster_cost = get_clan_booster_cost(clan)
        autoclicker_cost = get_clan_autoclicker_cost(clan)
        message_text = (
            f"🤝 <b>Клан: {clan['name']}</b>\n"
            f"👥 Участники: {', '.join([users_data.get(mid, {}).get('username', 'Аноним') for mid in clan['members']])}\n"
            f"💎 Клановые клики: {clan['clan_clicks']}\n"
            f"🏷️ Тег клана: {clan['clan_tag'] if clan['clan_tag'] else 'Нет'}\n"
            f"🚀 Бустер клана: {'Активен' if clan['clan_booster'] > time.time() else 'Неактивен'}\n"
            f"🕰️ Клановый автокликер: Уровень {clan['clan_autoclicker']} (+{50 * clan['clan_autoclicker']} кликов/10 сек)"
        )
        reply_markup = InlineKeyboardBuilder()
        reply_markup.button(text=f"🚀 Бустер клана (+10% за {booster_cost} клановых кликов, 1 час)", callback_data="buy_clan_booster")
        reply_markup.button(text=f"🕰️ Клановый автокликер (+50 кликов/10 сек за {autoclicker_cost} клановых кликов)", callback_data="buy_clan_autoclicker")
        reply_markup.button(text="🏷️ Купить тег клана (1000 клановых кликов)", callback_data="buy_clan_tag")
        reply_markup.button(text="🚪 Покинуть клан", callback_data="leave_clan")
        reply_markup.button(text="⬅️ Назад", callback_data="back")
        reply_markup.adjust(1)
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "create_clan")
async def handle_create_clan(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user["clan_id"]:
        message_text = "❌ Ты уже в клане! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    message_text = "📝 Введи название клана (отправь сообщение):"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="⬅️ Назад", callback_data="clan")
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()
    dp.register_message_handler(create_clan_message, content_types=types.ContentType.TEXT, state="*")

async def create_clan_message(message: Message):
    user = get_user(message.from_user.id)
    if user["clan_id"]:
        await message.answer("❌ Ты уже в клане! 😕", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clan_name = message.text.strip()
    if clan_name in clans:
        await message.answer("❌ Клан с таким названием уже существует! 😢", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clans[clan_name] = {
        "name": clan_name,
        "clan_clicks": 0,
        "members": [message.from_user.id],
        "clan_tag": None,
        "clan_booster": 0,
        "clan_autoclicker": 0
    }
    user["clan_id"] = clan_name
    user["clicks"] = 0
    user["daily_clicks"] = 0
    user["clan_clicks_contributed"] = 0
    await save_data()
    message_text = f"✅ Клан '{clan_name}' создан! 🎉"
    reply_markup = get_main_keyboard(message.from_user.id)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = reply_markup
    await message.answer(message_text, reply_markup=reply_markup)
    dp.message_handlers.unregister(create_clan_message)

@dp.callback_query(lambda c: c.data == "join_clan")
async def handle_join_clan(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if user["clan_id"]:
        message_text = "❌ Ты уже в клане! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    message_text = "🔗 Введи название клана (отправь сообщение):"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="⬅️ Назад", callback_data="clan")
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()
    dp.register_message_handler(join_clan_message, content_types=types.ContentType.TEXT, state="*")

async def join_clan_message(message: Message):
    user = get_user(message.from_user.id)
    if user["clan_id"]:
        await message.answer("❌ Ты уже в клане! 😕", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clan_name = message.text.strip()
    if clan_name not in clans:
        await message.answer("❌ Клан не найден! 😢", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clans[clan_name]["members"].append(message.from_user.id)
    user["clan_id"] = clan_name
    await save_data()
    message_text = f"✅ Ты присоединился к клану '{clan_name}'! 🤝"
    reply_markup = get_main_keyboard(message.from_user.id)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = reply_markup
    await message.answer(message_text, reply_markup=reply_markup)
    dp.message_handlers.unregister(join_clan_message)

@dp.callback_query(lambda c: c.data == "buy_clan_booster")
async def buy_clan_booster(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user["clan_id"]:
        message_text = "❌ Ты не в клане! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    clan = get_clan(user["clan_id"])
    booster_cost = get_clan_booster_cost(clan)
    missing = check_resources(user, clan_clicks_needed=booster_cost)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    clan["clan_clicks"] -= booster_cost
    clan["clan_booster"] = time.time() + 3600
    await save_data()
    message_text = f"🚀 Бустер клана куплен! +10% к клановым кликам на 1 час! ⚡"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "buy_clan_autoclicker")
async def buy_clan_autoclicker(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user["clan_id"]:
        message_text = "❌ Ты не в клане! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    clan = get_clan(user["clan_id"])
    autoclicker_cost = get_clan_autoclicker_cost(clan)
    missing = check_resources(user, clan_clicks_needed=autoclicker_cost)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    clan["clan_clicks"] -= autoclicker_cost
    clan["clan_autoclicker"] += 1
    asyncio.create_task(clan_autoclicker_task(user["clan_id"]))
    await save_data()
    message_text = f"🕰️ Клановый автокликер улучшен до уровня {clan['clan_autoclicker']}! +{50 * clan['clan_autoclicker']} кликов/10 сек! ⚡"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "buy_clan_tag")
async def buy_clan_tag(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user["clan_id"]:
        message_text = "❌ Ты не в клане! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    clan = get_clan(user["clan_id"])
    if clan["clan_tag"]:
        message_text = "❌ Тег клана уже куплен! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    missing = check_resources(user, clan_clicks_needed=1000)
    if missing:
        message_text = f"❌ Недостаточно ресурсов! Нужно {', '.join(missing)} 😢"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    message_text = "🏷️ Введи тег клана (отправь сообщение, до 10 символов):"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="⬅️ Назад", callback_data="clan")
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()
    dp.register_message_handler(set_clan_tag_message, content_types=types.ContentType.TEXT, state="*")

async def set_clan_tag_message(message: Message):
    user = get_user(message.from_user.id)
    if not user["clan_id"]:
        await message.answer("❌ Ты не в клане! 😕", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clan = get_clan(user["clan_id"])
    tag = message.text.strip()
    if len(tag) > 10:
        await message.answer("❌ Тег слишком длинный! Максимум 10 символов. 😢", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clan["clan_clicks"] -= 1000
    clan["clan_tag"] = tag
    await save_data()
    message_text = f"🏷️ Тег клана '{tag}' установлен! Теперь клан в лидерборде: {clan['name']} [{tag}]"
    reply_markup = get_main_keyboard(message.from_user.id)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = reply_markup
    await message.answer(message_text, reply_markup=reply_markup)
    dp.message_handlers.unregister(set_clan_tag_message)

@dp.callback_query(lambda c: c.data == "leave_clan")
async def leave_clan(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    if not user["clan_id"]:
        message_text = "❌ Ты не в клане! 😕"
        reply_markup = get_main_keyboard(callback_query.from_user.id)
        try:
            if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
                await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
                user["last_message_text"] = message_text
                user["last_reply_markup"] = reply_markup
                await save_data()
            await callback_query.answer()
        except TelegramBadRequest as e:
            if "message is not modified" in str(e):
                await callback_query.answer()
            else:
                await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
                await callback_query.answer()
        return
    clan = get_clan(user["clan_id"])
    clan["members"].remove(callback_query.from_user.id)
    if not clan["members"]:
        del clans[user["clan_id"]]
    user["clan_id"] = None
    user["clan_clicks_contributed"] = 0
    await save_data()
    message_text = "🚪 Ты покинул клан!"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    reset_daily_tasks(user)
    message_text = (
        f"📈 <b>Активность</b> 🔥\n"
        f"✅ Сделать 100 кликов: {user['daily_tasks']['clicks']}/100 (+1000 кликов, +5 монет)\n"
        f"🎁 Открыть 3 кейса: {user['daily_tasks']['cases']}/3 (+2000 кликов, +10 монет)\n"
        f"🔧 Купить улучшение: {user['daily_tasks']['upgrade']}/1 (+500 кликов, +5 монет)\n"
        f"👥 Пригласить реферала: {user['daily_tasks']['referral']}/1 (+1000 кликов, +10 монет)\n"
        f"🤝 500 клановых кликов: {user['daily_tasks']['clan_clicks']}/500 (+1500 кликов, +8 монет)"
    )
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

@dp.callback_query(lambda c: c.data == "game_info")
async def handle_game_info(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    season_message = "🌟 Сезон: двойные клики до 15 августа! 🌟" if time.time() < SEASON_END else ""
    message_text = (
        f"📜 <b>Описание игры</b> ℹ️\n"
        f"Добро пожаловать в кликер! 🎮\n"
        f"🖱️ Нажимай кнопку 'Клик', чтобы зарабатывать клики.\n"
        f"🔧 Покупай улучшения, чтобы получать больше кликов за нажатие.\n"
        f"🎁 Открывай кейсы для случайных наград.\n"
        f"🏬 В магазине можно купить автокликер, бонусы и теги.\n"
        f"👥 Присоединяйся к клану или создавай свой, чтобы зарабатывать клановые клики.\n"
        f"🎰 Участвуй в лотерее для шанса на крупный выигрыш.\n"
        f"📈 Выполняй ежедневные задания для дополнительных наград.\n"
        f"🏆 Соревнуйся в лидерборде и показывай, кто лучший!\n"
        f"🔗 Приглашай друзей по реферальной ссылке и получайте бонусы.\n"
        f"{season_message}"
    )
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
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
    message_text = "🔑 Введи промокод (отправь сообщение):"
    reply_markup = InlineKeyboardBuilder()
    reply_markup.button(text="⬅️ Назад", callback_data="back")
    reply_markup = reply_markup.as_markup()
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()
    dp.register_message_handler(promo_message, content_types=types.ContentType.TEXT, state="*")

async def promo_message(message: Message):
    user = get_user(message.from_user.id)
    promo_code = message.text.strip()
    current_time = time.time()
    cooldown = 86400
    if user["last_promo"] != 0 and (current_time - user["last_promo"]) < cooldown:
        remaining_time = int(cooldown - (current_time - user["last_promo"]))
        hours, remainder = divmod(remaining_time, 3600)
        minutes, seconds = divmod(remainder, 60)
        await message.answer(
            f"⏳ Промокод можно использовать через {hours} ч {minutes} мин {seconds} сек! ⏰",
            reply_markup=get_main_keyboard(message.from_user.id)
        )
        return
    valid_promos = {
        "241122": (5000, 10, 5000),
        "KLIKNET2025": (10000, 20, 10000),
        "CLANPOWER": (3000, 5, 3000)
    }
    if promo_code not in valid_promos:
        await message.answer("❌ Неверный промокод! 😢", reply_markup=get_main_keyboard(message.from_user.id))
        return
    clicks, coins, clan_clicks = valid_promos[promo_code]
    user["clicks"] += clicks
    user["coins"] += coins
    if user["clan_id"]:
        get_clan(user["clan_id"])["clan_clicks"] += clan_clicks
    user["last_promo"] = current_time
    rewards = check_achievements(user)
    await save_data()
    message_text = f"🎉 Промокод активирован! +{clicks} кликов, +{coins} монет! 💎🪙\nВсего кликов: {user['clicks']}, монет: {user['coins']}"
    if rewards:
        message_text += "\n" + "\n".join(rewards)
    user["last_message_text"] = message_text
    user["last_reply_markup"] = get_main_keyboard(message.from_user.id)
    await message.answer(message_text, reply_markup=user["last_reply_markup"])
    dp.message_handlers.unregister(promo_message)

@dp.callback_query(lambda c: c.data == "back")
async def handle_back(callback_query: CallbackQuery):
    user = get_user(callback_query.from_user.id)
    message_text = f"👋 Добро пожаловать в кликер! 🎮\n{'🌟 Сезон: двойные клики до 15 августа! 🌟' if time.time() < SEASON_END else ''}"
    reply_markup = get_main_keyboard(callback_query.from_user.id)
    try:
        if user["last_message_text"] != message_text or user["last_reply_markup"] != reply_markup:
            await callback_query.message.edit_text(message_text, reply_markup=reply_markup)
            user["last_message_text"] = message_text
            user["last_reply_markup"] = reply_markup
            await save_data()
        await callback_query.answer()
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            await callback_query.answer()
        else:
            await callback_query.message.answer(f"❌ Произошла ошибка: {str(e)} 😢")
            await callback_query.answer()

async def main():
    load_data()
    await set_bot_commands()
    for user_id, user in users_data.items():
        if user["autoclicker"]:
            asyncio.create_task(autoclicker_task(user_id))
    for clan_id, clan in clans.items():
        if clan["clan_autoclicker"] > 0:
            asyncio.create_task(clan_autoclicker_task(clan_id))
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
