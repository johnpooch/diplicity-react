from datetime import time

import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from user_profile.models import UserProfile
from game import models
from common.constants import DeadlineMode, GameStatus, PhaseFrequency, PhaseStatus, MovementPhaseDuration
from adjudication import service as adjudication_service
from unittest.mock import patch

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def pending_game_with_gm(db, primary_user, classical_variant, base_pending_phase):
    def _create(gm_user=None):
        if gm_user is None:
            gm_user = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Game with GM",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
        )
        game.members.create(user=gm_user, is_game_master=True)
        return game
    return _create


@pytest.fixture
def active_game_with_gm(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(gm_user=None, nmr_extensions_allowed=0):
        if gm_user is None:
            gm_user = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Active Game with GM",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            nmr_extensions_allowed=nmr_extensions_allowed,
        )
        game.members.create(user=gm_user, is_game_master=True)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game
    return _create


@pytest.fixture
def active_game_with_fixed_time(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(gm_user=None, target_time=None, timezone_name=None, movement_frequency=None, retreat_frequency=None):
        if gm_user is None:
            gm_user = primary_user
        if target_time is None:
            target_time = time(21, 0)
        if timezone_name is None:
            timezone_name = "America/New_York"
        if movement_frequency is None:
            movement_frequency = PhaseFrequency.DAILY
        if retreat_frequency is None:
            retreat_frequency = PhaseFrequency.DAILY

        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Fixed Time Game",
            deadline_mode=DeadlineMode.FIXED_TIME,
            fixed_deadline_time=target_time,
            fixed_deadline_timezone=timezone_name,
            movement_frequency=movement_frequency,
            retreat_frequency=retreat_frequency,
        )
        game.members.create(user=gm_user, is_game_master=True)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"fixed_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"Fixed Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game
    return _create
