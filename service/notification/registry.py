from django.conf import settings

from email_service.templates import notification_email
from notification.models import NotificationDelivery

Channel = NotificationDelivery.Channel

REGISTRY = {}


def register(event_type):
    def decorator(cls):
        cls.event_type = event_type
        REGISTRY[event_type] = cls
        return cls
    return decorator


def get_spec(event_type, context):
    spec_class = REGISTRY.get(event_type)
    if spec_class is None:
        return None
    return spec_class(context)


class NotificationSpec:
    event_type = None
    exclude_actor = False
    channels = [Channel.PUSH]
    email_link_text = "View Game"

    def __init__(self, context):
        self.context = context

    def get_audience(self):
        return self.context.payload.get("recipients", [])

    def get_recipients(self):
        recipients = set(self.get_audience())
        if self.exclude_actor:
            actor = self.context.actor
            actor_id = getattr(actor, "id", actor)
            recipients.discard(actor_id)
        return recipients

    def get_title(self):
        return self.context.game.name

    def get_body(self):
        raise NotImplementedError

    def get_link(self):
        return self._game_url()

    def _game_url(self):
        return f"{settings.FRONTEND_URL}/game/{self.context.game.id}"

    def get_email_subject(self):
        return self.context.game.name

    def get_email_body(self):
        return self.get_body()

    def render(self, channel):
        link = self.get_link() if self.context.game is not None else None
        if channel == Channel.EMAIL:
            return {
                "channel": channel,
                "heading": self.get_email_subject(),
                "body": notification_email(
                    title=self.get_title(),
                    body=self.get_email_body(),
                    link=link,
                    link_text=self.email_link_text,
                ),
                "link": None,
                "data": None,
            }
        return {
            "channel": channel,
            "heading": self.get_title(),
            "body": self.get_body(),
            "link": link,
            "data": self._push_data(link),
        }

    def _push_data(self, link):
        if self.context.game is None:
            return None
        data = {"game_id": str(self.context.game.id)}
        if link is not None:
            data["link"] = link
        return data

    def actor_name(self):
        if self.context.game.anonymity_active:
            return "Anonymous"
        actor = self.context.actor
        return actor.profile.name if actor is not None else "Deleted User"


@register("channel_message")
class ChannelMessageSpec(NotificationSpec):
    exclude_actor = True

    def get_audience(self):
        return self.context.channel.member_user_ids()

    def get_link(self):
        return f"{self._game_url()}/phase/{self.context.phase.id}/chat/channel/{self.context.channel.id}"

    def get_body(self):
        return f"{self.actor_name()}: {self._truncate(self.context.payload['body'])}"

    @staticmethod
    def _truncate(text: str, max_lines: int = 3, max_chars: int = 200) -> str:
        lines = text.split("\n")
        truncated = "\n".join(lines[:max_lines])
        if len(truncated) > max_chars:
            truncated = truncated[:max_chars].rstrip() + "…"
        elif len(lines) > max_lines:
            truncated += "…"
        return truncated


@register("draw_proposal")
class DrawProposalSpec(NotificationSpec):
    exclude_actor = True

    def get_audience(self):
        return self.context.game.active_member_user_ids(include_gm=True)

    def get_link(self):
        return f"{self._game_url()}/phase/{self.context.phase.id}/draw-proposals"

    def get_body(self):
        return f"{self.actor_name()} has proposed a draw. Respond to it now."


@register("game_start")
class GameStartSpec(NotificationSpec):
    channels = [Channel.PUSH, Channel.EMAIL]

    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True)

    def get_body(self):
        return "The game has started. You can now chat with other players and submit your orders. Good luck!"

    def get_email_subject(self):
        return f"{self.context.game.name} — Game Started"


@register("game_draw")
class GameDrawSpec(NotificationSpec):
    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True)

    def get_body(self):
        names = ", ".join(member.name for member in self.context.game.winner_members())
        return f"The game has ended in a draw, including {names}. Well played!"


@register("game_solo_win")
class GameSoloWinSpec(NotificationSpec):
    def get_audience(self):
        return self.context.game.winner_user_ids()

    def get_body(self):
        return "The game has ended, you achieved a solo win! Congratulations!"


@register("game_solo_loss")
class GameSoloLossSpec(NotificationSpec):
    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True) - self.context.game.winner_user_ids()

    def get_body(self):
        winners = self.context.game.winner_members()
        winner_name = winners[0].name if winners else ""
        return f"The game has ended, and {winner_name} achieved a solo win! Better luck next time!"


@register("phase_resolved")
class PhaseResolvedSpec(NotificationSpec):
    channels = [Channel.PUSH, Channel.EMAIL]

    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True)

    def get_body(self):
        return f"{self.context.phase.name} has been resolved"

    def get_email_subject(self):
        return f"{self.context.game.name} — {self.context.phase.name} Resolved"


@register("phase_resolved_early")
class PhaseResolvedEarlySpec(NotificationSpec):
    channels = [Channel.PUSH, Channel.EMAIL]

    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True)

    def get_body(self):
        return f"{self.context.phase.name} resolved early — all players confirmed their orders."

    def get_email_subject(self):
        return f"{self.context.game.name} — {self.context.phase.name} Resolved Early"


@register("game_deleted")
class GameDeletedSpec(NotificationSpec):
    def get_title(self):
        return self.context.payload["game_name"]

    def get_body(self):
        return "The game was deleted by the Game Master."


@register("game_admin_reassigned")
class GameAdminReassignedSpec(NotificationSpec):
    def get_audience(self):
        admin_id = self.context.game.admin_id
        return {admin_id} if admin_id is not None else set()

    def get_body(self):
        return "The previous manager is no longer available, so you are now managing this game."


class GameManagementSpec(NotificationSpec):
    exclude_actor = True

    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True)

    def manager_label(self):
        label = self.context.game.manager_label
        if not self.context.game.anonymity_active:
            label += f" ({self.context.actor.username})"
        return label

    def deadline(self):
        phase = self.context.game.current_phase
        return (phase.formatted_deadline if phase else None) or "N/A"


@register("game_paused")
class GamePausedSpec(GameManagementSpec):
    def get_body(self):
        return f"Game paused by {self.manager_label()}"


@register("game_resumed")
class GameResumedSpec(GameManagementSpec):
    def get_body(self):
        return f"Game resumed by {self.manager_label()}. New deadline: {self.deadline()}"


@register("game_deadline_extended")
class GameDeadlineExtendedSpec(GameManagementSpec):
    def get_body(self):
        return f"Deadline extended by {self.manager_label()}. New deadline: {self.deadline()}"


@register("kicked_from_staging")
class KickedFromStagingSpec(NotificationSpec):
    def get_body(self):
        return f"You were removed from this game by {self.context.game.manager_label}."


@register("removed_from_staging")
class RemovedFromStagingSpec(NotificationSpec):
    def get_title(self):
        return "Removed from staging games"

    def get_body(self):
        return f"You were removed from {self.context.game.name} because you entered civil disorder in an active game."


@register("civil_disorder")
class CivilDisorderSpec(NotificationSpec):
    channels = [Channel.PUSH, Channel.EMAIL]

    def get_audience(self):
        return self.context.game.active_member_user_ids(include_gm=True)

    def get_link(self):
        return None

    def get_title(self):
        return "Civil Disorder"

    def get_body(self):
        return f"{self.context.payload['nation_names']} entered civil disorder."

    def get_email_subject(self):
        return f"{self.context.game.name} — Civil Disorder"


@register("civil_disorder_recovery")
class CivilDisorderRecoverySpec(NotificationSpec):
    exclude_actor = True

    def get_audience(self):
        return self.context.game.active_member_user_ids(include_gm=True)

    def get_link(self):
        return None

    def get_title(self):
        return "Player Returned"

    def get_body(self):
        member = self.context.game.members.filter(user=self.context.actor).first()
        nation_name = member.nation.name if member and member.nation else "A player"
        return f"{nation_name} has returned from civil disorder."


@register("elimination")
class EliminationSpec(NotificationSpec):
    def get_body(self):
        return "You've been eliminated. You are not required to enter any orders anymore. You can still chat with players. Better luck next time!"


@register("nmr_extension_used")
class NmrExtensionUsedSpec(NotificationSpec):
    def get_audience(self):
        actor = self.context.actor
        actor_id = getattr(actor, "id", actor)
        return {actor_id} if actor_id is not None else set()

    def get_body(self):
        member = self.context.game.members.filter(user=self.context.actor).first()
        remaining = member.nmr_extensions_remaining if member else 0
        deadline = self.context.phase.formatted_deadline
        return f"You did not submit orders and used an automatic extension ({remaining} remaining). The current phase is extended until {deadline}."


@register("nmr_extension_applied")
class NmrExtensionAppliedSpec(NotificationSpec):
    def get_audience(self):
        return self.context.game.member_user_ids(include_gm=True)

    def get_body(self):
        deadline = self.context.phase.formatted_deadline
        return f"Some player(s) did not submit orders and used an extension. The current phase is extended until {deadline}."


@register("deadline_warning")
class DeadlineWarningSpec(NotificationSpec):
    channels = [Channel.PUSH, Channel.EMAIL]
    email_link_text = "Submit Orders"

    def get_body(self):
        return self.context.payload["body"]

    def get_email_subject(self):
        return f"{self.context.game.name} — Deadline Approaching"
