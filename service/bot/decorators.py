import functools

from common.constants import PhaseStatus
from member.models import Member
from phase.models import Phase

from bot.constants import BOT_USER_EMAIL

_previous_phase_status = {}


def capture_phase_status(sender, instance, **kwargs):
    if instance.pk and instance.status == PhaseStatus.ACTIVE:
        _previous_phase_status[instance.pk] = (
            Phase.objects.filter(pk=instance.pk).values_list("status", flat=True).first()
        )


def on_phase_activated(func):
    @functools.wraps(func)
    def wrapper(sender, instance, created, **kwargs):
        previous_status = _previous_phase_status.pop(instance.pk, None)
        if instance.status != PhaseStatus.ACTIVE:
            return
        if not created and previous_status == PhaseStatus.ACTIVE:
            return
        return func(sender=sender, instance=instance, created=created, **kwargs)

    return wrapper


def with_bot_members(func):
    @functools.wraps(func)
    def wrapper(sender, instance, **kwargs):
        bot_members = list(
            Member.objects.filter(
                game_id=instance.game_id, user__email=BOT_USER_EMAIL
            ).select_related("user")
        )
        if not bot_members:
            return
        return func(sender=sender, instance=instance, bot_members=bot_members, **kwargs)

    return wrapper
