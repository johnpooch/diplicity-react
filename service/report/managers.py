from django.apps import apps
from django.db.models import Manager

from common.commands import command
from emit import emit

from . import models
from .constants import ReportDecision
from .policies import (
    CanAssignPolicy,
    CanDecidePolicy,
    CanReportPolicy,
    CanUnassignPolicy,
)
from .querysets import ReportQuerySet


class ReportManager(Manager.from_queryset(ReportQuerySet)):

    def save_report(self, report):
        report.save()
        type(report.reported.game).objects.bump_version([report.reported.game_id])

    def delete_reports(self, reports):
        game_ids = tuple(reports.values_list("reported__game_id", flat=True))
        result = reports.delete()
        apps.get_model("game", "Game").objects.bump_version(game_ids)
        return result

    @command(requires=CanReportPolicy, locks=["game"])
    def report(self, member, actor, reason, note):
        report = self.create(
            reporter=member.game.members.get(user_id=actor.pk),
            reported=member,
            reason=reason,
            note=note,
        )
        emit("report_opened", game=member.game, actor=actor, report=report)
        type(member.game).objects.bump_version([member.game_id])
        return report

    @command(requires=CanAssignPolicy)
    def assign(self, report, actor):
        report.assign(actor)
        type(report.reported.game).objects.bump_version([report.reported.game_id])
        return report

    @command(requires=CanUnassignPolicy)
    def unassign(self, report, actor):
        report.unassign()
        type(report.reported.game).objects.bump_version([report.reported.game_id])
        return report

    @command(requires=CanDecidePolicy, locks=["reported"])
    def approve(self, report, actor, note):
        report.decide(ReportDecision.APPROVED, actor, note)
        models.Mark.objects.create_idempotent(
            member=report.reported, reason=report.reason
        )
        type(report.reported.game).objects.bump_version([report.reported.game_id])
        return report

    @command(requires=CanDecidePolicy, locks=["reported"])
    def reject(self, report, actor, note):
        report.decide(ReportDecision.REJECTED, actor, note)
        type(report.reported.game).objects.bump_version([report.reported.game_id])
        return report


class MarkManager(Manager):
    def create_idempotent(self, member, reason):
        return self.get_or_create(member=member, reason=reason)[0]
