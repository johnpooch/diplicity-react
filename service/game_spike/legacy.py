from game.models import Game as LegacyGame
from member.models import CommitmentEntry, Member as LegacyMember
from phase.models import Phase as LegacyPhase


def legacy_game(game):
    return LegacyGame.objects.get(pk=game.pk)


def legacy_phase(phase):
    return LegacyPhase.objects.get(pk=phase.pk)


def delete_game(game):
    LegacyGame.objects.get(pk=game.pk).delete()


def record_commitment(member, kind):
    CommitmentEntry.objects.record(LegacyMember.objects.select_related("game", "user__profile").get(pk=member.pk), kind)
