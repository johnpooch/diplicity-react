from re import I
import pytest
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch
from rest_framework import status
from game.models import Game
from member.models import Member
from common.constants import (
    DeadlineMode,
    GameStatus,
    NationAssignment,
    OrderCreationStep,
    OrderResolutionStatus,
    PhaseStatus,
    UnitType,
)

resolve_all_url = reverse("phase-resolve-all")


def create_active_game(authenticated_client, authenticated_client_for_secondary_user, italy_vs_germany_variant):
    create_url = reverse("game-create")
    create_payload = {
        "name": "Italy vs Germany Test",
        "variant_id": italy_vs_germany_variant.id,
        "nation_assignment": NationAssignment.ORDERED,
        "private": False,
        "deadline_mode": DeadlineMode.DURATION,
    }
    create_response = authenticated_client.post(create_url, create_payload, format="json")
    game_id = create_response.data["id"]
    join_url = reverse("game-join", args=[game_id])
    authenticated_client_for_secondary_user.post(join_url)
    return Game.objects.get(id=game_id)


@pytest.mark.django_db
def test_create_game_with_classical_variant_one_user_joins(
    authenticated_client,
    authenticated_client_for_secondary_user,
    classical_variant,
    primary_user,
    secondary_user,
):
    """
    - User creates a game with classical variant
    - Second user joins the game
    - Nations are not assigned yet
    - Initial phase is created
    - Public channel exists
    """
    # Step 1: Create game
    create_url = reverse("game-create")
    create_payload = {
        "name": "Integration Test Game",
        "variant_id": classical_variant.id,
        "nation_assignment": NationAssignment.RANDOM,
        "private": False,
        "deadline_mode": DeadlineMode.DURATION,
    }
    create_response = authenticated_client.post(create_url, create_payload, format="json")
    assert create_response.status_code == status.HTTP_201_CREATED

    game_id = create_response.data["id"]
    game = Game.objects.get(id=game_id)

    # Verify initial game state
    assert game.status == GameStatus.PENDING
    assert game.members.count() == 1
    assert game.members.first().user == primary_user

    # Verify public channel was created
    public_channels = game.channels.filter(private=False)
    assert public_channels.count() == 1
    assert public_channels.first().name == "Public Press"

    # Verify template phase was created
    assert game.phases.count() == 1
    pending_phase = game.phases.first()
    assert pending_phase.variant == classical_variant
    assert pending_phase.ordinal == 1
    assert pending_phase.status == PhaseStatus.PENDING

    # Second user joins
    join_url = reverse("game-join", args=[game_id])
    join_response = authenticated_client_for_secondary_user.post(join_url)
    assert join_response.status_code == status.HTTP_201_CREATED

    # Refresh game state
    game.refresh_from_db()

    # Verify both users are members
    assert game.members.count() == 2
    member_users = [member.user for member in game.members.all()]
    assert primary_user in member_users
    assert secondary_user in member_users

    # For classical variant with 2 players, game should still be pending
    # (Classical normally requires 7 players, but this tests the workflow)
    assert game.status == GameStatus.PENDING

    # Verify nations are not assigned yet
    members_with_nations = game.members.exclude(nation__isnull=True)
    assert members_with_nations.count() == 0


@pytest.mark.django_db
def test_create_game_with_italy_vs_germany_variant_one_user_joins(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    primary_user,
    secondary_user,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    """
    - User creates a game with italy vs germany variant
    - Initial phase is created
    - Second user joins the game
    - Public channel exists
    - Game automatically starts
    - Nations are assigned
    - Active phase is created
    """
    # Create game with 2-player variant
    create_url = reverse("game-create")
    create_payload = {
        "name": "Italy vs Germany Test",
        "variant_id": italy_vs_germany_variant.id,
        "nation_assignment": NationAssignment.RANDOM,
        "private": False,
        "deadline_mode": DeadlineMode.DURATION,
    }
    create_response = authenticated_client.post(create_url, create_payload, format="json")
    assert create_response.status_code == status.HTTP_201_CREATED

    game_id = create_response.data["id"]

    # Second user joins
    join_url = reverse("game-join", args=[game_id])
    join_response = authenticated_client_for_secondary_user.post(join_url)
    assert join_response.status_code == status.HTTP_201_CREATED

    # Game should now be full and started
    game = Game.objects.get(id=game_id)
    assert game.members.count() == 2
    assert game.status == GameStatus.ACTIVE

    # Verify nations are assigned
    italy_member = game.members.filter(nation__name="Italy").first()
    germany_member = game.members.filter(nation__name="Germany").first()

    assert italy_member is not None
    assert germany_member is not None
    assert italy_member.user != germany_member.user


@pytest.mark.django_db
def test_create_game_with_classical_variant_one_user_leaves_and_rejoins(
    authenticated_client,
    authenticated_client_for_secondary_user,
    classical_variant,
):
    """
    - User creates a game with classical variant
    - Second user joins the game
    - Second user leaves the game
    - Second user rejoins the game
    """
    # Create and join game
    create_url = reverse("game-create")
    create_payload = {
        "name": "Leave/Rejoin Test",
        "variant_id": classical_variant.id,
        "nation_assignment": NationAssignment.RANDOM,
        "private": False,
        "deadline_mode": DeadlineMode.DURATION,
    }
    create_response = authenticated_client.post(create_url, create_payload, format="json")
    game_id = create_response.data["id"]

    join_url = reverse("game-join", args=[game_id])
    authenticated_client_for_secondary_user.post(join_url)

    game = Game.objects.get(id=game_id)
    assert game.members.count() == 2

    # Second user leaves
    leave_url = reverse("game-leave", args=[game_id])
    leave_response = authenticated_client_for_secondary_user.delete(leave_url)
    assert leave_response.status_code == status.HTTP_204_NO_CONTENT

    game.refresh_from_db()
    assert game.members.count() == 1

    # Second user can rejoin
    rejoin_response = authenticated_client_for_secondary_user.post(join_url)
    assert rejoin_response.status_code == status.HTTP_201_CREATED

    game.refresh_from_db()
    assert game.members.count() == 2


@pytest.mark.django_db
def test_active_game_create_orders_and_confirm(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    """
    - Primary user creates an order (interactive)
    - Secondary user creates an order (interactive)
    - Both users confirm their orders
    - Game resolves
    """
    active_game = create_active_game(
        authenticated_client, authenticated_client_for_secondary_user, italy_vs_germany_variant
    )
    create_order_url = reverse("order-create", args=[active_game.id])
    first_phase = active_game.current_phase

    italy_member = active_game.members.filter(nation__name="Italy").first()
    germany_member = active_game.members.filter(nation__name="Germany").first()

    # Primary user creates an order

    create_order_payload = {"selected": ["kie"]}
    create_order_response = authenticated_client.post(create_order_url, create_order_payload, format="json")

    assert create_order_response.status_code == status.HTTP_201_CREATED
    assert create_order_response.data["selected"] == ["kie"]
    assert create_order_response.data["options"][0] == {"value": "Hold", "label": "Hold"}
    assert create_order_response.data["options"][1] == {"value": "Move", "label": "Move"}
    assert create_order_response.data["options"][2] == {"value": "Support", "label": "Support"}

    create_order_payload = {"selected": ["kie", "Move"]}
    create_order_response = authenticated_client.post(create_order_url, create_order_payload, format="json")

    assert create_order_response.status_code == status.HTTP_201_CREATED
    assert create_order_response.data["selected"] == ["kie", "Move"]
    assert create_order_response.data["options"][0] == {"value": "bal", "label": "Baltic Sea"}
    assert create_order_response.data["options"][1] == {"value": "ber", "label": "Berlin"}

    create_order_payload = {"selected": ["kie", "Move", "den"]}
    create_order_response = authenticated_client.post(create_order_url, create_order_payload, format="json")
    assert create_order_response.status_code == status.HTTP_201_CREATED

    assert create_order_response.data["selected"] == ["kie", "Move", "den"]
    assert create_order_response.data["options"] == []
    assert create_order_response.data["step"] == OrderCreationStep.COMPLETED
    assert create_order_response.data["title"] == "Kiel will move to Denmark"

    # Secondary user creates an order
    create_order_payload = {"selected": ["ven"]}
    create_order_response = authenticated_client_for_secondary_user.post(
        create_order_url, create_order_payload, format="json"
    )

    assert create_order_response.status_code == status.HTTP_201_CREATED
    assert create_order_response.data["selected"] == ["ven"]
    assert create_order_response.data["options"][0] == {"value": "Hold", "label": "Hold"}
    assert create_order_response.data["options"][1] == {"value": "Move", "label": "Move"}
    assert create_order_response.data["options"][2] == {"value": "Support", "label": "Support"}

    create_order_payload = {"selected": ["ven", "Move"]}
    create_order_response = authenticated_client_for_secondary_user.post(
        create_order_url, create_order_payload, format="json"
    )
    assert create_order_response.status_code == status.HTTP_201_CREATED
    assert create_order_response.data["selected"] == ["ven", "Move"]
    assert create_order_response.data["options"][0] == {"value": "apu", "label": "Apulia"}
    assert create_order_response.data["options"][1] == {"value": "pie", "label": "Piedmont"}

    create_order_payload = {"selected": ["ven", "Move", "tri"]}
    create_order_response = authenticated_client_for_secondary_user.post(
        create_order_url, create_order_payload, format="json"
    )
    assert create_order_response.status_code == status.HTTP_201_CREATED
    assert create_order_response.data["selected"] == ["ven", "Move", "tri"]
    assert create_order_response.data["options"] == []
    assert create_order_response.data["step"] == OrderCreationStep.COMPLETED
    assert create_order_response.data["title"] == "Venice will move to Trieste"

    # Phase has not resolved yet
    first_phase.refresh_from_db()
    assert first_phase.status == PhaseStatus.ACTIVE

    confirm_order_url = reverse("game-confirm-phase", args=[active_game.id])

    # Primary user confirms their order
    confirm_order_response = authenticated_client.put(confirm_order_url)
    assert confirm_order_response.status_code == status.HTTP_200_OK

    # Phase has not resolved yet
    first_phase.refresh_from_db()
    assert first_phase.status == PhaseStatus.ACTIVE

    # Secondary user confirms their order
    confirm_order_response = authenticated_client_for_secondary_user.put(confirm_order_url)
    assert confirm_order_response.status_code == status.HTTP_200_OK

    # Simulate the scheduled resolver task running
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    # Notification is sent to both users
    mock_send_notification_to_users.assert_called_with(
        user_ids=[germany_member.user.id, italy_member.user.id],
        title="Phase Resolved",
        body=f"Phase '{first_phase.name}' has been resolved!",
        notification_type="phase_resolved",
        data={"game_id": str(active_game.id)},
    )

    # Second phase has been created
    second_phase = active_game.current_phase
    assert second_phase.status == PhaseStatus.ACTIVE
    assert second_phase.season == "Spring"
    assert second_phase.year == 1901
    assert second_phase.type == "Retreat"

    # Test auto-resolution behavior: Retreat phase should resolve immediately
    # since typically no retreat moves are possible in small variants
    assert second_phase.should_resolve_immediately

    # Simulate the scheduled resolver task running
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1  # At least the retreat phase resolved

    # First phase has resolved
    first_phase.refresh_from_db()
    assert first_phase.status == PhaseStatus.COMPLETED

    # Notification is sent to both users (combined notification for skipped phases)
    third_phase = active_game.current_phase
    mock_send_notification_to_users.assert_called_with(
        user_ids=[germany_member.user.id, italy_member.user.id],
        title="Phase Resolved",
        body=f"{second_phase.name} resolved. No retreats needed. Next: {third_phase.name}.",
        notification_type="phase_resolved",
        data={"game_id": str(active_game.id)},
    )


@pytest.mark.django_db
def test_scheduled_phase_resolution_after_time_elapsed(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    """
    - Primary user creates an order (interactive)
    - Primary user confirms their order
    - Time advances past the phase duration
    - Game resolves
    """
    active_game = create_active_game(
        authenticated_client, authenticated_client_for_secondary_user, italy_vs_germany_variant
    )
    current_phase = active_game.current_phase

    # Only primary user creates and confirmdds an order (secondary user does nothing)
    create_order_url = reverse("order-create", args=[active_game.id])
    create_order_payload = {"selected": ["kie", "Move", "den"]}
    authenticated_client.post(create_order_url, create_order_payload, format="json")

    confirm_order_url = reverse("game-confirm-phase", args=[active_game.id])
    authenticated_client.put(confirm_order_url)

    # Phase should not resolve immediately since not all users with orders confirmed
    current_phase.refresh_from_db()
    assert not current_phase.should_resolve_immediately

    # Simulate time advancing by 25 hours (past the 24-hour phase duration)
    future_time = timezone.now() + timedelta(hours=25)

    with patch("django.utils.timezone.now", return_value=future_time):
        # Simulate the scheduled resolver task running
        resolve_response = authenticated_client.post(resolve_all_url)
        assert resolve_response.status_code == status.HTTP_200_OK
        assert resolve_response.data["resolved"] >= 1  # Phase resolved due to time elapsed

    # Verify the phase was resolved and a new phase created
    current_phase.refresh_from_db()
    assert current_phase.status == PhaseStatus.COMPLETED

    new_phase = active_game.current_phase
    assert new_phase.id != current_phase.id
    assert new_phase.status == PhaseStatus.ACTIVE


@pytest.mark.django_db
def test_active_game_create_move_order_fleet_to_named_coast(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    active_game = create_active_game(
        authenticated_client, authenticated_client_for_secondary_user, italy_vs_germany_variant
    )
    create_order_url = reverse("order-create", args=[active_game.id])
    first_phase = active_game.current_phase

    italy_member = active_game.members.filter(nation__name="Italy").first()
    germany_member = active_game.members.filter(nation__name="Germany").first()

    # Secondary user creates an order
    create_order_payload = {"selected": ["nap", "Move", "tys"]}
    create_order_response = authenticated_client_for_secondary_user.post(
        create_order_url, create_order_payload, format="json"
    )

    # Phase has not resolved yet
    confirm_order_url = reverse("game-confirm-phase", args=[active_game.id])

    # Primary user confirms their order
    confirm_order_response = authenticated_client.put(confirm_order_url)
    assert confirm_order_response.status_code == status.HTTP_200_OK

    # Phase has not resolved yet
    first_phase.refresh_from_db()
    assert first_phase.status == PhaseStatus.ACTIVE

    # Secondary user confirms their order
    confirm_order_response = authenticated_client_for_secondary_user.put(confirm_order_url)
    assert confirm_order_response.status_code == status.HTTP_200_OK

    # Simulate the scheduled resolver task running
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    # Second phase has been created
    second_phase = active_game.current_phase
    assert second_phase.status == PhaseStatus.ACTIVE
    assert second_phase.season == "Spring"
    assert second_phase.year == 1901
    assert second_phase.type == "Retreat"

    # Test auto-resolution behavior: Retreat phase should resolve immediately
    # since typically no retreat moves are possible in small variants
    assert second_phase.should_resolve_immediately

    # Simulate the scheduled resolver task running
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1  # At least the retreat phase resolved

    # First phase has resolved
    first_phase.refresh_from_db()
    assert first_phase.status == PhaseStatus.COMPLETED

    # Secondary user creates an order
    create_order_payload = {"selected": ["tys", "Move", "gol"]}
    create_order_response = authenticated_client_for_secondary_user.post(
        create_order_url, create_order_payload, format="json"
    )

    confirm_order_response = authenticated_client.put(confirm_order_url)
    confirm_order_response = authenticated_client_for_secondary_user.put(confirm_order_url)

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    phase = active_game.current_phase
    assert phase.status == PhaseStatus.ACTIVE
    assert phase.season == "Fall"
    assert phase.year == 1901
    assert phase.type == "Retreat"

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    phase = active_game.current_phase
    assert phase.status == PhaseStatus.ACTIVE
    assert phase.season == "Fall"
    assert phase.year == 1901
    assert phase.type == "Adjustment"

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    phase = active_game.current_phase
    assert phase.status == PhaseStatus.ACTIVE
    assert phase.season == "Spring"
    assert phase.year == 1902
    assert phase.type == "Movement"

    create_order_payload = {"selected": ["gol", "Move", "spa", "spa/sc"]}
    create_order_response = authenticated_client_for_secondary_user.post(
        create_order_url, create_order_payload, format="json"
    )
    assert create_order_response.status_code == status.HTTP_201_CREATED
    assert create_order_response.data["selected"] == ["gol", "Move", "spa", "spa/sc"]
    assert create_order_response.data["step"] == OrderCreationStep.COMPLETED
    assert create_order_response.data["title"] == "Gulf of Lyon will move to Spain"

    confirm_order_response = authenticated_client.put(confirm_order_url)
    confirm_order_response = authenticated_client_for_secondary_user.put(confirm_order_url)

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    order = phase.phase_states.get(member=italy_member).orders.get(source__province_id="gol")

    phase = active_game.current_phase
    assert phase.status == PhaseStatus.ACTIVE
    assert phase.season == "Spring"
    assert phase.year == 1902
    assert phase.type == "Retreat"

    # Assert that order has resolved successfully
    order.refresh_from_db()
    assert order.resolution.status == OrderResolutionStatus.SUCCEEDED

    # Assert that Italy has a fleet in Spain SC
    assert phase.units.filter(nation__name="Italy", province__province_id="spa/sc", type=UnitType.FLEET).exists()


@pytest.mark.django_db
def test_dislodged_unit_scenario(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    """
    Integration test covering a dislodged unit scenario:
    - Create Italy vs Germany game
    - Spring 1901 Movement: Setup positions
    - Fall 1901 Movement: Germany attacks Italy's position with support, causing dislodgement
    - Fall 1901 Retreat: Italy retreats the dislodged unit
    - Verify final positions
    """
    active_game = create_active_game(
        authenticated_client, authenticated_client_for_secondary_user, italy_vs_germany_variant
    )

    italy_member = active_game.members.filter(nation__name="Italy").first()
    germany_member = active_game.members.filter(nation__name="Germany").first()

    create_order_url = reverse("order-create", args=[active_game.id])
    confirm_url = reverse("game-confirm-phase", args=[active_game.id])

    # Determine which client is which nation
    primary_is_germany = germany_member.user == active_game.members.first().user
    if primary_is_germany:
        germany_client = authenticated_client
        italy_client = authenticated_client_for_secondary_user
    else:
        germany_client = authenticated_client_for_secondary_user
        italy_client = authenticated_client

    # ===== SPRING 1901 MOVEMENT PHASE =====
    # Germany: Berlin to Munich, Munich to Bohemia
    # Italy: Venice to Tyrolia

    phase = active_game.current_phase
    assert phase.season == "Spring"
    assert phase.year == 1901
    assert phase.type == "Movement"

    # Germany: Berlin to Munich
    germany_client.post(create_order_url, {"selected": ["ber"]}, format="json")
    germany_client.post(create_order_url, {"selected": ["ber", "Move"]}, format="json")
    response = germany_client.post(create_order_url, {"selected": ["ber", "Move", "mun"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Germany: Munich to Bohemia
    germany_client.post(create_order_url, {"selected": ["mun"]}, format="json")
    germany_client.post(create_order_url, {"selected": ["mun", "Move"]}, format="json")
    response = germany_client.post(create_order_url, {"selected": ["mun", "Move", "boh"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Italy: Venice to Tyrolia
    italy_client.post(create_order_url, {"selected": ["ven"]}, format="json")
    italy_client.post(create_order_url, {"selected": ["ven", "Move"]}, format="json")
    response = italy_client.post(create_order_url, {"selected": ["ven", "Move", "tyr"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Both players confirm
    germany_client.put(confirm_url)
    italy_client.put(confirm_url)

    # Resolve phase
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.data["resolved"] >= 1

    # ===== SPRING 1901 RETREAT PHASE =====
    # No units dislodged, should auto-resolve

    phase = active_game.current_phase
    phase.refresh_from_db()
    assert phase.season == "Spring"
    assert phase.year == 1901
    assert phase.type == "Retreat"

    # Resolve retreat phase (no orders needed)
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.data["resolved"] >= 1

    # ===== FALL 1901 MOVEMENT PHASE =====
    # Germany: Munich to Tyrolia (attacking Italy)
    # Germany: Bohemia supports Munich to Tyrolia

    phase = active_game.current_phase
    phase.refresh_from_db()
    assert phase.season == "Fall"
    assert phase.year == 1901
    assert phase.type == "Movement"

    # Verify positions from Spring 1901
    assert phase.units.filter(nation__name="Germany", province__province_id="mun").exists()
    assert phase.units.filter(nation__name="Germany", province__province_id="boh").exists()
    assert phase.units.filter(nation__name="Italy", province__province_id="tyr").exists()

    # Germany: Munich to Tyrolia
    germany_client.post(create_order_url, {"selected": ["mun"]}, format="json")
    germany_client.post(create_order_url, {"selected": ["mun", "Move"]}, format="json")
    response = germany_client.post(create_order_url, {"selected": ["mun", "Move", "tyr"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Germany: Bohemia supports Munich to Tyrolia
    germany_client.post(create_order_url, {"selected": ["boh"]}, format="json")
    germany_client.post(create_order_url, {"selected": ["boh", "Support"]}, format="json")
    germany_client.post(create_order_url, {"selected": ["boh", "Support", "mun"]}, format="json")
    response = germany_client.post(create_order_url, {"selected": ["boh", "Support", "mun", "tyr"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Both players confirm
    germany_client.put(confirm_url)
    italy_client.put(confirm_url)

    # Resolve phase
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.data["resolved"] >= 1

    # ===== FALL 1901 RETREAT PHASE =====
    # Italy's army in Tyrolia should be dislodged
    # Italy retreats to Trieste

    phase = active_game.current_phase
    phase.refresh_from_db()
    assert phase.season == "Fall"
    assert phase.year == 1901
    assert phase.type == "Retreat"

    # Verify Germany's army is now in Tyrolia
    assert phase.units.filter(nation__name="Germany", province__province_id="tyr").exists()

    # Verify Italy's dislodged army is still in Tyrolia (but marked as dislodged)
    italy_dislodged_unit = phase.units.filter(nation__name="Italy", province__province_id="tyr").first()
    assert italy_dislodged_unit is not None
    assert italy_dislodged_unit.dislodged
    assert italy_dislodged_unit.dislodged_by is not None

    # Italy: Retreat from Tyrolia to Trieste
    italy_client.post(create_order_url, {"selected": ["tyr"]}, format="json")
    italy_client.post(create_order_url, {"selected": ["tyr", "Move"]}, format="json")
    response = italy_client.post(create_order_url, {"selected": ["tyr", "Move", "tri"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # Italy confirms
    italy_client.put(confirm_url)

    # Resolve retreat phase
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.data["resolved"] >= 1

    # ===== FALL 1901 ADJUSTMENT PHASE =====
    # Verify final positions

    phase = active_game.current_phase
    phase.refresh_from_db()

    # German army should be in Tyrolia
    assert phase.units.filter(nation__name="Germany", province__province_id="tyr", type=UnitType.ARMY).exists()

    # Italian army should be in Trieste
    assert phase.units.filter(nation__name="Italy", province__province_id="tri", type=UnitType.ARMY).exists()

    # Italian army should NOT be in Tyrolia anymore
    assert not phase.units.filter(nation__name="Italy", province__province_id="tyr").exists()


def create_active_hundred_game(
    authenticated_client,
    authenticated_client_for_secondary_user,
    authenticated_client_for_tertiary_user,
    hundred_variant,
):
    """Helper function to create and start a Hundred variant game with 3 players"""
    print(hundred_variant.template_phase.season)
    create_url = reverse("game-create")
    create_payload = {
        "name": "Hundred Variant Test",
        "variant_id": hundred_variant.id,
        "nation_assignment": NationAssignment.ORDERED,
        "private": False,
        "deadline_mode": DeadlineMode.DURATION,
    }
    create_response = authenticated_client.post(create_url, create_payload, format="json")
    game_id = create_response.data["id"]

    # Second and third users join
    join_url = reverse("game-join", args=[game_id])
    authenticated_client_for_secondary_user.post(join_url)
    authenticated_client_for_tertiary_user.post(join_url)

    return Game.objects.get(id=game_id)


@pytest.mark.django_db
def test_hundred_variant_movement_phase_resolution_with_errors(
    authenticated_client,
    authenticated_client_for_secondary_user,
    authenticated_client_for_tertiary_user,
    hundred_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    """
    Test the exact production scenario from dry_run_resolution:
    - Create Hundred variant game with 3 players
    - Place England's orders that cause resolution errors
    - Resolve to Retreat phase
    - Verify resolution errors appear correctly
    """
    active_game = create_active_hundred_game(
        authenticated_client,
        authenticated_client_for_secondary_user,
        authenticated_client_for_tertiary_user,
        hundred_variant,
    )

    # Verify game started
    assert active_game.status == GameStatus.ACTIVE
    assert active_game.members.count() == 3

    # Verify initial phase
    current_phase = active_game.current_phase
    assert current_phase.season == "Year"
    assert current_phase.year == 1425
    assert current_phase.type == "Movement"
    assert current_phase.status == PhaseStatus.ACTIVE

    # Verify initial units (should be 14 total from variant data)
    assert current_phase.units.count() == 14
    assert current_phase.units.filter(nation__name="England").count() == 5
    assert current_phase.units.filter(nation__name="France").count() == 5
    assert current_phase.units.filter(nation__name="Burgundy").count() == 4

    # Get members
    england_member = active_game.members.filter(nation__name="England").first()
    france_member = active_game.members.filter(nation__name="France").first()
    burgundy_member = active_game.members.filter(nation__name="Burgundy").first()

    # Determine which client is which nation
    primary_is_england = england_member.user == active_game.members.first().user
    if primary_is_england:
        england_client = authenticated_client
        # France and Burgundy can be either secondary or tertiary
        if france_member.user.username == "secondaryuser":
            france_client = authenticated_client_for_secondary_user
            burgundy_client = authenticated_client_for_tertiary_user
        else:
            france_client = authenticated_client_for_tertiary_user
            burgundy_client = authenticated_client_for_secondary_user
    else:
        # Need to figure out which client is England
        if england_member.user.username == "secondaryuser":
            england_client = authenticated_client_for_secondary_user
            france_client = (
                authenticated_client
                if france_member.user == active_game.members.first().user
                else authenticated_client_for_tertiary_user
            )
            burgundy_client = (
                authenticated_client_for_tertiary_user
                if france_client == authenticated_client
                else authenticated_client
            )
        else:
            england_client = authenticated_client_for_tertiary_user
            france_client = (
                authenticated_client
                if france_member.user == active_game.members.first().user
                else authenticated_client_for_secondary_user
            )
            burgundy_client = (
                authenticated_client_for_secondary_user
                if france_client == authenticated_client
                else authenticated_client
            )

    # Create orders URL
    create_order_url = reverse("order-create", args=[active_game.id])
    confirm_url = reverse("game-confirm-phase", args=[active_game.id])

    # England places orders (from scratch.txt):
    # nom: Move to orl
    england_client.post(create_order_url, {"selected": ["nom"]}, format="json")
    england_client.post(create_order_url, {"selected": ["nom", "Move"]}, format="json")
    response = england_client.post(create_order_url, {"selected": ["nom", "Move", "orl"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # dev: Move to brs
    england_client.post(create_order_url, {"selected": ["dev"]}, format="json")
    england_client.post(create_order_url, {"selected": ["dev", "Move"]}, format="json")
    response = england_client.post(create_order_url, {"selected": ["dev", "Move", "brs"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # lon: Move to str
    england_client.post(create_order_url, {"selected": ["lon"]}, format="json")
    england_client.post(create_order_url, {"selected": ["lon", "Move"]}, format="json")
    response = england_client.post(create_order_url, {"selected": ["lon", "Move", "str"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # cal: Move to dij
    england_client.post(create_order_url, {"selected": ["cal"]}, format="json")
    england_client.post(create_order_url, {"selected": ["cal", "Move"]}, format="json")
    response = england_client.post(create_order_url, {"selected": ["cal", "Move", "dij"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # guy: Move to ara
    england_client.post(create_order_url, {"selected": ["guy"]}, format="json")
    england_client.post(create_order_url, {"selected": ["guy", "Move"]}, format="json")
    response = england_client.post(create_order_url, {"selected": ["guy", "Move", "ara"]}, format="json")
    assert response.status_code == status.HTTP_201_CREATED

    # All players confirm (France and Burgundy have no orders, they just confirm)
    england_client.put(confirm_url)
    france_client.put(confirm_url)
    burgundy_client.put(confirm_url)

    # Resolve phase
    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    # Verify new phase is Retreat phase
    new_phase = active_game.current_phase
    new_phase.refresh_from_db()
    assert new_phase.season == "Year"
    assert new_phase.year == 1425
    assert new_phase.type == "Retreat"
    assert new_phase.status == PhaseStatus.ACTIVE

    # Verify old phase is completed
    current_phase.refresh_from_db()
    assert current_phase.status == PhaseStatus.COMPLETED

    # Verify resolution errors exist
    # Get the orders from the completed phase
    england_phase_state = current_phase.phase_states.get(member=england_member)
    orders = england_phase_state.orders.all()

    # Should have 5 orders
    assert orders.count() == 5

    # Check for resolution statuses matching the production output
    nom_order = orders.filter(source__province_id="nom").first()
    dev_order = orders.filter(source__province_id="dev").first()
    lon_order = orders.filter(source__province_id="lon").first()
    cal_order = orders.filter(source__province_id="cal").first()
    guy_order = orders.filter(source__province_id="guy").first()

    assert nom_order is not None
    assert dev_order is not None
    assert lon_order is not None
    assert cal_order is not None
    assert guy_order is not None

    # From the production output:
    # "nom": "ErrInvalidSource"
    # "dev": "ErrInvalidSource"
    # "lon": "ErrInvalidDestination"
    # "cal": "ErrInvalidSource"
    # "guy": "ErrInvalidSource"

    # Verify these orders have resolution objects with error statuses
    assert nom_order.resolution is not None
    assert dev_order.resolution is not None
    assert lon_order.resolution is not None
    assert cal_order.resolution is not None
    assert guy_order.resolution is not None

    # Check the resolution status values
    assert nom_order.resolution.status == "ErrBounce"
    assert dev_order.resolution.status == "OK"
    assert lon_order.resolution.status == "OK"
    assert cal_order.resolution.status == "ErrBounce"
    assert guy_order.resolution.status == "OK"


@pytest.mark.django_db
def test_hundred_variant_france_solo_victory_after_one_year(
    authenticated_client,
    authenticated_client_for_secondary_user,
    authenticated_client_for_tertiary_user,
    hundred_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    from victory.models import Victory
    from victory.constants import VictoryType

    active_game = create_active_hundred_game(
        authenticated_client,
        authenticated_client_for_secondary_user,
        authenticated_client_for_tertiary_user,
        hundred_variant,
    )

    assert active_game.status == GameStatus.ACTIVE
    assert active_game.members.count() == 3

    current_phase = active_game.current_phase
    assert current_phase.year == 1425
    assert current_phase.season == "Year"
    assert current_phase.type == "Movement"
    assert current_phase.status == PhaseStatus.ACTIVE

    assert current_phase.units.count() == 14

    france_member = active_game.members.filter(nation__name="France").first()
    england_member = active_game.members.filter(nation__name="England").first()
    burgundy_member = active_game.members.filter(nation__name="Burgundy").first()

    primary_is_france = france_member.user == active_game.members.first().user
    if primary_is_france:
        france_client = authenticated_client
        if england_member.user.username == "secondaryuser":
            england_client = authenticated_client_for_secondary_user
            burgundy_client = authenticated_client_for_tertiary_user
        else:
            england_client = authenticated_client_for_tertiary_user
            burgundy_client = authenticated_client_for_secondary_user
    else:
        if france_member.user.username == "secondaryuser":
            france_client = authenticated_client_for_secondary_user
            england_client = (
                authenticated_client
                if england_member.user == active_game.members.first().user
                else authenticated_client_for_tertiary_user
            )
            burgundy_client = (
                authenticated_client_for_tertiary_user
                if england_client == authenticated_client
                else authenticated_client
            )
        else:
            france_client = authenticated_client_for_tertiary_user
            england_client = (
                authenticated_client
                if england_member.user == active_game.members.first().user
                else authenticated_client_for_secondary_user
            )
            burgundy_client = (
                authenticated_client_for_secondary_user
                if england_client == authenticated_client
                else authenticated_client
            )

    create_order_url = reverse("order-create", args=[active_game.id])
    confirm_url = reverse("game-confirm-phase", args=[active_game.id])

    france_client.post(create_order_url, {"selected": ["orl", "Move", "brt"]}, format="json")

    france_client.post(create_order_url, {"selected": ["pro", "Move", "sav"]}, format="json")

    france_client.post(create_order_url, {"selected": ["tou", "Move", "ara"]}, format="json")

    france_client.post(create_order_url, {"selected": ["par", "Move", "nom"]}, format="json")

    france_client.post(create_order_url, {"selected": ["dau", "Move", "dij"]}, format="json")

    burgundy_client.post(create_order_url, {"selected": ["dij", "Move", "lor"]}, format="json")

    burgundy_client.post(create_order_url, {"selected": ["fla", "Move", "hol"]}, format="json")

    burgundy_client.post(create_order_url, {"selected": ["hol", "Move", "fri"]}, format="json")

    england_client.post(create_order_url, {"selected": ["nom", "Move", "anj"]}, format="json")

    england_client.post(create_order_url, {"selected": ["cal", "Move", "fla"]}, format="json")

    france_client.put(confirm_url)
    england_client.put(confirm_url)
    burgundy_client.put(confirm_url)

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    spring_retreat_phase = active_game.current_phase
    spring_retreat_phase.refresh_from_db()
    assert spring_retreat_phase.season == "Year"
    assert spring_retreat_phase.year == 1425
    assert spring_retreat_phase.type == "Retreat"

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    fall_movement_phase = active_game.current_phase
    fall_movement_phase.refresh_from_db()
    assert fall_movement_phase.season == "Year"
    assert fall_movement_phase.year == 1430
    assert fall_movement_phase.type == "Movement"

    france_client.post(create_order_url, {"selected": ["sav", "Move", "can"]}, format="json")

    france_client.post(create_order_url, {"selected": ["ara", "Move", "cas"]}, format="json")

    france_client.put(confirm_url)
    england_client.put(confirm_url)
    burgundy_client.put(confirm_url)

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    fall_retreat_phase = active_game.current_phase
    fall_retreat_phase.refresh_from_db()
    assert fall_retreat_phase.season == "Year"
    assert fall_retreat_phase.year == 1430
    assert fall_retreat_phase.type == "Retreat"

    resolve_response = authenticated_client.post(resolve_all_url)
    assert resolve_response.status_code == status.HTTP_200_OK
    assert resolve_response.data["resolved"] >= 1

    fall_adjustment_phase = active_game.current_phase
    fall_adjustment_phase.refresh_from_db()
    assert fall_adjustment_phase.season == "Year"
    assert fall_adjustment_phase.year == 1430
    assert fall_adjustment_phase.type == "Adjustment"

    assert Victory.objects.filter(game=active_game).exists()
    victory = Victory.objects.get(game=active_game)
    assert victory.type == VictoryType.SOLO
    assert victory.members.count() == 1
    assert victory.members.first() == france_member
    assert victory.winning_phase == fall_adjustment_phase

    active_game.refresh_from_db()
    assert active_game.status == GameStatus.COMPLETED

    fall_adjustment_phase.refresh_from_db()
    assert fall_adjustment_phase.status == PhaseStatus.COMPLETED
    assert fall_adjustment_phase.scheduled_resolution is None
