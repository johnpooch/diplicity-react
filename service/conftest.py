import pytest
import json
from django.contrib.auth import get_user_model
from game import models
from user_profile.models import UserProfile
from variant.models import Variant
from nation.models import Nation
from province.models import Province
from rest_framework.test import APIClient
from common.constants import PhaseStatus, UnitType

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
def classical_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return Variant.objects.get(id="classical")


@pytest.fixture(scope="session")
def authenticated_client(primary_user):
    client = APIClient()
    client.force_authenticate(user=primary_user)
    return client


@pytest.fixture(scope="session")
def unauthenticated_client():
    return APIClient()


@pytest.fixture(scope="session")
def classical_england_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="England", variant=classical_variant)


@pytest.fixture(scope="session")
def classical_france_nation(django_db_setup, django_db_blocker, classical_variant):
    with django_db_blocker.unblock():
        return Nation.objects.get(name="France", variant=classical_variant)


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
        status=models.Game.ACTIVE,
    )

    # Create phase
    phase = game.phases.create(
        variant=classical_variant,
        season="Spring",
        year=1901,
        type="Movement",
        status=PhaseStatus.ACTIVE,
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
    phase.options = json.dumps(sample_options)
    phase.save()
    return game
