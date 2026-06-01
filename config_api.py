import sqlite3
import os
from datetime import datetime
from fastapi import FastAPI, Response, HTTPException
from contextlib import asynccontextmanager

DB_PATH = "data/users.db"

def parse_datetime_custom(date_str: str) -> datetime:
    return datetime.strptime(date_str, "%d.%m.%Y:%H.%M.%S")

def get_current_moscow_time_sync() -> datetime:
    from datetime import datetime
    return datetime.now()  # или импорт из utils, но для простоты так

def is_premium_active_by_token(token: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, plan, premium_until FROM users WHERE subscription_token = ?", (token,))
    row = cursor.fetchone()
    conn.close()
    if not row:
        return False, None
    user_id, plan, until_str = row
    if plan != "premium" or not until_str:
        return False, user_id
    try:
        until = parse_datetime_custom(until_str)
        return get_current_moscow_time_sync() <= until, user_id
    except:
        return False, user_id

def get_config_for_user(user_id: int) -> str:
    config_path = "configs/premium.conf"
    if not os.path.exists(config_path):
        # Заглушка – замените на ваш реальный конфиг
        return "vless://example@example.com:443?encryption=none#PremiumConfig"
    with open(config_path, "r") as f:
        return f.read()

@asynccontextmanager
async def lifespan(app: FastAPI):
    os.makedirs("configs", exist_ok=True)
    yield

app = FastAPI(lifespan=lifespan)

@app.get("/sub/{token}")
async def get_subscription(token: str, response: Response):
    active, user_id = is_premium_active_by_token(token)
    if not active or user_id is None:
        stub = """#profile-title: 🛡 StreamNetVPN | Premium
#announce: 🌐 Интернет без ограничений. Если сервера не работают - обновите их нажав на 🔄, иногда может помочь. Наш telegram бот: @StreamNetVPN_bot. #ЗаСвободныйИнтернет!
#profile-update-interval: 1

vless://#🚫 Ваша подписка истекла
vless://#🔁 Продлите ее в боте
vless://🤖 Наш бот: @StreamNetVPN_bot"""
        response.headers["subscription-userinfo"] = "upload=0; download=0; total=0; expire=1577836800"
        return Response(content=stub, media_type="text/plain")
    try:
        config_text = get_config_for_user(user_id)
    except FileNotFoundError:
        raise HTTPException(500, "Config not found")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT premium_until FROM users WHERE user_id = ?", (user_id,))
    row = cursor.fetchone()
    conn.close()
    if row and row[0]:
        until_dt = parse_datetime_custom(row[0])
        response.headers["subscription-userinfo"] = f"upload=0; download=0; total=0; expire={int(until_dt.timestamp())}"
    return Response(content=config_text, media_type="text/plain")