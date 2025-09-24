from django.db import models


class SupplyCenter(models.Model):
    province = models.ForeignKey("province.Province", on_delete=models.CASCADE, related_name="supply_centers")
    nation = models.ForeignKey("nation.Nation", on_delete=models.CASCADE, related_name="supply_centers")
    phase = models.ForeignKey("game.Phase", on_delete=models.CASCADE, related_name="supply_centers")
