from re import I
import pytest
from django.urls import reverse
from rest_framework import status
from game.models import Game
from member.models import Member
from common.constants import GameStatus, NationAssignment, OrderCreationStep, PhaseStatus


def create_active_game(authenticated_client, authenticated_client_for_secondary_user, italy_vs_germany_variant):
    create_url = reverse("game-create")
    create_payload = {
        "name": "Italy vs Germany Test",
        "variant_id": italy_vs_germany_variant.id,
        "nation_assignment": NationAssignment.ORDERED,
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

    # Notification is sent to both users
    mock_send_notification_to_users.assert_called_once_with(
        user_ids=[germany_member.user.id, italy_member.user.id],
        title="Game Started",
        body=f"Game '{game.name}' has started!",
        notification_type="game_start",
        data={"game_id": str(game.id)},
    )


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

    # Second phase has been created
    second_phase = active_game.current_phase
    assert second_phase.status == PhaseStatus.ACTIVE
    assert second_phase.season == "Spring"
    assert second_phase.year == 1901
    assert second_phase.type == "Retreat"

    # First phase has resolved
    first_phase.refresh_from_db()
    assert first_phase.status == PhaseStatus.COMPLETED

    italy_member = active_game.members.filter(nation__name="Italy").first()
    germany_member = active_game.members.filter(nation__name="Germany").first()

    # Notification is sent to both users
    mock_send_notification_to_users.assert_called_with(
        user_ids=[germany_member.user.id, italy_member.user.id],
        title="Phase Resolved",
        body=f"Phase '{first_phase.name}' has been resolved!",
        notification_type="phase_resolved",
        data={"game_id": str(active_game.id)},
    )
