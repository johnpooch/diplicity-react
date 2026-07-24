import json
from pathlib import Path


from attr import dataclass
from typing import Literal, TypedDict, Callable
from inspect_ai import Task, task
from inspect_ai.dataset import Sample
from inspect_ai.scorer import scorer, accuracy, stderr, grouped, Score, Target, CORRECT, INCORRECT
from inspect_ai.solver import solver, TaskState, Generate, generate
from django.conf import settings
from inference.constants import InferenceProvider
from inference.models import Inference

from harness.evals.select_orders import base_context
from harness.orders import group_options_by_source, option_to_selected
from harness.tasks import SelectOrdersTask
from harness.types import TaskContext


CLASSICAL = json.loads(Path(__file__).with_name("classical.json").read_text())


Pass = Literal["army", "fleet", "both"]
UnitType = Literal["Army", "Fleet"]
ProvinceType = Literal["land", "sea", "coastal", "named_coast"]
PhaseType = Literal["Movement", "Retreat", "Adjustment"]

# An order predicate takes a resolved option dict and returns bool.
OrderPredicate = Callable[[dict], bool]


def move_to(province_id: str) -> OrderPredicate:
    return lambda o: (
        o["order_type"]["label"] == "Move" and o["target"]["id"] == province_id
    )


def order_type_is(label: str) -> OrderPredicate:
    return lambda o: o["order_type"]["label"] == label


def supports(aux_id: str, target_id: str) -> OrderPredicate:
    return lambda o: (
        o["order_type"]["label"] == "Support"
        and o["aux"]["id"] == aux_id
        and o["target"]["id"] == target_id
    )


def build_in(province_id: str) -> OrderPredicate:
    return lambda o: (
        o["order_type"]["label"] == "Build" and o["source"]["id"] == province_id
    )


class Adjacency(TypedDict):
    to: str
    pass_: Pass  # 'pass' is a keyword; alias on serialisation


class ProvinceData(TypedDict):
    id: str
    name: str
    type: ProvinceType
    supply_center: bool
    parent_id: str | None
    adjacencies: list[Adjacency]


class UnitData(TypedDict):
    type: UnitType
    nation: str
    province: str
    dislodged: bool


class SupplyCenterData(TypedDict):
    nation: str | None   # None = uncontrolled/neutral
    province: str


class PhaseData(TypedDict):
    season: str
    year: int
    type: PhaseType
    build_count: int   # +n builds, -n disbands, 0 otherwise


class ContextData(TypedDict):
    nation: str                       # who the bot is playing
    phase: PhaseData
    provinces: list[ProvinceData]
    units: list[UnitData]
    supply_centers: list[SupplyCenterData]
    order_options: list[dict]


@dataclass
class Prompt:
    user_content: str
    system: str


class ContextBuilder:
    def __init__(self, nation: str = "England"):
        self._nation = nation
        self._phase: PhaseData = {
            "season": "Spring", "year": 1901,
            "type": "Movement", "build_count": 0,
        }
        self._provinces: dict[str, ProvinceData] = {}
        self._units: list[UnitData] = []
        self._supply_centers: list[SupplyCenterData] = []
        self._options: list[dict] = []

    def from_variant(self, variant: dict) -> "ContextBuilder":
        """Load all provinces from a variant JSON blob. Replaces any
        provinces added so far; call before .province() overrides."""
        self._provinces = {
            p["id"]: {
                "id": p["id"],
                "name": p["name"],
                "type": p["type"],
                "supply_center": p["supplyCenter"],
                "parent_id": p["parentId"],
                "adjacencies": [
                    {"to": a["to"], "pass_": a["pass"]} for a in p["adjacencies"]
                ],
            }
            for p in variant["provinces"]
        }
        return self

    def phase(self, season, year, type_, build_count=0) -> "ContextBuilder":
        self._phase = {
            "season": season, "year": year,
            "type": type_, "build_count": build_count,
        }
        return self

    def province(
        self, id, name, type_="coastal",
        supply_center=False, adjacent_to: dict[str, Pass] | None = None,
    ) -> "ContextBuilder":
        self._provinces[id] = {
            "id": id, "name": name, "type": type_,
            "supply_center": supply_center, "parent_id": None,
            "adjacencies": [
                {"to": t, "pass_": p} for t, p in (adjacent_to or {}).items()
            ],
        }
        return self

    def unit(self, type_, province, nation=None, dislodged=False) -> "ContextBuilder":
        self._units.append({
            "type": type_, "nation": nation or self._nation,
            "province": province, "dislodged": dislodged,
        })
        return self

    def supply_center(self, province, nation=None) -> "ContextBuilder":
        self._supply_centers.append({"nation": nation, "province": province})
        return self

    def add_option(
        self,
        source: ProvinceData,
        order_type: str,
        target: ProvinceData | None = None,
        aux: ProvinceData | None = None,
        unit_type: str | None = None,
    ) -> "ContextBuilder":
        def field(value: ProvinceData | str | None):
            if isinstance(value, dict) and "id" in value and "name" in value:
                return {"id": value["id"], "label": value["name"]}
            return {"id": value, "label": value} if value is not None else None

        self._options.append(
            {
                "source": field(source),
                "order_type": field(order_type),
                "target": field(target),
                "aux": field(aux),
                "unit_type": field(unit_type),
            }
        )
        return self

    def validate(self):
        ids = set(self._provinces)
        problems = []
        for p in self._provinces.values():
            for adj in p["adjacencies"]:
                if adj["to"] not in ids:
                    problems.append(f"{p['id']} -> unknown {adj['to']}")
                else:
                    back = self._provinces[adj["to"]]["adjacencies"]
                    if not any(a["to"] == p["id"] for a in back):
                        problems.append(f"{p['id']}~{adj['to']} not symmetric")
        for u in self._units:
            if u["province"] not in ids:
                problems.append(f"unit on unknown {u['province']}")
        for c in self._supply_centers:
            if c["province"] not in ids:
                problems.append(f"supply center on unknown {c['province']}")
            elif not self._provinces[c["province"]]["supply_center"]:
                problems.append(f"{c['province']} listed as supply center but flag is False")
        for o in self._options:
            for key in ("source", "target", "aux"):
                f = o.get(key)
                if f and f["id"] not in ids:
                    problems.append(f"option {key} unknown {f['id']}")
        if problems:
            raise ValueError("invalid fixture:\n  " + "\n  ".join(problems))

    def build(self) -> ContextData:
        self.validate()

        declared = {c["province"] for c in self._supply_centers}
        supply_centers = self._supply_centers + [
            {"nation": None, "province": pid}
            for pid, p in self._provinces.items()
            if p["supply_center"] and pid not in declared
        ]
        return {
            "nation": self._nation,
            "phase": self._phase,
            "provinces": list(self._provinces.values()),
            "units": self._units,
            "supply_centers": supply_centers,
            "order_options": self._options,
        }


def build_prompt(context: ContextData) -> Prompt:
    parts = []

    # Nation and phase
    parts.append(f"You are playing as {context['nation']}.")
    parts.append(f"The current phase is {context['phase']['season']} {context['phase']['year']}, {context['phase']['type']}.")

    # Adjustment available orders
    if context['phase']['type'] == "Adjustment":
        n = context['phase']['build_count']
        parts.append(f"You may submit {n} order(s).")

    by_id = {p["id"]: p for p in context["provinces"]}

    if context["provinces"]:

        # Explain adjacencies
        parts.append("\nProvinces (adjacency: A=army only, F=fleet only, AF=both):")

        # Provinces
        for p in context["provinces"]:
            sc = " [supply centre]" if p["supply_center"] else ""
            adj = ", ".join(
                f"{by_id[a['to']]['name']}"
                f"({ {'army':'A','fleet':'F','both':'AF'}[a['pass_']] })"
                for a in p["adjacencies"]
            )
            parts.append(f"  {p['name']} ({p['id']}, {p['type']}){sc} -> {adj}")

    # Units
    if context["units"]:
        parts.append("\nUnits on the board:")
        for u in context["units"]:
            mine = " [yours]" if u["nation"] == context["nation"] else ""
            dis = " [DISLODGED]" if u["dislodged"] else ""
            parts.append(
                f"  {u['type']} {by_id[u['province']]['name']} — {u['nation']}{mine}{dis}"
            )

    # Supply centers
    if context["supply_centers"]:
        parts.append("\nSupply centres:")
        for c in context["supply_centers"]:
            owner = c["nation"] or "UNCONTROLLED"
            mine = " [yours]" if c["nation"] == context["nation"] else ""
            parts.append(f"  {by_id[c['province']]['name']} — {owner}{mine}")

    
    parts.append("\nAvailable order options:")

    for index, option in enumerate(context["order_options"]):
        line = f"{index}. "

        source_label = option.get("source", {}).get("label", "unknown")
        order_type_label = option.get("order_type", {}).get("label", "unknown")
        line += f"Source: {source_label}, Order Type: {order_type_label}"
        if option.get("target"):
            line += f", Target: {option.get("target", {}).get("label", "unknown")}"
        if option.get("aux"):
            line += f", Aux: {option.get("aux", {}).get("label", "unknown")}"
        if option.get("unit_type"):
            line += f", Unit Type: {option.get("unit_type", {}).get("label", "unknown")}"
        parts.append(line)

    header = (
        "Return JSON only, no fences. Start with '{' and use this shape: "
        '{"selected":[<index1>,<index2>...]}\n'
    )
    user_content = header + "\n".join(parts)
    
    return Prompt(user_content=user_content, system="You are a helpful assistant.")


def make_sample(context: ContextData, rung: int) -> Sample:
    prompt = build_prompt(context)
    return Sample(
        input=prompt.user_content,
        metadata={
            "context": context,
            "system": prompt.system,
            "rung": rung,
        },
    )


@dataclass
class Tactic:
    strong: list[OrderPredicate]
    forbidden: list[OrderPredicate]
    note: str  # why this is unambiguous — read this when a fixture goes red


TACTICS: dict[str, Tactic] = {}


def make_tactical_sample(context: ContextData, scenario: str, tactic: Tactic, rung: int) -> Sample:
    TACTICS[scenario] = tactic
    prompt = build_prompt(context)
    return Sample(
        input=prompt.user_content,
        metadata={
            "context": context,
            "system": prompt.system,
            "scenario": scenario,
            "rung": rung,
        },
    )


def _parse_selected(state) -> tuple[list | None, str | None]:
    """Return (selected, error). selected is a list of indices, or None on failure."""
    raw = state.output.completion.strip()
    if raw.startswith("```"):
        # drop opening fence (```json or ```) and closing fence
        raw = raw.split("\n", 1)[-1] if "\n" in raw else raw
        raw = raw.rsplit("```", 1)[0]
        raw = raw.strip()
    try:
        result = json.loads(raw)
    except json.JSONDecodeError as e:
        return None, f"invalid JSON: {e}"
    selected = result.get("selected")
    if not isinstance(selected, list):
        return None, f"expected a list under 'selected', got: {selected!r}"
    return selected, None


@scorer(metrics=[grouped(accuracy(), "rung"), grouped(stderr(), "rung")])
def legality():
    async def score(state, target: Target) -> Score:
        selected, error = _parse_selected(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion, explanation=error)

        options = state.metadata["context"]["order_options"]
        n = len(options)
        out_of_range = [i for i in selected if not isinstance(i, int) or i < 0 or i >= n]
        legal = len(out_of_range) == 0

        return Score(
            value=CORRECT if legal else INCORRECT,
            answer=state.output.completion,
            explanation=f"selected {selected}, {n} options available"
            + (f", out of range: {out_of_range}" if out_of_range else ""),
        )

    return score

@scorer(metrics=[grouped(accuracy(), "rung"), grouped(stderr(), "rung")])
def deduplication():
    async def score(state, target: Target) -> Score:
        selected, error = _parse_selected(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion, explanation=error)

        options = state.metadata["context"]["order_options"]
        # Resolve each in-range index to its source province id.
        # Out-of-range indices are legality's job, not dedup's — skip them here.
        source_ids = [
            options[i]["source"]["id"]
            for i in selected
            if isinstance(i, int) and 0 <= i < len(options)
        ]
        duplicates = [sid for sid in set(source_ids) if source_ids.count(sid) > 1]
        deduped = len(duplicates) == 0

        return Score(
            value=CORRECT if deduped else INCORRECT,
            answer=state.output.completion,
            explanation=f"provinces ordered: {source_ids}"
            + (f", duplicated: {duplicates}" if duplicates else ""),
        )

    return score


@scorer(metrics=[grouped(accuracy(), "rung"), grouped(stderr(), "rung")])
def coverage():
    async def score(state, target: Target) -> Score:
        selected, error = _parse_selected(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion, explanation=error)

        options = state.metadata["context"]["order_options"]
        all_provinces = {opt["source"]["id"] for opt in options}
        covered = {
            options[i]["source"]["id"]
            for i in selected
            if isinstance(i, int) and 0 <= i < len(options)
        }
        missing = all_provinces - covered
        complete = len(missing) == 0

        return Score(
            value=CORRECT if complete else INCORRECT,
            answer=state.output.completion,
            explanation=f"covered {len(covered)}/{len(all_provinces)} provinces"
            + (f", missing: {sorted(missing)}" if missing else ""),
        )

    return score


@scorer(metrics=[accuracy(), stderr()])
def support_coherence():
    async def score(state, target: Target) -> Score:
        selected, error = _parse_selected(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion, explanation=error)

        options = state.metadata["context"]["order_options"]
        in_range = [
            options[i] for i in selected
            if isinstance(i, int) and 0 <= i < len(options)
        ]

        # Where does each source province's selected unit end up?
        #   a Move records its target province id; anything else (Hold,
        #   Support, Convoy) keeps the unit on its own source province.
        # If a province isn't selected at all it has no destination -> None.
        destination = {}
        for opt in in_range:
            src = opt["source"]["id"]
            if opt["order_type"]["label"] == "Move":
                destination[src] = opt["target"]["id"]
            else:
                destination[src] = src

        dangling = []
        for opt in in_range:
            if opt["order_type"]["label"] != "Support":
                continue
            aux = opt["aux"]["id"]
            tgt = opt["target"]["id"]
            # Coherent iff the supported unit actually ends up on tgt.
            # aux not selected -> destination.get(aux) is None -> dangles.
            if destination.get(aux) != tgt:
                dangling.append((aux, tgt, destination.get(aux)))

        coherent = len(dangling) == 0
        return Score(
            value=CORRECT if coherent else INCORRECT,
            answer=state.output.completion,
            explanation="all supports coherent" if coherent
            else "dangling supports (aux, target, aux_actual_dest): " + str(dangling),
        )

    return score


@scorer(metrics=[accuracy(), stderr()])
def convoy_coherence():
    async def score(state, target: Target) -> Score:
        selected, error = _parse_selected(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion, explanation=error)

        options = state.metadata["context"]["order_options"]
        in_range = [
            options[i] for i in selected
            if isinstance(i, int) and 0 <= i < len(options)
        ]

        # Same destination map as support_coherence: where does each source
        # province's selected unit end up? A Move records its target; anything
        # else keeps the unit on its own province; unselected -> None.
        destination = {}
        for opt in in_range:
            src = opt["source"]["id"]
            if opt["order_type"]["label"] == "Move":
                destination[src] = opt["target"]["id"]
            else:
                destination[src] = src

        # A Convoy names the convoyed army as aux and its destination as target.
        # Coherent iff that army actually moves to that destination.
        dangling = []
        for opt in in_range:
            if opt["order_type"]["label"] != "Convoy":
                continue
            army = opt["aux"]["id"]
            tgt = opt["target"]["id"]
            if destination.get(army) != tgt:
                dangling.append((army, tgt, destination.get(army)))

        coherent = len(dangling) == 0
        return Score(
            value=CORRECT if coherent else INCORRECT,
            answer=state.output.completion,
            explanation="all convoys coherent" if coherent
            else "dangling convoys (army, target, army_actual_dest): " + str(dangling),
        )

    return score


def _resolved(state) -> tuple[list[dict] | None, str | None]:
    selected, error = _parse_selected(state)
    if error:
        return None, error
    options = state.metadata["context"]["order_options"]
    return [
        options[i] for i in selected
        if isinstance(i, int) and 0 <= i < len(options)
    ], None


@scorer(metrics=[grouped(accuracy(), "scenario"), grouped(stderr(), "scenario")])
def tactical_strong():
    """Did the model find at least one clearly-good order?"""
    async def score(state, target: Target) -> Score:
        orders, error = _resolved(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion,
                         explanation=error)

        tactic = TACTICS[state.metadata["scenario"]]
        found = [o for o in orders if any(p(o) for p in tactic.strong)]

        return Score(
            value=CORRECT if found else INCORRECT,
            answer=state.output.completion,
            explanation=(
                f"found strong order(s): {[_describe(o) for o in found]}"
                if found else
                f"no strong order; selected {[_describe(o) for o in orders]}"
            ),
        )
    return score


@scorer(metrics=[grouped(accuracy(), "scenario"), grouped(stderr(), "scenario")])
def tactical_avoidance():
    """Did the model stay out of the clearly-bad orders?"""
    async def score(state, target: Target) -> Score:
        orders, error = _resolved(state)
        if error:
            return Score(value=INCORRECT, answer=state.output.completion,
                         explanation=error)

        tactic = TACTICS[state.metadata["scenario"]]
        hit = [o for o in orders if any(p(o) for p in tactic.forbidden)]

        return Score(
            value=INCORRECT if hit else CORRECT,
            answer=state.output.completion,
            explanation=(
                f"selected forbidden: {[_describe(o) for o in hit]}"
                if hit else "avoided all forbidden orders"
            ),
        )
    return score


def _describe(o: dict) -> str:
    s = f"{o['source']['label']} {o['order_type']['label']}"
    if o.get("aux"):
        s += f" {o['aux']['label']}"
    if o.get("target"):
        s += f" -> {o['target']['label']}"
    return s


def P(id: str, name: str) -> dict:
    return {"id": id, "name": name}


@task
def select_orders_structure():
    return Task(
        dataset=[
            # --- Rung 1: trivial baseline -------------------------------
            # One province, one option. The control. A competent model
            # cannot fail this on structure; a red here means parsing or
            # prompting is broken, not judgment.
            make_sample(
                ContextBuilder()
                .from_variant(CLASSICAL)
                .add_option(source=ProvinceData(id="lon", name="London"), order_type="Hold")
                .build(),
                rung=1
            ),

            # --- Rung 2: basic structure --------------------------------
            # Three provinces, two options each, in reading order. First
            # fixture where dedup and coverage are nominally in play, but
            # the path of least resistance ([0,2,4]) already passes all
            # three, so green here is weak evidence.
            make_sample(
                ContextBuilder(nation="England")
                .from_variant(CLASSICAL)
                .add_option(source=ProvinceData(id="lon", name="London"), order_type="Hold")
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Move", target=ProvinceData(id="eng", name="English Channel"))
                .add_option(source=ProvinceData(id="par", name="Paris"), order_type="Hold")
                .add_option(source=ProvinceData(id="par", name="Paris"),
                            order_type="Move", target=ProvinceData(id="bur", name="Burgundy"))
                .add_option(source=ProvinceData(id="ber", name="Berlin"), order_type="Hold")
                .add_option(source=ProvinceData(id="ber", name="Berlin"),
                            order_type="Move", target=ProvinceData(id="kie", name="Kiel"))
                .build(),
                rung=2
            ),

            # --- Rung 3: scale pressure on coverage ---------------------
            # Six provinces, two options each. "Pick one from each" is now
            # real work; omission becomes a plausible slip. First fixture
            # where a green COVERAGE score carries weight -- the model had
            # room to drop a province and didn't.
            make_sample(
                ContextBuilder(nation="England")
                .from_variant(CLASSICAL)
                .add_option(source=ProvinceData(id="lon", name="London"), order_type="Hold")
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Move", target=ProvinceData(id="eng", name="English Channel"))
                .add_option(source=ProvinceData(id="par", name="Paris"), order_type="Hold")
                .add_option(source=ProvinceData(id="par", name="Paris"),
                            order_type="Move", target=ProvinceData(id="bur", name="Burgundy"))
                .add_option(source=ProvinceData(id="ber", name="Berlin"), order_type="Hold")
                .add_option(source=ProvinceData(id="ber", name="Berlin"),
                            order_type="Move", target=ProvinceData(id="kie", name="Kiel"))
                .add_option(source=ProvinceData(id="rom", name="Rome"), order_type="Hold")
                .add_option(source=ProvinceData(id="rom", name="Rome"),
                            order_type="Move", target=ProvinceData(id="ven", name="Venice"))
                .add_option(source=ProvinceData(id="vie", name="Vienna"), order_type="Hold")
                .add_option(source=ProvinceData(id="vie", name="Vienna"),
                            order_type="Move", target=ProvinceData(id="bud", name="Budapest"))
                .add_option(source=ProvinceData(id="mos", name="Moscow"), order_type="Hold")
                .add_option(source=ProvinceData(id="mos", name="Moscow"),
                            order_type="Move", target=ProvinceData(id="ukr", name="Ukraine"))
                .build(),
                rung=3
            ),

            # --- Rung 4: adversarial / lopsided -------------------------
            # London has four attractive options listed FIRST; Paris has a
            # single dull Hold listed LAST. This tempts over-investment in
            # London and omission of Paris -- the "two orders for London,
            # none for Paris" failure that fails dedup AND coverage
            # together. The fixture most likely to actually go red, which
            # is why it's the most valuable one in the suite.
            # Predicted: legality PASS; dedup and coverage are the live
            # question. If the model picks e.g. [0,1] it fails both.
            make_sample(
                ContextBuilder(nation="England")
                .from_variant(CLASSICAL)
                .add_option(source=ProvinceData(id="lon", name="London"), order_type="Hold")
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Move", target=ProvinceData(id="eng", name="English Channel"))
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Move", target=ProvinceData(id="wal", name="Wales"))
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Support", aux=ProvinceData(id="wal", name="Wales"),
                            target=ProvinceData(id="lvp", name="Liverpool"))
                .add_option(source=ProvinceData(id="par", name="Paris"), order_type="Hold")
                .build(),
                rung=4
            ),
        ],
        solver=generate(),
        scorer=[legality(), deduplication(), coverage()],
    )


@task
def select_orders_coherence():
    return Task(
        dataset=[
            # Support-coherence fixture. One province pair expressing
            # support-MOVE and support-HOLD, each coherent and dangling:
            #   0  London Move -> Liverpool
            #   1  London Hold
            #   2  Wales  Support London -> Liverpool   (support-move)
            #   3  Wales  Support London -> London      (support-hold)
            #   4  Wales  Hold
            # Baseline support_coherence ~0.87 (Haiku 4.5, 100 epochs). ALL failures are
            # the single pattern [1,2(,4)]: London Hold + Wales Support London->Liverpool
            # -- a support attached to a move the model didn't commit. The opposite
            # incoherence ([0,3]: move London but support-HOLD it) was never observed.
            # A drop signals more decoupled-support selection; a rise toward 1.0 signals
            # either improvement or that added context is suppressing the temptation --
            # read completions to tell which. Failure shape, not just the number, is the
            # regression signal here.
            make_sample(
                ContextBuilder(nation="England")
                .from_variant(CLASSICAL)
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Move", target=ProvinceData(id="lvp", name="Liverpool"))
                .add_option(source=ProvinceData(id="lon", name="London"), order_type="Hold")
                .add_option(source=ProvinceData(id="wal", name="Wales"),
                            order_type="Support", aux=ProvinceData(id="lon", name="London"),
                            target=ProvinceData(id="lvp", name="Liverpool"))
                .add_option(source=ProvinceData(id="wal", name="Wales"),
                            order_type="Support", aux=ProvinceData(id="lon", name="London"),
                            target=ProvinceData(id="lon", name="London"))
                .add_option(source=ProvinceData(id="wal", name="Wales"), order_type="Hold")
                .build(),
                rung=5,
            ),
            # Convoy-coherence fixture. A fleet convoys an army across water;
            # coherent iff the army actually makes the convoyed move.
            #   0  Fleet English Channel Convoy London -> Brest
            #   1  Fleet English Channel Hold
            #   2  London Move -> Brest        (the convoyed move)
            #   3  London Hold                 (army stays; convoy dangles)
            # Coherent path: [0,2]. Dangling: [0,3] (convoy an army that holds).
            make_sample(
                ContextBuilder(nation="England")
                .from_variant(CLASSICAL)
                .add_option(source=ProvinceData(id="eng", name="English Channel"),
                            order_type="Convoy", aux=ProvinceData(id="lon", name="London"),
                            target=ProvinceData(id="bre", name="Brest"))
                .add_option(source=ProvinceData(id="eng", name="English Channel"), order_type="Hold")
                .add_option(source=ProvinceData(id="lon", name="London"),
                            order_type="Move", target=ProvinceData(id="bre", name="Brest"))
                .add_option(source=ProvinceData(id="lon", name="London"), order_type="Hold")
                .build(),
                rung=6,
            ),
        ],
        solver=generate(),
        scorer=[support_coherence(), convoy_coherence()],
    )

@task
def select_orders_tactics():
    return Task(
        dataset=[
            # --- T1: fall retreat into an uncontrolled supply centre -----
            # Austrian A Trieste is dislodged. It can retreat to Albania
            # (neutral, no SC) or Serbia (neutral SC, unoccupied), or
            # disband. Fall retreats resolve before adjustment, so Serbia
            # counts for the build this year.
            # Unambiguous because: the unit is already displaced, so there
            # is no opportunity cost; Serbia is unoccupied and no other
            # power has a unit adjacent to it in this fixture, so it isn't
            # obviously recaptured; disbanding forfeits a unit for nothing.
            make_tactical_sample(
                ContextBuilder(nation="Austria")
                .from_variant(CLASSICAL)
                .phase("Fall", 1902, "Retreat")
                .unit("Army", "tri", dislodged=True)
                .unit("Army", "vie")
                .unit("Army", "bud")
                .unit("Army", "tri", nation="Italy")   # the dislodger
                .supply_center("vie", nation="Austria")
                .supply_center("bud", nation="Austria")
                .supply_center("tri", nation="Italy")
                .add_option(source=P("tri", "Trieste"), order_type="Retreat",
                            target=P("ser", "Serbia"))
                .add_option(source=P("tri", "Trieste"), order_type="Retreat",
                            target=P("alb", "Albania"))
                .add_option(source=P("tri", "Trieste"), order_type="Disband")
                .build(),
                scenario="retreat_to_sc",
                tactic=Tactic(
                    strong=[move_to("ser")],
                    forbidden=[order_type_is("Disband"), move_to("alb")],
                    note="Serbia is a neutral SC; Albania is not; disband "
                         "forfeits the unit. Retreat has no opportunity cost.",
                ),
                rung=7,
            ),

            # --- T2: fall movement, take the neutral centre --------------
            # English F North Sea can take Norway (neutral SC, unoccupied,
            # no adjacent rival) or sit in Skagerrak / hold.
            # Unambiguous because: North Sea is not itself an SC and is not
            # under threat, so the fleet defends nothing by staying;
            # Skagerrak leads nowhere better; Norway is uncontested.
            make_tactical_sample(
                ContextBuilder(nation="England")
                .from_variant(CLASSICAL)
                .phase("Fall", 1901, "Movement")
                .unit("Fleet", "nth")
                .unit("Fleet", "lon")
                .unit("Army", "yor")
                .supply_center("lon", nation="England")
                .supply_center("edi", nation="England")
                .supply_center("lvp", nation="England")
                .add_option(source=P("nth", "North Sea"), order_type="Move",
                            target=P("nwy", "Norway"))
                .add_option(source=P("nth", "North Sea"), order_type="Move",
                            target=P("ska", "Skagerrak (SKA)"))
                .add_option(source=P("nth", "North Sea"), order_type="Hold")
                .add_option(source=P("lon", "London"), order_type="Hold")
                .add_option(source=P("yor", "Yorkshire"), order_type="Hold")
                .build(),
                scenario="take_neutral_sc",
                tactic=Tactic(
                    strong=[move_to("nwy")],
                    forbidden=[move_to("ska")],
                    note="Norway is a neutral SC and uncontested. North Sea "
                         "is not an SC and defends nothing. Hold is weak but "
                         "not forbidden — only Skagerrak is strictly wasted.",
                ),
                rung=8,
            ),

            # --- T3: support-hold a threatened centre --------------------
            # German A Munich is attacked by two French units (A Burgundy,
            # A Ruhr is German-held so the threat is Bur + Tyr). A Kiel can
            # support Munich to hold. Unsupported, Munich falls to a
            # 2-against-1; supported it survives.
            # Unambiguous because: Kiel is not itself threatened, has no
            # better use, and losing Munich costs a home centre.
            # This is the only fixture testing coordination rather than
            # single-unit greed.
            make_tactical_sample(
                ContextBuilder(nation="Germany")
                .from_variant(CLASSICAL)
                .phase("Fall", 1903, "Movement")
                .unit("Army", "mun")
                .unit("Army", "kie")
                .unit("Army", "bur", nation="France")
                .unit("Army", "tyr", nation="France")
                .supply_center("mun", nation="Germany")
                .supply_center("kie", nation="Germany")
                .supply_center("ber", nation="Germany")
                .add_option(source=P("kie", "Kiel"), order_type="Support",
                            aux=P("mun", "Munich"), target=P("mun", "Munich"))
                .add_option(source=P("kie", "Kiel"), order_type="Hold")
                .add_option(source=P("kie", "Kiel"), order_type="Move",
                            target=P("hol", "Holland"))
                .add_option(source=P("mun", "Munich"), order_type="Hold")
                .add_option(source=P("mun", "Munich"), order_type="Move",
                            target=P("ruh", "Ruhr"))
                .build(),
                scenario="support_hold_threatened_sc",
                tactic=Tactic(
                    strong=[supports("mun", "mun")],
                    forbidden=[move_to("ruh")],  # vacating the threatened SC
                    note="Munich faces two attackers and falls without "
                         "support. Kiel has no competing use. Vacating "
                         "Munich hands over a home centre.",
                ),
                rung=9,
            ),

            # --- T4: adjustment, build toward the open centre ------------
            # Russia has one build. Warsaw is adjacent to nothing
            # uncontrolled; Sevastopol is adjacent to Rumania (neutral SC,
            # unoccupied). Both builds are armies, so unit type is not a
            # confound.
            # Weakest of the four — build-site value is genuinely contested
            # in real play. Made unambiguous here by giving Warsaw no
            # adjacent threat to defend against and no path to anything.
            make_tactical_sample(
                ContextBuilder(nation="Russia")
                .from_variant(CLASSICAL)
                .phase("Winter", 1901, "Adjustment", build_count=1)
                .unit("Army", "mos")
                .unit("Army", "ukr")
                .supply_center("mos", nation="Russia")
                .supply_center("war", nation="Russia")
                .supply_center("sev", nation="Russia")
                .supply_center("stp", nation="Russia")
                .add_option(source=P("sev", "Sevastopol"), order_type="Build",
                            unit_type="Army")
                .add_option(source=P("war", "Warsaw"), order_type="Build",
                            unit_type="Army")
                .build(),
                scenario="build_toward_open_sc",
                tactic=Tactic(
                    strong=[build_in("sev")],
                    forbidden=[build_in("war")],
                    note="Sevastopol is adjacent to Rumania, a neutral SC. "
                         "Warsaw has no adjacent uncontrolled centre and no "
                         "threat to defend against.",
                ),
                rung=10,
            ),
        ],
        solver=generate(),
        scorer=[tactical_strong(), tactical_avoidance(),
                legality(), deduplication(), coverage()],
    )
    