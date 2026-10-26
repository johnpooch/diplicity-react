from django.db import models

from common.constants import GameStatus


class DrawProposalQuerySet(models.QuerySet):
    def visible_to(self, actor):
        return self

    def in_started_games(self):
        return self.filter(game__status__in=(GameStatus.ACTIVE, GameStatus.COMPLETED, GameStatus.ABANDONED))

    def active(self):
        return self.filter(cancelled_at__isnull=True)

    def for_game(self, game):
        return self.filter(game=game)

    def pending(self):
        return self.active().filter(votes__accepted__isnull=True).exclude(votes__accepted=False).distinct()
