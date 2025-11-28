import logging
from django.db import models
from django.db.models import Count
from common.models import BaseModel
from common.constants import PhaseType, PhaseStatus, GameStatus
from victory.constants import VictoryType
from victory.utils import check_for_solo_winner

logger = logging.getLogger(__name__)


class VictoryQuerySet(models.QuerySet):
    def solo_victories(self):
        return self.annotate(member_count=Count('members')).filter(member_count=1)

    def draw_victories(self):
        return self.annotate(member_count=Count('members')).filter(member_count__gte=2)


class VictoryManager(models.Manager):
    def get_queryset(self):
        return VictoryQuerySet(self.model, using=self._db)

    def solo_victories(self):
        return self.get_queryset().solo_victories()

    def draw_victories(self):
        return self.get_queryset().draw_victories()

    def try_create_victory(self, phase):
        if phase.type != PhaseType.ADJUSTMENT:
            return None

        winner = check_for_solo_winner(phase.game, phase)

        if not winner:
            return None

        logger.info(f"Solo victory detected for member {winner.id} in game {phase.game.id}")

        victory = self.create(
            game=phase.game,
            winning_phase=phase
        )
        victory.members.add(winner)

        return victory


class Victory(BaseModel):
    objects = VictoryManager()

    game = models.OneToOneField("game.Game", related_name="victory", on_delete=models.CASCADE)
    winning_phase = models.ForeignKey("phase.Phase", on_delete=models.CASCADE)
    members = models.ManyToManyField("member.Member", related_name="victories")

    @property
    def type(self):
        count = self.members.count()
        if count == 1:
            return VictoryType.SOLO
        elif count >= 2:
            return VictoryType.DRAW
        return None

    def __str__(self):
        return f"Victory in {self.game.name} ({self.type})"

    class Meta:
        verbose_name_plural = "Victories"
