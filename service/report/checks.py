from common.checks import Check


class HasUserCheck(Check):
    reason = "user_deleted"

    def check(self, member, actor):
        return member.user_id is not None


class IsNotOwnMemberCheck(Check):
    reason = "own_member"

    def check(self, member, actor):
        return member.user_id != actor.pk


class HasNotReportedCheck(Check):
    reason = "already_reported"

    def check(self, member, actor):
        if member.user_id is None:
            return True
        return not member.game.reports.filter(
            reporter_id=actor.pk, reported_user_id=member.user_id
        ).exists()
