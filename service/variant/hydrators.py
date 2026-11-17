from common.constants import VariantStatus
from common.loaders import Hydrator


class CanEditHydrator(Hydrator):
    def hydrate(self, variants, actor):
        for variant in variants:
            variant.can_edit = (
                actor.pk is not None
                and variant.status == VariantStatus.DRAFT
                and variant.owner_id == actor.pk
            )
