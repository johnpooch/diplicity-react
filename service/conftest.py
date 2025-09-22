import pytest
import json
from django.contrib.auth import get_user_model
from game import models
from rest_framework.test import APIClient

User = get_user_model()


@pytest.fixture(scope="session")
def primary_user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        primary_user = User.objects.create_user(
            username="primaryuser", email="primary@example.com", password="testpass123"
        )
        models.UserProfile.objects.create(
            user=primary_user, name="Primary User", picture=""
        )
        return primary_user


@pytest.fixture(scope="session")
def secondary_user(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        secondary_user = User.objects.create_user(
            username="secondaryuser", email="secondary@example.com", password="testpass123"
        )
        models.UserProfile.objects.create(
            user=secondary_user, name="Secondary User", picture=""
        )
        return secondary_user



@pytest.fixture(scope="session")
def classical_variant(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        return models.Variant.objects.get(id="classical")


@pytest.fixture(scope="session")
def authenticated_client(primary_user):
    client = APIClient()
    client.force_authenticate(user=primary_user)
    return client

@pytest.fixture(scope="session")
def unauthenticated_client():
    return APIClient()


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
def game_with_options(active_game, primary_user, sample_options):
    game = active_game
    phase = game.current_phase
    phase.options = json.dumps(sample_options)
    phase.save()
    return game

