import json
from pathlib import Path

from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import BaseCommand, CommandError

from agent.api_client import ApiClient, ApiClientError
from agent.context import fetch_context
from common.constants import OrderResolutionStatus
from game.models import Game
from harness.adapter import data_to_fixture
from harness.exceptions import FixtureError
from order.models import Order
from phase.models import Phase

MOVE_TYPES = ("Move", "MoveViaConvoy")


def _order_state(order):
    state = {"type": order.order_type, "nation": order.nation.name, "source": order.source.province_id}
    if order.order_type in MOVE_TYPES and order.named_coast:
        target = order.named_coast.province_id
    else:
        target = order.target.province_id if order.target else None
    if target:
        state["target"] = target
    if order.aux:
        state["aux"] = order.aux.province_id
    if order.unit_type:
        state["unitType"] = order.unit_type
    try:
        resolution = order.resolution
    except ObjectDoesNotExist:
        resolution = None
    state["failed"] = bool(resolution and resolution.status != OrderResolutionStatus.SUCCEEDED)
    return state


def _render_state(phase):
    return {
        "nationColors": {nation.name: nation.color for nation in phase.variant.nations.all()},
        "supplyCenters": [
            {"province": center.province.province_id, "nation": center.nation.name}
            for center in phase.supply_centers.all()
            if center.nation
        ],
        "units": [
            {
                "province": unit.province.province_id,
                "nation": unit.nation.name,
                "type": unit.type,
                "dislodged": unit.dislodged,
            }
            for unit in phase.units.all()
        ],
        "orders": [_order_state(order) for order in Order.objects.for_phase(phase).with_related_data()],
        "selected": [],
        "highlighted": [],
    }


class Command(BaseCommand):
    help = "Dump a game phase as a board RenderState (for render-phase.mjs) and per-nation select_orders fixture stubs."

    def add_arguments(self, parser):
        parser.add_argument("--game", required=True, help="game id")
        parser.add_argument("--phase", type=int, default=None, help="phase id; defaults to the current phase")
        parser.add_argument("--out", default="phase_dumps", help="output directory")

    def handle(self, *args, **options):
        game = Game.objects.filter(id=options["game"]).first()
        if game is None:
            raise CommandError(f"no game with id '{options['game']}'")

        current = game.current_phase
        if options["phase"] is not None:
            phase = Phase.objects.filter(game=game, id=options["phase"]).first()
            if phase is None:
                raise CommandError(f"game '{game.id}' has no phase with id {options['phase']}")
        else:
            phase = current
            if phase is None:
                raise CommandError(f"game '{game.id}' has no current phase; pass --phase to pick one")

        out = Path(options["out"])
        out.mkdir(parents=True, exist_ok=True)
        prefix = f"{game.id}_p{phase.ordinal}_{phase.season}{phase.year}"

        render_path = out / f"{prefix}_render.json"
        render_path.write_text(json.dumps(_render_state(phase), indent=2))
        self.stdout.write(f"wrote {render_path}")

        if current is None or phase.id != current.id:
            self.stdout.write("phase is not the current phase; order options unavailable, skipping fixture stubs")
            return

        for member in game.members.select_related("nation", "user"):
            if member.nation is None or member.user is None:
                continue
            api = ApiClient.for_user(member.user_id)
            try:
                data = fetch_context(api, game.id)
                fixture = data_to_fixture(
                    data,
                    fixture_id=f"{prefix}_{member.nation.name.lower()}",
                    notes=(
                        f"Harvested from game {game.id}, {phase.name}, {member.nation.name}. "
                        "Add ranked_options to encode the good/bad judgement."
                    ),
                )
            except (ApiClientError, FixtureError) as e:
                self.stderr.write(f"skip {member.nation.name}: {e}")
                continue
            fixture_path = out / f"{prefix}_{member.nation.name.lower()}.json"
            fixture_path.write_text(json.dumps(fixture, indent=2))
            self.stdout.write(f"wrote {fixture_path}")
