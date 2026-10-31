from django.db.models import Prefetch

from .actors import scoped


class Loader:
    queryset = None
    hydrators = ()
    nested = {}

    @classmethod
    def get_queryset(cls, actor):
        return scoped(cls.queryset.all(), actor).prefetch_related(
            *(
                Prefetch(lookup, queryset=loader.get_queryset(actor))
                for lookup, loader in cls.nested.items()
            )
        )

    @classmethod
    def hydrate(cls, instances, actor):
        instances = list(instances)
        for hydrator in cls.hydrators:
            hydrator.hydrate(instances, actor)
        for lookup, loader in cls.nested.items():
            loader.hydrate(
                [
                    child
                    for instance in instances
                    for child in getattr(instance, lookup).all()
                ],
                actor,
            )
        return instances

    @classmethod
    def get(cls, pk, actor):
        instances = cls.hydrate(cls.get_queryset(actor).filter(pk=pk), actor)
        return instances[0] if instances else None
