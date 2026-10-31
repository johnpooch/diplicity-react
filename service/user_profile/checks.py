from common.checks import Check

from .models import UserProfile


class IsModeratorCheck(Check):
    reason = "not_moderator"

    def check(self, instance, actor):
        return UserProfile.objects.filter(user_id=actor.pk, is_moderator=True).exists()
