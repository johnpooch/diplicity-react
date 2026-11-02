from common.checks import Check

from .constants import ReportDecision, ReportStatus


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


class IsAssignedInGameCheck(Check):
    reason = "not_assignee"

    def check(self, game, actor):
        return (
            actor.pk is not None
            and game.members.filter(
                reports_received__assigned_to_id=actor.pk,
                reports_received__review__isnull=True,
            ).exists()
        )


class IsApprovedCheck(Check):
    reason = "not_approved"

    def check(self, report, actor):
        return report.status == ReportDecision.APPROVED


class IsUnmarkedCheck(Check):
    reason = "already_marked"

    def check(self, report, actor):
        return not report.reported.marks.filter(reason=report.reason).exists()
