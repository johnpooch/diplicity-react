import pytest
from unittest.mock import patch
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta
from rest_framework import status

from channel.models import Channel, ChannelMessage, ChannelMember
from common.constants import (
    DeadlineMode,
    GameStatus,
    MovementPhaseDuration,
    NationAssignment,
    PressType,
)
from game.models import Game
from adjudication import service as adjudication_service


class TestIntroMessageOnJoin:

    @pytest.mark.django_db
    def test_full_press_join_without_message_succeeds(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        url = reverse("game-join", args=[pending_game_created_by_secondary_user.id])
        response = authenticated_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_full_press_join_with_message_succeeds(
        self, authenticated_client, pending_game_created_by_secondary_user, primary_user
    ):
        url = reverse("game-join", args=[pending_game_created_by_secondary_user.id])
        response = authenticated_client.post(
            url, {"message": "Hi everyone, excited to play!"}, format="json"
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["name"] == primary_user.profile.name

    @pytest.mark.django_db
    def test_full_press_join_message_posted_to_public_press(
        self, authenticated_client, pending_full_press_game_with_channel
    ):
        game = pending_full_press_game_with_channel
        url = reverse("game-join", args=[game.id])
        authenticated_client.post(
            url, {"message": "Hello, I'm new here!"}, format="json"
        )

        public_press = Channel.objects.get(game=game, name="Public Press")
        messages = ChannelMessage.objects.filter(channel=public_press)
        assert messages.count() == 1
        assert messages.first().body == "Hello, I'm new here!"

    @pytest.mark.django_db
    def test_full_press_join_blank_message_rejected(
        self, authenticated_client, pending_game_created_by_secondary_user
    ):
        url = reverse("game-join", args=[pending_game_created_by_secondary_user.id])
        response = authenticated_client.post(
            url, {"message": "   "}, format="json"
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_no_press_join_does_not_require_message(
        self, authenticated_client, no_press_pending_game
    ):
        url = reverse("game-join", args=[no_press_pending_game.id])
        response = authenticated_client.post(url, {}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_join_adds_member_to_public_press_channel(
        self, authenticated_client, pending_full_press_game_with_channel, primary_user
    ):
        game = pending_full_press_game_with_channel
        url = reverse("game-join", args=[game.id])
        authenticated_client.post(
            url, {"message": "Hi!"}, format="json"
        )

        public_press = Channel.objects.get(game=game, name="Public Press")
        new_member = game.members.get(user=primary_user)
        assert ChannelMember.objects.filter(member=new_member, channel=public_press).exists()


class TestChannelAccessInPendingGames:

    @pytest.mark.django_db
    def test_list_channels_in_pending_game(
        self, authenticated_client, pending_game_with_public_press, primary_user
    ):
        game = pending_game_with_public_press
        url = reverse("channel-list", args=[game.id])
        response = authenticated_client.get(url)
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 1
        assert response.data[0]["name"] == "Public Press"

    @pytest.mark.django_db
    def test_send_message_in_pending_game_public_channel(
        self, authenticated_client, pending_game_with_public_press, in_memory_procrastinate
    ):
        game = pending_game_with_public_press
        channel = Channel.objects.get(game=game, name="Public Press")
        url = reverse("channel-message-create", args=[game.id, channel.id])
        response = authenticated_client.post(url, {"body": "Hey!"}, format="json")
        assert response.status_code == status.HTTP_201_CREATED

    @pytest.mark.django_db
    def test_send_message_in_pending_game_private_channel_blocked(
        self, authenticated_client, pending_game_with_private_channel
    ):
        game = pending_game_with_private_channel
        channel = Channel.objects.get(game=game, private=True)
        url = reverse("channel-message-create", args=[game.id, channel.id])
        response = authenticated_client.post(url, {"body": "Hey!"}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_create_channel_in_pending_game_blocked(
        self, authenticated_client, pending_game_with_public_press
    ):
        game = pending_game_with_public_press
        url = reverse("channel-create", args=[game.id])
        response = authenticated_client.post(url, {"member_ids": []}, format="json")
        assert response.status_code == status.HTTP_403_FORBIDDEN


class TestConfirmation:

    @pytest.mark.django_db
    def test_confirm_sets_member_confirmed(
        self, authenticated_client, pending_game_with_all_members, primary_user
    ):
        game = pending_game_with_all_members
        url = reverse("game-confirm", args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_204_NO_CONTENT

        member = game.members.get(user=primary_user)
        assert member.confirmed is True

    @pytest.mark.django_db
    def test_confirm_already_confirmed_returns_error(
        self, authenticated_client, pending_game_with_all_members, primary_user
    ):
        game = pending_game_with_all_members
        game.members.filter(user=primary_user).update(confirmed=True)

        url = reverse("game-confirm", args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_confirm_when_not_required_returns_error(
        self, authenticated_client, pending_game_no_confirmation, primary_user
    ):
        game = pending_game_no_confirmation
        url = reverse("game-confirm", args=[game.id])
        response = authenticated_client.post(url)
        assert response.status_code == status.HTTP_400_BAD_REQUEST

    @pytest.mark.django_db
    def test_all_confirmed_starts_game(
        self,
        authenticated_client,
        authenticated_client_for_secondary_user,
        pending_game_with_all_members_ivg,
        adjudication_data_italy_vs_germany,
    ):
        game = pending_game_with_all_members_ivg

        with patch.object(adjudication_service, "start", return_value=adjudication_data_italy_vs_germany):
            authenticated_client.post(reverse("game-confirm", args=[game.id]))
            authenticated_client_for_secondary_user.post(reverse("game-confirm", args=[game.id]))

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE

    @pytest.mark.django_db
    def test_partial_confirmation_does_not_start_game(
        self, authenticated_client, pending_game_with_all_members_ivg
    ):
        game = pending_game_with_all_members_ivg
        authenticated_client.post(reverse("game-confirm", args=[game.id]))

        game.refresh_from_db()
        assert game.status == GameStatus.PENDING

    @pytest.mark.django_db
    def test_confirm_non_member_rejected(
        self, authenticated_client_for_tertiary_user, pending_game_with_all_members
    ):
        game = pending_game_with_all_members
        url = reverse("game-confirm", args=[game.id])
        response = authenticated_client_for_tertiary_user.post(url)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @pytest.mark.django_db
    def test_join_full_game_with_confirmation_sets_deadline(
        self, authenticated_client, pending_game_almost_full_ivg
    ):
        game = pending_game_almost_full_ivg
        url = reverse("game-join", args=[game.id])
        authenticated_client.post(url, {"message": "Hi!"}, format="json")

        game.refresh_from_db()
        assert game.confirmation_deadline is not None
        assert game.status == GameStatus.PENDING

    @pytest.mark.django_db
    def test_join_full_game_without_confirmation_starts_game(
        self,
        authenticated_client,
        pending_game_almost_full_ivg_no_confirmation,
        adjudication_data_italy_vs_germany,
    ):
        game = pending_game_almost_full_ivg_no_confirmation

        with patch.object(adjudication_service, "start", return_value=adjudication_data_italy_vs_germany):
            url = reverse("game-join", args=[game.id])
            authenticated_client.post(url, {"message": "Hi!"}, format="json")

        game.refresh_from_db()
        assert game.status == GameStatus.ACTIVE


class TestConfirmationSweep:

    @pytest.mark.django_db
    def test_sweep_removes_unconfirmed_members(
        self,
        pending_game_with_expired_confirmation,
    ):
        from game.tasks import sweep_confirmation_deadlines

        game = pending_game_with_expired_confirmation
        initial_count = game.members.count()

        sweep_confirmation_deadlines(0)

        game.refresh_from_db()
        assert game.members.count() < initial_count
        assert not game.members.filter(confirmed=False).exists()

    @pytest.mark.django_db
    def test_sweep_does_not_remove_confirmed_members(
        self,
        pending_game_with_expired_confirmation,
        primary_user,
    ):
        from game.tasks import sweep_confirmation_deadlines

        game = pending_game_with_expired_confirmation
        game.members.filter(user=primary_user).update(confirmed=True)

        sweep_confirmation_deadlines(0)

        assert game.members.filter(user=primary_user).exists()

    @pytest.mark.django_db
    def test_sweep_clears_confirmation_deadline(
        self,
        pending_game_with_expired_confirmation,
    ):
        from game.tasks import sweep_confirmation_deadlines

        game = pending_game_with_expired_confirmation
        sweep_confirmation_deadlines(0)

        game.refresh_from_db()
        assert game.confirmation_deadline is None

    @pytest.mark.django_db
    def test_sweep_ignores_games_with_future_deadline(
        self,
        pending_game_with_all_members,
    ):
        from game.tasks import sweep_confirmation_deadlines

        game = pending_game_with_all_members
        game.confirmation_deadline = timezone.now() + timedelta(hours=24)
        game.save()

        initial_count = game.members.count()
        sweep_confirmation_deadlines(0)

        assert game.members.count() == initial_count


class TestGameCreateConfirmationRequired:

    @pytest.mark.django_db
    def test_create_game_default_confirmation_not_required(
        self, authenticated_client, classical_variant
    ):
        url = reverse("game-create")
        payload = {
            "name": "Test Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.DURATION,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["confirmation_required"] is False

    @pytest.mark.django_db
    def test_create_game_opt_in_confirmation(
        self, authenticated_client, classical_variant
    ):
        url = reverse("game-create")
        payload = {
            "name": "Confirm Game",
            "variant_id": classical_variant.id,
            "nation_assignment": NationAssignment.RANDOM,
            "private": False,
            "deadline_mode": DeadlineMode.DURATION,
            "confirmation_required": True,
        }
        response = authenticated_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["confirmation_required"] is True


# --- Fixtures ---

@pytest.fixture
def pending_full_press_game_with_channel(db, secondary_user, classical_variant):
    game = Game.objects.create_from_template(
        classical_variant,
        name="Full Press Pending with Channel",
        press_type=PressType.FULL_PRESS,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
    )
    creator = game.members.create(user=secondary_user)
    channel = game.channels.create(name="Public Press", private=False)
    channel.member_channels.create(member=creator)
    return game


@pytest.fixture
def no_press_pending_game(db, secondary_user, classical_variant):
    game = Game.objects.create_from_template(
        classical_variant,
        name="No Press Pending Game",
        press_type=PressType.NO_PRESS,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
    )
    game.members.create(user=secondary_user)
    game.channels.create(name="Public Press", private=False)
    return game


@pytest.fixture
def pending_game_with_public_press(db, primary_user, classical_variant):
    game = Game.objects.create_from_template(
        classical_variant,
        name="Pending with Press",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
    )
    member = game.members.create(user=primary_user)
    channel = game.channels.create(name="Public Press", private=False)
    channel.member_channels.create(member=member)
    return game


@pytest.fixture
def pending_game_with_private_channel(db, primary_user, classical_variant):
    game = Game.objects.create_from_template(
        classical_variant,
        name="Pending with Private",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
    )
    member = game.members.create(user=primary_user)
    channel = game.channels.create(name="Private Channel", private=True)
    channel.member_channels.create(member=member)
    return game


@pytest.fixture
def pending_game_with_all_members(
    db, primary_user, secondary_user, classical_variant
):
    game = Game.objects.create_from_template(
        classical_variant,
        name="Full Pending Game",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        confirmation_required=True,
    )
    game.members.create(user=primary_user)
    game.members.create(user=secondary_user)
    game.channels.create(name="Public Press", private=False)
    return game


@pytest.fixture
def pending_game_with_all_members_ivg(
    db, primary_user, secondary_user, italy_vs_germany_variant
):
    game = Game.objects.create_from_template(
        italy_vs_germany_variant,
        name="Full IVG Pending Game",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        confirmation_required=True,
    )
    game.members.create(user=primary_user)
    game.members.create(user=secondary_user)
    game.channels.create(name="Public Press", private=False)
    return game


@pytest.fixture
def pending_game_no_confirmation(
    db, primary_user, secondary_user, classical_variant
):
    game = Game.objects.create_from_template(
        classical_variant,
        name="No Confirm Game",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        confirmation_required=False,
    )
    game.members.create(user=primary_user)
    game.members.create(user=secondary_user)
    return game


@pytest.fixture
def pending_game_almost_full_ivg(db, secondary_user, italy_vs_germany_variant):
    game = Game.objects.create_from_template(
        italy_vs_germany_variant,
        name="Almost Full IVG",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        confirmation_required=True,
    )
    game.members.create(user=secondary_user)
    game.channels.create(name="Public Press", private=False)
    return game


@pytest.fixture
def pending_game_almost_full_ivg_no_confirmation(db, secondary_user, italy_vs_germany_variant):
    game = Game.objects.create_from_template(
        italy_vs_germany_variant,
        name="Almost Full IVG No Confirm",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        confirmation_required=False,
    )
    game.members.create(user=secondary_user)
    game.channels.create(name="Public Press", private=False)
    return game


@pytest.fixture
def pending_game_with_expired_confirmation(
    db, primary_user, secondary_user, italy_vs_germany_variant
):
    game = Game.objects.create_from_template(
        italy_vs_germany_variant,
        name="Expired Confirmation",
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        deadline_mode=DeadlineMode.DURATION,
        confirmation_required=True,
    )
    game.members.create(user=primary_user)
    game.members.create(user=secondary_user)
    game.confirmation_deadline = timezone.now() - timedelta(hours=1)
    game.save()
    return game
