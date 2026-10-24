from typing import Optional

from adjudicator.types import ResolutionCode


class GameStatus:
    PENDING = "pending"
    MUSTERING = "mustering"
    ACTIVE = "active"
    COMPLETED = "completed"
    ABANDONED = "abandoned"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (MUSTERING, "Mustering"),
        (ACTIVE, "Active"),
        (COMPLETED, "Completed"),
        (ABANDONED, "Abandoned"),
    )


class ResolutionJob:
    TASK_NAME = "phase.resolve_phase"

    TODO = "todo"
    DOING = "doing"
    CANCELLED = "cancelled"

    PENDING_STATUSES = (TODO, DOING)

    @staticmethod
    def lock_for_game(game_id):
        return f"resolve-game-{game_id}"


class DeadlineWarningJob:
    TASK_NAME = "phase.send_deadline_warning"

    TODO = "todo"
    DOING = "doing"
    SUCCEEDED = "succeeded"

    LIVE_STATUSES = (TODO, DOING, SUCCEEDED)


class MusterJob:
    TASK_NAME = "game.start_if_mustered"

    TODO = "todo"
    DOING = "doing"
    CANCELLED = "cancelled"

    LIVE_STATUSES = (TODO, DOING)

    lock_for_game = ResolutionJob.lock_for_game


class MusterReminderJob:
    TASK_NAME = "game.send_muster_reminder"

    TODO = "todo"
    DOING = "doing"
    SUCCEEDED = "succeeded"
    CANCELLED = "cancelled"

    LIVE_STATUSES = (TODO, DOING, SUCCEEDED)


class MovementPhaseDuration:
    FIVE_MINUTES = "5 minutes"
    FIFTEEN_MINUTES = "15 minutes"
    THIRTY_MINUTES = "30 minutes"
    ONE_HOUR = "1 hour"
    TWO_HOURS = "2 hours"
    FOUR_HOURS = "4 hours"
    EIGHT_HOURS = "8 hours"
    TWELVE_HOURS = "12 hours"
    TWENTY_FOUR_HOURS = "24 hours"
    FORTY_EIGHT_HOURS = "48 hours"
    THREE_DAYS = "3 days"
    FOUR_DAYS = "4 days"
    ONE_WEEK = "1 week"
    TWO_WEEKS = "2 weeks"

    MOVEMENT_PHASE_DURATION_CHOICES = (
        (FIVE_MINUTES, "5 minutes"),
        (FIFTEEN_MINUTES, "15 minutes"),
        (THIRTY_MINUTES, "30 minutes"),
        (ONE_HOUR, "1 hour"),
        (TWO_HOURS, "2 hours"),
        (FOUR_HOURS, "4 hours"),
        (EIGHT_HOURS, "8 hours"),
        (TWELVE_HOURS, "12 hours"),
        (TWENTY_FOUR_HOURS, "24 hours"),
        (FORTY_EIGHT_HOURS, "48 hours"),
        (THREE_DAYS, "3 days"),
        (FOUR_DAYS, "4 days"),
        (ONE_WEEK, "1 week"),
        (TWO_WEEKS, "2 weeks"),
    )

    PRIVATE_ONLY_DURATIONS = frozenset({FIVE_MINUTES, FIFTEEN_MINUTES, THIRTY_MINUTES})


class DeadlineMode:
    DURATION = "duration"
    FIXED_TIME = "fixed_time"

    DEADLINE_MODE_CHOICES = (
        (DURATION, "Duration"),
        (FIXED_TIME, "Fixed Time"),
    )


class PhaseFrequency:
    HOURLY = "hourly"
    DAILY = "daily"
    EVERY_2_DAYS = "every_2_days"
    WEEKLY = "weekly"

    PHASE_FREQUENCY_CHOICES = (
        (HOURLY, "Hourly"),
        (DAILY, "Daily"),
        (EVERY_2_DAYS, "Every 2 days"),
        (WEEKLY, "Weekly"),
    )


def duration_to_seconds(duration: Optional[str]) -> Optional[int]:
    if duration is None:
        return None
    duration_map = {
        MovementPhaseDuration.FIVE_MINUTES: 5 * 60,
        MovementPhaseDuration.FIFTEEN_MINUTES: 15 * 60,
        MovementPhaseDuration.THIRTY_MINUTES: 30 * 60,
        MovementPhaseDuration.ONE_HOUR: 1 * 60 * 60,
        MovementPhaseDuration.TWO_HOURS: 2 * 60 * 60,
        MovementPhaseDuration.FOUR_HOURS: 4 * 60 * 60,
        MovementPhaseDuration.EIGHT_HOURS: 8 * 60 * 60,
        MovementPhaseDuration.TWELVE_HOURS: 12 * 60 * 60,
        MovementPhaseDuration.TWENTY_FOUR_HOURS: 24 * 60 * 60,
        MovementPhaseDuration.FORTY_EIGHT_HOURS: 48 * 60 * 60,
        MovementPhaseDuration.THREE_DAYS: 3 * 24 * 60 * 60,
        MovementPhaseDuration.FOUR_DAYS: 4 * 24 * 60 * 60,
        MovementPhaseDuration.ONE_WEEK: 7 * 24 * 60 * 60,
        MovementPhaseDuration.TWO_WEEKS: 14 * 24 * 60 * 60,
    }
    return duration_map.get(duration, 0)


class PressType:
    FULL_PRESS = "full_press"
    NO_PRESS = "no_press"

    PRESS_TYPE_CHOICES = (
        (FULL_PRESS, "Full Press"),
        (NO_PRESS, "No Press"),
    )


class Commitment:
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNDEFINED = "undefined"

    COMMITMENT_CHOICES = (
        (HIGH, "High"),
        (MEDIUM, "Medium"),
        (LOW, "Low"),
        (UNDEFINED, "New"),
    )


class CommitmentEvent:
    SUBMITTED = "submitted"
    NMR = "nmr"
    CIVIL_DISORDER = "civil_disorder"
    EARLY_WITHDRAWAL = "early_withdrawal"
    LATE_WITHDRAWAL = "late_withdrawal"
    MUSTER_NO_SHOW = "muster_no_show"

    KIND_CHOICES = (
        (SUBMITTED, "Submitted"),
        (NMR, "NMR"),
        (CIVIL_DISORDER, "Civil disorder"),
        (EARLY_WITHDRAWAL, "Early withdrawal"),
        (LATE_WITHDRAWAL, "Late withdrawal"),
        (MUSTER_NO_SHOW, "Muster no-show"),
    )

    POINTS = {
        SUBMITTED: 1,
        NMR: -2,
        CIVIL_DISORDER: -10,
        EARLY_WITHDRAWAL: -1,
        LATE_WITHDRAWAL: 0,
        MUSTER_NO_SHOW: -1,
    }


class UserKind:
    HUMAN = "human"
    LLM = "llm"
    DUMBBOT = "dumbbot"

    KIND_CHOICES = (
        (HUMAN, "Human"),
        (LLM, "LLM"),
        (DUMBBOT, "DumbBot"),
    )

    BOT_KINDS = (LLM, DUMBBOT)


class MemberKind:
    PLAYER = "player"
    GAME_MASTER = "game_master"

    KIND_CHOICES = (
        (PLAYER, "Player"),
        (GAME_MASTER, "Game Master"),
    )


class CommitmentRequirement:
    OPEN = "open"
    COMMITTED = "committed"

    COMMITMENT_REQUIREMENT_CHOICES = (
        (OPEN, "Open"),
        (COMMITTED, "Committed"),
    )


class CommitmentEligibility:
    ELIGIBLE = "eligible"
    COMMITTED_LOCKED = "committed_locked"
    LOW_LOCKED = "low_locked"


class MusterStatus:
    CONFIRMATION_REQUIRED = "confirmation_required"
    CONFIRMED = "confirmed"


class GameActionKey:
    JOIN = "join"
    CONFIRM_SEAT = "confirm_seat"
    EDIT_NATION_PREFERENCES = "edit_nation_preferences"
    ASSIGN_NATIONS = "assign_nations"
    EXTEND_DEADLINE = "extend_deadline"
    PAUSE = "pause"
    UNPAUSE = "unpause"
    CLONE_TO_SANDBOX = "clone_to_sandbox"
    LEAVE = "leave"
    WITHDRAW = "withdraw"
    DELETE = "delete"

    KEY_CHOICES = (
        (JOIN, "Join"),
        (CONFIRM_SEAT, "Confirm seat"),
        (EDIT_NATION_PREFERENCES, "Edit nation preferences"),
        (ASSIGN_NATIONS, "Assign nations"),
        (EXTEND_DEADLINE, "Extend deadline"),
        (PAUSE, "Pause"),
        (UNPAUSE, "Unpause"),
        (CLONE_TO_SANDBOX, "Clone to sandbox"),
        (LEAVE, "Leave"),
        (WITHDRAW, "Withdraw"),
        (DELETE, "Delete"),
    )

    GAME_INFO_KEYS = (
        JOIN,
        CONFIRM_SEAT,
        ASSIGN_NATIONS,
        EXTEND_DEADLINE,
        PAUSE,
        UNPAUSE,
        CLONE_TO_SANDBOX,
        LEAVE,
        WITHDRAW,
        DELETE,
    )
    PLAYER_LIST_KEYS = (EDIT_NATION_PREFERENCES,)
    SEAT_KEYS = (CONFIRM_SEAT, LEAVE, WITHDRAW)


class MemberActionKey:
    TAKE_OVER = "take_over"
    SHARE_REPLACEMENT_LINK = "share_replacement_link"
    REMOVE_FROM_LOBBY = "remove_from_lobby"
    REMOVE_FROM_GAME = "remove_from_game"

    KEY_CHOICES = (
        (TAKE_OVER, "Take over"),
        (SHARE_REPLACEMENT_LINK, "Share replacement link"),
        (REMOVE_FROM_LOBBY, "Remove from lobby"),
        (REMOVE_FROM_GAME, "Remove from game"),
    )


class ActionBlockedReason:
    COMMITMENT_TOO_LOW = "commitment_too_low"
    NO_MISSED_ORDERS = "no_missed_orders"

    REASON_CHOICES = (
        (COMMITMENT_TOO_LOW, "Commitment too low"),
        (NO_MISSED_ORDERS, "No missed orders"),
    )


class ParticipationStatus:
    GAME_MASTER = "game_master"
    REPLACED = "replaced"
    REMOVED = "removed"
    WITHDRAWN = "withdrawn"
    WON = "won"
    DREW = "drew"
    ELIMINATED = "eliminated"
    CIVIL_DISORDER = "civil_disorder"
    SEAT_UNCONFIRMED = "seat_unconfirmed"
    SEAT_CONFIRMED = "seat_confirmed"
    JOINED = "joined"
    PLAYING = "playing"

    STATUS_CHOICES = (
        (GAME_MASTER, "Game master"),
        (REPLACED, "Replaced"),
        (REMOVED, "Removed"),
        (WITHDRAWN, "Withdrawn"),
        (WON, "Won"),
        (DREW, "Drew"),
        (ELIMINATED, "Eliminated"),
        (CIVIL_DISORDER, "Civil disorder"),
        (SEAT_UNCONFIRMED, "Seat unconfirmed"),
        (SEAT_CONFIRMED, "Seat confirmed"),
        (JOINED, "Joined"),
        (PLAYING, "Playing"),
    )


class MyGamesSection:
    NEEDS_ATTENTION = "needs_attention"
    MANAGING = "managing"
    ACTIVE = "active"
    MUSTERING = "mustering"
    PENDING = "pending"
    RECENTLY_FINISHED = "recently_finished"
    SANDBOX = "sandbox"

    SECTION_CHOICES = (
        (NEEDS_ATTENTION, "Needs attention"),
        (MANAGING, "Managing"),
        (ACTIVE, "Active"),
        (MUSTERING, "Mustering"),
        (PENDING, "Pending"),
        (RECENTLY_FINISHED, "Recently finished"),
        (SANDBOX, "Sandbox"),
    )


class MyGameStateKind:
    CONFIRM_SEAT = "confirm_seat"
    SUBMIT_ORDERS = "submit_orders"
    VOTE_ON_DRAW = "vote_on_draw"
    SEAT_CONFIRMED = "seat_confirmed"
    ORDERS_UNCONFIRMED = "orders_unconfirmed"
    ORDERS_CONFIRMED = "orders_confirmed"
    RESOLVING = "resolving"
    MUSTERING = "mustering"
    WAITING_FOR_PLAYERS = "waiting_for_players"
    PAUSED = "paused"
    SANDBOX = "sandbox"
    FINISHED = "finished"

    KIND_CHOICES = (
        (CONFIRM_SEAT, "Confirm seat"),
        (SUBMIT_ORDERS, "Submit orders"),
        (VOTE_ON_DRAW, "Vote on draw"),
        (SEAT_CONFIRMED, "Seat confirmed"),
        (ORDERS_UNCONFIRMED, "Orders unconfirmed"),
        (ORDERS_CONFIRMED, "Orders confirmed"),
        (RESOLVING, "Resolving"),
        (MUSTERING, "Mustering"),
        (WAITING_FOR_PLAYERS, "Waiting for players"),
        (PAUSED, "Paused"),
        (SANDBOX, "Sandbox"),
        (FINISHED, "Finished"),
    )


class MyGameResult:
    SOLO_VICTORY = "solo_victory"
    WON_BY = "won_by"
    DRAW = "draw"
    ABANDONED = "abandoned"
    ONGOING = "ongoing"

    RESULT_CHOICES = (
        (SOLO_VICTORY, "Solo victory"),
        (WON_BY, "Won by"),
        (DRAW, "Draw"),
        (ABANDONED, "Abandoned"),
        (ONGOING, "Ongoing"),
    )


class MemberDeparture:
    ELIMINATED = "eliminated"
    CIVIL_DISORDER = "civil_disorder"
    WITHDRAWN = "withdrawn"
    REMOVED = "removed"

    DEPARTURE_CHOICES = (
        (ELIMINATED, "Eliminated"),
        (CIVIL_DISORDER, "Civil disorder"),
        (WITHDRAWN, "Withdrawn"),
        (REMOVED, "Removed"),
    )


class VariantStatus:
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"

    STATUS_CHOICES = (
        (DRAFT, "Draft"),
        (PUBLISHED, "Published"),
        (ARCHIVED, "Archived"),
    )


class PhaseStatus:
    PENDING = "pending"
    ACTIVE = "active"
    PROCESSING = "processing"
    COMPLETED = "completed"
    TEMPLATE = "template"

    STATUS_CHOICES = (
        (PENDING, "Pending"),
        (ACTIVE, "Active"),
        (PROCESSING, "Processing"),
        (COMPLETED, "Completed"),
        (TEMPLATE, "Template"),
    )


class PhaseType:
    MOVEMENT = "Movement"
    RETREAT = "Retreat"
    ADJUSTMENT = "Adjustment"

    TYPE_CHOICES = (
        (MOVEMENT, "Movement"),
        (RETREAT, "Retreat"),
        (ADJUSTMENT, "Adjustment"),
    )


class OrderType:
    MOVE = "Move"
    MOVE_VIA_CONVOY = "MoveViaConvoy"
    HOLD = "Hold"
    SUPPORT = "Support"
    CONVOY = "Convoy"
    BUILD = "Build"
    DISBAND = "Disband"

    ORDER_TYPE_CHOICES = (
        (MOVE, "Move"),
        (MOVE_VIA_CONVOY, "Move via Convoy"),
        (HOLD, "Hold"),
        (SUPPORT, "Support"),
        (CONVOY, "Convoy"),
        (BUILD, "Build"),
        (DISBAND, "Disband"),
    )


class OrderCreationStep:
    SELECT_ORDER_TYPE = "select-order-type"
    SELECT_UNIT_TYPE = "select-unit-type"
    SELECT_TARGET = "select-target"
    SELECT_AUX = "select-aux"
    SELECT_NAMED_COAST = "select-named-coast"
    COMPLETED = "completed"

    ORDER_CREATION_STEP_CHOICES = (
        (SELECT_ORDER_TYPE, "select-order-type"),
        (SELECT_UNIT_TYPE, "select-unit-type"),
        (SELECT_TARGET, "select-target"),
        (SELECT_AUX, "select-aux"),
        (SELECT_NAMED_COAST, "select-named-coast"),
        (COMPLETED, "completed"),
    )


class UnitType:
    ARMY = "Army"
    FLEET = "Fleet"

    UNIT_TYPE_CHOICES = (
        (ARMY, "Army"),
        (FLEET, "Fleet"),
    )


class ProvinceType:
    LAND = "land"
    SEA = "sea"
    COASTAL = "coastal"
    NAMED_COAST = "named_coast"

    TYPE_CHOICES = (
        (LAND, "Land"),
        (SEA, "Sea"),
        (COASTAL, "Coastal"),
        (NAMED_COAST, "Named coast"),
    )


class OrderResolutionStatus:
    SUCCEEDED = ResolutionCode.SUCCEEDED
    ILLEGAL_MOVE = ResolutionCode.ILLEGAL_MOVE
    ILLEGAL_DESTINATION = ResolutionCode.ILLEGAL_DESTINATION
    BOUNCED = ResolutionCode.BOUNCED
    INVALID_SUPPORT_ORDER = ResolutionCode.INVALID_SUPPORT_ORDER
    ILLEGAL_SUPPORT_DESTINATION = ResolutionCode.ILLEGAL_SUPPORT_DESTINATION
    INVALID_DESTINATION = ResolutionCode.INVALID_DESTINATION
    MISSING_SUPPORT_UNIT = ResolutionCode.MISSING_SUPPORT_UNIT
    MISSING_UNIT = ResolutionCode.MISSING_UNIT
    SUPPORT_BROKEN = ResolutionCode.SUPPORT_BROKEN
    MISSING_CONVOY_PATH = ResolutionCode.MISSING_CONVOY_PATH
    CONVOY_DISLODGED = ResolutionCode.CONVOY_DISLODGED

    STATUS_CHOICES = (
        (SUCCEEDED, "Succeeded"),
        (ILLEGAL_MOVE, "Illegal move"),
        (ILLEGAL_DESTINATION, "Illegal destination"),
        (BOUNCED, "Bounced"),
        (INVALID_SUPPORT_ORDER, "Invalid support order"),
        (ILLEGAL_SUPPORT_DESTINATION, "Illegal support destination"),
        (INVALID_DESTINATION, "Invalid destination"),
        (MISSING_SUPPORT_UNIT, "Missing support unit"),
        (MISSING_UNIT, "Missing unit"),
        (SUPPORT_BROKEN, "Support broken"),
        (MISSING_CONVOY_PATH, "Missing convoy path"),
        (CONVOY_DISLODGED, "Convoy dislodged"),
    )


class ChannelMessagePagination:
    DEFAULT_PAGE_SIZE = 50
    MAX_PAGE_SIZE = 100


class BundlePlatform:
    IOS = "ios"
    ANDROID = "android"

    PLATFORM_CHOICES = (
        (IOS, "iOS"),
        (ANDROID, "Android"),
    )


class UpdateResponseKind:
    UP_TO_DATE = "up_to_date"
