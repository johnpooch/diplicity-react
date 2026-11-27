from django.db import transaction
from django.db.models import Manager
from procrastinate.contrib.django import app

from common.commands import command
from draw_proposal.models import DrawProposal

from .checks import IsPendingCheck, IsRunningCheck, IsUnfinishedCheck
from .constants import COORDINATE_TASK
from .listeners import LISTENERS
from .querysets import RunQuerySet
from .steps import STEPS


def defer_tick():
    app.configure_task(COORDINATE_TASK).defer()


class RunManager(Manager.from_queryset(RunQuerySet)):
    def create_from_event(self, event_type, context):
        listener = LISTENERS.get(event_type)
        if listener is None:
            return []
        runs = listener.create_runs(context)
        if runs:
            transaction.on_commit(defer_tick)
        return runs

    @command(only_if=IsPendingCheck)
    def start(self, run):
        run.mark_running()
        app.configure_task(STEPS[run.step].task, lock=f"bot-run-{run.pk}").defer(
            pk=run.pk
        )
        return run

    @command(only_if=IsRunningCheck, locks=["phase"])
    def vote_on_draw(self, run, accepted):
        DrawProposal.objects.vote(
            run.draw_proposal, actor=run.bot.user, accepted=accepted
        )
        run.mark_succeeded()
        return run

    @command(only_if=IsUnfinishedCheck)
    def skip(self, run):
        run.mark_skipped()
        return run

    @command(only_if=IsRunningCheck)
    def fail(self, run, error):
        run.mark_failed(error)
        return run

    @command(only_if=IsRunningCheck)
    def time_out(self, run):
        run.mark_timed_out()
        return run
