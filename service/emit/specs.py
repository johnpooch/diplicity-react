from emit.audience import (
    AllPlayers,
    AllPlayersExceptActor,
    AllPlayersExceptExtensionUsers,
    AllPlayersExceptWinner,
    Active,
    ActiveExceptActor,
    ChannelMembersExceptActor,
)
from emit.base import EmitSpec
from emit.link import ChannelLink, DrawProposalsLink, NoLink
from emit.registry import register
from emit.transport import Push, Timeline


@register("channel_message")
class ChannelMessageSpec(EmitSpec):
    transports = [Push]
    audience = ChannelMembersExceptActor
    link = ChannelLink

    def get_body(self, context):
        return f"{context.payload['sender_name']}: {context.payload['body']}"


@register("draw_proposal")
class DrawProposalSpec(EmitSpec):
    transports = [Push]
    audience = ActiveExceptActor
    link = DrawProposalsLink

    def get_body(self, context):
        return f"{context.payload['proposer_name']} has proposed a draw. Respond to it now."


@register("game_start")
class GameStartSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayers

    def get_body(self, context):
        return "The game has started. You can now chat with other players and submit your orders. Good luck!"


@register("game_draw")
class GameDrawSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayers

    def get_body(self, context):
        return f"The game has ended in a draw, including {context.payload['winner_names']}. Well played!"


@register("game_solo_win")
class GameSoloWinSpec(EmitSpec):
    transports = [Push, Timeline]

    def get_body(self, context):
        return "The game has ended, you achieved a solo win! Congratulations!"


@register("game_solo_loss")
class GameSoloLossSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptWinner

    def get_body(self, context):
        return f"The game has ended, and {context.payload['winner_name']} achieved a solo win! Better luck next time!"


@register("phase_resolved")
class PhaseResolvedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayers

    def get_body(self, context):
        return f"{context.payload['phase_name']} has been resolved"


@register("phase_resolved_early")
class PhaseResolvedEarlySpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayers

    def get_body(self, context):
        return f"{context.payload['phase_name']} resolved early — all players confirmed their orders."


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

    def get_body(self, context):
        return "The previous manager is no longer available, so you are now managing this game."


@register("game_paused")
class GamePausedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptActor

    def get_body(self, context):
        return f"Game paused by {context.payload['manager_label']}"


@register("game_resumed")
class GameResumedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptActor

    def get_body(self, context):
        return f"Game resumed by {context.payload['manager_label']}. New deadline: {context.payload['deadline']}"


@register("game_deadline_extended")
class GameDeadlineExtendedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptActor

    def get_body(self, context):
        return f"Deadline extended by {context.payload['manager_label']}. New deadline: {context.payload['deadline']}"


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
        return f"You were removed from {context.payload['game_names']} because you entered civil disorder in an active game."


@register("civil_disorder")
class CivilDisorderSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = Active
    link = NoLink

    def get_title(self, context):
        return "Civil Disorder"

    def get_body(self, context):
        return f"{context.payload['nation_names']} entered civil disorder."


@register("civil_disorder_recovery")
class CivilDisorderRecoverySpec(EmitSpec):
    transports = [Push, Timeline]
    audience = ActiveExceptActor
    link = NoLink

    def get_title(self, context):
        return "Player Returned"

    def get_body(self, context):
        return f"{context.payload['nation_name']} has returned from civil disorder."


@register("elimination")
class EliminationSpec(EmitSpec):
    transports = [Push, Timeline]

    def get_body(self, context):
        return "You've been eliminated. You are not required to enter any orders anymore. You can still chat with players. Better luck next time!"


@register("nmr_extension_used")
class NmrExtensionUsedSpec(EmitSpec):
    transports = [Push]

    def get_body(self, context):
        return f"You did not submit orders and used an automatic extension ({context.payload['extensions_remaining']} remaining). The current phase is extended until {context.payload['deadline']}."


@register("nmr_extension_applied")
class NmrExtensionAppliedSpec(EmitSpec):
    transports = [Push, Timeline]
    audience = AllPlayersExceptExtensionUsers

    def get_body(self, context):
        return f"Some player(s) did not submit orders and used an extension. The current phase is extended until {context.payload['deadline']}."


@register("deadline_warning")
class DeadlineWarningSpec(EmitSpec):
    transports = [Push]

    def get_body(self, context):
        return context.payload["body"]
