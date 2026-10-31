from common.checks import Check


class HasUserCheck(Check):
    reason = "user_deleted"

    def check(self, member, actor):
        return member.user_id is not None


class IsNotOwnMemberCheck(Check):
    reason = "own_member"

    def check(self, member, actor):
        return member.user_id != actor.pk
