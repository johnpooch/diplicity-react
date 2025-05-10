import json
import os

from django.db import models
from django.conf import settings

from .base import BaseModel


class Variant(BaseModel):
    id = models.CharField(primary_key=True)
    name = models.CharField(max_length=100)

    def load_data(self):
        file_path = os.path.join(
            settings.BASE_DIR, "game", "data", "variants", f"{self.id}.json"
        )
        with open(file_path, "r") as file:
            data = json.load(file)
        return data

    @property
    def nations(self):
        data = self.load_data()
        return data["nations"]

    @property
    def start(self):
        data = self.load_data()
        return data["start"]

    @property
    def description(self):
        data = self.load_data()
        return data["description"]

    @property
    def author(self):
        data = self.load_data()
        return data["author"]

    @property
    def provinces(self):
        data = self.load_data()
        return data["provinces"]
