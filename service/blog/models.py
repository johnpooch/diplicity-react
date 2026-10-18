from django.db import models

from common.models import BaseModel


class BlogPost(BaseModel):
    slug = models.SlugField(max_length=100, unique=True)
    title = models.CharField(max_length=200)
    summary = models.CharField(max_length=500)
    body = models.TextField()

    class Meta:
        ordering = ["-created_at"]
