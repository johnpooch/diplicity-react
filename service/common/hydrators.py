class Hydrator:
    attribute = None
    default = None

    def __init__(self, user):
        self.user = user

    def hydrate(self, instances):
        values = self.values(instances) if instances else {}
        for instance in instances:
            setattr(instance, self.attribute, values.get(instance.pk, self.default))

    def values(self, instances):
        raise NotImplementedError
