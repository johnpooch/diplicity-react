from collections import namedtuple

from django.conf import settings

from notification.tasks import send_notification


class Bucket:
    TIMELINE_ONLY = "timeline-only"
    PUSH_AND_TIMELINE = "push+timeline"
    PUSH_ONLY = "push-only"


_Emission = namedtuple("_Emission", ["event_type", "game", "phase", "actor", "context"])
_Spec = namedtuple("_Spec", ["bucket", "resolve", "copy"])
_Copy = namedtuple("_Copy", ["title", "body", "data"])


def _actor_id(actor):
    if actor is None:
        return None
    return getattr(actor, "id", actor)


def _member_user_ids(members):
    return {member.user_id for member in members if member.user_id is not None}


def _with_game_master(user_ids, game):
    result = set(user_ids)
    if game.game_master_id is not None:
        result.add(game.game_master_id)
    return result


def _all_recipients(game, actor=None):
    user_ids = _with_game_master(_member_user_ids(game.members.all()), game)
    user_ids.discard(_actor_id(actor))
    return user_ids


def _canonical_recipients(game, actor=None):
    active = game.members.filter(eliminated=False, kicked=False)
    user_ids = _with_game_master(_member_user_ids(active), game)
    user_ids.discard(_actor_id(actor))
    return user_ids


def _game_link(game):
    return f"{settings.FRONTEND_URL}/game/{game.id}"


def _data(game, link=None):
    payload = {"game_id": str(game.id)}
    if link is not None:
        payload["link"] = link
    return payload


def _resolve_explicit(e):
    return set(e.context.get("recipients", []))


def _resolve_channel_message(e):
    channel = e.context["channel"]
    sender = e.context["sender"]
    if channel.private:
        members = channel.members.exclude(id=sender.id)
    else:
        members = channel.game.members.exclude(id=sender.id)
    return _member_user_ids(members)


def _resolve_draw_proposal(e):
    members = e.game.members.filter(eliminated=False, kicked=False, civil_disorder=False)
    user_ids = _with_game_master(_member_user_ids(members), e.game)
    user_ids.discard(_actor_id(e.actor))
    return user_ids


def _resolve_all(e):
    return _all_recipients(e.game)


def _resolve_all_except_actor(e):
    return _all_recipients(e.game, actor=e.actor)


def _resolve_canonical(e):
    return _canonical_recipients(e.game)


def _resolve_solo_loss(e):
    user_ids = _all_recipients(e.game)
    user_ids.discard(e.context["winner_user_id"])
    return user_ids


def _resolve_nmr_extension_applied(e):
    user_ids = _all_recipients(e.game)
    return user_ids - set(e.context["extension_user_ids"])


def _copy_channel_message(e):
    return _Copy(
        title=e.game.name,
        body=f"{e.context['sender_name']}: {e.context['body']}",
        data=_data(e.game, link=e.context["link"]),
    )


def _copy_draw_proposal(e):
    return _Copy(
        title=e.game.name,
        body=f"{e.context['proposer_name']} has proposed a draw. Respond to it now.",
        data=_data(e.game, link=e.context["link"]),
    )


def _copy_game_start(e):
    return _Copy(
        title=e.game.name,
        body="The game has started. You can now chat with other players and submit your orders. Good luck!",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_draw(e):
    return _Copy(
        title=e.game.name,
        body=f"The game has ended in a draw, including {e.context['winner_names']}. Well played!",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_solo_win(e):
    return _Copy(
        title=e.game.name,
        body="The game has ended, you achieved a solo win! Congratulations!",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_solo_loss(e):
    return _Copy(
        title=e.game.name,
        body=f"The game has ended, and {e.context['winner_name']} achieved a solo win! Better luck next time!",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_phase_resolved(e):
    return _Copy(
        title=e.game.name,
        body=f"{e.context['phase_name']} has been resolved",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_phase_resolved_early(e):
    return _Copy(
        title=e.game.name,
        body=f"{e.context['phase_name']} resolved early — all players confirmed their orders.",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_deleted(e):
    return _Copy(
        title=e.context["game_name"],
        body="The game was deleted by the Game Master.",
        data=None,
    )


def _copy_game_admin_reassigned(e):
    return _Copy(
        title=e.game.name,
        body="The previous manager is no longer available, so you are now managing this game.",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_paused(e):
    return _Copy(
        title=e.game.name,
        body=f"Game paused by {e.context['manager_label']}",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_resumed(e):
    return _Copy(
        title=e.game.name,
        body=f"Game resumed by {e.context['manager_label']}. New deadline: {e.context['deadline']}",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_game_deadline_extended(e):
    return _Copy(
        title=e.game.name,
        body=f"Deadline extended by {e.context['manager_label']}. New deadline: {e.context['deadline']}",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_kicked_from_staging(e):
    return _Copy(
        title=e.game.name,
        body=f"You were removed from this game by {e.game.manager_label}.",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_removed_from_staging(e):
    return _Copy(
        title="Removed from staging games",
        body=f"You were removed from {e.context['game_names']} because you entered civil disorder in an active game.",
        data=None,
    )


def _copy_civil_disorder(e):
    return _Copy(
        title="Civil Disorder",
        body=f"{e.context['nation_names']} entered civil disorder.",
        data=_data(e.game),
    )


def _copy_civil_disorder_recovery(e):
    return _Copy(
        title="Player Returned",
        body=f"{e.context['nation_name']} has returned from civil disorder.",
        data=_data(e.game),
    )


def _copy_elimination(e):
    return _Copy(
        title=e.game.name,
        body="You've been eliminated. You are not required to enter any orders anymore. You can still chat with players. Better luck next time!",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_nmr_extension_used(e):
    return _Copy(
        title=e.game.name,
        body=f"You did not submit orders and used an automatic extension ({e.context['extensions_remaining']} remaining). The current phase is extended until {e.context['deadline']}.",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_nmr_extension_applied(e):
    return _Copy(
        title=e.game.name,
        body=f"Some player(s) did not submit orders and used an extension. The current phase is extended until {e.context['deadline']}.",
        data=_data(e.game, link=_game_link(e.game)),
    )


def _copy_deadline_warning(e):
    return _Copy(
        title=e.game.name,
        body=e.context["body"],
        data=_data(e.game, link=_game_link(e.game)),
    )


REGISTRY = {
    "channel_message": _Spec(
        Bucket.PUSH_ONLY, _resolve_channel_message, _copy_channel_message
    ),
    "draw_proposal": _Spec(
        Bucket.PUSH_ONLY, _resolve_draw_proposal, _copy_draw_proposal
    ),
    "game_start": _Spec(Bucket.PUSH_AND_TIMELINE, _resolve_all, _copy_game_start),
    "game_draw": _Spec(Bucket.PUSH_AND_TIMELINE, _resolve_all, _copy_game_draw),
    "game_solo_win": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_explicit, _copy_game_solo_win
    ),
    "game_solo_loss": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_solo_loss, _copy_game_solo_loss
    ),
    "phase_resolved": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_all, _copy_phase_resolved
    ),
    "phase_resolved_early": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_all, _copy_phase_resolved_early
    ),
    "game_deleted": _Spec(Bucket.PUSH_ONLY, _resolve_explicit, _copy_game_deleted),
    "game_admin_reassigned": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_explicit, _copy_game_admin_reassigned
    ),
    "game_paused": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_all_except_actor, _copy_game_paused
    ),
    "game_resumed": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_all_except_actor, _copy_game_resumed
    ),
    "game_deadline_extended": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_all_except_actor, _copy_game_deadline_extended
    ),
    "kicked_from_staging": _Spec(
        Bucket.PUSH_ONLY, _resolve_explicit, _copy_kicked_from_staging
    ),
    "removed_from_staging": _Spec(
        Bucket.PUSH_ONLY, _resolve_explicit, _copy_removed_from_staging
    ),
    "civil_disorder": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_canonical, _copy_civil_disorder
    ),
    "civil_disorder_recovery": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_all_except_actor, _copy_civil_disorder_recovery
    ),
    "elimination": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_explicit, _copy_elimination
    ),
    "nmr_extension_used": _Spec(
        Bucket.PUSH_ONLY, _resolve_explicit, _copy_nmr_extension_used
    ),
    "nmr_extension_applied": _Spec(
        Bucket.PUSH_AND_TIMELINE, _resolve_nmr_extension_applied, _copy_nmr_extension_applied
    ),
    "deadline_warning": _Spec(
        Bucket.PUSH_ONLY, _resolve_explicit, _copy_deadline_warning
    ),
}


def _emission(event_type, game, phase, actor, context):
    if game is None and phase is not None:
        game = phase.game
    return _Emission(event_type, game, phase, actor, context or {})


def classification(event_type):
    return REGISTRY[event_type].bucket


def recipients(event_type, *, game=None, phase=None, actor=None, context=None):
    spec = REGISTRY[event_type]
    return spec.resolve(_emission(event_type, game, phase, actor, context))


def emit(event_type, *, game=None, phase=None, actor=None, context=None):
    spec = REGISTRY[event_type]
    e = _emission(event_type, game, phase, actor, context)

    user_ids = spec.resolve(e)

    if spec.bucket in (Bucket.PUSH_AND_TIMELINE, Bucket.PUSH_ONLY) and user_ids:
        copy = spec.copy(e)
        send_notification.defer(
            user_ids=list(user_ids),
            title=copy.title,
            body=copy.body,
            notification_type=event_type,
            data=copy.data,
        )
