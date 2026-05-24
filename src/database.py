import aiosqlite
from src.config import DB_PATH
from datetime import datetime

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS schedule (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                day_of_week TEXT,
                time TEXT,
                subject TEXT,
                info TEXT DEFAULT ''
            )
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                chat_id INTEGER,
                event_date TEXT,
                time TEXT,
                text TEXT,
                notified INTEGER DEFAULT 0
            )
        """)
        await db.commit()

async def clear_schedule(user_id: int):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM schedule WHERE user_id = ?", (user_id,))
        await db.commit()

async def insert_schedule(user_id: int, day: str, time_val: str, subject: str, info: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO schedule (user_id, day_of_week, time, subject, info) VALUES (?,?,?,?,?)",
            (user_id, day, time_val, subject, info)
        )
        await db.commit()

async def get_schedule_for_day(user_id: int, day_of_week: str):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT time, subject, info FROM schedule WHERE user_id = ? AND day_of_week = ? ORDER BY time",
            (user_id, day_of_week)
        )
        return await cursor.fetchall()

# --- Методы для разовых событий ---
async def add_event(user_id, chat_id, event_date, event_time, text):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO events (user_id, chat_id, event_date, time, text) VALUES (?,?,?,?,?)",
            (user_id, chat_id, event_date, event_time, text)
        )
        await db.commit()

async def get_due_events():
    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    now_time_str = now.strftime("%H:%M")
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, chat_id, text FROM events WHERE event_date = ? AND time <= ? AND notified = 0",
            (today_str, now_time_str)
        )
        return await cursor.fetchall()

async def mark_event_notified(event_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE events SET notified = 1 WHERE id = ?", (event_id,))
        await db.commit()

async def get_user_events(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT id, event_date, time, text, notified FROM events WHERE user_id = ? ORDER BY event_date, time",
            (user_id,)
        )
        return await cursor.fetchall()
