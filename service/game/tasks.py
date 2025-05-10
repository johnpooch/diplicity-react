import uuid

from celery import Task as CeleryTask

from .models import Task


class BaseTask(CeleryTask):

    def apply_async(self, args, kwargs, **options):
        task_id = uuid.uuid4()
        Task.objects.create(
            id=task_id,
            name=self.name,
            status=Task.PENDING,
        )
        return super().apply_async(args, kwargs, task_id=task_id, **options)

    def before_start(self, task_id, args, kwargs):
        task = Task.objects.get(id=task_id)
        task.status = Task.ACTIVE
        task.save()

    def on_success(self, retval, task_id, args, kwargs):
        task = Task.objects.get(id=task_id)
        task.status = Task.COMPLETED
        task.result = "Task completed successfully!"
        task.save()

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        task = Task.objects.get(id=task_id)
        task.status = Task.FAILED
        task.result = str(exc)
        task.save()
