import pytest
from victory.models import Victory


@pytest.fixture
def victory_factory(db):
    def _create(game=None, winning_phase=None):
        from game.models import Game
        from phase.models import Phase
        from common.constants import PhaseType, GameStatus

        if game is None:
            from variant.models import Variant
            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Victory.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if winning_phase is None:
            winning_phase = Phase.objects.create(
                game=game,
                variant=game.variant,
                season="Fall",
                year=1901,
                type=PhaseType.ADJUSTMENT,
                ordinal=1,
            )

        return Victory.objects.create(
            game=game,
            winning_phase=winning_phase
        )

    return _create


@pytest.fixture
def supply_center_factory(db):
    def _create(phase=None, nation=None, province=None):
        from phase.models import Phase
        from nation.models import Nation
        from province.models import Province
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

        return phase.supply_centers.create(
            nation=nation,
            province=province
        )

    return _create


@pytest.fixture
def game_factory(db):
    def _create(variant=None, status=None, **kwargs):
        from game.models import Game
        from variant.models import Variant
        from common.constants import GameStatus

        if variant is None:
            variant = Variant.objects.first()

        if status is None:
            status = GameStatus.ACTIVE

        variant_solo_victory_sc_count = kwargs.pop('variant__solo_victory_sc_count', None)
        if variant_solo_victory_sc_count is not None:
            variant.solo_victory_sc_count = variant_solo_victory_sc_count
            variant.save()

        return Game.objects.create(
            variant=variant,
            status=status,
            name=f"Test Game {Game.objects.count()}",
            **kwargs
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
            type = PhaseType.ADJUSTMENT

        if season is None:
            season = "Fall"

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
            ordinal=kwargs.pop('ordinal', 1),
            **kwargs
        )

    return _create


@pytest.fixture
def member_factory(db):
    def _create(game=None, user=None, nation=None, **kwargs):
        from member.models import Member
        from django.contrib.auth import get_user_model

        User = get_user_model()

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
                password="testpass123"
            )

        if nation is None:
            available_nations = game.variant.nations.exclude(
                id__in=game.members.values_list('nation_id', flat=True)
            )
            nation = available_nations.first()

        return Member.objects.create(
            game=game,
            user=user,
            nation=nation,
            **kwargs
        )

    return _create
