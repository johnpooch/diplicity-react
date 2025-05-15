from django.contrib.auth import get_user_model
from .base import BaseTestCase
from ..services import AdjudicationService
from .. import models

User = get_user_model()


class BaseAdjudicationTestCase(BaseTestCase):
    def setUp(self):
        super().setUp()
        self.adjudication_service = AdjudicationService(self.user)

    def get_unit(self, response, province, dislodged=False):
        return next(
            unit
            for unit in response["phase"]["units"]
            if unit["province"] == province
            and unit.get("dislodged", False) == dislodged
        )

    def get_resolution(self, response, province):
        return next(
            resolution
            for resolution in response["phase"]["resolutions"]
            if resolution["province"] == province
        )

    def get_supply_center(self, response, province):
        return next(
            supply_center
            for supply_center in response["phase"]["supply_centers"]
            if supply_center["province"] == province
        )

    def create_unit(self, phase, nation, province, unit_type, **kwargs):
        phase.units.create(type=unit_type, nation=nation, province=province, **kwargs)

    def create_order(self, phase, nation, order_type, source, target=None, aux=None):
        phase_state = phase.phase_states.get(member__nation=nation)
        phase_state.orders.create(
            order_type=order_type,
            source=source,
            target=target,
            aux=aux,
        )


class TestAdjudicationStart(BaseAdjudicationTestCase):
    def setUp(self):
        super().setUp()

    def test_start_classical(self):
        game = self.create_game(self.user, "Test Game")

        response = self.adjudication_service.start(game)

        unit = self.get_unit(response, "ank")
        supply_center = self.get_supply_center(response, "ank")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Movement")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "Turkey")
        self.assertEqual(unit["province"], "ank")

        self.assertIsInstance(response["phase"]["supply_centers"], list)
        self.assertEqual(supply_center["province"], "ank")
        self.assertEqual(supply_center["nation"], "Turkey")

        self.assertEqual(response["phase"]["resolutions"], [])

        self.assertIsInstance(response["options"], dict)


class TestAdjudicationResolve(BaseAdjudicationTestCase):
    def setUp(self):
        super().setUp()
        self.game = self.create_game(self.user, "Test Game")
        self.france_member = self.game.members.create(
            user=self.other_user, nation="France"
        )
        self.england_member = self.game.members.create(user=self.user, nation="England")

    def create_phase(self, season, year, phase_type):
        phase = self.game.phases.create(
            season=season, year=year, type=phase_type, status=models.Phase.PENDING
        )
        phase.phase_states.create(member=self.england_member)
        phase.phase_states.create(member=self.france_member)
        return phase

    def test_resolve_move(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_order(phase, "England", "Move", "lon", "eng")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "eng")
        resolution = self.get_resolution(response, "lon")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "eng")

        self.assertEqual(resolution["province"], "lon")
        self.assertEqual(resolution["result"], "OK")

    def test_resolve_move_to_source(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_order(phase, "England", "Move", "lon", "lon")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "lon")
        resolution = self.get_resolution(response, "lon")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "lon")

        self.assertEqual(resolution["province"], "lon")
        self.assertEqual(resolution["result"], "ErrIllegalMove")
        self.assertEqual(resolution["by"], None)

    def test_resolve_move_bounce(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_unit(phase, "England", "lvp", "Army")

        self.create_order(phase, "England", "Move", "lon", "wal")
        self.create_order(phase, "England", "Move", "lvp", "wal")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "lon")
        resolution = self.get_resolution(response, "lon")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "lon")

        self.assertEqual(resolution["province"], "lon")
        self.assertEqual(resolution["result"], "ErrBounce")
        self.assertEqual(resolution["by"], "lvp")

    def test_resolve_move_three_way_bounce(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_unit(phase, "England", "lvp", "Army")
        self.create_unit(phase, "France", "iri", "Fleet")

        self.create_order(phase, "England", "Move", "lon", "wal")
        self.create_order(phase, "England", "Move", "lvp", "wal")
        self.create_order(phase, "France", "Move", "iri", "wal")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "lon")
        resolution = self.get_resolution(response, "lon")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "lon")

        self.assertEqual(resolution["province"], "lon")
        self.assertEqual(resolution["result"], "ErrBounce")
        self.assertIn(resolution["by"], ["lvp", "iri"])

    def test_resolve_successful_support_move(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_unit(phase, "England", "lvp", "Army")
        self.create_unit(phase, "France", "iri", "Fleet")

        self.create_order(phase, "England", "Move", "lon", "wal")
        self.create_order(phase, "England", "Support", "lvp", "lon", "wal")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "wal")
        resolution_move = self.get_resolution(response, "lon")
        resolution_support = self.get_resolution(response, "lvp")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "wal")

        self.assertEqual(resolution_move["province"], "lon")
        self.assertEqual(resolution_move["result"], "OK")

        self.assertEqual(resolution_support["province"], "lvp")
        self.assertEqual(resolution_support["result"], "OK")

    def test_resolve_support_without_move(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_unit(phase, "England", "lvp", "Army")

        self.create_order(phase, "England", "Hold", "lon")
        self.create_order(phase, "England", "Support", "lvp", "lon", "wal")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "lon")
        resolution_support = self.get_resolution(response, "lvp")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "lon")

        self.assertEqual(resolution_support["province"], "lvp")
        self.assertEqual(resolution_support["result"], "ErrInvalidSupporteeOrder")
        self.assertEqual(resolution_support["by"], None)

    def test_resolve_illegal_support_destination(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "France", "wal", "Army")
        self.create_unit(phase, "France", "lvp", "Army")

        self.create_order(phase, "France", "Move", "wal", "lon")
        self.create_order(phase, "France", "Support", "lvp", "wal", "lon")

        response = self.adjudication_service.resolve(self.game)

        resolution_support = self.get_resolution(response, "lvp")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)

        self.assertEqual(resolution_support["province"], "lvp")
        self.assertEqual(resolution_support["result"], "ErrIllegalSupportDestination")

    def test_resolve_dislodged_by_supported_move(self):
        phase = self.create_phase("Spring", 1901, "Movement")
        self.create_unit(phase, "England", "lon", "Fleet")
        self.create_unit(phase, "France", "wal", "Army")
        self.create_unit(phase, "France", "yor", "Army")

        self.create_order(phase, "France", "Move", "wal", "lon")
        self.create_order(phase, "France", "Support", "yor", "wal", "lon")

        response = self.adjudication_service.resolve(self.game)

        dislodged_unit = self.get_unit(response, "lon", dislodged=True)
        resolution_move = self.get_resolution(response, "wal")
        resolution_support = self.get_resolution(response, "yor")

        self.assertEqual(response["phase"]["season"], "Spring")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Retreat")

        self.assertIsInstance(response["phase"]["units"], list)

        self.assertEqual(resolution_move["province"], "wal")
        self.assertEqual(resolution_move["result"], "OK")

        self.assertEqual(resolution_support["province"], "yor")
        self.assertEqual(resolution_support["result"], "OK")

        self.assertEqual(dislodged_unit["nation"], "England")
        self.assertEqual(dislodged_unit["province"], "lon")
        self.assertEqual(dislodged_unit["dislodged"], True)
        self.assertEqual(dislodged_unit["dislodged_by"], "wal")

    def test_resolve_valid_retreat(self):
        phase = self.create_phase("Spring", 1901, "Retreat")
        self.create_unit(phase, "England", "lon", "Fleet", dislodged=True)

        self.create_order(phase, "England", "Move", "lon", "eng")

        response = self.adjudication_service.resolve(self.game)

        unit = self.get_unit(response, "eng")
        resolution = self.get_resolution(response, "lon")

        self.assertEqual(response["phase"]["season"], "Fall")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Movement")

        self.assertIsInstance(response["phase"]["units"], list)
        self.assertEqual(unit["type"], "Fleet")
        self.assertEqual(unit["nation"], "England")
        self.assertEqual(unit["province"], "eng")

        self.assertEqual(resolution["province"], "lon")
        self.assertEqual(resolution["result"], "OK")

    def test_resolve_invalid_retreat(self):
        phase = self.create_phase("Spring", 1901, "Retreat")
        self.create_unit(
            phase, "England", "lon", "Fleet", dislodged=True, dislodged_by="wal"
        )

        # Attempt to retreat to an invalid province
        self.create_order(phase, "England", "Move", "lon", "invalid_province")

        response = self.adjudication_service.resolve(self.game)

        resolution = self.get_resolution(response, "lon")

        self.assertEqual(response["phase"]["season"], "Fall")
        self.assertEqual(response["phase"]["year"], 1901)
        self.assertEqual(response["phase"]["type"], "Movement")

        self.assertIsInstance(response["phase"]["units"], list)

        # Assert iteration error when trying to get the unit
        try:
            dislodged_unit = self.get_unit(response, "lon", dislodged=True)
        except StopIteration:
            dislodged_unit = None

        self.assertIsNone(dislodged_unit)

        self.assertEqual(resolution["province"], "lon")
        self.assertEqual(resolution["result"], "ErrInvalidDestination")
