from django.db.models import Max, Min

from common.checks import Check

MINIMUM_YEARS = 2


class HasPlayedMinimumYearsCheck(Check):
    def check(self, game, actor):
        years = game.phases.aggregate(first=Min("year"), last=Max("year"))
        if years["first"] is None:
            return False
        return years["last"] - years["first"] >= MINIMUM_YEARS


class IsUnratedCheck(Check):
    def check(self, game, actor):
        return not game.members.filter(rating_result__isnull=False).exists()


class IsRankedVariantCheck(Check):
    reason = "variant_not_ranked"

    def check(self, game, actor):
        return game.variant.ranked
