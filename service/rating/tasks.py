from procrastinate.contrib.django import app

from common.constants import RatingJob
from game.models import Game
from rating.models import RatingResult


@app.task(name=RatingJob.TASK_NAME, retry=3)
def rate_game(game_id: str):
    RatingResult.objects.rate_game(Game.objects.get(pk=game_id))
