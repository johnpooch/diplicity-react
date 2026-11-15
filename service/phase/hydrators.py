from common.loaders import Hydrator
from province.models import Province

from .utils import compute_province_nations


class ProvinceNationsHydrator(Hydrator):
    def hydrate(self, phases, actor):
        for phase in phases:
            phase.province_nations = compute_province_nations(
                phase.supply_centers.all(),
                Province.objects.cached_for_variant(phase.variant),
                phase.variant.dominance_rules,
                phase.variant.nations.all(),
            )
