from django.db import transaction


class Builder:
    def __init__(self, **fields):
        self.fields = fields

    def run(self):
        with transaction.atomic():
            return self.build()

    def build(self):
        raise NotImplementedError
