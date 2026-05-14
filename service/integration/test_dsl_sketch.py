import pytest

from common.constants import UnitType
from integration.dsl import GameSession


@pytest.mark.django_db
def test_dislodged_unit_scenario_with_dsl(
    authenticated_client,
    authenticated_client_for_secondary_user,
    italy_vs_germany_variant,
    mock_send_notification_to_users,
    mock_immediate_on_commit,
):
    session = GameSession.start(
        variant=italy_vs_germany_variant,
        clients=[authenticated_client, authenticated_client_for_secondary_user],
    )

    # Spring 1901 Movement: Germany advances; Italy moves to Tyrolia.
    session.assert_phase(season="Spring", year=1901, type="Movement")
    session.order("Germany", "ber", "Move", "mun")
    session.order("Germany", "mun", "Move", "boh")
    session.order("Italy", "ven", "Move", "tyr")
    session.confirm_all()
    session.resolve()

    # Spring 1901 Retreat: no dislodgements, auto-resolves.
    session.assert_phase(season="Spring", year=1901, type="Retreat")
    session.resolve()

    # Fall 1901 Movement: Germany attacks Italy in Tyrolia with Bohemia support.
    session.assert_phase(season="Fall", year=1901, type="Movement")
    session.assert_unit(nation="Germany", province="mun")
    session.assert_unit(nation="Germany", province="boh")
    session.assert_unit(nation="Italy", province="tyr")

    session.order("Germany", "mun", "Move", "tyr")
    session.order("Germany", "boh", "Support", "mun", "tyr")
    session.confirm_all()
    session.resolve()

    # Fall 1901 Retreat: Italy retreats from Tyrolia to Trieste.
    session.assert_phase(season="Fall", year=1901, type="Retreat")
    session.assert_unit(nation="Germany", province="tyr")
    session.assert_dislodged(nation="Italy", province="tyr")
    session.order("Italy", "tyr", "Move", "tri")
    session.confirm_all()
    session.resolve()

    # Final state in Fall 1901 Adjustment.
    session.assert_unit(nation="Germany", province="tyr", type=UnitType.ARMY)
    session.assert_unit(nation="Italy", province="tri", type=UnitType.ARMY)
    session.assert_no_unit(nation="Italy", province="tyr")
