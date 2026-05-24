from telegram.ext import MessageHandler, filters
from telegram import Update
from telegram.ext import (
    ContextTypes,
)
from database import  clear_schedule, insert_schedule
import csv
import io
from utils import normalize_day

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


def register_document_handlers(app):
    app.add_handler(MessageHandler(filters.Document.MimeType("text/csv"), handle_document))
    app.add_handler(MessageHandler(filters.Document.FileExtension("csv"), handle_document))