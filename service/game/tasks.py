import uuid
import logging

from celery import Task as CeleryTask, shared_task
from celery.result import AsyncResult
from django.db import transaction

from . import models, services

logger = logging.getLogger("game")


class BaseTask(CeleryTask):

    def apply_async(self, args, kwargs, **options):
        task_id = options.get('task_id', uuid.uuid4())
        options['task_id'] = task_id

        task, created = models.Task.objects.get_or_create(
            id=task_id,
            defaults={
                'name': self.name,
                'status': models.Task.PENDING,
            }
        )

        if not created and task.status != models.Task.PENDING:
            task.status = models.Task.PENDING
            task.save()

        transaction.on_commit(
            lambda: super(BaseTask, self).apply_async(args, kwargs, **options)
        )

        return AsyncResult(task_id)

    def before_start(self, task_id, args, kwargs):
        task = models.Task.objects.get(id=task_id)
        task.status = models.Task.ACTIVE
        task.save()

    def on_success(self, retval, task_id, args, kwargs):
        task = models.Task.objects.get(id=task_id)
        task.status = models.Task.COMPLETED
        task.result = "models.Task completed successfully!"
        task.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task = models.Task.objects.get(id=task_id)
        task.status = models.Task.FAILED
        task.result = str(exc)
        task.save()


@shared_task(base=BaseTask)
def start_task(game_id):
    logger.info(f"start_task() called with game_id: {game_id}")
    adjudication_service = services.AdjudicationService(None)
    service = services.GameService(user=None, adjudication_service=adjudication_service)
    service.start(game_id)
    logger.info(f"start_task() completed")


@shared_task(base=BaseTask)
def resolve_task(game_id):
    logger.info(f"resolve_task() called with game_id: {game_id}")
    adjudication_service = services.AdjudicationService(None)
    service = services.GameService(user=None, adjudication_service=adjudication_service)
    service.resolve(game_id)
    logger.info(f"resolve_task() completed")


@shared_task(base=BaseTask)
def notify_task(user_ids, data):
    logger.info(f"notify_task() called with user_ids: {user_ids} and data: {data}")
    service = services.NotificationService(user=None)
    service.notify(user_ids, data)
    logger.info(f"notify_task() completed")
