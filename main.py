import sys
import time
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

    max_retries = 5       
    retry_delay = 10       
    
    for attempt in range(1, max_retries + 1):
        try:
            
            builder = Application.builder().token(TOKEN)
            if PROXY_URL:
                builder = builder.proxy(PROXY_URL)
            
            builder = (
                builder
                .connect_timeout(15)
                .read_timeout(15)
                .write_timeout(15)
                .pool_timeout(15)
            )
            
            app = builder.build()
            register_handlers(app)
            start_scheduler(loop, app)

            print(f"Попытка {attempt}: запуск бота...")\
            
            app.run_polling(bootstrap_retries=3)
            break 
        except Exception as e:
            print(f"Попытка {attempt} провалилась: {e}")
            if attempt < max_retries:
                print(f"Жду {retry_delay} сек...")
                time.sleep(retry_delay)
                retry_delay *= 2  
            else:
                print("Все попытки исчерпаны. Бот остановлен.")
                sys.exit(1)

if __name__ == "__main__":
    main()