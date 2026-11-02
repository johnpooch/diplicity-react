from django.db.models import Manager

from common.commands import command
from emit import emit

from .policies import CanAssignPolicy, CanReportPolicy, CanUnassignPolicy
from .querysets import ReportQuerySet


class ReportManager(Manager.from_queryset(ReportQuerySet)):
    @command(requires=CanReportPolicy, locks=["game"])
    def report(self, member, actor, reason, note):
        report = self.create(
            reporter=member.game.members.get(user_id=actor.pk),
            reported=member,
            reason=reason,
            note=note,
        )
        emit("report_opened", game=member.game, actor=actor, report=report)
        return report

    @command(requires=CanAssignPolicy)
    def assign(self, report, actor):
        report.assign(actor)
        return report

    @command(requires=CanUnassignPolicy)
    def unassign(self, report, actor):
        report.unassign()
        return report
