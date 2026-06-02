from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from common.constants import DeadlineMode, GameStatus, UnitType
from phase.models import Phase


class TestDeadlineReminderGuard:

    @pytest.mark.django_db
    def test_sends_one_reminder_per_deadline(
        self, phase_factory, classical_england_nation, classical_edinburgh_province
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_edinburgh_province)

        with patch("phase.models.notification_utils.send_notification_to_users") as mock_send:
            first = Phase.objects.send_deadline_warnings()
            second = Phase.objects.send_deadline_warnings()

        assert first["notifications_sent"] == 1
        assert second["notifications_sent"] == 0
        mock_send.assert_called_once()

        phase_state = phase.phase_states.first()
        phase_state.refresh_from_db()
        assert phase_state.deadline_warning_sent_for == phase.scheduled_resolution

    @pytest.mark.django_db
    def test_fresh_reminder_after_deadline_moves(
        self, phase_factory, classical_england_nation, classical_edinburgh_province
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_edinburgh_province)

        with patch("phase.models.notification_utils.send_notification_to_users") as mock_send:
            Phase.objects.send_deadline_warnings()

            phase.scheduled_resolution = phase.scheduled_resolution + timedelta(minutes=10)
            phase.save()

            third = Phase.objects.send_deadline_warnings()

        assert third["notifications_sent"] == 1
        assert mock_send.call_count == 2

    @pytest.mark.django_db
    def test_confirmed_player_not_reminded(
        self,
        phase_factory,
        classical_england_nation,
        classical_france_nation,
        classical_edinburgh_province,
        classical_paris_province,
        secondary_user,
    ):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": True},
                {
                    "nation": classical_france_nation,
                    "has_possible_orders": True,
                    "orders_confirmed": False,
                    "user": secondary_user,
                },
            ],
        )
        phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_edinburgh_province)
        phase.units.create(type=UnitType.ARMY, nation=classical_france_nation, province=classical_paris_province)

        with patch("phase.models.notification_utils.send_notification_to_users") as mock_send:
            result = Phase.objects.send_deadline_warnings()

        assert result["notifications_sent"] == 1
        mock_send.assert_called_once()
        assert mock_send.call_args.kwargs["user_ids"] == [secondary_user.id]

    @pytest.mark.django_db
    def test_eliminated_player_not_reminded(self, phase_factory, classical_england_nation):
        phase_factory(
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": False, "orders_confirmed": False},
            ],
        )

        with patch("phase.models.notification_utils.send_notification_to_users") as mock_send:
            result = Phase.objects.send_deadline_warnings()

        assert result["notifications_sent"] == 0
        mock_send.assert_not_called()

    @pytest.mark.django_db
    def test_fixed_time_game_reminds_players_with_orders(
        self, phase_factory, classical_variant, classical_england_nation, classical_edinburgh_province
    ):
        from game.models import Game

        game = Game.objects.create(
            variant=classical_variant,
            name="Fixed Time Game",
            status=GameStatus.ACTIVE,
            deadline_mode=DeadlineMode.FIXED_TIME,
        )
        phase = phase_factory(
            game=game,
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_edinburgh_province)

        with patch("phase.models.notification_utils.send_notification_to_users") as mock_send:
            result = Phase.objects.send_deadline_warnings()

        assert result["notifications_sent"] == 1
        mock_send.assert_called_once()
