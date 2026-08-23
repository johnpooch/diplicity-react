from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app

from common.constants import ResolutionJob
from phase.models import Phase


def run_due_resolution_jobs():
    now = timezone.now()
    ready_job_ids = [
        job.id
        for job in procrastinate_app.job_manager.list_jobs(
            task=ResolutionJob.TASK_NAME, status=ResolutionJob.TODO
        )
        if job.scheduled_at is None or job.scheduled_at <= now
    ]
    phase_ids = list(
        Phase.objects.filter(resolution_job_id__in=ready_job_ids).values_list("id", flat=True)
    )
    for job_id in ready_job_ids:
        procrastinate_app.job_manager.cancel_job_by_id(job_id)
    for phase_id in phase_ids:
        Phase.objects.resolve_if_due(phase_id)
    return len(phase_ids)
