import pytest

from common.constants import GameStatus, PhaseStatus, PhaseType
from game.models import Game
from phase.models import Phase
from variant.models import Variant

from .models import DrawProposal, DrawVote


@pytest.fixture
def draw_proposal_factory(db, member_factory):
    def _create(game=None, created_by=None, phase=None, included_member_ids=None, cancelled_at=None):
        if game is None:
            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {DrawProposal.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if phase is None:
            phase = Phase.objects.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.ACTIVE,
                ordinal=1,
            )

        if created_by is None:
            created_by = member_factory(game=game)

        proposal = DrawProposal.objects.create(
            game=game,
            created_by=created_by,
            phase=phase,
            cancelled_at=cancelled_at,
        )

        all_active_members = list(game.members.holding_seat().filter(eliminated_at__isnull=True))

        if included_member_ids is None:
            included_member_ids = [created_by.id]

        for member in all_active_members:
            is_included = member.id in included_member_ids
            is_proposer = member.id == created_by.id
            DrawVote.objects.create(
                proposal=proposal,
                member=member,
                included=is_included,
                accepted=True if is_proposer else None,
            )

        return proposal

    return _create
