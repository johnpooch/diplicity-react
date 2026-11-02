from procrastinate.contrib.django import app

from discord_service import utils


@app.task(name="discord_service.post", retry=3)
def post(content):
    utils.post_message(content)
