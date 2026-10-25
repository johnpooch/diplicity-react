from procrastinate.contrib.django import app

from .commands import SendMusterReminder, StartMusteredGame
from .models import Game
from .timers import MusterReminderTimer, MusterTimer


@app.task(name=MusterTimer.task, retry=3)
def start_if_mustered(game_id: str):
    game = Game.objects.filter(pk=game_id).first()
    if game is not None:
        StartMusteredGame()(game)


@app.task(name=MusterReminderTimer.task, retry=3)
def send_muster_reminder(game_id: str):
    game = Game.objects.filter(pk=game_id).first()
    if game is not None:
        SendMusterReminder()(game)
