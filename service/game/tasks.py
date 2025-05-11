import uuid

from celery import Task as CeleryTask, shared_task

from . import models, services


class BaseTask(CeleryTask):

    def apply_async(self, args, kwargs, **options):
        task_id = uuid.uuid4()
        models.Task.objects.create(
            id=task_id,
            name=self.name,
            status=models.Task.PENDING,
        )
        return super().apply_async(args, kwargs, task_id=task_id, **options)

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
    service = services.GameService(user=None)
    service.start(game_id)


@shared_task(base=BaseTask)
def resolve_task(game_id):
    service = services.GameService(user=None)
    service.resolve(game_id)


@shared_task(base=BaseTask)
def notify_task(user_ids, data):
    service = services.NotificationService(user=None)
    service.notify(user_ids, data)
