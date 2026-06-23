from datetime import timedelta

import pytest
from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from common.constants import GameStatus, PhaseStatus

list_viewname = "game-list"


@pytest.mark.django_db
def test_started_games_ordered_by_deadline_with_sandboxes_last(
    authenticated_client, primary_user, classical_variant, game_factory, phase_factory
):
    now = timezone.now()

    soon = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    soon.members.create(user=primary_user)
    phase_factory(game=soon, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(hours=1))

    later = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    later.members.create(user=primary_user)
    phase_factory(game=later, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(hours=5))

    manual = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    manual.members.create(user=primary_user)
    phase_factory(game=manual, status=PhaseStatus.ACTIVE, scheduled_resolution=None)

    sandbox = game_factory(variant=classical_variant, status=GameStatus.ACTIVE, sandbox=True)
    sandbox.members.create(user=primary_user)
    phase_factory(game=sandbox, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(minutes=10))

    url = reverse(list_viewname) + "?mine=true&status=active&ordering=deadline"
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    ids = [g["id"] for g in response.data["results"]]
    my_ids = {soon.id, later.id, manual.id, sandbox.id}
    assert [i for i in ids if i in my_ids] == [soon.id, later.id, manual.id, sandbox.id]


@pytest.mark.django_db
def test_eliminated_games_sort_last_regardless_of_deadline(
    authenticated_client, primary_user, classical_variant, game_factory, phase_factory
):
    now = timezone.now()

    active = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    active.members.create(user=primary_user)
    phase_factory(game=active, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(hours=5))

    eliminated = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    eliminated.members.create(user=primary_user, eliminated=True)
    phase_factory(game=eliminated, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(hours=1))

    url = reverse(list_viewname) + "?mine=true&status=active&ordering=deadline"
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    ids = [g["id"] for g in response.data["results"]]
    my_ids = {active.id, eliminated.id}
    assert [i for i in ids if i in my_ids] == [active.id, eliminated.id]


@pytest.mark.django_db
def test_started_games_default_order_is_created_at(
    authenticated_client, primary_user, classical_variant, game_factory, phase_factory
):
    now = timezone.now()

    first = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    first.members.create(user=primary_user)
    phase_factory(game=first, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(hours=1))

    second = game_factory(variant=classical_variant, status=GameStatus.ACTIVE)
    second.members.create(user=primary_user)
    phase_factory(game=second, status=PhaseStatus.ACTIVE, scheduled_resolution=now + timedelta(hours=5))

    url = reverse(list_viewname) + "?mine=true&status=active"
    response = authenticated_client.get(url)

    assert response.status_code == status.HTTP_200_OK
    ids = [g["id"] for g in response.data["results"]]
    my_ids = {first.id, second.id}
    assert [i for i in ids if i in my_ids] == [second.id, first.id]
