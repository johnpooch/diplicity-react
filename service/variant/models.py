from django.db import models

from game.models.base import BaseModel
from common.constants import PhaseStatus


class Variant(BaseModel):
    id = models.CharField(primary_key=True, max_length=36)
    name = models.CharField(max_length=100)
    description = models.TextField()
    author = models.CharField(max_length=200, blank=True)

    @property
    def nations(self):
        return [
            {
                "name": n.name,
                "color": n.color,
            }
            for n in self.nation_set.all()
        ]

    @property
    def provinces(self):
        return [
            {
                "id": p.province_id,
                "name": p.name,
                "type": p.type,
                "supply_center": p.supply_center,
            }
            for p in self.province_set.all()
        ]

    def get_province(self, province_id):
        try:
            province = self.province_set.get(province_id=province_id)
            return {
                "id": province.province_id,
                "name": province.name,
                "type": province.type,
                "supply_center": province.supply_center,
            }
        except self.province_set.model.DoesNotExist:
            return None

    def get_nation(self, nation_name):
        try:
            nation = self.nation_set.get(name=nation_name)
            return {
                "name": nation.name,
                "color": nation.color,
            }
        except self.nation_set.model.DoesNotExist:
            return None

    @property
    def template_phase(self):
        return self.phases.get(game=None, status=PhaseStatus.TEMPLATE)
