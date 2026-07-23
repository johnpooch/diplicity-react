from datetime import timedelta
from unittest.mock import patch

import pytest
from django.utils import timezone

from common.constants import DeadlineMode, GameStatus, PhaseStatus, UnitType
from game.models import Game
from phase.models import Phase


class TestDeadlineWarningRecipients:

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

        with patch("phase.models.emit") as mock_emit:
            result = Phase.objects.send_deadline_warning(phase.id)

        assert result["notifications_sent"] == 1
        mock_emit.assert_called_once()
        assert mock_emit.call_args.kwargs["recipients"] == [secondary_user.id]

    @pytest.mark.django_db
    def test_eliminated_player_not_reminded(self, phase_factory, classical_england_nation):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": False, "orders_confirmed": False},
            ],
        )

        with patch("phase.models.emit") as mock_emit:
            result = Phase.objects.send_deadline_warning(phase.id)

        assert result["notifications_sent"] == 0
        mock_emit.assert_not_called()

    @pytest.mark.django_db
    def test_fixed_time_game_reminds_players_with_orders(
        self, phase_factory, classical_variant, classical_england_nation, classical_edinburgh_province
    ):
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

        with patch("phase.models.emit") as mock_emit:
            result = Phase.objects.send_deadline_warning(phase.id)

        assert result["notifications_sent"] == 1
        mock_emit.assert_called_once()

    @pytest.mark.django_db
    def test_completed_phase_is_skipped(self, phase_factory, classical_england_nation, classical_edinburgh_province):
        phase = phase_factory(
            scheduled_resolution=timezone.now() + timedelta(minutes=30),
            status=PhaseStatus.COMPLETED,
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_edinburgh_province)

        with patch("phase.models.emit") as mock_emit:
            result = Phase.objects.send_deadline_warning(phase.id)

        assert result["notifications_sent"] == 0
        mock_emit.assert_not_called()

    @pytest.mark.django_db
    def test_passed_deadline_is_skipped(self, phase_factory, classical_england_nation, classical_edinburgh_province):
        phase = phase_factory(
            scheduled_resolution=timezone.now() - timedelta(minutes=1),
            phase_states_config=[
                {"nation": classical_england_nation, "has_possible_orders": True, "orders_confirmed": False},
            ],
        )
        phase.units.create(type=UnitType.ARMY, nation=classical_england_nation, province=classical_edinburgh_province)

        with patch("phase.models.emit") as mock_emit:
            result = Phase.objects.send_deadline_warning(phase.id)

        assert result["notifications_sent"] == 0
        mock_emit.assert_not_called()

    @pytest.mark.django_db
    def test_missing_phase_is_skipped(self):
        with patch("phase.models.emit") as mock_emit:
            result = Phase.objects.send_deadline_warning(999999)

        assert result["notifications_sent"] == 0
        mock_emit.assert_not_called()
