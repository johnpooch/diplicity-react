import pytest
from django.contrib.auth import get_user_model

User = get_user_model()


@pytest.fixture
def primary_user(db):
    from user_profile.models import UserProfile

    user = User.objects.create_user(
        username="primary_user",
        email="primary@example.com",
        password="testpass123",
    )
    UserProfile.objects.create(user=user, name="Primary User")
    return user


@pytest.fixture
def secondary_user(db):
    from user_profile.models import UserProfile

    user = User.objects.create_user(
        username="secondary_user",
        email="secondary@example.com",
        password="testpass123",
    )
    UserProfile.objects.create(user=user, name="Secondary User")
    return user


@pytest.fixture
def tertiary_user(db):
    from user_profile.models import UserProfile

    user = User.objects.create_user(
        username="tertiary_user",
        email="tertiary@example.com",
        password="testpass123",
    )
    UserProfile.objects.create(user=user, name="Tertiary User")
    return user


@pytest.fixture
def game_factory(db):
    def _create(variant=None, status=None, sandbox=False, **kwargs):
        from game.models import Game
        from variant.models import Variant
        from common.constants import GameStatus

        if variant is None:
            variant = Variant.objects.first()

        if status is None:
            status = GameStatus.ACTIVE

        variant_solo_victory_sc_count = kwargs.pop("variant__solo_victory_sc_count", None)
        if variant_solo_victory_sc_count is not None:
            variant.solo_victory_sc_count = variant_solo_victory_sc_count
            variant.save()

        return Game.objects.create(
            variant=variant,
            status=status,
            sandbox=sandbox,
            name=f"Test Game {Game.objects.count()}",
            **kwargs,
        )

    return _create


@pytest.fixture
def phase_factory(db):
    def _create(game=None, type=None, season=None, year=None, status=None, **kwargs):
        from phase.models import Phase
        from common.constants import PhaseType, PhaseStatus

        if game is None:
            from game.models import Game
            from variant.models import Variant
            from common.constants import GameStatus

            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Phase.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if type is None:
            type = PhaseType.MOVEMENT

        if season is None:
            season = "Spring"

        if year is None:
            year = 1901

        if status is None:
            status = PhaseStatus.ACTIVE

        return Phase.objects.create(
            game=game,
            variant=game.variant,
            season=season,
            year=year,
            type=type,
            status=status,
            ordinal=kwargs.pop("ordinal", 1),
            **kwargs,
        )

    return _create


@pytest.fixture
def member_factory(db):
    def _create(game=None, user=None, nation=None, eliminated=False, kicked=False, **kwargs):
        from member.models import Member

        if game is None:
            from game.models import Game
            from variant.models import Variant
            from common.constants import GameStatus

            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Member.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if user is None:
            user = User.objects.create_user(
                username=f"testuser{Member.objects.count()}",
                email=f"test{Member.objects.count()}@example.com",
                password="testpass123",
            )
            from user_profile.models import UserProfile
            UserProfile.objects.get_or_create(user=user, defaults={"name": f"Test User {user.id}"})

        if nation is None:
            available_nations = game.variant.nations.exclude(
                id__in=game.members.values_list("nation_id", flat=True)
            )
            nation = available_nations.first()

        return Member.objects.create(
            game=game,
            user=user,
            nation=nation,
            eliminated=eliminated,
            kicked=kicked,
            **kwargs,
        )

    return _create


@pytest.fixture
def supply_center_factory(db):
    def _create(phase=None, nation=None, province=None):
        from phase.models import Phase
        from variant.models import Variant
        from common.constants import PhaseType

        if phase is None:
            from game.models import Game
            from common.constants import GameStatus

            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Phase.objects.count()}",
                status=GameStatus.ACTIVE,
            )
            phase = Phase.objects.create(
                game=game,
                variant=variant,
                season="Fall",
                year=1901,
                type=PhaseType.ADJUSTMENT,
                ordinal=1,
            )

        if nation is None:
            nation = phase.variant.nations.first()

        if province is None:
            province = phase.variant.provinces.filter(supply_center=True).first()

        return phase.supply_centers.create(nation=nation, province=province)

    return _create


@pytest.fixture
def draw_proposal_factory(db, member_factory):
    def _create(game=None, created_by=None, phase=None, included_member_ids=None, cancelled=False):
        from draw_proposal.models import DrawProposal, DrawVote

        if game is None:
            from game.models import Game
            from variant.models import Variant
            from common.constants import GameStatus

            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {DrawProposal.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if phase is None:
            from phase.models import Phase
            from common.constants import PhaseType, PhaseStatus

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
            cancelled=cancelled,
        )

        all_active_members = list(game.members.filter(eliminated=False, kicked=False))

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


@pytest.fixture
def api_client():
    from rest_framework.test import APIClient
    return APIClient()


@pytest.fixture
def authenticated_client(api_client, primary_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    refresh = RefreshToken.for_user(primary_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    return api_client
