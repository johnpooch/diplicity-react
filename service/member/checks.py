from common.checks import Check
from common.constants import ActionBlockedReason, CommitmentRequirement


class HasUserCheck(Check):
    reason = "user_deleted"

    def check(self, member, actor):
        return member.user_id is not None


class IsNotOwnMemberCheck(Check):
    reason = "own_member"

    def check(self, member, actor):
        return member.user_id != actor.pk


class MeetsCommitmentRequirementCheck(Check):
    reason = ActionBlockedReason.COMMITMENT_TOO_LOW

    def check(self, game, actor):
        if game.commitment_requirement != CommitmentRequirement.COMMITTED:
            return True
        return actor.profile.commitment_total >= CommitmentRequirement.COMMITTED_THRESHOLD
