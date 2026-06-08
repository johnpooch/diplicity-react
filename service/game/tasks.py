import logging

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from procrastinate.contrib.django import app

from common.constants import GameStatus
from notification import utils as notification_utils

logger = logging.getLogger(__name__)


@app.periodic(cron="* * * * *")
@app.task(name="game.sweep_confirmation_deadlines")
def sweep_confirmation_deadlines(timestamp: int):
    from game.models import Game

    logger.info(f"Running sweep_confirmation_deadlines task (scheduled for {timestamp})")

    games = Game.objects.filter(
        status=GameStatus.PENDING,
        confirmation_required=True,
        confirmation_deadline__isnull=False,
        confirmation_deadline__lte=timezone.now(),
    ).prefetch_related("members__user")

    removed_count = 0
    for game in games:
        unconfirmed = list(game.members.filter(confirmed=False))
        if not unconfirmed:
            continue

        with transaction.atomic():
            unconfirmed_user_ids = [
                m.user_id for m in unconfirmed if m.user_id is not None
            ]

            for member in unconfirmed:
                member.delete()

            game.confirmation_deadline = None
            game.save(update_fields=["confirmation_deadline"])
            game.delete_if_empty_pending()

            removed_count += len(unconfirmed)

            def send_notifications(user_ids=unconfirmed_user_ids, g=game):
                for user_id in user_ids:
                    notification_utils.send_notification_to_users(
                        user_ids=[user_id],
                        title=g.name,
                        body="You were removed from the game because you did not confirm in time.",
                        notification_type="confirmation_expired",
                        data={"game_id": str(g.id), "link": f"{settings.FRONTEND_URL}/game/{g.id}"},
                    )

            transaction.on_commit(send_notifications)

    logger.info(f"Confirmation sweep complete: removed {removed_count} unconfirmed members")
    return {"removed": removed_count}
