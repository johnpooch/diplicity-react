from django.urls import reverse
from django.utils import timezone
from procrastinate.contrib.django import app as procrastinate_app

from common.constants import MusterJob, ResolutionJob
from game.models import Game
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
        Phase.objects.filter(resolution_job_id__in=ready_job_ids).values_list(
            "id", flat=True
        )
    )
    for job_id in ready_job_ids:
        procrastinate_app.job_manager.cancel_job_by_id(job_id)
    for phase_id in phase_ids:
        Phase.objects.resolve_if_due(phase_id)
    return len(phase_ids)


def run_due_muster_jobs():
    now = timezone.now()
    ready_job_ids = [
        job.id
        for job in procrastinate_app.job_manager.list_jobs(
            task=MusterJob.TASK_NAME, status=MusterJob.TODO
        )
        if job.scheduled_at is None or job.scheduled_at <= now
    ]
    game_ids = list(
        Game.objects.filter(muster_job_id__in=ready_job_ids).values_list(
            "id", flat=True
        )
    )
    for job_id in ready_job_ids:
        procrastinate_app.job_manager.cancel_job_by_id(job_id)
    for game_id in game_ids:
        Game.objects.start_if_mustered(game_id)
    return len(game_ids)


def muster(game_id, *clients):
    for client in clients:
        client.post(reverse("game-muster", args=[game_id]))
    run_due_muster_jobs()
