import json
import os
import time

from django.db import models
from django.conf import settings

from .base import BaseModel


class Variant(BaseModel):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._cached_data = None

    def load_data(self):
        if self._cached_data is None:
            start_time = time.time()
            file_path = os.path.join(
                settings.BASE_DIR, "game", "data", "variants", f"{self.id}.json"
            )
            with open(file_path, "r") as file:
                self._cached_data = json.load(file)
            end_time = time.time()
            print(f"Variant {self.id} load_data took: {(end_time - start_time) * 1000:.2f}ms")
        return self._cached_data

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