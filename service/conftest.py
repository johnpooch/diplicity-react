import json
from datetime import time
from pathlib import Path
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.test import override_settings
from django.utils import timezone
from rest_framework.test import APIClient

from adjudication import service as adjudication_service
from channel.models import Channel, ChannelMember, ChannelMessage
from common.constants import (
    DeadlineMode,
    GameStatus,
    MovementPhaseDuration,
    OrderType,
    PhaseFrequency,
    PhaseStatus,
    PhaseType,
    UnitType,
)
from draw_proposal.models import DrawProposal, DrawVote
from game import models
from game.models import Game
from member.models import Member
from nation.models import Nation
from order.models import OrderResolution
from phase.models import Phase
from province.models import Province
from user_profile.models import UserProfile
from variant.models import Variant
from victory.models import Victory

User = get_user_model()


# ---------------------------------------------------------------------------
# Global test settings
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session", autouse=True)
def override_test_settings():
    with override_settings(
        CACHES={
            "default": {
                "BACKEND": "django.core.cache.backends.dummy.DummyCache",
            }
        },
        STORAGES={
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        },
        PASSWORD_HASHERS=[
            "django.contrib.auth.hashers.MD5PasswordHasher",
            "django.contrib.auth.hashers.PBKDF2PasswordHasher",
        ],
    ):
        yield


# ---------------------------------------------------------------------------
# Users and API clients
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def primary_user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        primary_user = User.objects.create_user(
            username="primaryuser", email="primary@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=primary_user, name="Primary User", picture="")
        return primary_user


@pytest.fixture(scope="session")
def secondary_user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        secondary_user = User.objects.create_user(
            username="secondaryuser", email="secondary@example.com", password="testpass123"
        )
        UserProfile.objects.create(user=secondary_user, name="Secondary User", picture="")
        return secondary_user


@pytest.fixture(scope="session")
def tertiary_user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        tertiary_user = User.objects.create_user(
            username="tertiaryuser",
            email="tertiary@example.com",
            password="testpass123",
        )
        UserProfile.objects.create(user=tertiary_user, name="Tertiary User", picture="")
        return tertiary_user


@pytest.fixture
def user_factory(db):
    def _create(username=None, email=None, name=None):
        count = User.objects.count()
        if username is None:
            username = f"testuser{count}"
        if email is None:
            email = f"{username}@example.com"
        if name is None:
            name = f"Test User {count}"
        user = User.objects.create_user(username=username, email=email, password="testpass123")
        UserProfile.objects.create(user=user, name=name)
        return user

    return _create


@pytest.fixture(scope="session")
def authenticated_client(primary_user):
    client = APIClient()
    client.force_authenticate(user=primary_user)
    return client


@pytest.fixture(scope="session")
def authenticated_client_for_secondary_user(secondary_user):
    client = APIClient()
    client.force_authenticate(user=secondary_user)
    return client


@pytest.fixture(scope="session")
def authenticated_client_for_tertiary_user(tertiary_user):
    client = APIClient()
    client.force_authenticate(user=tertiary_user)
    return client


@pytest.fixture(scope="session")
def unauthenticated_client():
    return APIClient()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_client_factory():
    def _create(user):
        client = APIClient()
        client.force_authenticate(user=user)
        return client

    return _create


# ---------------------------------------------------------------------------
# Variant reference data (session-scoped lookups)
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def classical_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="classical")


@pytest.fixture(scope="session")
def classical_england_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="England", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_france_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="France", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_germany_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Germany", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_italy_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Italy", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_austria_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Austria", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_turkey_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Turkey", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_russia_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Russia", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_edinburgh_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="edi", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_irish_sea_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="iri", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_liverpool_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="lvp", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_london_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="lon", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_wales_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="wal", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_english_channel_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="eng", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_paris_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="par", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_burgundy_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="bur", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_budapest_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="bud", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_galicia_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="gal", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_rumania_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="rum", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_serbia_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ser", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_trieste_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="tri", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_vienna_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="vie", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_sevastopol_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="sev", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_spain_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="spa", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_spain_nc_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="spa/nc", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_spain_sc_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="spa/sc", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_stp_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="stp", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_stp_nc_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="stp/nc", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_stp_sc_province(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="stp/sc", variant=classical_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="italy-vs-germany")


@pytest.fixture(scope="session")
def italy_vs_germany_italy_nation(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Italy", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_germany_nation(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Germany", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_venice_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ven", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_rome_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="rom", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_greece_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="gre", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_warsaw_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="war", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_naples_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="nap", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_trieste_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="tri", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_kiel_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="kie", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_berlin_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ber", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_munich_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="mun", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_ionian_sea_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ion", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_denmark_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="den", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_prussia_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="pru", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def italy_vs_germany_ruhr_province(django_db_setup, django_db_blocker, italy_vs_germany_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ruh", variant=italy_vs_germany_variant)


@pytest.fixture(scope="session")
def hundred_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="hundred")


@pytest.fixture(scope="session")
def hundred_england_nation(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="England", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_france_nation(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="France", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_burgundy_nation(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="Burgundy", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_calais_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="cal", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_devon_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="dev", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_london_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="lon", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_normandy_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="nom", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_guyenne_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="guy", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_dijon_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="dij", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_bristol_channel_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="brs", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_strait_of_dover_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="str", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_orleanais_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="orl", variant=hundred_variant)


@pytest.fixture(scope="session")
def hundred_aragon_province(django_db_setup, django_db_blocker, hundred_variant):
    with django_db_blocker.unblock():
        return Province.objects.get(province_id="ara", variant=hundred_variant)


# ---------------------------------------------------------------------------
# Generic model factories
# ---------------------------------------------------------------------------


@pytest.fixture
def game_factory(db):
    def _create(variant=None, status=None, sandbox=False, **kwargs):
        if variant is None:
            variant = Variant.objects.first()

        if status is None:
            status = GameStatus.ACTIVE

        variant_solo_victory_sc_count = kwargs.pop("variant__solo_victory_sc_count", None)
        if variant_solo_victory_sc_count is not None:
            variant.victory_conditions = [
                {
                    "type": "supply-center-majority",
                    "supplyCenters": variant_solo_victory_sc_count,
                }
            ]
            variant.save()

        return Game.objects.create(
            variant=variant,
            status=status,
            sandbox=sandbox,
            name=f"Test Game {Game.objects.count()}",
            **kwargs,
        )

    return _create


@pytest.fixture
def phase_factory(db, classical_variant, primary_user):
    def _create(
        game=None,
        type=None,
        season=None,
        year=None,
        status=None,
        scheduled_resolution=None,
        phase_states_config=None,
        options=None,
        **kwargs,
    ):
        if game is None:
            game = Game.objects.create(
                variant=classical_variant,
                name=f"Test Game {Phase.objects.count()}",
                status=GameStatus.ACTIVE,
                deadline_mode=DeadlineMode.DURATION,
                movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            )

        if type is None:
            type = PhaseType.MOVEMENT

        if season is None:
            season = "Spring"

        if year is None:
            year = 1901

        if status is None:
            status = PhaseStatus.ACTIVE

        phase = Phase.objects.create(
            game=game,
            variant=game.variant,
            season=season,
            year=year,
            type=type,
            status=status,
            scheduled_resolution=scheduled_resolution,
            options=options or {},
            ordinal=kwargs.pop("ordinal", 1),
            **kwargs,
        )

        if phase_states_config:
            for config in phase_states_config:
                nation = config.get("nation")
                if not nation:
                    continue

                member = game.members.filter(nation=nation).first()
                if not member:
                    member = Member.objects.create(
                        nation=nation,
                        user=config.get("user", primary_user),
                        game=game,
                    )

                phase.phase_states.create(
                    member=member,
                    has_possible_orders=config.get("has_possible_orders", False),
                    orders_confirmed=config.get("orders_confirmed", False),
                )

        return phase

    return _create


@pytest.fixture
def member_factory(db):
    def _create(game=None, user=None, nation=None, eliminated=False, kicked=False, **kwargs):
        if game is None:
            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Member.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if user is None:
            user = User.objects.create_user(
                username=f"testuser{Member.objects.count()}",
                email=f"test{Member.objects.count()}@example.com",
                password="testpass123",
            )
            UserProfile.objects.get_or_create(user=user, defaults={"name": f"Test User {user.id}"})

        if nation is None:
            available_nations = game.variant.nations.exclude(id__in=game.members.values_list("nation_id", flat=True))
            nation = available_nations.first()

        return Member.objects.create(
            game=game,
            user=user,
            nation=nation,
            eliminated=eliminated,
            kicked=kicked,
            **kwargs,
        )

    return _create


@pytest.fixture
def supply_center_factory(db):
    def _create(phase=None, nation=None, province=None):
        if phase is None:
            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Phase.objects.count()}",
                status=GameStatus.ACTIVE,
            )
            phase = Phase.objects.create(
                game=game,
                variant=variant,
                season="Fall",
                year=1901,
                type=PhaseType.ADJUSTMENT,
                ordinal=1,
            )

        if nation is None:
            nation = phase.variant.nations.first()

        if province is None:
            province = phase.variant.provinces.filter(supply_center=True).first()

        return phase.supply_centers.create(nation=nation, province=province)

    return _create


@pytest.fixture
def victory_factory(db):
    def _create(game=None, winning_phase=None):
        if game is None:
            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {Victory.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if winning_phase is None:
            winning_phase = Phase.objects.create(
                game=game,
                variant=game.variant,
                season="Fall",
                year=1901,
                type=PhaseType.ADJUSTMENT,
                ordinal=1,
            )

        return Victory.objects.create(game=game, winning_phase=winning_phase)

    return _create


@pytest.fixture
def draw_proposal_factory(db, member_factory):
    def _create(game=None, created_by=None, phase=None, included_member_ids=None, cancelled=False):
        if game is None:
            variant = Variant.objects.first()
            game = Game.objects.create(
                variant=variant,
                name=f"Test Game {DrawProposal.objects.count()}",
                status=GameStatus.ACTIVE,
            )

        if phase is None:
            phase = Phase.objects.create(
                game=game,
                variant=game.variant,
                season="Spring",
                year=1901,
                type=PhaseType.MOVEMENT,
                status=PhaseStatus.ACTIVE,
                ordinal=1,
            )

        if created_by is None:
            created_by = member_factory(game=game)

        proposal = DrawProposal.objects.create(
            game=game,
            created_by=created_by,
            phase=phase,
            cancelled=cancelled,
        )

        all_active_members = list(game.members.filter(eliminated=False, kicked=False))

        if included_member_ids is None:
            included_member_ids = [created_by.id]

        for member in all_active_members:
            is_included = member.id in included_member_ids
            is_proposer = member.id == created_by.id
            DrawVote.objects.create(
                proposal=proposal,
                member=member,
                included=is_included,
                accepted=True if is_proposer else None,
            )

        return proposal

    return _create


# ---------------------------------------------------------------------------
# Game scenario factories (callables returning configured games)
# ---------------------------------------------------------------------------


@pytest.fixture
def pending_game_factory(db, primary_user, classical_variant):
    def _create(creator=None):
        if creator is None:
            creator = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Game with Creator",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            created_by=creator,
            admin=creator,
        )
        game.members.create(user=creator)
        return game

    return _create


@pytest.fixture
def active_game_factory(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(creator=None, nmr_extensions_allowed=0):
        if creator is None:
            creator = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Active Game with Creator",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            nmr_extensions_allowed=nmr_extensions_allowed,
            deadline_mode=DeadlineMode.DURATION,
            created_by=creator,
            admin=creator,
        )
        game.members.create(user=creator)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game

    return _create


@pytest.fixture
def fixed_deadline_game_factory(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(creator=None, target_time=None, timezone_name=None, movement_frequency=None, retreat_frequency=None):
        if creator is None:
            creator = primary_user
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
            created_by=creator,
            admin=creator,
        )
        game.members.create(user=creator)

        for i in range(game.variant.nations.count() - 1):
            other_user = User.objects.create_user(f"fixed_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"Fixed Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game

    return _create


@pytest.fixture
def sandbox_game_factory(db, primary_user, classical_variant, base_active_phase, sample_options):
    def _create(user=None):
        if user is None:
            user = primary_user
        game = models.Game.objects.create(
            name="Test Sandbox Game",
            variant=classical_variant,
            status=GameStatus.ACTIVE,
            sandbox=True,
            private=True,
        )
        phase = base_active_phase(game)
        phase.options = sample_options
        phase.save()
        game.members.create(user=user)
        return game

    return _create


# ---------------------------------------------------------------------------
# Game scenario fixtures (classical variant)
# ---------------------------------------------------------------------------


@pytest.fixture
def base_active_game_for_primary_user(db, classical_variant):
    return models.Game.objects.create(
        name="Primary User's Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
        deadline_mode=DeadlineMode.DURATION,
    )


@pytest.fixture
def active_game_created_by_primary_user(db, primary_user, base_active_game_for_primary_user, base_active_phase):
    base_active_phase(base_active_game_for_primary_user)
    base_active_game_for_primary_user.created_by = primary_user
    base_active_game_for_primary_user.admin = primary_user
    base_active_game_for_primary_user.save()
    base_active_game_for_primary_user.members.create(user=primary_user)
    return base_active_game_for_primary_user


@pytest.fixture
def base_active_phase(db, classical_england_nation, classical_edinburgh_province):
    def _create_phase(game):
        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)
        return phase

    return _create_phase


@pytest.fixture
def base_active_game_for_secondary_user(db, classical_variant):
    return models.Game.objects.create(
        name="Secondary User's Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )


@pytest.fixture
def active_game_created_by_secondary_user(db, secondary_user, base_active_game_for_secondary_user, base_active_phase):
    base_active_phase(base_active_game_for_secondary_user)
    base_active_game_for_secondary_user.created_by = secondary_user
    base_active_game_for_secondary_user.admin = secondary_user
    base_active_game_for_secondary_user.save()
    base_active_game_for_secondary_user.members.create(user=secondary_user)
    return base_active_game_for_secondary_user


@pytest.fixture
def active_game_with_phase_state(
    db,
    primary_user,
    base_active_game_for_primary_user,
    base_active_phase,
    classical_england_nation,
    classical_edinburgh_province,
):
    phase = base_active_phase(base_active_game_for_primary_user)
    member = base_active_game_for_primary_user.members.create(user=primary_user, nation=classical_england_nation)
    phase.phase_states.create(member=member, has_possible_orders=True)
    return base_active_game_for_primary_user


@pytest.fixture
def active_game_with_confirmed_phase_state(db, active_game_with_phase_state, classical_england_nation):
    phase_state = active_game_with_phase_state.current_phase.phase_states.first()
    phase_state.orders_confirmed = True
    phase_state.save()
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_eliminated_member(db, active_game_with_phase_state, secondary_user, classical_england_nation):
    member = active_game_with_phase_state.members.create(
        user=secondary_user, eliminated=True, nation=classical_england_nation
    )
    active_game_with_phase_state.current_phase.phase_states.create(member=member)
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_kicked_member(db, active_game_with_phase_state, secondary_user, classical_england_nation):
    member = active_game_with_phase_state.members.create(
        user=secondary_user, kicked=True, nation=classical_england_nation
    )
    active_game_with_phase_state.current_phase.phase_states.create(member=member)
    return active_game_with_phase_state


@pytest.fixture
def base_pending_phase(db, classical_england_nation, classical_edinburgh_province):
    def _create_phase(game):
        phase = game.phases.create(
            game=game,
            variant=game.variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.PENDING,
            ordinal=0,
        )
        phase.units.create(type="Fleet", nation=classical_england_nation, province=classical_edinburgh_province)
        phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)
        return phase

    return _create_phase


@pytest.fixture
def base_pending_game_for_primary_user(db, classical_variant):
    return models.Game.objects.create(
        name="Primary User's Pending Game",
        variant=classical_variant,
        status=GameStatus.PENDING,
    )


@pytest.fixture
def base_pending_game_for_secondary_user(db, classical_variant):
    return models.Game.objects.create(
        name="Secondary User's Pending Game",
        variant=classical_variant,
        status=GameStatus.PENDING,
    )


@pytest.fixture
def pending_game_created_by_secondary_user(
    db, secondary_user, base_pending_game_for_secondary_user, base_pending_phase
):
    base_pending_phase(base_pending_game_for_secondary_user)
    base_pending_game_for_secondary_user.created_by = secondary_user
    base_pending_game_for_secondary_user.admin = secondary_user
    base_pending_game_for_secondary_user.save()
    base_pending_game_for_secondary_user.members.create(user=secondary_user)
    return base_pending_game_for_secondary_user


@pytest.fixture
def pending_game_created_by_secondary_user_joined_by_primary(db, primary_user, pending_game_created_by_secondary_user):
    pending_game_created_by_secondary_user.members.create(user=primary_user)
    return pending_game_created_by_secondary_user


@pytest.fixture
def pending_game_created_by_primary_user(db, primary_user, base_pending_game_for_primary_user, base_pending_phase):
    base_pending_phase(base_pending_game_for_primary_user)
    base_pending_game_for_primary_user.created_by = primary_user
    base_pending_game_for_primary_user.admin = primary_user
    base_pending_game_for_primary_user.save()
    base_pending_game_for_primary_user.members.create(user=primary_user)
    return base_pending_game_for_primary_user


@pytest.fixture
def active_game_with_phase_options(db, active_game_with_phase_state, sample_options):
    phase = active_game_with_phase_state.current_phase
    phase.options = sample_options
    phase.save()
    return active_game_with_phase_state


@pytest.fixture
def sandbox_game_with_phase_options(
    db, primary_user, base_active_game_for_primary_user, base_active_phase, sample_options
):
    base_active_game_for_primary_user.sandbox = True
    base_active_game_for_primary_user.save()
    phase = base_active_phase(base_active_game_for_primary_user)
    phase.options = sample_options
    phase.save()
    for nation in base_active_game_for_primary_user.variant.nations.all():
        member = base_active_game_for_primary_user.members.create(user=primary_user, nation=nation)
        phase.phase_states.create(member=member)
    return base_active_game_for_primary_user


@pytest.fixture
def active_game(
    db,
    primary_user,
    secondary_user,
    classical_variant,
    classical_england_nation,
    classical_france_nation,
    classical_edinburgh_province,
):
    game = models.Game.objects.create(
        name="Test Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
        created_by=primary_user,
        admin=primary_user,
    )

    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )

    phase.units.create(type=UnitType.FLEET, nation=classical_england_nation, province=classical_edinburgh_province)
    phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

    primary_member = game.members.create(user=primary_user, nation=classical_england_nation)
    secondary_member = game.members.create(user=secondary_user, nation=classical_france_nation)
    phase.phase_states.create(member=primary_member)
    phase.phase_states.create(member=secondary_member)

    return game


@pytest.fixture
def game_with_options(active_game, sample_options):
    game = active_game
    phase = game.current_phase
    phase.options = sample_options
    phase.save()
    return game


# ---------------------------------------------------------------------------
# Order scenario fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def order_active_game(
    db,
    primary_user,
    secondary_user,
    base_active_game_for_primary_user,
    base_active_phase,
    classical_england_nation,
    classical_france_nation,
):
    phase = base_active_phase(base_active_game_for_primary_user)
    primary_member = base_active_game_for_primary_user.members.create(
        user=primary_user, nation=classical_england_nation
    )
    secondary_member = base_active_game_for_primary_user.members.create(
        user=secondary_user, nation=classical_france_nation
    )
    phase.phase_states.create(member=primary_member)
    phase.phase_states.create(member=secondary_member)
    return base_active_game_for_primary_user


@pytest.fixture
def primary_phase_state(order_active_game, primary_user):
    return order_active_game.current_phase.phase_states.get(member__user=primary_user)


@pytest.fixture
def game_with_many_phase_states(primary_user, classical_variant):
    game = Game.objects.create(
        name="Game with Many Phase States",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )

    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )

    all_nations = Nation.objects.filter(variant=classical_variant).order_by("id")

    for i, nation in enumerate(all_nations):
        if i == 0:
            user = primary_user
        else:
            user = User.objects.create_user(
                username=f"user_{nation.name.lower()}",
                email=f"{nation.name.lower()}@test.com",
                password="testpass123",
            )

        member = game.members.create(user=user, nation=nation)
        phase.phase_states.create(member=member)

        province_ids = {
            "England": "lon",
            "France": "par",
            "Germany": "ber",
            "Italy": "rom",
            "Austria": "vie",
            "Turkey": "con",
            "Russia": "mos",
        }

        province_id = province_ids.get(nation.name)
        if province_id:
            province = Province.objects.get(province_id=province_id, variant=classical_variant)
            phase.units.create(type=UnitType.ARMY, nation=nation, province=province)

    phase.options = {
        "England": {
            "bud": {
                "Next": {
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "gal": {"Next": {}, "Type": "Province"},
                                },
                                "Type": "SrcProvince",
                            }
                        },
                        "Type": "OrderType",
                    },
                },
                "Type": "Province",
            },
        },
    }
    phase.save()

    return game


@pytest.fixture
def retreat_phase(db):
    def _create_phase(game):
        phase = game.phases.create(
            variant=game.variant,
            season="Spring",
            year=1901,
            type=PhaseType.RETREAT,
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        primary_member = game.members.first()
        phase.phase_states.create(member=primary_member)
        return phase

    return _create_phase


# ---------------------------------------------------------------------------
# Channel scenario fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def active_game_with_private_channel(db, active_game_with_phase_state):
    private_channel = Channel.objects.create(game=active_game_with_phase_state, name="Private Channel", private=True)
    private_channel.members.add(active_game_with_phase_state.members.first())
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_public_channel(db, active_game_with_phase_state):
    Channel.objects.create(game=active_game_with_phase_state, name="Public Channel", private=False)
    return active_game_with_phase_state


@pytest.fixture
def active_game_with_channels(db, active_game_with_phase_state, secondary_user, classical_france_nation):
    private_member_channel = Channel.objects.create(
        game=active_game_with_phase_state, name="Private Member", private=True
    )
    private_member_channel.members.add(active_game_with_phase_state.members.first())
    ChannelMessage.objects.create(
        channel=private_member_channel, sender=active_game_with_phase_state.members.first(), body="Test message"
    )
    Channel.objects.create(game=active_game_with_phase_state, name="Private Non-Member", private=True)
    Channel.objects.create(game=active_game_with_phase_state, name="Public Channel", private=False)
    active_game_with_phase_state.members.create(user=secondary_user, nation=classical_france_nation)
    return active_game_with_phase_state


@pytest.fixture
def game_with_two_members(
    db, active_game_with_phase_state, secondary_user, classical_england_nation, classical_france_nation
):
    game = active_game_with_phase_state
    game.members.first().nation = classical_england_nation
    game.members.first().save()
    game.members.create(user=secondary_user, nation=classical_france_nation)
    return game


@pytest.fixture
def sandbox_game_with_channel(sandbox_game_factory):
    game = sandbox_game_factory()
    channel = Channel.objects.create(game=game, name="Sandbox Channel", private=True)
    channel.members.add(game.members.first())
    return game


@pytest.fixture
def game_with_public_channel_and_messages(db, active_game_with_phase_state, secondary_user, classical_france_nation):
    game = active_game_with_phase_state
    primary_member = game.members.first()
    secondary_member = game.members.create(user=secondary_user, nation=classical_france_nation)

    public_channel = Channel.objects.create(game=game, name="Public Press", private=False)

    ChannelMember.objects.create(member=primary_member, channel=public_channel)
    ChannelMember.objects.create(member=secondary_member, channel=public_channel)

    ChannelMessage.objects.create(channel=public_channel, sender=secondary_member, body="Message 1")
    ChannelMessage.objects.create(channel=public_channel, sender=secondary_member, body="Message 2")

    return game


# ---------------------------------------------------------------------------
# Italy vs Germany scenario fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def italy_vs_germany_active_game(italy_vs_germany_variant):
    return Game.objects.create(variant=italy_vs_germany_variant, name="Test Game", status=GameStatus.ACTIVE)


@pytest.fixture
def member_italy(italy_vs_germany_variant, italy_vs_germany_italy_nation, primary_user, italy_vs_germany_active_game):
    return Member.objects.create(
        nation=italy_vs_germany_italy_nation, user=primary_user, game=italy_vs_germany_active_game
    )


@pytest.fixture
def member_germany(
    italy_vs_germany_variant, italy_vs_germany_germany_nation, secondary_user, italy_vs_germany_active_game
):
    return Member.objects.create(
        nation=italy_vs_germany_germany_nation, user=secondary_user, game=italy_vs_germany_active_game
    )


@pytest.fixture
def phase_spring_1901_movement(italy_vs_germany_active_game):
    return Phase.objects.create(
        game=italy_vs_germany_active_game,
        variant=italy_vs_germany_active_game.variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
    )


@pytest.fixture
def phase_spring_1901_retreat(italy_vs_germany_active_game):
    return Phase.objects.create(
        game=italy_vs_germany_active_game,
        variant=italy_vs_germany_active_game.variant,
        season="Spring",
        year=1901,
        type="Retreat",
        ordinal=2,
    )


@pytest.fixture
def phase_fall_1901_movement(italy_vs_germany_active_game):
    return Phase.objects.create(
        game=italy_vs_germany_active_game,
        variant=italy_vs_germany_active_game.variant,
        season="Fall",
        year=1901,
        type="Movement",
        ordinal=3,
    )


@pytest.fixture
def phase_fall_1901_retreat(italy_vs_germany_active_game):
    return Phase.objects.create(
        game=italy_vs_germany_active_game,
        variant=italy_vs_germany_active_game.variant,
        season="Fall",
        year=1901,
        type="Retreat",
        ordinal=4,
    )


@pytest.fixture
def phase_fall_1901_adjustment(italy_vs_germany_active_game):
    return Phase.objects.create(
        game=italy_vs_germany_active_game,
        variant=italy_vs_germany_active_game.variant,
        season="Fall",
        year=1901,
        type="Adjustment",
        ordinal=5,
    )


@pytest.fixture
def italy_vs_germany_phase_with_orders(
    db,
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
    game = Game.objects.create(
        variant=italy_vs_germany_variant,
        name="Test Game",
        status=GameStatus.ACTIVE,
        deadline_mode=DeadlineMode.DURATION,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )

    member_italy = Member.objects.create(
        nation=italy_vs_germany_italy_nation,
        user=primary_user,
        game=game,
    )

    member_germany = Member.objects.create(
        nation=italy_vs_germany_germany_nation,
        user=secondary_user,
        game=game,
    )

    phase = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status=PhaseStatus.ACTIVE,
    )

    phase_state_italy = phase.phase_states.create(member=member_italy)
    phase_state_germany = phase.phase_states.create(member=member_germany)

    phase.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)

    phase.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)
    phase.supply_centers.create(province=italy_vs_germany_munich_province, nation=italy_vs_germany_germany_nation)

    phase.units.create(
        province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase.units.create(
        province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase.units.create(
        province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation
    )

    phase.units.create(
        province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation
    )
    phase.units.create(
        province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )
    phase.units.create(
        province=italy_vs_germany_munich_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )

    phase_state_italy.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )

    phase_state_germany.orders.create(
        source=italy_vs_germany_kiel_province,
        order_type=OrderType.HOLD,
    )

    return phase


@pytest.fixture
def game_with_three_phases(
    db,
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
    game = Game.objects.create(
        variant=italy_vs_germany_variant,
        name="Test Game with Multiple Phases",
        status=GameStatus.ACTIVE,
        deadline_mode=DeadlineMode.DURATION,
        movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
    )

    member_italy = Member.objects.create(
        nation=italy_vs_germany_italy_nation,
        user=primary_user,
        game=game,
    )

    member_germany = Member.objects.create(
        nation=italy_vs_germany_germany_nation,
        user=secondary_user,
        game=game,
    )

    phase1 = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1901,
        type="Movement",
        ordinal=1,
        status=PhaseStatus.COMPLETED,
    )

    phase_state_italy_1 = phase1.phase_states.create(member=member_italy)
    phase_state_germany_1 = phase1.phase_states.create(member=member_germany)

    phase1.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase1.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase1.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)
    phase1.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase1.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)
    phase1.supply_centers.create(province=italy_vs_germany_munich_province, nation=italy_vs_germany_germany_nation)

    phase1.units.create(
        province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase1.units.create(
        province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase1.units.create(
        province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation
    )
    phase1.units.create(
        province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation
    )
    phase1.units.create(
        province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )
    phase1.units.create(
        province=italy_vs_germany_munich_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )

    order1 = phase_state_italy_1.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )
    OrderResolution.objects.create(order=order1, status="OK")

    order2 = phase_state_germany_1.orders.create(
        source=italy_vs_germany_kiel_province,
        order_type=OrderType.HOLD,
    )
    OrderResolution.objects.create(order=order2, status="OK")

    phase2 = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Fall",
        year=1901,
        type="Movement",
        ordinal=2,
        status=PhaseStatus.COMPLETED,
    )

    phase_state_italy_2 = phase2.phase_states.create(member=member_italy)
    phase_state_germany_2 = phase2.phase_states.create(member=member_germany)

    phase2.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase2.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase2.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)
    phase2.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase2.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)
    phase2.supply_centers.create(province=italy_vs_germany_munich_province, nation=italy_vs_germany_germany_nation)

    phase2.units.create(
        province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase2.units.create(
        province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase2.units.create(
        province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation
    )
    phase2.units.create(
        province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation
    )
    phase2.units.create(
        province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )
    phase2.units.create(
        province=italy_vs_germany_munich_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )

    order3 = phase_state_italy_2.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )
    OrderResolution.objects.create(order=order3, status="OK")

    phase3 = Phase.objects.create(
        game=game,
        variant=italy_vs_germany_variant,
        season="Spring",
        year=1902,
        type="Movement",
        ordinal=3,
        status=PhaseStatus.ACTIVE,
    )

    phase_state_italy_3 = phase3.phase_states.create(member=member_italy, orders_confirmed=True)
    phase_state_germany_3 = phase3.phase_states.create(member=member_germany, orders_confirmed=False)

    phase3.supply_centers.create(province=italy_vs_germany_venice_province, nation=italy_vs_germany_italy_nation)
    phase3.supply_centers.create(province=italy_vs_germany_rome_province, nation=italy_vs_germany_italy_nation)
    phase3.supply_centers.create(province=italy_vs_germany_naples_province, nation=italy_vs_germany_italy_nation)
    phase3.supply_centers.create(province=italy_vs_germany_kiel_province, nation=italy_vs_germany_germany_nation)
    phase3.supply_centers.create(province=italy_vs_germany_berlin_province, nation=italy_vs_germany_germany_nation)

    phase3.units.create(
        province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase3.units.create(
        province=italy_vs_germany_rome_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
    )
    phase3.units.create(
        province=italy_vs_germany_naples_province, type=UnitType.FLEET, nation=italy_vs_germany_italy_nation
    )
    phase3.units.create(
        province=italy_vs_germany_kiel_province, type=UnitType.FLEET, nation=italy_vs_germany_germany_nation
    )
    phase3.units.create(
        province=italy_vs_germany_berlin_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
    )

    phase_state_italy_3.orders.create(
        source=italy_vs_germany_venice_province,
        order_type=OrderType.HOLD,
    )

    phase_state_germany_3.orders.create(
        source=italy_vs_germany_kiel_province,
        order_type=OrderType.HOLD,
    )

    return game


@pytest.fixture
def deadline_warning_game_factory(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    primary_user,
    secondary_user,
):
    def _create(deadline_mode, scheduled_resolution):
        game = Game.objects.create(
            name=f"Test Game {deadline_mode}",
            variant=italy_vs_germany_variant,
            deadline_mode=deadline_mode,
            movement_phase_duration="24h",
        )
        italy = game.members.create(nation=italy_vs_germany_italy_nation, user=primary_user)
        germany = game.members.create(nation=italy_vs_germany_germany_nation, user=secondary_user)
        phase = Phase.objects.create(
            game=game,
            variant=italy_vs_germany_variant,
            season="Spring",
            year=1901,
            type=PhaseType.MOVEMENT,
            ordinal=1,
            status=PhaseStatus.ACTIVE,
            scheduled_resolution=scheduled_resolution,
        )
        return game, italy, germany, phase

    return _create


@pytest.fixture
def add_italy_germany_units(
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    italy_vs_germany_venice_province,
    italy_vs_germany_kiel_province,
):
    def _add(phase):
        phase.units.create(
            province=italy_vs_germany_venice_province, type=UnitType.ARMY, nation=italy_vs_germany_italy_nation
        )
        phase.units.create(
            province=italy_vs_germany_kiel_province, type=UnitType.ARMY, nation=italy_vs_germany_germany_nation
        )

    return _add


@pytest.fixture
def elimination_game_factory(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    primary_user,
    secondary_user,
):
    def _create():
        game = Game.objects.create(
            name="Elimination Test",
            variant=italy_vs_germany_variant,
            status=GameStatus.ACTIVE,
        )
        italy = game.members.create(user=primary_user, nation=italy_vs_germany_italy_nation)
        germany = game.members.create(user=secondary_user, nation=italy_vs_germany_germany_nation)
        return game, italy, germany

    return _create


@pytest.fixture
def draw_notification_game_factory(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    primary_user,
    secondary_user,
):
    def _create():
        game = Game.objects.create(
            name="Draw Notification Test",
            variant=italy_vs_germany_variant,
            status=GameStatus.ACTIVE,
        )
        phase = Phase.objects.create(
            game=game,
            variant=italy_vs_germany_variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        italy = game.members.create(user=primary_user, nation=italy_vs_germany_italy_nation)
        germany = game.members.create(user=secondary_user, nation=italy_vs_germany_germany_nation)
        phase.phase_states.create(member=italy, has_possible_orders=True)
        phase.phase_states.create(member=germany, has_possible_orders=True)
        return game, italy, germany

    return _create


@pytest.fixture
def end_game_notification_game_factory(
    db,
    italy_vs_germany_variant,
    italy_vs_germany_italy_nation,
    italy_vs_germany_germany_nation,
    primary_user,
    secondary_user,
):
    def _create():
        game = Game.objects.create(
            name="End Game Test",
            variant=italy_vs_germany_variant,
            status=GameStatus.ACTIVE,
        )
        phase = Phase.objects.create(
            game=game,
            variant=italy_vs_germany_variant,
            season="Spring",
            year=1901,
            type="Movement",
            status=PhaseStatus.ACTIVE,
            ordinal=1,
        )
        italy = game.members.create(user=primary_user, nation=italy_vs_germany_italy_nation)
        germany = game.members.create(user=secondary_user, nation=italy_vs_germany_germany_nation)
        return game, phase, italy, germany

    return _create


# ---------------------------------------------------------------------------
# Mocks
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _neutralize_notification_delivery():
    with patch("notification.tasks.deliver_notifications.defer"):
        yield


@pytest.fixture
def mock_immediate_on_commit():
    def immediate_on_commit(func):
        func()

    with patch("django.db.transaction.on_commit", side_effect=immediate_on_commit):
        yield


@pytest.fixture
def in_memory_procrastinate():
    from procrastinate import testing
    from procrastinate.contrib.django import app

    connector = testing.InMemoryConnector()
    with app.replace_connector(connector):
        yield connector


# ---------------------------------------------------------------------------
# Static data fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_options():
    return {
        "England": {
            "bud": {
                "Next": {
                    "Hold": {"Next": {"bud": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"},
                    "Move": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "gal": {"Next": {}, "Type": "Province"},
                                    "rum": {"Next": {}, "Type": "Province"},
                                    "ser": {"Next": {}, "Type": "Province"},
                                    "tri": {"Next": {}, "Type": "Province"},
                                    "vie": {"Next": {}, "Type": "Province"},
                                },
                                "Type": "SrcProvince",
                            }
                        },
                        "Type": "OrderType",
                    },
                    "Support": {
                        "Next": {
                            "bud": {
                                "Next": {
                                    "sev": {"Next": {"rum": {"Next": {}, "Type": "Province"}}, "Type": "Province"},
                                    "tri": {"Next": {"tri": {"Next": {}, "Type": "Province"}}, "Type": "Province"},
                                    "vie": {
                                        "Next": {
                                            "gal": {"Next": {}, "Type": "Province"},
                                            "tri": {"Next": {}, "Type": "Province"},
                                            "vie": {"Next": {}, "Type": "Province"},
                                        },
                                        "Type": "Province",
                                    },
                                },
                                "Type": "SrcProvince",
                            }
                        },
                        "Type": "OrderType",
                    },
                },
                "Type": "Province",
            },
            "tri": {
                "Next": {
                    "Hold": {"Next": {"tri": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"},
                    "Move": {
                        "Next": {
                            "tri": {
                                "Next": {
                                    "adr": {"Next": {}, "Type": "Province"},
                                    "alb": {"Next": {}, "Type": "Province"},
                                    "ven": {"Next": {}, "Type": "Province"},
                                },
                                "Type": "SrcProvince",
                            }
                        },
                        "Type": "OrderType",
                    },
                },
                "Type": "Province",
            },
        },
    }


@pytest.fixture
def godip_options_simple_hold():
    return {
        "England": {
            "lon": {
                "Next": {"Hold": {"Next": {"lon": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"}},
                "Type": "Province",
            }
        }
    }


@pytest.fixture
def godip_options_england_london_hold():
    return {
        "England": {
            "lon": {
                "Next": {"Hold": {"Next": {"lon": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"}},
                "Type": "Province",
            }
        },
        "France": {},
    }


@pytest.fixture
def godip_options_england_france_both_hold():
    return {
        "England": {
            "lon": {
                "Next": {"Hold": {"Next": {"lon": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"}},
                "Type": "Province",
            }
        },
        "France": {
            "par": {
                "Next": {"Hold": {"Next": {"par": {"Next": {}, "Type": "SrcProvince"}}, "Type": "OrderType"}},
                "Type": "Province",
            }
        },
    }


@pytest.fixture
def adjudication_data_classical():
    data_path = Path(__file__).parent / "game" / "tests" / "data" / "start_classical.json"
    with open(data_path) as f:
        return json.load(f)


@pytest.fixture
def adjudication_data_italy_vs_germany():
    data_path = Path(__file__).parent / "game" / "tests" / "data" / "start_italy_vs_germany.json"
    with open(data_path) as f:
        return json.load(f)


@pytest.fixture
def mock_adjudication_data_basic():
    return {
        "season": "Spring",
        "year": 1901,
        "type": "Retreat",
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
            {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "ber", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "mun", "dislodged": False, "dislodged_by": None},
        ],
        "resolutions": [
            {"province": "ven", "result": "OK", "by": None},
            {"province": "kie", "result": "OK", "by": None},
        ],
    }


@pytest.fixture
def mock_adjudication_data_with_dislodged_unit():
    return {
        "season": "Spring",
        "year": 1901,
        "type": "Retreat",
        "options": {},
        "supply_centers": [
            {"province": "ven", "nation": "Italy"},
            {"province": "rom", "nation": "Italy"},
            {"province": "nap", "nation": "Italy"},
            {"province": "kie", "nation": "Germany"},
        ],
        "units": [
            {"type": "Army", "nation": "Italy", "province": "kie", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Italy", "province": "rom", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "kie", "dislodged": True, "dislodged_by": "ven"},
        ],
        "resolutions": [
            {"province": "ven", "result": "OK", "by": None},
            {"province": "kie", "result": "OK", "by": None},
        ],
    }


@pytest.fixture
def mock_adjudication_data_with_failed_implicit_hold():
    return {
        "season": "Spring",
        "year": 1901,
        "type": "Retreat",
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
            {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "ber", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "mun", "dislodged": False, "dislodged_by": None},
        ],
        "resolutions": [
            {"province": "ven", "result": "OK", "by": None},
            {"province": "kie", "result": "OK", "by": None},
            {"province": "ber", "result": "ErrBounce", "by": None},
        ],
    }


@pytest.fixture
def mock_adjudication_data_with_dislodged_implicit_hold():
    return {
        "season": "Spring",
        "year": 1901,
        "type": "Retreat",
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
            {"type": "Fleet", "nation": "Italy", "province": "nap", "dislodged": False, "dislodged_by": None},
            {"type": "Fleet", "nation": "Germany", "province": "kie", "dislodged": False, "dislodged_by": None},
            {"type": "Army", "nation": "Germany", "province": "ber", "dislodged": True, "dislodged_by": "ven"},
            {"type": "Army", "nation": "Germany", "province": "mun", "dislodged": False, "dislodged_by": None},
        ],
        "resolutions": [
            {"province": "ven", "result": "OK", "by": None},
            {"province": "kie", "result": "OK", "by": None},
            {"province": "ber", "result": "ErrForcedDisband", "by": None},
        ],
    }


@pytest.fixture
def pending_game_with_game_master_factory(db, primary_user, classical_variant, base_pending_phase):
    def _create(game_master=None):
        if game_master is None:
            game_master = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Game with Game Master",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            private=True,
            created_by=game_master,
            game_master=game_master,
            admin=game_master,
        )
        game.channels.create(name="Public Press", private=False)
        return game

    return _create


@pytest.fixture
def active_game_with_game_master_factory(db, primary_user, classical_variant, adjudication_data_classical):
    def _create(game_master=None):
        if game_master is None:
            game_master = primary_user
        game = models.Game.objects.create_from_template(
            classical_variant,
            name="Test Active Game with Game Master",
            movement_phase_duration=MovementPhaseDuration.TWENTY_FOUR_HOURS,
            deadline_mode=DeadlineMode.DURATION,
            private=True,
            created_by=game_master,
            game_master=game_master,
            admin=game_master,
        )
        game.channels.create(name="Public Press", private=False)

        for i in range(game.variant.nations.count()):
            other_user = User.objects.create_user(f"gm_player{i}@test.com", password="testpass")
            UserProfile.objects.create(user=other_user, name=f"GM Player {i}")
            game.members.create(user=other_user)

        with patch.object(adjudication_service, "start", return_value=adjudication_data_classical):
            game.start()

        return game

    return _create
