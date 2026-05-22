import os
import csv
import io
import asyncio
from datetime import datetime

import aiosqlite
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

# ------------------------------------------------------------
# Переменные окружения
# ------------------------------------------------------------
TOKEN = os.getenv("BOT_TOKEN")
PROXY_URL = os.getenv("PROXY_URL")
DB_PATH = "bot_data.db"

# ------------------------------------------------------------
# База данных
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Утилиты
# ------------------------------------------------------------
DAYS_MAP = {
    "понедельник": "Понедельник",
    "вторник": "Вторник",
    "среда": "Среда",
    "четверг": "Четверг",
    "пятница": "Пятница",
    "суббота": "Суббота",
    "воскресенье": "Воскресенье",
}

def normalize_day(raw: str) -> str:
    raw_lower = raw.strip().lower()
    for key, name in DAYS_MAP.items():
        if key.startswith(raw_lower[:3]):
            return name
    return raw.strip().capitalize()

# ------------------------------------------------------------
# Обработчики команд
# ------------------------------------------------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Привет! Я бот-расписание.\n\n"
        "Основные команды:\n"
        "/upload — загрузить CSV с расписанием (отправьте файл)\n"
        "/today — расписание на сегодня\n"
        "/tomorrow — на завтра\n"
        "/week — вся неделя\n"
        "/addevent <дата> <время> <описание> — добавить событие\n"
        "/myevents — мои события\n"
        "/clearschedule — очистить моё расписание\n"
        "/help — помощь"
    )
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 Как загрузить расписание:\n"
        "1. Создайте CSV-файл с колонками: day,time,subject,info\n"
        "   Пример:\n"
        "   day,time,subject,info\n"
        "   Понедельник,08:30,Математика,ауд.301\n"
        "   Понедельник,10:15,Физика,лаб.5\n"
        "   ...\n"
        "2. Отправьте файл боту командой /upload или просто скиньте файл.\n\n"
        "⏰ Ежедневная рассылка: каждое утро в 07:00 вы получите расписание на текущий день.\n"
        "Для разовых событий используйте /addevent."
    )
    await update.message.reply_text(text)

async def today(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    ru_days = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    }
    day_ru = ru_days.get(datetime.now().strftime("%A"), "Unknown")
    schedule = await get_schedule_for_day(user_id, day_ru)
    if not schedule:
        await update.message.reply_text("На сегодня занятий нет 🎉")
        return
    lines = [f"📅 *{day_ru}*"]
    for t, subj, info in schedule:
        info_str = f" ({info})" if info else ""
        lines.append(f"• {t} — {subj}{info_str}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def tomorrow(update: Update, context: ContextTypes.DEFAULT_TYPE):
    from datetime import timedelta
    user_id = update.effective_user.id
    tomorrow_date = datetime.now() + timedelta(days=1)
    ru_days = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    }
    day_ru = ru_days.get(tomorrow_date.strftime("%A"), "Unknown")
    schedule = await get_schedule_for_day(user_id, day_ru)
    if not schedule:
        await update.message.reply_text("На завтра занятий нет 🎉")
        return
    lines = [f"📅 *{day_ru}* (завтра)"]
    for t, subj, info in schedule:
        info_str = f" ({info})" if info else ""
        lines.append(f"• {t} — {subj}{info_str}")
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")

async def week(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    days_order = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    all_lines = []
    for day_name in days_order:
        pairs = await get_schedule_for_day(user_id, day_name)
        if pairs:
            all_lines.append(f"📌 *{day_name}*")
            for t, subj, info in pairs:
                info_str = f" ({info})" if info else ""
                all_lines.append(f"  • {t} — {subj}{info_str}")
    if not all_lines:
        await update.message.reply_text("Расписание пустое. Загрузите CSV через /upload.")
        return
    await update.message.reply_text("\n".join(all_lines), parse_mode="Markdown")

async def clear_schedule_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await clear_schedule(user_id)
    await update.message.reply_text("✅ Расписание очищено.")

async def upload_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Отправьте CSV-файл с расписанием.")

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    doc = update.message.document
    if not doc.file_name.endswith(".csv"):
        await update.message.reply_text("❌ Пожалуйста, отправьте файл .csv")
        return

    file = await doc.get_file()
    file_bytes = await file.download_as_bytearray()
    file_text = file_bytes.decode("utf-8")

    reader = csv.DictReader(io.StringIO(file_text))
    required = {"day", "time", "subject"}
    if not required.issubset(reader.fieldnames):
        await update.message.reply_text("❌ В файле должны быть колонки: day, time, subject")
        return

    await clear_schedule(user_id)
    count = 0
    for row in reader:
        day_raw = row["day"]
        time_val = row["time"]
        subject = row["subject"]
        info = row.get("info", "")
        day_norm = normalize_day(day_raw)
        await insert_schedule(user_id, day_norm, time_val, subject, info)
        count += 1

    await update.message.reply_text(f"✅ Загружено {count} записей. Ваше расписание обновлено!\nПроверьте: /week")

async def addevent_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id
    args = context.args
    if len(args) < 3:
        await update.message.reply_text(
            "Использование: /addevent ГГГГ-ММ-ДД ЧЧ:ММ Описание\n"
            "Пример: /addevent 2026-06-01 15:00 Встреча с деканом"
        )
        return
    date_str = args[0]
    time_str = args[1]
    text = " ".join(args[2:])
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        datetime.strptime(time_str, "%H:%M")
    except ValueError:
        await update.message.reply_text("❌ Неверный формат даты или времени. Используйте ГГГГ-ММ-ДД и ЧЧ:ММ")
        return
    await add_event(user.id, chat_id, date_str, time_str, text)
    await update.message.reply_text(f"✅ Событие добавлено: {date_str} {time_str} — {text}")

async def myevents_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    events = await get_user_events(user.id)
    if not events:
        await update.message.reply_text("У вас нет запланированных событий.")
        return
    lines = ["📌 Ваши события:"]
    for ev_id, date, time_val, text, notified in events:
        status = "✅" if notified else "⏳"
        lines.append(f"{status} {date} {time_val} — {text}")
    await update.message.reply_text("\n".join(lines))

# ------------------------------------------------------------
# Фоновые задачи
# ------------------------------------------------------------
async def daily_schedule_job(app: Application):
    today_ru = {
        "Monday": "Понедельник",
        "Tuesday": "Вторник",
        "Wednesday": "Среда",
        "Thursday": "Четверг",
        "Friday": "Пятница",
        "Saturday": "Суббота",
        "Sunday": "Воскресенье",
    }
    day_ru = today_ru[datetime.now().strftime("%A")]
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT DISTINCT user_id FROM schedule")
        users = [row[0] for row in await cursor.fetchall()]
    for user_id in users:
        try:
            pairs = await get_schedule_for_day(user_id, day_ru)
            if not pairs:
                continue
            lines = [f"📅 *{day_ru}* (расписание на сегодня)"]
            for t, subj, info in pairs:
                info_str = f" ({info})" if info else ""
                lines.append(f"• {t} — {subj}{info_str}")
            await app.bot.send_message(
                chat_id=user_id,
                text="\n".join(lines),
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Не удалось отправить расписание пользователю {user_id}: {e}")

async def check_events_job(app: Application):
    due = await get_due_events()
    for ev_id, chat_id, text in due:
        try:
            await app.bot.send_message(chat_id=chat_id, text=f"⏰ Событие: {text}")
            await mark_event_notified(ev_id)
        except Exception as e:
            print(f"Ошибка при отправке события {ev_id}: {e}")

# ------------------------------------------------------------
# Главная функция (синхронная, создаёт event loop)
# ------------------------------------------------------------
def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Инициализация БД
    loop.run_until_complete(init_db())

    # Сборка приложения
    builder = Application.builder().token(TOKEN)
    if PROXY_URL:
        builder = builder.proxy(PROXY_URL)
    app = builder.build()

    # Регистрация обработчиков
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("clearschedule", clear_schedule_command))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("addevent", addevent_command))
    app.add_handler(CommandHandler("myevents", myevents_command))
    app.add_handler(MessageHandler(filters.Document.MimeType("text/csv"), handle_document))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), handle_document))

    # Планировщик в том же event loop
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(daily_schedule_job, "cron", hour=7, minute=0, args=[app])
    scheduler.add_job(check_events_job, "interval", seconds=60, args=[app])
    scheduler.start()

    print("Бот с расписанием запущен...")
    # Запуск опроса – будет использовать текущий event loop
    app.run_polling()

if __name__ == "__main__":
    main()