from common.constants import PhaseType

from harness.blocks._format import unit_label
from harness.types import ContextData, TaskContext


class GameStateBlock:
    def render(self, context: ContextData, task_ctx: TaskContext) -> str | None:
        phase = context["phase"]
        if not phase:
            return None

        lines = [f"Current phase: {phase['name']}"]

        units_by_nation: dict[str, list[str]] = {}
        for unit in sorted(phase.get("units", []), key=lambda u: u["province"]["id"]):
            label = unit_label(unit)
            if unit.get("dislodged"):
                label += " (dislodged)"
            units_by_nation.setdefault(unit["nation"]["name"], []).append(label)

        lines.append("Units:")
        for nation in sorted(units_by_nation):
            labels = units_by_nation[nation]
            lines.append(f"  {nation}: {len(labels)} ({', '.join(labels)})")

        centers_by_nation: dict[str, list[str]] = {}
        for center in phase.get("supply_centers", []):
            centers_by_nation.setdefault(center["nation"]["name"], []).append(
                center["province"]["id"]
            )

        lines.append("Supply centers:")
        for nation in sorted(centers_by_nation):
            provinces = sorted(centers_by_nation[nation])
            lines.append(f"  {nation}: {len(provinces)} ({', '.join(provinces)})")

        if phase.get("type") == PhaseType.RETREAT:
            lines.append("")
            lines.append(self._dislodged_units_line(phase))
        elif phase.get("type") == PhaseType.ADJUSTMENT:
            lines.append("")
            lines.extend(self._adjustments_lines(units_by_nation, centers_by_nation))

        return "\n".join(lines)

    def _dislodged_units_line(self, phase) -> str:
        dislodged = sorted(
            (unit for unit in phase.get("units", []) if unit.get("dislodged")),
            key=lambda u: u["province"]["id"],
        )
        if not dislodged:
            return "Dislodged units: none"
        entries = [f"{unit_label(unit)} ({unit['nation']['name']})" for unit in dislodged]
        return f"Dislodged units: {', '.join(entries)}"

    def _adjustments_lines(self, units_by_nation, centers_by_nation) -> list[str]:
        lines = ["Adjustments:"]
        for nation in sorted(set(units_by_nation) | set(centers_by_nation)):
            delta = len(centers_by_nation.get(nation, [])) - len(units_by_nation.get(nation, []))
            if delta > 0:
                summary = f"{delta} build{'s' if delta != 1 else ''} available"
            elif delta < 0:
                summary = f"{-delta} disband{'s' if delta != -1 else ''} required"
            else:
                summary = "no change"
            lines.append(f"  {nation}: {summary}")
        return lines
