import asyncio
from src.config import TOKEN, PROXY_URL
from src.database import init_db
from src.handlers.commands import register_handlers
from src.scheduler import start_scheduler
from telegram.ext import Application

def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    loop.run_until_complete(init_db())

    builder = Application.builder().token(TOKEN)
    if PROXY_URL:
        builder = builder.proxy(PROXY_URL)
    app = builder.build()

    register_handlers(app)

    start_scheduler(loop, app)

    print("bot started")


    app.run_polling(
        bootstrap_retries=10,        # количество повторных попыток при старте
        read_timeout=30,            # таймаут на чтение (сек)
        connect_timeout=30,         # таймаут на соединение (сек)
        pool_timeout=30             # таймаут ожидания соединения из пула
    )

if __name__ == "__main__":
    main()