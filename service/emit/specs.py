from emit.audience import (
    Active,
    ActiveExceptActor,
    Actor,
    Admin,
    AllPlayers,
    AllPlayersExceptActor,
    AllPlayersExceptWinners,
    ChannelMembersExceptActor,
    Winners,
    victory_members,
)
from emit.base import EmitSpec
from emit.context import EmitContext
from emit.link import ChannelLink, DrawProposalsLink, NoLink
from emit.registry import register
from emit.transport import Email, Push, Timeline


@register("channel_message")
class ChannelMessageSpec(EmitSpec):
    transports = [Push]
    audience = ChannelMembersExceptActor
    link = ChannelLink

    def build_context(self, message):
        game = message.channel.game
        return EmitContext(
            self.event_type,
            game=game,
            phase=message.phase or game.phases.last(),
            actor=message.sender.user,
            channel=message.channel,
            payload={"body": message.body},
        )

    def get_body(self, context):
        return f"{self.actor_name(context)}: {self._truncate(context.payload['body'])}"

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
class DrawProposalSpec(EmitSpec):
    transports = [Push]
    audience = ActiveExceptActor
    link = DrawProposalsLink

    def build_context(self, draw_proposal):
        return EmitContext(
            self.event_type,
            game=draw_proposal.game,
            phase=draw_proposal.phase,
            actor=draw_proposal.created_by.user,
        )

    def get_body(self, context):
        return f"{self.actor_name(context)} has proposed a draw. Respond to it now."


@register("game_start")
class GameStartSpec(EmitSpec):
    transports = [Push, Timeline, Email]
    audience = AllPlayers

    def get_body(self, context):
        return "The game has started. You can now chat with other players and submit your orders. Good luck!"

    def get_email_subject(self, context):
        return f"{context.game.name} — Game Started"


@register("game_draw")
class GameDrawSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayers

    def get_body(self, context):
        names = ", ".join(member.name for member in victory_members(context.game))
        return f"The game has ended in a draw, including {names}. Well played!"


@register("game_solo_win")
class GameSoloWinSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = Winners

    def get_body(self, context):
        return "The game has ended, you achieved a solo win! Congratulations!"


@register("game_solo_loss")
class GameSoloLossSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptWinners

    def get_body(self, context):
        winners = victory_members(context.game)
        winner_name = winners[0].name if winners else ""
        return f"The game has ended, and {winner_name} achieved a solo win! Better luck next time!"


@register("phase_resolved")
class PhaseResolvedSpec(EmitSpec):
    transports = [Push, Timeline, Email]
    audience = AllPlayers

    def get_body(self, context):
        return f"{context.phase.name} has been resolved"

    def get_email_subject(self, context):
        return f"{context.game.name} — {context.phase.name} Resolved"


@register("phase_resolved_early")
class PhaseResolvedEarlySpec(EmitSpec):
    transports = [Push, Timeline, Email]
    audience = AllPlayers

    def get_body(self, context):
        return f"{context.phase.name} resolved early — all players confirmed their orders."

    def get_email_subject(self, context):
        return f"{context.game.name} — {context.phase.name} Resolved Early"


@register("game_deleted")
class GameDeletedSpec(EmitSpec):
    transports = [Push]

    def get_title(self, context):
        return context.payload["game_name"]

    def get_body(self, context):
        return "The game was deleted by the Game Master."


@register("game_admin_reassigned")
class GameAdminReassignedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = Admin

    def get_body(self, context):
        return "The previous manager is no longer available, so you are now managing this game."


class GameManagementSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptActor

    def manager_label(self, context):
        label = context.game.manager_label
        if not context.game.anonymity_active:
            label += f" ({context.actor.username})"
        return label

    def deadline(self, context):
        phase = context.game.current_phase
        return (phase.formatted_deadline if phase else None) or "N/A"


@register("game_paused")
class GamePausedSpec(GameManagementSpec):
    def get_body(self, context):
        return f"Game paused by {self.manager_label(context)}"


@register("game_resumed")
class GameResumedSpec(GameManagementSpec):
    def get_body(self, context):
        return f"Game resumed by {self.manager_label(context)}. New deadline: {self.deadline(context)}"


@register("game_deadline_extended")
class GameDeadlineExtendedSpec(GameManagementSpec):
    def get_body(self, context):
        return f"Deadline extended by {self.manager_label(context)}. New deadline: {self.deadline(context)}"


@register("kicked_from_staging")
class KickedFromStagingSpec(EmitSpec):
    transports = [Push]

    def get_body(self, context):
        return f"You were removed from this game by {context.game.manager_label}."


@register("removed_from_staging")
class RemovedFromStagingSpec(EmitSpec):
    transports = [Push]

    def get_title(self, context):
        return "Removed from staging games"

    def get_body(self, context):
        return f"You were removed from {context.game.name} because you entered civil disorder in an active game."


@register("civil_disorder")
class CivilDisorderSpec(EmitSpec):
    transports = [Push, Timeline, Email]
    audience = Active
    link = NoLink

    def get_title(self, context):
        return "Civil Disorder"

    def get_body(self, context):
        return f"{context.payload['nation_names']} entered civil disorder."

    def get_email_subject(self, context):
        return f"{context.game.name} — Civil Disorder"


@register("civil_disorder_recovery")
class CivilDisorderRecoverySpec(EmitSpec):
    transports = [Push, Timeline]
    audience = ActiveExceptActor
    link = NoLink

    def get_title(self, context):
        return "Player Returned"

    def get_body(self, context):
        member = context.game.members.filter(user=context.actor).first()
        nation_name = member.nation.name if member and member.nation else "A player"
        return f"{nation_name} has returned from civil disorder."


@register("elimination")
class EliminationSpec(EmitSpec):
    transports = [Push, Timeline]

    def get_body(self, context):
        return "You've been eliminated. You are not required to enter any orders anymore. You can still chat with players. Better luck next time!"


@register("nmr_extension_used")
class NmrExtensionUsedSpec(EmitSpec):
    transports = [Push]
    audience = Actor

    def get_body(self, context):
        member = context.game.members.filter(user=context.actor).first()
        remaining = member.nmr_extensions_remaining if member else 0
        deadline = context.phase.formatted_deadline
        return f"You did not submit orders and used an automatic extension ({remaining} remaining). The current phase is extended until {deadline}."


@register("nmr_extension_applied")
class NmrExtensionAppliedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayers

    def get_body(self, context):
        deadline = context.phase.formatted_deadline
        return f"Some player(s) did not submit orders and used an extension. The current phase is extended until {deadline}."


@register("deadline_warning")
class DeadlineWarningSpec(EmitSpec):
    transports = [Push]

    def get_body(self, context):
        return context.payload["body"]
