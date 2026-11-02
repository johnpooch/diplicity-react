from common.checks import Check


class IsModeratorCheck(Check):
    reason = "not_moderator"

    def check(self, instance, actor):
        profile = getattr(actor, "profile", None)
        return profile is not None and profile.is_moderator
