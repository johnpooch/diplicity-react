from common.loaders import Hydrator
from member.loaders import MemberLoader
from province.models import Province

from .utils import compute_province_nations


class PhaseStateMemberHydrator(Hydrator):
    def hydrate(self, phase_states, actor):
        MemberLoader.hydrate([phase_state.member for phase_state in phase_states], actor)


class ProvinceNationsHydrator(Hydrator):
    def hydrate(self, phases, actor):
        for phase in phases:
            phase.province_nations = compute_province_nations(
                phase.supply_centers.all(),
                Province.objects.cached_for_variant(phase.variant),
                phase.variant.dominance_rules,
                phase.variant.nations.all(),
            )
