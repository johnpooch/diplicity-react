from common.checks import Check


class HasNotReportedCheck(Check):
    reason = "already_reported"

    def check(self, member, actor):
        return not member.reports_received.filter(reporter__user_id=actor.pk).exists()
