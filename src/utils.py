DAYS_MAP = {
    "пн": "Понедельник",
    "вт": "Вторник",
    "ср": "Среда",
    "чт": "Четверг",
    "пт": "Пятница",
    "сб": "Суббота",
    "вс": "Воскресенье",
}

RU_DAYS_MAP = {
    "Monday": "Понедельник",
    "Tuesday": "Вторник",
    "Wednesday": "Среда",
    "Thursday": "Четверг",
    "Friday": "Пятница",
    "Saturday": "Суббота",
    "Sunday": "Воскресенье",
}

START_MENU = (
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

HELP_MENU = (
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


def normalize_day(raw: str) -> str:
    raw_lower = raw.strip().lower()
    for prefix, full_name in DAYS_MAP.items():
        if raw_lower.startswith(prefix):
            return full_name

    return raw.strip().capitalize()