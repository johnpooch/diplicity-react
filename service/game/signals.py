from django.db.models.signals import post_save
from django.dispatch import receiver

from game.models import Game


@receiver(post_save, sender=Game)
def arm_game_muster(sender, instance, created, **kwargs):
    Game.objects.arm_muster(instance)
