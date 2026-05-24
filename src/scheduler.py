from apscheduler.schedulers.asyncio import AsyncIOScheduler
from handlers.commands import daily_schedule_job, check_events_job 

def start_scheduler(loop, app):
    scheduler = AsyncIOScheduler(event_loop=loop)
    scheduler.add_job(daily_schedule_job, "cron", hour=7, minute=0, args=[app])
    scheduler.add_job(check_events_job, "interval", seconds=60, args=[app])
    scheduler.start()