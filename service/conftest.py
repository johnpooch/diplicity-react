import pytest
from unittest.mock import patch
import json
from django.conf import settings
from django.contrib.auth import get_user_model
from game import models
from user_profile.models import UserProfile
from variant.models import Variant
from nation.models import Nation
from province.models import Province
from rest_framework.test import APIClient
from common.constants import PhaseStatus, UnitType, GameStatus

User = get_user_model()


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
def base_active_game_for_primary_user(db, classical_variant):
    return models.Game.objects.create(
        name="Primary User's Active Game",
        variant=classical_variant,
        status=GameStatus.ACTIVE,
    )


@pytest.fixture
def active_game_created_by_primary_user(db, primary_user, base_active_game_for_primary_user, base_active_phase):
    """
    Creates an active game created by the primary user.
    """
    base_active_phase(base_active_game_for_primary_user)
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
    phase_state = phase.phase_states.create(member=member)
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
    base_pending_game_for_secondary_user.members.create(user=secondary_user)
    return base_pending_game_for_secondary_user


@pytest.fixture
def pending_game_created_by_secondary_user_joined_by_primary(db, primary_user, pending_game_created_by_secondary_user):
    pending_game_created_by_secondary_user.members.create(user=primary_user)
    return pending_game_created_by_secondary_user


@pytest.fixture
def pending_game_created_by_primary_user(db, primary_user, base_pending_game_for_primary_user, base_pending_phase):
    base_pending_phase(base_pending_game_for_primary_user)
    base_pending_game_for_primary_user.members.create(user=primary_user)
    return base_pending_game_for_primary_user


@pytest.fixture
def active_game_with_phase_options(db, active_game_with_phase_state, sample_options):
    phase = active_game_with_phase_state.current_phase
    phase.options = sample_options
    phase.save()
    return active_game_with_phase_state


@pytest.fixture(scope="session")
def classical_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="classical")


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


@pytest.fixture(scope="session")
def italy_vs_germany_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="italy-vs-germany")


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
    )

    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
        ordinal=1,
    )

    # Create units and supply centers
    phase.units.create(type=UnitType.FLEET, nation=classical_england_nation, province=classical_edinburgh_province)
    phase.supply_centers.create(nation=classical_england_nation, province=classical_edinburgh_province)

    # Create members and phase states
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


@pytest.fixture
def mock_send_notification_to_users():
    with patch("notification.signals.send_notification_to_users") as mock_send_notification_to_users:
        yield mock_send_notification_to_users


@pytest.fixture
def mock_immediate_on_commit():
    def immediate_on_commit(func):
        func()  # Execute immediately instead of deferring

    with patch("django.db.transaction.on_commit", side_effect=immediate_on_commit):
        yield

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
