import functools

from common.constants import PhaseStatus
from member.models import Member
from phase.models import Phase

_previous_phase_status = {}


def _bot_user_ids_for_phase(phase_id):
    return set(
        Member.objects.filter(
            game__phases=phase_id, user__bot_profile__isnull=False
        ).values_list("user_id", flat=True)
    )


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
                game_id=instance.game_id, user__bot_profile__isnull=False
            ).select_related("user")
        )
        if not bot_members:
            return
        return func(sender=sender, instance=instance, bot_members=bot_members, **kwargs)

    return wrapper


def on_public_chat_message(func):
    @functools.wraps(func)
    def wrapper(sender, instance, created, **kwargs):
        if not created:
            return
        if instance.channel.private:
            return
        if Member.objects.filter(pk=instance.sender_id, user__bot_profile__isnull=False).exists():
            return
        return func(sender=sender, instance=instance, created=created, **kwargs)

    return wrapper


def with_bot_channel_members(func):
    @functools.wraps(func)
    def wrapper(sender, instance, **kwargs):
        bot_members = list(
            instance.channel.members.filter(
                user__bot_profile__isnull=False
            ).select_related("user")
        )
        if not bot_members:
            return
        return func(sender=sender, instance=instance, bot_members=bot_members, **kwargs)

    return wrapper


def on_orders_confirmed(func):
    @functools.wraps(func)
    def wrapper(sender, instance, **kwargs):
        if not instance.orders_confirmed:
            return
        return func(sender=sender, instance=instance, **kwargs)

    return wrapper


def when_humans_confirmed(func):
    @functools.wraps(func)
    def wrapper(sender, instance, **kwargs):
        bot_user_ids = _bot_user_ids_for_phase(instance.phase_id)
        if not bot_user_ids:
            return

        phase = instance.phase
        if phase.status != PhaseStatus.ACTIVE:
            return

        humans_pending = (
            phase.phase_states.filter(has_possible_orders=True, orders_confirmed=False)
            .exclude(member__user_id__in=bot_user_ids)
            .exists()
        )
        if humans_pending:
            return

        bot_phase_states = list(
            phase.phase_states.filter(
                has_possible_orders=True,
                orders_confirmed=False,
                member__user_id__in=bot_user_ids,
            ).select_related("member")
        )
        if not bot_phase_states:
            return

        return func(
            sender=sender, instance=instance, phase=phase, bot_phase_states=bot_phase_states, **kwargs
        )

    return wrapper
