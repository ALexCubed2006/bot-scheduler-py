from telegram import Update
from telegram.ext import (
    CommandHandler,
    ContextTypes,
)
from datetime import datetime
from database import get_schedule_for_day, clear_schedule, add_event, get_user_events
from src.utils import HELP_MENU, START_MENU

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(START_MENU)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_MENU)

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


def register_handlers(app):
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("today", today))
    app.add_handler(CommandHandler("tomorrow", tomorrow))
    app.add_handler(CommandHandler("week", week))
    app.add_handler(CommandHandler("clearschedule", clear_schedule_command))
    app.add_handler(CommandHandler("upload", upload_command))
    app.add_handler(CommandHandler("addevent", addevent_command))
    app.add_handler(CommandHandler("myevents", myevents_command))