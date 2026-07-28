import asyncio
import json
import os
from collections import Counter
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand

from inspect_ai.model import ChatMessageSystem, ChatMessageUser, get_model

from harness.adapter import fixture_to_context
from harness.exceptions import ParsingError
from harness.tasks.select_orders import parse_completion, system_prompt, user_prompt
from harness.tasks.select_orders.options import describe_option
from harness.tasks.select_orders.scorers.coherence import dangling

OPENINGS_DIR = Path(__file__).resolve().parents[2] / "tasks" / "select_orders" / "openings" / "s1901m"


def _unit_types(context):
    return {unit["province"]: ("A" if unit["type"] == "Army" else "F") for unit in context["units"]}


def _order_str(order, context, unit_types):
    prefix = unit_types.get(order["source"], "?")
    return f"{prefix} {order['source']} {describe_option(order, context)}"


def _flags(orders):
    sources = {order["source"] for order in orders}
    flags = [f"hold:{order['source']}" for order in orders if order["order_type"] == "Hold"]
    for order_type, own_label, foreign_label in (
        ("Support", "dangling_support", "support_foreign"),
        ("Convoy", "dangling_convoy", "convoy_foreign"),
    ):
        for aux, _target, _actual in dangling(orders, order_type):
            label = own_label if aux in sources else foreign_label
            flags.append(f"{label}:{aux}")
    return flags


def ledger_for_nation(context, completions):
    unit_types = _unit_types(context)
    joint = Counter()
    representative = {}
    marginals = {}
    unparseable = 0

    for completion in completions:
        try:
            orders = parse_completion(completion, context)
        except ParsingError:
            unparseable += 1
            continue
        key = tuple(sorted(_order_str(order, context, unit_types) for order in orders))
        joint[key] += 1
        representative.setdefault(key, orders)
        for order in orders:
            marginals.setdefault(order["source"], Counter())[_order_str(order, context, unit_types)] += 1

    scored = sum(joint.values())
    order_sets = [
        {
            "count": count,
            "share": round(count / scored, 3) if scored else 0.0,
            "orders": list(key),
            "flags": _flags(representative[key]),
        }
        for key, count in joint.most_common()
    ]
    unit_marginals = {
        source: [
            {"order": order, "count": count, "share": round(count / scored, 3) if scored else 0.0}
            for order, count in counts.most_common()
        ]
        for source, counts in marginals.items()
    }
    return {
        "samples": len(completions),
        "unparseable": unparseable,
        "order_sets": order_sets,
        "unit_marginals": unit_marginals,
    }


class Command(BaseCommand):
    help = (
        "Sample select_orders many times per nation on the fixed classical S1901M opening "
        "and write a ledger of the order distributions (with mechanical-blunder flags)."
    )

    def add_arguments(self, parser):
        parser.add_argument("--samples", type=int, default=50, help="samples per nation")
        parser.add_argument("--model", default=f"anthropic/{settings.BOT_LLM_MODEL}")
        parser.add_argument("--concurrency", type=int, default=8)
        parser.add_argument("--out", default="phase_dumps/opening_ledger.json")

    def handle(self, *args, **options):
        if not settings.BOT_ANTHROPIC_API_KEY:
            self.stdout.write("skip: BOT_ANTHROPIC_API_KEY is not set")
            return
        os.environ.setdefault("ANTHROPIC_API_KEY", settings.BOT_ANTHROPIC_API_KEY)

        fixtures = sorted(OPENINGS_DIR.glob("*.json"))
        if not fixtures:
            self.stderr.write(f"no opening fixtures in {OPENINGS_DIR}")
            return

        model = get_model(options["model"])
        nations = {}
        for path in fixtures:
            fixture = json.loads(path.read_text())
            context = fixture_to_context(fixture)
            completions = asyncio.run(
                self._sample(model, context, options["samples"], options["concurrency"])
            )
            nations[fixture["nation"]] = ledger_for_nation(context, completions)
            self.stdout.write(f"sampled {fixture['nation']}: {len(completions)} completion(s)")

        ledger = {
            "meta": {
                "position": "classical Spring 1901 Movement",
                "model": options["model"],
                "samples_per_nation": options["samples"],
                "persona": None,
            },
            "nations": nations,
        }
        out = Path(options["out"])
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(ledger, indent=2) + "\n")
        self.stdout.write(f"wrote {out}")

    async def _sample(self, model, context, samples, concurrency):
        system = system_prompt(context)
        user = user_prompt(context)
        semaphore = asyncio.Semaphore(concurrency)

        async def one():
            async with semaphore:
                output = await model.generate([ChatMessageSystem(content=system), ChatMessageUser(content=user)])
                return output.completion

        return await asyncio.gather(*[one() for _ in range(samples)])
