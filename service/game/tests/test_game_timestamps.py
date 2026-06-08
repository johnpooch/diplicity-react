import pytest
from unittest.mock import patch, MagicMock
from django.utils import timezone
from django.contrib.auth import get_user_model

from game.models import Game
from phase.models import Phase, PhaseState
from member.models import Member
from draw_proposal.models import DrawProposal, DrawVote
from common.constants import GameStatus, PhaseStatus, PhaseType, MovementPhaseDuration, DeadlineMode
from adjudication import service as adjudication_service
from user_profile.models import UserProfile

User = get_user_model()


def make_user(username):
    user = User.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password="testpass",
    )
    UserProfile.objects.create(user=user, name=username)
    return user


@pytest.fixture
def italy_vs_germany_game(db, italy_vs_germany_variant, primary_user, secondary_user):
    game = Game.objects.create(
        variant=italy_vs_germany_variant,
        name="Timestamps Test Game",
        status=GameStatus.ACTIVE,
        deadline_mode=DeadlineMode.DURATION,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )
    italy_nation = italy_vs_germany_variant.nations.get(name="Italy")
    germany_nation = italy_vs_germany_variant.nations.get(name="Germany")
    Member.objects.create(game=game, user=primary_user, nation=italy_nation)
    Member.objects.create(game=game, user=secondary_user, nation=germany_nation)
    return game


@pytest.fixture
def active_phase_with_orders(
    italy_vs_germany_game,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    italy_vs_germany_venice_province,
    italy_vs_germany_rome_province,
    italy_vs_germany_naples_province,
    italy_vs_germany_kiel_province,
    italy_vs_germany_berlin_province,
    italy_vs_germany_munich_province,
    primary_user,
    secondary_user,
):
    game = italy_vs_germany_game
    italy_member = game.members.get(nation__name="Italy")
    germany_member = game.members.get(nation__name="Germany")

    phase = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1901,
        type=PhaseType.MOVEMENT,
        ordinal=1,
        status=PhaseStatus.ACTIVE,
    )
    ps_italy = phase.phase_states.create(member=italy_member, has_possible_orders=True)
    ps_germany = phase.phase_states.create(member=germany_member, has_possible_orders=True)

    for province in [italy_vs_germany_venice_province, italy_vs_germany_rome_province, italy_vs_germany_naples_province]:
        phase.supply_centers.create(province=province, nation=italy_vs_germany_italy_nation)
        phase.units.create(province=province, type="Army", nation=italy_vs_germany_italy_nation)
    for province in [italy_vs_germany_kiel_province, italy_vs_germany_berlin_province, italy_vs_germany_munich_province]:
        phase.supply_centers.create(province=province, nation=italy_vs_germany_germany_nation)
        phase.units.create(province=province, type="Army", nation=italy_vs_germany_germany_nation)

    from order.models import Order
    ps_italy.orders.create(source=italy_vs_germany_venice_province, order_type="Hold")
    ps_germany.orders.create(source=italy_vs_germany_kiel_province, order_type="Hold")

    return phase


BASIC_ADJUDICATION_DATA = {
    "season": "Fall",
    "year": 1901,
    "type": "Movement",
    "options": {},
    "supply_centers": [
        {"province": "ven", "nation": "Italy"},
        {"province": "rom", "nation": "Italy"},
        {"province": "nap", "nation": "Italy"},
        {"province": "kie", "nation": "Germany"},
        {"province": "ber", "nation": "Germany"},
        {"province": "mun", "nation": "Germany"},
    ],
    "units": [
        {"type": "Army", "nation": "Italy", "province": "ven", "dislodged": False, "dislodged_by": None},
        {"type": "Army", "nation": "Italy", "province": "rom", "dislodged": False, "dislodged_by": None},
        {"type": "Army", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
        {"type": "Army", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
        {"type": "Army", "nation": "Germany", "province": "ber", "dislodged": False, "dislodged_by": None},
        {"type": "Army", "nation": "Germany", "province": "mun", "dislodged": False, "dislodged_by": None},
    ],
    "resolutions": [
        {"province": "ven", "result": "OK", "by": None},
        {"province": "kie", "result": "OK", "by": None},
    ],
}


class TestGameStartedAt:
    @pytest.mark.django_db
    def test_started_at_set_when_game_starts(self, db, classical_variant, adjudication_data_classical):
        game = Game.objects.create_from_template(
            classical_variant,
            name="Test Start Timestamp",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        assert game.started_at is None

        nations = list(classical_variant.nations.all())
        members = []
        for i, nation in enumerate(nations):
            user = make_user(f"startuser{i}")
            m = game.members.create(user=user)
            members.append(m)

        before = timezone.now()
        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start(members=members)
        after = timezone.now()

        game.refresh_from_db()
        assert game.started_at is not None
        assert before <= game.started_at <= after

    @pytest.mark.django_db
    def test_pending_game_has_no_started_at(self, db, classical_variant):
        game = Game.objects.create_from_template(
            classical_variant,
            name="Test Pending Timestamps",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        assert game.started_at is None
        assert game.finished_at is None


class TestGameFinishedAtSoloVictory:
    @pytest.mark.django_db
    def test_finished_at_set_on_solo_victory(self, active_phase_with_orders):
        phase = active_phase_with_orders
        game = phase.game

        before = timezone.now()
        mock_victory = MagicMock()
        with patch("phase.models.resolve", return_value=BASIC_ADJUDICATION_DATA):
            with patch("phase.models.Victory.objects.try_create_victory", return_value=mock_victory):
                Phase.objects.resolve(phase)
        after = timezone.now()

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        assert game.finished_at is not None
        assert before <= game.finished_at <= after


class TestGameFinishedAtAbandonment:
    @pytest.mark.django_db
    def test_finished_at_set_on_abandonment(self, active_phase_with_orders):
        phase = active_phase_with_orders
        game = phase.game

        for member in game.members.all():
            member.civil_disorder = True
            member.save()

        before = timezone.now()
        with patch("phase.models.resolve", return_value=BASIC_ADJUDICATION_DATA):
            with patch("phase.models.Victory.objects.try_create_victory", return_value=None):
                Phase.objects.resolve(phase)
        after = timezone.now()

        game.refresh_from_db()
        assert game.status == GameStatus.ABANDONED
        assert game.finished_at is not None
        assert before <= game.finished_at <= after


class TestGameFinishedAtDraw:
    @pytest.mark.django_db
    def test_finished_at_set_on_draw_accepted(self, db, italy_vs_germany_variant):
        game = Game.objects.create(
            variant=italy_vs_germany_variant,
            name="Draw Timestamp Test",
            status=GameStatus.ACTIVE,
        )
        italy_nation = italy_vs_germany_variant.nations.get(name="Italy")
        germany_nation = italy_vs_germany_variant.nations.get(name="Germany")
        phase = Phase.objects.create(
            game=game,
            variant=italy_vs_germany_variant,
            season="Spring",
            year=1901,
            type=PhaseType.MOVEMENT,
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        m1 = game.members.create(user=make_user("draw_p1"), nation=italy_nation)
        m2 = game.members.create(user=make_user("draw_p2"), nation=germany_nation)

        proposal = DrawProposal.objects.create(game=game, created_by=m1, phase=phase)
        DrawVote.objects.create(proposal=proposal, member=m1, included=True, accepted=True)
        DrawVote.objects.create(proposal=proposal, member=m2, included=True, accepted=True)

        before = timezone.now()
        proposal.process_acceptance()
        after = timezone.now()

        game.refresh_from_db()
        assert game.status == GameStatus.COMPLETED
        assert game.finished_at is not None
        assert before <= game.finished_at <= after
