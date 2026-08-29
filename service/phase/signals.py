import logging

from django.db.models.signals import post_save
from django.dispatch import receiver

from phase.models import Phase

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Phase)
def arm_phase_resolution(sender, instance, created, **kwargs):
    Phase.objects.arm_resolution(instance)
