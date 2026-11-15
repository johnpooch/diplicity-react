from common.loaders import Loader

from .hydrators import ProvinceNationsHydrator
from .models import Phase


class PhaseRetrieveLoader(Loader):
    queryset = Phase.objects.with_retrieve_data()
    hydrators = [
        ProvinceNationsHydrator(),
    ]
