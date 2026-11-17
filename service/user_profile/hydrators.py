from collections import defaultdict

from django.utils import timezone

from common.constants import CommitmentRequirement
from common.loaders import Hydrator
from game.models import Game
from member.checks import MeetsCommitmentRequirementCheck
from member.models import Member
from rating.models import Rating
from report.models import Mark

from .utils import get_player_stats


class CanCreateCommittedGameHydrator(Hydrator):
    def hydrate(self, profiles, actor):
        for profile in profiles:
            profile.can_create_committed_game = MeetsCommitmentRequirementCheck.decide(
                Game(commitment_requirement=CommitmentRequirement.COMMITTED),
                profile.user,
            ).allowed


class CommitmentSquaresHydrator(Hydrator):
    def hydrate(self, profiles, actor):
        humans = [profile.user_id for profile in profiles if not profile.is_bot]
        squares = list(Member.objects.filter(user_id__in=humans).commitment_squares())
        Member.objects.hydrate_commitment_breakdowns(squares)
        squares_by_user = defaultdict(list)
        for square in squares:
            squares_by_user[square.user_id].append(square)
        for profile in profiles:
            profile.commitment_squares = squares_by_user[profile.user_id]


class ProfileRatingHydrator(Hydrator):
    def hydrate(self, profiles, actor):
        humans = [profile.user_id for profile in profiles if not profile.is_bot]
        ratings = {
            rating.user_id: rating
            for rating in Rating.objects.filter(user_id__in=humans)
            .with_rank(timezone.now())
            .with_record()
        }
        for profile in profiles:
            profile.rating = ratings.get(profile.user_id)


class MarksHydrator(Hydrator):
    def hydrate(self, profiles, actor):
        humans = [profile.user_id for profile in profiles if not profile.is_bot]
        marks_by_user = defaultdict(list)
        for mark in (
            Mark.objects.filter(member__user_id__in=humans)
            .select_related("member")
            .order_by("-created_at")
        ):
            marks_by_user[mark.member.user_id].append(mark)
        for profile in profiles:
            profile.marks = marks_by_user[profile.user_id]


class PlayerStatsHydrator(Hydrator):
    def hydrate(self, profiles, actor):
        for profile in profiles:
            stats = get_player_stats(profile.user)
            profile.total_games = stats["total_games"]
            profile.active_games = stats["active_games"]
