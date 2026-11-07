from django.db.models import Manager
from django.utils import timezone

from common.commands import command

from . import models
from .calculation import DEFAULT_PARAMETERS, Player, rate
from .policies import RateablePolicy
from .querysets import RatingResultQuerySet


class RatingResultManager(Manager.from_queryset(RatingResultQuerySet)):
    @command(only_if=RateablePolicy)
    def rate_game(self, game):
        rated_at = timezone.now()
        members = list(
            game.members.players()
            .humans()
            .select_related("nation__handicap")
            .prefetch_related("replaces")
        )
        user_ids = sorted(member.user_id for member in members)
        models.Rating.objects.bulk_create(
            [
                models.Rating(
                    user_id=user_id,
                    rating=DEFAULT_PARAMETERS.starting_rating,
                    deviation=DEFAULT_PARAMETERS.max_deviation,
                    rated_at=rated_at,
                )
                for user_id in user_ids
            ],
            ignore_conflicts=True,
        )
        ratings = (
            models.Rating.objects.select_for_update()
            .order_by("user_id")
            .in_bulk(user_ids, field_name="user_id")
        )
        victors = set(game.victory.members.all())
        results = rate(
            [
                Player(
                    member_id=member.pk,
                    seat=member.nation_id,
                    rating=ratings[member.user_id].rating,
                    deviation=ratings[member.user_id].deviation,
                    rated_at=ratings[member.user_id].rated_at,
                    handicap=member.nation.handicap.offset,
                    victor=member in victors,
                    departed=member.replaced_by_id is not None,
                    replacement=bool(member.replaces.all()),
                )
                for member in members
            ],
            rated_at,
        )
        for member, result in zip(members, results):
            rating_result = self.create(
                member=member,
                rating_before=result.rating_before,
                deviation_before=result.deviation_before,
                rating_after=result.rating_after,
                deviation_after=result.deviation_after,
                handicap=result.handicap,
                protected=result.protected,
            )
            rating_result.record_pairings(result.pairings)
            if not result.protected:
                ratings[member.user_id].record(rating_result)
        type(game).objects.bump_version([game.pk])
        return game
