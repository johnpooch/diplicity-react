from django.db.models import Manager

from common.commands import command

from .policies import CanAssignPolicy, CanReportPolicy, CanUnassignPolicy
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
