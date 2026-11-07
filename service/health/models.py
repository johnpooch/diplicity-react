from django.db import models


class RailwayMetricsCursor(models.Model):
    environment_id = models.CharField(max_length=36, primary_key=True)
    exported_until = models.DateTimeField()
