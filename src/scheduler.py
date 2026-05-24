from apscheduler.schedulers.asyncio import AsyncIOScheduler
import aiosqlite
from telegram.ext import (
    Application,
)
from datetime import datetime
from src.database import get_schedule_for_day, get_due_events, mark_event_notified
from src.config import DB_PATH

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


def start_scheduler(loop, app):
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(daily_schedule_job, "cron", hour=7, minute=0, args=[app])
    scheduler.add_job(check_events_job, "interval", seconds=60, args=[app])
    scheduler.start()