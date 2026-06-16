import pytest
from django.urls import reverse
from rest_framework import status

from common.constants import GameStatus, PhaseStatus
from game.models import Game
from phase.models import PhaseState


LIST_URL = reverse("game-list")


def _get_game_data(response, game_id):
    results = response.data.get("results", response.data)
    for item in results:
        if item["id"] == game_id:
            return item
    return None


@pytest.fixture
def active_game_with_member_and_phase_state(
    db,
    primary_user,
    classical_variant,
    classical_england_nation,
):
    game = Game.objects.create(
        name="Status Field Test Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )
    member = game.members.create(user=primary_user, nation=classical_england_nation)
    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )
    phase_state = phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_confirmed=False,
    )
    return game, member, phase, phase_state


@pytest.mark.django_db
def test_order_status_orders_required(
    authenticated_client,
    active_game_with_member_and_phase_state,
):
    game, member, phase, phase_state = active_game_with_member_and_phase_state
    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert data["order_status"] == "orders_required"


@pytest.mark.django_db
def test_order_status_orders_submitted(
    authenticated_client,
    active_game_with_member_and_phase_state,
):
    game, member, phase, phase_state = active_game_with_member_and_phase_state
    phase_state.orders_confirmed = True
    phase_state.save()

    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert data["order_status"] == "orders_submitted"


@pytest.mark.django_db
def test_order_status_no_orders_required(
    authenticated_client,
    active_game_with_member_and_phase_state,
):
    game, member, phase, phase_state = active_game_with_member_and_phase_state
    phase_state.has_possible_orders = False
    phase_state.orders_confirmed = False
    phase_state.save()

    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert data["order_status"] == "no_orders_required"


@pytest.mark.django_db
def test_order_status_null_for_pending_game(
    authenticated_client,
    db,
    primary_user,
    classical_variant,
):
    game = Game.objects.create(
        name="Pending Status Field Test Game",
        variant=classical_variant,
        status=GameStatus.PENDING,
    )
    game.members.create(user=primary_user)

    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert data["order_status"] is None


@pytest.mark.django_db
def test_order_status_null_when_not_a_member(
    authenticated_client,
    db,
    secondary_user,
    classical_variant,
    classical_france_nation,
):
    game = Game.objects.create(
        name="Non-Member Status Field Test Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )
    other_member = game.members.create(user=secondary_user, nation=classical_france_nation)
    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )
    phase.phase_states.create(
        member=other_member,
        has_possible_orders=True,
        orders_confirmed=False,
    )

    response = authenticated_client.get(LIST_URL)
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert data["order_status"] is None


@pytest.mark.django_db
def test_member_status_includes_civil_disorder(
    authenticated_client,
    db,
    primary_user,
    classical_variant,
    classical_england_nation,
):
    game = Game.objects.create(
        name="Civil Disorder Status Field Test Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )
    member = game.members.create(
        user=primary_user,
        nation=classical_england_nation,
        civil_disorder=True,
    )
    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )
    phase.phase_states.create(member=member, has_possible_orders=True)

    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert "civil_disorder" in data["member_status"]


@pytest.mark.django_db
def test_member_status_includes_nmr(
    authenticated_client,
    db,
    primary_user,
    classical_variant,
    classical_england_nation,
):
    game = Game.objects.create(
        name="NMR Status Field Test Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )
    member = game.members.create(user=primary_user, nation=classical_england_nation)

    prev_phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.COMPLETED,
        ordinal=1,
    )
    prev_phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_outcome=PhaseState.OrdersOutcome.NMR,
    )

    current_phase = game.phases.create(
        variant=classical_variant,
        season="Fall",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=2,
    )
    current_phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_confirmed=False,
    )

    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert "nmr" in data["member_status"]


@pytest.mark.django_db
def test_member_status_empty_when_no_flags(
    authenticated_client,
    active_game_with_member_and_phase_state,
):
    game, member, phase, phase_state = active_game_with_member_and_phase_state

    response = authenticated_client.get(LIST_URL + "?mine=1")
    assert response.status_code == status.HTTP_200_OK
    data = _get_game_data(response, game.id)
    assert data is not None
    assert data["member_status"] == []
