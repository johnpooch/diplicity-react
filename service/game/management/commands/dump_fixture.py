import hashlib
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from game.models import Game
from victory.models import Victory

SCHEMA_VERSION = 1


def _hash_id(raw):
    return hashlib.sha256(str(raw).encode()).hexdigest()[:12]


def _units_for_phase(phase):
    payload = [
        {
            "nation": u.nation.name,
            "type": u.type,
            "province": u.province.province_id,
            "dislodged": u.dislodged,
        }
        for u in phase.units.all()
    ]
    payload.sort(key=lambda u: (u["nation"], u["province"], u["type"]))
    return payload


def _supply_centers_for_phase(phase):
    pairs = sorted(
        (sc.province.province_id, sc.nation.name)
        for sc in phase.supply_centers.all()
    )
    return dict(pairs)


def _state_after(next_phase):
    if next_phase is None:
        return None
    return {
        "units": _units_for_phase(next_phase),
        "supply_centers": _supply_centers_for_phase(next_phase),
    }


def _resolution_trigger(phase, is_last_phase, game_has_victory):
    if is_last_phase and game_has_victory:
        return "terminal", []
    with_orders = [ps for ps in phase.phase_states.all() if ps.has_possible_orders]
    if not with_orders:
        return "auto", []
    non_confirming = sorted(
        ps.member.nation.name for ps in with_orders if not ps.orders_confirmed
    )
    if non_confirming:
        return "deadline", non_confirming
    return "consensus", []


def _orders_for_phase(phase):
    rows = []
    for phase_state in phase.phase_states.all():
        if phase_state.member.nation is None:
            continue
        nation_name = phase_state.member.nation.name
        for order in phase_state.orders.all():
            resolution = getattr(order, "resolution", None)
            rows.append({
                "nation": nation_name,
                "selected": order.selected,
                "expected_resolution": resolution.status if resolution else None,
            })
    rows.sort(key=lambda o: (o["nation"], tuple(o["selected"])))
    return rows


def _phase_to_dict(phase, next_phase, is_last_phase, game_has_victory):
    orders = _orders_for_phase(phase)
    trigger, non_confirming = _resolution_trigger(phase, is_last_phase, game_has_victory)
    return {
        "ordinal": phase.ordinal,
        "season": phase.season,
        "year": phase.year,
        "type": phase.type,
        "resolution_trigger": trigger,
        "non_confirming_nations": non_confirming,
        "orders": orders,
        "expected_state_after": _state_after(next_phase),
    }


def _outcome(game):
    victory = Victory.objects.filter(game=game).select_related("winning_phase").first()
    if victory is None:
        return None
    winners = sorted(m.nation.name for m in victory.members.select_related("nation").all())
    return {
        "type": victory.type,
        "winners": winners,
        "winning_phase_ordinal": victory.winning_phase.ordinal,
    }


class Command(BaseCommand):
    help = "Dump a game from the database to a JSON regression fixture."

    def add_arguments(self, parser):
        parser.add_argument("game_id", help="Game.id (e.g. the slug-like primary key).")
        parser.add_argument(
            "--out",
            default=None,
            help=(
                "Output path, e.g. service/integration/fixtures/01_classical_solo_short.json. "
                "If omitted, the JSON is written to stdout (use this when running via `railway ssh`)."
            ),
        )

    def handle(self, *args, game_id, out, **opts):
        game = (
            Game.objects.select_related("variant")
            .filter(id=game_id)
            .first()
        )
        if game is None:
            raise CommandError(f"Game {game_id!r} not found")

        phases = list(
            game.phases.prefetch_related(
                "units__nation",
                "units__province",
                "supply_centers__nation",
                "supply_centers__province",
                "phase_states__member__nation",
                "phase_states__orders__source",
                "phase_states__orders__target",
                "phase_states__orders__aux",
                "phase_states__orders__named_coast",
                "phase_states__orders__resolution",
            ).order_by("ordinal")
        )

        outcome = _outcome(game)
        game_has_victory = outcome is not None

        phases_payload = [
            _phase_to_dict(
                phase,
                phases[i + 1] if i + 1 < len(phases) else None,
                is_last_phase=(i == len(phases) - 1),
                game_has_victory=game_has_victory,
            )
            for i, phase in enumerate(phases)
        ]

        last_phase = phases[-1] if phases else None
        document = {
            "schema_version": SCHEMA_VERSION,
            "source": {
                "original_game_id_hash": _hash_id(game.id),
                "captured_at": timezone.now().isoformat(),
                "captured_from": "database",
                "game_created_at": game.created_at.isoformat() if game.created_at else None,
                "last_phase_completed_at": (
                    last_phase.completed_at.isoformat()
                    if last_phase and last_phase.completed_at
                    else None
                ),
            },
            "variant": game.variant.name,
            "outcome": outcome,
            "phases": phases_payload,
        }

        rendered = json.dumps(document, indent=2) + "\n"
        if out is None:
            self.stdout.write(rendered, ending="")
        else:
            out_path = Path(out)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(rendered)
            self.stderr.write(f"Wrote {out_path} ({len(phases)} phases)")
