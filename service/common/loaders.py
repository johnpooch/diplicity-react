from django.db.models import prefetch_related_objects


class Loader:
    queryset = None
    hydrators = ()

    def __init__(self, user):
        self.user = user

    def get_queryset(self):
        return type(self).queryset()

    def hydrate(self, instances):
        instances = list(instances)
        if self.user.is_authenticated:
            prefetch_related_objects([self.user], "profile")
        for hydrator in self.hydrators:
            hydrator(self.user).hydrate(instances)
        return instances

    def load(self, pk):
        return self.hydrate([self.get_queryset().get(pk=pk)])[0]
