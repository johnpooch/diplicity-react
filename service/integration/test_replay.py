import json
from pathlib import Path

import pytest

from integration.dsl import GameSession

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load_fixture(name):
    with (FIXTURES_DIR / name).open() as f:
        return json.load(f)


@pytest.mark.django_db
def test_replay_fixture_01_ivg_draw(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_immediate_on_commit,
):
    fixture = _load_fixture("01_ivg_draw_23p.json")
    assert fixture["variant"] == italy_vs_germany_variant.name

    session = GameSession.start(
        variant=italy_vs_germany_variant,
        clients=[authenticated_client, authenticated_client_for_secondary_user],
    )

    session.replay_all(fixture["phases"])

    session.assert_outcome(fixture["outcome"])


@pytest.mark.django_db
def test_replay_fixture_02_classical_solo(
    authenticated_client,
    authenticated_client_for_secondary_user,
    authenticated_client_for_tertiary_user,
    authenticated_clients_4_through_7,
    classical_variant,
    mock_immediate_on_commit,
):
    fixture = _load_fixture("02_classical_solo_35p.json")
    assert fixture["variant"] == classical_variant.name

    session = GameSession.start(
        variant=classical_variant,
        clients=[
            authenticated_client,
            authenticated_client_for_secondary_user,
            authenticated_client_for_tertiary_user,
            *authenticated_clients_4_through_7,
        ],
    )

    session.replay_all(fixture["phases"])

    session.assert_outcome(fixture["outcome"])


@pytest.mark.django_db
@pytest.mark.parametrize(
    "fixture_name",
    [
        "09_classical_solo_110p.json",
        "10_classical_solo_convoyheavy_65p.json",
    ],
)
def test_replay_classical_long_solos(
    fixture_name,
    authenticated_client,
    authenticated_client_for_secondary_user,
    authenticated_client_for_tertiary_user,
    authenticated_clients_4_through_7,
    classical_variant,
    mock_immediate_on_commit,
):
    fixture = _load_fixture(fixture_name)
    assert fixture["variant"] == classical_variant.name

    session = GameSession.start(
        variant=classical_variant,
        clients=[
            authenticated_client,
            authenticated_client_for_secondary_user,
            authenticated_client_for_tertiary_user,
            *authenticated_clients_4_through_7,
        ],
    )

    session.replay_all(fixture["phases"])

    session.assert_outcome(fixture["outcome"])


@pytest.mark.django_db
def test_replay_fixture_03_hundred_solo(
    authenticated_client,
    authenticated_client_for_secondary_user,
    authenticated_client_for_tertiary_user,
    hundred_variant,
    mock_immediate_on_commit,
):
    fixture = _load_fixture("03_hundred_solo_40p.json")
    assert fixture["variant"] == hundred_variant.name

    session = GameSession.start(
        variant=hundred_variant,
        clients=[
            authenticated_client,
            authenticated_client_for_secondary_user,
            authenticated_client_for_tertiary_user,
        ],
    )

    session.replay_all(fixture["phases"])

    session.assert_outcome(fixture["outcome"])
