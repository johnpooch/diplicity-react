from common.loaders import Loader

from .hydrators import CanEditHydrator
from .models import Variant


class VariantLoader(Loader):
    queryset = Variant.objects.with_related_data()
    hydrators = [
        CanEditHydrator(),
    ]
