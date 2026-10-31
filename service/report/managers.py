from django.db.models import Manager

from common.commands import command

from .policies import CanReportPolicy
from .querysets import ReportQuerySet


class ReportManager(Manager.from_queryset(ReportQuerySet)):
    @command(requires=CanReportPolicy, locks=["game"])
    def report(self, member, actor, reason, note):
        return self.create(
            game=member.game,
            reporter=actor,
            reported_member=member,
            reported_user=member.user,
            reason=reason,
            note=note,
        )
