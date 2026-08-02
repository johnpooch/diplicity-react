import logging
from datetime import timedelta

from django.utils import timezone
from procrastinate.contrib.django import app

from game.models import Game

logger = logging.getLogger(__name__)

SANDBOX_RETENTION_DAYS = 7


@app.periodic(cron="45 3 * * *")
@app.task(name="game.purge_stale_sandbox_games")
def purge_stale_sandbox_games(timestamp: int):
    cutoff = timezone.now() - timedelta(days=SANDBOX_RETENTION_DAYS)
    stale = Game.objects.filter(sandbox=True, updated_at__lt=cutoff)
    count = stale.count()
    if count:
        stale.delete()
        logger.info(f"Purged {count} sandbox games idle for more than {SANDBOX_RETENTION_DAYS}d")
