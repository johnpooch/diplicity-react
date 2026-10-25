import django_filters
from django.http import QueryDict


class FilterSet(django_filters.FilterSet):
    defaults = {}

    def __init__(self, data=None, *args, **kwargs):
        data = data.copy() if data is not None else QueryDict(mutable=True)
        for key, value in self.defaults.items():
            data.setdefault(key, value)
        super().__init__(data, *args, **kwargs)
