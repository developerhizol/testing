# utils.py - ПОЛНЫЙ ФАЙЛ
import asyncio
import sqlite3
import os
import random
import string
import secrets
import aiohttp
from datetime import datetime, timedelta
from aiogram import Bot, types
from aiogram.enums import ParseMode
from aiogram.types import InputMediaPhoto
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN, SUBGRAM_API_URL, SUBGRAM_API_KEY, SUBGRAM_CHECK_URL, PROXIES_FILE

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))

DB_PATH = "data/users.db"
os.makedirs("data", exist_ok=True)


# ==================== ФУНКЦИИ ПОЛУЧЕНИЯ МОСКОВСКОГО ВРЕМЕНИ ====================
async def get_current_moscow_time_async() -> datetime:
    try:
        async with aiohttp.ClientSession() as session:
            url = "https://smartapp-code.sberdevices.ru/tools/api/now?tz=Europe/Moscow"
            async with session.get(url, timeout=5) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    year = data.get("year")
                    month = data.get("month")
                    day = data.get("day")
                    hour = data.get("hour")
                    minute = data.get("minute")
                    if all([year, month, day, hour is not None, minute is not None]):
                        return datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=0)
    except:
        pass
    return datetime.now()


def get_current_moscow_time_sync() -> datetime:
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        moscow_time = loop.run_until_complete(get_current_moscow_time_async())
        loop.close()
        return moscow_time
    except:
        return datetime.now()
# ==================== КОНЕЦ ФУНКЦИЙ ВРЕМЕНИ ====================


def migrate_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]

    if 'plan' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN plan TEXT DEFAULT 'free'")
    if 'language' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN language TEXT DEFAULT NULL")
    if 'ads_disabled' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN ads_disabled INTEGER DEFAULT 0")
    if 'premium_until' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN premium_until TIMESTAMP DEFAULT NULL")
    if 'payment_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN payment_id TEXT DEFAULT NULL")
    if 'payment_date' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN payment_date TIMESTAMP DEFAULT NULL")
    if 'referrer_id' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referrer_id INTEGER DEFAULT NULL")
    if 'referral_code' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_code TEXT DEFAULT NULL")
    if 'referral_count' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_count INTEGER DEFAULT 0")
    if 'referral_earnings' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN referral_earnings INTEGER DEFAULT 0")
    if 'captcha_passed' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN captcha_passed INTEGER DEFAULT 0")
    if 'captcha_data' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN captcha_data TEXT DEFAULT NULL")
    if 'subscription_token' not in columns:
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_token TEXT DEFAULT NULL")
        cursor.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_subscription_token ON users(subscription_token)")
        cursor.execute("SELECT user_id FROM users WHERE subscription_token IS NULL")
        for (user_id,) in cursor.fetchall():
            token = generate_subscription_token()
            while True:
                cursor.execute("SELECT 1 FROM users WHERE subscription_token = ?", (token,))
                if not cursor.fetchone():
                    break
                token = generate_subscription_token()
            cursor.execute("UPDATE users SET subscription_token = ? WHERE user_id = ?", (token, user_id))
    conn.commit()
    conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        ads_disabled INTEGER DEFAULT 0,
        language TEXT DEFAULT NULL,
        plan TEXT DEFAULT 'free',
        premium_until TIMESTAMP DEFAULT NULL,
        payment_id TEXT DEFAULT NULL,
        payment_date TIMESTAMP DEFAULT NULL,
        referrer_id INTEGER DEFAULT NULL,
        referral_code TEXT DEFAULT NULL,
        referral_count INTEGER DEFAULT 0,
        referral_earnings INTEGER DEFAULT 0,
        captcha_passed INTEGER DEFAULT 0,
        captcha_data TEXT DEFAULT NULL,
        subscription_token TEXT DEFAULT NULL UNIQUE
    )''')
    cursor.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS user_balance (user_id INTEGER PRIMARY KEY, balance INTEGER DEFAULT 0)')
    cursor.execute('CREATE TABLE IF NOT EXISTS referrals (id INTEGER PRIMARY KEY AUTOINCREMENT, referrer_id INTEGER, referred_id INTEGER, reward INTEGER, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    conn.close()
    migrate_db()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('INSERT OR IGNORE INTO user_balance (user_id, balance) SELECT user_id, 0 FROM users')
    conn.commit()
    conn.close()
    sync_all_users_premium_status()


def sync_all_users_premium_status():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('SELECT user_id, premium_until FROM users WHERE premium_until IS NOT NULL')
    now = get_current_moscow_time_sync()
    for user_id, until_str in cursor.fetchall():
        try:
            until = datetime.strptime(until_str, "%d.%m.%Y:%H.%M.%S")
            if now > until:
                cursor.execute('UPDATE users SET plan = "free", premium_until = NULL, payment_date = NULL, payment_id = NULL WHERE user_id = ?', (user_id,))
            else:
                cursor.execute('UPDATE users SET plan = "premium" WHERE user_id = ?', (user_id,))
        except:
            cursor.execute('UPDATE users SET plan = "free", premium_until = NULL, payment_date = NULL, payment_id = NULL WHERE user_id = ?', (user_id,))
    cursor.execute('UPDATE users SET plan = "free", premium_until = NULL, payment_date = NULL, payment_id = NULL WHERE premium_until IS NULL AND plan = "premium"')
    conn.commit()
    conn.close()


def get_balance(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT balance FROM user_balance WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else 0


def add_balance(user_id: int, amount: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO user_balance (user_id, balance) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET balance = balance + ?', (user_id, amount, amount))
    conn.commit()
    conn.close()


def deduct_balance(user_id: int, amount: int) -> bool:
    if get_balance(user_id) < amount:
        return False
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE user_balance SET balance = balance - ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()
    return True


def set_captcha_passed(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET captcha_passed = 1, captcha_data = NULL WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def is_captcha_passed(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT captcha_passed FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res and res[0] == 1


def get_referral_code(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    if res and res[0]:
        return res[0]
    code = f"{user_id}{''.join(random.choices(string.ascii_uppercase + string.digits, k=4))}"
    cur.execute('UPDATE users SET referral_code = ? WHERE user_id = ?', (code, user_id))
    conn.commit()
    conn.close()
    return code


def get_referrer(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT referrer_id FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else None


def set_referrer(user_id: int, referrer_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET referrer_id = ? WHERE user_id = ? AND referrer_id IS NULL', (referrer_id, user_id))
    conn.commit()
    conn.close()


def add_referral_reward(referrer_id: int, referred_id: int, reward: int):
    add_balance(referrer_id, reward)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT INTO referrals (referrer_id, referred_id, reward) VALUES (?, ?, ?)', (referrer_id, referred_id, reward))
    cur.execute('UPDATE users SET referral_count = referral_count + 1, referral_earnings = referral_earnings + ? WHERE user_id = ?', (reward, referrer_id))
    conn.commit()
    conn.close()


def get_referral_stats(user_id: int) -> dict:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT referral_count, referral_earnings FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return {"count": res[0] if res else 0, "earnings": res[1] if res else 0}


def get_referral_list(user_id: int) -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('''SELECT u.user_id, u.first_name, u.joined_at, r.reward, r.created_at
                   FROM referrals r JOIN users u ON r.referred_id = u.user_id
                   WHERE r.referrer_id = ? ORDER BY r.created_at DESC''', (user_id,))
    res = cur.fetchall()
    conn.close()
    return res


def format_datetime_custom(dt: datetime) -> str:
    return dt.strftime("%d.%m.%Y:%H.%M.%S")


def parse_datetime_custom(s: str) -> datetime:
    return datetime.strptime(s, "%d.%m.%Y:%H.%M.%S")


def activate_premium(user_id: int, days: int = 30, payment_id: str = None):
    now = get_current_moscow_time_sync()
    until = now + timedelta(days=days)
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    if payment_id:
        cur.execute('UPDATE users SET premium_until = ?, plan = "premium", payment_date = ?, payment_id = ? WHERE user_id = ?',
                    (format_datetime_custom(until), format_datetime_custom(now), payment_id, user_id))
    else:
        cur.execute('UPDATE users SET premium_until = ?, plan = "premium", payment_date = ?, payment_id = NULL WHERE user_id = ?',
                    (format_datetime_custom(until), format_datetime_custom(now), user_id))
    conn.commit()
    conn.close()


def disable_premium(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET premium_until = NULL, plan = "free", payment_date = NULL, payment_id = NULL WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_premium_until(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT premium_until FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else None


def check_premium_active(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT plan, premium_until FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    conn.close()
    if not row or row[0] != 'premium' or not row[1]:
        return False
    try:
        until = parse_datetime_custom(row[1])
        return get_current_moscow_time_sync() <= until
    except:
        return False


async def disable_expired_premiums_async():
    now = await get_current_moscow_time_async()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT user_id, premium_until FROM users WHERE plan = "premium" AND premium_until IS NOT NULL')
    disabled = 0
    for user_id, until_str in cur.fetchall():
        try:
            until = parse_datetime_custom(until_str)
            if now > until:
                cur.execute('UPDATE users SET plan = "free", premium_until = NULL, payment_date = NULL, payment_id = NULL WHERE user_id = ?', (user_id,))
                disabled += 1
        except:
            pass
    conn.commit()
    conn.close()
    return disabled


def get_plan(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT plan FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else 'free'


def set_plan(user_id: int, plan: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET plan = ? WHERE user_id = ?', (plan, user_id))
    if plan == 'free':
        cur.execute('UPDATE users SET premium_until = NULL, payment_date = NULL, payment_id = NULL WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def get_language(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT language FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else None


def set_language(user_id: int, lang: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET language = ? WHERE user_id = ?', (lang, user_id))
    conn.commit()
    conn.close()


def get_user_joined_date(user_id: int) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT joined_at FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    if res:
        joined = datetime.strptime(res[0], '%Y-%m-%d %H:%M:%S')
        days = (get_current_moscow_time_sync() - joined).days
        return days if days >= 0 else 0
    return 0


def is_ads_disabled(user_id: int) -> bool:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT ads_disabled FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res and res[0] == 1


def disable_ads(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET ads_disabled = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def enable_ads(user_id: int):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET ads_disabled = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()


def disable_ads_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET ads_disabled = 1')
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count


def enable_ads_all():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET ads_disabled = 0')
    count = cur.rowcount
    conn.commit()
    conn.close()
    return count


def add_user(user_id: int, username: str, first_name: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('INSERT OR IGNORE INTO users (user_id, username, first_name, ads_disabled, plan) VALUES (?, ?, ?, ?, ?)',
                (user_id, username, first_name, 0, 'free'))
    cur.execute('INSERT OR IGNORE INTO user_balance (user_id, balance) VALUES (?, 0)', (user_id,))
    conn.commit()
    conn.close()


def get_user_count() -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM users')
    count = cur.fetchone()[0]
    conn.close()
    return count


def get_all_users() -> list:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users')
    users = [row[0] for row in cur.fetchall()]
    conn.close()
    return users


def get_user_payment_id(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT payment_id FROM users WHERE user_id = ?', (user_id,))
    res = cur.fetchone()
    conn.close()
    return res[0] if res else None


def save_payment_info(user_id: int, payment_id: str):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('UPDATE users SET payment_id = ?, payment_date = ? WHERE user_id = ?',
                (payment_id, get_current_moscow_time_sync().strftime('%Y-%m-%d %H:%M:%S'), user_id))
    conn.commit()
    conn.close()


# ========== ФУНКЦИИ ДЛЯ ТОКЕНА ПОДПИСКИ ==========
def generate_subscription_token() -> str:
    return ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(24))


def get_or_create_subscription_token(user_id: int) -> str:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT subscription_token FROM users WHERE user_id = ?', (user_id,))
    row = cur.fetchone()
    if row and row[0]:
        token = row[0]
    else:
        while True:
            token = generate_subscription_token()
            cur.execute('SELECT 1 FROM users WHERE subscription_token = ?', (token,))
            if not cur.fetchone():
                break
        cur.execute('UPDATE users SET subscription_token = ? WHERE user_id = ?', (token, user_id))
        conn.commit()
    conn.close()
    return token


def get_user_id_by_token(token: str) -> int:
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute('SELECT user_id FROM users WHERE subscription_token = ?', (token,))
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None
# ========== КОНЕЦ ==========


init_db()


# ========== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ДЛЯ БОТА ==========
async def send_photo(chat_id, text, reply_markup=None, image_url=None, message_effect_id=None):
    if not image_url:
        raise ValueError("image_url is required")
    return await bot.send_photo(chat_id=chat_id, photo=image_url, caption=text, reply_markup=reply_markup, message_effect_id=message_effect_id)


async def edit_photo(message, text, reply_markup=None, image_url=None):
    if not image_url:
        raise ValueError("image_url is required")
    await message.edit_media(InputMediaPhoto(media=image_url, caption=text), reply_markup=reply_markup)


async def get_sponsors(user_id, chat_id, plan='free'):
    if is_ads_disabled(user_id):
        return []
    headers = {"Auth": SUBGRAM_API_KEY, "Content-Type": "application/json"}
    payload = {"user_id": user_id, "chat_id": chat_id}
    async with aiohttp.ClientSession() as session:
        async with session.post(SUBGRAM_API_URL, headers=headers, json=payload) as resp:
            if resp.status == 200:
                data = await resp.json()
                if data.get("status") == "warning":
                    return data.get("additional", {}).get("sponsors", [])
                elif data.get("status") == "ok":
                    return []
            return None


def load_proxies():
    try:
        with open(PROXIES_FILE, "r") as f:
            return [line.strip() for line in f if line.strip()]
    except:
        return []