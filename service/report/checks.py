from common.checks import Check

from .constants import ReportStatus


class HasNotReportedCheck(Check):
    reason = "already_reported"

    def check(self, member, actor):
        return not member.reports_received.filter(reporter__user_id=actor.pk).exists()


class IsPendingCheck(Check):
    reason = "already_reviewed"

    def check(self, report, actor):
        return report.status == ReportStatus.PENDING


class IsUnassignedCheck(Check):
    reason = "already_assigned"

    def check(self, report, actor):
        return report.assigned_to_id is None


class IsAssigneeCheck(Check):
    reason = "not_assignee"

    def check(self, report, actor):
        return report.assigned_to_id is not None and report.assigned_to_id == actor.pk
