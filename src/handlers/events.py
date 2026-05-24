from telegram.ext import CommandHandler
from commands import addevent_command, myevents_command

def register_event_handlers(app):
    app.add_handler(CommandHandler("addevent", addevent_command))
    app.add_handler(CommandHandler("myevents", myevents_command))