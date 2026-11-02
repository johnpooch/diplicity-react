from django.db.models import Manager

from common.commands import command

from . import models
from .constants import ReportDecision
from .policies import (
    CanAssignPolicy,
    CanDecidePolicy,
    CanReportPolicy,
    CanUnassignPolicy,
    MarkablePolicy,
)
from .querysets import ReportQuerySet


class ReportManager(Manager.from_queryset(ReportQuerySet)):
    @command(requires=CanReportPolicy, locks=["game"])
    def report(self, member, actor, reason, note):
        return self.create(
            reporter=member.game.members.get(user_id=actor.pk),
            reported=member,
            reason=reason,
            note=note,
        )

    @command(requires=CanAssignPolicy)
    def assign(self, report, actor):
        report.assign(actor)
        return report

    @command(requires=CanUnassignPolicy)
    def unassign(self, report, actor):
        report.unassign()
        return report

    @command(requires=CanDecidePolicy, locks=["reported"])
    def approve(self, report, actor, note):
        report.decide(ReportDecision.APPROVED, actor, note)
        self.mark(report)
        return report

    @command(requires=CanDecidePolicy, locks=["reported"])
    def reject(self, report, actor, note):
        report.decide(ReportDecision.REJECTED, actor, note)
        return report

    @command(only_if=MarkablePolicy, locks=["reported"])
    def mark(self, report):
        return models.Mark.objects.create(member=report.reported, reason=report.reason)
