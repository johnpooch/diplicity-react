import pytest
from datetime import timedelta

from django.utils import timezone

from common.constants import DeadlineMode, MovementPhaseDuration, PressType
from game.models import Game


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
def pending_game_with_all_members(db, primary_user, secondary_user, classical_variant):
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
def pending_game_with_all_members_ivg(db, primary_user, secondary_user, italy_vs_germany_variant):
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
def pending_game_no_confirmation(db, primary_user, secondary_user, classical_variant):
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
def pending_game_with_expired_confirmation(db, primary_user, secondary_user, italy_vs_germany_variant):
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
