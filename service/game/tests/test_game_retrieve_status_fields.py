import pytest
from django.urls import reverse
from rest_framework import status

from common.constants import GameStatus, PhaseStatus
from game.models import Game
from phase.models import PhaseState


@pytest.mark.django_db
def test_order_status_reads_current_phase_state(
    authenticated_client,
    db,
    primary_user,
    classical_variant,
    classical_england_nation,
):
    game = Game.objects.create(
        name="Retrieve Order Status Game",
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
    phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_confirmed=False,
    )

    response = authenticated_client.get(reverse("game-retrieve", args=[game.id]))

    assert response.status_code == status.HTTP_200_OK
    assert response.data["order_status"] == "orders_required"


@pytest.mark.django_db
def test_member_status_reads_latest_completed_phase_state(
    authenticated_client,
    db,
    primary_user,
    classical_variant,
    classical_england_nation,
):
    game = Game.objects.create(
        name="Retrieve Member Status Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )
    member = game.members.create(user=primary_user, nation=classical_england_nation)

    oldest_phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.COMPLETED,
        ordinal=1,
    )
    oldest_phase.phase_states.create(member=member, has_possible_orders=True)

    latest_completed_phase = game.phases.create(
        variant=classical_variant,
        season="Fall",
        year=1901,
        type="Movement",
        status=PhaseStatus.COMPLETED,
        ordinal=2,
    )
    latest_completed_phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_outcome=PhaseState.OrdersOutcome.NMR,
    )

    current_phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1902,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=3,
    )
    current_phase.phase_states.create(
        member=member,
        has_possible_orders=True,
        orders_confirmed=False,
    )

    response = authenticated_client.get(reverse("game-retrieve", args=[game.id]))

    assert response.status_code == status.HTTP_200_OK
    assert "nmr" in response.data["member_status"]
