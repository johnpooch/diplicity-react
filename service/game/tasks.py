import uuid

from celery import shared_task

from . import models, services


@shared_task
def start_task(game_id):
    """Start a game task."""
    adjudication_service = services.AdjudicationService(None)
    service = services.GameService(user=None, adjudication_service=adjudication_service)
    service.start(game_id)


@shared_task
def resolve_task(game_id):
    """Resolve a game task."""
    adjudication_service = services.AdjudicationService(None)
    service = services.GameService(user=None, adjudication_service=adjudication_service)
    service.resolve(game_id)


@shared_task
def notify_task(user_ids, data):
    """Send notifications to users."""
    service = services.NotificationService(user=None)
    service.notify(user_ids, data)
