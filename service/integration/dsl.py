from datetime import timedelta
from unittest.mock import patch

from django.urls import reverse
from django.utils import timezone
from rest_framework import status

from common.constants import DeadlineMode, GameStatus, NationAssignment
from game.models import Game
from victory.models import Victory

RESOLVE_ALL_URL = reverse("phase-resolve-all")


class GameSession:
    def __init__(self, game, clients_by_nation, resolver_client):
        self.game = game
        self.clients_by_nation = clients_by_nation
        self._resolver_client = resolver_client
        self._order_url = reverse("order-create", args=[game.id])
        self._confirm_url = reverse("game-confirm-phase", args=[game.id])

    @classmethod
    def start(cls, *, variant, clients, name="DSL Test Game"):
        creator, *joiners = clients
        create_response = creator.post(
            reverse("game-create"),
            {
                "name": name,
                "variant_id": variant.id,
                "nation_assignment": NationAssignment.ORDERED,
                "private": False,
                "deadline_mode": DeadlineMode.DURATION,
                "confirmation_required": False,
            },
            format="json",
        )
        assert create_response.status_code == status.HTTP_201_CREATED, create_response.data
        game_id = create_response.data["id"]

        join_url = reverse("game-join", args=[game_id])
        for client in joiners:
            join_response = client.post(join_url, {"message": "Hello!"}, format="json")
            assert join_response.status_code == status.HTTP_201_CREATED, join_response.data

        game = Game.objects.get(id=game_id)
        members_in_join_order = list(game.members.order_by("id"))
        assert len(members_in_join_order) == len(clients), (
            f"Expected {len(clients)} members, got {len(members_in_join_order)}"
        )

        clients_by_nation = {}
        for client, member in zip(clients, members_in_join_order):
            assert member.nation is not None, "Game did not auto-start; member has no nation"
            clients_by_nation[member.nation.name] = client

        return cls(game=game, clients_by_nation=clients_by_nation, resolver_client=creator)

    @property
    def current_phase(self):
        self.game.refresh_from_db()
        return self.game.current_phase

    def order(self, nation, *parts):
        client = self.clients_by_nation[nation]
        selected = []
        last_response = None
        for part in parts:
            selected = [*selected, part]
            last_response = client.post(self._order_url, {"selected": selected}, format="json")
        assert last_response is not None
        assert last_response.status_code == status.HTTP_201_CREATED, last_response.data
        return last_response

    def confirm_all(self):
        for client in self.clients_by_nation.values():
            response = client.put(self._confirm_url)
            assert response.status_code == status.HTTP_200_OK, response.data

    def resolve(self):
        response = self._resolver_client.post(RESOLVE_ALL_URL)
        assert response.status_code == status.HTTP_200_OK, response.data
        assert response.data["resolved"] >= 1, response.data

    def assert_phase(self, *, season, year, type):
        phase = self.current_phase
        assert phase.season == season, f"Expected season {season}, got {phase.season}"
        assert phase.year == year, f"Expected year {year}, got {phase.year}"
        assert phase.type == type, f"Expected type {type}, got {phase.type}"

    def assert_unit(self, *, nation, province, type=None):
        phase = self.current_phase
        qs = phase.units.filter(nation__name=nation, province__province_id=province)
        if type is not None:
            qs = qs.filter(type=type)
        assert qs.exists(), f"Expected {nation} unit at {province}, not found"

    def assert_dislodged(self, *, nation, province):
        phase = self.current_phase
        unit = phase.units.filter(nation__name=nation, province__province_id=province).first()
        assert unit is not None, f"No {nation} unit at {province}"
        assert unit.dislodged, f"{nation} unit at {province} is not dislodged"

    def assert_no_unit(self, *, nation, province):
        phase = self.current_phase
        assert not phase.units.filter(
            nation__name=nation, province__province_id=province
        ).exists(), f"Did not expect {nation} unit at {province}"

    # ---------- Replay-mode helpers ----------

    def confirm_subset(self, confirming_nations):
        for nation in confirming_nations:
            client = self.clients_by_nation[nation]
            response = client.put(self._confirm_url)
            assert response.status_code == status.HTTP_200_OK, response.data

    def resolve_after_deadline(self):
        phase = self.current_phase
        if phase.scheduled_resolution is not None:
            future = phase.scheduled_resolution + timedelta(minutes=1)
        else:
            future = timezone.now() + timedelta(days=2)
        with patch("django.utils.timezone.now", return_value=future):
            response = self._resolver_client.post(RESOLVE_ALL_URL)
            assert response.status_code == status.HTTP_200_OK, response.data
            assert response.data["resolved"] >= 1, response.data

    def assert_resolutions(self, resolved_phase, expected_orders):
        actual_by_key = {}
        for ps in resolved_phase.phase_states.all():
            nation = ps.member.nation.name
            for order in ps.orders.all():
                key = (nation, tuple(order.selected))
                resolution = getattr(order, "resolution", None)
                actual_by_key[key] = resolution.status if resolution else None

        mismatches = []
        for expected in expected_orders:
            key = (expected["nation"], tuple(expected["selected"]))
            if key not in actual_by_key:
                mismatches.append(f"missing order: {key}")
                continue
            actual = actual_by_key[key]
            if actual != expected["expected_resolution"]:
                mismatches.append(
                    f"{key}: expected {expected['expected_resolution']!r}, got {actual!r}"
                )
        assert not mismatches, "Resolution mismatches:\n  " + "\n  ".join(mismatches)

    def assert_state(self, expected_state_after):
        if expected_state_after is None:
            return
        phase = self.current_phase

        actual_units = sorted(
            (u.nation.name, u.province.province_id, u.type, u.dislodged)
            for u in phase.units.all()
        )
        expected_units = sorted(
            (u["nation"], u["province"], u["type"], u["dislodged"])
            for u in expected_state_after["units"]
        )
        assert actual_units == expected_units, (
            "Units mismatch:\n"
            f"  Expected: {expected_units}\n"
            f"  Actual:   {actual_units}"
        )

        actual_scs = {
            sc.province.province_id: sc.nation.name
            for sc in phase.supply_centers.all()
        }
        assert actual_scs == expected_state_after["supply_centers"], (
            "Supply centers mismatch:\n"
            f"  Expected: {expected_state_after['supply_centers']}\n"
            f"  Actual:   {actual_scs}"
        )

    def assert_outcome(self, outcome):
        self.game.refresh_from_db()
        if outcome["type"] == "solo":
            assert self.game.status == GameStatus.COMPLETED, (
                f"Expected game COMPLETED, got {self.game.status}"
            )
            victory = Victory.objects.get(game=self.game)
            assert victory.type == "solo", f"Expected solo victory, got {victory.type}"
            actual_winners = sorted(m.nation.name for m in victory.members.all())
            assert actual_winners == sorted(outcome["winners"]), (
                f"Winners mismatch: expected {outcome['winners']}, got {actual_winners}"
            )
        # Draw outcomes can't be reproduced from replay alone (no draw-vote sequence
        # is captured), so we don't assert game completion for them — the test just
        # validates that we got to the terminal phase with the expected orders.

    def _phase_matches_current(self, phase_data):
        phase = self.current_phase
        return (
            phase.season == phase_data["season"]
            and phase.year == phase_data["year"]
            and phase.type == phase_data["type"]
        )

    def _is_skippable_phase(self, phase_data):
        # Phases with no possible orders for anyone -- empty retreats (nothing
        # dislodged) and balanced adjustments -- are no longer created; the
        # adjudicator advances straight to the next interactive phase. These
        # were recorded with an "auto" trigger and no orders.
        return (
            phase_data["type"] in ("Retreat", "Adjustment")
            and phase_data["resolution_trigger"] == "auto"
            and not phase_data["orders"]
        )

    def replay_all(self, phases):
        i = 0
        n = len(phases)
        while i < n:
            phase_data = phases[i]

            self.assert_phase(
                season=phase_data["season"],
                year=phase_data["year"],
                type=phase_data["type"],
            )

            trigger = phase_data["resolution_trigger"]

            if trigger == "terminal":
                for order in phase_data["orders"]:
                    self.order(order["nation"], *order["selected"])
                return

            phase_being_resolved = self.current_phase

            for order in phase_data["orders"]:
                self.order(order["nation"], *order["selected"])

            if trigger == "auto":
                self.resolve()
            elif trigger == "consensus":
                self.confirm_all()
                self.resolve()
            elif trigger == "deadline":
                non_confirming = set(phase_data["non_confirming_nations"])
                confirming = [n for n in self.clients_by_nation if n not in non_confirming]
                self.confirm_subset(confirming)
                self.resolve_after_deadline()
            else:
                raise ValueError(f"Unknown resolution_trigger: {trigger!r}")

            self.assert_resolutions(phase_being_resolved, phase_data["orders"])

            # Fold in any phases the adjudicator skipped: units carry forward
            # unchanged and supply-center ownership recomputed during a skipped
            # retreat surfaces on the phase we land on, so the resulting state
            # matches the last skipped phase's expected_state_after.
            expected_state = phase_data["expected_state_after"]
            j = i + 1
            while j < n and not self._phase_matches_current(phases[j]):
                skipped = phases[j]
                assert self._is_skippable_phase(skipped), (
                    f"Phase divergence: fixture expected {skipped['season']} "
                    f"{skipped['year']} {skipped['type']} but game is at "
                    f"{self.current_phase.name}"
                )
                if skipped["expected_state_after"] is not None:
                    expected_state = skipped["expected_state_after"]
                j += 1

            self.assert_state(expected_state)
            i = j
